import os
from groq import Groq
from dotenv import load_dotenv

load_dotenv()

GROQ_API_KEY = os.getenv("GROQ_API_KEY")

if not GROQ_API_KEY:
    raise ValueError("GROQ_API_KEY is missing in .env file")

client = Groq(api_key=GROQ_API_KEY)

# ---------------------------
# Groq LLM Response Generator
# ---------------------------
def generate_response(user_message: str) -> str:
    """
    Sends user message to Groq Llama model and returns the response text.
    """
    response = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[
            {"role": "system", "content": "You are a helpful AI assistant."},
            {"role": "user", "content": user_message}
        ],
        max_tokens=200
    )

    return response.choices[0].message.content





# # app/services/llm_service.py
# import os
# from groq import Groq


# class LLMService:

#     def __init__(self):
#         self.client = Groq(api_key=os.getenv("GROQ_API_KEY"))

#     def generate(self, prompt: str):
#         response = self.client.chat.completions.create(
#             model="llama-3.1-8b-instant",
#             messages=[
#                 {"role": "user", "content": prompt}
#             ],
#             temperature=0.2
#         )

#         # FIXED LINE
#         return response.choices[0].message.content















# from openai import OpenAI
# import os
# from dotenv import load_dotenv
# load_dotenv()

# client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# class LLMService:
#     def generate(self, prompt: str) -> str:
#         response = client.chat.completions.create(
#             model="gpt-4o-mini",
#             messages=[
#                 {"role": "user", "content": prompt}
#             ]
#         )
#         return response.choices[0].message["content"]






# # app/services/llm_service.py
# import os
# from typing import List, Dict, Any, Optional
# from dotenv import load_dotenv
# load_dotenv()

# import openai
# OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
# OPENAI_CHAT_MODEL = os.getenv("OPENAI_CHAT_MODEL", "gpt-4o-mini")  # change as desired
# openai.api_key = OPENAI_API_KEY

# class LLMService:
#     def __init__(self):
#         self.model = OPENAI_CHAT_MODEL

#     def _build_system_prompt(self) -> str:
#         return (
#             "You are an intelligent assistant for PalmMind. Use the provided context from "
#             "documents and the recent conversation history to answer user queries. If the user "
#             "asks to book an interview, confirm details and ask for any missing information."
#         )

#     def _compose_messages(self,
#                           user_message: str,
#                           context_blocks: List[Dict[str, Any]],
#                           history: List[Dict[str, str]],
#                           detected_intent: Optional[str]) -> List[Dict[str, str]]:
#         messages = [{"role": "system", "content": self._build_system_prompt()}]

#         # append context as a system-level context chunk (kept separate)
#         if context_blocks:
#             ctx_texts = []
#             for i, ctx in enumerate(context_blocks, start=1):
#                 excerpt = ctx.get("text") or str(ctx.get("payload", {}))
#                 ctx_texts.append(f"[Context {i} | score={ctx.get('score')}] {excerpt}")
#             context_content = "Relevant documents:\n" + "\n\n".join(ctx_texts)
#             messages.append({"role": "system", "content": context_content})

#         # append conversation history
#         for m in history:
#             role = "user" if m["role"] == "user" else "assistant"
#             messages.append({"role": role, "content": m["message"]})

#         # now append current user message
#         messages.append({"role": "user", "content": user_message})

#         # small instruction if intent is booking
#         if detected_intent and detected_intent.lower().startswith("book"):
#             messages.append({"role": "system",
#                              "content": "User appears to want to book an interview. When replying, "
#                                         "ask necessary scheduling details (date/time, position) and "
#                                         "offer to confirm."})
#         return messages

#     def generate_reply(self,
#                        user_id: str,
#                        user_message: str,
#                        context_blocks: List[Dict[str, Any]],
#                        history: List[Dict[str, str]],
#                        detected_intent: Optional[str] = None) -> str:
#         messages = self._compose_messages(user_message, context_blocks, history, detected_intent)

#         # Call OpenAI Chat Completion API (ChatCompletion)
#         resp = openai.ChatCompletion.create(
#             model=self.model,
#             messages=messages,
#             max_tokens=512,
#             temperature=0.2
#         )
#         # Extract assistant message
#         assistant_msg = resp["choices"][0]["message"]["content"]
#         return assistant_msg
