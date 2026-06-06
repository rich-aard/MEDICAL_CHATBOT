import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

HF_TOKEN = os.environ.get("HF_TOKEN")

GROQ_API_KEY = os.getenv("GROQ_API_KEY")
GROQ_LLM_MODEL = "llama-3.3-70b-versatile"

# Dynamic project paths
BASE_DIR = Path(__file__).resolve().parent.parent.parent
DATA_PATH = os.path.join(BASE_DIR, "data", "raw_documents")
DB_FAISS_PATH = os.path.join(BASE_DIR, "data", "vector_store", "faiss_index")

CHUNK_SIZE = 1000
CHUNK_OVERLAP = 200

# Hugging Face repos
HUGGINGFACE_EMBEDDING_MODEL = "NeuML/pubmedbert-base-embeddings"
