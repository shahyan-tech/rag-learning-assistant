import os
from typing import Dict, List, Literal, Tuple, TypedDict

from dotenv import load_dotenv # type: ignore
from langchain_core.prompts import ChatPromptTemplate # type: ignore
from langchain_groq import ChatGroq # type: ignore
from langgraph.graph import END, START, StateGraph # type: ignore
from langsmith import traceable # type: ignore

from app.rag.vector_store import search_notes


load_dotenv()


NOTES_DISTANCE_THRESHOLD = float(os.getenv("NOTES_DISTANCE_THRESHOLD", "1.35"))
MIN_CONTEXT_CHARS = int(os.getenv("MIN_CONTEXT_CHARS", "250"))


NOTES_SYSTEM_PROMPT = """
You are a helpful AI tutor for Machine Learning, Deep Learning, Generative AI, and Agentic AI.

You must answer using the provided context from the user's uploaded notes.

Rules:
1. Use simple teaching language.
2. If the answer is in the context, explain it clearly.
3. Do not invent facts outside the provided context.
4. Mention the source file and page/slide/cell when useful.
"""


GENERAL_SYSTEM_PROMPT = """
You are a helpful AI tutor for Machine Learning, Deep Learning, Generative AI, and Agentic AI.

The uploaded notes did not contain enough relevant information for this question.

Rules:
1. Answer using general AI knowledge.
2. Be clear and educational.
3. Start the answer with this sentence exactly:
"This answer is from general AI knowledge, not from the uploaded notes."
4. Do not pretend that the answer came from uploaded notes.
"""


notes_prompt = ChatPromptTemplate.from_messages(
    [
        ("system", NOTES_SYSTEM_PROMPT),
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


general_prompt = ChatPromptTemplate.from_messages(
    [
        ("system", GENERAL_SYSTEM_PROMPT),
        (
            "human",
            """
Question:
{question}

Answer clearly.
""",
        ),
    ]
)


class RAGState(TypedDict, total=False):
    question: str
    n_results: int

    search_results: dict
    context: str
    sources: List[Dict]

    is_relevant: bool

    answer: str
    answer_type: str
    note: str


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


@traceable(name="Check context relevance", run_type="chain")
def is_context_relevant(context: str, sources: List[Dict]) -> bool:
    """
    Decide whether retrieved notes are relevant enough.

    In Chroma distance:
    - lower distance usually means better match
    - higher distance usually means weaker match

    This threshold is adjustable in .env using:
    NOTES_DISTANCE_THRESHOLD=1.35
    """
    if not context.strip():
        return False

    if len(context.strip()) < MIN_CONTEXT_CHARS:
        return False

    if not sources:
        return False

    best_distance = min(source["distance"] for source in sources)

    return best_distance <= NOTES_DISTANCE_THRESHOLD


@traceable(name="LangGraph retrieve context", run_type="chain")
def retrieve_context_node(state: RAGState) -> RAGState:
    """
    LangGraph node:
    Search vector DB and format context.
    """
    question = state["question"]
    n_results = state.get("n_results", 4)

    search_results = search_notes(
        query=question,
        n_results=n_results,
    )

    context, sources = format_context(search_results)

    return {
        "search_results": search_results,
        "context": context,
        "sources": sources,
    }


@traceable(name="LangGraph grade relevance", run_type="chain")
def grade_relevance_node(state: RAGState) -> RAGState:
    """
    LangGraph node:
    Decide whether uploaded notes are strong enough to answer from.
    """
    relevant = is_context_relevant(
        context=state.get("context", ""),
        sources=state.get("sources", []),
    )

    return {
        "is_relevant": relevant,
    }


def route_after_relevance(
    state: RAGState,
) -> Literal["answer_from_notes", "answer_general"]:
    """
    LangGraph conditional edge:
    Choose the next node.
    """
    if state.get("is_relevant"):
        return "answer_from_notes"

    return "answer_general"


@traceable(name="LangGraph answer from notes", run_type="chain")
def answer_from_notes_node(state: RAGState) -> RAGState:
    """
    LangGraph node:
    Generate answer using uploaded-note context.
    """
    llm = get_llm()
    chain = notes_prompt | llm

    response = chain.invoke(
        {
            "question": state["question"],
            "context": state.get("context", ""),
        }
    )

    return {
        "answer": response.content,
        "answer_type": "notes",
        "note": "Answered from uploaded notes.",
    }


@traceable(name="LangGraph answer general", run_type="chain")
def answer_general_node(state: RAGState) -> RAGState:
    """
    LangGraph node:
    Generate general answer when uploaded notes are weak or empty.
    """
    llm = get_llm()
    chain = general_prompt | llm

    response = chain.invoke(
        {
            "question": state["question"],
        }
    )

    return {
        "answer": response.content,
        "answer_type": "general",
        "note": (
            "Uploaded notes did not contain enough relevant information, "
            "so the answer came from general AI knowledge."
        ),
        "sources": [],
    }


def build_rag_graph():
    """
    Build and compile the LangGraph RAG workflow.
    """
    graph = StateGraph(RAGState)

    graph.add_node("retrieve_context", retrieve_context_node)
    graph.add_node("grade_relevance", grade_relevance_node)
    graph.add_node("answer_from_notes", answer_from_notes_node)
    graph.add_node("answer_general", answer_general_node)

    graph.add_edge(START, "retrieve_context")
    graph.add_edge("retrieve_context", "grade_relevance")

    graph.add_conditional_edges(
        "grade_relevance",
        route_after_relevance,
        {
            "answer_from_notes": "answer_from_notes",
            "answer_general": "answer_general",
        },
    )

    graph.add_edge("answer_from_notes", END)
    graph.add_edge("answer_general", END)

    return graph.compile()


RAG_GRAPH = build_rag_graph()


@traceable(name="RAG answer question", run_type="chain")
def answer_question(question: str, n_results: int = 4) -> Dict:
    """
    Public function used by API.

    Under the hood this now runs a LangGraph workflow:
    1. Retrieve context.
    2. Grade relevance.
    3. Route to notes answer or general answer.
    4. Return final answer.
    """
    result = RAG_GRAPH.invoke(
        {
            "question": question,
            "n_results": n_results,
        }
    )

    return {
        "answer": result.get("answer", ""),
        "sources": result.get("sources", []),
        "answer_type": result.get("answer_type", "unknown"),
        "note": result.get("note"),
    }