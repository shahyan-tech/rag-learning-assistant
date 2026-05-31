from fastapi import APIRouter, Depends # type: ignore
from sqlalchemy.orm import Session # type: ignore

from app.db.models import ChatMessage, ChatSession, DocumentRecord, StudyArtifact
from app.db.session import DEFAULT_DB_PATH, get_db


router = APIRouter(
    prefix="/database",
    tags=["Database"],
)


@router.get("/status")
def database_status(db: Session = Depends(get_db)):
    return {
        "database_file": str(DEFAULT_DB_PATH),
        "database_exists": DEFAULT_DB_PATH.exists(),
        "tables": {
            "documents": db.query(DocumentRecord).count(),
            "chat_sessions": db.query(ChatSession).count(),
            "chat_messages": db.query(ChatMessage).count(),
            "study_artifacts": db.query(StudyArtifact).count(),
        },
    }