from app.ingestion.loaders import load_documents, chunk_documents


def main():
    print("Starting document ingestion...")

    documents = load_documents()
    print(f"Loaded documents/pages/slides/cells: {len(documents)}")

    if not documents:
        print("No documents found. Add PDF, PPTX, IPYNB, TXT, or MD files inside data/raw.")
        return

    chunks = chunk_documents(documents)
    print(f"Created chunks: {len(chunks)}")

    print("\n--- First Chunk Preview ---")
    print(chunks[0].page_content[:800])

    print("\n--- First Chunk Metadata ---")
    print(chunks[0].metadata)


if __name__ == "__main__":
    main()