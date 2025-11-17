# app/services/vector_db.py
from qdrant_client import QdrantClient
from qdrant_client.http import models
from app.utils.config import QDRANT_URL

# Initialize Qdrant client
client = QdrantClient(url=QDRANT_URL)

def upsert_vectors(collection_name: str, points: list[models.PointStruct]):
    """
    Insert embeddings and metadata into Qdrant collection.
    """
    client.upsert(collection_name=collection_name, points=points)


# Create a collection (like a table for vectors)
def create_collection():
    client.recreate_collection(
        collection_name="documents",
        vectors_config=models.VectorParams(size=384, distance=models.Distance.COSINE),
    )
    return {"status": "collection created"}

# Add a sample vector (later will store embeddings here)
def insert_sample_vector():
    client.upsert(
        collection_name="documents",
        points=[
            models.PointStruct(
                id=1,
                vector=[0.1] * 384,
                payload={"text": "Hello Qdrant!"}
            )
        ]
    )
    return {"status": "vector inserted"}
