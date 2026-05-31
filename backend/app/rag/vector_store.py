from pathlib import Path
from typing import List

import chromadb # type: ignore
from langchain_core.documents import Document # type: ignore

from app.ingestion.loaders import load_documents, chunk_documents


PROJECT_ROOT = Path(__file__).resolve().parents[3]
VECTORSTORE_DIR = PROJECT_ROOT / "data" / "vectorstore"
COLLECTION_NAME = "learning_notes"


def get_chroma_client():
    """Create a persistent ChromaDB client."""
    VECTORSTORE_DIR.mkdir(parents=True, exist_ok=True)

    client = chromadb.PersistentClient(
        path=str(VECTORSTORE_DIR)
    )

    return client


def get_or_create_collection():
    """Get or create the collection where note chunks will be stored."""
    client = get_chroma_client()

    collection = client.get_or_create_collection(
        name=COLLECTION_NAME
    )

    return collection


def build_chunk_id(chunk: Document, index: int) -> str:
    """
    Create a stable ID for every chunk.

    Example:
    Normal Equation.pdf-page-1-chunk-0
    """
    metadata = chunk.metadata
    source = metadata.get("source", "unknown")
    page = metadata.get("page", metadata.get("slide", metadata.get("cell", "na")))

    return f"{source}-part-{page}-chunk-{index}"


def index_documents() -> int:
    """
    Load documents, split them into chunks, and store them in ChromaDB.
    """
    documents = load_documents()
    chunks = chunk_documents(documents)

    if not chunks:
        print("No chunks found. Add files to data/raw first.")
        return 0

    collection = get_or_create_collection()

    ids: List[str] = []
    texts: List[str] = []
    metadatas: List[dict] = []

    for index, chunk in enumerate(chunks):
        chunk_id = build_chunk_id(chunk, index)

        ids.append(chunk_id)
        texts.append(chunk.page_content)
        metadatas.append(chunk.metadata)

    collection.upsert(
        ids=ids,
        documents=texts,
        metadatas=metadatas,
    )

    return len(chunks)


def search_notes(query: str, n_results: int = 3):
    """
    Search the vector database for the most relevant chunks.
    """
    collection = get_or_create_collection()

    results = collection.query(
        query_texts=[query],
        n_results=n_results,
    )

    return results