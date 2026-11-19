"""Cálculo determinístico da maturidade. A IA nunca altera estes números.

Cada item vale 0 (não atende), 1 (atende parcialmente) ou 2 (atende). A nota é o percentual de atendimento (0 a 100),
ponderado pelo peso de cada item.
"""
from . import catalog

MAX = catalog.MAX_LEVEL
TARGET = 80  # % mínimo para "pronta para auditoria externa"
BANDS = [
    (30, "Inicial", "Ainda longe de uma auditoria externa de certificação."),
    (55, "Em estruturação", "Há bases, mas faltam processos e registros em vários requisitos."),
    (TARGET, "Parcialmente pronta", "Próxima, porém ainda há lacunas relevantes antes da certificação."),
    (101, "Pronta para auditoria externa", "Requisitos principais atendidos e evidenciados."),
]


def effective_level(ans) -> float | None:
    """Nível usado na pontuação. None = fora do cálculo (N/A). Só conta o que o profissional validou."""
    if ans is None or ans.status != "validated":
        return 0.0
    if ans.na:
        return None
    lvl = min(ans.level or 0, MAX)
    has_evidence = any(e.get("accepted") for e in (ans.evidence or []))
    if lvl >= MAX and not has_evidence:
        return MAX - 1.0  # "Atende" sem evidência aceita vale "Atende parcialmente"
    return float(lvl)


def pct(x: float) -> float:
    return round(100 * x / MAX, 1)


def band(score: float):
    for limit, name, desc in BANDS:
        if score < limit:
            return name, desc
    return BANDS[-1][1], BANDS[-1][2]


def compute(answers: list) -> dict:
    cat = catalog.load()
    by_no = {a.item_no: a for a in answers}
    clauses: dict[int, dict] = {}
    rows = []
    for it in cat["items"]:
        a = by_no.get(it["n"])
        eff = effective_level(a)
        declared = None if a is None or a.status == "pending" else (None if a.na else min(a.level or 0, MAX))
        cat_ = "pending" if not (a and a.status == "validated") else "na" if a.na else ("nao", "parcial", "atende")[int(eff)]
        rows.append({"cat": cat_, "n": it["n"], "clause_no": it["clause_no"], "weight": it["weight"], "blocking": it["blocking"],
                     "declared": declared, "effective": eff, "validated": bool(a and a.status == "validated"),
                     "downgraded": bool(a and a.status == "validated" and eff is not None and declared is not None and eff < declared)})
        if eff is None:
            continue
        c = clauses.setdefault(it["clause_no"], {"name": it["clause"], "sum": 0.0, "w": 0, "items": 0})
        c["sum"] += eff * it["weight"]
        c["w"] += it["weight"]
        c["items"] += 1
    cats = ("atende", "parcial", "nao", "na", "pending")
    dist = {k: 0 for k in cats}
    dist_clause: dict[int, dict] = {}
    for r in rows:
        dist[r["cat"]] += 1
        dist_clause.setdefault(r["clause_no"], {k: 0 for k in cats})[r["cat"]] += 1
    clause_list, tot_s, tot_w = [], 0.0, 0.0
    for no in sorted(clauses):
        c = clauses[no]
        clause_list.append({"clause_no": no, "name": c["name"], "score": pct(c["sum"] / c["w"]) if c["w"] else 0.0, "items": c["items"], "dist": dist_clause[no]})
        tot_s += c["sum"]
        tot_w += c["w"]
    overall = pct(tot_s / tot_w) if tot_w else 0.0
    n_items = len(cat["items"])
    validated = sum(1 for r in rows if r["validated"])
    blockers = [r["n"] for r in rows if r["blocking"] and r["effective"] is not None and r["effective"] < MAX]
    downgraded = sum(1 for r in rows if r["downgraded"])
    confidence = max(0.0, validated / n_items - 0.5 * downgraded / n_items)
    name, desc = band(overall)
    ready = overall >= TARGET and not blockers and validated == n_items
    if name == "Pronta para auditoria externa" and not ready:
        name, desc = "Parcialmente pronta", "Nota alta, mas há requisitos bloqueantes sem 'Atende' ou itens sem validação."
    return {"overall": overall, "target": TARGET, "band": name, "band_description": desc, "ready": ready,
            "clauses": clause_list, "distribution": dist, "rows": rows, "blockers": blockers, "validated": validated, "total": n_items,
            "completeness": round(validated / n_items, 2), "confidence": round(confidence, 2), "downgraded": downgraded}


def suggestions(answers: list, limit: int = 15) -> list[dict]:
    """Melhorias ordenadas: bloqueantes primeiro, depois maior ganho de pontuação, depois menor esforço."""
    cat = catalog.load()
    by_no = {a.item_no: a for a in answers}
    out = []
    for it in cat["items"]:
        a = by_no.get(it["n"])
        eff = effective_level(a)
        if eff is None or eff >= MAX:
            continue
        gap = MAX - eff
        out.append({
            "n": it["n"], "clause": it["subclause"] or it["clause"], "question": it["question"],
            "blocking": it["blocking"], "current": eff, "current_label": catalog.LEVELS[int(eff)][0],
            "what": f"Atender ao requisito e gerar o registro que o comprove: {it['question']}",
            "evidence": it["evidence_examples"],
            "missing": list(a.ai_missing) if a and a.ai_missing else [],
            "validated": bool(a and a.status == "validated"),
            "effort": "baixo" if gap <= 1 else "alto",
            "_key": (not it["blocking"], -gap * it["weight"], gap),
        })
    out.sort(key=lambda s: s["_key"])
    for s in out:
        s.pop("_key")
    return out[:limit]


def strengths(answers: list) -> list[dict]:
    out = []
    for a in answers:
        if a.status == "validated" and not a.na and (a.level or 0) >= MAX and any(e.get("accepted") for e in a.evidence or []):
            it = catalog.item(a.item_no)
            out.append({"n": a.item_no, "clause": it["subclause"] or it["clause"], "question": it["question"], "level": a.level})
    return out
