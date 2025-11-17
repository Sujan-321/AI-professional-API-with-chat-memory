# app/api/conversate.py
from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session
import logging

from app.services.embedding import generate_embeddings
from app.services.llm_service import generate_response
from app.services.rag_service import RAGService
from app.db.database import get_db
from app.db.models import Booking

# Redis utilities
from app.utils.redis_client import get_chat_history, save_message

router = APIRouter()
logger = logging.getLogger("conversate")
logger.setLevel(logging.INFO)

rag_service = RAGService()


# -----------------------------
# Pydantic Models
# -----------------------------
class ConversateRequest(BaseModel):
    session_id: Optional[str] = None
    query: str
    top_k: Optional[int] = 4
    include_memory: Optional[bool] = True
    mode: Optional[str] = "semantic"
    booking: Optional[Dict[str, Any]] = None


class SourceItem(BaseModel):
    filename: Optional[str] = None
    chunk_id: Optional[int] = None
    score: Optional[float] = None
    chunk: Optional[str] = None


class ConversateResponse(BaseModel):
    answer: str
    round_trip_id: Optional[str] = None
    sources: List[SourceItem] = []


# -----------------------------
# Prompt Builder
# -----------------------------
def build_prompt(context_chunks: List[str], user_query: str, session_memory: Optional[str] = None) -> str:
    system_instruct = (
        "You are a helpful assistant that answers user questions using only the provided context. "
        "If the answer is not found in the context, say you don't know and suggest how the user can find it."
    )

    parts = [system_instruct]

    if session_memory:
        parts.append("### Conversation Memory:")
        parts.append(session_memory)

    if context_chunks:
        parts.append("### Relevant Document Excerpts:")
        for i, c in enumerate(context_chunks):
            excerpt = c if len(c) <= 2000 else c[:2000] + "..."
            parts.append(f"[EXCERPT {i+1}]\n{excerpt}\n")

    parts.append("### User Question:")
    parts.append(user_query)

    parts.append(
        "### Instructions:\nAnswer concisely. "
        "If referencing info, cite the excerpt number like [EXCERPT 1]."
    )

    return "\n\n".join(parts)


# -----------------------------
# Conversate Endpoint
# -----------------------------
@router.post("/conversate", response_model=ConversateResponse)
def conversate_endpoint(payload: ConversateRequest, db: Session = Depends(get_db)):
    """
    Conversational RAG:
      1) Optional booking save
      2) RAG retrieval via Qdrant
      3) Memory from Redis
      4) LLM generation
      5) Save conversation back to Redis
    """

    # -----------------------------
    # 1. Handle booking request
    # -----------------------------
    if payload.booking:
        try:
            info = payload.booking
            booking = Booking(
                session_id=payload.session_id,
                name=info.get("name"),
                email=info.get("email"),
                date=info.get("date"),
                time=info.get("time"),
            )
            db.add(booking)
            db.commit()
            db.refresh(booking)

            return ConversateResponse(
                answer=f"Booking confirmed for {booking.name} on {booking.date} at {booking.time} ✅",
                round_trip_id=None,
                sources=[]
            )
        except Exception as e:
            logger.exception("Booking save failed")
            raise HTTPException(status_code=500, detail=f"Booking creation failed: {e}")

    if not payload.query.strip():
        raise HTTPException(status_code=400, detail="Query cannot be empty.")

    top_k = payload.top_k if payload.top_k and payload.top_k > 0 else 4

    # -----------------------------
    # 2. Generate query embedding
    # -----------------------------
    try:
        _ = generate_embeddings([payload.query])[0]  # for validation, RAGService also embeds internally
    except Exception as e:
        logger.exception("Embedding generation failed")
        raise HTTPException(status_code=500, detail=f"Embedding generation failed: {e}")

    # -----------------------------
    # 3. RAG: Search Qdrant
    # -----------------------------
    try:
        search_result = rag_service.search(payload.query, limit=top_k)
    except Exception as e:
        logger.exception("RAG retrieval failed")
        raise HTTPException(status_code=500, detail=f"RAG retrieval failed: {e}")

    context_chunks: List[str] = []
    sources: List[SourceItem] = []

    # Normalize output
    if isinstance(search_result, list):
        for hit in search_result:
            chunk_text = hit.get("chunk") or hit.get("text") or ""
            if chunk_text:
                context_chunks.append(chunk_text)

            sources.append(
                SourceItem(
                    filename=hit.get("filename"),
                    chunk_id=hit.get("chunk_id"),
                    score=hit.get("score"),
                    chunk=(chunk_text[:250] + "...") if len(chunk_text) > 250 else chunk_text
                )
            )
    else:
        # fallback (rare)
        chunk = str(search_result)
        context_chunks = [chunk]
        sources = [SourceItem(chunk=chunk)]

    # -----------------------------
    # 4. Load Redis conversation memory
    # -----------------------------
    session_memory_text = None

    if payload.session_id and payload.include_memory:
        try:
            mem = get_chat_history(payload.session_id)
            if mem:
                session_memory_text = "\n".join(mem)
        except Exception:
            logger.exception("Redis memory load failed")

    # -----------------------------
    # 5. Build final prompt
    # -----------------------------
    prompt = build_prompt(context_chunks, payload.query, session_memory_text)

    # -----------------------------
    # 6. Call LLM
    # -----------------------------
    try:
        llm_resp = generate_response(prompt)
        llm_text = llm_resp["text"] if isinstance(llm_resp, dict) else str(llm_resp)
    except Exception as e:
        logger.exception("LLM generation failed")
        raise HTTPException(status_code=500, detail=f"LLM call failed: {e}")

    # -----------------------------
    # 7. Save chat to Redis
    # -----------------------------
    if payload.session_id:
        try:
            save_message(payload.session_id, "user", payload.query)
            save_message(payload.session_id, "assistant", llm_text)
        except Exception:
            logger.exception("Redis save failed")

    # -----------------------------
    # 8. Return final response
    # -----------------------------
    return ConversateResponse(
        answer=llm_text,
        round_trip_id=None,
        sources=sources
    )



















# # app/api/conversate.py
# from typing import List, Optional, Dict, Any
# from fastapi import APIRouter, Depends, HTTPException
# from pydantic import BaseModel
# from sqlalchemy.orm import Session
# import logging

# # local services (you already have these in your project)
# from app.services.embedding import generate_embeddings
# from app.services.vector_db import client as qdrant_client
# from app.services.llm_service import generate_response  # your Groq wrapper
# from app.db.database import get_db
# from app.db.models import Booking

# # Try to use memory service (higher-level). If not available, fall back to redis utils.
# try:
#     from app.services.memory_service import save_message_to_memory, get_memory_for_session  # optional
#     _memory_save = save_message_to_memory
#     _memory_get = get_memory_for_session
# except Exception:
#     # fallback to redis utils
#     try:
#         from app.utils.redis_client import save_message as _redis_save_message, get_chat_history as _redis_get_history
#         _memory_save = lambda session_id, message, db=None: _redis_save_message(session_id, message.get("role"), message.get("text"))
#         _memory_get = lambda session_id, db=None: "\n".join(_redis_get_history(session_id) or [])
#     except Exception:
#         _memory_save = None
#         _memory_get = None

# router = APIRouter()
# logger = logging.getLogger("conversate")
# logger.setLevel(logging.INFO)


# # ---------- Request / Response Schemas ----------
# class ConversateRequest(BaseModel):
#     session_id: Optional[str] = None
#     query: str
#     top_k: Optional[int] = 4
#     include_memory: Optional[bool] = True
#     mode: Optional[str] = "semantic"  # reserved for future modes
#     booking: Optional[Dict[str, Any]] = None  # optional booking payload


# class SourceItem(BaseModel):
#     filename: Optional[str] = None
#     chunk_id: Optional[int] = None
#     score: Optional[float] = None
#     chunk: Optional[str] = None


# class ConversateResponse(BaseModel):
#     answer: str
#     round_trip_id: Optional[str] = None
#     sources: List[SourceItem] = []


# # ---------- Helper functions ----------
# def build_prompt(context_chunks: List[str], user_query: str, session_memory: Optional[str] = None) -> str:
#     """
#     Builds a prompt to send to the LLM.
#     Combines system instruction, optional session memory, retrieved context chunks, and the user question.
#     """
#     system_instruct = (
#         "You are a helpful assistant that answers user questions using only the provided context. "
#         "If the answer is not in the context, say you don't know and provide a short suggestion on how the user can find it."
#     )

#     parts = [system_instruct]

#     if session_memory:
#         parts.append("### Conversation memory (previous messages):")
#         parts.append(session_memory)

#     if context_chunks:
#         parts.append("### Relevant document excerpts (use these to answer):")
#         for i, c in enumerate(context_chunks):
#             # keep excerpt length reasonable
#             excerpt = c if len(c) <= 2000 else c[:2000] + "..."
#             parts.append(f"[EXCERPT {i+1}]\n{excerpt}\n")

#     parts.append("### User question:")
#     parts.append(user_query)

#     parts.append(
#         "### Instructions:\nAnswer concisely. If you quote or use facts, cite which excerpt number you used, e.g., [EXCERPT 1]."
#     )

#     prompt = "\n\n".join(parts)
#     return prompt


# # ---------- Main endpoint ----------
# @router.post("/conversate", response_model=ConversateResponse)
# def conversate_endpoint(payload: ConversateRequest, db: Session = Depends(get_db)):
#     """
#     Custom RAG endpoint (no RetrievalQAChain).
#     Steps:
#       0. Optional: handle booking (if payload.booking is present) and store in DB.
#       1. Embed the query
#       2. Search Qdrant for top_k similar chunks
#       3. Build prompt with retrieved chunks and optional session memory
#       4. Call LLM service to generate answer
#       5. Save to memory (best-effort)
#       6. Return answer + sources
#     """
#     if not payload.query or not payload.query.strip():
#         raise HTTPException(status_code=400, detail="query is required")

#     # ---------- Optional booking handling ----------
#     if payload.booking:
#         try:
#             booking_info = payload.booking
#             booking_entry = Booking(
#                 session_id=payload.session_id,
#                 name=booking_info.get("name"),
#                 email=booking_info.get("email"),
#                 date=booking_info.get("date"),
#                 time=booking_info.get("time")
#             )
#             db.add(booking_entry)
#             db.commit()
#             db.refresh(booking_entry)

#             return ConversateResponse(
#                 answer=f"Booking confirmed for {booking_entry.name} on {booking_entry.date} at {booking_entry.time} ✅",
#                 round_trip_id=None,
#                 sources=[]
#             )
#         except Exception as e:
#             logger.exception("Failed to create booking")
#             raise HTTPException(status_code=500, detail=f"Booking creation failed: {e}")

#     top_k = payload.top_k if payload.top_k and payload.top_k > 0 else 4

#     # 1) Embed the query
#     try:
#         query_embedding = generate_embeddings([payload.query])[0]
#     except Exception as e:
#         logger.exception("Embedding generation failed")
#         raise HTTPException(status_code=500, detail=f"Embedding generation failed: {e}")

#     # 2) Search Qdrant
#     try:
#         search_results = qdrant_client.search(
#             collection_name="documents",
#             query_vector=query_embedding,
#             limit=top_k,
#             with_payload=True
#         )
#     except Exception as e:
#         logger.exception("Vector search failed")
#         raise HTTPException(status_code=500, detail=f"Vector search failed: {e}")

#     # 3) Collect retrieved chunks and metadata
#     context_chunks: List[str] = []
#     sources: List[SourceItem] = []

#     for item in search_results:
#         # Depending on Qdrant client version, payload may be item.payload or item.payload if attribute exists
#         payload_data = getattr(item, "payload", None)
#         if payload_data is None and hasattr(item, "payload"):
#             payload_data = item.payload
#         payload_data = payload_data or {}

#         # several possible keys based on ingestion: "chunk", "text"
#         chunk_text = payload_data.get("chunk") or payload_data.get("text") or ""
#         filename = payload_data.get("filename")
#         chunk_id = payload_data.get("chunk_id")
#         # score location may vary
#         score = getattr(item, "score", None) or (item.score if hasattr(item, "score") else None)

#         if chunk_text:
#             context_chunks.append(chunk_text)

#         snippet = (chunk_text[:250] + "...") if chunk_text and len(chunk_text) > 250 else chunk_text

#         sources.append(
#             SourceItem(
#                 filename=filename,
#                 chunk_id=int(chunk_id) if chunk_id is not None else None,
#                 score=float(score) if score is not None else None,
#                 chunk=snippet
#             )
#         )

#     # 4) Load session memory (if requested and available)
#     session_memory_text: Optional[str] = None
#     if payload.include_memory and payload.session_id and _memory_get:
#         try:
#             # memory getter may accept db (some implementations might)
#             session_memory_text = _memory_get(payload.session_id, db=db) if callable(_memory_get) else None
#             # ensure it's a string
#             if isinstance(session_memory_text, list):
#                 session_memory_text = "\n".join(session_memory_text)
#             elif session_memory_text is None:
#                 session_memory_text = None
#             else:
#                 session_memory_text = str(session_memory_text)
#         except Exception:
#             logger.exception("Failed to load session memory, continuing without memory")
#             session_memory_text = None

#     # 5) Build prompt (use only the chunk texts)
#     prompt = build_prompt(context_chunks, payload.query, session_memory=session_memory_text)

#     # 6) Call LLM
#     try:
#         llm_answer = generate_response(prompt)
#         if isinstance(llm_answer, dict) and "text" in llm_answer:
#             llm_text = llm_answer["text"]
#         else:
#             llm_text = str(llm_answer)
#     except Exception as e:
#         logger.exception("LLM call failed")
#         raise HTTPException(status_code=500, detail=f"LLM call failed: {e}")

#     # 7) Save user query + assistant response into memory (best-effort)
#     if payload.session_id and _memory_save:
#         try:
#             # _memory_save expected signature: (session_id, message: dict, db=...)
#             # we adapt for both variants: memory_service expects (session_id, {"role":..., "text":...}, db=...), 
#             # fallback _memory_save wraps redis save which expects (session_id, role, text)
#             _memory_save(payload.session_id, {"role": "user", "text": payload.query}, db=db)
#             _memory_save(payload.session_id, {"role": "assistant", "text": llm_text}, db=db)
#         except Exception:
#             logger.exception("Failed to save messages to memory (continuing)")

#     # 8) Return structured response
#     response = ConversateResponse(
#         answer=llm_text,
#         round_trip_id=None,
#         sources=sources
#     )

#     return response






# # app/api/conversate.py

# from fastapi import APIRouter
# from pydantic import BaseModel
# from app.services.conversate_service import ConversateService

# router = APIRouter()
# service = ConversateService()

# class ChatRequest(BaseModel):
#     session_id: str
#     message: str

# @router.post("/conversate")
# def conversate(data: ChatRequest):
#     return service.handle_conversation(
#         session_id=data.session_id,
#         user_message=data.message
#     )








# # app/api/conversate.py
# from fastapi import APIRouter, HTTPException
# from pydantic import BaseModel
# from typing import Optional

# from app.services.memory_service import MemoryService
# from app.services.rag_service import RAGService
# from app.services.llm_service import LLMService
# from app.services.intent_service import IntentService


# router = APIRouter()

# class ConversateRequest(BaseModel):
#     user_id: str
#     message: str
#     reset: Optional[bool] = False  # if true, clear conversation memory

# class ConversateResponse(BaseModel):
#     reply: str
#     intent: Optional[str] = None
#     confidence: Optional[float] = None

# # instantiate services (they read env on import)
# memory = MemoryService()
# rag = RAGService()
# llm = LLMService()
# intent = IntentService()

# @router.post("/converse", response_model=ConversateResponse)
# async def converse(req: ConversateRequest):
#     try:
#         if req.reset:
#             memory.clear_conversation(req.user_id)

#         # 1. store user message in memory (short-term)
#         memory.append_user_message(req.user_id, req.message)

#         # 2. intent detection
#         detected_intent, confidence = intent.detect_intent(req.user_id, req.message)

#         # 3. run RAG: get top context chunks from Qdrant
#         context_blocks = rag.get_relevant_contexts(req.message, top_k=3)

#         # 4. call LLM with memory + context
#         convo_history = memory.get_conversation(req.user_id)
#         reply = llm.generate_reply(
#             user_id=req.user_id,
#             user_message=req.message,
#             context_blocks=context_blocks,
#             history=convo_history,
#             detected_intent=detected_intent
#         )

#         # 5. append assistant reply to memory
#         memory.append_assistant_message(req.user_id, reply)

#         # If intent is interview booking and confidence high, you can trigger booking flow (example)
#         # (You can implement booking logic in intent_service or external endpoint)
#         return ConversateResponse(reply=reply, intent=detected_intent, confidence=confidence)
#     except Exception as e:
#         raise HTTPException(status_code=500, detail=str(e))
