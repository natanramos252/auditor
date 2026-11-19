export interface Slot { id: string; name: string; description: string; items: number[] }
export interface Level { level: number; name: string; description: string }
export interface CatalogItem { n: number; clause: string; clause_no: number; subclause: string; question: string; evidence_examples: string; weight: number; blocking: boolean; slots: string[] }
export interface Catalog { norm: string; slots: Slot[]; items: CatalogItem[]; levels: Level[]; llm: { provider: string; model: string } }
export interface Doc { id: number; slot: string; filename: string; size: number; chunks: number; error: string }
export interface Analysis { status: "idle" | "running" | "done" | "error"; done: number; total: number; error: string; provider: string }
export interface Assessment { id: number; company: string; sector: string; scope: string; analysis: Analysis; documents: Doc[] }
export interface Evidence { chunk_id: number | null; doc_name: string; page: number | null; quote: string; accepted: boolean; context: string; quote_start: number; manual?: boolean }
export type Status = "pending" | "suggested" | "validated";
export interface Item extends CatalogItem {
  status: Status; level: number | null; na: boolean; comment: string;
  ai_level: number | null; ai_confidence: number | null; ai_justification: string; ai_missing: string[]; evidence: Evidence[];
}
export type Dist = Record<"atende" | "parcial" | "nao" | "na" | "pending", number>;
export interface ClauseScore { clause_no: number; name: string; score: number; items: number; dist: Dist }
export interface Scores { overall: number; target: number; band: string; band_description: string; ready: boolean; clauses: ClauseScore[]; distribution: Dist; blockers: number[]; validated: number; total: number; completeness: number; confidence: number; downgraded: number }
export interface Suggestion { n: number; clause: string; question: string; blocking: boolean; current: number; current_label: string; what: string; evidence: string; missing: string[]; validated: boolean; effort: string }
export interface Report { company: string; sector: string; scope: string; norm: string; analysis_provider: string; scores: Scores; strengths: { n: number; clause: string; question: string; level: number }[]; suggestions: Suggestion[]; pending: number[]; stats: { evidences_accepted: number; ai_suggested: number; blockers_total: number }; disclaimer: string }
