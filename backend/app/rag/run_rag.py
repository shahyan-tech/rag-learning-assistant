import sys

from app.rag.rag_chain import answer_question


def main():
    question = " ".join(sys.argv[1:]).strip()

    if not question:
        question = "Explain the normal equation in linear regression."

    print(f"Question: {question}")
    print("=" * 80)

    result = answer_question(question)

    print("\nAnswer:")
    print(result["answer"])

    print("\nSources:")
    for source in result["sources"]:
        print(
            f"- {source['source']} | part: {source['location']} | distance: {source['distance']}"
        )


if __name__ == "__main__":
    main()