from typing import List

from pydantic import BaseModel


class DocumentInfo(BaseModel):
    file_name: str
    file_type: str
    size_kb: float


class DocumentListResponse(BaseModel):
    total: int
    documents: List[DocumentInfo]


class UploadResponse(BaseModel):
    message: str
    file_name: str
    saved_to: str


class IndexResponse(BaseModel):
    message: str
    indexed_chunks: int
    total_vectors: int