import os
from fastapi import APIRouter, UploadFile, File, Form
from sqlalchemy.orm import Session

from app.services.text_extraction import extract_text_from_pdf, extract_text_from_txt
from app.services.chunking import fixed_length_chunking, paragraph_chunking
from app.services.embedding import generate_embeddings
from app.services.vector_db import client
from app.db.database import SessionLocal
from app.db.models import Document


from qdrant_client.http import models

router = APIRouter()

UPLOAD_DIR = "uploaded_docs"
os.makedirs(UPLOAD_DIR, exist_ok=True)


# Dependency to get DB session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.post("/upload")
async def upload_document(
    file: UploadFile = File(...),
    chunk_strategy: str = Form("fixed")
):
    """
    1. Upload PDF/TXT
    2. Extract text
    3. Chunk text (fixed or paragraph)
    4. Generate embeddings
    5. Store vectors in Qdrant
    6. Save metadata (chunks + vector IDs) in SQLite
    """

    # ------------------------------
    # 1. Save uploaded file locally
    # ------------------------------
    file_path = os.path.join(UPLOAD_DIR, file.filename)
    with open(file_path, "wb") as f:
        f.write(await file.read())

    # ------------------------------
    # 2. Extract text
    # ------------------------------
    if file.filename.endswith(".pdf"):
        text = extract_text_from_pdf(file_path)
        filetype = "pdf"
    elif file.filename.endswith(".txt"):
        text = extract_text_from_txt(file_path)
        filetype = "txt"
    else:
        return {"error": "Unsupported file type. Only PDF and TXT are allowed."}

    if not text.strip():
        return {"error": "No readable text found in document."}

    # ------------------------------
    # 3. Chunk text
    # ------------------------------
    if chunk_strategy == "fixed":
        chunks = fixed_length_chunking(text)
    else:
        chunks = paragraph_chunking(text)

    if len(chunks) == 0:
        return {"error": "Chunking produced 0 chunks. Document might be empty."}

    # ------------------------------
    # 4. Generate embeddings
    # ------------------------------
    embeddings = generate_embeddings(chunks)
    if len(embeddings) != len(chunks):
        return {"error": "Embedding count mismatch!"}

    # ------------------------------
    # 5. Store embeddings in Qdrant
    # ------------------------------
    vector_ids = []
    points = []

    for i in range(len(chunks)):
        vector_id = i  # You can generate UUID too
        vector_ids.append(vector_id)

        points.append(
            models.PointStruct(
                id=vector_id,
                vector=embeddings[i],
                payload={
                    "chunk": chunks[i],
                    "filename": file.filename,
                    "chunk_id": i
                }
            )
        )

    # Push to Qdrant
    client.upsert(collection_name="documents", points=points)

    # ------------------------------
    # 6. Save metadata in SQLite
    # ------------------------------
    db: Session = SessionLocal()

    doc_entry = Document(
        filename=file.filename,
        filetype=filetype,
        chunk_strategy=chunk_strategy,
        number_of_chunks=len(chunks),
        vector_ids=str(vector_ids)  # Store list as string or JSON
    )

    db.add(doc_entry)
    db.commit()
    db.refresh(doc_entry)
    db.close()

    # ------------------------------
    # Return
    # ------------------------------
    return {
        "message": "Document uploaded and processed successfully.",
        "filename": file.filename,
        "filetype": filetype,
        "total_chunks": len(chunks),
        "document_id": doc_entry.id,
        "vector_ids": vector_ids
    }
















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
