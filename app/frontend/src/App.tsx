import { useCallback, useEffect, useState } from "react";
import { api } from "./api";
import type { Assessment, Catalog } from "./types";
import Start from "./screens/Start";
import Documents from "./screens/Documents";
import AnalysisScreen from "./screens/AnalysisScreen";
import Questionnaire from "./screens/Questionnaire";
import Dashboard from "./screens/Dashboard";
import TermsGate from "./screens/TermsGate";
import TermsDialog from "./components/TermsDialog";
import ReportScreen from "./screens/ReportScreen";

const STEPS = ["Empresa", "Documentos", "Análise", "Questionário", "Painel", "Relatório"];
const KEY = "auditor.assessment";

export default function App() {
  const [catalog, setCatalog] = useState<Catalog | null>(null);
  const [assessment, setAssessment] = useState<Assessment | null>(null);
  const [step, setStep] = useState(0);
  const [error, setError] = useState("");
  const [showTerms, setShowTerms] = useState(false);

  const refresh = useCallback(async (id: number) => {
    const a = await api.get(id);
    setAssessment(a);
    return a;
  }, []);

  useEffect(() => {
    (async () => {
      try {
        setCatalog(await api.catalog());
        const fromUrl = new URLSearchParams(location.search).get("avaliacao");  // abre uma avaliação específica: ?avaliacao=10
        if (fromUrl) { localStorage.setItem(KEY, fromUrl); history.replaceState(null, "", location.pathname); }
        const saved = Number(localStorage.getItem(KEY));
        if (saved) {
          const a = await refresh(saved);
          setStep(a.analysis.status === "done" ? 3 : a.documents.length ? 1 : 1);
        }
      } catch (e) {
        if (localStorage.getItem(KEY)) localStorage.removeItem(KEY);
        setError(e instanceof Error ? e.message : "Falha ao conectar com a API");
      }
    })();
  }, [refresh]);

  const created = (a: Assessment) => { localStorage.setItem(KEY, String(a.id)); setAssessment(a); setStep(1); };
  const restart = () => { localStorage.removeItem(KEY); setAssessment(null); setStep(0); };

  if (error && !catalog) return <div className="center"><div className="card"><h2>Não foi possível conectar</h2><p>{error}</p></div></div>;
  if (!catalog) return <div className="center">Carregando…</div>;

  return (
    <div className="shell">
      <aside className="rail">
        <div className="brand"><span className="brand-mark">22301</span>Prontidão</div>
        <ol className="steps" aria-label="Etapas da avaliação">
          {STEPS.map((s, i) => (
            <li key={s}>
              <button className={`step ${i === step ? "on" : ""} ${i < step ? "done" : ""}`} aria-current={i === step ? "step" : undefined}
                disabled={!assessment && i > 0} onClick={() => setStep(i)}>
                <span>{i + 1}</span>{s}
              </button>
            </li>
          ))}
        </ol>
        <div className="who">
          {assessment && <><b>{assessment.company}</b><button className="link" onClick={restart}>Nova avaliação</button></>}
          <button className="link" onClick={() => setShowTerms(true)}>Termos de uso</button>
        </div>
        <TermsDialog open={showTerms} onClose={() => setShowTerms(false)} />
      </aside>
      <main className="stage">
        {error && <div className="banner err">{error}</div>}
        {step === 0 && <Start onCreated={created} />}
        {assessment && !assessment.terms.accepted && step > 0 && <TermsGate assessment={assessment} onAccepted={setAssessment} />}
        {assessment && assessment.terms.accepted && step === 1 && <Documents catalog={catalog} assessment={assessment} refresh={() => refresh(assessment.id)} next={() => setStep(2)} />}
        {assessment && assessment.terms.accepted && step === 2 && <AnalysisScreen assessment={assessment} refresh={() => refresh(assessment.id)} next={() => setStep(3)} back={() => setStep(1)} llm={catalog.llm} />}
        {assessment && assessment.terms.accepted && step === 3 && <Questionnaire catalog={catalog} assessment={assessment} done={() => setStep(4)} />}
        {assessment && assessment.terms.accepted && step === 4 && <Dashboard catalog={catalog} assessment={assessment} goQuestionnaire={() => setStep(3)} goReport={() => setStep(5)} />}
        {assessment && assessment.terms.accepted && step === 5 && <ReportScreen catalog={catalog} assessment={assessment} back={() => setStep(4)} />}
      </main>
    </div>
  );
}
