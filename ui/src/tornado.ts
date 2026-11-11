// How sure's two what-if charts, shared by every reform (owner, 2026-11-11 23:41):
//   1. "What moves the estimate: model inputs": a one-way sensitivity tornado. Each row changes one input of the main
//      model; its bar runs from the input's low setting to its high setting (or from the pivot to the one alternative),
//      around the number the 90% range is built on. Rows are sorted by bar length, largest first.
//   2. "Other ways to estimate it": alternative methods and robustness checks, each a dot at its own total against the
//      90% range band; rows outside the range are marked.
// Which what-if goes in which chart is listed in docs/shared/HOWSURE_TORNADO_CLASSIFICATION.md. Every number comes from
// a reform's bundle; the browser only sorts, scales and draws.
import { details } from "./app";
import { esc } from "./format";
import { num, type Range90 } from "./range";

/** One setting of an input: its plain name and the reform's total over 2027–2031 at that setting. */
export interface Setting { name: string; value: number }
/** One input row. `ids` are the original what-ifs it draws (more than one when they are settings of the same input). */
export interface InputRow { ids: string[]; label: string; settings: Setting[]; note?: string }
/** One "other way" row: a single total, or its own low and high. */
export interface OtherRow { id: string; label: string; value?: number; low?: number; high?: number; group?: string; note?: string }

export interface TornadoBar { ids: string[]; label: string; low: number; high: number; lowName: string; highName: string; swing: number; note?: string }

/** Each input row as a bar around the pivot: the pivot is always inside the bar, so a single alternative gives a
 *  one-sided bar from the pivot to that value. Sorted by bar length, largest first (ties keep their order). */
export function tornadoBars(rows: InputRow[], pivot: number, pivotName: string): TornadoBar[] {
  return rows.map((r) => {
    const pts = [{ name: pivotName, value: pivot }, ...r.settings];
    const lo = pts.reduce((a, b) => (b.value < a.value ? b : a));
    const hi = pts.reduce((a, b) => (b.value > a.value ? b : a));
    return { ids: r.ids, label: r.label, low: lo.value, high: hi.value, lowName: lo.name, highName: hi.name, swing: hi.value - lo.value, note: r.note };
  }).map((b, i) => ({ b, i })).sort((x, y) => y.b.swing - x.b.swing || x.i - y.i).map((x) => x.b);
}

/** Zero-swing rows: tested, and the five-year total does not move (rounded to the nearest home). */
const moves = (b: TornadoBar) => Math.round(b.swing) !== 0;

export function tornadoHTML(o: {
  prefix: string; rows: InputRow[]; pivot: number; pivotName: string; pivotLabel: string; range: Range90; unit: string;
}): string {
  const bars = tornadoBars(o.rows, o.pivot, o.pivotName);
  const shown = bars.filter(moves), flat = bars.filter((b) => !moves(b));
  const R = o.range;
  const min = Math.min(R.low, o.pivot, ...shown.map((b) => b.low)), max = Math.max(R.high, o.pivot, ...shown.map((b) => b.high));
  const P = (x: number) => ((x - min) / (max - min || 1)) * 100;
  const ids = (b: TornadoBar) => esc(b.ids.join("|"));
  const range = (b: TornadoBar) => `${num(b.low)} to ${num(b.high)}`;
  const row = (b: TornadoBar) => `<li class="tn-row" data-whatif="${ids(b)}" data-swing="${Math.round(b.swing)}">
      <span class="tn-label">${esc(b.label)}</span>
      <span class="tn-track" aria-hidden="true"><span class="tn-band" style="left:${P(R.low)}%;width:${P(R.high) - P(R.low)}%"></span>${b.low < o.pivot ? `<span class="tn-bar tn-down" style="left:${P(b.low)}%;width:${P(o.pivot) - P(b.low)}%"></span>` : ""}${b.high > o.pivot ? `<span class="tn-bar tn-up" style="left:${P(o.pivot)}%;width:${P(b.high) - P(o.pivot)}%"></span>` : ""}<span class="tn-pivot" style="left:${P(o.pivot)}%"></span></span>
      <span class="tn-val"><span class="sr-only">${esc(b.label)}: </span>${range(b)}<span class="tn-names"> (low: ${esc(b.lowName)}; high: ${esc(b.highName)})</span></span>
    </li>`;
  const table = `<div class="table-wrap"><table class="data" data-testid="${esc(o.prefix)}-inputs-table"><caption>${esc(o.unit)}: each input at its low and high setting, largest swing first</caption>
    <thead><tr><th scope="col">Input</th><th scope="col" class="num">Low</th><th scope="col">Low setting</th><th scope="col" class="num">High</th><th scope="col">High setting</th><th scope="col" class="num">Swing</th></tr></thead>
    <tbody>${bars.map((b) => `<tr><th scope="row">${esc(b.label)}${b.note ? `<br><span class="small muted">${esc(b.note)}</span>` : ""}</th><td class="num">${num(b.low)}</td><td class="small">${esc(b.lowName)}</td><td class="num">${num(b.high)}</td><td class="small">${esc(b.highName)}</td><td class="num">${num(Math.round(b.swing))}</td></tr>`).join("")}</tbody></table></div>`;
  const notes = shown.filter((b) => b.note);
  return `<div class="tn" data-testid="${esc(o.prefix)}-inputs">
    <p class="tn-pivot-label" data-testid="${esc(o.prefix)}-pivot" data-value="${o.pivot}"><span class="tn-key tn-key-pivot" aria-hidden="true"></span>${esc(o.pivotLabel)}</p>
    <p class="small muted tn-legend"><span class="tn-key tn-key-band" aria-hidden="true"></span>Shaded: the 90% range, ${num(R.low)} to ${num(R.high)}. <span class="tn-key tn-key-down" aria-hidden="true"></span>Lowers the estimate. <span class="tn-key tn-key-up" aria-hidden="true"></span>Raises it.</p>
    ${shown.length ? `<ul class="tn-rows" aria-label="${esc(o.unit)}: ${shown.length} inputs, largest swing first">${shown.map(row).join("")}</ul>
    <p class="tn-axis small muted" aria-hidden="true"><span>${num(Math.round(min))}</span><span>${num(Math.round(max))}</span></p>` : `<p class="small">No input tested here moves the five-year total.</p>`}
    ${notes.length ? `<ul class="plain small muted tn-notes">${notes.map((b) => `<li><strong>${esc(b.label)}:</strong> ${esc(b.note!)}</li>`).join("")}</ul>` : ""}
    ${flat.length ? `<p class="small" data-testid="${esc(o.prefix)}-inputs-flat"><strong>Tested, no change to the 2027–2031 total:</strong></p><ul class="plain small tn-flat">${flat.map((b) => `<li data-whatif="${ids(b)}" data-swing="0">${esc(b.label)}${b.note ? ` <span class="muted">(${esc(b.note)})</span>` : ""}</li>`).join("")}</ul>` : ""}
    ${details("Show as a table", table)}
  </div>`;
}

export function otherWaysHTML(o: { prefix: string; rows: OtherRow[]; range: Range90; unit: string; note?: string }): string {
  const R = o.range;
  const vals = o.rows.flatMap((r) => (r.value !== undefined ? [r.value] : [r.low!, r.high!]));
  const min = Math.min(0, R.low, ...vals), max = Math.max(R.high, ...vals);
  const P = (x: number) => ((x - min) / (max - min || 1)) * 100;
  const inside = (r: OtherRow) => (r.value !== undefined ? r.value >= R.low && r.value <= R.high : r.low! >= R.low && r.high! <= R.high);
  const txt = (r: OtherRow) => (r.value !== undefined ? num(r.value) : `${num(r.low!)} to ${num(r.high!)}`);
  const row = (r: OtherRow) => `<li class="vs-row ow-row" data-whatif="${esc(r.id)}">
      <span class="vs-label">${esc(r.label)}</span>
      <span class="vs-track" aria-hidden="true"><span class="vs-band-fill" style="left:${P(R.low)}%;width:${P(R.high) - P(R.low)}%"></span><span class="vs-zero" style="left:${P(0)}%"></span>${r.value !== undefined
        ? `<span class="vs-bar" style="left:${Math.min(P(0), P(r.value))}%;width:${Math.abs(P(r.value) - P(0))}%"></span><span class="vs-dot${inside(r) ? "" : " out"}" style="left:${P(r.value)}%"></span>`
        : `<span class="vs-span${inside(r) ? "" : " out"}" style="left:${P(r.low!)}%;width:${P(r.high!) - P(r.low!)}%"></span>`}</span>
      <span class="vs-val"><span class="sr-only">${esc(r.label)}: </span>${txt(r)}${inside(r) ? "" : ` <span class="vs-out">outside<span class="sr-only"> the 90% range</span></span>`}</span>
    </li>`;
  const groups = [...new Set(o.rows.map((r) => r.group ?? ""))];
  const list = (rs: OtherRow[]) => `<ul class="vs-band ow-rows" aria-label="${esc(o.unit)}">${rs.map(row).join("")}</ul>`;
  const table = `<div class="table-wrap"><table class="data" data-testid="${esc(o.prefix)}-other-table"><caption>${esc(o.unit)}: other ways to estimate it, against the 90% range ${num(R.low)} to ${num(R.high)}</caption>
    <thead><tr><th scope="col">Other way</th><th scope="col" class="num">Total, 2027–2031</th><th scope="col">Against the 90% range</th></tr></thead>
    <tbody>${o.rows.map((r) => `<tr><th scope="row">${esc(r.label)}${r.note ? `<br><span class="small muted">${esc(r.note)}</span>` : ""}</th><td class="num">${txt(r)}</td><td>${inside(r) ? "inside" : "outside"}</td></tr>`).join("")}</tbody></table></div>`;
  return `<div class="ow" data-testid="${esc(o.prefix)}-other">
    <p class="small muted tn-legend"><span class="tn-key tn-key-band" aria-hidden="true"></span>Shaded: the 90% range, ${num(R.low)} to ${num(R.high)}. A hollow dot sits outside it. The thin line is zero.</p>
    ${groups.map((g) => `${g ? `<h3 class="ow-group">${esc(g)}</h3>` : ""}${list(o.rows.filter((r) => (r.group ?? "") === g))}`).join("")}
    <p class="tn-axis small muted" aria-hidden="true"><span>${num(Math.round(min))}</span><span>${num(Math.round(max))}</span></p>
    ${o.note ? `<p class="small muted">${esc(o.note)}</p>` : ""}
    ${details("Show as a table", table)}
  </div>`;
}

/** Both charts in one card, for the top of How sure. */
export function howSureChartsHTML(o: {
  prefix: string; unit: string; range: Range90;
  pivot: number; pivotName: string; pivotLabel: string; inputs: InputRow[]; inputsNote?: string;
  others: OtherRow[]; othersNote?: string;
}): string {
  return `<section class="card" aria-labelledby="h-${esc(o.prefix)}-inputs" data-testid="${esc(o.prefix)}-whatifs">
    <h2 id="h-${esc(o.prefix)}-inputs">What moves the estimate: model inputs</h2>
    <p>Each bar changes one input of the main model, holding everything else fixed: it runs from the estimate at the input's low setting to the estimate at its high setting, and the biggest swing is at the top.${o.inputsNote ? ` ${esc(o.inputsNote)}` : ""}</p>
    ${tornadoHTML({ prefix: o.prefix, rows: o.inputs, pivot: o.pivot, pivotName: o.pivotName, pivotLabel: o.pivotLabel, range: o.range, unit: o.unit })}
    <h2 class="tn-h2-second" id="h-${esc(o.prefix)}-other">Other ways to estimate it</h2>
    <p>Each row is a different method or a robustness check, with its own total drawn against the 90% range; none of them changes the range.</p>
    ${otherWaysHTML({ prefix: o.prefix, rows: o.others, range: o.range, unit: o.unit, note: o.othersNote })}
  </section>`;
}
