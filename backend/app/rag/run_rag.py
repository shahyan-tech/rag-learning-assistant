import sys

from app.rag.rag_chain import answer_question


def main():
    question = " ".join(sys.argv[1:]).strip()

    if not question:
        question = "Explain the normal equation in linear regression."

    print(f"Question: {question}")
    print("=" * 80)

    result = answer_question(question)

    print("\nAnswer Type:")
    print(result["answer_type"])

    print("\nNote:")
    print(result["note"])

    print("\nAnswer:")
    print(result["answer"])

    print("\nSources:")
    if result["sources"]:
        for source in result["sources"]:
            print(
                f"- {source['source']} | part: {source['location']} | distance: {source['distance']}"
            )
    else:
        print("- No uploaded-note sources used.")


if __name__ == "__main__":
    main()