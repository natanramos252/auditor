import { useEffect, useState } from "react";
import { api } from "../api";
import type { Assessment, Catalog, Report } from "../types";
import { CAT, Donut, Gauge, Legend, Radar, Stacked, type Cat } from "../components/charts";

export default function Dashboard({ catalog, assessment, goQuestionnaire, goReport }: { catalog: Catalog; assessment: Assessment; goQuestionnaire: () => void; goReport: () => void }) {
  const [r, setR] = useState<Report | null>(null);
  useEffect(() => { api.report(assessment.id).then(setR); }, [assessment.id]);
  if (!r) return <div className="center">Carregando painel…</div>;
  const s = r.scores, d = s.distribution;
  const name = (no: number) => catalog.items.find(i => i.clause_no === no)?.clause.replace(/^\d+\.\s*/, "") ?? "";
  const blockersOpen = s.blockers.length;
    const worst = [...s.clauses].filter(c => c.items > 0).sort((a, b) => a.score - b.score).slice(0, 3);

  return (
    <div>
      <div className="page-h">
        <div>
          <h1>Painel de maturidade</h1>
          <p className="muted">{r.company}, {r.norm}. Atualiza conforme você valida o questionário.</p>
        </div>
        <div className="row">
          <button className="secondary" onClick={goQuestionnaire}>Continuar validando</button>
          <button className="primary" onClick={goReport}>Relatório completo</button>
        </div>
      </div>

      {s.completeness < 1 && <div className="banner warn">{s.validated} de {s.total} perguntas validadas. Itens não validados contam como "Não atende", então os números estão subestimados até você terminar.</div>}

      <div className="ledger">
        <div className="cell lead-cell"><span>Grau de maturidade</span><b>{Math.round(s.overall)}%</b><em>{s.band}</em></div>
        <div className="cell"><span>Validação</span><b>{Math.round(s.completeness * 100)}%</b><em>{s.validated} de {s.total} perguntas</em></div>
        <div className={`cell ${blockersOpen ? "low" : "ok"}`}><span>Bloqueantes pendentes</span><b>{blockersOpen}</b><em>de {r.stats.blockers_total} obrigatórios</em></div>
        <div className="cell"><span>Evidências aceitas</span><b>{r.stats.evidences_accepted}</b><em>{r.stats.ai_suggested} sugestões da IA</em></div>
        <div className="cell"><span>Confiança</span><b>{Math.round(s.confidence * 100)}%</b><em>{s.downgraded} rebaixado(s) sem evidência</em></div>
      </div>

      <div className="dgrid">
        <section className="card">
          <h3>Maturidade geral</h3>
          <Gauge value={s.overall} target={s.target} />
          <p className="muted small center-t">A marca preta é a meta de {s.target}% para auditoria externa.</p>
          <div className="scale"><span className="bad">0–30 Inicial</span><span className="warn">30–55 Estruturação</span><span className="mid">55–{s.target} Parcial</span><span className="good">{s.target}+ Pronta</span></div>
        </section>

        <section className="card">
          <h3>Como estão as respostas</h3>
          <div className="donut-row">
            <Donut data={d} />
            <ul className="dl">
              {(["atende", "parcial", "nao", "na", "pending"] as Cat[]).map(k => (
                <li key={k}><i style={{ background: CAT[k].color }} />{CAT[k].label}<b>{d[k]}</b></li>
              ))}
            </ul>
          </div>
        </section>

        <section className="card">
          <h3>Perfil por cláusula</h3>
          <Radar data={s.clauses} target={s.target} />
          <p className="muted small center-t">Linha tracejada = meta. Números = cláusulas da norma.</p>
        </section>

        <section className="card wide2">
          <h3>Atendimento por cláusula</h3>
          {s.clauses.map(c => (
            <div key={c.clause_no} className="crow2">
              <span className="cname" title={name(c.clause_no)}>{c.clause_no}. {name(c.clause_no)}</span>
              <Stacked dist={c.dist} />
              <b>{Math.round(c.score)}%</b>
            </div>
          ))}
          <Legend keys={["atende", "parcial", "nao", "na", "pending"]} />
        </section>

        <section className="card">
          <h3>Onde agir primeiro</h3>
          {worst.length > 0 && <p className="muted small">Cláusulas com menor nota: {worst.map(c => `${c.clause_no} (${Math.round(c.score)}%)`).join(", ")}</p>}
          {r.suggestions.length === 0 ? <p className="muted">Nenhuma lacuna nos itens validados.</p> :
            <ol className="top5">{r.suggestions.slice(0, 5).map(x => (
              <li key={x.n}>{x.blocking && <span className="chip warn">bloqueante</span>} <b>{x.clause}</b> {x.question}</li>))}</ol>}
        </section>
      </div>
    </div>
  );
}
