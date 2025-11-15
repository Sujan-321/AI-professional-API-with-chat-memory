from fastapi import APIRouter
from app.services.vector_db import create_collection, insert_sample_vector

router = APIRouter()

@router.get("/qdrant/setup")
def setup_qdrant():
    create_collection()
    result = insert_sample_vector()
    return {"message": "Qdrant working fine!", "detail": result}
