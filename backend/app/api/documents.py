import shutil
from pathlib import Path

from fastapi import APIRouter, File, HTTPException, UploadFile # type: ignore

from app.models.document import (
    DocumentInfo,
    DocumentListResponse,
    IndexResponse,
    UploadResponse,
)
from app.rag.vector_store import get_or_create_collection, index_documents


router = APIRouter(
    prefix="/documents",
    tags=["Documents"],
)


PROJECT_ROOT = Path(__file__).resolve().parents[3]
RAW_DATA_DIR = PROJECT_ROOT / "data" / "raw"

SUPPORTED_EXTENSIONS = {
    ".pdf",
    ".pptx",
    ".ipynb",
    ".txt",
    ".md",
}


@router.get("/raw", response_model=DocumentListResponse)
def list_raw_documents():
    """
    List all supported documents currently available in data/raw.
    """
    RAW_DATA_DIR.mkdir(parents=True, exist_ok=True)

    documents = []

    for file_path in RAW_DATA_DIR.iterdir():
        if file_path.is_dir() or file_path.name.startswith("."):
            continue

        suffix = file_path.suffix.lower()

        if suffix not in SUPPORTED_EXTENSIONS:
            continue

        documents.append(
            DocumentInfo(
                file_name=file_path.name,
                file_type=suffix.replace(".", ""),
                size_kb=round(file_path.stat().st_size / 1024, 2),
            )
        )

    return DocumentListResponse(
        total=len(documents),
        documents=documents,
    )


@router.post("/upload", response_model=UploadResponse)
def upload_document(file: UploadFile = File(...)):
    """
    Upload a PDF, PPTX, IPYNB, TXT, or MD file into data/raw.
    """
    if not file.filename:
        raise HTTPException(
            status_code=400,
            detail="No file name found.",
        )

    original_name = Path(file.filename).name
    suffix = Path(original_name).suffix.lower()

    if suffix not in SUPPORTED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=f"Unsupported file type: {suffix}. Supported types: {sorted(SUPPORTED_EXTENSIONS)}",
        )

    RAW_DATA_DIR.mkdir(parents=True, exist_ok=True)

    save_path = RAW_DATA_DIR / original_name

    try:
        with save_path.open("wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

    except Exception as error:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to upload file: {str(error)}",
        )

    finally:
        file.file.close()

    return UploadResponse(
        message="File uploaded successfully.",
        file_name=original_name,
        saved_to=str(save_path),
    )


@router.post("/index", response_model=IndexResponse)
def index_raw_documents():
    """
    Index all documents from data/raw into the vector database.
    """
    try:
        indexed_chunks = index_documents()
        collection = get_or_create_collection()
        total_vectors = collection.count()

        return IndexResponse(
            message="Documents indexed successfully.",
            indexed_chunks=indexed_chunks,
            total_vectors=total_vectors,
        )

    except Exception as error:
        raise HTTPException(
            status_code=500,
            detail=f"Failed to index documents: {str(error)}",
        )