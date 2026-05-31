import os
from pathlib import Path
from typing import List
from uuid import NAMESPACE_URL, uuid5

import chromadb # type: ignore
from langchain_core.documents import Document # type: ignore
from qdrant_client import QdrantClient, models # type: ignore

from app.ingestion.loaders import chunk_documents, load_documents


PROJECT_ROOT = Path(__file__).resolve().parents[3]
VECTORSTORE_DIR = PROJECT_ROOT / "data" / "vectorstore"

COLLECTION_NAME = "learning_notes"

VECTOR_BACKEND = os.getenv("VECTOR_BACKEND", "chroma").lower()

QDRANT_URL = os.getenv("QDRANT_URL")
QDRANT_API_KEY = os.getenv("QDRANT_API_KEY")
QDRANT_COLLECTION = os.getenv("QDRANT_COLLECTION", COLLECTION_NAME)
QDRANT_EMBEDDING_MODEL = os.getenv(
    "QDRANT_EMBEDDING_MODEL",
    "BAAI/bge-small-en",
)


# -----------------------------
# Shared helpers
# -----------------------------

def empty_search_result():
    return {
        "documents": [[]],
        "metadatas": [[]],
        "distances": [[]],
    }


def build_chunk_id(chunk: Document, index: int) -> str:
    """
    Create a stable text ID for every chunk.
    """
    metadata = chunk.metadata
    source = metadata.get("source", "unknown")
    page = metadata.get("page", metadata.get("slide", metadata.get("cell", "na")))

    safe_source = str(source).replace("\\", "/")

    return f"{safe_source}-part-{page}-chunk-{index}"


def build_qdrant_uuid(chunk: Document, index: int) -> str:
    """
    Qdrant point IDs must be UUID or integer.
    So we convert our stable chunk ID into a deterministic UUID.
    """
    raw_id = build_chunk_id(chunk, index)
    return str(uuid5(NAMESPACE_URL, raw_id))


# -----------------------------
# Chroma backend
# -----------------------------

def get_chroma_client():
    VECTORSTORE_DIR.mkdir(parents=True, exist_ok=True)

    client = chromadb.PersistentClient(path=str(VECTORSTORE_DIR))

    return client


def get_chroma_collection():
    client = get_chroma_client()
    return client.get_or_create_collection(name=COLLECTION_NAME)


def reset_chroma_collection() -> None:
    client = get_chroma_client()

    try:
        client.delete_collection(COLLECTION_NAME)
    except Exception:
        pass

    client.get_or_create_collection(name=COLLECTION_NAME)


def index_documents_chroma() -> int:
    documents = load_documents()
    chunks = chunk_documents(documents)

    if not chunks:
        print("No chunks found. Add files to data/raw first.")
        return 0

    collection = get_chroma_collection()

    ids: List[str] = []
    texts: List[str] = []
    metadatas: List[dict] = []

    for index, chunk in enumerate(chunks):
        ids.append(build_chunk_id(chunk, index))
        texts.append(chunk.page_content)
        metadatas.append(chunk.metadata)

    collection.upsert(
        ids=ids,
        documents=texts,
        metadatas=metadatas,
    )

    return len(chunks)


def search_notes_chroma(query: str, n_results: int = 3):
    collection = get_chroma_collection()

    if collection.count() == 0:
        return empty_search_result()

    return collection.query(
        query_texts=[query],
        n_results=n_results,
    )


def count_vectors_chroma() -> int:
    collection = get_chroma_collection()
    return collection.count()


def delete_vectors_by_source_chroma(source: str) -> None:
    collection = get_chroma_collection()

    try:
        collection.delete(where={"source": source})
    except Exception:
        pass


# -----------------------------
# Qdrant backend
# -----------------------------

def get_qdrant_client() -> QdrantClient:
    """
    Create Qdrant client.

    If QDRANT_URL is set, use Qdrant Cloud.
    If not, use local Qdrant embedded storage for development.
    """
    if QDRANT_URL:
        return QdrantClient(
            url=QDRANT_URL,
            api_key=QDRANT_API_KEY,
        )

    local_qdrant_path = VECTORSTORE_DIR / "qdrant_local"

    return QdrantClient(path=str(local_qdrant_path))


def ensure_qdrant_collection() -> None:
    client = get_qdrant_client()

    try:
        client.get_collection(QDRANT_COLLECTION)
        return
    except Exception:
        pass

    vector_size = client.get_embedding_size(QDRANT_EMBEDDING_MODEL)

    client.create_collection(
        collection_name=QDRANT_COLLECTION,
        vectors_config=models.VectorParams(
            size=vector_size,
            distance=models.Distance.COSINE,
        ),
    )


def reset_qdrant_collection() -> None:
    client = get_qdrant_client()

    try:
        client.delete_collection(QDRANT_COLLECTION)
    except Exception:
        pass

    ensure_qdrant_collection()


def index_documents_qdrant() -> int:
    documents = load_documents()
    chunks = chunk_documents(documents)

    if not chunks:
        print("No chunks found. Add files to data/raw first.")
        return 0

    ensure_qdrant_collection()

    client = get_qdrant_client()

    ids = []
    vectors = []
    payloads = []

    for index, chunk in enumerate(chunks):
        ids.append(build_qdrant_uuid(chunk, index))

        vectors.append(
            models.Document(
                text=chunk.page_content,
                model=QDRANT_EMBEDDING_MODEL,
            )
        )

        payload = {
            **chunk.metadata,
            "document": chunk.page_content,
        }

        payloads.append(payload)

    client.upload_collection(
        collection_name=QDRANT_COLLECTION,
        vectors=vectors,
        payload=payloads,
        ids=ids,
        batch_size=64,
    )

    return len(chunks)


def search_notes_qdrant(query: str, n_results: int = 3):
    ensure_qdrant_collection()

    if count_vectors_qdrant() == 0:
        return empty_search_result()

    client = get_qdrant_client()

    points = client.query_points(
        collection_name=QDRANT_COLLECTION,
        query=models.Document(
            text=query,
            model=QDRANT_EMBEDDING_MODEL,
        ),
        limit=n_results,
        with_payload=True,
    ).points

    documents = []
    metadatas = []
    distances = []

    for point in points:
        payload = point.payload or {}

        document = payload.get("document", "")
        metadata = {
            key: value
            for key, value in payload.items()
            if key != "document"
        }

        score = float(point.score or 0.0)

        # Qdrant cosine score: higher is better.
        # Our RAG relevance logic expects distance: lower is better.
        distance = 1.0 - score

        documents.append(document)
        metadatas.append(metadata)
        distances.append(distance)

    return {
        "documents": [documents],
        "metadatas": [metadatas],
        "distances": [distances],
    }


def count_vectors_qdrant() -> int:
    ensure_qdrant_collection()

    client = get_qdrant_client()

    return client.count(
        collection_name=QDRANT_COLLECTION,
        exact=True,
    ).count


def delete_vectors_by_source_qdrant(source: str) -> None:
    ensure_qdrant_collection()

    client = get_qdrant_client()

    try:
        client.delete(
            collection_name=QDRANT_COLLECTION,
            points_selector=models.FilterSelector(
                filter=models.Filter(
                    must=[
                        models.FieldCondition(
                            key="source",
                            match=models.MatchValue(value=source),
                        )
                    ]
                )
            ),
        )
    except Exception:
        pass


# -----------------------------
# Public interface used by app
# -----------------------------

def get_or_create_collection():
    """
    Backward-compatible function.

    For Chroma, returns the Chroma collection.
    For Qdrant, ensures the collection exists and returns the Qdrant client.
    """
    if VECTOR_BACKEND == "qdrant":
        ensure_qdrant_collection()
        return get_qdrant_client()

    return get_chroma_collection()


def index_documents() -> int:
    if VECTOR_BACKEND == "qdrant":
        return index_documents_qdrant()

    return index_documents_chroma()


def search_notes(query: str, n_results: int = 3):
    if VECTOR_BACKEND == "qdrant":
        return search_notes_qdrant(query=query, n_results=n_results)

    return search_notes_chroma(query=query, n_results=n_results)


def count_vectors() -> int:
    if VECTOR_BACKEND == "qdrant":
        return count_vectors_qdrant()

    return count_vectors_chroma()


def delete_vectors_by_source(source: str) -> None:
    if VECTOR_BACKEND == "qdrant":
        delete_vectors_by_source_qdrant(source)
        return

    delete_vectors_by_source_chroma(source)


def reset_vectorstore_collection() -> None:
    if VECTOR_BACKEND == "qdrant":
        reset_qdrant_collection()
        return

    reset_chroma_collection()