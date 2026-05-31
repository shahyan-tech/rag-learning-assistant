import os
from typing import Dict, List, Tuple

from dotenv import load_dotenv # type: ignore
from langchain_core.prompts import ChatPromptTemplate # type: ignore
from langchain_groq import ChatGroq # type: ignore

from app.rag.vector_store import search_notes


load_dotenv()


SYSTEM_PROMPT = """
You are a helpful AI tutor for Machine Learning, Deep Learning, Generative AI, and Agentic AI.

You must answer using the provided context from the user's notes.

Rules:
1. Use simple teaching language.
2. If the answer is in the context, explain it clearly.
3. If the context is not enough, say: "I do not have enough information in the uploaded notes."
4. Do not invent facts.
5. Mention the source file and page/slide/cell when useful.
"""


prompt = ChatPromptTemplate.from_messages(
    [
        ("system", SYSTEM_PROMPT),
        (
            "human",
            """
Question:
{question}

Context from uploaded notes:
{context}

Now answer the question clearly.
""",
        ),
    ]
)


def get_llm() -> ChatGroq:
    """
    Create the LLM object.

    The API key and model name come from the .env file.
    """
    api_key = os.getenv("GROQ_API_KEY")
    model = os.getenv("GROQ_MODEL", "llama-3.1-8b-instant")

    if not api_key:
        raise ValueError(
            "GROQ_API_KEY is missing. Add it to backend/.env first."
        )

    return ChatGroq(
        model=model,
        temperature=0,
        api_key=api_key,
    )


def format_context(search_results: dict) -> Tuple[str, List[Dict]]:
    """
    Convert Chroma search results into clean text context for the LLM.
    Also return source information for display.
    """
    documents = search_results.get("documents", [[]])[0]
    metadatas = search_results.get("metadatas", [[]])[0]
    distances = search_results.get("distances", [[]])[0]

    context_blocks = []
    sources = []

    for index, document in enumerate(documents, start=1):
        metadata = metadatas[index - 1]
        distance = distances[index - 1]

        source = metadata.get("source", "unknown")
        location = (
            metadata.get("page")
            or metadata.get("slide")
            or metadata.get("cell")
            or "unknown"
        )

        source_label = f"{source}, part {location}"

        context_blocks.append(
            f"[Source {index}: {source_label}]\n{document}"
        )

        sources.append(
            {
                "source": source,
                "location": location,
                "distance": distance,
            }
        )

    context = "\n\n".join(context_blocks)

    return context, sources


def answer_question(question: str, n_results: int = 4) -> Dict:
    """
    Full RAG flow:
    1. Search relevant chunks.
    2. Format context.
    3. Send question + context to LLM.
    4. Return answer and sources.
    """
    search_results = search_notes(
        query=question,
        n_results=n_results,
    )

    context, sources = format_context(search_results)

    if not context.strip():
        return {
            "answer": "I do not have enough information in the uploaded notes.",
            "sources": [],
        }

    llm = get_llm()
    chain = prompt | llm

    response = chain.invoke(
        {
            "question": question,
            "context": context,
        }
    )

    return {
        "answer": response.content,
        "sources": sources,
    }