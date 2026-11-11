// The middle housing reform (2–6 homes per lot): screens over the bundle written by scripts/build_middle_bundle.py.
// The browser only selects, sums and formats bundle values.
import { ALL_HOUSING_BASELINE_2027_2031, againstBandHTML, num, rangeCardHTML, sideLinesHTML, type Range90, type SideLine } from "../../range";
import { esc, int } from "../../format";
import { loadWiHomes, renderSummary, type SummaryInput, type WiHomes } from "../../summary";
import type { MountedReform, ReformEntry, ReformModule, Route, ShellEnv } from "../types";

/** The modeled law, shown on Why and in the Summary's policy box. */
export const MIDDLE_LAW_TEXT = "From 1 January 2027 (illustrative), any lot now limited to one home could have 2–6 homes, up to 3 stories, without special approval. Setbacks and lot coverage are assumed not to block them.";

// ---- bundle types --------------------------------------------------------------------------
interface Range { lower: number; central: number; upper: number }
interface YearRange extends Range { year: number }
interface Side extends Range { id: string; label: string; caveat: string; by_year: YearRange[] }
interface Extra extends Range { id: string; label: string; info: string; share_band_central?: { low: number; high: number; portland_check: number } }
interface Statewide {
  headline: string;
  core: Range & { label: string; by_year: YearRange[]; split: Record<"2_unit" | "3_4_unit", Range>; rate_per_1000_sf_homes: Range };
  timing: { label: string; toggle_off_label: string; flat: Range; note: string };
  side_measures: Side[]; extra_lines: Extra[];
  range90: Range90; range90_flat: Range90; side_lines: SideLine[]; baseline_by_year: { central: number[]; low: number[]; high: number[] };
  baseline: { version: string; total: number; low_total: number; high_total: number };
}
interface Area extends Range { area_id: string; name: string; sf_homes: number }
interface HowSure { bars: { id: string; label: string; central?: number; low?: number; high?: number; note?: string }[]; notes: string[] }
interface Why { evidence: { label: string; url: string }[]; cannot_tell: string[] }
interface Manifest { run_id: string; outcome: { short: string; rate_units: string }; dates: { last_observed_year: number }; repo_url: string }
export interface MiddleBundle { manifest: Manifest; statewide: Statewide; areas: Area[]; howsure: HowSure; why: Why; homes: WiHomes }

async function load(entry: ReformEntry): Promise<MiddleBundle> {
  const root = `${import.meta.env.BASE_URL}${entry.bundle_root}`;
  const get = async (p: string) => { const r = await fetch(p); if (!r.ok) throw new Error(`${p}: ${r.status}`); return r.json(); };
  const { run_id } = await get(`${root}latest.json`);
  const dir = `${root}${run_id}/`;
  const [[manifest, statewide, areas, howsure, why], homes] = await Promise.all([Promise.all(
    ["manifest", "statewide", "areas", "howsure", "why"].map((f) => get(`${dir}${f}.json`))), loadWiHomes()]);
  return { manifest, statewide, areas, howsure, why, homes };
}

// ---- helpers ----------------------------------------------------------------------------------

// The same tabs, in the same order, for every reform (owner, 2026-11-11); middle housing has no pilots or brief yet.
const ROUTES: Route[] = [
  { path: "/summary", label: "Summary", n: 1 },
  { path: "/where", label: "Where", n: 2 },
  { path: "/how-sure", label: "How sure", n: 3 },
  { path: "/why", label: "Why", n: 4 },
];

// ---- screens --------------------------------------------------------------------------------
/** The Summary: the shared component. The all-building-sizes line is far above this scale, so it is listed, not drawn. */
function summaryInput(b: MiddleBundle): SummaryInput {
  const s = b.statewide;
  const all = s.side_lines.find((l) => l.id === "all" && l.where === "chart");
  return {
    id: "middle", title: "Missing middle housing", law: "allows 2–6 homes on every lot now limited to one home", modeled: [MIDDLE_LAW_TEXT], unit: "homes in 2–4 unit buildings", chartName: "Homes in 2–4 unit buildings",
    range: s.range90, rangeFlat: s.range90_flat, sideLines: s.side_lines.filter((l) => l.where === "chart" && l.id !== "all"),
    notDrawn: all ? `Not drawn: "${all.label}" (${num(all.value ?? 0)} over 2027–2031), far above this scale; it is on How sure.` : undefined,
    base: s.baseline_by_year, baseName: "homes of all kinds permitted under current law", homes: b.homes,
  };
}

/** The former Statewide comparison, now How sure's Details: the range card, both timings, the yearly table and the side lines. */
function details(b: MiddleBundle): string {
  const s = b.statewide, R = s.range90, F = s.range90_flat;
  const chartLines = s.side_lines.filter((l) => l.where === "chart");
  const row = (y: { year: number; low: number; high: number }) => `<td class="num">${num(Math.min(y.low, y.high))}</td><td class="num">${num(Math.max(y.low, y.high))}</td>`;
  return `
  <h2 class="section-h" id="h-details" data-testid="details">Details</h2>
  <p data-testid="mid-headline">${esc(s.headline)}</p>
  ${rangeCardHTML({ title: "Homes in 2–4 unit buildings, 2027–2031", range: R, baselineTotal: ALL_HOUSING_BASELINE_2027_2031, testid: "range-card", headingLevel: 3 })}
  <section class="card" aria-labelledby="h-mid-timing"><h3 id="h-mid-timing">Timing</h3>
    <p>${esc(s.timing.label)}: ${num(R.low)} to ${num(R.high)}. ${esc(s.timing.toggle_off_label)}: <span data-testid="flat-range">${num(F.low)} to ${num(F.high)}</span> extra homes in 2–4 unit buildings over 2027–2031 (90% range).</p>
    <p class="small muted">${esc(s.timing.note)}</p></section>
  <section class="card" aria-labelledby="h-mid-years"><h3 id="h-mid-years">Extra 2–4 unit homes each year</h3>
    <div class="table-wrap"><table class="data" data-testid="compare-table"><caption>Extra homes in 2–4 unit buildings by year, 90% range, with each timing</caption>
      <thead><tr><th scope="col">Year</th><th scope="col" class="num">${esc(s.timing.label)}: low end</th><th scope="col" class="num">${esc(s.timing.label)}: high end</th><th scope="col" class="num">${esc(s.timing.toggle_off_label)}: low end</th><th scope="col" class="num">${esc(s.timing.toggle_off_label)}: high end</th></tr></thead>
      <tbody>${R.years.map((y, i) => `<tr><th scope="row">${y.year}</th>${row(y)}${row(F.years[i])}</tr>`).join("")}
      <tr><th scope="row">2027–2031</th><td class="num" data-testid="table-range-low">${num(R.low)}</td><td class="num" data-testid="table-range-high">${num(R.high)}</td><td class="num">${num(F.low)}</td><td class="num">${num(F.high)}</td></tr></tbody></table></div>
    <p class="small muted">${esc(R.years_method ?? "")} Yearly rows may not add exactly to the totals because of rounding.</p></section>
  <section class="card" aria-labelledby="h-mid-side"><h3 id="h-mid-side">Side lines</h3>${sideLinesHTML(chartLines, "extra homes, 2027–2031", "side-lines", "All but the last are drawn on the Summary chart; the all-building-sizes line is far above its scale. None changes the 90% range.")}</section>`;
}

function where(b: MiddleBundle, main: HTMLElement): void {
  const top = [...b.areas].sort((a, c) => c.sf_homes - a.sf_homes).slice(0, 25);
  main.innerHTML = `
  <h1>Where the extra homes would be</h1>
  <p class="lede">Every place gets the same measured rate per single-family home, so each place's range is the statewide 90% range times its share of Wisconsin's single-family homes. Nothing here is measured place by place.</p>
  <section class="card"><h2>25 places with the most single-family homes</h2><div class="table-wrap"><table class="data">
    <caption class="sr-only">Extra 2–4 unit homes, 2027–2031, 90% range, by place</caption>
    <thead><tr><th scope="col">Place</th><th scope="col" class="num">Single-family homes</th><th scope="col" class="num">Low end</th><th scope="col" class="num">High end</th></tr></thead>
    <tbody>${top.map((a) => `<tr><th scope="row">${esc(a.name)}</th><td class="num">${int(a.sf_homes)}</td><td class="num">${num(a.lower)}</td><td class="num">${num(a.upper)}</td></tr>`).join("")}</tbody></table></div>
    <p class="small muted">${b.areas.length.toLocaleString("en-US")} places in all. Single-family homes from ACS 2020–2024 (detached and attached).</p></section>`;
}

function howSure(b: MiddleBundle, main: HTMLElement): void {
  const s = b.statewide, R = s.range90;
  const rows = b.howsure.bars.filter((x) => x.central !== undefined).map((x) => ({ label: x.label, value: x.central! }));
  const hs = s.side_lines.filter((l) => l.where === "howsure");
  main.innerHTML = `
  <h1>How sure we are</h1>
  <p class="lede">90% range for 2–4 unit homes: ${num(R.low)} to ${num(R.high)} extra homes over 2027–2031. ${esc(R.coverage)}</p>
  <section class="card"><h2>What-ifs against the range</h2>
    ${againstBandHTML(rows, R, "Extra homes, 2027–2031", "mid-vs-band")}
    <div class="table-wrap"><table class="data"><caption class="sr-only">What-ifs and their five-year totals</caption>
    <thead><tr><th scope="col">What-if</th><th scope="col" class="num">Extra homes, 2027–2031</th></tr></thead>
    <tbody>${b.howsure.bars.map((x) => `<tr><th scope="row">${esc(x.label)}${x.note ? `<br><span class="small muted">${esc(x.note)}</span>` : ""}</th><td class="num">${x.central !== undefined ? num(x.central) : `${num(x.low!)} to ${num(x.high!)}`}</td></tr>`).join("")}</tbody></table></div></section>
  <section class="card"><h2>Possibilities beyond what was measured</h2>${sideLinesHTML(hs, "extra homes, 2027–2031", "howsure-lines")}</section>
  <section class="card"><h2>Notes</h2><ul class="plain">${b.howsure.notes.map((n) => `<li>${esc(n)}</li>`).join("")}</ul></section>
  ${details(b)}`;
}

function why(b: MiddleBundle, main: HTMLElement): void {
  main.innerHTML = `
  <h1>Why these numbers</h1>
  <p class="law" data-testid="law-text"><strong>The law.</strong> ${esc(MIDDLE_LAW_TEXT)}</p>
  <section class="card"><h2>How it works</h2><p>Four states (Oregon, California, Maine and Vermont) passed laws allowing 2–4 homes on single-family lots. We compared their permits for 2–4 unit buildings, per 1,000 single-family homes, with similar places in the same regions, before and after each law. That gap is applied to Wisconsin.</p></section>
  <section class="card"><h2>What it cannot tell you</h2><ul class="plain">${b.why.cannot_tell.map((c) => `<li>${esc(c)}</li>`).join("")}</ul></section>
  <section class="card"><h2>Evidence</h2><ul class="plain">${b.why.evidence.map((d) => `<li><a href="${esc(d.url)}" target="_blank" rel="noopener">${esc(d.label)}<span class="sr-only"> (opens GitHub in a new tab)</span> ↗</a></li>`).join("")}</ul></section>`;
}

// ---- module -----------------------------------------------------------------------------------
function mount(env: ShellEnv, data: unknown): MountedReform {
  const b = data as MiddleBundle;
  const m = b.manifest;
  return {
    routes: ROUTES,
    defaultPath: "/summary",
    titleSuffix: "Wisconsin middle housing law",
    statusStrip: `<span>Run <code data-testid="run-id">${esc(m.run_id)}</code></span><span>Last observed year ${m.dates.last_observed_year}</span><span>Forecast 2027–2031</span><span>Law in effect 1 Jan 2027 (illustrative)</span>`,
    footer: `<p><strong>Outcome:</strong> ${esc(m.outcome.short)}</p>
      <p class="pill-key"><span class="pill pill-observed">Observed</span> counted in a published source. <span class="pill pill-calculated">Calculated</span> computed from observed inputs and stated rules. <span class="pill pill-assumed">Assumed</span> a judgment where no data decide it.</p>
      <p class="muted">Run <code>${esc(m.run_id)}</code> · <a href="${esc(m.repo_url)}" target="_blank" rel="noopener">Source code and documentation<span class="sr-only"> (opens GitHub in a new tab)</span> ↗</a> · Apache-2.0</p>`,
    extra: "",
    bind() { /* nothing to bind */ },
    render(path: string, params: URLSearchParams, main: HTMLElement) {
      if (path.startsWith("/where")) where(b, main);
      else if (path.startsWith("/how-sure")) howSure(b, main);
      else if (path.startsWith("/why")) why(b, main);
      else renderSummary(main, summaryInput(b), env, params);
    },
  };
}

export const middleReform: ReformModule = { load, mount };
