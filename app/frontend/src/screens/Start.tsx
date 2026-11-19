import { useState } from "react";
import { api } from "../api";
import type { Assessment } from "../types";
import TermsDialog, { useTerms } from "../components/TermsDialog";

function Proof() {
  return (
    <figure className="proof" aria-label="Exemplo de como um trecho do documento vira evidência">
      <div className="doc">
        <h5>Política de Continuidade de Negócios</h5>
        <div className="skel" style={{ width: "92%" }} />
        <p style={{ margin: "0 0 4px" }}>
          <mark className="sweep">A Alta Direção estabelece esta política de continuidade de negócios, apropriada ao propósito da organização.</mark>{" "}
          Aprovada em 10/03/2025.
        </p>
        <div className="skel" style={{ width: "78%" }} />
      </div>
      <div className="link-v" aria-hidden="true" />
      <div className="ans">
        <b className="req">Requisito 18</b>
        <div className="q">Existe política de continuidade aprovada pela Alta Direção?</div>
        <div className="res"><span className="tick">✓</span><b style={{ color: "var(--ink)" }}>Atende</b> com evidência recortada de politica.docx, página 1</div>
      </div>
      <figcaption>Exemplo. Na sua avaliação, você confere cada trecho e valida a resposta.</figcaption>
    </figure>
  );
}

export default function Start({ onCreated }: { onCreated: (a: Assessment) => void }) {
  const [company, setCompany] = useState("");
  const [sector, setSector] = useState("");
  const [scope, setScope] = useState("");
  const [by, setBy] = useState("");
  const [agree, setAgree] = useState(false);
  const [showTerms, setShowTerms] = useState(false);
  const { terms } = useTerms();
  const [busy, setBusy] = useState(false);
  const [err, setErr] = useState("");

  const submit = async (e: React.FormEvent) => {
    e.preventDefault();
    setBusy(true); setErr("");
    try { onCreated(await api.create({ company, sector, scope, accept_terms: agree, accepted_by: by, terms_version: terms?.version ?? "" })); }
    catch (x) { setErr(x instanceof Error ? x.message : "Erro"); setBusy(false); }
  };

  return (
    <div className="start">
      <div>
        <h1>Veja quanto dos seus documentos já prova a ISO&nbsp;22301</h1>
        <p className="lead" style={{ marginTop: 16 }}>Anexe política, BIA, planos e atas. A plataforma marca os trechos que comprovam cada requisito, e você só confere.</p>
        <form onSubmit={submit}>
          <label>Nome da empresa<input required minLength={2} value={company} onChange={e => setCompany(e.target.value)} placeholder="Ex.: Acme Ltda" autoFocus /></label>
          <label>Setor<input value={sector} onChange={e => setSector(e.target.value)} placeholder="Ex.: Varejo, saúde, tecnologia" /></label>
          <details>
            <summary>Informar o escopo da certificação</summary>
            <label>Unidades, produtos e serviços incluídos<textarea rows={3} value={scope} onChange={e => setScope(e.target.value)} /></label>
          </details>
          <div className="accept">
            <label className="check">
              <input type="checkbox" checked={agree} onChange={e => setAgree(e.target.checked)} />
              <span>Li e aceito os <button type="button" className="link" onClick={() => setShowTerms(true)}>Termos de Uso e o Aviso de Privacidade</button>.</span>
            </label>
            {agree && <label>Seu nome, para registrar o aceite<input required minLength={2} value={by} onChange={e => setBy(e.target.value)} placeholder="Nome de quem está aceitando" /></label>}
          </div>
          {err && <div className="banner err small">{err}</div>}
          <div><button className="primary" disabled={busy || !agree || by.trim().length < 2 || !terms}>{busy ? "Criando…" : "Começar avaliação"}</button></div>
        </form>
      </div>
      <Proof />
      <TermsDialog open={showTerms} onClose={() => setShowTerms(false)} />
      <ol className="steps3">
        <li><b>1</b><h3>Anexe os documentos</h3><p>Em PDF, Word, Excel ou texto. O que você não tiver vira lacuna no relatório.</p></li>
        <li><b>2</b><h3>Confira o que foi encontrado</h3><p>Cada resposta vem pré-preenchida com o trecho que a sustenta. Você aceita, corrige ou recusa.</p></li>
        <li><b>3</b><h3>Receba o diagnóstico</h3><p>Grau de maturidade, pontos fortes e o que melhorar antes da auditoria externa.</p></li>
      </ol>
    </div>
  );
}
