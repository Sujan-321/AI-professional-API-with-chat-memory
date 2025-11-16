# app/services/conversate_service.py

from app.services.intent_service import IntentService
from app.services.rag_service import RAGService
from app.services.llm_service import LLMService
from app.services.chat_memory import save_message, get_chat_history


class ConversateService:

    def __init__(self):
        self.intent_service = None
        self.rag_service = None
        self.llm = None

    def get_intent_service(self):
        if self.intent_service is None:
            self.intent_service = IntentService()
        return self.intent_service

    def get_rag_service(self):
        if self.rag_service is None:
            self.rag_service = RAGService()
        return self.rag_service

    def get_llm(self):
        if self.llm is None:
            self.llm = LLMService()
        return self.llm

    def build_prompt(self, intent, history, context, user_message):
        prompt = f"""
            You are an AI assistant.

            Intent: {intent}

            Conversation history:
            {history}

            Relevant document context:
            {context}

            User message:
            {user_message}

            Using the above information, generate the best possible answer.
            """

        return prompt

    def handle_conversation(self, session_id: str, user_message: str):

        intent = self.get_intent_service().detect_intent(user_message)

        history_list = get_chat_history(session_id)
        history = "\n".join(history_list)

        context = ""
        if intent in ["document_query", "general_query"]:
            context = self.get_rag_service().search(user_message)

        prompt = self.build_prompt(intent, history, context, user_message)

        reply = self.get_llm().generate(prompt)

        save_message(session_id, "user", user_message)
        save_message(session_id, "assistant", reply)

        return {
            "intent": intent,
            "reply": str(reply),
            "context_used": str(context)[:200] + "..." if context else "None",
        }


