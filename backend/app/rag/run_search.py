from app.rag.vector_store import search_notes


def main():
    query = "What is the normal equation in linear regression?"

    print(f"Search query: {query}")
    print("-" * 80)

    results = search_notes(query=query, n_results=3)

    documents = results.get("documents", [[]])[0]
    metadatas = results.get("metadatas", [[]])[0]
    distances = results.get("distances", [[]])[0]

    for index, document in enumerate(documents, start=1):
        metadata = metadatas[index - 1]
        distance = distances[index - 1]

        print(f"\nResult {index}")
        print(f"Source: {metadata.get('source')}")
        print(f"Page/Slide/Cell: {metadata.get('page') or metadata.get('slide') or metadata.get('cell')}")
        print(f"Distance: {distance}")
        print("-" * 80)
        print(document[:700])


if __name__ == "__main__":
    main()