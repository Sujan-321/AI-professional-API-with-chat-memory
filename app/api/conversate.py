# app/api/conversate.py

from fastapi import APIRouter
from pydantic import BaseModel
from app.services.conversate_service import ConversateService

router = APIRouter()
service = ConversateService()

class ChatRequest(BaseModel):
    session_id: str
    message: str

@router.post("/conversate")
def conversate(data: ChatRequest):
    return service.handle_conversation(
        session_id=data.session_id,
        user_message=data.message
    )








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
