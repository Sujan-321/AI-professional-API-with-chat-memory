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












# import os
# from fastapi import APIRouter, UploadFile, File, Form
# from sqlalchemy.orm import Session

# from app.services.text_extraction import extract_text_from_pdf, extract_text_from_txt
# from app.services.chunking import fixed_length_chunking, paragraph_chunking
# from app.services.embedding import generate_embeddings
# from app.services.vector_db import client
# from app.db.database import SessionLocal
# from app.db.models import Document


# from qdrant_client.http import models

# router = APIRouter()

# UPLOAD_DIR = "uploaded_docs"
# os.makedirs(UPLOAD_DIR, exist_ok=True)


# # Dependency to get DB session
# def get_db():
#     db = SessionLocal()
#     try:
#         yield db
#     finally:
#         db.close()


# @router.post("/upload")
# async def upload_document(
#     file: UploadFile = File(...),
#     chunk_strategy: str = Form("fixed")
# ):
#     """
#     1. Upload PDF/TXT
#     2. Extract text
#     3. Chunk text (fixed or paragraph)
#     4. Generate embeddings
#     5. Store vectors in Qdrant
#     6. Save metadata (chunks + vector IDs) in SQLite
#     """

#     # ------------------------------
#     # 1. Save uploaded file locally
#     # ------------------------------
#     file_path = os.path.join(UPLOAD_DIR, file.filename)
#     with open(file_path, "wb") as f:
#         f.write(await file.read())

#     # ------------------------------
#     # 2. Extract text
#     # ------------------------------
#     if file.filename.endswith(".pdf"):
#         text = extract_text_from_pdf(file_path)
#         filetype = "pdf"
#     elif file.filename.endswith(".txt"):
#         text = extract_text_from_txt(file_path)
#         filetype = "txt"
#     else:
#         return {"error": "Unsupported file type. Only PDF and TXT are allowed."}

#     if not text.strip():
#         return {"error": "No readable text found in document."}

#     # ------------------------------
#     # 3. Chunk text
#     # ------------------------------
#     if chunk_strategy == "fixed":
#         chunks = fixed_length_chunking(text)
#     else:
#         chunks = paragraph_chunking(text)

#     if len(chunks) == 0:
#         return {"error": "Chunking produced 0 chunks. Document might be empty."}

#     # ------------------------------
#     # 4. Generate embeddings
#     # ------------------------------
#     embeddings = generate_embeddings(chunks)
#     if len(embeddings) != len(chunks):
#         return {"error": "Embedding count mismatch!"}

#     # ------------------------------
#     # 5. Store embeddings in Qdrant
#     # ------------------------------
#     vector_ids = []
#     points = []

#     for i in range(len(chunks)):
#         vector_id = i  # You can generate UUID too
#         vector_ids.append(vector_id)

#         points.append(
#             models.PointStruct(
#                 id=vector_id,
#                 vector=embeddings[i],
#                 payload={
#                     "chunk": chunks[i],
#                     "filename": file.filename,
#                     "chunk_id": i
#                 }
#             )
#         )

#     # Push to Qdrant
#     client.upsert(collection_name="documents", points=points)

#     # ------------------------------
#     # 6. Save metadata in SQLite
#     # ------------------------------
#     db: Session = SessionLocal()

#     doc_entry = Document(
#         filename=file.filename,
#         filetype=filetype,
#         chunk_strategy=chunk_strategy,
#         number_of_chunks=len(chunks),
#         vector_ids=str(vector_ids)  # Store list as string or JSON
#     )

#     db.add(doc_entry)
#     db.commit()
#     db.refresh(doc_entry)
#     db.close()

#     # ------------------------------
#     # Return
#     # ------------------------------
#     return {
#         "message": "Document uploaded and processed successfully.",
#         "filename": file.filename,
#         "filetype": filetype,
#         "total_chunks": len(chunks),
#         "document_id": doc_entry.id,
#         "vector_ids": vector_ids
#     }
















# import os
# from fastapi import APIRouter, UploadFile, Form
# from app.services.text_extraction import extract_text_from_pdf, extract_text_from_txt
# from app.services.chunking import fixed_length_chunking, paragraph_chunking
# from app.services.embedding import generate_embeddings
# from app.services.vector_db import client
# from app.db.database import SessionLocal, Document
# from qdrant_client.http import models

# router = APIRouter()

# UPLOAD_DIR = "uploaded_docs"
# os.makedirs(UPLOAD_DIR, exist_ok=True)

# @router.post("/upload")
# async def upload_document(file: UploadFile, chunk_strategy: str = Form("fixed")):
#     # Save file
#     file_path = os.path.join(UPLOAD_DIR, file.filename)
#     with open(file_path, "wb") as f:
#         f.write(await file.read())

#     # Extract text
#     if file.filename.endswith(".pdf"):
#         text = extract_text_from_pdf(file_path)
#         filetype = "pdf"
#     elif file.filename.endswith(".txt"):
#         text = extract_text_from_txt(file_path)
#         filetype = "txt"
#     else:
#         return {"error": "Unsupported file type"}

#     # Chunk text
#     if chunk_strategy == "fixed":
#         chunks = fixed_length_chunking(text)
#     else:
#         chunks = paragraph_chunking(text)

#     # Generate embeddings
#     embeddings = generate_embeddings(chunks)

#     # Store embeddings in Qdrant
#     points = [
#         models.PointStruct(
#             id=i,
#             vector=embeddings[i],
#             payload={"chunk": chunks[i], "filename": file.filename}
#         )
#         for i in range(len(chunks))
#     ]
#     client.upsert(collection_name="documents", points=points)

#     # Save metadata in SQLite
#     db = SessionLocal()
#     doc_entry = Document(filename=file.filename, filetype=filetype, chunk_strategy=chunk_strategy)
#     db.add(doc_entry)
#     db.commit()
#     db.close()

#     return {"message": "Document uploaded and processed successfully", "total_chunks": len(chunks)}
