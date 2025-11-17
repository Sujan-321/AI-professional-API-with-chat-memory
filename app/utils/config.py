import os
from dotenv import load_dotenv

load_dotenv()

# Environment variables
QDRANT_URL = os.getenv("QDRANT_URL", "http://localhost:6333")
REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
REDIS_PORT = int(os.getenv("REDIS_PORT", 6379))
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
