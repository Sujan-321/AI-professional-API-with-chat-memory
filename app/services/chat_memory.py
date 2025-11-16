import redis
from app.utils.config import REDIS_HOST, REDIS_PORT

# Create Redis client
redis_client = redis.Redis(
    host=REDIS_HOST,
    port=REDIS_PORT,
    decode_responses=False   # keep raw bytes so we decode manually
)

def save_message(session_id: str, role: str, message: str):
    redis_client.rpush(session_id, f"{role}:{message}")

def get_chat_history(session_id: str):
    history = redis_client.lrange(session_id, 0, -1)

    converted = []
    for item in history:
        if isinstance(item, bytes):
            converted.append(item.decode("utf-8", errors="ignore"))
        else:
            converted.append(str(item))

    return converted
