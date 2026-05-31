from __future__ import annotations

from datetime import datetime
from typing import Any, List, Optional

from pydantic import BaseModel, Field


class SourceRef(BaseModel):
    source: str
    location: Any
    distance: float


class FlashcardRequest(BaseModel):
    topic: str = Field(..., min_length=2, examples=["normal equation"])
    count: int = Field(default=5, ge=1, le=20)
    n_results: int = Field(default=4, ge=1, le=10)


class Flashcard(BaseModel):
    front: str
    back: str


class FlashcardResponse(BaseModel):
    artifact_id: Optional[int] = None
    topic: str
    flashcards: List[Flashcard]
    sources: List[SourceRef]


class QuizRequest(BaseModel):
    topic: str = Field(..., min_length=2, examples=["normal equation"])
    count: int = Field(default=5, ge=1, le=15)
    difficulty: str = Field(default="beginner")
    n_results: int = Field(default=4, ge=1, le=10)


class QuizQuestion(BaseModel):
    question: str
    options: List[str]
    correct_answer: str
    explanation: str


class QuizResponse(BaseModel):
    artifact_id: Optional[int] = None
    topic: str
    difficulty: str
    questions: List[QuizQuestion]
    sources: List[SourceRef]


class MindMapRequest(BaseModel):
    topic: str = Field(..., min_length=2, examples=["linear regression"])
    n_results: int = Field(default=5, ge=1, le=10)


class MindMapNode(BaseModel):
    title: str
    children: List["MindMapNode"] = Field(default_factory=list)


class MindMapResponse(BaseModel):
    artifact_id: Optional[int] = None
    topic: str
    mind_map: MindMapNode
    sources: List[SourceRef]


class StudyArtifactSummary(BaseModel):
    id: int
    artifact_type: str
    topic: str
    created_at: datetime


class StudyArtifactDetail(BaseModel):
    id: int
    artifact_type: str
    topic: str
    payload: Any
    sources: List[SourceRef] = []
    created_at: datetime


class DeleteStudyArtifactResponse(BaseModel):
    message: str
    artifact_id: int