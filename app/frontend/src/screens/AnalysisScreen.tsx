import { useEffect, useRef, useState } from "react";
import { api } from "../api";
import type { Assessment, Item } from "../types";
import { analyzed, failed } from "./Questionnaire";

const LABEL = ["Não atende", "Atende parcialmente", "Atende"];

function Result({ i }: { i: Item }) {
  if (failed(i)) return <span className="chip warn">falhou</span>;
  if (i.ai_level !== null) return <span className="chip st-suggested">{LABEL[i.ai_level]} · {i.evidence.length} evid.</span>;
  if (i.ai_justification) return <span className="chip">sem trecho relevante</span>;
  return <span className="muted small">aguardando</span>;
}

function Evaluated({ id, running }: { id: number; running: boolean }) {
  const [items, setItems] = useState<Item[]>([]);
  useEffect(() => {
    const load = () => api.items(id).then(setItems).catch(() => undefined);
    load();
    if (!running) return;
    const t = window.setInterval(load, 2500);
    return () => window.clearInterval(t);
  }, [id, running]);
  const done = items.filter(i => analyzed(i) || failed(i));
  const withSug = items.filter(i => i.ai_level !== null).length;
  if (!done.length) return null;
  return (
    <div className="card" style={{ marginTop: 16 }}>
      <h3>Itens já avaliados ({done.length} de {items.length})</h3>
      <p className="muted small">{withSug} com sugestão e evidência · {done.filter(i => !failed(i) && i.ai_level === null).length} sem trecho relevante · {done.filter(failed).length} com falha</p>
      <div className="evlist">
        {done.map(i => (
          <div key={i.n} className="evrow">
            <span className="num">{i.n}</span>
            <span className="q" title={i.question}>{i.question}</span>
            <Result i={i} />
          </div>
        ))}
      </div>
    </div>
  );
}

export default function AnalysisScreen({ assessment, refresh, next, back, llm }: { assessment: Assessment; refresh: () => Promise<Assessment>; next: () => void; back: () => void; llm: string }) {
  const a = assessment.analysis;
  const timer = useRef<number>();

  useEffect(() => {
    if (a.status !== "running") return;
    timer.current = window.setInterval(() => { refresh().catch(() => undefined); }, 1000);
    return () => window.clearInterval(timer.current);
  }, [a.status, refresh]);

  const start = async () => { await api.analyze(assessment.id).catch(e => alert(e.message)); await refresh(); };
  const pct = a.total ? Math.round((a.done / a.total) * 100) : 0;

  return (
    <div className="narrow">
      <h1>Análise dos documentos</h1>
      <div className="card">
        <p>Para cada uma das 90 perguntas, a plataforma procura nos seus documentos os trechos que comprovam o requisito, sugere se o requisito atende e recorta a evidência. <b>Nada vale até você validar.</b></p>
        <p className="muted">Motor de análise: <b>{llm === "mock" ? "modo demonstração (busca por palavras, sem IA)" : a.provider || llm}</b></p>
        {llm === "mock" && <div className="banner warn small">Sem IA configurada, as sugestões são só uma busca por palavras-chave e têm baixa confiança. Defina LLM_PROVIDER para obter análise completa.</div>}
        {a.status === "idle" && <button className="primary" onClick={start}>Iniciar análise</button>}
        {a.status === "running" && (<><div className="bar"><i style={{ width: `${pct}%` }} /></div><p>{a.done} de {a.total} requisitos analisados ({pct}%)</p></>)}
        {a.status === "error" && (<><div className="banner err">{a.error || "A análise falhou."}</div><button className="primary" onClick={start}>Tentar novamente</button></>)}
        {a.status === "done" && (<>
          <div className="banner ok">Análise concluída. {a.error && <span>Avisos: {a.error}</span>}</div>
          <button className="primary" onClick={next}>Revisar o questionário →</button>
          <button className="link" onClick={start}>Reanalisar (mantém o que você já validou)</button>
        </>)}
        <div><button className="link" onClick={back}>← Voltar aos documentos</button></div>
      </div>
      {a.status !== "idle" && <Evaluated id={assessment.id} running={a.status === "running"} />}
    </div>
  );
}
