from typing import Any, List

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


class Source(BaseModel):
    source: str
    location: Any
    distance: float


class ChatResponse(BaseModel):
    answer: str
    sources: List[Source]