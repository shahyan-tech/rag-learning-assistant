# RAG Learning Assistant

A full-stack AI-powered learning platform that helps users learn Machine Learning, Deep Learning, Generative AI, and Agentic AI from their own uploaded notes.

Users can upload PDFs, PowerPoint slides, Jupyter notebooks, Markdown files, or text files, then ask questions, generate flashcards, create quizzes, build mind maps, and save learning history.

The project uses a complete RAG pipeline with LangChain, LangGraph, LangSmith, FastAPI, React, PostgreSQL, Qdrant, Docker, Kubernetes, Vercel, and Render.

---

## Live Demo

Frontend:

```text
https://rag-learning-assistant-pi.vercel.app/
```

Backend API:

```text
https://rag-learning-assistant-vbdy.onrender.com
```

API Docs:

```text
https://rag-learning-assistant-vbdy.onrender.com/docs
```

---

## What This Project Does

The application supports two learning modes:

### 1. General AI Learning Mode

If the user has not uploaded any documents, the chatbot still works using general LLM knowledge.

Example:

```text
User: What is deep learning?
Assistant: This answer is from general AI knowledge, not from the uploaded notes...
```

### 2. RAG-Based Learning Mode

If the user uploads and indexes documents, the chatbot answers using those uploaded notes.

The answer includes source references such as file name, page, slide, or notebook cell.

Example:

```text
User uploads a PDF about Linear Regression.
User asks: What is the normal equation?
Assistant answers from the uploaded PDF and shows the source.
```

---

## Main Features

* RAG chatbot using uploaded documents
* General LLM fallback when no relevant notes are found
* Upload PDFs, PPTX, IPYNB, TXT, and MD files
* Document parsing and chunking
* Vector search using Qdrant Cloud or local ChromaDB
* Flashcard generation
* Quiz generation
* Mind map generation
* Chat history
* Study artifact library
* Saved flashcards, quizzes, and mind maps
* LangGraph workflow for RAG routing
* LangSmith tracing and observability
* PostgreSQL database for production
* SQLite support for local development
* Dockerized backend and frontend
* Docker Compose full-stack setup
* Kubernetes manifests for local orchestration
* Frontend deployed on Vercel
* Backend deployed on Render

---

## Tech Stack

### Frontend

* React
* Vite
* Axios
* CSS
* Nginx for Docker production serving

### Backend

* FastAPI
* Python
* LangChain
* LangGraph
* LangSmith
* Groq LLM API
* SQLAlchemy
* PostgreSQL
* SQLite for local development

### RAG and Vector Search

* Qdrant Cloud for production vector database
* ChromaDB for local vector database
* Document chunking with LangChain text splitters
* Semantic search over uploaded notes

### Document Processing

* pypdf for PDFs
* python-pptx for PowerPoint files
* nbformat for Jupyter notebooks
* Plain text parsing for TXT and MD files

### DevOps and Deployment

* Docker
* Docker Compose
* Kubernetes
* Vercel for frontend deployment
* Render for backend deployment
* Render PostgreSQL
* Qdrant Cloud

---

## Final Architecture

```text
User Browser
   |
   v
Vercel React Frontend
   |
   | HTTP API requests
   v
Render FastAPI Backend
   |
   |---- PostgreSQL
   |       Stores chat sessions, messages, documents, and study artifacts
   |
   |---- Qdrant Cloud
   |       Stores embeddings and performs semantic search
   |
   |---- Groq LLM
   |       Generates answers, flashcards, quizzes, and mind maps
   |
   |---- LangGraph
   |       Controls the RAG workflow
   |
   |---- LangSmith
           Traces and debugs LLM workflow
```

---

## RAG Workflow

The core RAG pipeline works like this:

```text
User uploads documents
   |
   v
Backend extracts text from PDF, PPTX, IPYNB, TXT, or MD
   |
   v
Text is split into chunks
   |
   v
Chunks are converted into embeddings
   |
   v
Embeddings are stored in Qdrant or Chroma
   |
   v
User asks a question
   |
   v
Question is used to retrieve relevant chunks
   |
   v
LangGraph checks if retrieved context is relevant
   |
   |---- If relevant:
   |       Answer from uploaded notes
   |
   |---- If not relevant:
           Answer from general LLM knowledge
```

---

## LangGraph Workflow

The chatbot uses LangGraph to route each question through a structured workflow.

```text
START
  |
  v
retrieve_context
  |
  v
grade_relevance
  |
  v
conditional_route
  |
  |---- answer_from_notes
  |
  |---- answer_general
  |
  v
END
```

### Why LangGraph?

LangGraph was used to make the RAG process more structured, visible, and easier to extend.

Instead of one large function, the RAG pipeline is divided into clear nodes:

* Retrieve context
* Grade relevance
* Route conditionally
* Answer from uploaded notes
* Answer from general AI knowledge

This also makes debugging easier in LangSmith.

---

## LangSmith Observability

LangSmith is used for tracing and debugging the LLM application.

It helps inspect:

* User question
* Retrieved context
* LangGraph node execution
* Prompt sent to the LLM
* Final model response
* Errors and latency

This is useful because RAG applications are difficult to debug without visibility into each step.

---

## Database Design

The project uses SQLAlchemy ORM.

### Main Tables

```text
documents
```

Stores uploaded document metadata.

```text
chat_sessions
```

Stores chat conversations.

```text
chat_messages
```

Stores user and assistant messages.

```text
study_artifacts
```

Stores generated flashcards, quizzes, and mind maps.

---

## Project Structure

```text
rag-learning-assistant/
|
|-- backend/
|   |-- app/
|   |   |-- api/
|   |   |   |-- chat.py
|   |   |   |-- documents.py
|   |   |   |-- study.py
|   |   |   |-- database.py
|   |   |   |-- observability.py
|   |   |
|   |   |-- db/
|   |   |   |-- models.py
|   |   |   |-- session.py
|   |   |
|   |   |-- ingestion/
|   |   |   |-- loaders.py
|   |   |
|   |   |-- models/
|   |   |   |-- chat.py
|   |   |   |-- document.py
|   |   |   |-- study.py
|   |   |
|   |   |-- rag/
|   |   |   |-- rag_chain.py
|   |   |   |-- vector_store.py
|   |   |
|   |   |-- study/
|   |   |   |-- generators.py
|   |   |
|   |   |-- main.py
|   |
|   |-- Dockerfile
|   |-- requirements.txt
|   |-- .env.example
|
|-- frontend/
|   |-- src/
|   |   |-- App.jsx
|   |   |-- App.css
|   |   |-- main.jsx
|   |
|   |-- Dockerfile
|   |-- nginx.conf
|   |-- package.json
|   |-- .env.example
|
|-- data/
|   |-- raw/
|   |-- vectorstore/
|
|-- k8s/
|   |-- namespace.yaml
|   |-- backend-deployment.yaml
|   |-- backend-service.yaml
|   |-- frontend-deployment.yaml
|   |-- frontend-service.yaml
|
|-- docker-compose.yml
|-- README.md
```

---

## Local Development Setup

### 1. Clone the Repository

```bash
git clone https://github.com/shahyan-tech/rag-learning-assistant.git
cd rag-learning-assistant
```

---

## Backend Setup

Go to the backend folder:

```bash
cd backend
```

Create virtual environment:

```bash
python -m venv .venv
```

Activate virtual environment on Windows:

```bash
.\.venv\Scripts\Activate.ps1
```

Install dependencies:

```bash
pip install -r requirements.txt
```

Create environment file:

```bash
copy .env.example .env
```

Add your real API keys inside `.env`.

Run backend:

```bash
uvicorn app.main:app --reload
```

Backend will run at:

```text
http://127.0.0.1:8000
```

API docs:

```text
http://127.0.0.1:8000/docs
```

Health check:

```text
http://127.0.0.1:8000/health
```

---

## Frontend Setup

Open a new terminal:

```bash
cd frontend
```

Install dependencies:

```bash
npm install
```

Create environment file:

```bash
copy .env.example .env
```

Set backend URL:

```env
VITE_API_BASE_URL=http://127.0.0.1:8000
```

Run frontend:

```bash
npm run dev
```

Frontend will run at:

```text
http://localhost:5173
```

---

## Environment Variables

### Backend `.env`

```env
GROQ_API_KEY=your_groq_api_key_here
GROQ_MODEL=llama-3.1-8b-instant

LANGSMITH_TRACING=false
LANGSMITH_API_KEY=your_langsmith_api_key_here
LANGSMITH_PROJECT=rag-learning-assistant

NOTES_DISTANCE_THRESHOLD=1.35
MIN_CONTEXT_CHARS=250

DATABASE_URL=sqlite:///../data/rag_learning.db

VECTOR_BACKEND=chroma

QDRANT_URL=your_qdrant_cloud_url_here
QDRANT_API_KEY=your_qdrant_api_key_here
QDRANT_COLLECTION=learning_notes
QDRANT_EMBEDDING_MODEL=BAAI/bge-small-en
```

### Frontend `.env`

```env
VITE_API_BASE_URL=http://127.0.0.1:8000
```

---

## Production Environment

For production deployment, these values were used:

### Frontend

Hosted on Vercel.

```env
VITE_API_BASE_URL=https://rag-learning-assistant-vbdy.onrender.com
```

### Backend

Hosted on Render.

Important Render environment variables:

```env
DATABASE_URL=your_render_postgres_url

GROQ_API_KEY=your_groq_api_key
GROQ_MODEL=llama-3.1-8b-instant

LANGSMITH_TRACING=true
LANGSMITH_API_KEY=your_langsmith_api_key
LANGSMITH_PROJECT=rag-learning-assistant

VECTOR_BACKEND=qdrant
QDRANT_URL=your_qdrant_cloud_url
QDRANT_API_KEY=your_qdrant_api_key
QDRANT_COLLECTION=learning_notes
QDRANT_EMBEDDING_MODEL=BAAI/bge-small-en

NOTES_DISTANCE_THRESHOLD=0.55
MIN_CONTEXT_CHARS=250
PYTHON_VERSION=3.12.7
```

---

## Docker Setup

Build and run the full app using Docker Compose:

```bash
docker compose up --build
```

Frontend:

```text
http://localhost:5173
```

Backend:

```text
http://localhost:8000
```

Stop containers:

```bash
docker compose down
```

---

## Kubernetes Setup

This project also includes Kubernetes manifests for local learning using Docker Desktop Kubernetes.

Create namespace:

```bash
kubectl apply -f k8s/namespace.yaml
```

Create backend secret from `.env`:

```bash
kubectl create secret generic rag-backend-env \
  --from-env-file=backend/.env \
  -n rag-learning
```

Apply deployments and services:

```bash
kubectl apply -f k8s/backend-deployment.yaml
kubectl apply -f k8s/backend-service.yaml
kubectl apply -f k8s/frontend-deployment.yaml
kubectl apply -f k8s/frontend-service.yaml
```

Check pods:

```bash
kubectl get pods -n rag-learning
```

Check services:

```bash
kubectl get svc -n rag-learning
```

If localhost does not work directly, use port forwarding:

```bash
kubectl port-forward -n rag-learning service/rag-backend-service 8000:8000
kubectl port-forward -n rag-learning service/rag-frontend-service 5173:5173
```

---

## API Endpoints

### Chat

```text
POST /chat/ask
GET /chat/sessions
GET /chat/sessions/{session_id}
DELETE /chat/sessions/{session_id}
```

### Documents

```text
GET /documents/raw
POST /documents/upload
POST /documents/upload-multiple
POST /documents/index
POST /documents/sync
DELETE /documents/{document_id}
DELETE /documents/clear-all
```

### Study Tools

```text
POST /study/flashcards
POST /study/quiz
POST /study/mindmap
GET /study/artifacts
GET /study/artifacts/{artifact_id}
DELETE /study/artifacts/{artifact_id}
```

### Observability

```text
GET /observability/langsmith
GET /observability/langgraph
GET /observability/vectorstore
```

### Database

```text
GET /database/status
```

---

## Important Security Note

This project is currently suitable as a portfolio/demo application.

Before using it as a real public product, the next important step is authentication.

Currently:

* Users are not separated.
* Uploaded documents are not isolated per user.
* Chat history is shared through the same backend database.
* Vector collections are not separated per user.

Recommended next improvements:

* Add user authentication
* Add per-user documents
* Add per-user chat history
* Add per-user vector namespaces or collections
* Add rate limiting
* Add background document indexing
* Add file storage such as S3, Cloudflare R2, or Supabase Storage

---

## What I Learned

This project helped me understand how real AI applications are built beyond simple prompting.

I learned:

* How RAG works end to end
* How to parse and chunk documents
* How to store and search embeddings
* How to use vector databases
* How to build FastAPI backend APIs
* How to build React frontend dashboards
* How to save chats and study artifacts in a database
* How to use LangChain for LLM calls
* How to use LangGraph for workflow routing
* How to use LangSmith for tracing
* How to deploy frontend and backend separately
* How to use PostgreSQL in production
* How to use Qdrant Cloud for vector search
* How to Dockerize a full-stack app
* How to create Kubernetes manifests

---

## Future Improvements

* User authentication
* Per-user document isolation
* Per-user vector collections
* Background indexing with progress tracking
* Better RAG evaluation
* Better document parsing for scanned PDFs
* File storage using S3 or Cloudflare R2
* Admin dashboard
* Rate limiting
* Streaming chat responses
* Better UI for source previews
* Team workspace support

---

## Author

Built by Shahyan.

GitHub:

```text
https://github.com/shahyan-tech/rag-learning-assistant
```

Live Demo:

```text
https://rag-learning-assistant-pi.vercel.app/
```
