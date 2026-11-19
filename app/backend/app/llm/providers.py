import time

import httpx

from .. import config
from .base import LLMError, LLMProvider

RETRY_STATUS = {408, 425, 429, 500, 502, 503, 504}


def post(url: str, **kw) -> httpx.Response:
    """POST com novas tentativas para limite de uso (429), falhas do provedor (5xx) e timeout, com espera crescente."""
    last = ""
    for attempt in range(config.LLM_RETRIES + 1):
        try:
            r = httpx.post(url, timeout=config.LLM_TIMEOUT, **kw)
            if r.status_code not in RETRY_STATUS:
                return r
            last = f"{r.status_code}: {r.text[:200]}"
        except httpx.HTTPError as e:
            last = f"{type(e).__name__}: {e}"
        if attempt < config.LLM_RETRIES:
            time.sleep(min(3 * 2 ** attempt, 30))
    raise LLMError(f"Provedor indisponível após {config.LLM_RETRIES + 1} tentativas ({last})")


class Anthropic(LLMProvider):
    name = "anthropic"

    def __init__(self):
        if not config.ANTHROPIC_API_KEY:
            raise LLMError("ANTHROPIC_API_KEY não definida")
        self.model = config.LLM_MODEL or "claude-sonnet-5-5"

    def complete(self, system, user):
        r = post(
            "https://api.anthropic.com/v1/messages",
            headers={"x-api-key": config.ANTHROPIC_API_KEY, "anthropic-version": "2023-06-01"},
            json={"model": self.model, "max_tokens": 1500, "temperature": 0, "system": system,
                  "messages": [{"role": "user", "content": user}]},
        )
        if r.status_code >= 400:
            raise LLMError(f"Anthropic {r.status_code}: {r.text[:300]}")
        return "".join(b.get("text", "") for b in r.json().get("content", []))


class OpenAI(LLMProvider):
    """Também serve para qualquer API compatível (vLLM, LM Studio, OpenRouter) via OPENAI_BASE_URL."""
    name = "openai"

    def __init__(self):
        if config.key_missing("openai"):
            raise LLMError("OPENAI_API_KEY não definida")
        self.model = config.LLM_MODEL or "gpt-4o-mini"

    def complete(self, system, user):
        r = post(
            f"{config.OPENAI_BASE_URL}/chat/completions",
            headers={"Authorization": f"Bearer {config.OPENAI_API_KEY}"},
            json={"model": self.model, "temperature": 0, "response_format": {"type": "json_object"},
                  "messages": [{"role": "system", "content": system}, {"role": "user", "content": user}]},
        )
        if r.status_code >= 400:
            raise LLMError(f"OpenAI {r.status_code}: {r.text[:300]}")
        return r.json()["choices"][0]["message"]["content"]


class Ollama(LLMProvider):
    name = "ollama"

    def __init__(self):
        self.model = config.LLM_MODEL or "phi3.5:latest"

    def complete(self, system, user):
        r = post(
            f"{config.OLLAMA_URL}/api/chat",
            json={"model": self.model, "stream": False, "format": "json", "options": {"temperature": 0},
                  "messages": [{"role": "system", "content": system}, {"role": "user", "content": user}]},
        )
        if r.status_code >= 400:
            raise LLMError(f"Ollama {r.status_code}: {r.text[:300]}")
        return r.json()["message"]["content"]


class Mock(LLMProvider):
    """Sem IA: a análise cai na heurística local (ver analysis.heuristic). Serve para demonstração e testes."""
    name = "mock"
    model = "heuristica-local"

    def complete(self, system, user):
        raise LLMError("O provedor mock não gera texto")


def get_provider(name: str | None = None) -> LLMProvider:
    name = (name or config.effective_provider()).lower()
    table = {"anthropic": Anthropic, "openai": OpenAI, "ollama": Ollama, "mock": Mock}
    if name not in table:
        raise LLMError(f"Provedor desconhecido: {name}")
    return table[name]()
