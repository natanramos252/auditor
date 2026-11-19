import { useEffect, useRef, useState } from "react";
import { api } from "../api";
import type { TermsDoc } from "../types";

/** Texto dos termos de uso, vindo da API (o parágrafo sobre IA muda conforme o provedor configurado). */
export function TermsText({ terms }: { terms: TermsDoc }) {
  return (
    <div className="terms-text">
      {terms.sections.map(s => (
        <section key={s.title}>
          <h4>{s.title}</h4>
          <p>{s.body}</p>
        </section>
      ))}
      <p className="muted small">Versão {terms.version}</p>
    </div>
  );
}

export function useTerms() {
  const [terms, setTerms] = useState<TermsDoc | null>(null);
  const [error, setError] = useState("");
  useEffect(() => { api.terms().then(setTerms).catch(e => setError(e instanceof Error ? e.message : "Erro ao carregar os termos")); }, []);
  return { terms, error };
}

export default function TermsDialog({ open, onClose }: { open: boolean; onClose: () => void }) {
  const ref = useRef<HTMLDialogElement>(null);
  const { terms, error } = useTerms();
  useEffect(() => {
    const d = ref.current;
    if (!d) return;
    if (open && !d.open) d.showModal();
    if (!open && d.open) d.close();
  }, [open]);
  return (
    <dialog ref={ref} className="terms-dialog" onClose={onClose} onClick={e => { if (e.target === ref.current) onClose(); }}>
      <div className="terms-box">
        <div className="terms-head"><h2>{terms?.title ?? "Termos de Uso"}</h2><button className="secondary" onClick={onClose}>Fechar</button></div>
        {error && <div className="banner err">{error}</div>}
        {terms ? <TermsText terms={terms} /> : !error && <p className="muted">Carregando…</p>}
      </div>
    </dialog>
  );
}
