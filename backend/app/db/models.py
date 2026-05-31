from datetime import datetime
from typing import Optional

from sqlalchemy import DateTime, Float, ForeignKey, Integer, String, Text # type: ignore
from sqlalchemy.orm import Mapped, mapped_column, relationship # type: ignore

from app.db.session import Base


class DocumentRecord(Base):
    __tablename__ = "documents"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)

    file_name: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    file_type: Mapped[str] = mapped_column(String(50))
    file_path: Mapped[str] = mapped_column(Text)
    size_kb: Mapped[float] = mapped_column(Float)

    status: Mapped[str] = mapped_column(String(50), default="uploaded")
    chunk_count: Mapped[int] = mapped_column(Integer, default=0)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
    )


class ChatSession(Base):
    __tablename__ = "chat_sessions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)

    title: Mapped[str] = mapped_column(String(255), default="New Chat")

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
    )

    messages: Mapped[list["ChatMessage"]] = relationship(
        back_populates="session",
        cascade="all, delete-orphan",
    )


class ChatMessage(Base):
    __tablename__ = "chat_messages"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)

    session_id: Mapped[int] = mapped_column(
        ForeignKey("chat_sessions.id"),
        index=True,
    )

    role: Mapped[str] = mapped_column(String(50))
    content: Mapped[str] = mapped_column(Text)

    answer_type: Mapped[Optional[str]] = mapped_column(String(50), nullable=True)
    note: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    # JSON stored as text for now.
    # Later PostgreSQL can use JSONB.
    sources_json: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    session: Mapped["ChatSession"] = relationship(back_populates="messages")


class StudyArtifact(Base):
    __tablename__ = "study_artifacts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)

    artifact_type: Mapped[str] = mapped_column(String(50))
    topic: Mapped[str] = mapped_column(String(255), index=True)

    # JSON stored as text for SQLite.
    payload_json: Mapped[str] = mapped_column(Text)
    sources_json: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)