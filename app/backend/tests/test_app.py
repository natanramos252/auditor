import os
import tempfile

_tmp = tempfile.mkdtemp()
os.environ["DATA_DIR"] = _tmp
os.environ["DATABASE_URL"] = f"sqlite:///{_tmp}/t.db"
os.environ["LLM_PROVIDER"] = "mock"

import time  # noqa: E402

import docx  # noqa: E402
import pytest  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402

from app import analysis, scoring  # noqa: E402
from app.main import app  # noqa: E402
from app.textutil import fold  # noqa: E402

TERMS = {"accept_terms": True, "accepted_by": "Tester", "terms_version": "1.0"}

POLITICA = """Política de Continuidade de Negócios da Acme Ltda. Versão 2.1, aprovada pela Diretoria em 10/03/2025.
A Alta Direção estabelece esta política de continuidade de negócios, apropriada ao propósito da organização.
A empresa se compromete a satisfazer os requisitos aplicáveis e com a melhoria contínua do sistema de gestão de continuidade de negócios.
A política é comunicada a todos os colaboradores por e-mail e está disponível na intranet para as partes interessadas."""

BIA = """Relatório de Análise de Impacto nos Negócios (BIA) - 2025.
Para cada atividade prioritária foi definido o período máximo tolerável de disrupção (MTPD) e o objetivo de tempo de recuperação (RTO).
Atividade: faturamento. MTPD 48 horas. RTO 24 horas. Recursos necessários: ERP, equipe financeira, fornecedor de internet.
As dependências de fornecedores e parceiros foram identificadas para as atividades priorizadas."""


@pytest.fixture(scope="module")
def client():
    with TestClient(app) as c:
        yield c


def make_docx(path, text):
    d = docx.Document()
    for line in text.split("\n"):
        d.add_paragraph(line)
    d.save(path)


def test_fold_preserves_length():
    s = "Política de CONTINUIDADE, ação"
    assert len(fold(s)) == len(s) and fold(s).startswith("politica")


def test_locate_quote_ignores_accents_and_case():
    text = "A Alta Direção estabelece esta política de continuidade de negócios."
    span = analysis.locate("alta direcao estabelece ESTA política", text)
    assert span and text[span[0]:span[1]].startswith("Alta Direção")
    assert analysis.locate("frase inventada que não existe no texto", text) is None


def test_end_to_end(client, tmp_path):
    r = client.post("/api/assessments", json={"company": "Acme Ltda", "sector": "Varejo", **TERMS})
    aid = r.json()["id"]
    make_docx(tmp_path / "politica.docx", POLITICA)
    for slot, name, content in [("politica", "politica.docx", None), ("bia", "bia.txt", BIA)]:
        files = {"file": (name, open(tmp_path / name, "rb") if content is None else content.encode())}
        up = client.post(f"/api/assessments/{aid}/documents", data={"slot": slot}, files=files)
        assert up.status_code == 200 and up.json()["chunks"] >= 1, up.text

    bad = client.post(f"/api/assessments/{aid}/documents", data={"slot": "bia"}, files={"file": ("x.exe", b"MZ")})
    assert bad.status_code == 400

    assert client.post(f"/api/assessments/{aid}/analyze").status_code == 200
    for _ in range(100):
        st = client.get(f"/api/assessments/{aid}").json()["analysis"]
        if st["status"] in ("done", "error"):
            break
        time.sleep(0.1)
    assert st["status"] == "done" and st["done"] == 90, st

    items = {i["n"]: i for i in client.get(f"/api/assessments/{aid}/items").json()}
    pol = items[18]
    assert pol["status"] == "suggested" and pol["level"] is not None
    assert pol["evidence"] and "politica" in pol["evidence"][0]["doc_name"]
    assert pol["evidence"][0]["quote"] in pol["evidence"][0]["context"]
    assert items[76]["status"] == "pending" and items[76]["evidence"] == []  # sem doc de auditoria

    # profissional valida o item 18 com nível 4 e evidência aceita
    ok = client.put(f"/api/assessments/{aid}/answers/18", json={"level": 2, "comment": "ok", "validated": True})
    assert ok.status_code == 200 and ok.json()["status"] == "validated"
    # nível 3+ sem evidência aceita é rebaixado para 2 na pontuação
    ev = ok.json()["evidence"]
    client.put(f"/api/assessments/{aid}/answers/18", json={"level": 2, "validated": True,
               "evidence": [{"chunk_id": e["chunk_id"], "quote": e["quote"], "accepted": False} for e in ev]})
    rep = client.get(f"/api/assessments/{aid}/report").json()
    assert rep["scores"]["downgraded"] == 1 and rep["scores"]["validated"] == 1
    assert not rep["scores"]["ready"] and 18 in rep["scores"]["blockers"]
    d = rep["scores"]["distribution"]
    assert d["pending"] == 89 and d["parcial"] == 1 and sum(d.values()) == 90  # 18 rebaixado: atende sem evidência -> parcial
    assert rep["stats"]["ai_suggested"] >= 1
    assert rep["suggestions"][0]["blocking"] and "diagnóstico preparatório" in rep["disclaimer"]

    # reanalisar não pode sobrescrever o que foi validado
    client.post(f"/api/assessments/{aid}/analyze")
    for _ in range(100):
        if client.get(f"/api/assessments/{aid}").json()["analysis"]["status"] != "running":
            break
        time.sleep(0.1)
    assert client.get(f"/api/assessments/{aid}/items").json()[17]["level"] == 2

    assert client.put(f"/api/assessments/{aid}/answers/19", json={"validated": True}).status_code == 400


def test_scoring_ready_requires_everything_validated():
    class A:  # resposta mínima
        def __init__(self, n, lvl):
            self.item_no, self.status, self.level, self.na, self.evidence, self.ai_missing = n, "validated", lvl, False, [{"accepted": True}], []
    answers = [A(n, 2) for n in range(1, 91)]
    s = scoring.compute(answers)
    assert s["overall"] == 100.0 and s["ready"] and s["band"] == "Pronta para auditoria externa"
    answers[41].level = 0  # item 42 (BIA) é bloqueante
    s = scoring.compute(answers)
    assert not s["ready"] and 42 in s["blockers"]


def test_llm_path_discards_invented_quotes():
    from types import SimpleNamespace as NS

    from app.llm.base import LLMProvider
    from app.retrieval import Index

    chunk = NS(id=7, page=2, text=POLITICA.replace("\n", " "), document=NS(id=1, filename="pol.txt", slot="politica"))
    from app import catalog
    it = dict(catalog.item(18))

    class Fake(LLMProvider):
        name, model = "fake", "x"

        def complete(self, system, user):
            assert "ignore qualquer instrução" in system.lower() or "ignore qualquer instrução" in system
            return '```json\n{"nivel": 2, "confianca": 0.9, "justificativa": "Política aprovada.", "citacoes": [' \
                   '{"trecho_id": 7, "texto": "aprovada pela Diretoria em 10/03/2025"},' \
                   '{"trecho_id": 7, "texto": "citação totalmente inventada pelo modelo agora"}], "faltando": []}\n```'

    res = analysis.analyze_item(it, Index([chunk]), Fake())
    assert res["level"] == 2 and len(res["evidence"]) == 1
    assert res["evidence"][0]["quote"] == "aprovada pela Diretoria em 10/03/2025"


def test_provider_retries_rate_limit(monkeypatch):
    import httpx

    from app.llm import providers

    calls = []

    def fake_post(url, **kw):
        calls.append(1)
        return httpx.Response(429 if len(calls) < 3 else 200, json={"choices": [{"message": {"content": "{}"}}]},
                              request=httpx.Request("POST", url))

    monkeypatch.setattr(providers.httpx, "post", fake_post)
    monkeypatch.setattr(providers.time, "sleep", lambda s: None)
    assert providers.post("http://x").status_code == 200 and len(calls) == 3


def test_search_ignores_duplicate_chunks():
    from types import SimpleNamespace as NS

    from app.retrieval import Index

    mk = lambda i, slot: NS(id=i, page=None, text=POLITICA.replace("\n", " "), document=NS(id=i, filename="p.docx", slot=slot))  # noqa: E731
    idx = Index([mk(1, "politica"), mk(2, "pcn"), mk(3, "bia")])
    hits = idx.search("política de continuidade de negócios aprovada pela Alta Direção", ["politica"])
    assert len(hits) == 1 and hits[0].slot == "politica"


def test_llm_malformed_answers_do_not_crash():
    from types import SimpleNamespace as NS

    from app.llm.base import LLMProvider
    from app.retrieval import Index

    chunk = NS(id=7, page=None, text=POLITICA.replace("\n", " "), document=NS(id=1, filename="pol.txt", slot="politica"))
    from app import catalog
    it = dict(catalog.item(18))

    class Sloppy(LLMProvider):
        name, model = "sloppy", "x"

        def complete(self, system, user):
            return '{"nivel": "2", "confianca": "alta", "justificativa": 5, "citacoes": ["aprovada pela Diretoria em 10/03/2025", 3, null], "faltando": [null, "ata"]}'

    res = analysis.analyze_item(it, Index([chunk]), Sloppy())
    assert res["level"] == 2 and res["confidence"] == 0.0 and res["missing"] == ["ata"]
    assert res["evidence"] and res["evidence"][0]["quote"] == "aprovada pela Diretoria em 10/03/2025"


def test_principal_document_detects_covered_types(client):
    from pathlib import Path
    aid = client.post("/api/assessments", json={"company": "Principal", **TERMS}).json()["id"]
    manual = Path(__file__).resolve().parents[2] / "samples" / "manual_sgcn_acme.docx"
    up = client.post(f"/api/assessments/{aid}/documents", data={"slot": "principal"}, files={"file": ("manual.docx", manual.read_bytes())})
    assert up.status_code == 200, up.text
    d = up.json()
    covered = {c["slot"] for c in d["covers"]}
    assert {"politica", "bia", "pcn", "auditoria", "analise_critica"} <= covered
    assert "objetivos" not in covered and "backup" not in covered  # o manual de exemplo não tem essas partes

    d = client.delete(f"/api/assessments/{aid}/documents/{d['id']}/covers/bia").json()
    assert "bia" not in {c["slot"] for c in d["covers"]}
    d = client.put(f"/api/assessments/{aid}/documents/{d['id']}/covers/objetivos").json()
    assert any(c["slot"] == "objetivos" and c["reason"] == "Marcado por você" for c in d["covers"])

    client.post(f"/api/assessments/{aid}/analyze")
    for _ in range(100):
        st = client.get(f"/api/assessments/{aid}").json()["analysis"]
        if st["status"] != "running":
            break
        time.sleep(0.1)
    assert st["status"] == "done"
    items = {i["n"]: i for i in client.get(f"/api/assessments/{aid}/items").json()}
    assert items[18]["evidence"], "o principal cobre a política, então o item 18 deve achar evidência"


def test_guard_requires_execution_record():
    from datetime import date

    from app.analysis import guard_level, shows_execution

    today = date(2026, 10, 19)
    plano = "Teste de failover e de restauração de backup | Anual | Coordenador de Disaster Recovery | Relatório com tempo obtido e RTO"
    assert not shows_execution(plano, today)
    assert not shows_execution("O teste será realizado em 10/12/2026.", today)  # data futura não prova execução
    assert shows_execution("Exercício realizado em 18/06/2025, com 22 participantes.", today)
    assert shows_execution("A auditoria foi realizada pela equipe de compliance.", today)
    assert shows_execution("Ata da reunião de 15 de abril de 2025", today)

    lvl, conf, just = guard_level(2, 0.9, "Programa anual de testes.", [{"quote": plano}])
    assert lvl == 1 and conf < 0.9 and "Rebaixado automaticamente" in just
    assert guard_level(2, 0.9, "ok", [{"quote": "Relatório emitido em 20/06/2025."}])[0] == 2
    assert guard_level(1, 0.5, "ok", [{"quote": plano}])[0] == 1  # só mexe em "Atende"


def test_criteria_path_computes_level_by_code_and_checks_quotes():
    from types import SimpleNamespace as NS

    from app import catalog
    from app.llm.base import LLMProvider
    from app.retrieval import Index

    chunk = NS(id=7, page=1, text=POLITICA.replace("\n", " "), document=NS(id=1, filename="pol.txt", slot="politica"))
    it = dict(catalog.item(18))  # 3 critérios, tipo "documento"
    assert it["kind"] == "documento" and len(it["criteria"]) == 3

    class Crit(LLMProvider):
        name, model = "crit", "x"

        def complete(self, system, user):
            assert "Critérios (da norma)" in user and "1. " in user
            return ('{"criterios": [{"i":1,"status":"atendido","trecho_id":7,"texto":"estabelece esta política de continuidade de negócios"},'
                    '{"i":2,"status":"atendido","trecho_id":7,"texto":"apropriada ao propósito da organização"},'
                    '{"i":3,"status":"atendido","trecho_id":7,"texto":"frase que o modelo inventou e não existe no documento"}],'
                    '"confianca":0.9,"justificativa":"ok","faltando":[]}')

    res = analysis.analyze_item(it, Index([chunk]), Crit())
    st = [c["status"] for c in res["criteria"]]
    assert st == ["atendido", "atendido", "parcial"]  # citação inventada derruba "atendido" para "parcial"
    assert res["level"] == 1 and len(res["evidence"]) == 2  # cobertura 2,5/3 = 0,83, abaixo de 0,85: Atende parcialmente


def test_registro_kind_needs_execution_but_documento_does_not():
    from app.analysis import guard_level
    plano = [{"quote": "Teste de failover | Anual | Responsável | Relatório com tempo obtido"}]
    assert guard_level(2, 1.0, "", plano, "registro")[0] == 1
    assert guard_level(2, 1.0, "", plano, "documento")[0] == 2


def test_review_api_verifies_quotes_and_adopt(client, tmp_path):
    aid = client.post("/api/assessments", json={"company": "Revisão", **TERMS}).json()["id"]
    up = client.post(f"/api/assessments/{aid}/documents", data={"slot": "politica"}, files={"file": ("pol.txt", POLITICA.encode())})
    did = up.json()["id"]
    q = client.get(f"/api/assessments/{aid}/review/queue").json()
    item18 = next(i for i in q["items"] if i["n"] == 18)
    assert item18["kind"] == "documento" and len(item18["criteria"]) == 3
    assert client.get(f"/api/assessments/{aid}/review/documents/{did}/text").json()["chunks"]

    body = {"reviewer": "Claude", "model": "teste", "items": [{
        "n": 18, "justification": "Política aprovada e divulgada.",
        "criteria": [{"i": 1, "status": "atendido"}, {"i": 2, "status": "atendido"}, {"i": 3, "status": "atendido"}],
        "evidence": [
            {"quote": "aprovada pela Diretoria em 10/03/2025", "verdict": "comprova", "criterion": 3, "doc_id": did},
            {"quote": "texto inventado que não existe em documento algum", "verdict": "comprova"}]}]}
    r = client.post(f"/api/assessments/{aid}/review", json=body).json()
    assert r["saved"] == 1 and len(r["rejected_quotes"]) == 1 and r["items"][0]["level"] == 2

    item = next(i for i in client.get(f"/api/assessments/{aid}/items").json() if i["n"] == 18)
    assert item["claude_review"]["level"] == 2 and item["claude_review"]["evidence"][0]["quote"] == "aprovada pela Diretoria em 10/03/2025"
    assert item["status"] == "pending"  # o parecer não valida nada

    adopted = client.post(f"/api/assessments/{aid}/answers/18/adopt-review").json()
    assert adopted["level"] == 2 and adopted["status"] == "suggested" and adopted["evidence"][0]["accepted"]
    assert client.post(f"/api/assessments/{aid}/answers/19/adopt-review").status_code == 400


def test_terms_are_required_and_recorded(client):
    t = client.get("/api/terms").json()
    assert t["version"] == "1.0" and len(t["hash"]) == 64 and len(t["sections"]) == 10
    assert "@AI@" not in str(t) and "modo sem IA" in str(t)  # texto da IA em uso é preenchido (testes rodam em mock)

    base = {"company": "Sem aceite"}
    assert client.post("/api/assessments", json=base).status_code == 400
    assert client.post("/api/assessments", json={**base, "accept_terms": True, "terms_version": "1.0"}).status_code == 400  # falta o nome
    assert client.post("/api/assessments", json={**TERMS, **base, "terms_version": "0.1"}).status_code == 409  # versão velha

    a = client.post("/api/assessments", json={**base, **TERMS}).json()
    assert a["terms"]["accepted"] and a["terms"]["accepted_by"] == "Tester" and a["terms"]["current_version"] == "1.0"


def test_old_assessment_cannot_upload_or_analyze_until_accepted(client):
    from app.db import SessionLocal
    from app.models import Assessment
    with SessionLocal() as db:  # avaliação criada antes dos termos: sem registro de aceite
        legacy = Assessment(company="Antiga")
        db.add(legacy)
        db.commit()
        aid = legacy.id
    assert client.get(f"/api/assessments/{aid}").json()["terms"]["accepted"] is False
    up = client.post(f"/api/assessments/{aid}/documents", data={"slot": "politica"}, files={"file": ("p.txt", POLITICA.encode())})
    assert up.status_code == 403 and "Termos" in up.json()["detail"]
    assert client.post(f"/api/assessments/{aid}/analyze").status_code == 403

    assert client.post(f"/api/assessments/{aid}/accept-terms", json={"accepted_by": "Maria", "terms_version": "9.9"}).status_code == 409
    ok = client.post(f"/api/assessments/{aid}/accept-terms", json={"accepted_by": "Maria", "terms_version": "1.0"}).json()
    assert ok["terms"]["accepted"] and ok["terms"]["accepted_by"] == "Maria"
    up = client.post(f"/api/assessments/{aid}/documents", data={"slot": "politica"}, files={"file": ("p.txt", POLITICA.encode())})
    assert up.status_code == 200


def test_adopt_all_skips_validated_and_never_validates(client):
    aid = client.post("/api/assessments", json={"company": "Lote", **TERMS}).json()["id"]
    did = client.post(f"/api/assessments/{aid}/documents", data={"slot": "politica"}, files={"file": ("pol.txt", POLITICA.encode())}).json()["id"]
    item = lambda n, q: {"n": n, "justification": "ok", "criteria": [{"i": i, "status": "atendido"} for i in range(1, {18: 4, 19: 4}[n])],
                         "evidence": [{"quote": q, "doc_id": did, "verdict": "comprova"}]}
    body = {"reviewer": "Claude", "items": [item(18, "aprovada pela Diretoria em 10/03/2025"), item(19, "apropriada ao propósito da organização")]}
    assert client.post(f"/api/assessments/{aid}/review", json=body).json()["saved"] == 2
    client.put(f"/api/assessments/{aid}/answers/19", json={"level": 0, "validated": True})  # o profissional já validou o 19

    assert client.post(f"/api/assessments/{aid}/review/adopt-all").json() == {"adopted": 1}
    items = {i["n"]: i for i in client.get(f"/api/assessments/{aid}/items").json()}
    assert items[18]["status"] == "suggested" and items[18]["level"] == 2
    assert items[19]["status"] == "validated" and items[19]["level"] == 0  # não sobrescreve


def test_provider_without_key_falls_back_to_mock(monkeypatch):
    from app import config, terms
    from app.llm.providers import get_provider

    monkeypatch.setattr(config, "LLM_PROVIDER", "openai")
    monkeypatch.setattr(config, "OPENAI_API_KEY", "")
    monkeypatch.setattr(config, "OPENAI_ALLOW_NO_KEY", False)
    assert config.key_missing("openai") and config.effective_provider() == "mock"
    assert get_provider().name == "mock" and "modo sem IA" in terms.ai_paragraph()

    monkeypatch.setattr(config, "OPENAI_API_KEY", "chave-de-teste")
    assert config.effective_provider() == "openai" and get_provider().name == "openai"
    assert "nuvem" in terms.ai_paragraph() or "provedor de IA" in terms.ai_paragraph()

    monkeypatch.setattr(config, "OPENAI_API_KEY", "")
    monkeypatch.setattr(config, "OPENAI_ALLOW_NO_KEY", True)  # servidor local sem chave
    assert config.effective_provider() == "openai"
    monkeypatch.setattr(config, "LLM_PROVIDER", "anthropic")
    monkeypatch.setattr(config, "ANTHROPIC_API_KEY", "")
    assert config.effective_provider() == "mock"
