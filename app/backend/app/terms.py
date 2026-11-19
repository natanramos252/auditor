"""Termos de uso: texto versionado, texto dinâmico sobre a IA em uso e hash do conteúdo aceito."""
import hashlib
import json
from functools import lru_cache
from pathlib import Path

from . import config

PATH = Path(__file__).parent / "data" / "terms.json"

AI_TEXT = {
    "mock": "Neste momento a plataforma está em modo sem IA: a sugestão é feita por busca de palavras no próprio servidor e nenhum conteúdo dos seus documentos é enviado a terceiros.",
    "ollama": "Neste momento a análise usa um modelo de linguagem local ({model}), executado no servidor da instalação. Os trechos dos seus documentos não são enviados a serviços externos.",
    "cloud": "Neste momento a análise usa o provedor de IA “{name}” (modelo {model}). Para sugerir cada resposta, a plataforma envia a esse provedor os trechos dos seus documentos mais relevantes para a pergunta. O provedor é um terceiro, sujeito aos próprios termos e à própria política de privacidade, e pode processar esses trechos fora do Brasil. Se isso não for adequado aos seus documentos, não aceite, ou peça ao responsável para usar o modo local.",
}


def ai_paragraph() -> str:
    p, m = config.effective_provider(), config.LLM_MODEL or "padrão do provedor"
    if p == "mock":
        return AI_TEXT["mock"]
    if p == "ollama":
        return AI_TEXT["ollama"].format(model=m)
    names = {"anthropic": "Anthropic (Claude)", "openai": "OpenAI ou serviço compatível"}
    return AI_TEXT["cloud"].format(name=names.get(p, p), model=m)


@lru_cache
def _raw() -> dict:
    return json.loads(PATH.read_text(encoding="utf-8"))


def version() -> str:
    return _raw()["version"]


def current() -> dict:
    t = _raw()
    operator = config.OPERATOR_NAME + (f". Contato: {config.OPERATOR_CONTACT}" if config.OPERATOR_CONTACT else "")
    sections = [{"title": s["title"], "body": s["body"].replace("@AI@", ai_paragraph()).replace("@OPERATOR@", operator)} for s in t["sections"]]
    text = "\n\n".join(f"{s['title']}\n{s['body']}" for s in sections)
    return {"version": t["version"], "title": t["title"], "sections": sections,
            "hash": hashlib.sha256(text.encode("utf-8")).hexdigest()}
