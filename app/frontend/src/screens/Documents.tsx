import { useRef, useState } from "react";
import { api } from "../api";
import type { Assessment, Catalog, Doc, Slot } from "../types";

const kb = (n: number) => (n > 1048576 ? `${(n / 1048576).toFixed(1)} MB` : `${Math.max(1, Math.round(n / 1024))} KB`);
const ACCEPT = ".pdf,.docx,.xlsx,.txt,.md,.csv";

/** Área de soltar arquivos que envia cada um para o tipo indicado. */
function Drop({ assessmentId, slot, label, refresh, big }: { assessmentId: number; slot: string; label: string; refresh: () => Promise<unknown>; big?: boolean }) {
  const input = useRef<HTMLInputElement>(null);
  const [over, setOver] = useState(false);
  const [busy, setBusy] = useState(0);
  const [err, setErr] = useState("");
  const send = async (files: FileList | File[]) => {
    setErr("");
    for (const f of Array.from(files)) {
      setBusy(b => b + 1);
      try { await api.upload(assessmentId, slot, f); }
      catch (e) { setErr(`${f.name}: ${e instanceof Error ? e.message : "falha"}`); }
      setBusy(b => b - 1);
    }
    await refresh();
  };
  return (
    <>
      <div className={`drop ${big ? "big" : ""} ${over ? "over" : ""}`} role="button" tabIndex={0}
        onClick={() => input.current?.click()} onKeyDown={e => (e.key === "Enter" || e.key === " ") && input.current?.click()}
        onDragOver={e => { e.preventDefault(); setOver(true); }} onDragLeave={() => setOver(false)}
        onDrop={e => { e.preventDefault(); setOver(false); send(e.dataTransfer.files); }}>
        {busy ? (slot === "principal" ? "Lendo o arquivo e identificando o que ele cobre…" : "Enviando…") : label}
        <input ref={input} type="file" multiple={slot !== "principal"} hidden accept={ACCEPT} onChange={e => e.target.files && send(e.target.files)} />
      </div>
      {err && <div className="banner err small">{err}</div>}
    </>
  );
}

function FileRow({ d, assessmentId, refresh }: { d: Doc; assessmentId: number; refresh: () => Promise<unknown> }) {
  return (
    <div className="file">
      <span className="fname" title={d.filename}>{d.filename}</span>
      <span className="muted">{kb(d.size)}, {d.chunks} trechos</span>
      <button className="link danger" onClick={async () => { await api.removeDoc(assessmentId, d.id); refresh(); }}>remover</button>
      {d.error && <div className="banner warn small">{d.error}</div>}
    </div>
  );
}

function SlotCard({ slot, assessment, principals, refresh }: { slot: Slot; assessment: Assessment; principals: Doc[]; refresh: () => Promise<unknown> }) {
  const [more, setMore] = useState(false);
  const own = assessment.documents.filter(d => d.slot === slot.id);
  const via = principals.flatMap(p => p.covers.filter(c => c.slot === slot.id).map(c => ({ doc: p, cover: c })));
  const covered = own.some(d => d.chunks > 0) || via.length > 0;
  return (
    <div className={`slot ${covered ? "filled" : ""}`}>
      <div className="slot-h"><h3>{slot.name}</h3><span className="chip">{slot.items.length} perguntas</span></div>
      <p>{slot.description}</p>
      {via.map(({ doc, cover }) => (
        <div key={doc.id} className="via">
          <span>No arquivo principal <b>{doc.filename}</b></span>
          <span className="muted small">{cover.reason}</span>
          <button className="link" onClick={async () => { await api.removeCover(assessment.id, doc.id, slot.id); refresh(); }}>Não está nesse arquivo</button>
        </div>
      ))}
      {own.map(d => <FileRow key={d.id} d={d} assessmentId={assessment.id} refresh={refresh} />)}
      {via.length > 0 && !more && own.length === 0
        ? <button className="link" onClick={() => setMore(true)}>Anexar um documento separado</button>
        : <Drop assessmentId={assessment.id} slot={slot.id} label="Arraste aqui ou clique para anexar" refresh={refresh} />}
      {!covered && principals.length > 0 && (
        <button className="link" onClick={async () => { await api.addCover(assessment.id, principals[0].id, slot.id); refresh(); }}>
          Está no arquivo principal
        </button>
      )}
    </div>
  );
}

export default function Documents({ catalog, assessment, refresh, next }: { catalog: Catalog; assessment: Assessment; refresh: () => Promise<unknown>; next: () => void }) {
  const principals = assessment.documents.filter(d => d.slot === "principal");
  const isCovered = (id: string) =>
    assessment.documents.some(d => d.slot === id && d.chunks > 0) || principals.some(p => p.covers.some(c => c.slot === id));
  const missing = catalog.slots.filter(s => !isCovered(s.id));
  const done = catalog.slots.filter(s => isCovered(s.id));
  const hasText = assessment.documents.some(d => d.chunks > 0);

  return (
    <div>
      <div className="page-h">
        <div>
          <h1>Documentos da empresa</h1>
          <p className="lead">Se você tem um documento que reúne vários assuntos, como um PCN completo ou um manual do SGCN, comece por ele. O sistema identifica quais tipos ele cobre e você anexa só o que faltar.</p>
        </div>
        <div className="side-cta">
          <div className="big">{done.length}<small> / {catalog.slots.length}</small></div>
          <div className="muted">tipos cobertos</div>
          <button className="primary" disabled={!hasText} onClick={next}>Analisar documentos</button>
          <button className="link" onClick={next}>Pular e responder manualmente</button>
        </div>
      </div>

      <section className="principal">
        <h2>Arquivo principal</h2>
        {principals.map(p => (
          <div key={p.id} className="principal-file">
            <FileRow d={p} assessmentId={assessment.id} refresh={refresh} />
            {p.chunks > 0 && <p className="muted small">Cobre {p.covers.length} dos {catalog.slots.length} tipos. Confira abaixo e corrija se algum foi identificado errado.</p>}
          </div>
        ))}
        <Drop assessmentId={assessment.id} slot="principal" refresh={refresh} big={principals.length === 0}
          label={principals.length ? "Enviar outro arquivo principal" : "Arraste aqui o documento consolidado, ou clique para escolher"} />
      </section>

      {missing.length > 0 && (<>
        <h2>{principals.length ? `Ainda faltam ${missing.length}` : "Documentos por tipo"}</h2>
        {principals.length > 0 && <p className="muted">Estes tipos não foram encontrados no arquivo principal. O que você não tiver vira lacuna no relatório.</p>}
        <div className="grid">{missing.map(s => <SlotCard key={s.id} slot={s} assessment={assessment} principals={principals} refresh={refresh} />)}</div>
      </>)}

      {done.length > 0 && (<>
        <h2>Já cobertos ({done.length})</h2>
        <div className="grid">{done.map(s => <SlotCard key={s.id} slot={s} assessment={assessment} principals={principals} refresh={refresh} />)}</div>
      </>)}
    </div>
  );
}
