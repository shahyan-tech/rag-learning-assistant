from fastapi import APIRouter, HTTPException # type: ignore

from app.models.chat import ChatRequest, ChatResponse
from app.rag.rag_chain import answer_question


router = APIRouter(
    prefix="/chat",
    tags=["Chatbot"],
)


@router.post("/ask", response_model=ChatResponse)
def ask_question(request: ChatRequest):
    """
    Ask a question to the RAG chatbot.

    The system will:
    1. Search relevant chunks from the vector database.
    2. Send those chunks to the LLM.
    3. Return an answer with source references.
    """
    try:
        result = answer_question(
            question=request.question,
            n_results=request.n_results,
        )

        return result

    except ValueError as error:
        raise HTTPException(
            status_code=400,
            detail=str(error),
        )

    except Exception as error:
        raise HTTPException(
            status_code=500,
            detail=f"Something went wrong while generating the answer: {str(error)}",
        )