# """
# backend_server.py
# ==================
# Standalone FastAPI server that exposes the RAG backend over HTTP.
# Run with: uvicorn backend_server:app --host 0.0.0.0 --port 7860 --reload

# Endpoints:
#   POST /chat        — main RAG query
#   POST /upload      — upload and index a document
#   GET  /health      — liveness check
#   POST /clear       — clear the in-memory vector store
# """

# import logging
# import os
# import tempfile
# from typing import Dict, List, Optional

# import uvicorn
# from fastapi import FastAPI, File, HTTPException, UploadFile
# from fastapi.middleware.cors import CORSMiddleware
# from pydantic import BaseModel

# import backend  # your existing backend.py — unchanged

# logging.basicConfig(level=logging.INFO)
# logger = logging.getLogger("backend_server")

# app = FastAPI(title="RAG Backend Server")

# app.add_middleware(
#     CORSMiddleware,
#     allow_origins=["*"],  # tighten this in production
#     allow_methods=["*"],
#     allow_headers=["*"],
# )

# # --------------------------------------------------------------------------
# # In-memory state (single process — sufficient for local/dev use)
# # --------------------------------------------------------------------------
# _llm = backend.create_llm()
# _vectorstore = None
# _indexed_files: List[str] = []


# # --------------------------------------------------------------------------
# # Request / Response schemas
# # --------------------------------------------------------------------------
# class ChatRequest(BaseModel):
#     question: str
#     chat_history: List[Dict[str, str]] = []
#     use_web_search: bool = False

# class ChatResponse(BaseModel):
#     answer: str
#     sources: List[str]

# class HealthResponse(BaseModel):
#     status: str
#     llm_reachable: bool
#     indexed_files: List[str]


# # --------------------------------------------------------------------------
# # Endpoints
# # --------------------------------------------------------------------------
# @app.get("/health", response_model=HealthResponse)
# def health():
#     return HealthResponse(
#         status="ok",
#         llm_reachable=backend.check_llm_health(),
#         indexed_files=_indexed_files,
#     )


# @app.post("/upload")
# async def upload_file(file: UploadFile = File(...)):
#     global _vectorstore

#     suffix = os.path.splitext(file.filename)[1]
#     with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
#         tmp.write(await file.read())
#         tmp_path = tmp.name

#     try:
#         _vectorstore = backend.process_uploaded_file(tmp_path, file.filename, _vectorstore)
#         _indexed_files.append(file.filename)
#         logger.info("Indexed file: %s", file.filename)
#         return {"status": "indexed", "filename": file.filename}
#     except Exception as e:
#         logger.error("Failed to index %s: %s", file.filename, e)
#         raise HTTPException(status_code=500, detail=str(e))
#     finally:
#         os.remove(tmp_path)


# @app.post("/chat", response_model=ChatResponse)
# def chat(req: ChatRequest):
#     try:
#         answer, sources = backend.generate_answer(
#             llm=_llm,
#             chat_history=req.chat_history,
#             vectorstore=_vectorstore,
#             question=req.question,
#             use_web_search=req.use_web_search,
#         )
#         return ChatResponse(answer=answer, sources=sources)
#     except Exception as e:
#         logger.error("Error during /chat: %s", e)
#         raise HTTPException(status_code=500, detail=str(e))


# @app.post("/clear")
# def clear():
#     global _vectorstore, _indexed_files
#     _vectorstore = None
#     _indexed_files = []
#     logger.info("Vector store cleared.")
#     return {"status": "cleared"}


# if __name__ == "__main__":
#     uvicorn.run("backend_server:app", host="0.0.0.0", port=7860, reload=True)








#----------------------------------updated from the claude to store the faiss index on disk and load it on startup----------------------------------





# """
# backend_server.py
# ==================
# Standalone FastAPI server with persistent FAISS vector store.
# Run with: python backend_server.py
# """

# import logging
# import os
# import tempfile
# from typing import Dict, List

# import uvicorn
# from fastapi import FastAPI, File, HTTPException, UploadFile
# from fastapi.middleware.cors import CORSMiddleware
# from pydantic import BaseModel

# import backend

# logging.basicConfig(level=logging.INFO)
# logger = logging.getLogger("backend_server")

# app = FastAPI(title="RAG Backend Server")

# app.add_middleware(
#     CORSMiddleware,
#     allow_origins=["*"],
#     allow_methods=["*"],
#     allow_headers=["*"],
# )

# # --------------------------------------------------------------------------
# # State — load from disk on startup if index exists
# # --------------------------------------------------------------------------
# _llm = backend.create_llm()
# _vectorstore = backend.load_vectorstore()          # loads from disk if exists
# _indexed_files: List[str] = []

# if _vectorstore is not None:
#     logger.info("Loaded existing FAISS index from disk: %s", backend.Config.VECTORSTORE_DIR)
# else:
#     logger.info("No existing FAISS index found — starting fresh.")


# # --------------------------------------------------------------------------
# # Schemas
# # --------------------------------------------------------------------------
# class ChatRequest(BaseModel):
#     question: str
#     chat_history: List[Dict[str, str]] = []
#     use_web_search: bool = False

# class ChatResponse(BaseModel):
#     answer: str
#     sources: List[str]

# class HealthResponse(BaseModel):
#     status: str
#     llm_reachable: bool
#     indexed_files: List[str]


# # --------------------------------------------------------------------------
# # Endpoints
# # --------------------------------------------------------------------------
# @app.get("/health", response_model=HealthResponse)
# def health():
#     return HealthResponse(
#         status="ok",
#         llm_reachable=backend.check_llm_health(),
#         indexed_files=_indexed_files,
#     )


# @app.post("/upload")
# async def upload_file(file: UploadFile = File(...)):
#     global _vectorstore

#     suffix = os.path.splitext(file.filename)[1]
#     with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
#         tmp.write(await file.read())
#         tmp_path = tmp.name

#     try:
#         _vectorstore = backend.process_uploaded_file(tmp_path, file.filename, _vectorstore)
#         _indexed_files.append(file.filename)

#         # Save to disk immediately after every upload
#         backend.save_vectorstore(_vectorstore)
#         logger.info("Indexed and saved: %s", file.filename)

#         return {"status": "indexed", "filename": file.filename}
#     except Exception as e:
#         logger.error("Failed to index %s: %s", file.filename, e)
#         raise HTTPException(status_code=500, detail=str(e))
#     finally:
#         os.remove(tmp_path)


# @app.post("/chat", response_model=ChatResponse)
# def chat(req: ChatRequest):
#     try:
#         answer, sources = backend.generate_answer(
#             llm=_llm,
#             chat_history=req.chat_history,
#             vectorstore=_vectorstore,
#             question=req.question,
#             use_web_search=req.use_web_search,
#         )
#         return ChatResponse(answer=answer, sources=sources)
#     except Exception as e:
#         logger.error("Error during /chat: %s", e)
#         raise HTTPException(status_code=500, detail=str(e))


# @app.post("/clear")
# def clear():
#     global _vectorstore, _indexed_files
#     _vectorstore = None
#     _indexed_files = []

#     # Also delete from disk
#     import shutil
#     if os.path.exists(backend.Config.VECTORSTORE_DIR):
#         shutil.rmtree(backend.Config.VECTORSTORE_DIR)
#         logger.info("Deleted FAISS index from disk.")

#     return {"status": "cleared"}


# if __name__ == "__main__":
#     uvicorn.run("backend_server:app", host="0.0.0.0", port=7860, reload=False)














#-------------------------------- the code is works like the above one but with some refactoring to support multiple conversations with separate vector stores on disk, and better error handling/logging. The frontend.py is also updated to work with the new backend_server.py structure.----------------------------------










"""
backend_server.py
==================
Standalone FastAPI server: serves the chat/RAG API *and* the static
HTML/CSS/JS frontend. Streamlit has been removed entirely - this single
process is now the whole web layer.

Run with: python backend_server.py
Requires a reachable PostgreSQL instance configured via .env (see
.env.example and docker-compose.yml for a quick local Postgres).

Redis is optional (for short-term message cache); if unavailable, falls
back to Postgres-only memory without breaking chat.
"""

import logging
import os
import shutil
import tempfile
from typing import Dict, List, Optional

import uvicorn
from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

import backend
import db
import memory_cache

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("backend_server")

app = FastAPI(title="RAG Backend Server")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# --------------------------------------------------------------------------
# Startup state
# --------------------------------------------------------------------------
_llm = backend.create_llm()
db.init_db()

# Per-conversation FAISS vector stores, loaded lazily from disk on first use
# and cached in memory afterwards (avoids re-reading the index file on every
# single chat turn for an active conversation).
_vectorstore_cache: Dict[str, object] = {}


def get_or_load_vectorstore(conversation_id: str):
    """Return the cached vector store for a conversation, loading it from
    disk on first access. Returns None if the conversation has no documents
    indexed yet - this is a normal, expected state, not an error."""
    if conversation_id in _vectorstore_cache:
        return _vectorstore_cache[conversation_id]

    path = backend.get_vectorstore_path(conversation_id)
    vs = backend.load_vectorstore(path)
    if vs is not None:
        _vectorstore_cache[conversation_id] = vs
        logger.info("Loaded FAISS index for conversation %s from disk", conversation_id)
    return vs


def set_vectorstore(conversation_id: str, vectorstore) -> None:
    _vectorstore_cache[conversation_id] = vectorstore


# --------------------------------------------------------------------------
# Schemas
# --------------------------------------------------------------------------
class ChatRequest(BaseModel):
    question: str
    conversation_id: Optional[str] = None


class ChatResponse(BaseModel):
    answer: str
    sources: List[str]
    conversation_id: str
    error: bool = False  # NEW: true if the LLM/pipeline failed this turn


class HealthResponse(BaseModel):
    status: str
    llm_reachable: bool
    database_reachable: bool


class ConversationOut(BaseModel):
    id: str
    title: str
    created_at: str
    updated_at: str


class MessageOut(BaseModel):
    role: str
    content: str
    created_at: str


class VectorstoreStatus(BaseModel):
    conversation_id: str
    loaded: bool
    embedding_model: str
    document_count: int
    chunk_count: int
    faiss_path: str


class DocumentOut(BaseModel):
    filename: str
    num_chunks: int
    uploaded_at: str


# --------------------------------------------------------------------------
# Health
# --------------------------------------------------------------------------
@app.get("/health", response_model=HealthResponse)
def health():
    db_ok = True
    try:
        db.list_conversations()
    except Exception as e:
        logger.error("Database health check failed: %s", e)
        db_ok = False

    return HealthResponse(
        status="ok",
        llm_reachable=backend.check_llm_health(),
        database_reachable=db_ok,
    )


# --------------------------------------------------------------------------
# Conversations
# --------------------------------------------------------------------------
@app.post("/conversations", response_model=ConversationOut)
def create_conversation():
    convo = db.create_conversation()
    return ConversationOut(
        id=str(convo.id),
        title=convo.title,
        created_at=convo.created_at.isoformat(),
        updated_at=convo.updated_at.isoformat(),
    )


@app.get("/conversations", response_model=List[ConversationOut])
def get_conversations():
    convos = db.list_conversations()
    return [
        ConversationOut(
            id=str(c.id),
            title=c.title,
            created_at=c.created_at.isoformat(),
            updated_at=c.updated_at.isoformat(),
        )
        for c in convos
    ]


@app.get("/conversations/{conversation_id}/messages", response_model=List[MessageOut])
def get_conversation_messages(conversation_id: str):
    convo = db.get_conversation(conversation_id)
    if convo is None:
        raise HTTPException(status_code=404, detail="Conversation not found")
    messages = db.get_messages(conversation_id)
    return [
        MessageOut(role=m.role, content=m.content, created_at=m.created_at.isoformat()) for m in messages
    ]


@app.get("/conversations/{conversation_id}/documents", response_model=List[DocumentOut])
def get_conversation_documents(conversation_id: str):
    convo = db.get_conversation(conversation_id)
    if convo is None:
        raise HTTPException(status_code=404, detail="Conversation not found")
    docs = db.list_documents(conversation_id)
    return [
        DocumentOut(filename=d.filename, num_chunks=d.num_chunks, uploaded_at=d.uploaded_at.isoformat())
        for d in docs
    ]


@app.delete("/conversations/{conversation_id}")
def delete_conversation(conversation_id: str):
    db.delete_conversation(conversation_id)
    _vectorstore_cache.pop(conversation_id, None)
    memory_cache.invalidate(conversation_id)

    path = backend.get_vectorstore_path(conversation_id)
    if os.path.exists(path):
        shutil.rmtree(path)
        logger.info("Deleted FAISS index for conversation %s", conversation_id)

    return {"status": "deleted"}


# --------------------------------------------------------------------------
# Upload (conversation-scoped - never blocks chat on failure)
# --------------------------------------------------------------------------
@app.post("/upload")
async def upload_file(file: UploadFile = File(...), conversation_id: str = Form(...)):
    convo = db.get_conversation(conversation_id)
    if convo is None:
        raise HTTPException(status_code=404, detail="Conversation not found")

    suffix = os.path.splitext(file.filename)[1]
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
        tmp.write(await file.read())
        tmp_path = tmp.name

    try:
        vectorstore = get_or_load_vectorstore(conversation_id)
        vectorstore, num_chunks = backend.process_uploaded_file(tmp_path, file.filename, vectorstore)
        set_vectorstore(conversation_id, vectorstore)

        path = backend.get_vectorstore_path(conversation_id)
        backend.save_vectorstore(vectorstore, path)
        db.add_document_record(conversation_id, file.filename, num_chunks)

        logger.info(
            "Indexed and saved '%s' for conversation %s (%d chunk(s))",
            file.filename,
            conversation_id,
            num_chunks,
        )
        return {"status": "indexed", "filename": file.filename, "chunks": num_chunks}
    except Exception as e:
        # Document processing failures must never break the chat experience -
        # the error is surfaced to the caller, but /chat keeps working
        # regardless (it never depends on a successful upload).
        logger.error("Failed to index %s for conversation %s: %s", file.filename, conversation_id, e)
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        os.remove(tmp_path)


# --------------------------------------------------------------------------
# Chat - always works, with or without documents; automatic web-search routing
# --------------------------------------------------------------------------
@app.post("/chat", response_model=ChatResponse)
def chat(req: ChatRequest):
    conversation_id = req.conversation_id
    is_error = False

    if conversation_id is None:
        convo = db.create_conversation(title="New Chat")
        conversation_id = str(convo.id)
    else:
        convo = db.get_conversation(conversation_id)
        if convo is None:
            raise HTTPException(status_code=404, detail="Conversation not found")

    db.add_message(conversation_id, "user", req.question)
    memory_cache.push_message(conversation_id, "user", req.question)

    # A missing or unreadable vector store must never stop the chat from
    # working - it just means there's no document context this turn.
    try:
        vectorstore = get_or_load_vectorstore(conversation_id)
    except Exception as e:
        logger.error("Failed to load vector store for %s, continuing without it: %s", conversation_id, e)
        vectorstore = None

    try:
        answer, sources = backend.generate_answer(
            llm=_llm,
            conversation_id=conversation_id,
            vectorstore=vectorstore,
            question=req.question,
        )
    except Exception as e:
        logger.error("Error during /chat: %s", e)
        answer = "I couldn't reach the model just now. Please try again in a moment."
        sources = []
        is_error = True

    db.add_message(conversation_id, "assistant", answer)
    memory_cache.push_message(conversation_id, "assistant", answer)
    db.touch_conversation(conversation_id)

    # Generate AI title after first exchange
    try:
        convo = db.get_conversation(conversation_id)

        if convo and (convo.title == "New Chat" or not convo.title):
            title = backend.generate_conversation_title(_llm, req.question, answer)
            db.update_conversation_title(conversation_id, title)

    except Exception as e:
        logger.error("Title generation failed (non-fatal): %s", e)

    try:
        backend.maybe_update_long_term_summary(_llm, conversation_id)
    except Exception as e:
        logger.error("Long-term summary update failed (non-fatal): %s", e)

    return ChatResponse(
        answer=answer,
        sources=sources,
        conversation_id=conversation_id,
        error=is_error,
    )


# --------------------------------------------------------------------------
# Vector store status
# --------------------------------------------------------------------------
@app.get("/vectorstore/status", response_model=VectorstoreStatus)
def vectorstore_status(conversation_id: str):
    convo = db.get_conversation(conversation_id)
    if convo is None:
        raise HTTPException(status_code=404, detail="Conversation not found")

    vectorstore = get_or_load_vectorstore(conversation_id)
    path = backend.get_vectorstore_path(conversation_id)
    status = backend.get_vectorstore_status(vectorstore, path, conversation_id)
    return VectorstoreStatus(conversation_id=conversation_id, **status)


# --------------------------------------------------------------------------
# Static frontend (Streamlit removed - plain HTML/CSS/JS served by FastAPI)
# --------------------------------------------------------------------------
STATIC_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "static")
app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")


@app.get("/")
def serve_index():
    return FileResponse(os.path.join(STATIC_DIR, "index.html"))


if __name__ == "__main__":
    uvicorn.run("backend_server:app", host="0.0.0.0", port=7860, reload=False)