import type { Assessment, Catalog, Doc, Item, Report, TermsDoc } from "./types";

async function req<T>(url: string, init?: RequestInit): Promise<T> {
  const r = await fetch(url, init);
  if (!r.ok) {
    let msg = `Erro ${r.status}`;
    try { const j = await r.json(); msg = typeof j.detail === "string" ? j.detail : msg; } catch { /* corpo vazio */ }
    throw new Error(msg);
  }
  return r.json();
}
const json = (method: string, body: unknown): RequestInit => ({ method, headers: { "Content-Type": "application/json" }, body: JSON.stringify(body) });

export const api = {
  catalog: () => req<Catalog>("/api/catalog"),
  terms: () => req<TermsDoc>("/api/terms"),
  acceptTerms: (id: number, b: { accepted_by: string; terms_version: string }) => req<Assessment>(`/api/assessments/${id}/accept-terms`, json("POST", b)),
  create: (b: { company: string; sector: string; scope: string; accept_terms: boolean; accepted_by: string; terms_version: string }) => req<Assessment>("/api/assessments", json("POST", b)),
  get: (id: number) => req<Assessment>(`/api/assessments/${id}`),
  upload: (id: number, slot: string, file: File) => {
    const fd = new FormData(); fd.append("slot", slot); fd.append("file", file);
    return req<Doc>(`/api/assessments/${id}/documents`, { method: "POST", body: fd });
  },
  removeDoc: (id: number, did: number) => req<{ ok: boolean }>(`/api/assessments/${id}/documents/${did}`, { method: "DELETE" }),
  addCover: (id: number, did: number, slot: string) => req<Doc>(`/api/assessments/${id}/documents/${did}/covers/${slot}`, { method: "PUT" }),
  removeCover: (id: number, did: number, slot: string) => req<Doc>(`/api/assessments/${id}/documents/${did}/covers/${slot}`, { method: "DELETE" }),
  analyze: (id: number) => req<Assessment>(`/api/assessments/${id}/analyze`, { method: "POST" }),
  items: (id: number) => req<Item[]>(`/api/assessments/${id}/items`),
  save: (id: number, n: number, b: { level: number | null; na: boolean; comment: string; validated: boolean; evidence: { chunk_id: number | null; quote: string; accepted: boolean }[] }) =>
    req<Item>(`/api/assessments/${id}/answers/${n}`, json("PUT", b)),
  addEvidence: (id: number, n: number, b: { doc_name: string; quote: string; page?: number | null }) =>
    req<Item>(`/api/assessments/${id}/answers/${n}/evidence`, json("POST", b)),
  adoptAll: (id: number) => req<{ adopted: number }>(`/api/assessments/${id}/review/adopt-all`, { method: "POST" }),
  adoptReview: (id: number, n: number) => req<Item>(`/api/assessments/${id}/answers/${n}/adopt-review`, { method: "POST" }),
  report: (id: number) => req<Report>(`/api/assessments/${id}/report`),
};
