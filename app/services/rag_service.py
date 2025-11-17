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



    # def search(self, query: str, limit: int = 5):
    #     vector = self.encoder.encode(query).tolist()

    #     results = self.client.search(
    #         collection_name=self.collection,
    #         query_vector=vector,
    #         limit=limit
    #     )

    #     hits = []
    #     for hit in results:
    #         payload = hit.payload or {}
    #         hits.append({
    #             "chunk": payload.get("chunk") or payload.get("text") or "",
    #             "filename": payload.get("filename"),
    #             "chunk_id": payload.get("chunk_id"),
    #             "score": hit.score
    #         })

    #     return hits








# # app/services/rag_service.py
# import os
# from typing import List, Dict, Any
# from dotenv import load_dotenv
# load_dotenv()

# from qdrant_client import QdrantClient
# from qdrant_client.http import models as qmodels
# import openai

# OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
# OPENAI_MODEL_EMBED = os.getenv("OPENAI_EMBED_MODEL", "text-embedding-3-small")
# QDRANT_URL = os.getenv("QDRANT_URL", "http://localhost:6333")
# QDRANT_API_KEY = os.getenv("QDRANT_API_KEY", None)
# QDRANT_COLLECTION = os.getenv("QDRANT_COLLECTION", "documents")

# openai.api_key = OPENAI_API_KEY

# class RAGService:
#     def __init__(self):
#         # Connect to Qdrant (assumes Qdrant is running and collection exists)
#         if QDRANT_API_KEY:
#             self.client = QdrantClient(url=QDRANT_URL, api_key=QDRANT_API_KEY)
#         else:
#             # If using local qdrant without api_key:
#             self.client = QdrantClient(url=QDRANT_URL)

#         self.collection = QDRANT_COLLECTION

#     def _embed(self, text: str) -> List[float]:
#         # Use OpenAI embeddings
#         resp = openai.Embedding.create(model=OPENAI_MODEL_EMBED, input=text)
#         return resp["data"][0]["embedding"]

#     def get_relevant_contexts(self, query: str, top_k: int = 3) -> List[Dict[str, Any]]:
#         """
#         Returns a list of top_k context dicts from Qdrant.
#         Each dict may contain: {id, score, payload (text, metadata)}
#         """
#         emb = self._embed(query)

#         search_result = self.client.search(
#             collection_name=self.collection,
#             query_vector=emb,
#             limit=top_k,
#             with_payload=True,
#             with_vectors=False
#         )

#         contexts = []
#         for hit in search_result:
#             # Qdrant hit has: id, score, payload
#             payload = hit.payload or {}
#             text = None
#             # try common payload fields
#             for k in ["text", "content", "page_text", "body"]:
#                 if k in payload:
#                     text = payload[k]
#                     break
#             if text is None:
#                 # fallback: try any string in payload
#                 for v in payload.values():
#                     if isinstance(v, str):
#                         text = v
#                         break

#             contexts.append({
#                 "id": hit.id,
#                 "score": hit.score,
#                 "text": text,
#                 "payload": payload
#             })
#         return contexts
