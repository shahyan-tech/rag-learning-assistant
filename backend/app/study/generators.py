import json
from typing import Any, Dict

from langchain_core.prompts import ChatPromptTemplate # type: ignore
from langsmith import traceable # type: ignore
from app.rag.rag_chain import format_context, get_llm
from app.rag.vector_store import search_notes


def extract_json(text: str) -> Any:
    """
    Extract JSON safely from an LLM response.
    """
    text = text.strip()

    if text.startswith("```json"):
        text = text.replace("```json", "").replace("```", "").strip()

    if text.startswith("```"):
        text = text.replace("```", "").strip()

    try:
        return json.loads(text)
    except json.JSONDecodeError:
        pass

    first_array = text.find("[")
    last_array = text.rfind("]")

    if first_array != -1 and last_array != -1:
        return json.loads(text[first_array : last_array + 1])

    first_object = text.find("{")
    last_object = text.rfind("}")

    if first_object != -1 and last_object != -1:
        return json.loads(text[first_object : last_object + 1])

    raise ValueError("LLM did not return valid JSON.")


def get_context(topic: str, n_results: int):
    """
    Search ChromaDB for relevant chunks and format them for the LLM.
    """
    search_results = search_notes(
        query=topic,
        n_results=n_results,
    )

    context, sources = format_context(search_results)

    return context, sources

@traceable(name="Generate flashcards", run_type="chain")
def generate_flashcards(topic: str, count: int = 5, n_results: int = 4) -> Dict:
    context, sources = get_context(topic, n_results)

    system_prompt = """
You are an expert AI tutor.

Generate high-quality flashcards for learning.

Rules:
1. Prefer the uploaded notes context.
2. If the notes are not enough, use general knowledge.
3. Keep each flashcard clear and exam-friendly.
4. Return ONLY valid JSON.
5. Do not wrap the JSON in markdown.
6. Generate exactly the requested number of flashcards.

Return JSON in this exact format:
[
  {{
    "front": "Question side of the card",
    "back": "Answer side of the card"
  }}
]
"""

    prompt = ChatPromptTemplate.from_messages(
        [
            ("system", system_prompt),
            (
                "human",
                """
Topic:
{topic}

Number of flashcards:
{count}

Context from uploaded notes:
{context}

Generate the flashcards now.
""",
            ),
        ]
    )

    llm = get_llm()
    chain = prompt | llm

    response = chain.invoke(
        {
            "topic": topic,
            "count": count,
            "context": context,
        }
    )

    flashcards = extract_json(response.content)

    return {
        "topic": topic,
        "flashcards": flashcards,
        "sources": sources,
    }

@traceable(name="Generate quiz", run_type="chain")
def generate_quiz(
    topic: str,
    count: int = 5,
    difficulty: str = "beginner",
    n_results: int = 4,
) -> Dict:
    context, sources = get_context(topic, n_results)

    system_prompt = """
You are an expert AI tutor.

Generate multiple-choice quiz questions.

Rules:
1. Prefer the uploaded notes context.
2. If the notes are not enough, use general knowledge.
3. Each question must have exactly 4 options.
4. The correct_answer must exactly match one option.
5. Include a short explanation.
6. Return ONLY valid JSON.
7. Do not wrap the JSON in markdown.
8. Generate exactly the requested number of questions.

Return JSON in this exact format:
[
  {{
    "question": "Question text",
    "options": ["Option A", "Option B", "Option C", "Option D"],
    "correct_answer": "Correct option text",
    "explanation": "Why this answer is correct"
  }}
]
"""

    prompt = ChatPromptTemplate.from_messages(
        [
            ("system", system_prompt),
            (
                "human",
                """
Topic:
{topic}

Difficulty:
{difficulty}

Number of questions:
{count}

Context from uploaded notes:
{context}

Generate the quiz now.
""",
            ),
        ]
    )

    llm = get_llm()
    chain = prompt | llm

    response = chain.invoke(
        {
            "topic": topic,
            "difficulty": difficulty,
            "count": count,
            "context": context,
        }
    )

    questions = extract_json(response.content)

    return {
        "topic": topic,
        "difficulty": difficulty,
        "questions": questions,
        "sources": sources,
    }

@traceable(name="Generate mind map", run_type="chain")
def generate_mindmap(topic: str, n_results: int = 5) -> Dict:
    context, sources = get_context(topic, n_results)

    system_prompt = """
You are an expert AI tutor.

Generate a structured mind map for a learning topic.

Rules:
1. Prefer the uploaded notes context.
2. If the notes are not enough, use general knowledge.
3. Keep node titles short and clear.
4. Use a maximum depth of 3 levels.
5. Return ONLY valid JSON.
6. Do not wrap the JSON in markdown.

Return JSON in this exact format:
{{
  "title": "Main Topic",
  "children": [
    {{
      "title": "Subtopic",
      "children": [
        {{
          "title": "Detail",
          "children": []
        }}
      ]
    }}
  ]
}}
"""

    prompt = ChatPromptTemplate.from_messages(
        [
            ("system", system_prompt),
            (
                "human",
                """
Topic:
{topic}

Context from uploaded notes:
{context}

Generate the mind map now.
""",
            ),
        ]
    )

    llm = get_llm()
    chain = prompt | llm

    response = chain.invoke(
        {
            "topic": topic,
            "context": context,
        }
    )

    mind_map = extract_json(response.content)

    return {
        "topic": topic,
        "mind_map": mind_map,
        "sources": sources,
    }