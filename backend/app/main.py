from contextlib import asynccontextmanager

from fastapi import FastAPI # type: ignore
from fastapi.middleware.cors import CORSMiddleware # type: ignore
from app.api.observability import router as observability_router
from app.api.chat import router as chat_router
from app.api.database import router as database_router
from app.api.documents import router as documents_router
from app.api.study import router as study_router
from app.db.init_db import create_db_and_tables


@asynccontextmanager
async def lifespan(app: FastAPI):
    create_db_and_tables()
    yield


app = FastAPI(
    title="RAG Learning Assistant API",
    description="Backend API for ML, DL, GenAI, and Agentic AI learning assistant.",
    version="0.1.0",
    lifespan=lifespan,
)


origins = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
    "https://rag-learning-assistant-pi.vercel.app",
]


app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


app.include_router(chat_router)
app.include_router(documents_router)
app.include_router(study_router)
app.include_router(database_router)
app.include_router(observability_router)


@app.get("/")
def root():
    return {
        "message": "RAG Learning Assistant API is running",
        "status": "ok",
    }


@app.get("/health")
def health_check():
    return {
        "status": "healthy",
    }