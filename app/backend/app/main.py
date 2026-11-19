import re
import uuid
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import BackgroundTasks, Depends, FastAPI, File, Form, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.orm import Session

from datetime import datetime

from . import analysis, catalog, config, scoring, terms
from .db import Base, engine, get_db
from .classify import classify
from .extract import extract
from .models import Answer, Assessment, Chunk, Document, DocumentSlot, TermsAcceptance


@asynccontextmanager
async def lifespan(_):
    Base.metadata.create_all(engine)
    from sqlalchemy import inspect, text  # create_all não altera tabelas existentes: acrescenta colunas novas
    cols = {c["name"] for c in inspect(engine).get_columns("answers")}
    with engine.begin() as conn:
        for name in ("ai_criteria", "claude_review"):
            if name not in cols:
                conn.execute(text(f"ALTER TABLE answers ADD COLUMN {name} JSON"))
    from .db import SessionLocal
    with SessionLocal() as db:  # uma análise que estava rodando quando o servidor reiniciou não vai terminar sozinha
        for a in db.scalars(select(Assessment).where(Assessment.analysis_status == "running")):
            a.analysis_status, a.analysis_error = "error", "Interrompida por reinício do servidor. Reanalise."
        db.commit()
    yield


app = FastAPI(title="Auditor — prontidão ISO 22301", lifespan=lifespan)
app.add_middleware(CORSMiddleware, allow_origins=config.CORS_ORIGINS, allow_methods=["*"], allow_headers=["*"])


def get_assessment(aid: int, db: Session) -> Assessment:
    a = db.get(Assessment, aid)
    if not a:
        raise HTTPException(404, "Avaliação não encontrada")
    return a


# ---------- catálogo ----------
@app.get("/api/catalog")
def get_catalog():
    cat = catalog.load()
    return {"norm": cat["norm"], "version": cat["version"], "slots": cat["slots"], "items": cat["items"],
            "levels": [{"level": k, "name": v[0], "description": v[1]} for k, v in catalog.LEVELS.items()],
            "llm": {"provider": config.effective_provider(), "configured": config.LLM_PROVIDER, "model": config.LLM_MODEL,
                    "missing_key": config.key_missing(config.LLM_PROVIDER), "base_url": config.OPENAI_BASE_URL if config.LLM_PROVIDER == "openai" else ""}}


# ---------- avaliações ----------
class AssessmentIn(BaseModel):
    company: str = Field(min_length=2, max_length=200)
    sector: str = ""
    scope: str = ""
    accept_terms: bool = False
    accepted_by: str = Field(default="", max_length=200)
    terms_version: str = ""


class AcceptIn(BaseModel):
    accepted_by: str = Field(min_length=2, max_length=200)
    terms_version: str


def terms_status(a: Assessment) -> dict:
    cur = terms.version()
    ok = next((x for x in reversed(a.acceptances) if x.version == cur), None)
    return {"accepted": ok is not None, "current_version": cur,
            "accepted_by": ok.accepted_by if ok else None, "accepted_at": ok.accepted_at.isoformat(timespec="seconds") if ok else None}


def record_acceptance(db: Session, a: Assessment, name: str, version: str) -> None:
    if version != terms.version():
        raise HTTPException(409, f"Os termos mudaram (versão atual {terms.version()}). Leia e aceite de novo.")
    a.acceptances.append(TermsAcceptance(version=version, text_hash=terms.current()["hash"], accepted_by=name.strip()))


def require_terms(a: Assessment) -> None:
    if not terms_status(a)["accepted"]:
        raise HTTPException(403, "Aceite os Termos de Uso para continuar.")


@app.get("/api/terms")
def get_terms():
    return terms.current()


def assessment_out(a: Assessment, db: Session) -> dict:
    return {"id": a.id, "company": a.company, "sector": a.sector, "scope": a.scope,
            "analysis": {"status": a.analysis_status, "done": a.analysis_done, "total": a.analysis_total,
                         "error": a.analysis_error, "provider": a.analysis_provider},
            "documents": [doc_out(d) for d in a.documents], "terms": terms_status(a)}


def doc_out(d: Document) -> dict:
    return {"id": d.id, "slot": d.slot, "filename": d.filename, "size": d.size, "chunks": d.n_chunks, "error": d.error,
            "covers": [{"slot": c.slot, "score": c.score, "reason": c.reason} for c in d.covers]}


@app.post("/api/assessments")
def create_assessment(body: AssessmentIn, db: Session = Depends(get_db)):
    if not body.accept_terms or len(body.accepted_by.strip()) < 2:
        raise HTTPException(400, "Para começar, aceite os Termos de Uso e informe o seu nome.")
    a = Assessment(company=body.company.strip(), sector=body.sector, scope=body.scope)
    record_acceptance(db, a, body.accepted_by, body.terms_version)
    db.add(a)
    db.commit()
    return assessment_out(a, db)


@app.post("/api/assessments/{aid}/accept-terms")
def accept_terms(aid: int, body: AcceptIn, db: Session = Depends(get_db)):
    """Aceite de avaliações criadas antes dos termos, ou depois de uma nova versão."""
    a = get_assessment(aid, db)
    record_acceptance(db, a, body.accepted_by, body.terms_version)
    db.commit()
    return assessment_out(a, db)


@app.get("/api/assessments/{aid}")
def read_assessment(aid: int, db: Session = Depends(get_db)):
    return assessment_out(get_assessment(aid, db), db)


# ---------- documentos ----------
@app.post("/api/assessments/{aid}/documents")
async def upload_document(aid: int, slot: str = Form(...), file: UploadFile = File(...), db: Session = Depends(get_db)):
    a = get_assessment(aid, db)
    require_terms(a)
    if slot != "principal" and slot not in catalog.load()["slot_by_id"]:
        raise HTTPException(400, "Tipo de documento desconhecido")
    ext = Path(file.filename or "").suffix.lower()
    if ext not in config.ALLOWED_EXT:
        raise HTTPException(400, f"Formato não aceito ({ext}). Use: {', '.join(sorted(config.ALLOWED_EXT))}")
    data = await file.read()
    if len(data) > config.MAX_UPLOAD_MB * 1024 * 1024:
        raise HTTPException(413, f"Arquivo maior que {config.MAX_UPLOAD_MB} MB")
    safe = re.sub(r"[^A-Za-z0-9._-]", "_", Path(file.filename).name)[:120]
    folder = config.UPLOAD_DIR / str(a.id)
    folder.mkdir(parents=True, exist_ok=True)
    path = folder / f"{uuid.uuid4().hex[:8]}_{safe}"
    path.write_bytes(data)
    doc = Document(assessment_id=a.id, slot=slot, filename=Path(file.filename).name, path=str(path), size=len(data))
    try:
        chunks = extract(path)
        doc.chunks = [Chunk(idx=i, page=p, text=t) for i, (p, t) in enumerate(chunks)]
        doc.n_chunks = len(chunks)
        if not chunks:
            doc.error = "Nenhum texto extraído (PDF escaneado? OCR ainda não disponível)."
        elif slot == "principal":  # arquivo consolidado: descobre quais tipos de documento ele cobre
            doc.covers = [DocumentSlot(**c) for c in classify(" ".join(t for _, t in chunks))]
    except Exception as e:  # noqa: BLE001
        doc.error = f"Falha ao ler o arquivo: {type(e).__name__}"
    db.add(doc)
    db.commit()
    return doc_out(doc)


@app.delete("/api/assessments/{aid}/documents/{did}")
def delete_document(aid: int, did: int, db: Session = Depends(get_db)):
    d = db.get(Document, did)
    if not d or d.assessment_id != aid:
        raise HTTPException(404, "Documento não encontrado")
    Path(d.path).unlink(missing_ok=True)
    db.delete(d)
    db.commit()
    return {"ok": True}


@app.put("/api/assessments/{aid}/documents/{did}/covers/{slot}")
def add_cover(aid: int, did: int, slot: str, db: Session = Depends(get_db)):
    """O usuário indica que o arquivo principal também cobre este tipo."""
    d = db.get(Document, did)
    if not d or d.assessment_id != aid or slot not in catalog.load()["slot_by_id"]:
        raise HTTPException(404, "Documento ou tipo não encontrado")
    if not any(c.slot == slot for c in d.covers):
        d.covers.append(DocumentSlot(slot=slot, score=0, reason="Marcado por você"))
        db.commit()
    return doc_out(d)


@app.delete("/api/assessments/{aid}/documents/{did}/covers/{slot}")
def remove_cover(aid: int, did: int, slot: str, db: Session = Depends(get_db)):
    """O usuário indica que este tipo não está no arquivo principal."""
    d = db.get(Document, did)
    if not d or d.assessment_id != aid:
        raise HTTPException(404, "Documento não encontrado")
    d.covers = [c for c in d.covers if c.slot != slot]
    db.commit()
    return doc_out(d)


# ---------- análise ----------
@app.post("/api/assessments/{aid}/analyze")
def start_analysis(aid: int, bg: BackgroundTasks, db: Session = Depends(get_db)):
    a = get_assessment(aid, db)
    require_terms(a)
    if a.analysis_status == "running":
        raise HTTPException(409, "Análise já em andamento")
    if not any(d.n_chunks for d in a.documents):
        raise HTTPException(400, "Anexe ao menos um documento com texto legível")
    a.analysis_status, a.analysis_done, a.analysis_error = "running", 0, ""
    db.commit()
    bg.add_task(analysis.run_analysis, aid)
    return assessment_out(a, db)


# ---------- questionário ----------
def answer_out(it: dict, ans: Answer | None, chunk_text: dict[int, str]) -> dict:
    ev = []
    for e in (ans.evidence if ans else []) or []:
        ctx = chunk_text.get(e.get("chunk_id"), "")
        pos = ctx.find(e["quote"]) if ctx else -1
        ev.append({**e, "context": ctx, "quote_start": pos})
    return {**{k: it[k] for k in ("n", "clause", "clause_no", "subclause", "question", "evidence_examples", "weight", "blocking", "slots", "norma", "kind", "criteria")},
            "ai_criteria": (ans.ai_criteria if ans else None) or [], "claude_review": ans.claude_review if ans else None,
            "status": ans.status if ans else "pending", "level": ans.level if ans else None, "na": bool(ans and ans.na),
            "comment": ans.comment if ans else "", "ai_level": ans.ai_level if ans else None,
            "ai_confidence": ans.ai_confidence if ans else None, "ai_justification": ans.ai_justification if ans else "",
            "ai_missing": ans.ai_missing if ans else [], "evidence": ev}


def chunk_texts(db: Session, answers: list[Answer]) -> dict[int, str]:
    ids = {e["chunk_id"] for a in answers for e in (a.evidence or []) if e.get("chunk_id")}
    if not ids:
        return {}
    return {c.id: c.text for c in db.scalars(select(Chunk).where(Chunk.id.in_(ids)))}


@app.get("/api/assessments/{aid}/items")
def list_items(aid: int, db: Session = Depends(get_db)):
    a = get_assessment(aid, db)
    ctx = chunk_texts(db, a.answers)
    by_no = {x.item_no: x for x in a.answers}
    return [answer_out(it, by_no.get(it["n"]), ctx) for it in catalog.load()["items"]]


class EvidenceFlag(BaseModel):
    chunk_id: int | None = None
    quote: str
    accepted: bool


class AnswerIn(BaseModel):
    level: int | None = Field(default=None, ge=0, le=2)
    na: bool = False
    comment: str = ""
    validated: bool = False
    evidence: list[EvidenceFlag] | None = None  # marca aceitas/rejeitadas


class ManualEvidence(BaseModel):
    doc_name: str = Field(min_length=1, max_length=300)
    quote: str = Field(min_length=3, max_length=1500)
    page: int | None = None


def get_or_create_answer(db: Session, aid: int, n: int) -> Answer:
    if n not in catalog.load()["by_no"]:
        raise HTTPException(404, "Item inexistente")
    ans = db.scalar(select(Answer).where(Answer.assessment_id == aid, Answer.item_no == n))
    if not ans:
        ans = Answer(assessment_id=aid, item_no=n)
        db.add(ans)
    return ans


@app.put("/api/assessments/{aid}/answers/{n}")
def save_answer(aid: int, n: int, body: AnswerIn, db: Session = Depends(get_db)):
    get_assessment(aid, db)
    ans = get_or_create_answer(db, aid, n)
    if body.validated and not body.na and body.level is None:
        raise HTTPException(400, "Escolha um nível ou 'Não se aplica' antes de validar")
    ans.level, ans.na, ans.comment = (None if body.na else body.level), body.na, body.comment
    if body.evidence is not None:
        flags = {(e.chunk_id, e.quote): e.accepted for e in body.evidence}
        ans.evidence = [{**e, "accepted": flags.get((e.get("chunk_id"), e["quote"]), e["accepted"])} for e in ans.evidence or []]
    if body.validated:
        ans.status = "validated"
    elif ans.status == "validated":
        ans.status = "suggested" if ans.ai_level is not None else "pending"  # editar tira a validação
    elif body.level is not None or body.na:
        ans.status = "suggested" if ans.ai_level is not None else ans.status
    db.commit()
    return answer_out(catalog.item(n), ans, chunk_texts(db, [ans]))


@app.post("/api/assessments/{aid}/answers/{n}/evidence")
def add_evidence(aid: int, n: int, body: ManualEvidence, db: Session = Depends(get_db)):
    get_assessment(aid, db)
    ans = get_or_create_answer(db, aid, n)
    ans.evidence = [*(ans.evidence or []), {"chunk_id": None, "doc_id": None, "doc_name": body.doc_name, "slot": None,
                                            "page": body.page, "quote": body.quote, "accepted": True, "manual": True}]
    if ans.status == "validated":
        ans.status = "suggested"
    db.commit()
    return answer_out(catalog.item(n), ans, chunk_texts(db, [ans]))


# ---------- relatório ----------
@app.get("/api/assessments/{aid}/report")
def report(aid: int, db: Session = Depends(get_db)):
    a = get_assessment(aid, db)
    sc = scoring.compute(a.answers)
    sc.pop("rows")
    return {
        "company": a.company, "sector": a.sector, "scope": a.scope, "norm": catalog.load()["norm"],
        "analysis_provider": a.analysis_provider, "scores": sc,
        "strengths": scoring.strengths(a.answers), "suggestions": scoring.suggestions(a.answers),
        "stats": {"evidences_accepted": sum(1 for x in a.answers for e in (x.evidence or []) if e.get("accepted")),
                  "ai_suggested": sum(1 for x in a.answers if x.ai_level is not None),
                  "blockers_total": sum(1 for i in catalog.load()["items"] if i["blocking"])},
        "pending": [x["n"] for x in scoring.compute(a.answers)["rows"] if not x["validated"]],
        "disclaimer": "Este relatório é um diagnóstico preparatório baseado em autoavaliação e não substitui a "
                      "auditoria de certificação realizada por organismo certificador acreditado.",
    }


# ---------- revisão por um revisor externo (Claude) ----------
# Fluxo: GET /review/queue (o que revisar, com critérios da norma) -> o revisor lê os documentos
# (GET /review/documents/{id}/text) -> POST /review (parecer por critério, com citações literais).
# O backend confere cada citação no texto e calcula o nível com a mesma regra da análise automática.
# O parecer NÃO valida nada: o profissional adota (POST .../adopt-review) e valida na tela.
@app.get("/api/assessments/{aid}/review/queue")
def review_queue(aid: int, only: str = "all", db: Session = Depends(get_db)):
    a = get_assessment(aid, db)
    by_no = {x.item_no: x for x in a.answers}
    out = []
    for it in catalog.load()["items"]:
        ans = by_no.get(it["n"])
        if only == "unreviewed" and ans and ans.claude_review:
            continue
        if only == "suggested" and not (ans and ans.status == "suggested"):
            continue
        out.append({"n": it["n"], "norma": it["norma"], "kind": it["kind"], "blocking": it["blocking"], "question": it["question"],
                    "criteria": it["criteria"], "doc_types": it["slots"],
                    "ai": {"level": ans.ai_level, "justification": ans.ai_justification, "criteria": ans.ai_criteria} if ans else None,
                    "evidence": [{"idx": i, "doc_name": e["doc_name"], "page": e.get("page"), "quote": e["quote"]}
                                 for i, e in enumerate((ans.evidence if ans else []) or [])],
                    "reviewed": bool(ans and ans.claude_review)})
    return {"assessment": a.company, "norm": catalog.load()["norm"], "items": out,
            "documents": [{"id": d.id, "filename": d.filename, "slot": d.slot, "chunks": d.n_chunks} for d in a.documents]}


@app.get("/api/assessments/{aid}/review/documents/{did}/text")
def review_document_text(aid: int, did: int, db: Session = Depends(get_db)):
    d = db.get(Document, did)
    if not d or d.assessment_id != aid:
        raise HTTPException(404, "Documento não encontrado")
    return {"id": d.id, "filename": d.filename, "chunks": [{"id": c.id, "page": c.page, "text": c.text} for c in d.chunks]}


class ReviewCriterion(BaseModel):
    i: int
    status: str  # atendido | parcial | ausente
    note: str = ""


class ReviewEvidence(BaseModel):
    quote: str = Field(min_length=15, max_length=1500)
    verdict: str = "comprova"  # comprova | parcial | nao_comprova
    reason: str = ""
    doc_id: int | None = None
    criterion: int | None = None


class ReviewItem(BaseModel):
    n: int
    criteria: list[ReviewCriterion]
    evidence: list[ReviewEvidence] = []
    justification: str = ""
    missing: list[str] = []


class ReviewIn(BaseModel):
    reviewer: str = "Claude"
    model: str = ""
    items: list[ReviewItem]


@app.post("/api/assessments/{aid}/review")
def submit_review(aid: int, body: ReviewIn, db: Session = Depends(get_db)):
    a = get_assessment(aid, db)
    chunks = db.scalars(select(Chunk).join(Document).where(Document.assessment_id == aid)).all()
    docs = {d.id: d for d in a.documents}
    summary, rejected = [], []
    for ri in body.items:
        it = catalog.load()["by_no"].get(ri.n)
        if not it:
            continue
        by_i = {c.i: c for c in ri.criteria}
        crit = []
        evidence = []
        for ev in ri.evidence:
            found = None
            for c in chunks:
                if ev.doc_id and c.document_id != ev.doc_id:
                    continue
                span = analysis.locate(ev.quote, c.text)
                if span:
                    found = (c, c.text[span[0]:span[1]])
                    break
            if not found:
                rejected.append({"n": ri.n, "quote": ev.quote[:80], "reason": "citação não encontrada literalmente nos documentos"})
                continue
            c, quote = found
            evidence.append({"chunk_id": c.id, "doc_id": c.document_id, "doc_name": docs[c.document_id].filename, "slot": docs[c.document_id].slot,
                             "page": c.page, "quote": quote, "verdict": ev.verdict if ev.verdict in ("comprova", "parcial", "nao_comprova") else "parcial",
                             "reason": ev.reason, "criterion": ev.criterion})
        valid_quotes = [e["quote"] for e in evidence if e["verdict"] != "nao_comprova"]
        for i, text in enumerate(it["criteria"], 1):
            r = by_i.get(i)
            status = r.status if r and r.status in analysis.STATUS_VALUE else "ausente"
            has_cite = any(e.get("criterion") == i and e["verdict"] != "nao_comprova" for e in evidence)
            if status == "atendido" and not has_cite and not valid_quotes:
                status = "parcial"  # "atendido" precisa de pelo menos uma citação verificada no item
            crit.append({"text": text, "status": status, "note": r.note if r else ""})
        level = analysis.level_from_criteria(crit)
        level, _, just = analysis.guard_level(level, 1.0, ri.justification, [{"quote": q} for q in valid_quotes], it["kind"])
        ans = get_or_create_answer(db, aid, ri.n)
        ans.claude_review = {"reviewer": body.reviewer, "model": body.model, "at": datetime.utcnow().isoformat(timespec="seconds"),
                             "level": level, "criteria": crit, "evidence": evidence, "justification": just, "missing": ri.missing[:6]}
        summary.append({"n": ri.n, "level": level})
    db.commit()
    return {"saved": len(summary), "rejected_quotes": rejected, "items": summary}


@app.post("/api/assessments/{aid}/review/adopt-all")
def adopt_all_reviews(aid: int, db: Session = Depends(get_db)):
    """Adota o parecer em todos os itens que o têm e que o profissional ainda não validou. Não valida nada."""
    a = get_assessment(aid, db)
    done = 0
    for ans in a.answers:
        rv = ans.claude_review
        if not rv or ans.status == "validated":
            continue
        if rv["level"] is not None:
            ans.level, ans.na = rv["level"], False
        ans.evidence = [{k: e[k] for k in ("chunk_id", "doc_id", "doc_name", "slot", "page", "quote")} | {"accepted": e["verdict"] != "nao_comprova"}
                        for e in rv["evidence"]]
        ans.ai_missing = rv.get("missing", [])
        ans.comment = rv.get("justification") or ans.comment
        ans.status = "suggested" if rv["level"] is not None else ans.status
        done += 1
    db.commit()
    return {"adopted": done}


@app.post("/api/assessments/{aid}/answers/{n}/adopt-review")
def adopt_review(aid: int, n: int, db: Session = Depends(get_db)):
    """Copia o parecer do revisor para a resposta (nível, evidências e lacunas). Continua sem validar."""
    get_assessment(aid, db)
    ans = get_or_create_answer(db, aid, n)
    rv = ans.claude_review
    if not rv:
        raise HTTPException(400, "Este item não tem parecer do revisor")
    if rv["level"] is not None:
        ans.level, ans.na = rv["level"], False
    ans.evidence = [{k: e[k] for k in ("chunk_id", "doc_id", "doc_name", "slot", "page", "quote")} | {"accepted": e["verdict"] != "nao_comprova"}
                    for e in rv["evidence"]]
    ans.ai_missing = rv.get("missing", [])
    ans.comment = rv.get("justification") or ans.comment
    ans.status = "suggested"
    db.commit()
    return answer_out(catalog.item(n), ans, chunk_texts(db, [ans]))
