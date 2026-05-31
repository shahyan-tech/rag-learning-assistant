from datetime import datetime
from typing import Any, List, Optional

from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    question: str = Field(
        ...,
        min_length=3,
        description="The user's question about ML, DL, GenAI, or Agentic AI.",
        examples=["What is the normal equation in linear regression?"],
    )

    n_results: int = Field(
        default=4,
        ge=1,
        le=10,
        description="Number of relevant chunks to retrieve from the vector database.",
    )

    session_id: Optional[int] = Field(
        default=None,
        description="Existing chat session ID. If empty, a new session is created.",
    )


class Source(BaseModel):
    source: str
    location: Any
    distance: float


class ChatResponse(BaseModel):
    answer: str
    sources: List[Source]
    answer_type: str
    note: Optional[str] = None
    session_id: int


class ChatMessageResponse(BaseModel):
    id: int
    role: str
    content: str
    answer_type: Optional[str] = None
    note: Optional[str] = None
    sources: List[Source] = []
    created_at: datetime


class ChatSessionSummary(BaseModel):
    id: int
    title: str
    created_at: datetime
    updated_at: datetime
    message_count: int


class ChatSessionDetail(BaseModel):
    id: int
    title: str
    created_at: datetime
    updated_at: datetime
    messages: List[ChatMessageResponse]


class DeleteSessionResponse(BaseModel):
    message: str
    session_id: int