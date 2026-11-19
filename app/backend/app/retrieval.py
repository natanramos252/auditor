"""Busca lexical (TF-IDF) de trechos relevantes, com reforço para os documentos do tipo esperado."""
import math
from collections import Counter
from dataclasses import dataclass

from .textutil import tokens

SLOT_BOOST = 1.6


@dataclass
class Hit:
    chunk_id: int
    doc_id: int
    doc_name: str
    slot: str
    page: int | None
    text: str
    score: float
    matched: int  # termos distintos da pergunta encontrados


class Index:
    def __init__(self, chunks):
        """chunks: lista de objetos com id, text, page, document(id, filename, slot)."""
        self.chunks = chunks
        self.tf = [Counter(tokens(c.text)) for c in chunks]
        df = Counter()
        for tf in self.tf:
            df.update(tf.keys())
        n = max(len(chunks), 1)
        self.idf = {t: math.log(1 + n / d) for t, d in df.items()}

    def search(self, query: str, slots: list[str], k: int = 4, min_matched: int = 2) -> list[Hit]:
        q = set(tokens(query))
        if not q:
            return []
        scored = []
        for c, tf in zip(self.chunks, self.tf):
            hits = [t for t in q if t in tf]
            if len(hits) < min_matched:
                continue
            s = sum(self.idf.get(t, 0) * (1 + math.log(tf[t])) for t in hits) / math.sqrt(len(q))
            if c.document.slot in slots:
                s *= SLOT_BOOST
            scored.append(Hit(c.id, c.document.id, c.document.filename, c.document.slot, c.page, c.text, s, len(hits)))
        scored.sort(key=lambda h: h.score, reverse=True)
        return scored[:k]
