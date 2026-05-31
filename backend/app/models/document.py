from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel


class DocumentInfo(BaseModel):
    id: Optional[int] = None
    file_name: str
    file_type: str
    file_path: Optional[str] = None
    size_kb: float
    status: str = "uploaded"
    chunk_count: int = 0
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class DocumentListResponse(BaseModel):
    total: int
    documents: List[DocumentInfo]


class UploadResponse(BaseModel):
    message: str
    file_name: str
    saved_to: str
    document_id: int
    status: str


class UploadItemResult(BaseModel):
    file_name: str
    success: bool
    message: str
    document_id: Optional[int] = None
    status: Optional[str] = None


class MultiUploadResponse(BaseModel):
    message: str
    uploaded_count: int
    failed_count: int
    results: List[UploadItemResult]


class IndexResponse(BaseModel):
    message: str
    indexed_chunks: int
    total_vectors: int
    updated_documents: int


class SyncDocumentsResponse(BaseModel):
    message: str
    synced_documents: int


class DeleteDocumentResponse(BaseModel):
    message: str
    document_id: int
    file_name: str

class ClearDocumentsResponse(BaseModel):
    message: str
    deleted_documents: int
    deleted_files: int
    vectorstore_reset: bool