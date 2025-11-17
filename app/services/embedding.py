# app/services/embedding.py
from sentence_transformers import SentenceTransformer
from typing import List

# Load the embedding model once
model = SentenceTransformer("all-MiniLM-L6-v2")

def generate_embeddings(chunks: List[str]) -> List[List[float]]:
    """
    Generate embeddings for a list of text chunks.
    """
    return model.encode(chunks).tolist()
