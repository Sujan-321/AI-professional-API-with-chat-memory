# app/services/memory_service.py
import os
from typing import List, Dict
from dotenv import load_dotenv
load_dotenv()

from app.utils.redis_client import get_redis_client

# settings
MAX_HISTORY_LEN = int(os.getenv("MAX_HISTORY_LEN", "10"))  # messages per user

class MemoryService:
    def __init__(self):
        self.redis = get_redis_client()

    def _key(self, user_id: str) -> str:
        return f"conv:{user_id}"

    def append_user_message(self, user_id: str, message: str):
        key = self._key(user_id)
        # store as JSON-like strings "role||message" to be simple
        self.redis.rpush(key, f"user||{message}")
        self.redis.ltrim(key, -MAX_HISTORY_LEN, -1)

    def append_assistant_message(self, user_id: str, message: str):
        key = self._key(user_id)
        self.redis.rpush(key, f"assistant||{message}")
        self.redis.ltrim(key, -MAX_HISTORY_LEN, -1)

    def get_conversation(self, user_id: str) -> List[Dict[str, str]]:
        key = self._key(user_id)
        raw = self.redis.lrange(key, 0, -1)
        convo = []
        for item in raw:
            if isinstance(item, bytes):
                item = item.decode()
            if "||" in item:
                role, msg = item.split("||", 1)
                convo.append({"role": role, "message": msg})
        return convo

    def clear_conversation(self, user_id: str):
        key = self._key(user_id)
        self.redis.delete(key)
