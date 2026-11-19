import { useEffect, useState } from "react";
import { api } from "../api";
import type { Assessment, Catalog, Report } from "../types";
import { Radar } from "../components/charts";

export default function ReportScreen({ catalog, assessment, back }: { catalog: Catalog; assessment: Assessment; back: () => void }) {
  const [r, setR] = useState<Report | null>(null);
  useEffect(() => { api.report(assessment.id).then(setR); }, [assessment.id]);
  if (!r) return <div className="center">Gerando relatório…</div>;
  const s = r.scores;
  const clauseName = (no: number) => catalog.items.find(i => i.clause_no === no)?.clause.replace(/^\d+\.\s*/, "") ?? "";
  const tone = s.ready ? "ok" : s.overall >= 55 ? "mid" : "low";

  return (
    <div className="report">
      <div className="page-h noprint">
        <button className="link" onClick={back}>← Voltar ao questionário</button>
        <button className="primary" onClick={() => window.print()}>Imprimir / salvar em PDF</button>
      </div>
      <h1>Relatório de prontidão — {r.company}</h1>
      <p className="muted">{r.norm}{r.sector ? ` · ${r.sector}` : ""}{r.scope ? ` · Escopo: ${r.scope}` : ""}</p>

      {s.completeness < 1 && <div className="banner warn">Apenas {s.validated} de {s.total} perguntas foram validadas. Itens não validados contam como "Não atende" na pontuação, então o resultado abaixo está subestimado.</div>}

      <section className={`hero ${tone}`}>
        <div>
          <div className="score">{Math.round(s.overall)}<small>% de atendimento</small></div>
          <div className="band">{s.band}</div>
          <p>{s.band_description}</p>
          <p className="muted small">Confiança do diagnóstico: {Math.round(s.confidence * 100)}% · {s.downgraded > 0 ? `${s.downgraded} item(ns) rebaixado(s) por falta de evidência` : "sem rebaixamentos por falta de evidência"}</p>
        </div>
        <Radar data={s.clauses} target={s.target} />
      </section>

      <section>
        <h2>Maturidade por cláusula</h2>
        {s.clauses.map(c => (
          <div key={c.clause_no} className="crow">
            <span className="cname">{clauseName(c.clause_no)}</span>
            <div className="cbar"><i className={c.score >= s.target ? "good" : c.score >= 55 ? "mid" : "bad"} style={{ width: `${c.score}%` }} /><em style={{ left: `${s.target}%` }} /></div>
            <b>{Math.round(c.score)}%</b>
          </div>
        ))}
        <p className="muted small">A linha marca {s.target}% de atendimento, referência para considerar a cláusula pronta para a auditoria externa.</p>
      </section>

      <section>
        <h2>Pontos fortes</h2>
        {r.strengths.length === 0 ? <p className="muted">Nenhum requisito foi validado como "Atende" com evidência ainda.</p> :
          <ul className="list">{r.strengths.map(x => <li key={x.n}><b>{x.clause}</b> — {x.question} <span className="chip">Atende</span></li>)}</ul>}
      </section>

      <section>
        <h2>O que melhorar antes da auditoria externa</h2>
        {s.blockers.length > 0 && <div className="banner err">Requisitos bloqueantes que ainda não "atendem": {s.blockers.join(", ")}. Resolva-os primeiro.</div>}
        {r.suggestions.length === 0 ? <p className="muted">Nenhuma lacuna: todos os requisitos validados atendem.</p> :
          <ol className="sugg">{r.suggestions.map(x => (
            <li key={x.n}>
              <div className="sugg-h"><b>{x.clause}</b>
                {x.blocking && <span className="chip warn">bloqueante</span>}
                <span className="chip">hoje: {x.current_label}</span>
                <span className="chip">esforço {x.effort}</span>
                {!x.validated && <span className="chip">não validado</span>}
              </div>
              <p>{x.question}</p>
              <p className="muted small"><b>Evidência que comprovaria:</b> {x.evidence}</p>
              {x.missing.length > 0 && <ul className="missing">{x.missing.map(m => <li key={m}>{m}</li>)}</ul>}
            </li>))}
          </ol>}
      </section>

      <p className="disclaimer">{r.disclaimer}</p>
    </div>
  );
}
