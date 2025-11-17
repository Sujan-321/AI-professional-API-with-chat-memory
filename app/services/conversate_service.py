# app/services/conversate_service.py

from app.services.intent_service import IntentService
from app.services.rag_service import RAGService
from app.services.llm_service import LLMService
from app.utils.redis_client import save_message, get_chat_history

class ConversateService:

    def __init__(self):
        self.intent_service = IntentService()
        self.rag_service = RAGService()
        self.llm_service = LLMService()

    def build_prompt(self, intent, history, context, user_message):
        return f"""
You are an AI assistant.

Intent: {intent}

Conversation history:
{history or 'None'}

Relevant document context:
{context or 'None'}

User message:
{user_message}

Answer using the context. Cite excerpt numbers if used. If answer not in context, say you don't know.
"""

    def handle_conversation(self, session_id: str, user_message: str):
        intent = self.intent_service.detect_intent(user_message)

        history_list = get_chat_history(session_id)
        history = "\n".join(history_list)

        context = ""
        if intent in ["document_query", "general_query"]:
            context = self.rag_service.search(user_message)

        prompt = self.build_prompt(intent, history, context, user_message)
        reply = self.llm_service.generate(prompt)

        save_message(session_id, "user", user_message)
        save_message(session_id, "assistant", reply)

        return {
            "intent": intent,
            "reply": reply,
            "context_used": (context[:200] + "...") if context else "None",
        }