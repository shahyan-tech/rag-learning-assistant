\# RAG Learning Assistant



A full-stack AI learning platform for studying Machine Learning, Deep Learning, Generative AI, and Agentic AI using uploaded notes.



Users can upload PDFs, PPTX files, Jupyter notebooks, Markdown, or text files, then ask questions, generate flashcards, create quizzes, build mind maps, and view history.



\## Features



\- RAG chatbot using uploaded documents

\- General LLM fallback when no relevant notes are found

\- Flashcard generation

\- Quiz generation

\- Mind map generation

\- Chat history saved in database

\- Study artifacts saved in database

\- Document upload and indexing

\- LangSmith tracing

\- LangGraph workflow for RAG routing

\- React + Vite frontend

\- FastAPI backend

\- Chroma vector store

\- SQLite for local development



\## Tech Stack



\### Frontend

\- React

\- Vite

\- Axios

\- CSS



\### Backend

\- FastAPI

\- LangChain

\- LangGraph

\- LangSmith

\- Groq LLM API

\- ChromaDB

\- SQLAlchemy

\- SQLite



\## Project Structure



```text

rag-learning-assistant-v2/

├── backend/

│   ├── app/

│   │   ├── api/

│   │   ├── db/

│   │   ├── ingestion/

│   │   ├── models/

│   │   ├── rag/

│   │   ├── study/

│   │   └── main.py

│   └── requirements.txt

├── frontend/

│   ├── src/

│   └── package.json

├── data/

│   ├── raw/

│   └── vectorstore/

└── README.md

