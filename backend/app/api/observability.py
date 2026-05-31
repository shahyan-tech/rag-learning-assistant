import os

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