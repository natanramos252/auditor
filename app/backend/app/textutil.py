import re
import unicodedata

STOP = set("""
a o as os um uma uns umas de do da dos das em no na nos nas por para com sem sob sobre entre ate ao aos
e ou nem mas que se como quando onde qual quais seu sua seus suas ser sao esta estao foi ha tem ter
deve devem pode podem mais menos muito pela pelo pelas pelos isso este essa esses essas todo toda todos todas
organizacao organizacoes sgcn documento documentos documentada documentado informacao
""".split())


def fold(s: str) -> str:
    """Minúsculas e sem acentos, preservando o comprimento (1 caractere -> 1 caractere)."""
    out = []
    for ch in s:
        if ch.isspace():
            out.append(" ")
            continue
        base = unicodedata.normalize("NFD", ch)[0]
        out.append(base.lower() if len(base.lower()) == 1 else ch)
    return "".join(out)


def tokens(s: str) -> list[str]:
    return [t for t in re.findall(r"[a-z0-9]{3,}", fold(s)) if t not in STOP]


def collapse(s: str) -> str:
    return re.sub(r"\s+", " ", s).strip()


def sentences(s: str) -> list[tuple[int, int]]:
    """Posições (início, fim) das frases de um texto."""
    spans, start = [], 0
    for m in re.finditer(r"[.;!?]\s+|\n", s):
        if m.end() - start > 1:
            spans.append((start, m.end()))
        start = m.end()
    if start < len(s):
        spans.append((start, len(s)))
    return [(a, b) for a, b in spans if s[a:b].strip()]
