from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.models import ChatMessage, ChatSession, DocumentRecord, StudyArtifact
from app.db.session import DATABASE_URL, DEFAULT_DB_PATH, get_db


router = APIRouter(
    prefix="/database",
    tags=["Database"],
)


def get_database_type() -> str:
    if DATABASE_URL.startswith("sqlite"):
        return "sqlite"

    if DATABASE_URL.startswith("postgresql"):
        return "postgresql"

    return "unknown"


@router.get("/status")
def database_status(db: Session = Depends(get_db)):
    database_type = get_database_type()

    return {
        "database_type": database_type,
        "sqlite_file": str(DEFAULT_DB_PATH) if database_type == "sqlite" else None,
        "sqlite_file_exists": DEFAULT_DB_PATH.exists()
        if database_type == "sqlite"
        else None,
        "tables": {
            "documents": db.query(DocumentRecord).count(),
            "chat_sessions": db.query(ChatSession).count(),
            "chat_messages": db.query(ChatMessage).count(),
            "study_artifacts": db.query(StudyArtifact).count(),
        },
    }