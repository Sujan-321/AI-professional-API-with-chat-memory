from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session
import os
import logging

# local services (you already have these in your project)
from app.services.embedding import generate_embeddings
from app.services.vector_db import client as qdrant_client
from app.services.llm_service import generate_response  # your Groq wrapper
from app.db.database import get_db

# optional memory utilities (best-effort import)
try:
    from app.services.memory_service import save_message_to_memory, get_memory_for_session
except Exception:
    save_message_to_memory = None
    get_memory_for_session = None

router = APIRouter()

logger = logging.getLogger("conversate")
logger.setLevel(logging.INFO)

# ---------- Request / Response Schemas ----------
class ConversateRequest(BaseModel):
    session_id: Optional[str] = None
    query: str
    top_k: Optional[int] = 4
    include_memory: Optional[bool] = True
    # chunk retrieval mode: "semantic" (default) or "simple"
    mode: Optional[str] = "semantic"

class SourceItem(BaseModel):
    filename: Optional[str] = None
    chunk_id: Optional[int] = None
    score: Optional[float] = None
    chunk: Optional[str] = None

class ConversateResponse(BaseModel):
    answer: str
    round_trip_id: Optional[str] = None
    sources: List[SourceItem] = []

# ---------- Helper functions ----------
def build_prompt(context_chunks: List[str], user_query: str, session_memory: Optional[str]=None) -> str:
    """
    Builds a prompt to send to the LLM.
    Combines system instruction, optional session memory, retrieved context chunks, and the user question.
    """
    system_instruct = (
        "You are a helpful assistant that answers user questions using only the provided context. "
        "If the answer is not in the context, say you don't know and provide a short suggestion on how the user can find it."
    )

    parts = [system_instruct]

    if session_memory:
        parts.append("### Conversation memory (previous messages):")
        parts.append(session_memory)

    if context_chunks:
        parts.append("### Relevant document excerpts (use these to answer):")
        # limit size of each chunk included to avoid extremely long prompts
        for i, c in enumerate(context_chunks):
            parts.append(f"[EXCERPT {i+1}]\n{c}\n")

    parts.append("### User question:")
    parts.append(user_query)

    # final instruction
    parts.append(
        "### Instructions:\nAnswer concisely. If you quote or use facts, cite which excerpt number you used, e.g., [EXCERPT 1]."
    )

    prompt = "\n\n".join(parts)
    return prompt

# ---------- Main endpoint ----------
@router.post("/conversate", response_model=ConversateResponse)
def conversate_endpoint(payload: ConversateRequest, db: Session = Depends(get_db)):
    """
    Custom RAG endpoint (no RetrievalQAChain).
    Steps:
      1. Embed the query
      2. Search Qdrant
      3. Build prompt with top_k retrieved chunks
      4. Optionally include session memory
      5. Call LLM service to generate answer
      6. Save to memory (best-effort)
      7. Return answer + sources
    """
    if not payload.query or not payload.query.strip():
        raise HTTPException(status_code=400, detail="query is required")

    top_k = payload.top_k if payload.top_k and payload.top_k > 0 else 4

    # 1) Embed the query
    try:
        query_embedding = generate_embeddings([payload.query])[0]
    except Exception as e:
        logger.exception("Embedding generation failed")
        raise HTTPException(status_code=500, detail=f"Embedding generation failed: {e}")

    # 2) Search Qdrant
    try:
        # qdrant_client is expected to be a QdrantClient instance
        search_results = qdrant_client.search(
            collection_name="documents",
            query_vector=query_embedding,
            limit=top_k,
            with_payload=True
        )
    except Exception as e:
        logger.exception("Vector search failed")
        raise HTTPException(status_code=500, detail=f"Vector search failed: {e}")

    # 3) Collect retrieved chunks and metadata
    context_chunks = []
    sources: List[SourceItem] = []
    for item in search_results:
        # item.payload should include "chunk", "filename", "chunk_id" if your ingestion used that
        payload_data = getattr(item, "payload", None) or item.payload if hasattr(item, "payload") else {}
        chunk_text = payload_data.get("chunk") or payload_data.get("text") or ""
        filename = payload_data.get("filename")
        chunk_id = payload_data.get("chunk_id")
        score = getattr(item, "score", None) or item.score if hasattr(item, "score") else None

        if chunk_text:
            context_chunks.append(chunk_text)

        sources.append(
            SourceItem(
                filename=filename,
                chunk_id=chunk_id,
                score=score,
                chunk=(chunk_text[:250] + "...") if chunk_text else None
            )
        )

    # 4) Load session memory (if requested and available)
    session_memory_text = None
    if payload.include_memory and payload.session_id and get_memory_for_session:
        try:
            session_memory_text = get_memory_for_session(payload.session_id, db=db)  # your memory service may accept db
        except Exception:
            # If memory retrieval fails, keep going without it
            logger.exception("Failed to load session memory, continuing without memory")

    # 5) Build prompt
    prompt = build_prompt(context_chunks, payload.query, session_memory=session_memory_text)

    # 6) Call LLM (your generate_response should be a wrapper for Groq)
    try:
        # generate_response(prompt, session_id=None) signature depends on your llm_service implementation.
        # llm_answer = generate_response(prompt, session_id=payload.session_id if hasattr(generate_response, "__call__") else None)
        llm_answer = generate_response(prompt)

        # If your llm_service returns a dict like {"text": "..."} adapt accordingly.
        if isinstance(llm_answer, dict) and "text" in llm_answer:
            llm_text = llm_answer["text"]
        else:
            llm_text = str(llm_answer)
    except Exception as e:
        logger.exception("LLM call failed")
        raise HTTPException(status_code=500, detail=f"LLM call failed: {e}")

    # 7) Save user query + assistant response into memory (best-effort)
    if payload.session_id and save_message_to_memory:
        try:
            save_message_to_memory(payload.session_id, {"role": "user", "text": payload.query}, db=db)
            save_message_to_memory(payload.session_id, {"role": "assistant", "text": llm_text}, db=db)
        except Exception:
            logger.exception("Failed to save messages to memory (continuing)")

    # 8) Return structured response
    response = ConversateResponse(
        answer=llm_text,
        round_trip_id=None,
        sources=sources
    )

    return response





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
