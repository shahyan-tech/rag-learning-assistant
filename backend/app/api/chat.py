import json
from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException # type: ignore
from sqlalchemy.orm import Session # type: ignore

from app.db.models import ChatMessage, ChatSession
from app.db.session import get_db
from app.models.chat import (
    ChatRequest,
    ChatResponse,
    ChatSessionDetail,
    ChatSessionSummary,
    DeleteSessionResponse,
)
from app.rag.rag_chain import answer_question


router = APIRouter(
    prefix="/chat",
    tags=["Chatbot"],
)


def create_chat_title(question: str) -> str:
    """
    Create a short chat title from the first user question.
    """
    clean_question = question.strip()

    if len(clean_question) <= 60:
        return clean_question

    return clean_question[:57] + "..."


def get_or_create_session(db: Session, session_id: int | None, question: str) -> ChatSession:
    """
    Get an existing chat session or create a new one.
    """
    if session_id is not None:
        session = db.query(ChatSession).filter(ChatSession.id == session_id).first()

        if not session:
            raise HTTPException(
                status_code=404,
                detail=f"Chat session {session_id} not found.",
            )

        return session

    session = ChatSession(
        title=create_chat_title(question),
    )

    db.add(session)
    db.commit()
    db.refresh(session)

    return session


def parse_sources(sources_json: str | None):
    """
    Convert stored JSON text back into Python list.
    """
    if not sources_json:
        return []

    try:
        return json.loads(sources_json)
    except json.JSONDecodeError:
        return []


@router.post("/ask", response_model=ChatResponse)
def ask_question(request: ChatRequest, db: Session = Depends(get_db)):
    """
    Ask a question to the RAG chatbot and save the conversation in database.

    The system will:
    1. Create or reuse a chat session.
    2. Search relevant chunks from the vector database.
    3. Send those chunks to the LLM.
    4. Save user question and assistant answer.
    5. Return answer with source references.
    """
    try:
        session = get_or_create_session(
            db=db,
            session_id=request.session_id,
            question=request.question,
        )

        result = answer_question(
            question=request.question,
            n_results=request.n_results,
        )

        user_message = ChatMessage(
            session_id=session.id,
            role="user",
            content=request.question,
            sources_json=json.dumps([]),
        )

        assistant_message = ChatMessage(
            session_id=session.id,
            role="assistant",
            content=result["answer"],
            answer_type=result.get("answer_type"),
            note=result.get("note"),
            sources_json=json.dumps(result.get("sources", [])),
        )

        session.updated_at = datetime.utcnow()

        db.add(user_message)
        db.add(assistant_message)
        db.commit()

        return {
            "answer": result["answer"],
            "sources": result.get("sources", []),
            "answer_type": result.get("answer_type", "unknown"),
            "note": result.get("note"),
            "session_id": session.id,
        }

    except HTTPException:
        raise

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


@router.get("/sessions", response_model=list[ChatSessionSummary])
def list_chat_sessions(db: Session = Depends(get_db)):
    """
    List all saved chat sessions.
    """
    sessions = (
        db.query(ChatSession)
        .order_by(ChatSession.updated_at.desc())
        .all()
    )

    return [
        {
            "id": session.id,
            "title": session.title,
            "created_at": session.created_at,
            "updated_at": session.updated_at,
            "message_count": len(session.messages),
        }
        for session in sessions
    ]


@router.get("/sessions/{session_id}", response_model=ChatSessionDetail)
def get_chat_session(session_id: int, db: Session = Depends(get_db)):
    """
    Get one chat session with all messages.
    """
    session = db.query(ChatSession).filter(ChatSession.id == session_id).first()

    if not session:
        raise HTTPException(
            status_code=404,
            detail=f"Chat session {session_id} not found.",
        )

    messages = (
        db.query(ChatMessage)
        .filter(ChatMessage.session_id == session_id)
        .order_by(ChatMessage.created_at.asc())
        .all()
    )

    return {
        "id": session.id,
        "title": session.title,
        "created_at": session.created_at,
        "updated_at": session.updated_at,
        "messages": [
            {
                "id": message.id,
                "role": message.role,
                "content": message.content,
                "answer_type": message.answer_type,
                "note": message.note,
                "sources": parse_sources(message.sources_json),
                "created_at": message.created_at,
            }
            for message in messages
        ],
    }


@router.delete("/sessions/{session_id}", response_model=DeleteSessionResponse)
def delete_chat_session(session_id: int, db: Session = Depends(get_db)):
    """
    Delete a chat session and all its messages.
    """
    session = db.query(ChatSession).filter(ChatSession.id == session_id).first()

    if not session:
        raise HTTPException(
            status_code=404,
            detail=f"Chat session {session_id} not found.",
        )

    db.delete(session)
    db.commit()

    return {
        "message": "Chat session deleted successfully.",
        "session_id": session_id,
    }