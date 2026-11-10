// The middle housing reform (2–6 homes per lot): screens over the bundle written by scripts/build_middle_bundle.py.
// The browser only selects, sums and formats bundle values.
import { legendHTML, xyChart } from "../../charts";
import { esc, int, pill, YEARS } from "../../format";
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
const C = { central: "#17644f", upper: "#7b3fb0", lower: "#a8452c", side: "#4b5450" };
const signed = (v: number) => `${v > 0 ? "+" : v < 0 ? "−" : ""}${int(Math.abs(v))}`;
const rng = (r: Range) => `${signed(r.central)} (${signed(r.lower)} to ${signed(r.upper)})`;

const ROUTES: Route[] = [
  { path: "/compare", label: "Statewide comparison", n: 1 },
  { path: "/where", label: "Where", n: 2 },
  { path: "/how-sure", label: "How sure", n: 3 },
  { path: "/why", label: "Why", n: 4 },
];

/** Core line for the chosen timing: measured slow start (default) or the same effect every year. */
function coreYears(s: Statewide, flat: boolean): YearRange[] {
  if (!flat) return s.core.by_year;
  return YEARS.map((year) => ({ year, lower: s.timing.flat.lower / 5, central: s.timing.flat.central / 5, upper: s.timing.flat.upper / 5 }));
}

// ---- screens --------------------------------------------------------------------------------
function compare(b: MiddleBundle, env: ShellEnv, params: URLSearchParams, main: HTMLElement): void {
  const s = b.statewide, flat = params.get("timing") === "flat";
  const core: Range = flat ? s.timing.flat : s.core;
  const ys = coreYears(s, flat);
  main.innerHTML = `
  <h1>Middle housing: extra homes over five years</h1>
  <p class="lede">${esc(s.headline)}</p>
  <div class="tiles tiles-3">
    <section class="tile tile-accent"><h2 class="tile-label">${esc(s.core.label)}, 2027–2031</h2>
      <p class="tile-num" data-testid="core-central">${signed(core.central)}</p>
      <p class="tile-sub">extra homes permitted (range ${signed(core.lower)} to ${signed(core.upper)}) ${pill("calculated")}</p>
      <p class="tile-note">2-unit: ${rng(s.core.split["2_unit"])}. 3–4 unit: ${rng(s.core.split["3_4_unit"])}.</p></section>
    <section class="tile"><h2 class="tile-label">Under current law, 2027–2031</h2>
      <p class="tile-num">${int(s.baseline.total)}</p>
      <p class="tile-sub">homes of all sizes (range ${int(s.baseline.low_total)}–${int(s.baseline.high_total)}) ${pill("calculated")}</p>
      <p class="tile-note">Shared ${esc(s.baseline.version)}.</p></section>
    <section class="tile"><h2 class="tile-label">Measured rate</h2>
      <p class="tile-num">${s.core.rate_per_1000_sf_homes.central.toFixed(2)}</p>
      <p class="tile-sub">extra 2–4 unit homes per 1,000 single-family homes a year (${s.core.rate_per_1000_sf_homes.lower.toFixed(2)} to ${s.core.rate_per_1000_sf_homes.upper.toFixed(2)}) ${pill("calculated")}</p>
      <p class="tile-note">Oregon, California, Maine and Vermont against similar places, applied to Wisconsin's 1,839,569 single-family homes.</p></section>
  </div>
  <section class="card"><h2>Timing</h2>
    <p><label><input type="checkbox" id="mid-flat" ${flat ? "" : "checked"}> ${esc(s.timing.label)}</label>
    <span class="small muted">(off: ${esc(s.timing.toggle_off_label)}, ${rng(s.timing.flat)})</span></p>
    <p class="small muted">${esc(s.timing.note)}</p></section>
  <section class="card"><h2>Extra 2–4 unit homes each year</h2><div class="chart-box" id="mid-chart"></div>
    ${legendHTML([{ name: "Central", color: C.central }, { name: "Upper", color: C.upper, dash: "6 4" }, { name: "Lower", color: C.lower, dash: "6 4" }])}
    <div class="table-wrap"><table class="data"><caption class="sr-only">Extra homes by year</caption>
      <thead><tr><th scope="col">Year</th><th scope="col" class="num">Lower</th><th scope="col" class="num">Central</th><th scope="col" class="num">Upper</th></tr></thead>
      <tbody>${ys.map((y) => `<tr><th scope="row">${y.year}</th><td class="num">${signed(y.lower)}</td><td class="num">${signed(y.central)}</td><td class="num">${signed(y.upper)}</td></tr>`).join("")}</tbody></table></div></section>
  <section class="card" data-testid="side-measures"><h2>Other ways to count</h2>
    <ul class="plain">${s.side_measures.map((m) => `<li><strong>${esc(m.label)}</strong> <span class="small">(${signed(m.lower)} to ${signed(m.upper)})</span> <span class="small muted">(${esc(m.caveat)})</span></li>`).join("")}</ul></section>
  <section class="card" data-testid="extra-lines"><h2>Possibilities beyond what was measured</h2>
    <ul class="plain">${s.extra_lines.map((e) => `<li><strong>${esc(e.label)}: ${rng(e)}</strong> ${pill("assumed")}<br><span class="small muted">${esc(e.info)}</span></li>`).join("")}</ul></section>`;
  const box = main.querySelector<HTMLElement>("#mid-chart")!;
  const pts = (k: keyof Range) => ys.map((y) => ({ x: y.year, y: y[k] }));
  xyChart(box, {
    title: "Extra 2–4 unit homes permitted each year", desc: `Central ${signed(core.central)} over 2027–2031.`, yLabel: "Extra homes",
    xTicks: YEARS, series: [
      { name: "Upper", values: pts("upper"), color: C.upper, dash: "6 4" },
      { name: "Central", values: pts("central"), color: C.central, width: 3 },
      { name: "Lower", values: pts("lower"), color: C.lower, dash: "6 4" }],
  });
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
  <p class="lede">Every place gets the same measured rate per single-family home, so the split follows where single-family homes are. Nothing here is measured place by place.</p>
  <section class="card"><h2>25 places with the most single-family homes</h2><div class="table-wrap"><table class="data">
    <caption class="sr-only">Extra 2–4 unit homes, 2027–2031, by place</caption>
    <thead><tr><th scope="col">Place</th><th scope="col" class="num">Single-family homes</th><th scope="col" class="num">Lower</th><th scope="col" class="num">Central</th><th scope="col" class="num">Upper</th></tr></thead>
    <tbody>${top.map((a) => `<tr><th scope="row">${esc(a.name)}</th><td class="num">${int(a.sf_homes)}</td><td class="num">${signed(a.lower)}</td><td class="num">${signed(a.central)}</td><td class="num">${signed(a.upper)}</td></tr>`).join("")}</tbody></table></div>
    <p class="small muted">${b.areas.length.toLocaleString("en-US")} places in all. Single-family homes from ACS 2020–2024 (detached and attached).</p></section>`;
}

function howSure(b: MiddleBundle, main: HTMLElement): void {
  const s = b.statewide;
  main.innerHTML = `
  <h1>How sure we are</h1>
  <p class="lede">Predicted range for 2–4 unit homes: ${rng(s.core)} extra homes over 2027–2031. The range comes from comparing the real result with 10,000 sets of fake law states.</p>
  <section class="card"><h2>What changes the number</h2><div class="table-wrap"><table class="data">
    <caption class="sr-only">Other choices and the five-year central they give</caption>
    <thead><tr><th scope="col">Choice</th><th scope="col" class="num">Extra homes, 2027–2031</th></tr></thead>
    <tbody><tr><th scope="row">Core, as shown</th><td class="num">${signed(s.core.central)}</td></tr>
    ${b.howsure.bars.map((x) => `<tr><th scope="row">${esc(x.label)}${x.note ? `<br><span class="small muted">${esc(x.note)}</span>` : ""}</th><td class="num">${x.central !== undefined ? signed(x.central) : `${signed(x.low!)} to ${signed(x.high!)}`}</td></tr>`).join("")}</tbody></table></div></section>
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
