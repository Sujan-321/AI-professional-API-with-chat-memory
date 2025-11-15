from fastapi import FastAPI
from app.api import document_ingestion, test_qdrant, test_redis
from app.api import router as api_router
from app.api.test_redis import router as test_redis_router
from app.api.conversate import router as conversate_router
from dotenv import load_dotenv
load_dotenv()



app = FastAPI(title="Palm Mind Backend")

# Routers
app.include_router(conversate_router, prefix="/api")
app.include_router(api_router, prefix="/api")
app.include_router(test_qdrant.router, prefix="/api/test")
app.include_router(test_redis.router, prefix="/api/test")
app.include_router(document_ingestion.router, prefix="/api/doc")
app.include_router(test_redis_router)

@app.get("/")
def root():
    return {"message": "Backend running successfully 🚀"}
