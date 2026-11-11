// The middle housing reform (2–6 homes per lot): screens over the bundle written by scripts/build_middle_bundle.py.
// The browser only selects, sums and formats bundle values.
import { ALL_HOUSING_BASELINE_2027_2031, againstBandHTML, drawRangeChart, num, rangeCardHTML, sideLinesHTML, type Range90, type SideLine } from "../../range";
import { esc, int, YEARS } from "../../format";
import type { MountedReform, ReformEntry, ReformModule, Route, ShellEnv } from "../types";

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
export interface MiddleBundle { manifest: Manifest; statewide: Statewide; areas: Area[]; howsure: HowSure; why: Why }

async function load(entry: ReformEntry): Promise<MiddleBundle> {
  const root = `${import.meta.env.BASE_URL}${entry.bundle_root}`;
  const get = async (p: string) => { const r = await fetch(p); if (!r.ok) throw new Error(`${p}: ${r.status}`); return r.json(); };
  const { run_id } = await get(`${root}latest.json`);
  const dir = `${root}${run_id}/`;
  const [manifest, statewide, areas, howsure, why] = await Promise.all(
    ["manifest", "statewide", "areas", "howsure", "why"].map((f) => get(`${dir}${f}.json`)));
  return { manifest, statewide, areas, howsure, why };
}

// ---- helpers ----------------------------------------------------------------------------------

const ROUTES: Route[] = [
  { path: "/compare", label: "Statewide comparison", n: 1 },
  { path: "/where", label: "Where", n: 2 },
  { path: "/how-sure", label: "How sure", n: 3 },
  { path: "/why", label: "Why", n: 4 },
];

// ---- screens --------------------------------------------------------------------------------
function compare(b: MiddleBundle, env: ShellEnv, params: URLSearchParams, main: HTMLElement): void {
  const s = b.statewide, flat = params.get("timing") === "flat";
  const R = flat ? s.range90_flat : s.range90;
  const chartLines = s.side_lines.filter((l) => l.where === "chart");
  main.innerHTML = `
  <h1>Middle housing: extra homes over five years</h1>
  <p class="lede">${esc(s.headline)}</p>
  <p><strong>The law.</strong> From 1 January 2027 (illustrative), any lot now limited to one home could have 2–6 homes, up to 3 stories, without special approval. Setbacks and lot coverage are assumed not to block them.</p>
  ${rangeCardHTML({ title: "Homes in 2–4 unit buildings, 2027–2031", range: R, baselineTotal: ALL_HOUSING_BASELINE_2027_2031, testid: "mid-range" })}
  <section class="card"><h2>Timing</h2>
    <p><label><input type="checkbox" id="mid-flat" ${flat ? "" : "checked"}> ${esc(s.timing.label)}</label>
    <span class="small muted">(off: ${esc(s.timing.toggle_off_label)}, ${num(s.range90_flat.low)} to ${num(s.range90_flat.high)})</span></p>
    <p class="small muted">${esc(s.timing.note)}</p></section>
  <section class="card"><h2>Extra 2–4 unit homes each year</h2><div class="chart-box" id="mid-chart"></div><div id="mid-legend"></div>
    <div class="table-wrap"><table class="data"><caption class="sr-only">Extra homes by year, 90% range</caption>
      <thead><tr><th scope="col">Year</th><th scope="col" class="num">Low end</th><th scope="col" class="num">High end</th></tr></thead>
      <tbody>${R.years.map((y) => `<tr><th scope="row">${y.year}</th><td class="num">${num(Math.min(y.low, y.high))}</td><td class="num">${num(Math.max(y.low, y.high))}</td></tr>`).join("")}</tbody></table></div>
    <p class="small muted">${esc(R.years_method ?? "")} The all-building-sizes line is listed below but not drawn: it is far above this scale.</p></section>
  <section class="card"><h2>Reasons to believe</h2>${sideLinesHTML(chartLines, "extra homes, 2027–2031", "side-lines")}</section>`;
  const base = s.baseline_by_year;
  const legend = drawRangeChart(main.querySelector<HTMLElement>("#mid-chart")!, {
    mode: "extra", range: R, sideLines: chartLines.filter((l) => l.id !== "all"), noun: "homes",
    base: { years: YEARS, central: base.central, low: base.low, high: base.high },
    title: "Extra homes from the law per year, 2027 to 2031", yLabel: "Extra homes per year",
  });
  main.querySelector("#mid-legend")!.innerHTML = legend;
  main.querySelector<HTMLInputElement>("#mid-flat")!.addEventListener("change", (ev) => {
    const q = new URLSearchParams(params);
    if ((ev.target as HTMLInputElement).checked) q.delete("timing"); else q.set("timing", "flat");
    env.replaceQuery(q); env.refresh();
  });
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
  <section class="card"><h2>Notes</h2><ul class="plain">${b.howsure.notes.map((n) => `<li>${esc(n)}</li>`).join("")}</ul></section>`;
}

function why(b: MiddleBundle, main: HTMLElement): void {
  main.innerHTML = `
  <h1>Why these numbers</h1>
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
    defaultPath: "/compare",
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
      else compare(b, env, params, main);
    },
  };
}

export const middleReform: ReformModule = { load, mount };
