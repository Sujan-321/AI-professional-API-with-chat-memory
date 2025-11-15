import os
from fastapi import APIRouter, UploadFile, Form
from app.services.text_extraction import extract_text_from_pdf, extract_text_from_txt
from app.services.chunking import fixed_length_chunking, paragraph_chunking
from app.services.embedding import generate_embeddings
from app.services.vector_db import client
from app.db.database import SessionLocal, Document
from qdrant_client.http import models

router = APIRouter()

UPLOAD_DIR = "uploaded_docs"
os.makedirs(UPLOAD_DIR, exist_ok=True)

@router.post("/upload")
async def upload_document(file: UploadFile, chunk_strategy: str = Form("fixed")):
    # Save file
    file_path = os.path.join(UPLOAD_DIR, file.filename)
    with open(file_path, "wb") as f:
        f.write(await file.read())

    # Extract text
    if file.filename.endswith(".pdf"):
        text = extract_text_from_pdf(file_path)
        filetype = "pdf"
    elif file.filename.endswith(".txt"):
        text = extract_text_from_txt(file_path)
        filetype = "txt"
    else:
        return {"error": "Unsupported file type"}

    # Chunk text
    if chunk_strategy == "fixed":
        chunks = fixed_length_chunking(text)
    else:
        chunks = paragraph_chunking(text)

    # Generate embeddings
    embeddings = generate_embeddings(chunks)

    # Store embeddings in Qdrant
    points = [
        models.PointStruct(
            id=i,
            vector=embeddings[i],
            payload={"chunk": chunks[i], "filename": file.filename}
        )
        for i in range(len(chunks))
    ]
    client.upsert(collection_name="documents", points=points)

    # Save metadata in SQLite
    db = SessionLocal()
    doc_entry = Document(filename=file.filename, filetype=filetype, chunk_strategy=chunk_strategy)
    db.add(doc_entry)
    db.commit()
    db.close()

    return {"message": "Document uploaded and processed successfully", "total_chunks": len(chunks)}
