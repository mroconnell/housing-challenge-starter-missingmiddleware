// Small dependency-free SVG/HTML charts. Each chart is drawn at its container's width, carries a
// <title>/<desc> text summary, and is always paired with a data table by the caller.
import { esc } from "./format";

export interface Pt { x: number; y: number | null }
export interface Series {
  name: string; values: Pt[]; color: string; dash?: string; width?: number; opacity?: number; marker?: "circle" | "square";
  legend?: boolean;
}
export interface BarSeries { name: string; values: (Pt & { hatch?: boolean })[]; color: string }
export interface ChartSpec {
  title: string; desc: string; yLabel: string; xTicks: number[]; xFormat?: (x: number) => string;
  series: Series[]; band?: { name: string; lo: Pt[]; hi: Pt[]; color: string }; bars?: BarSeries;
  vline?: { x: number; label: string }; height?: number;
  /** Short text labels placed at data points (e.g. "provisional, partial year"). */
  notes?: { x: number; y: number; text: string; anchor?: "start" | "middle" | "end"; dy?: number }[]; yMax?: number; yFormat?: (y: number) => string; xPad?: number;
}

let uid = 0;

function niceMax(v: number): number {
  if (v <= 0) return 1;
  const p = Math.pow(10, Math.floor(Math.log10(v)));
  for (const m of [1, 1.2, 1.5, 2, 2.5, 3, 4, 5, 6, 8, 10]) if (m * p >= v) return m * p;
  return 10 * p;
}

export function legendHTML(items: { name: string; color: string; dash?: string; kind?: "line" | "band" | "bar" | "hatch"; width?: number }[]): string {
  return `<ul class="legend" aria-label="Chart key">${items.map((it) => {
    const pid = `hatch-legend-${++uid}`; // unique per swatch: ids must not repeat on a page
    let sw = "";
    if (it.kind === "band") sw = `<rect x="0" y="2" width="28" height="10" fill="${it.color}" opacity="0.25"/>`;
    else if (it.kind === "bar") sw = `<rect x="6" y="1" width="14" height="12" fill="${it.color}"/>`;
    else if (it.kind === "hatch") sw = `<rect x="6" y="1" width="14" height="12" fill="url(#${pid})" stroke="${it.color}"/>`;
    else sw = `<line x1="0" x2="28" y1="7" y2="7" stroke="${it.color}" stroke-width="${it.width ?? 2.5}" ${it.dash ? `stroke-dasharray="${it.dash}"` : ""}/>`;
    return `<li><svg width="28" height="14" aria-hidden="true" focusable="false"><defs><pattern id="${pid}" width="4" height="4" patternUnits="userSpaceOnUse" patternTransform="rotate(45)"><line x1="0" y1="0" x2="0" y2="4" stroke="${it.color}" stroke-width="1.5"/></pattern></defs>${sw}</svg>${esc(it.name)}</li>`;
  }).join("")}</ul>`;
}

export function xyChart(container: HTMLElement, spec: ChartSpec): void {
  const draw = () => {
    const W = Math.max(280, container.clientWidth || 640);
    const H = spec.height ?? (W < 500 ? 260 : 320);
    const m = { t: 16, r: W < 500 ? 12 : 24, b: 36, l: W < 500 ? 60 : 66 };
    const xs = spec.xTicks;
    const pad = spec.xPad ?? 0.5;
    const x0 = Math.min(...xs) - pad, x1 = Math.max(...xs) + pad;
    let ymax = spec.yMax ?? 0;
    if (!spec.yMax) {
      for (const s of spec.series) for (const p of s.values) if (p.y !== null) ymax = Math.max(ymax, p.y);
      if (spec.band) for (const p of spec.band.hi) if (p.y !== null) ymax = Math.max(ymax, p.y);
      if (spec.bars) for (const p of spec.bars.values) if (p.y !== null) ymax = Math.max(ymax, p.y);
      ymax = niceMax(ymax * (spec.notes?.length ? 1.2 : 1.05));
    }
    const stepRaw = ymax / 4, pw = Math.pow(10, Math.floor(Math.log10(stepRaw)));
    const ystep = [1, 2, 2.5, 5, 10].map((m) => m * pw).find((s) => s >= stepRaw - 1e-12)!;
    ymax = Math.ceil(ymax / ystep - 1e-9) * ystep;
    const X = (x: number) => m.l + ((x - x0) / (x1 - x0)) * (W - m.l - m.r);
    const Y = (y: number) => H - m.b - (y / ymax) * (H - m.t - m.b);
    const yf = spec.yFormat ?? ((y: number) => y.toLocaleString("en-US"));
    const xf = spec.xFormat ?? ((x: number) => String(x));
    const id = `c${++uid}`;
    const parts: string[] = [];
    // grid + y axis
    for (let i = 0; i <= Math.round(ymax / ystep); i++) {
      const v = i * ystep;
      parts.push(`<line x1="${m.l}" x2="${W - m.r}" y1="${Y(v)}" y2="${Y(v)}" class="grid"/>`);
      parts.push(`<text x="${m.l - 6}" y="${Y(v) + 4}" text-anchor="end" class="tick">${esc(yf(v))}</text>`);
    }
    const step = W < 420 && xs.length > 8 ? 2 : 1;
    xs.forEach((x, i) => {
      if (i % step === 0 || i === xs.length - 1) parts.push(`<text x="${X(x)}" y="${H - m.b + 18}" text-anchor="middle" class="tick">${esc(xf(x))}</text>`);
    });
    parts.push(`<line x1="${m.l}" x2="${W - m.r}" y1="${Y(0)}" y2="${Y(0)}" class="axis"/>`);
    if (spec.vline) {
      const vx = X(spec.vline.x);
      parts.push(`<line x1="${vx}" x2="${vx}" y1="${m.t}" y2="${H - m.b}" class="vline"/>`);
      parts.push(`<text x="${vx + 4}" y="${m.t + 10}" class="vlabel">${esc(spec.vline.label)}</text>`);
    }
    if (spec.bars) {
      const bw = Math.max(4, ((W - m.l - m.r) / (x1 - x0)) * 0.6);
      parts.push(`<defs><pattern id="${id}-h" width="5" height="5" patternUnits="userSpaceOnUse" patternTransform="rotate(45)"><line x1="0" y1="0" x2="0" y2="5" stroke="${spec.bars.color}" stroke-width="2"/></pattern></defs>`);
      for (const p of spec.bars.values) {
        if (p.y === null) {
          parts.push(`<text x="${X(p.x)}" y="${Y(0) - 4}" text-anchor="middle" class="tick">—</text>`);
          continue;
        }
        const top = Y(p.y);
        parts.push(`<rect x="${X(p.x) - bw / 2}" y="${top}" width="${bw}" height="${Math.max(0, Y(0) - top)}" fill="${p.hatch ? `url(#${id}-h)` : spec.bars.color}" stroke="${spec.bars.color}"/>`);
      }
    }
    if (spec.band) {
      const lo = spec.band.lo.filter((p) => p.y !== null), hi = spec.band.hi.filter((p) => p.y !== null);
      const d = hi.map((p, i) => `${i ? "L" : "M"}${X(p.x)},${Y(p.y!)}`).join("") + lo.slice().reverse().map((p) => `L${X(p.x)},${Y(p.y!)}`).join("") + "Z";
      parts.push(`<path d="${d}" fill="${spec.band.color}" opacity="0.16"/>`);
    }
    for (const s of spec.series) {
      const segs: string[] = [];
      let pen = false;
      for (const p of s.values) {
        if (p.y === null) { pen = false; continue; }
        segs.push(`${pen ? "L" : "M"}${X(p.x).toFixed(1)},${Y(p.y).toFixed(1)}`);
        pen = true;
      }
      parts.push(`<path d="${segs.join("")}" fill="none" stroke="${s.color}" stroke-width="${s.width ?? 2.5}" ${s.dash ? `stroke-dasharray="${s.dash}"` : ""} opacity="${s.opacity ?? 1}" stroke-linejoin="round" stroke-linecap="round"/>`);
      if (s.marker) for (const p of s.values) if (p.y !== null)
        parts.push(s.marker === "square"
          ? `<rect x="${X(p.x) - 3.5}" y="${Y(p.y) - 3.5}" width="7" height="7" fill="${s.color}" opacity="${s.opacity ?? 1}"/>`
          : `<circle cx="${X(p.x)}" cy="${Y(p.y)}" r="3.2" fill="${s.color}" opacity="${s.opacity ?? 1}"/>`);
    }
    for (const n of spec.notes ?? []) {
      const nx = X(n.x), ny = Y(n.y) + (n.dy ?? -8);
      const anchor = n.anchor ?? "middle";
      n.text.split("\n").forEach((line, i, all) =>
        parts.push(`<text x="${nx}" y="${ny - (all.length - 1 - i) * 13}" text-anchor="${anchor}" class="anno">${esc(line)}</text>`));
    }
    parts.push(`<text x="${12}" y="${(H - m.b + m.t) / 2}" transform="rotate(-90 12 ${(H - m.b + m.t) / 2})" text-anchor="middle" class="ylabel">${esc(spec.yLabel)}</text>`);
    container.innerHTML = `<svg width="${W}" height="${H}" viewBox="0 0 ${W} ${H}" role="img" aria-labelledby="${id}-t ${id}-d" class="chart"><title id="${id}-t">${esc(spec.title)}</title><desc id="${id}-d">${esc(spec.desc)}</desc>${parts.join("")}</svg>`;
  };
  draw();
  let last = container.clientWidth;
  const ro = new ResizeObserver(() => {
    if (Math.abs(container.clientWidth - last) > 8) { last = container.clientWidth; draw(); }
  });
  ro.observe(container);
}

/** Diverging horizontal bars in HTML (wraps labels on small screens). */
export function tornadoHTML(rows: { label: string; value: number; note?: string }[], unit: string): string {
  const max = Math.max(...rows.map((r) => Math.abs(r.value)), 1);
  return `<div class="tornado" role="img" aria-label="${esc(`Change from the central scenario, ${unit}. ` + rows.map((r) => `${r.label}: ${r.value > 0 ? "+" : ""}${Math.round(r.value).toLocaleString("en-US")}`).join("; "))}">${rows.map((r) => {
    const w = (Math.abs(r.value) / max) * 50;
    const neg = r.value < 0;
    return `<div class="t-row" aria-hidden="true"><div class="t-label">${esc(r.label)}</div><div class="t-track"><div class="t-mid"></div><div class="t-bar ${neg ? "neg" : "pos"}" style="${neg ? `right:50%` : `left:50%`};width:${w}%"></div></div><div class="t-val">${r.value > 0 ? "+" : r.value < 0 ? "−" : ""}${Math.abs(Math.round(r.value)).toLocaleString("en-US")}</div></div>`;
  }).join("")}</div>`;
}

/** 100% stacked bar in HTML. */
export function stackHTML(parts: { label: string; value: number; cls: string }[], aria: string): string {
  const tot = parts.reduce((a, p) => a + p.value, 0) || 1;
  return `<div class="stack" role="img" aria-label="${esc(aria)}">${parts.map((p) => `<div class="stack-seg ${p.cls}" style="width:${(p.value / tot) * 100}%" title="${esc(p.label)}"><span>${Math.round((p.value / tot) * 100)}%</span></div>`).join("")}</div>`;
}
