import { useState } from "react";
import { api } from "../api";
import { TermsText, useTerms } from "../components/TermsDialog";
import type { Assessment } from "../types";

export default function TermsGate({ assessment, onAccepted }: { assessment: Assessment; onAccepted: (a: Assessment) => void }) {
  const { terms, error } = useTerms();
  const [agree, setAgree] = useState(false);
  const [by, setBy] = useState("");
  const [busy, setBusy] = useState(false);
  const [err, setErr] = useState("");
  const submit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!terms) return;
    setBusy(true); setErr("");
    try { onAccepted(await api.acceptTerms(assessment.id, { accepted_by: by, terms_version: terms.version })); }
    catch (x) { setErr(x instanceof Error ? x.message : "Erro"); setBusy(false); }
  };
  return (
    <div className="narrow">
      <h1>Aceite os termos para continuar</h1>
      <p className="lead">A avaliação de <b>{assessment.company}</b> não tem o aceite dos Termos de Uso na versão atual ({assessment.terms.current_version}). Leia e aceite para enviar documentos e analisar.</p>
      {error && <div className="banner err">{error}</div>}
      {terms && <div className="card terms-gate"><TermsText terms={terms} /></div>}
      <form onSubmit={submit} className="accept" style={{ marginTop: 18 }}>
        <label className="check"><input type="checkbox" checked={agree} onChange={e => setAgree(e.target.checked)} /><span>Li e aceito os Termos de Uso e o Aviso de Privacidade.</span></label>
        {agree && <label>Seu nome, para registrar o aceite<input required minLength={2} value={by} onChange={e => setBy(e.target.value)} /></label>}
        {err && <div className="banner err small">{err}</div>}
        <div><button className="primary" disabled={busy || !agree || by.trim().length < 2 || !terms}>{busy ? "Registrando…" : "Aceitar e continuar"}</button></div>
      </form>
    </div>
  );
}
