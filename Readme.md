# 🚀 RAG Backend with FastAPI, Qdrant, Redis & LLM

This project implements a **production‑grade Retrieval‑Augmented Generation (RAG) backend** using FastAPI. It was developed as a hiring task and fulfills all requirements, including document ingestion, vector storage, multi‑turn chat, and interview booking.

---

# 📌 **Features**

## ✅ 1. Document Ingestion API

* Upload **PDF** or **TXT** files
* Extract text (PDF/TXT supported)
* Two chunking strategies:

  * **fixed** (word‑based)
  * **paragraph** (newline/paragraph based)
* Generate embeddings using **Sentence Transformers (all‑MiniLM‑L6‑v2)**
* Store vectors in **Qdrant** with metadata
* Store document info in **SQLite**

## ✅ 2. Conversational RAG API

* Custom RAG (**no RetrievalQAChain**)
* Multi‑turn conversation memory stored in **Redis**
* Retrieves top chunks from Qdrant
* Builds custom prompt with context
* Uses LLM (Groq/OpenAI/etc.) for final answer
* Stores conversation history in Redis
* Fully stateless backend except for DB + Redis

## ✅ 3. Interview Booking

* User can provide name, email, date, time
* API saves booking in **SQLite (Booking model)**
* Returns confirmation message via LLM or direct logic

## 🔒 Constraints (All Followed)

* ❌ No FAISS
* ❌ No Chroma
* ❌ No RetrievalQAChain
* ❌ No UI required
* ✔ Clean modular architecture
* ✔ Proper typing & structure

---

# 🏗 **Project Architecture**

```
app/
 ├── api/
 │    ├── document_ingestion.py
 │    └── conversate.py
 │
 ├── services/
 │    ├── chunking.py
 │    ├── embedding.py
 │    ├── rag_service.py
 │    ├── text_extraction.py
 │    └── vector_db.py
 │
 ├── db/
 │    ├── database.py
 │    └── models.py
 │
 └── utils/
      ├── config.py
      └── redis_client.py

main.py
requirements.txt
```

---

# 📥 **Document Ingestion API**

`POST /api/doc/upload`

### **Form‑data fields:**

* `file`: PDF or TXT file
* `chunk_strategy`: `fixed` or `paragraph`

### **Response example:**

```json
{
  "message": "Document uploaded and processed successfully.",
  "document_id": 4,
  "filename": "universe.txt",
  "filetype": "txt",
  "chunk_strategy": "fixed",
  "total_chunks": 1,
  "vector_ids": ["ac905921-07ce-4a79-b806-94cc2c9b73ef"]
}
```

---

# 💬 **Conversational RAG API**

`POST /api/conversate`

### **Request Body:**

```json
{
  "session_id": "123",
  "query": "How was the universe formed?",
  "top_k": 4
}
```

### **Features during conversation**

* Retrieves relevant document chunks
* Includes previous conversation context (Redis)
* Builds custom prompt
* Sends to LLM
* Saves back conversation

### **Response Example:**

```json
{
  "answer": "The universe formed after...",
  "sources": [ { "chunk": "...", "filename": "universe.txt" } ]
}
```

---

# 📆 **Interview Booking Support**

### **Request Body:**

```json
{
  "session_id": "12345",
  "booking": {
    "name": "Sujan",
    "email": "sujan@mail.com",
    "date": "2025-01-10",
    "time": "14:00"
  }
}
```

### **Response:**

```json
{
  "answer": "Booking confirmed for Sujan on 2025-01-10 at 14:00 ✅",
  "sources": []
}
```

---

# 🧩 Chunking Strategies

### **1. Fixed Chunking**

* 200–300 word slices
* Best for dense text

### **2. Paragraph Chunking**

* Split by blank lines
* Best for knowledge documents

Both methods are selectable via API.

---

# 🧠 Embeddings

Uses:

```
sentence-transformers/all-MiniLM-L6-v2 (384-dim)
```

Stored in Qdrant with metadata:

```
filename
chunk text
chunk_id
document_id
```

---

# 🗄 Qdrant Vector Store

Collection name: `documents`

Vector schema:

* size = 384
* distance = COSINE

Upsert uses `PointStruct` with UUID-based IDs.

---

# 🧱 Redis (Conversation Memory)

Memory is stored per session:

```
session:<session_id>:history
```

Used for multi-turn chat.

---

# 🛠 Installation

### 1 Clone repo

```
git clone <repo-url>
cd project-folder
```

### 2 Create virtual environment

```
python -m venv venv
source venv/bin/activate     # Linux/macOS
venv\Scripts\activate       # Windows
```
![Image Alt](https://github.com/Sujan-321/AI-professional-API-with-chat-memory/blob/e6762b1c3dd37dcdc375de7bf9118148aef4759e/images/activateEnvironment.JPG)

### 3 Install dependencies

```
pip install -r requirements.txt
```

### 4 Start Qdrant

```
docker run -d --name qdrant -p 6333:6333 qdrant/qdrant
docker run -d -p 6379:6379 redis
```
![Image Alt](https://github.com/Sujan-321/AI-professional-API-with-chat-memory/blob/e5445c795fcb1388fe575f31ba4ac682a31ce56a/images/RedisAndQdrant.JPG)


### 5 Run FastAPI

```
uvicorn main:app --reload
```
![Image Alt](https://github.com/Sujan-321/AI-professional-API-with-chat-memory/blob/e5445c795fcb1388fe575f31ba4ac682a31ce56a/images/RunApp.JPG)

### 6 Create .env file in root directory with following

```
GROQ_API_KEY=Your-api-key-here
OPENAI_CHAT_MODEL=gpt-4o-mini   
OPENAI_EMBED_MODEL=text-embedding-3-small
QDRANT_URL=http://localhost:6333
QDRANT_COLLECTION=documents
REDIS_HOST=localhost
REDIS_PORT=6379
```

### 7 Run backend

```
open browser and run : 127.0.0.1:8000
```
![Image Alt](https://github.com/Sujan-321/AI-professional-API-with-chat-memory/blob/e5445c795fcb1388fe575f31ba4ac682a31ce56a/images/step%204%20check%20localhost%20for%20backend%20running.JPG)


### 8 Upload the document

```
open postman and run : 127.0.0.1:8000/api/doc/upload
```
![Image Alt](https://github.com/Sujan-321/AI-professional-API-with-chat-memory/blob/e5445c795fcb1388fe575f31ba4ac682a31ce56a/images/step%205%20upload%20document%20in%20postman.JPG)



### 9 Upload file with chunkstrategy:paragraph

```
open postman and run : 127.0.0.1:8000/api/doc/upload
```
![Image Alt](https://github.com/Sujan-321/AI-professional-API-with-chat-memory/blob/e5445c795fcb1388fe575f31ba4ac682a31ce56a/images/step%205a%20upload%20file%20with%20chunkstrategy%20paragraph.JPG)


### 10 Upload file with chunkstrategy:fixed

```
open postman and run : 127.0.0.1:8000/api/doc/upload
```
![Image Alt](https://github.com/Sujan-321/AI-professional-API-with-chat-memory/blob/e5445c795fcb1388fe575f31ba4ac682a31ce56a/images/step%205b%20upload%20file%20with%20chunk%20strategy.JPG)


### 11 Chat with bot

```
open postman and run : 127.0.0.1:8000/api/conversate
```
![Image Alt](https://github.com/Sujan-321/AI-professional-API-with-chat-memory/blob/e5445c795fcb1388fe575f31ba4ac682a31ce56a/images/step%205c%20conversationwith%20bot.JPG)


### 12 Bot can book inerview 

```
open postman and run : 127.0.0.1:8000/api/conversate
```
![Image Alt](https://github.com/Sujan-321/AI-professional-API-with-chat-memory/blob/e5445c795fcb1388fe575f31ba4ac682a31ce56a/images/step%206%20booking%20confirmed.JPG)



# 🧪 Testing

Visit Swagger:

```
http://localhost:8000/docs
```

Try:

* `/api/doc/upload`
* `/api/conversate`

---

# 🐞 Troubleshooting

### **Error: limit argument in Qdrant search**

Solution implemented:

* Automatic fallback for older Qdrant client

### **Document returns 0 chunks**

* Ensure file has readable text
* Check paragraph mode (requires blank lines)

---

# 🎯 Conclusion

This backend fully implements a modern RAG system with modular design, rich features, and production-ready architecture suitable for real business applications.

---

# 👨‍💻 Author

**Sujan Ghimire** — AI/ML Developer

---

# ⭐ Want to Improve?

Feel free to extend:

* Streaming responses
* Auth layer
* Support for DOCX
* Hybrid search (BM25 + vectors)
