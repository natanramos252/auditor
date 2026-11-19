import os
from pathlib import Path

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./data/app.db")
DATA_DIR = Path(os.getenv("DATA_DIR", "./data"))
UPLOAD_DIR = DATA_DIR / "uploads"
MAX_UPLOAD_MB = int(os.getenv("MAX_UPLOAD_MB", "25"))
ALLOWED_EXT = {".pdf", ".docx", ".xlsx", ".txt", ".md", ".csv"}

# Provedor de IA: mock | anthropic | openai | ollama
LLM_PROVIDER = os.getenv("LLM_PROVIDER", "mock")
LLM_MODEL = os.getenv("LLM_MODEL", "")
LLM_TIMEOUT = float(os.getenv("LLM_TIMEOUT", "120"))
LLM_CONCURRENCY = int(os.getenv("LLM_CONCURRENCY", "4"))
LLM_RETRIES = int(os.getenv("LLM_RETRIES", "4"))
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
OPENAI_BASE_URL = os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1")
OLLAMA_URL = os.getenv("OLLAMA_URL", "http://localhost:11434")
CORS_ORIGINS = [o for o in os.getenv("CORS_ORIGINS", "http://localhost:5173,http://localhost:8080").split(",") if o]
