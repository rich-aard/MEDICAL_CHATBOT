# 🏥 Medical RAG Chatbot

A **Retrieval-Augmented Generation (RAG)** chatbot for medical question answering, built with FastAPI, LangChain, FAISS, domain-specific PubMedBERT embeddings, and Llama 3.3 70B via Groq. The system retrieves semantically relevant chunks from a local medical knowledge base before generating grounded, context-aware answers.

> ⚠️ **Disclaimer:** This project is for educational and research purposes only. It does not provide medical diagnosis, treatment recommendations, or professional healthcare advice. Always consult a qualified healthcare professional for medical decisions.

---

## Table of Contents

- [Overview](#overview)
- [Architecture](#architecture)
- [Tech Stack](#tech-stack)
- [Project Structure](#project-structure)
- [How It Works](#how-it-works)
- [Getting Started](#getting-started)
  - [Prerequisites](#prerequisites)
  - [Installation](#installation)
  - [Environment Variables](#environment-variables)
  - [Build the Vector Store](#build-the-vector-store)
  - [Run the App](#run-the-app)
- [Docker](#docker)
- [CI/CD with Jenkins](#cicd-with-jenkins)
- [API Reference](#api-reference)
- [Configuration](#configuration)
- [Logging](#logging)

---

## Overview

The Medical RAG Chatbot ingests medical PDF documents, chunks and embeds them using a biomedical-domain language model, and indexes them in a local FAISS vector store. At query time, semantically similar chunks are retrieved and passed alongside the user's question to Llama 3.3 70B (served via Groq) to produce a concise, grounded answer.

Key design goals:
- **Domain accuracy** — PubMedBERT embeddings are trained on biomedical literature, making retrieval significantly more precise than general-purpose models.
- **Low latency** — Groq's hardware inference layer keeps generation fast even for a 70B-parameter model.
- **Self-contained** — the vector store is built locally from your own documents; no external knowledge base dependency.
- **Production-ready** — containerized with a multi-stage Dockerfile, managed with `uv`, and deployable via a Jenkins pipeline.

---

## Architecture

```
┌─────────────────────┐
│   Medical PDF Files │
└──────────┬──────────┘
           │  PyPDF loader
           ▼
┌─────────────────────┐
│    Text Chunking    │  chunk_size=1000, overlap=200
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│  PubMedBERT         │  NeuML/pubmedbert-base-embeddings
│  Embeddings         │
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│  FAISS Vector Store │  persisted at data/vector_store/faiss_index/
└──────────┬──────────┘
           │
           ▼
User Query ──► Semantic Retriever (top-k=3)
           │
           ▼
┌─────────────────────┐
│  LangChain RAG Chain│
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│  Groq LLM           │  llama-3.3-70b-versatile
└──────────┬──────────┘
           │
           ▼
      Final Answer
```

---

## Tech Stack

| Layer | Technology |
|---|---|
| Web framework | FastAPI + Uvicorn |
| RAG orchestration | LangChain, LangChain-Community |
| LLM provider | Groq (`langchain-groq`) |
| Embeddings | `NeuML/pubmedbert-base-embeddings` via `langchain-huggingface` |
| Vector store | FAISS CPU (`faiss-cpu`) |
| PDF parsing | PyPDF |
| Frontend | Jinja2 templates + HTML/CSS |
| Package management | Astral `uv` |
| Containerization | Docker (multi-stage build, Python 3.12-slim) |
| CI/CD | Jenkins declarative pipeline |
| Registry | Docker Hub (`thefool23/medical-chatbot`) |

**Python version:** `>=3.12, <3.13`

---

## Project Structure

```
MEDICAL_CHATBOT/
│
├── app/
│   ├── app.py                  # FastAPI application entrypoint
│   │
│   ├── common/
│   │   ├── logger.py           # Structured logging setup
│   │   └── custom_exception.py # Custom exception classes
│   │
│   ├── components/
│   │   ├── data_loader.py      # PDF ingestion + vector store builder
│   │   ├── embedding.py        # PubMedBERT embedding model wrapper
│   │   ├── llm.py              # Groq LLM configuration
│   │   ├── loader.py           # Document loading utilities
│   │   ├── retriever.py        # FAISS retriever setup
│   │   └── vector_store.py     # FAISS index creation/loading
│   │
│   ├── config/
│   │   └── config.py           # Centralised configuration constants
│   │
│   └── templates/
│       └── index.html          # Chat UI (Jinja2)
│
├── data/
│   ├── raw_documents/          # Drop your medical PDFs here
│   └── vector_store/
│       └── faiss_index/        # Persisted FAISS index (auto-generated)
│
├── logs/                       # Runtime log files
│
├── custom_jenkins/             # Jenkins agent configuration
├── Dockerfile
├── Jenkinsfile
├── pyproject.toml
├── requirements.txt            # Compiled lockfile (generated by uv)
└── .python-version             # Pins Python 3.12
```

---

## How It Works

**Step 1 — Ingest documents.** Medical PDF files placed in `data/raw_documents/` are loaded and parsed by PyPDF.

**Step 2 — Chunk.** Documents are split into overlapping 1000-token chunks (200-token overlap) to preserve sentence context across boundaries.

**Step 3 — Embed.** Each chunk is encoded by `NeuML/pubmedbert-base-embeddings`, a model pretrained on PubMed abstracts and clinical notes, producing dense 768-dimensional vectors.

**Step 4 — Index.** Vectors are stored in a FAISS flat index on disk at `data/vector_store/faiss_index/` for fast approximate nearest-neighbour search.

**Step 5 — Retrieve.** At inference time, the user's query is embedded with the same model and the top-3 nearest chunks are returned.

**Step 6 — Generate.** The retrieved chunks are injected into a LangChain prompt and sent to `llama-3.3-70b-versatile` on Groq. The model produces a concise, context-grounded answer that is streamed back to the UI.

---

## Getting Started

### Prerequisites

- Python 3.12
- [Astral `uv`](https://docs.astral.sh/uv/) installed globally
- A [Groq API key](https://console.groq.com/)
- A [Hugging Face token](https://huggingface.co/settings/tokens) (for downloading the embedding model)

### Installation

```bash
# 1. Clone the repository
git clone https://github.com/rich-aard/MEDICAL_CHATBOT.git
cd MEDICAL_CHATBOT

# 2. Compile a locked requirements file (CPU-only PyTorch)
uv pip compile pyproject.toml \
  --find-links https://download.pytorch.org/whl/cpu \
  -o requirements.txt

# 3. Create the virtual environment
uv venv .venv

# 4. Activate it
# Linux / macOS:
source .venv/bin/activate
# Windows:
.venv\Scripts\activate

# 5. Install dependencies
uv pip sync requirements.txt \
  --find-links https://download.pytorch.org/whl/cpu
```

### Environment Variables

Create a `.env` file in the project root:

```env
GROQ_API_KEY=your_groq_api_key_here
HF_TOKEN=your_huggingface_token_here
```

### Build the Vector Store

Place your medical PDF files into `data/raw_documents/`, then run:

```bash
python app/components/data_loader.py
```

This will chunk, embed, and persist the FAISS index. You only need to re-run this when your document set changes.

### Run the App

```bash
uvicorn app.app:app --reload
```

Open your browser at [http://localhost:8000](http://localhost:8000).

---

## Docker

### Build

```bash
docker build -t medical-chatbot .
```

The Dockerfile uses a **two-stage build**: a `builder` stage installs all dependencies with `uv` into a venv, and a lean `runner` stage (Python 3.12-slim) copies only the venv and application code, keeping the final image small.

### Run

```bash
docker run -p 8000:8000 \
  -e GROQ_API_KEY=your_key \
  -e HF_TOKEN=your_token \
  medical-chatbot
```

> **Note:** The vector store is not pre-bundled into the image. Mount your pre-built index or add a build step to `data_loader.py` as part of your image build if you want a fully self-contained image.

---

## CI/CD with Jenkins

The `Jenkinsfile` defines a declarative pipeline with the following stages:

1. **Checkout** — pulls the latest commit from the remote repository.
2. **Build** — compiles the Docker image locally.
3. **Tag** — appends the Jenkins build number as an image tag for traceability.
4. **Push** — delivers the tagged image to Docker Hub under `thefool23/medical-chatbot`.
5. **Cleanup** — removes intermediate build artifacts to keep the workspace clean.

The `custom_jenkins/` directory contains supporting configuration for the Jenkins agent environment.

---

## API Reference

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/` | Renders the chat UI |
| `POST` | `/` | Accepts a `prompt` form field and returns a generated answer |
| `GET` | `/clear` | Clears the current session history |

**Example POST request:**

```bash
curl -X POST http://localhost:8000/ \
  -F "prompt=What are the symptoms of type 2 diabetes?"
```

---

## Configuration

Key parameters live in `app/config/config.py`:

| Parameter | Default | Description |
|-----------|---------|-------------|
| `CHUNK_SIZE` | `1000` | Token length of each document chunk |
| `CHUNK_OVERLAP` | `200` | Overlap between consecutive chunks |
| `EMBEDDING_MODEL` | `NeuML/pubmedbert-base-embeddings` | Sentence-transformer model for encoding |
| `LLM_MODEL` | `llama-3.3-70b-versatile` | Groq model ID |
| `TOP_K` | `3` | Number of chunks retrieved per query |
| `VECTOR_STORE_PATH` | `data/vector_store/faiss_index/` | On-disk index location |

---

## Logging

Runtime logs are written to `logs/`. The logging framework captures:

- Application startup and shutdown events
- Vector store load/index operations
- Retrieval queries and chunk counts
- LLM API authentication and response status
- Exceptions and custom error traces

Log files are excluded from Docker images via `.dockerignore`.