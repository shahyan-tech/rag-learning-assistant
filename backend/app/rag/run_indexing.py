from app.rag.vector_store import index_documents


def main():
    print("Starting vector indexing...")

    total_chunks = index_documents()

    print(f"Indexed chunks into vector database: {total_chunks}")
    print("Vector indexing completed.")


if __name__ == "__main__":
    main()