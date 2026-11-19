import type { ClauseScore } from "../types";

export const CAT = {
  atende: { label: "Atende", color: "var(--ok)" },
  parcial: { label: "Atende parcialmente", color: "var(--warn)" },
  nao: { label: "Não atende", color: "var(--err)" },
  na: { label: "Não se aplica", color: "var(--muted)" },
  pending: { label: "Não validado", color: "var(--line)" },
} as const;
export type Cat = keyof typeof CAT;

/** Medidor semicircular de 0 a 100, com marca na meta. */
export function Gauge({ value, target }: { value: number; target: number }) {
  const R = 90, C = 110;
  const pt = (v: number, r = R) => { const a = Math.PI * (1 - v / 100); return [C + Math.cos(a) * r, C - Math.sin(a) * r]; };
  const arc = (from: number, to: number, color: string, w = 16) => {
    const [x1, y1] = pt(from), [x2, y2] = pt(to);
    return <path d={`M${x1} ${y1} A${R} ${R} 0 0 1 ${x2} ${y2}`} stroke={color} strokeWidth={w} fill="none" strokeLinecap="butt" />;
  };
  const [nx, ny] = pt(value, R - 22), [tx1, ty1] = pt(target, R - 12), [tx2, ty2] = pt(target, R + 12);
  return (
    <svg viewBox="0 0 220 135" className="gauge" role="img" aria-label={`Maturidade ${Math.round(value)}%`}>
      {arc(0, 30, "var(--err)")}{arc(30, 55, "var(--warn)")}{arc(55, target, "#d6b400")}{arc(target, 100, "var(--ok)")}
      <line x1={tx1} y1={ty1} x2={tx2} y2={ty2} stroke="var(--text)" strokeWidth={2} />
      <line x1={C} y1={C} x2={nx} y2={ny} stroke="var(--text)" strokeWidth={3} strokeLinecap="round" />
      <circle cx={C} cy={C} r={6} fill="var(--text)" />
      <text x={C} y={C + 24} textAnchor="middle" fontSize="22" fontWeight="700" fill="var(--text)">{Math.round(value)}%</text>
    </svg>
  );
}

export function Donut({ data }: { data: Record<Cat, number> }) {
  const order: Cat[] = ["atende", "parcial", "nao", "na", "pending"];
  const total = order.reduce((s, k) => s + data[k], 0) || 1;
  const R = 52, C = 70, L = 2 * Math.PI * R;
  let off = 0;
  return (
    <svg viewBox="0 0 140 140" className="donut" role="img" aria-label="Distribuição das respostas">
      <circle cx={C} cy={C} r={R} fill="none" stroke="var(--line)" strokeWidth={20} />
      {order.map(k => {
        const len = (data[k] / total) * L;
        const el = data[k] > 0 && k !== "pending" ? (
          <circle key={k} cx={C} cy={C} r={R} fill="none" stroke={CAT[k].color} strokeWidth={20}
            strokeDasharray={`${len} ${L - len}`} strokeDashoffset={-off} transform={`rotate(-90 ${C} ${C})`} />) : null;
        off += len;
        return el;
      })}
      <text x={C} y={C - 2} textAnchor="middle" fontSize="24" fontWeight="700" fill="var(--text)">{total - data.pending}</text>
      <text x={C} y={C + 15} textAnchor="middle" fontSize="10" fill="var(--muted)">de {total} validadas</text>
    </svg>
  );
}

export function Radar({ data, target }: { data: ClauseScore[]; target: number }) {
  const n = data.length, R = 110, C = 150;
  const pt = (i: number, v: number) => { const a = (Math.PI * 2 * i) / n - Math.PI / 2; return [C + Math.cos(a) * R * (v / 100), C + Math.sin(a) * R * (v / 100)]; };
  const poly = (vals: number[]) => vals.map((v, i) => pt(i, v).join(",")).join(" ");
  if (n < 3) return null;
  return (
    <svg viewBox="0 0 300 300" className="radar" role="img" aria-label="Maturidade por cláusula">
      {[25, 50, 75, 100].map(l => <polygon key={l} points={poly(data.map(() => l))} fill="none" stroke="var(--line)" />)}
      {data.map((_, i) => <line key={i} x1={C} y1={C} x2={pt(i, 100)[0]} y2={pt(i, 100)[1]} stroke="var(--line)" />)}
      <polygon points={poly(data.map(() => target))} fill="none" stroke="var(--warn)" strokeDasharray="4 3" />
      <polygon points={poly(data.map(d => d.score))} fill="var(--accent-a)" stroke="var(--accent)" strokeWidth={2} />
      {data.map((d, i) => { const [x, y] = pt(i, 118); return <text key={i} x={x} y={y} textAnchor="middle" dominantBaseline="middle" fontSize="11" fill="var(--text)">{d.clause_no}</text>; })}
    </svg>
  );
}

export function Legend({ keys }: { keys: Cat[] }) {
  return <div className="legend">{keys.map(k => <span key={k}><i style={{ background: CAT[k].color }} />{CAT[k].label}</span>)}</div>;
}

/** Barra empilhada com a contagem de respostas por categoria. */
export function Stacked({ dist }: { dist: Record<Cat, number> }) {
  const order: Cat[] = ["atende", "parcial", "nao", "na", "pending"];
  const total = order.reduce((s, k) => s + dist[k], 0) || 1;
  return (
    <div className="stack">
      {order.map(k => dist[k] > 0 && (
        <i key={k} style={{ width: `${(dist[k] / total) * 100}%`, background: CAT[k].color }} title={`${CAT[k].label}: ${dist[k]}`}>{dist[k] / total > 0.09 ? dist[k] : ""}</i>
      ))}
    </div>
  );
}
