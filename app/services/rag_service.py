# app/services/rag_service.py

from qdrant_client import QdrantClient
from sentence_transformers import SentenceTransformer

class RAGService:
    def __init__(self):
        self.client = QdrantClient(url="http://localhost:6333")
        self.encoder = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")
        self.collection = "documents"

    def search(self, query: str, limit: int = 5):
        vector = self.encoder.encode(query).tolist()

        try:
            # Newer versions of Qdrant client (limit as keyword)
            results = self.client.search(
                collection_name=self.collection,
                query_vector=vector,
                limit=limit
            )
        except TypeError:
            # Older versions (limit as positional argument)
            results = self.client.search(
                collection_name=self.collection,
                query_vector=vector
            )[:limit]

        hits = []
        for hit in results:
            payload = hit.payload or {}
            hits.append({
                "chunk": payload.get("chunk") or payload.get("text") or "",
                "filename": payload.get("filename"),
                "chunk_id": payload.get("chunk_id"),
                "score": hit.score
            })

        return hits