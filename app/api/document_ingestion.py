# app/api/document_ingestion.py
from typing import Literal, List
import os
import json
import uuid
from fastapi import APIRouter, UploadFile, File, Form, Depends, HTTPException
from sqlalchemy.orm import Session

from app.services.text_extraction import extract_text_from_pdf, extract_text_from_txt
from app.services.chunking import fixed_length_chunking, paragraph_chunking
from app.services.embedding import generate_embeddings
from app.services.vector_db import upsert_vectors  # expects function to upsert list of PointStruct
from app.db.database import get_db
from app.db.models import Document
from qdrant_client.http import models as qdrant_models

router = APIRouter()
UPLOAD_DIR = "uploaded_docs"
os.makedirs(UPLOAD_DIR, exist_ok=True)


@router.post("/upload")
async def upload_document(
    file: UploadFile = File(...),
    chunk_strategy: Literal["fixed", "paragraph"] = Form("fixed"),
    db: Session = Depends(get_db),
):
    """
    Document ingestion pipeline:
      - Save file
      - Extract text (.pdf or .txt)
      - Chunk (fixed word-size or paragraph)
      - Create embeddings for chunks
      - Upsert vectors to Qdrant
      - Persist metadata in SQLite (Document model)
    """
    # 1) Save uploaded file locally
    file_path = os.path.join(UPLOAD_DIR, file.filename)
    with open(file_path, "wb") as fh:
        fh.write(await file.read())

    # 2) Extract text
    filename_lower = file.filename.lower()
    if filename_lower.endswith(".pdf"):
        text = extract_text_from_pdf(file_path)
        filetype = "pdf"
    elif filename_lower.endswith(".txt"):
        text = extract_text_from_txt(file_path)
        filetype = "txt"
    else:
        raise HTTPException(status_code=400, detail="Unsupported file type. Only .pdf and .txt allowed.")

    if not text or not text.strip():
        raise HTTPException(status_code=400, detail="No readable text found in document.")

    # 3) Chunk text
    if chunk_strategy == "fixed":
        chunks: List[str] = fixed_length_chunking(text)
    else:
        chunks = paragraph_chunking(text)

    if not chunks:
        raise HTTPException(status_code=400, detail="Chunking produced 0 chunks. Document may be empty.")

    # 4) Generate embeddings
    try:
        embeddings = generate_embeddings(chunks)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Embedding generation failed: {e}")

    if len(embeddings) != len(chunks):
        raise HTTPException(status_code=500, detail="Embedding count mismatch with chunks.")

    # 5) Create DB document entry first so we have an id
    doc = Document(
        filename=file.filename,
        filetype=filetype,
        chunk_strategy=chunk_strategy,
        number_of_chunks=len(chunks),
        vector_ids="[]",
    )
    db.add(doc)
    db.commit()
    db.refresh(doc)

    # 6) Prepare PointStructs for Qdrant and generate stable vector ids
    points: List[qdrant_models.PointStruct] = []
    vector_ids: List[str] = []
    collection_name = "documents"

    for idx, (chunk_text, vector) in enumerate(zip(chunks, embeddings)):
        # stable unique id: <docid>_<chunk_idx>_<uuid8>
        # vector_id = f"{doc.id}_{idx}_{uuid.uuid4().hex[:8]}"
        vector_id = str(uuid.uuid4())

        vector_ids.append(vector_id)

        payload = {
            "chunk": chunk_text,
            "filename": file.filename,
            "chunk_id": idx,
            "document_id": doc.id,
        }

        points.append(
            qdrant_models.PointStruct(
                id=vector_id,
                vector=vector,
                payload=payload,
            )
        )

    # 7) Upsert to Qdrant
    try:
        upsert_vectors(collection_name=collection_name, points=points)
    except Exception as e:
        # If upsert fails, keep DB entry but inform user
        raise HTTPException(status_code=500, detail=f"Qdrant upsert failed: {e}")

    # 8) Update DB with vector ids JSON and return response
    doc.vector_ids = json.dumps(vector_ids)
    db.add(doc)
    db.commit()
    db.refresh(doc)

    return {
        "message": "Document uploaded and processed successfully.",
        "document_id": doc.id,
        "filename": doc.filename,
        "filetype": doc.filetype,
        "chunk_strategy": doc.chunk_strategy,
        "total_chunks": doc.number_of_chunks,
        "vector_ids": vector_ids,
    }