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













# # app/services/intent_service.py
# import os
# from typing import Tuple
# from dotenv import load_dotenv
# load_dotenv()

# # Simple keyword-based intent detection with confidence heuristic.
# BOOKING_KEYWORDS = ["book", "interview", "schedule", "appointment", "hire", "slot"]
# GREETING_KEYWORDS = ["hi", "hello", "hey", "good morning", "good evening"]
# CANCEL_KEYWORDS = ["cancel", "stop", "nevermind"]

# class IntentService:
#     def __init__(self):
#         pass

#     def detect_intent(self, user_id: str, text: str) -> Tuple[str, float]:
#         """
#         Returns (intent_name, confidence)
#         """
#         txt = (text or "").lower()
#         # exact heuristics
#         for kw in BOOKING_KEYWORDS:
#             if kw in txt:
#                 # strong signal for booking keywords
#                 return ("book_interview", 0.92)
#         for kw in CANCEL_KEYWORDS:
#             if kw in txt:
#                 return ("cancel", 0.9)
#         for kw in GREETING_KEYWORDS:
#             if kw in txt:
#                 return ("greeting", 0.75)

#         # default fallback
#         return ("unknown", 0.5)
