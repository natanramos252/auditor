import re
import uuid
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import BackgroundTasks, Depends, FastAPI, File, Form, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.orm import Session

from . import analysis, catalog, config, scoring
from .db import Base, engine, get_db
from .extract import extract
from .models import Answer, Assessment, Chunk, Document


@asynccontextmanager
async def lifespan(_):
    Base.metadata.create_all(engine)
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
            "llm": {"provider": config.LLM_PROVIDER, "model": config.LLM_MODEL}}


# ---------- avaliações ----------
class AssessmentIn(BaseModel):
    company: str = Field(min_length=2, max_length=200)
    sector: str = ""
    scope: str = ""


def assessment_out(a: Assessment, db: Session) -> dict:
    return {"id": a.id, "company": a.company, "sector": a.sector, "scope": a.scope,
            "analysis": {"status": a.analysis_status, "done": a.analysis_done, "total": a.analysis_total,
                         "error": a.analysis_error, "provider": a.analysis_provider},
            "documents": [doc_out(d) for d in a.documents]}


def doc_out(d: Document) -> dict:
    return {"id": d.id, "slot": d.slot, "filename": d.filename, "size": d.size, "chunks": d.n_chunks, "error": d.error}


@app.post("/api/assessments")
def create_assessment(body: AssessmentIn, db: Session = Depends(get_db)):
    a = Assessment(company=body.company.strip(), sector=body.sector, scope=body.scope)
    db.add(a)
    db.commit()
    return assessment_out(a, db)


@app.get("/api/assessments/{aid}")
def read_assessment(aid: int, db: Session = Depends(get_db)):
    return assessment_out(get_assessment(aid, db), db)


# ---------- documentos ----------
@app.post("/api/assessments/{aid}/documents")
async def upload_document(aid: int, slot: str = Form(...), file: UploadFile = File(...), db: Session = Depends(get_db)):
    a = get_assessment(aid, db)
    if slot not in catalog.load()["slot_by_id"]:
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


# ---------- análise ----------
@app.post("/api/assessments/{aid}/analyze")
def start_analysis(aid: int, bg: BackgroundTasks, db: Session = Depends(get_db)):
    a = get_assessment(aid, db)
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
    return {**{k: it[k] for k in ("n", "clause", "clause_no", "subclause", "question", "evidence_examples", "weight", "blocking", "slots")},
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
