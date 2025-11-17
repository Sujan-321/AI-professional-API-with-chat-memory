# app/utils/redis_client.py
import os
from dotenv import load_dotenv
import redis

load_dotenv()

REDIS_URL = os.getenv("REDIS_URL")
REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
REDIS_PORT = int(os.getenv("REDIS_PORT", 6379))
REDIS_DB = int(os.getenv("REDIS_DB", 0))
REDIS_PASSWORD = os.getenv("REDIS_PASSWORD", None)

_redis_client = None

def get_redis_client():
    global _redis_client
    if _redis_client is None:
        if REDIS_URL:
            _redis_client = redis.from_url(REDIS_URL, decode_responses=True)
        else:
            _redis_client = redis.Redis(
                host=REDIS_HOST,
                port=REDIS_PORT,
                db=REDIS_DB,
                password=REDIS_PASSWORD,
                decode_responses=True
            )
    return _redis_client

def get_chat_history(session_id: str) -> list[str]:
    client = get_redis_client()
    return client.lrange(f"chat:{session_id}", 0, -1) or []

def save_message(session_id: str, role: str, message: str):
    client = get_redis_client()
    client.rpush(f"chat:{session_id}", f"{role}: {message}")

def clear_chat_history(session_id: str):
    client = get_redis_client()
    client.delete(f"chat:{session_id}")
