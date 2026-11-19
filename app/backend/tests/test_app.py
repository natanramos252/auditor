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
    r = client.post("/api/assessments", json={"company": "Acme Ltda", "sector": "Varejo"})
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
    it = {"n": 18, "question": "Existe política de continuidade aprovada, apropriada ao propósito da organização?",
          "evidence_examples": "Política de continuidade assinada, com data e versão", "slots": ["politica"], "subclause": "5.2", "clause": "5"}

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
