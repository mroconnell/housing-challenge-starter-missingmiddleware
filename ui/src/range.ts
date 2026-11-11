// The uniform range display (docs/UNIFORM_DISPLAY_SPEC.md): one 90% range per reform with its low and high ends
// labelled, no centre line, and side lines drawn across it as reasons to believe. Shared by the ADU and TOD screens.
// Every number comes from a reform's bundle; the browser only scales, formats and draws.
import { legendHTML, xyChart, type ChartMode, type Pt, type Series } from "./charts";
import { esc, int } from "./format";

export interface RangeYear { year: number; low: number; high: number }
export interface Range90 {
  low: number; high: number; unit: string; method: string; coverage: string; caveat?: string; source: string;
  years: RangeYear[]; years_method?: string;
}
export interface SideLine { id: string; label: string; value?: number; low?: number; high?: number; note: string; where: "chart" | "howsure"; source?: string }

/** The shared all-housing baseline (v4) central total for Wisconsin, 2027–2031: every reform's range ends are given
 *  as shares of it (spec rule 7). The ADU bundle does not carry it, so it is kept here and tested against
 *  reference/housing_baseline_statewide_by_year.csv (tests/test_uniform_range.py) and the TOD bundle. */
export const ALL_HOUSING_BASELINE_2027_2031 = 124000;

export const BAND_COLOR = "#17644f";
export const CURRENT_LAW_COLOR = "#4b5450";
// Side lines: thin, each with its own colour and dash so the legend can tell them apart.
const SIDE_STYLE: { color: string; dash?: string }[] = [
  { color: "#2f6db5" }, { color: "#7b3fb0", dash: "6 3" }, { color: "#b0501a", dash: "2 3" },
  { color: "#8a5300", dash: "9 3 2 3" }, { color: "#0e7c86", dash: "4 4" }, { color: "#a3285a", dash: "1 3" },
];
export const sideStyle = (i: number) => SIDE_STYLE[i % SIDE_STYLE.length];

/** A share with one decimal: "6.5%", "−37.0%". */
export function share1(v: number): string {
  const p = v * 100;
  return `${p < 0 ? "−" : ""}${Math.abs(p).toFixed(1)}%`;
}
/** A signed whole number with a true minus sign. */
export function num(v: number): string {
  return v < 0 ? `−${int(-v)}` : int(v);
}
/** A side line's number: one value, or its own low to high. */
export function sideValue(s: SideLine): string {
  return s.value !== undefined ? num(s.value) : `${num(s.low!)} to ${num(s.high!)}`;
}

/** A "Read with care" note for a range's caveat, for screens that show it beside the side lines rather than in the card. */
export function rangeCaveatHTML(R: Range90): string {
  return R.caveat ? `<div class="note-box" role="note" data-testid="range-caveat"><p><strong>Read with care.</strong> ${esc(R.caveat)}</p></div>` : "";
}

/** The headline range card: low and high ends labelled, unit, shares of the all-housing baseline, method and coverage
 *  lines, and an optional caveat and scope note. */
export function rangeCardHTML(o: { title: string; range: Range90; baselineTotal: number; scopeNote?: string; testid?: string; headingLevel?: 2 | 3; caveatInCard?: boolean }): string {
  const R = o.range, h = o.headingLevel ?? 2, id = `${o.testid ?? "range"}-h`;
  const shareOf = (v: number) => `${share1(v / o.baselineTotal)} of the ${int(o.baselineTotal)} homes of all kinds Wisconsin is expected to permit under current law, 2027–2031`;
  return `<section class="card range-card" aria-labelledby="${id}" data-testid="${esc(o.testid ?? "range-card")}">
    <h${h} id="${id}">${esc(o.title)}</h${h}>
    <p class="range-ends"><span class="range-end"><span class="range-end-label">Low end</span><span class="range-end-num" data-testid="range-low">${num(R.low)}</span></span>
      <span class="range-to" aria-hidden="true">to</span>
      <span class="range-end"><span class="range-end-label">High end</span><span class="range-end-num" data-testid="range-high">${num(R.high)}</span></span></p>
    <p class="range-unit" data-testid="range-unit">${esc(R.unit)} (90% range)</p>
    ${o.scopeNote ? `<p class="small"><strong>${esc(o.scopeNote)}</strong></p>` : ""}
    <ul class="plain small range-shares" data-testid="range-shares">
      <li>Low end: ${shareOf(R.low)}.</li>
      <li>High end: ${shareOf(R.high)}.</li>
    </ul>
    <p class="small" data-testid="range-method"><strong>How the range is built.</strong> ${esc(R.method)}</p>
    <p class="small" data-testid="range-coverage"><strong>Coverage check.</strong> ${esc(R.coverage)}</p>
    ${R.caveat && o.caveatInCard !== false ? `<div class="note-box" role="note" data-testid="range-caveat"><p><strong>Read with care.</strong> ${esc(R.caveat)}</p></div>` : ""}
  </section>`;
}

/** The side lines as a short list, one sentence each. */
export function sideLinesHTML(lines: SideLine[], unitShort: string, testid = "side-lines", intro = ""): string {
  return `<div data-testid="${esc(testid)}">${intro ? `<p class="small muted">${esc(intro)}</p>` : ""}<ul class="plain side-lines">${lines.map((s, i) => {
    const st = sideStyle(i);
    return `<li data-side="${esc(s.id)}"><svg width="28" height="12" aria-hidden="true" focusable="false"><line x1="0" x2="28" y1="6" y2="6" stroke="${st.color}" stroke-width="2" ${st.dash ? `stroke-dasharray="${st.dash}"` : ""}/></svg> <strong>${esc(s.label)}:</strong> ${sideValue(s)} ${esc(unitShort)}. ${esc(s.note)}</li>`;
  }).join("")}</ul></div>`;
}

/** Each year's fixed share of the five-year range (the range's yearly profile). */
export function yearShares(R: Range90): number[] {
  return R.years.map((y) => y.low / R.low);
}

/** The yearly chart: the shaded 90% band, the grey current-law band (totals view only) and thin side lines, each
 *  spread over the years by the range's own yearly profile. No centre line. In the extra-homes view current law is
 *  the zero line. `f` converts a count (e.g. to a rate per 1,000 homes). Returns the legend HTML. */
export function drawRangeChart(container: HTMLElement, o: {
  mode: ChartMode; range: Range90; sideLines: SideLine[];
  base: { years: number[]; central: number[]; low: number[]; high: number[]; prior?: { year: number; value: number } };
  title: string; yLabel: string; noun: string; f?: (v: number) => number; yFormat?: (y: number) => string;
  vline?: { x: number; label: string }; xTicks?: number[];
}): string {
  const f = o.f ?? ((v: number) => v);
  const R = o.range, sh = yearShares(R), yrs = R.years.map((y) => y.year);
  const extra = o.mode === "extra";
  const add = (i: number) => (extra ? 0 : o.base.central[i]);
  const pts = (vals: number[]): Pt[] => yrs.map((x, i) => ({ x, y: f(vals[i]) }));
  const bands = [
    ...(extra ? [] : [{ name: "current-law", lo: pts(o.base.low), hi: pts(o.base.high), color: CURRENT_LAW_COLOR, opacity: 0.14 }]),
    { name: "range90", lo: pts(R.years.map((y, i) => add(i) + y.low)), hi: pts(R.years.map((y, i) => add(i) + y.high)), color: BAND_COLOR, opacity: 0.28 },
  ];
  const prior = o.base.prior && !extra ? [{ x: o.base.prior.year, y: f(o.base.prior.value) }] : [];
  const zeroXs = o.base.prior ? [o.base.prior.year, ...yrs] : yrs;
  const series: Series[] = [
    { id: "current-law", name: "Current law", color: CURRENT_LAW_COLOR, dash: "7 5", width: 2,
      values: extra ? zeroXs.map((x) => ({ x, y: 0 })) : [...prior, ...pts(o.base.central)] },
    ...o.sideLines.filter((s) => s.value !== undefined).map((s, i) => ({
      id: `side-${s.id}`, name: s.label, color: sideStyle(i).color, dash: sideStyle(i).dash, width: 1.5,
      values: yrs.map((x, k) => ({ x, y: f(add(k) + s.value! * sh[k]) })),
    })),
  ];
  const sum = (xs: number[]) => xs.reduce((a, b) => a + b, 0);
  xyChart(container, {
    title: o.title,
    desc: `${extra ? `Current law is the zero line. ` : `Current law: ${int(sum(o.base.central))} ${o.noun} over 2027–2031 (range ${int(sum(o.base.low))} to ${int(sum(o.base.high))}), shaded grey. `}`
      + `The law's 90% range, shaded green: ${num(R.low)} to ${num(R.high)} extra ${o.noun} over 2027–2031${extra ? "" : ", on top of current law"}. `
      + `Side lines over 2027–2031: ${o.sideLines.filter((s) => s.value !== undefined).map((s) => `${s.label} ${num(s.value!)}`).join("; ")}. No centre line is drawn. The table below has the yearly values.`,
    yLabel: o.yLabel, xTicks: o.xTicks ?? yrs, xPad: 0.4, yFormat: o.yFormat, vline: o.vline,
    bands, series,
  });
  return legendHTML([
    ...(extra ? [{ name: "Current law: the zero line", color: CURRENT_LAW_COLOR, dash: "7 5" }] : [
      { name: "Current law (range shaded grey)", color: CURRENT_LAW_COLOR, dash: "7 5" },
    ]),
    { name: `With the law: 90% range, ${num(R.low)} to ${num(R.high)} extra ${o.noun}, 2027–2031${extra ? "" : " (on top of current law)"}`, color: BAND_COLOR, kind: "band" as const },
    ...o.sideLines.filter((s) => s.value !== undefined).map((s, i) => ({ name: `${s.label}: ${num(s.value!)} over 2027–2031`, color: sideStyle(i).color, dash: sideStyle(i).dash, width: 1.5 })),
  ]);
}

/** What-if totals drawn against the 90% range band: each row is a dot at the what-if's own five-year total on one
 *  shared axis, with the band shaded behind every row. Rows outside the band are marked. */
export function againstBandHTML(rows: { label: string; value: number }[], R: Range90, unit: string, testid: string, scale?: { min: number; max: number }): string {
  const lo = Math.min(0, R.low, ...rows.map((r) => r.value)), hi = Math.max(R.high, ...rows.map((r) => r.value));
  const min = scale?.min ?? lo, max = scale?.max ?? hi;
  const P = (x: number) => ((x - min) / (max - min || 1)) * 100;
  const inside = (v: number) => v >= R.low && v <= R.high;
  const name = `${unit}. The 90% range, ${num(R.low)} to ${num(R.high)}, is shaded. ` + rows.map((r) => `${r.label}: ${num(r.value)}${inside(r.value) ? "" : " (outside the range)"}`).join("; ");
  const label = name.length <= 800 ? name : `${unit}, ${rows.length} what-ifs against the 90% range ${num(R.low)} to ${num(R.high)}; every value is in the table below.`;
  return `<div class="vs-band" role="img" aria-label="${esc(label)}" data-testid="${esc(testid)}">${rows.map((r) => `<div class="vs-row" aria-hidden="true"><span class="vs-label">${esc(r.label)}</span><span class="vs-track"><span class="vs-band-fill" style="left:${P(R.low)}%;width:${P(R.high) - P(R.low)}%"></span><span class="vs-zero" style="left:${P(0)}%"></span><span class="vs-bar" style="left:${Math.min(P(0), P(r.value))}%;width:${Math.abs(P(r.value) - P(0))}%"></span><span class="vs-dot${inside(r.value) ? "" : " out"}" style="left:${P(r.value)}%"></span></span><span class="vs-val">${num(r.value)}${inside(r.value) ? "" : " <span class=\"vs-out\">outside</span>"}</span></div>`).join("")}</div>`;
}
export function againstBandScale(R: Range90, values: number[]): { min: number; max: number } {
  return { min: Math.min(0, R.low, ...values), max: Math.max(R.high, ...values) };
}
