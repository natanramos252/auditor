import os
from pathlib import Path

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./data/app.db")
DATA_DIR = Path(os.getenv("DATA_DIR", "./data"))
UPLOAD_DIR = DATA_DIR / "uploads"
MAX_UPLOAD_MB = int(os.getenv("MAX_UPLOAD_MB", "25"))
ALLOWED_EXT = {".pdf", ".docx", ".xlsx", ".txt", ".md", ".csv"}

# Provedor de IA: mock | anthropic | openai | ollama
LLM_PROVIDER = (os.getenv("LLM_PROVIDER") or "mock").lower()
LLM_MODEL = os.getenv("LLM_MODEL", "")
LLM_TIMEOUT = float(os.getenv("LLM_TIMEOUT", "120"))
LLM_CONCURRENCY = int(os.getenv("LLM_CONCURRENCY", "4"))
LLM_RETRIES = int(os.getenv("LLM_RETRIES", "4"))
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
OPENAI_BASE_URL = os.getenv("OPENAI_BASE_URL") or "https://api.openai.com/v1"
OPENAI_ALLOW_NO_KEY = os.getenv("OPENAI_ALLOW_NO_KEY", "").lower() in {"1", "true", "yes"}  # LM Studio, vLLM...
OLLAMA_URL = os.getenv("OLLAMA_URL") or "http://localhost:11434"
CORS_ORIGINS = [o for o in os.getenv("CORS_ORIGINS", "http://localhost:5173,http://localhost:8080").split(",") if o]

# Quem responde por esta instalação (aparece nos termos de uso)
OPERATOR_NAME = os.getenv("OPERATOR_NAME") or "a organização ou pessoa que instalou e opera esta plataforma"
OPERATOR_CONTACT = os.getenv("OPERATOR_CONTACT", "")


def key_missing(provider: str) -> bool:
    """O provedor configurado precisa de chave e ela não foi informada."""
    if provider == "anthropic":
        return not ANTHROPIC_API_KEY
    if provider == "openai":
        return not OPENAI_API_KEY and not OPENAI_ALLOW_NO_KEY
    return False


def effective_provider() -> str:
    """Provedor realmente usado: sem a chave, cai para o modo sem IA (mock) em vez de falhar item a item."""
    return "mock" if key_missing(LLM_PROVIDER) else LLM_PROVIDER
