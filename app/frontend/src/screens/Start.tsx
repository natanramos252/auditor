import { useState } from "react";
import { api } from "../api";
import type { Assessment } from "../types";

export default function Start({ onCreated }: { onCreated: (a: Assessment) => void }) {
  const [company, setCompany] = useState("");
  const [sector, setSector] = useState("");
  const [scope, setScope] = useState("");
  const [busy, setBusy] = useState(false);
  const [err, setErr] = useState("");

  const submit = async (e: React.FormEvent) => {
    e.preventDefault();
    setBusy(true); setErr("");
    try { onCreated(await api.create({ company, sector, scope })); }
    catch (x) { setErr(x instanceof Error ? x.message : "Erro"); setBusy(false); }
  };

  return (
    <div className="narrow">
      <h1>Descubra o quanto sua empresa está pronta para a certificação ISO 22301</h1>
      <p className="lead">Você anexa os documentos que já tem, a plataforma lê tudo, <b>pré-preenche o questionário com os trechos que comprovam cada requisito</b> e você só valida. No fim, recebe o grau de maturidade, os pontos fortes e o que melhorar antes da auditoria externa.</p>
      <form className="card" onSubmit={submit}>
        <label>Nome da empresa<input required minLength={2} value={company} onChange={e => setCompany(e.target.value)} placeholder="Ex.: Acme Ltda" /></label>
        <label>Setor<input value={sector} onChange={e => setSector(e.target.value)} placeholder="Ex.: Varejo, Saúde, Tecnologia" /></label>
        <label>Escopo pretendido para a certificação<textarea rows={3} value={scope} onChange={e => setScope(e.target.value)} placeholder="Unidades, produtos e serviços que entrariam na certificação" /></label>
        {err && <div className="banner err">{err}</div>}
        <button className="primary" disabled={busy}>{busy ? "Criando…" : "Começar"}</button>
      </form>
    </div>
  );
}
