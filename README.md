# Medical RAG Chatbot

A **Retrieval-Augmented Generation (RAG)** chatbot for medical question answering, built with FastAPI, LangChain, FAISS, biomedical PubMedBERT embeddings, and gpt-oss-120b via Groq. It retrieves relevant chunks from a local collection of medical PDFs and asks the LLM to answer using only that context.

> ⚠️ **Disclaimer:** This project is for educational and research purposes only. It does not provide medical diagnosis, treatment recommendations, or professional healthcare advice. Always consult a qualified healthcare professional for medical decisions.

---

## Table of Contents

- [Overview](#overview)
- [Architecture](#architecture)
- [Tech Stack](#tech-stack)
- [Project Structure](#project-structure)
- [How It Works](#how-it-works)
- [Getting Started](#getting-started)
- [Docker](#docker)
- [Jenkins Pipeline](#jenkins-pipeline)
- [API Reference](#api-reference)
- [Configuration](#configuration)
- [Logging](#logging)
- [Limitations](#limitations)

---

## Overview

The app ingests medical PDF documents, splits them into chunks, embeds them with a biomedical embedding model, and stores them in a local FAISS index. At query time, the top 3 most similar chunks are retrieved and passed with the question to gpt-oss-120b (served by Groq). The prompt tells the model to answer in 2–3 lines using only the retrieved context, and to say it doesn't know if the context doesn't contain the answer.

Design goals:
- **Domain-specific retrieval:** `NeuML/pubmedbert-base-embeddings` is a biomedical embedding model, chosen over a general-purpose one for medical text.
- **Grounded answers:** the prompt restricts the model to the retrieved context.
- **Self-contained knowledge base:** the index is built locally from your own PDFs, with no external knowledge-base dependency.
- **Simple to run:** managed with `uv`, containerized with a multi-stage Dockerfile, with a Jenkins pipeline that builds and pushes the image.

---

## Architecture

```
┌─────────────────────┐
│   Medical PDF Files │
└──────────┬──────────┘
           │  PyPDF loader
           ▼
┌─────────────────────┐
│    Text Chunking    │  RecursiveCharacterTextSplitter
│                     │  chunk_size=1000, overlap=200 (characters)
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
│  FAISS Vector Store │  saved at data/vector_store/faiss_index/
└──────────┬──────────┘
           │
           ▼
User Query ──► Similarity Retriever (top-k=3)
           │
           ▼
┌─────────────────────┐
│  LangChain RAG Chain│  retriever → prompt → LLM → string output
└──────────┬──────────┘
           │
           ▼
┌─────────────────────┐
│  Groq LLM           │  openai/gpt-oss-120b (temperature 0.2)
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
| Containerization | Docker (multi-stage build, Python 3.12-slim, CPU-only PyTorch) |
| CI | Jenkins declarative pipeline (build and push image) |
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
│   │   ├── logger.py           # Console + daily log file setup
│   │   └── custom_exception.py # Exception that adds file/line context
│   │
│   ├── components/
│   │   ├── data_loader.py      # Ingestion pipeline: load → chunk → embed → save index
│   │   ├── embedding.py        # PubMedBERT embedding model wrapper
│   │   ├── llm.py              # Groq LLM setup
│   │   ├── loader.py           # PDF loading and chunking
│   │   ├── retriever.py        # Builds the RAG chain (retriever + prompt + LLM)
│   │   └── vector_store.py     # FAISS index creation and loading
│   │
│   ├── config/
│   │   └── config.py           # Configuration constants
│   │
│   └── templates/
│       └── index.html          # Chat UI (Jinja2)
│
├── data/                       # Not in the repo; create it locally (see below)
│   ├── raw_documents/          # Put your medical PDFs here
│   └── vector_store/
│       └── faiss_index/        # Generated FAISS index
│
├── logs/                       # Generated at runtime (git-ignored)
│
├── custom_jenkins/             # Custom Jenkins image (Docker CLI + uv)
├── Dockerfile
├── Jenkinsfile
├── pyproject.toml
├── requirements.txt            # Pinned dependencies compiled by uv
└── .python-version             # Pins Python 3.12
```

---

## How It Works

**Step 1: Load.** PDFs in `data/raw_documents/` are read page by page with PyPDF.

**Step 2: Chunk.** Documents are split by `RecursiveCharacterTextSplitter` into chunks of 1000 characters with a 200-character overlap.

**Step 3: Embed.** Each chunk is encoded by `NeuML/pubmedbert-base-embeddings`, a biomedical sentence-embedding model that outputs 768-dimensional vectors.

**Step 4: Index.** Vectors are added to a FAISS index (in batches of 64 chunks) and saved to `data/vector_store/faiss_index/`. FAISS performs exact similarity search over the stored vectors. You only need to rebuild the index when the document set changes.

**Step 5: Retrieve.** At query time, the question is embedded with the same model and the 3 most similar chunks are retrieved.

**Step 6: Generate.** The chunks and the question are inserted into the prompt and sent to `openai/gpt-oss-120b` on Groq. The full answer is returned once generation finishes (responses are not streamed).

---

## Getting Started

### Prerequisites

- Python 3.12
- [Astral `uv`](https://docs.astral.sh/uv/)
- A [Groq API key](https://console.groq.com/)
- (Optional) A [Hugging Face token](https://huggingface.co/settings/tokens). The embedding model is public, but a token can help avoid download rate limits.

### Installation

```bash
# 1. Clone the repository
git clone https://github.com/rich-aard/MEDICAL_CHATBOT.git
cd MEDICAL_CHATBOT

# 2. Create the virtual environment
uv venv .venv

# 3. Activate it
# Linux / macOS:
source .venv/bin/activate
# Windows (PowerShell):
.venv\Scripts\activate

# 4. Install the pinned dependencies (CPU-only PyTorch)
uv pip sync requirements.txt \
  --find-links https://download.pytorch.org/whl/cpu
```

If you change dependencies in `pyproject.toml`, regenerate the pinned file first:

```bash
uv pip compile pyproject.toml \
  --find-links https://download.pytorch.org/whl/cpu \
  -o requirements.txt
```

### Environment Variables

Create a `.env` file in the project root:

```env
GROQ_API_KEY=your_groq_api_key_here
# Optional:
HF_TOKEN=your_huggingface_token_here
```

### Build the Vector Store

Create the data folder and add your PDFs:

```bash
# Linux / macOS
mkdir -p data/raw_documents

# Windows (PowerShell)
mkdir data\raw_documents
```

Copy your medical PDFs into `data/raw_documents/`, then run this from the project root:

```bash
python -m app.components.data_loader
```

This loads, chunks, and embeds the PDFs and saves the FAISS index. Re-run it only when your documents change.

### Run the App

```bash
uvicorn app.app:app --reload
```

Open [http://localhost:8000](http://localhost:8000).

---

## Docker

### Build

```bash
docker build -t medical-chatbot .
```

The Dockerfile uses a two-stage build: a `builder` stage installs dependencies with `uv` into a virtual environment, and a `runner` stage (Python 3.12-slim) copies only that environment and the `app/` code.

### Run

The vector store is **not** included in the image, and the app will not start without it. Build the index locally first, then mount it:

```bash
# Linux / macOS
docker run -p 8000:8000 \
  -e GROQ_API_KEY=your_key \
  -v "$(pwd)/data/vector_store:/app/data/vector_store" \
  medical-chatbot
```

```powershell
# Windows (PowerShell)
docker run -p 8000:8000 `
  -e GROQ_API_KEY=your_key `
  -v "${PWD}/data/vector_store:/app/data/vector_store" `
  medical-chatbot
```

The embedding model is downloaded from Hugging Face on first start, so the container needs internet access.

---

## Jenkins Pipeline

The `Jenkinsfile` defines a declarative pipeline with four stages:

1. **Checkout Code:** pulls `main` from GitHub.
2. **Build Docker Image:** builds the image with `--no-cache` and tags it with the Jenkins build number and `latest`.
3. **Push to Container Registry:** logs in and pushes both tags to Docker Hub (`thefool23/medical-chatbot`).
4. **Workspace Cleanup:** removes the local build-number image.

The pipeline only builds and publishes the image. It has no test, lint, or deployment stage. The `custom_jenkins/` directory holds a Dockerfile for a custom Jenkins image with the Docker CLI and `uv` installed.

---

## API Reference

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/` | Renders the chat UI |
| `POST` | `/` | Accepts a `prompt` form field and returns the chat page (HTML) with the answer added |
| `GET` | `/clear` | Clears the in-memory chat history and redirects to `/` |

**Example request:**

```bash
curl -X POST http://localhost:8000/ \
  -F "prompt=What are the symptoms of type 2 diabetes?"
```

The response is an HTML page, not JSON.

---

## Configuration

Settings live in `app/config/config.py`, except where noted.

| Setting | Value | Description |
|---------|-------|-------------|
| `GROQ_LLM_MODEL` | `openai/gpt-oss-120b` | Groq model ID |
| `HUGGINGFACE_EMBEDDING_MODEL` | `NeuML/pubmedbert-base-embeddings` | Embedding model |
| `CHUNK_SIZE` | `1000` | Chunk length in characters |
| `CHUNK_OVERLAP` | `200` | Overlap between consecutive chunks, in characters |
| `DATA_PATH` | `data/raw_documents` | Where the PDFs are read from |
| `DB_FAISS_PATH` | `data/vector_store/faiss_index` | Where the FAISS index is saved and loaded |
| Top-k (`retriever.py`) | `3` | Chunks retrieved per question (hardcoded in `search_kwargs`) |
| Temperature (`llm.py`) | `0.2` | LLM sampling temperature |

Environment variables: `GROQ_API_KEY` (required) and `HF_TOKEN` (optional).

---

## Logging

Logs go to the console and to a daily file at `logs/log_YYYY-MM-DD.log`, using Python's standard `logging` module in plain text. Logged events include:

- Application startup and shutdown
- Embedding model, vector store, and LLM initialization
- Each question received from the UI
- Errors, with file and line context

Questions are logged in plain text, so avoid entering sensitive personal information. The `logs/` directory is git-ignored.

---

## Limitations

- **Single-turn only.** Each question is answered independently. The chat history shown on screen is not sent to the model, so follow-up questions that rely on earlier turns will not work. The history is also a single in-memory list shared by all visitors, so the app is intended for local, single-user use.
- **No evaluation or automated tests.** Behavior has been checked manually. Retrieval quality has not been measured.
- **Answers depend on the indexed documents.** If the retrieved context doesn't contain the answer, the model is instructed to say it doesn't know. Sources are not shown in the UI.
- **Vector store is not bundled** in the Docker image (see [Docker](#docker)).
- **CI only.** The Jenkins pipeline builds and pushes an image; it does not test or deploy.
- **Not medical advice.** See the disclaimer at the top.
