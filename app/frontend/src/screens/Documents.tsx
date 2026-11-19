import { useRef, useState } from "react";
import { api } from "../api";
import type { Assessment, Catalog, Slot } from "../types";

const kb = (n: number) => (n > 1048576 ? `${(n / 1048576).toFixed(1)} MB` : `${Math.max(1, Math.round(n / 1024))} KB`);

function SlotCard({ slot, assessment, refresh }: { slot: Slot; assessment: Assessment; refresh: () => Promise<unknown> }) {
  const input = useRef<HTMLInputElement>(null);
  const [over, setOver] = useState(false);
  const [busy, setBusy] = useState(0);
  const [err, setErr] = useState("");
  const docs = assessment.documents.filter(d => d.slot === slot.id);

  const send = async (files: FileList | File[]) => {
    setErr("");
    for (const f of Array.from(files)) {
      setBusy(b => b + 1);
      try { await api.upload(assessment.id, slot.id, f); }
      catch (e) { setErr(`${f.name}: ${e instanceof Error ? e.message : "falha"}`); }
      setBusy(b => b - 1);
    }
    await refresh();
  };

  return (
    <div className={`slot ${docs.length ? "filled" : ""}`}>
      <div className="slot-h">
        <h3>{slot.name}</h3>
        <span className="chip">{slot.items.length} perguntas</span>
      </div>
      <p className="muted">{slot.description}</p>
      <div className={`drop ${over ? "over" : ""}`}
        onClick={() => input.current?.click()}
        onDragOver={e => { e.preventDefault(); setOver(true); }}
        onDragLeave={() => setOver(false)}
        onDrop={e => { e.preventDefault(); setOver(false); send(e.dataTransfer.files); }}>
        {busy ? "Enviando…" : "Arraste aqui ou clique para anexar"}
        <input ref={input} type="file" multiple hidden accept=".pdf,.docx,.xlsx,.txt,.md,.csv" onChange={e => e.target.files && send(e.target.files)} />
      </div>
      {err && <div className="banner err small">{err}</div>}
      {docs.map(d => (
        <div key={d.id} className="file">
          <span className="fname" title={d.filename}>{d.filename}</span>
          <span className="muted">{kb(d.size)} · {d.chunks} trechos</span>
          <button className="link danger" onClick={async () => { await api.removeDoc(assessment.id, d.id); refresh(); }}>remover</button>
          {d.error && <div className="banner warn small">{d.error}</div>}
        </div>
      ))}
    </div>
  );
}

export default function Documents({ catalog, assessment, refresh, next }: { catalog: Catalog; assessment: Assessment; refresh: () => Promise<unknown>; next: () => void }) {
  const filled = new Set(assessment.documents.filter(d => d.chunks > 0).map(d => d.slot)).size;
  return (
    <div>
      <div className="page-h">
        <div>
          <h1>Documentos da empresa</h1>
          <p className="lead">Anexe o que você já tem, em PDF, Word, Excel ou texto. <b>Não precisa ter todos</b>: o que faltar será indicado no relatório como lacuna. Documentos escaneados (imagem) ainda não são lidos.</p>
        </div>
        <div className="side-cta">
          <div className="big">{filled}<small> / {catalog.slots.length}</small></div>
          <div className="muted">tipos anexados</div>
          <button className="primary" disabled={!assessment.documents.some(d => d.chunks > 0)} onClick={next}>Analisar documentos →</button>
          <button className="link" onClick={next}>Pular e responder manualmente</button>
        </div>
      </div>
      <div className="grid">
        {catalog.slots.map(s => <SlotCard key={s.id} slot={s} assessment={assessment} refresh={refresh} />)}
      </div>
    </div>
  );
}
