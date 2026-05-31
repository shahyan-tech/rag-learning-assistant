import shutil
from datetime import datetime
from pathlib import Path
from typing import Dict

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile # type: ignore
from sqlalchemy.orm import Session # type: ignore

from app.db.models import DocumentRecord
from app.db.session import get_db
from app.ingestion.loaders import (
    RAW_DATA_DIR,
    chunk_documents,
    get_source_name,
    get_supported_files,
    load_documents,
)
from app.models.document import (
    ClearDocumentsResponse,
    DeleteDocumentResponse,
    DocumentInfo,
    DocumentListResponse,
    IndexResponse,
    MultiUploadResponse,
    SyncDocumentsResponse,
    UploadItemResult,
    UploadResponse,
)
from app.rag.vector_store import (
    get_or_create_collection,
    index_documents,
    reset_vectorstore_collection,
)


router = APIRouter(
    prefix="/documents",
    tags=["Documents"],
)


SUPPORTED_EXTENSIONS = {
    ".pdf",
    ".pptx",
    ".ipynb",
    ".txt",
    ".md",
}


def get_file_type(file_path: Path) -> str:
    return file_path.suffix.lower().replace(".", "")


def get_file_size_kb(file_path: Path) -> float:
    return round(file_path.stat().st_size / 1024, 2)


def safe_relative_upload_path(filename: str) -> Path:
    """
    Safely handle browser folder uploads.
    """
    raw_parts = Path(filename).parts
    safe_parts = []

    for part in raw_parts:
        if part in ["", ".", ".."]:
            continue

        clean_part = part.replace("\\", "").replace("/", "").strip()

        if clean_part:
            safe_parts.append(clean_part)

    if not safe_parts:
        raise ValueError("Invalid file name.")

    return Path(*safe_parts)


def remove_empty_folders(folder: Path) -> None:
    """
    Remove empty folders inside data/raw after deleting files.
    """
    if not folder.exists():
        return

    for child in sorted(folder.rglob("*"), reverse=True):
        if child.is_dir():
            try:
                child.rmdir()
            except OSError:
                pass


def upsert_document_record(db: Session, file_path: Path) -> DocumentRecord:
    """
    Create or update a database record for a file in data/raw.

    file_name stores the relative source path.
    Example:
    ML Specialization/Course 1/Module 1/lecture.pdf
    """
    source_name = get_source_name(file_path)

    existing_record = (
        db.query(DocumentRecord)
        .filter(DocumentRecord.file_name == source_name)
        .first()
    )

    if existing_record:
        existing_record.file_type = get_file_type(file_path)
        existing_record.file_path = str(file_path)
        existing_record.size_kb = get_file_size_kb(file_path)
        existing_record.updated_at = datetime.utcnow()

        db.commit()
        db.refresh(existing_record)

        return existing_record

    new_record = DocumentRecord(
        file_name=source_name,
        file_type=get_file_type(file_path),
        file_path=str(file_path),
        size_kb=get_file_size_kb(file_path),
        status="uploaded",
        chunk_count=0,
    )

    db.add(new_record)
    db.commit()
    db.refresh(new_record)

    return new_record


def sync_raw_files_to_database(db: Session) -> int:
    """
    Recursively sync every supported file inside data/raw into the database.
    """
    RAW_DATA_DIR.mkdir(parents=True, exist_ok=True)

    synced_count = 0

    for file_path in get_supported_files(RAW_DATA_DIR):
        upsert_document_record(db, file_path)
        synced_count += 1

    return synced_count


def get_chunk_counts_by_source() -> Dict[str, int]:
    """
    Count how many chunks each source file creates.
    """
    documents = load_documents()
    chunks = chunk_documents(documents)

    counts: Dict[str, int] = {}

    for chunk in chunks:
        source = chunk.metadata.get("source", "unknown")
        counts[source] = counts.get(source, 0) + 1

    return counts


def save_upload_file(file: UploadFile, db: Session) -> UploadItemResult:
    if not file.filename:
        return UploadItemResult(
            file_name="unknown",
            success=False,
            message="No file name found.",
        )

    try:
        relative_path = safe_relative_upload_path(file.filename)
    except ValueError as error:
        return UploadItemResult(
            file_name=file.filename,
            success=False,
            message=str(error),
        )

    suffix = relative_path.suffix.lower()

    if suffix not in SUPPORTED_EXTENSIONS:
        return UploadItemResult(
            file_name=str(relative_path),
            success=False,
            message=f"Unsupported file type: {suffix}.",
        )

    RAW_DATA_DIR.mkdir(parents=True, exist_ok=True)

    save_path = RAW_DATA_DIR / relative_path
    save_path.parent.mkdir(parents=True, exist_ok=True)

    try:
        with save_path.open("wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        record = upsert_document_record(db, save_path)

        record.status = "uploaded"
        record.chunk_count = 0
        record.updated_at = datetime.utcnow()

        db.commit()
        db.refresh(record)

        return UploadItemResult(
            file_name=record.file_name,
            success=True,
            message="Uploaded successfully.",
            document_id=record.id,
            status=record.status,
        )

    except Exception as error:
        return UploadItemResult(
            file_name=str(relative_path),
            success=False,
            message=f"Failed to upload file: {str(error)}",
        )

    finally:
        file.file.close()


@router.get("/raw", response_model=DocumentListResponse)
def list_raw_documents(db: Session = Depends(get_db)):
    sync_raw_files_to_database(db)

    records = (
        db.query(DocumentRecord)
        .order_by(DocumentRecord.updated_at.desc())
        .all()
    )

    documents = [
        DocumentInfo(
            id=record.id,
            file_name=record.file_name,
            file_type=record.file_type,
            file_path=record.file_path,
            size_kb=record.size_kb,
            status=record.status,
            chunk_count=record.chunk_count,
            created_at=record.created_at,
            updated_at=record.updated_at,
        )
        for record in records
    ]

    return DocumentListResponse(
        total=len(documents),
        documents=documents,
    )


@router.post("/sync", response_model=SyncDocumentsResponse)
def sync_documents(db: Session = Depends(get_db)):
    synced_count = sync_raw_files_to_database(db)

    return SyncDocumentsResponse(
        message="Documents synced successfully.",
        synced_documents=synced_count,
    )


@router.post("/upload", response_model=UploadResponse)
def upload_document(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    result = save_upload_file(file=file, db=db)

    if not result.success:
        raise HTTPException(
            status_code=400,
            detail=result.message,
        )

    record = (
        db.query(DocumentRecord)
        .filter(DocumentRecord.id == result.document_id)
        .first()
    )

    return UploadResponse(
        message="File uploaded successfully and saved in database.",
        file_name=result.file_name,
        saved_to=record.file_path if record else "",
        document_id=result.document_id,
        status=result.status or "uploaded",
    )


@router.post("/upload-multiple", response_model=MultiUploadResponse)
def upload_multiple_documents(
    files: list[UploadFile] = File(...),
    db: Session = Depends(get_db),
):
    if not files:
        raise HTTPException(
            status_code=400,
            detail="No files uploaded.",
        )

    results = []

    for file in files:
        result = save_upload_file(file=file, db=db)
        results.append(result)

    uploaded_count = sum(1 for result in results if result.success)
    failed_count = len(results) - uploaded_count

    return MultiUploadResponse(
        message=f"Uploaded {uploaded_count} file(s). Failed {failed_count} file(s).",
        uploaded_count=uploaded_count,
        failed_count=failed_count,
        results=results,
    )


@router.post("/index", response_model=IndexResponse)
def index_raw_documents(db: Session = Depends(get_db)):
    try:
        sync_raw_files_to_database(db)

        chunk_counts = get_chunk_counts_by_source()

        indexed_chunks = index_documents()
        collection = get_or_create_collection()
        total_vectors = collection.count()

        updated_documents = 0

        records = db.query(DocumentRecord).all()

        for record in records:
            if record.file_name in chunk_counts:
                record.status = "indexed"
                record.chunk_count = chunk_counts[record.file_name]
                record.updated_at = datetime.utcnow()
                updated_documents += 1
            else:
                record.status = "uploaded"
                record.chunk_count = 0
                record.updated_at = datetime.utcnow()

        db.commit()

        return IndexResponse(
            message="Documents indexed successfully and database records updated.",
            indexed_chunks=indexed_chunks,
            total_vectors=total_vectors,
            updated_documents=updated_documents,
        )

    except Exception as error:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to index documents: {str(error)}",
        )


@router.delete("/clear-all", response_model=ClearDocumentsResponse)
def clear_all_documents(db: Session = Depends(get_db)):
    """
    Clear the whole local knowledge base:
    1. Delete supported files from data/raw.
    2. Delete document records from SQLite.
    3. Reset Chroma vector collection.
    """
    try:
        records = db.query(DocumentRecord).all()
        deleted_documents = len(records)

        deleted_files = 0

        for file_path in get_supported_files(RAW_DATA_DIR):
            try:
                if file_path.exists() and file_path.is_file():
                    file_path.unlink()
                    deleted_files += 1
            except Exception:
                pass

        db.query(DocumentRecord).delete()
        db.commit()

        reset_vectorstore_collection()
        remove_empty_folders(RAW_DATA_DIR)

        return ClearDocumentsResponse(
            message="Knowledge base cleared successfully.",
            deleted_documents=deleted_documents,
            deleted_files=deleted_files,
            vectorstore_reset=True,
        )

    except Exception as error:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to clear knowledge base: {str(error)}",
        )


@router.delete("/{document_id}", response_model=DeleteDocumentResponse)
def delete_document(
    document_id: int,
    db: Session = Depends(get_db),
):
    record = (
        db.query(DocumentRecord)
        .filter(DocumentRecord.id == document_id)
        .first()
    )

    if not record:
        raise HTTPException(
            status_code=404,
            detail=f"Document {document_id} not found.",
        )

    file_name = record.file_name
    file_path = Path(record.file_path)

    try:
        if file_path.exists():
            file_path.unlink()

        collection = get_or_create_collection()

        try:
            collection.delete(where={"source": file_name})
        except Exception:
            pass

        db.delete(record)
        db.commit()

        remove_empty_folders(RAW_DATA_DIR)

        return DeleteDocumentResponse(
            message="Document deleted successfully.",
            document_id=document_id,
            file_name=file_name,
        )

    except Exception as error:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to delete document: {str(error)}",
        )