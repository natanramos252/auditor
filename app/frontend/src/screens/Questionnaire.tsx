import { useEffect, useMemo, useState } from "react";
import { api } from "../api";
import type { Assessment, Catalog, Evidence, Item, Level } from "../types";

type Filter = "todas" | "analisadas" | "validar" | "sem_ia" | "falhas" | "validadas";
export const failed = (i: Item) => i.ai_justification.startsWith("[falha]");
export const analyzed = (i: Item) => i.ai_level !== null || (i.ai_justification !== "" && !failed(i));

function Quote({ ev }: { ev: Evidence }) {
  const [open, setOpen] = useState(false);
  const { context: c, quote: q, quote_start: s } = ev;
  const found = c && s >= 0;
  const from = open || !found ? 0 : Math.max(0, s - 160);
  const to = open || !found ? c.length : Math.min(c.length, s + q.length + 160);
  return (
    <blockquote>
      {found ? (<>{from > 0 && "… "}{c.slice(from, s)}<mark>{q}</mark>{c.slice(s + q.length, to)}{to < c.length && " …"}</>) : <mark>{q}</mark>}
      {found && c.length > q.length + 320 && <button className="link" onClick={() => setOpen(!open)}>{open ? "menos contexto" : "mais contexto"}</button>}
    </blockquote>
  );
}

function ItemCard({ item, levels, assessmentId, onSaved, onNext }: { item: Item; levels: Level[]; assessmentId: number; onSaved: (i: Item) => void; onNext: () => void }) {
  const [level, setLevel] = useState<number | null>(item.level);
  const [na, setNa] = useState(item.na);
  const [comment, setComment] = useState(item.comment);
  const [ev, setEv] = useState<Evidence[]>(item.evidence);
  const [busy, setBusy] = useState(false);
  const [err, setErr] = useState("");
  const [help, setHelp] = useState(false);
  const [manual, setManual] = useState({ doc: "", quote: "" });

  useEffect(() => { setLevel(item.level); setNa(item.na); setComment(item.comment); setEv(item.evidence); setErr(""); }, [item]);

  const accepted = ev.filter(e => e.accepted).length;
  const dirty = level !== item.level || na !== item.na || comment !== item.comment || ev.some((e, i) => e.accepted !== item.evidence[i]?.accepted);
  const warnNoEv = !na && level === 2 && accepted === 0;

  const save = async (validated: boolean) => {
    setBusy(true); setErr("");
    try {
      const out = await api.save(assessmentId, item.n, { level: na ? null : level, na, comment, validated,
        evidence: ev.map(e => ({ chunk_id: e.chunk_id, quote: e.quote, accepted: e.accepted })) });
      onSaved(out);
      if (validated) onNext();
    } catch (e) { setErr(e instanceof Error ? e.message : "Erro ao salvar"); }
    setBusy(false);
  };

  const addManual = async () => {
    if (manual.quote.trim().length < 3 || !manual.doc.trim()) return;
    try { onSaved(await api.addEvidence(assessmentId, item.n, { doc_name: manual.doc, quote: manual.quote })); setManual({ doc: "", quote: "" }); }
    catch (e) { setErr(e instanceof Error ? e.message : "Erro"); }
  };

  const statusLabel = item.status === "validated" ? "Validada" : item.status === "suggested" ? "Sugerida pela IA — falta validar" : "Sem resposta";
  const conf = item.ai_confidence ?? 0;

  return (
    <article className={`item ${item.status}`} id={`item-${item.n}`}>
      <div className="item-h">
        <span className="num">{item.n}</span>
        <span className="muted">Cláusula {item.subclause || item.clause}</span>
        {item.blocking && <span className="chip warn" title="Requisito obrigatório: precisa estar como Atende para a classificação pronta">bloqueante</span>}
        <span className={`chip st-${item.status}`}>{statusLabel}</span>
      </div>
      <h3>{item.question}</h3>
      <button className="link" onClick={() => setHelp(!help)}>{help ? "Ocultar" : "O que costuma comprovar este requisito?"}</button>
      {help && <div className="help">{item.evidence_examples}</div>}

      {failed(item) ? <div className="banner warn small">A análise automática falhou para este item ({item.ai_justification.replace("[falha] ", "")}). Responda manualmente ou reanalise.</div> : item.ai_justification || item.ai_missing.length > 0 ? (
        <div className="ai">
          <div className="ai-h">
            <b>Análise dos documentos</b>
            {item.ai_level !== null && <span>sugere: <b>{levels[item.ai_level].name}</b></span>}
            {item.ai_level !== null && <span className="conf" title={`Confiança ${Math.round(conf * 100)}%`}><i style={{ width: `${conf * 100}%` }} /></span>}
          </div>
          {item.ai_justification && <p>{item.ai_justification}</p>}
          {item.ai_missing.length > 0 && <ul className="missing">{item.ai_missing.map(m => <li key={m}>Falta: {m}</li>)}</ul>}
        </div>
      ) : null}

      <div className="levels" role="radiogroup" aria-label="Resposta">
        {levels.map(l => (
          <button key={l.level} type="button" role="radio" aria-checked={!na && level === l.level} title={l.description}
            className={`lvl ${!na && level === l.level ? "sel" : ""} ${item.ai_level === l.level ? "ai" : ""}`}
            onClick={() => { setNa(false); setLevel(l.level); }}>
            <b>{l.name}</b>
          </button>
        ))}
        <button type="button" role="radio" aria-checked={na} className={`lvl na ${na ? "sel" : ""}`} onClick={() => { setNa(true); setLevel(null); }}>
          <b>Não se aplica</b>
        </button>
      </div>
      {level !== null && !na && <p className="muted small">{levels[level].description}</p>}

      <div className="evs">
        <h4>Evidências ({accepted} aceita{accepted === 1 ? "" : "s"})</h4>
        {ev.length === 0 && <p className="muted small">Nenhum trecho encontrado nos documentos. Anexe o documento correspondente ou registre uma evidência manualmente.</p>}
        {ev.map((e, i) => (
          <label key={i} className={`ev ${e.accepted ? "" : "off"}`}>
            <input type="checkbox" checked={e.accepted} onChange={() => setEv(ev.map((x, j) => (j === i ? { ...x, accepted: !x.accepted } : x)))} />
            <div>
              <div className="ev-h">{e.manual ? "Informada manualmente" : "Recortada automaticamente"} · <b>{e.doc_name}</b>{e.page ? ` · pág. ${e.page}` : ""}</div>
              <Quote ev={e} />
            </div>
          </label>
        ))}
        <details className="manual">
          <summary>Adicionar evidência manualmente</summary>
          <input placeholder="Nome do documento" value={manual.doc} onChange={e => setManual({ ...manual, doc: e.target.value })} />
          <textarea rows={2} placeholder="Trecho que comprova o requisito" value={manual.quote} onChange={e => setManual({ ...manual, quote: e.target.value })} />
          <button type="button" className="secondary" onClick={addManual}>Adicionar</button>
        </details>
      </div>
      {warnNoEv && <div className="banner warn small">"Atende" sem evidência aceita: na pontuação este item valerá "Atende parcialmente".</div>}

      <textarea className="comment" rows={2} placeholder="Comentário (opcional)" value={comment} onChange={e => setComment(e.target.value)} />
      {err && <div className="banner err small">{err}</div>}
      <div className="actions">
        <button className="primary" disabled={busy || (!na && level === null)} onClick={() => save(true)}>{item.status === "validated" && !dirty ? "Validada ✓ (próxima)" : "Validar e ir para a próxima"}</button>
        <button className="secondary" disabled={busy || !dirty} onClick={() => save(false)}>Salvar sem validar</button>
        {dirty && <span className="muted small">alterações não salvas</span>}
      </div>
    </article>
  );
}

export default function Questionnaire({ catalog, assessment, done }: { catalog: Catalog; assessment: Assessment; done: () => void }) {
  const [items, setItems] = useState<Item[]>([]);
  const [clause, setClause] = useState<number>(4);
  const [filter, setFilter] = useState<Filter>("todas");
  const [loading, setLoading] = useState(true);

  useEffect(() => { api.items(assessment.id).then(setItems).finally(() => setLoading(false)); }, [assessment.id]);

  const clauses = useMemo(() => {
    const m = new Map<number, { no: number; name: string; total: number; ok: number }>();
    for (const i of items) {
      const c = m.get(i.clause_no) ?? { no: i.clause_no, name: i.clause, total: 0, ok: 0 };
      c.total++; if (i.status === "validated") c.ok++;
      m.set(i.clause_no, c);
    }
    return [...m.values()].sort((a, b) => a.no - b.no);
  }, [items]);

  const validated = items.filter(i => i.status === "validated").length;
  const toValidate = items.filter(i => i.status === "suggested").length;
  const shown = items.filter(i => i.clause_no === clause && (
    filter === "todas" || (filter === "analisadas" && analyzed(i)) || (filter === "falhas" && failed(i)) || (filter === "validar" && i.status !== "validated") || (filter === "sem_ia" && i.evidence.length === 0) || (filter === "validadas" && i.status === "validated")));

  const onSaved = (u: Item) => setItems(prev => prev.map(i => (i.n === u.n ? u : i)));
  const goNext = (n: number) => {
    const idx = items.findIndex(i => i.n === n);
    const nxt = items.slice(idx + 1).find(i => i.status !== "validated" && i.n !== n);
    if (!nxt) return;
    setClause(nxt.clause_no);
    setTimeout(() => document.getElementById(`item-${nxt.n}`)?.scrollIntoView({ behavior: "smooth", block: "start" }), 80);
  };

  if (loading) return <div className="center">Carregando questionário…</div>;
  return (
    <div className="qwrap">
      <aside className="side">
        <div className="prog"><b>{validated}</b> / {items.length} validadas<div className="bar"><i style={{ width: `${(validated / Math.max(items.length, 1)) * 100}%` }} /></div></div>
        {toValidate > 0 && <p className="muted small">{toValidate} sugestão(ões) da IA aguardando sua validação.</p>}
        {clauses.map(c => (
          <button key={c.no} className={`clause ${c.no === clause ? "on" : ""}`} onClick={() => setClause(c.no)}>
            <span>{c.name}</span><span className={`cnt ${c.ok === c.total ? "full" : ""}`}>{c.ok}/{c.total}</span>
          </button>
        ))}
        <button className="primary wide" onClick={done}>Ver painel e relatório →</button>
      </aside>
      <section className="qmain">
        <div className="filters">
          {([["todas", "Todas"], ["analisadas", `Analisadas (${items.filter(analyzed).length})`], ["validar", "A validar"], ["sem_ia", "Sem evidência"], ...(items.some(failed) ? [["falhas", `Falharam (${items.filter(failed).length})`]] : []), ["validadas", "Validadas"]] as [Filter, string][]).map(([k, l]) => (
            <button key={k} className={`pill ${filter === k ? "on" : ""}`} onClick={() => setFilter(k)}>{l}</button>
          ))}
        </div>
        {shown.length === 0 && <div className="card">Nenhuma pergunta neste filtro para esta cláusula.</div>}
        {shown.map(i => <ItemCard key={i.n} item={i} levels={catalog.levels} assessmentId={assessment.id} onSaved={onSaved} onNext={() => goNext(i.n)} />)}
      </section>
    </div>
  );
}
