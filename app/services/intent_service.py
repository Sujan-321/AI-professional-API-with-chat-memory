# app/services/intent_service.py

class IntentService:

    @staticmethod
    def detect_intent(user_message: str):
        text = user_message.lower()

        if any(w in text for w in ["hello", "hi", "hey"]):
            return "greeting"

        if any(w in text for w in ["book interview", "schedule", "interview"]):
            return "interview_booking"

        if any(w in text for w in ["document", "pdf", "file", "content"]):
            return "document_query"

        # default fallback
        return "general_query"