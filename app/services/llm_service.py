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