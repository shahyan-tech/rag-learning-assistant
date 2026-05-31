import os
from app.rag.vector_store import count_vectors
from fastapi import APIRouter # type: ignore


router = APIRouter(
    prefix="/observability",
    tags=["Observability"],
)


@router.get("/langsmith")
def langsmith_status():
    tracing = os.getenv("LANGSMITH_TRACING", "false")
    api_key = os.getenv("LANGSMITH_API_KEY")
    project = os.getenv("LANGSMITH_PROJECT", "default")

    return {
        "langsmith_tracing": tracing,
        "langsmith_api_key_loaded": bool(api_key),
        "langsmith_project": project,
    }

@router.get("/langgraph")
def langgraph_status():
    return {
        "langgraph_enabled": True,
        "workflow": [
            "retrieve_context",
            "grade_relevance",
            "conditional_route",
            "answer_from_notes OR answer_general",
        ],
    }



@router.get("/vectorstore")
def vectorstore_status():
    try:
        vector_count = count_vectors()
        healthy = True
        error = None
    except Exception as exc:
        vector_count = None
        healthy = False
        error = str(exc)

    return {
        "healthy": healthy,
        "vector_backend": os.getenv("VECTOR_BACKEND", "chroma"),
        "qdrant_url_loaded": bool(os.getenv("QDRANT_URL")),
        "qdrant_api_key_loaded": bool(os.getenv("QDRANT_API_KEY")),
        "qdrant_collection": os.getenv("QDRANT_COLLECTION", "learning_notes"),
        "qdrant_embedding_model": os.getenv(
            "QDRANT_EMBEDDING_MODEL",
            "BAAI/bge-small-en",
        ),
        "vector_count": vector_count,
        "error": error,
    }