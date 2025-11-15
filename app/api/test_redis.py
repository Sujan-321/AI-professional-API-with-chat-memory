from fastapi import APIRouter
from app.services.chat_memory import save_message, get_chat_history

router = APIRouter()

@router.get("/redis/test")
def test_redis():
    session_id = "test_session"
    save_message(session_id, "user", "Hello Redis!")
    save_message(session_id, "assistant", "Hi user")
    history = get_chat_history(session_id)
    return {"message": "Redis connected successfully!", "history": history}
