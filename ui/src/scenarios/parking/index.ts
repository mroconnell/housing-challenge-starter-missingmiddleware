// The parking requirement reduction reform: six screens over the bundle written by
// scripts/build_parking_bundle.py. The browser only selects, sums and formats bundle values.
import { legendHTML, xyChart } from "../../charts";
import { againstBandHTML, num, rangeCardHTML, sideLinesHTML, sideValue, type Range90, type SideLine } from "../../range";
import { loadWiHomes, renderSummary, type SummaryInput, type WiHomes } from "../../summary";
import { createMap, RAMP, WATER, type GeoKind, type MapHandle } from "../../map";
import { dec, esc, int, pill, YEARS } from "../../format";
import type { MountedReform, ReformEntry, ReformModule, Route, ShellEnv } from "../types";

// ---- bundle types --------------------------------------------------------------------------
interface YearRow { year: number; observed?: number; observed_published?: number; baseline_low?: number; baseline?: number; baseline_high?: number; bridge?: boolean; add_central?: number; add_upper?: number; add_lower?: number }
interface Scen { id: "central" | "upper" | "lower"; label: string; info: string; additional_total: number; with_law_total: number; rate_per_1000_homes?: number }
interface PkRow { place: string; spaces_per_home: number | null; share_built: number | null; climate?: string; source?: string }
interface Statewide {
  years: YearRow[]; baseline_total: number; baseline_low_total: number; baseline_high_total: number; baseline_published_total: number; baseline_recent_strength_total?: number | null;
  parking_checkup?: { wisconsin: PkRow[]; after_repeal: PkRow[]; notes?: PkRow[]; wisconsin_weighted: number; without_mandate: number; typical_share_built: number } | null;
  checkup?: { wisconsin_rate: number; wisconsin_years: string; wisconsin_homes: number; places: number; p10: number; p25: number; p50: number; p75: number; p90: number; max_shown: number };
  baseline_by_type: { type: string; low: number; central: number; high: number }[]; observed_2021_2025: number;
  scenarios: Scen[]; reference_line: { label: string; value: number; per_year: number; rate_per_1000_homes: number; info: string };
  // the uniform range display (docs/UNIFORM_DISPLAY_SPEC.md): one 90% range, no centre line, side lines across it
  range90: Range90 & { rate_low: number; rate_high: number }; side_lines: SideLine[];
}
interface Muni { id: string; name: string; county: string; type: string; homes: number; eligible_homes: number; at_benchmark: boolean; near_benchmark: boolean; baseline: number; add_upper: number; acres: number }
interface Areas {
  munis: Muni[]; counties: { id: string; name: string; homes: number; baseline: number; add_upper: number; acres: number }[];
  districts: { assembly: { id: number; homes: number; baseline: number; add_upper: number }[]; senate: { id: number; homes: number; baseline: number; add_upper: number }[] };
  benchmark_places: { name: string; rating: string; adopted: string | null }[];
}
interface HowSure {
  sensitivities: { case: string; moves: string; value: number; description: string }[];
  robustness: { check: string; places: number; effect: number; p05: number | null; p95: number | null }[];
  leave_one_state: { min: number; max: number; min_state: string; max_state: string };
  event_path: { year_since: number; places: number; effect: number; median: number }[];
  models: { one_average: number; best: string; best_error: number; best_band: number };
  trace: { part: string; status: string; text: string }[];
  traits: { dataset: string; label: string; places: number; gain: number; passes: boolean }[];
  tools: { tool: string; us_gain: number; ca_gain: number }[];
  placebo: Record<string, number>;
  average_views: { weighted: number; equal: number; median: number; places: number };
}
interface Why {
  places: { place: string; state: string; group: string; year: number; population: number; comparisons: number; after_years: number; before: number; after: number; cmp_before: number; cmp_after: number; effect: number; rewrite: boolean; evidence: string | null; confidence: string | null }[];
  average: Record<"all" | "2plus", { effect: number; p05: number; p95: number }>;
  studies: { case: string; finding: string; status: string; source: string; url: string }[];
  california: { all_units: { effect: number; p05: number; p95: number }; units_2plus: { effect: number; p05: number; p95: number }; jurisdictions: number; text: string; caveats: string };
  north_carolina: string; developer_parking: string; how_it_works?: string[]; docs: { label: string; url: string }[];
}
interface Pilot { slug: string; id: string; name: string; homes: number; at_benchmark: boolean; baseline: number; add_upper: number; history: { year: number; units_1: number | null; units_2: number | null; units_3_4: number | null; units_5: number | null; adjusted: boolean; split: boolean }[]; rules: { rating: string; date: string | null; summary: string | null }[] }
interface Manifest { run_id: string; title: string; outcome: { short: string; long: string; rate_units: string }; dates: { last_observed_year: number; forecast_years: number[]; effective: string }; vintages: { what: string; vintage: string }[]; validation: { passed: number; failed: number; checks: { check: string; passed: boolean; detail: string }[] }; repo_url: string; inputs: unknown[] }
export interface ParkingBundle { manifest: Manifest; statewide: Statewide; areas: Areas; howsure: HowSure; why: Why; pilots: Pilot[]; homes: WiHomes }

async function load(entry: ReformEntry): Promise<ParkingBundle> {
  const root = `${import.meta.env.BASE_URL}${entry.bundle_root}`;
  const get = async (p: string) => { const r = await fetch(p); if (!r.ok) throw new Error(`${p}: ${r.status}`); return r.json(); };
  const { run_id } = await get(`${root}latest.json`);
  const dir = `${root}${run_id}/`;
  const [[manifest, statewide, areas, howsure, why, pilots], homes] = await Promise.all([Promise.all(
    ["manifest", "statewide", "areas", "howsure", "why", "pilots"].map((f) => get(`${dir}${f}.json`))), loadWiHomes()]);
  return { manifest, statewide, areas, howsure, why, pilots, homes };
}

// ---- helpers ----------------------------------------------------------------------------------
const C = { baseline: "#4b5450", central: "#17644f", upper: "#7b3fb0", lower: "#a8452c", observed: "#4b5450" };
const TYPE_LABEL: Record<string, string> = { "1unit": "1 unit", "2units": "2 units", "3_4units": "3–4 units", "5plus": "5+ units" };
const signed = (v: number, d = 2) => `${v > 0 ? "+" : v < 0 ? "−" : ""}${dec(Math.abs(v), d)}`;
const more = (summary: string, html: string) => `<details class="more"><summary>${esc(summary)}</summary>${html}</details>`;

// The same tabs, in the same order, for every reform (owner, 2026-11-11). The former "Wisconsin today" content is on
// the shared Wisconsin today page; the former Statewide comparison is Summary plus How sure's Details.
const ROUTES: Route[] = [
  { path: "/summary", label: "Summary", n: 1 },
  { path: "/where", label: "Where", n: 2 },
  { path: "/how-sure", label: "How sure", n: 3 },
  { path: "/why", label: "Why", n: 4 },
  { path: "/pilot/milwaukee", label: "Pilots", n: 5, match: "/pilot" },
  { path: "/brief", label: "Brief", n: 6 },
];

// ---- screens --------------------------------------------------------------------------------
/** Owner, 2026-11-02: parking per new apartment — what Wisconsin cities require, what builders build without a mandate. */
function parkingCheckupHTML(c: NonNullable<Statewide["parking_checkup"]>): string {
  const max = Math.max(...c.wisconsin.map((w) => w.spaces_per_home ?? 0), 1);
  const bar = (label: string, v: number, color: string, note = "") => `<div class="pk-bar-row"><span class="pk-bar-label">${esc(label)}</span>
    <span class="pk-bar-track"><span class="pk-bar" style="width:${(v / max) * 100}%;background:${color}"></span></span><span class="pk-bar-val">${dec(v, 2)}${note}</span></div>`;
  const built = c.after_repeal.filter((r) => r.spaces_per_home != null);
  const shares = c.after_repeal.filter((r) => r.share_built != null).map((r) => `${esc(r.place)} ${dec((r.share_built ?? 0) * 100, 0)}%`).join(", ");
  const tag = (_r: PkRow) => "";
  const note = (r: PkRow) => (r.place === "Buffalo" ? " (share of old 1-per-home rule)" : r.place === "St. Paul" ? " (one building)" : r.place === "Minneapolis" ? " (all approvals 2021–23)" : " (median project)");
  return `<section class="card" data-testid="parking-checkup"><h2>Check-up: parking per new apartment</h2>
    <p>Your cities require about <strong>${dec(c.wisconsin_weighted, 2)}</strong> parking spaces for every new apartment (weighted by where apartments are expected). Where cities removed the mandate, builders still added parking, but less: about <strong>${dec(c.without_mandate, 2)}</strong> per apartment at the typical rate.</p>
    <div class="pk-bars" role="group" aria-label="Parking spaces per new apartment">
      <p class="small"><strong>Required today in Wisconsin cities</strong></p>
      ${c.wisconsin.map((w) => bar(w.place, w.spaces_per_home ?? 0, C.baseline)).join("")}
      <p class="small"><strong>Built in cities without a mandate</strong></p>
      ${built.map((w) => bar(w.place + tag(w), w.spaces_per_home ?? 0, C.central, note(w))).join("")}
      ${bar("Wisconsin apartments, if built like that", c.without_mandate, C.central, " (estimate)")}
    </div>
    ${(c.notes ?? []).length ? `<p class="small">${(c.notes ?? []).map((n) => `<strong>${esc(n.place)}</strong>: ${esc(n.source ?? "")}`).join(" ")}</p>` : ""}
    <p class="small muted">Minneapolis: all apartment approvals 2021–2023, after its 2021 repeal (old rule 1 per home). St. Paul: one 114-home building redesigned after its 2021 repeal. Buffalo: 36 major projects after its 2017 repeal kept about 80% of the old 1-per-home rule (all uses). Wisconsin rules: 16 city codes as compiled by Mankato's planning staff (2025), at a typical mix of one- and two-bedroom homes. After repeal, builders still built ${shares} of the old requirement (project studies); the estimate applies the typical share (${dec(c.typical_share_built * 100, 0)}%) to Wisconsin's rules. Los Angeles: 12 projects filed 2024–2026; Seattle: projects near frequent transit, 2012–2016.</p></section>`;
}

/** Owner, 2026-11-02: a "check-up" — Wisconsin's building rate against the range seen after repeals elsewhere. */
function checkupHTML(c: NonNullable<Statewide["checkup"]>): string {
  const top = Math.max(c.max_shown, c.wisconsin_rate * 1.2, c.p90);
  const x = (v: number) => (Math.min(v, top) / top) * 100;
  const where = c.wisconsin_rate < c.p25 ? "below the usual range" : c.wisconsin_rate > c.p75 ? "above the usual range" : "inside the usual range";
  return `<section class="card" data-testid="checkup"><h2>Check-up: how fast Wisconsin builds, against places that removed parking minimums</h2>
    <p>Wisconsin permitted <strong>${dec(c.wisconsin_rate, 1)}</strong> new homes per 1,000 existing homes a year in ${esc(c.wisconsin_years.replace("-", "–"))}. In the ${c.places} US places that removed parking minimums, the middle half permitted ${dec(c.p25, 1)} to ${dec(c.p75, 1)} in the years after (typical ${dec(c.p50, 1)}). So Wisconsin is ${where}.</p>
    <div class="checkup-bar" role="img" aria-label="Wisconsin ${dec(c.wisconsin_rate, 1)} per 1,000 homes a year; places after repeal: low below ${dec(c.p25, 1)}, usual ${dec(c.p25, 1)} to ${dec(c.p75, 1)}, high above ${dec(c.p75, 1)}">
      <svg viewBox="0 0 100 14" preserveAspectRatio="none" width="100%" height="40" aria-hidden="true" focusable="false">
        <rect x="0" y="4" width="${x(c.p25)}" height="6" fill="var(--line)"></rect>
        <rect x="${x(c.p25)}" y="4" width="${x(c.p75) - x(c.p25)}" height="6" fill="${C.central}" opacity="0.55"></rect>
        <rect x="${x(c.p75)}" y="4" width="${100 - x(c.p75)}" height="6" fill="${C.upper}" opacity="0.35"></rect>
        <line x1="${x(c.wisconsin_rate)}" x2="${x(c.wisconsin_rate)}" y1="0" y2="14" stroke="var(--ink)" stroke-width="0.8"></line>
      </svg>
      <div class="small" style="display:flex;justify-content:space-between"><span>Low (below ${dec(c.p25, 1)})</span><span>Usual (${dec(c.p25, 1)}–${dec(c.p75, 1)})</span><span>High (above ${dec(c.p75, 1)})</span></div>
    </div>
    <p class="small muted">The black line is Wisconsin. Ranges are the 25th and 75th percentiles of the repeal places' permit rates in the one to three years after repeal (permits per 1,000 existing homes per year). A place's rate depends mostly on its market; this is context, not a forecast.</p></section>`;
}

export function today(b: ParkingBundle, env: ShellEnv, main: HTMLElement): void {
  const s = b.statewide;
  const last = s.years.find((y) => y.year === 2025)!;
  const bench = b.areas.benchmark_places;
  main.innerHTML = `
  <h1>Parking requirements in Wisconsin today</h1>
  <p class="lede">How many new homes Wisconsin permits under current law, and where cities have already removed minimum parking requirements. All figures are housing units in new buildings, counted when the building permit is issued.</p>
  <div class="tiles tiles-3">
    <section class="tile"><h2 class="tile-label">New homes permitted in 2025</h2>
      <p class="tile-num" data-testid="observed-2025">${int(last.observed)}</p>
      <p class="tile-sub">all building sizes ${pill("observed")}</p>
      <p class="tile-note">Census building permits as published. Milwaukee's apartment estimate is not yet available for 2025, so this undercounts.</p></section>
    <section class="tile tile-accent"><h2 class="tile-label">Expected under current law, 2027–2031</h2>
      <p class="tile-num" data-testid="baseline-total">${int(s.baseline_total)}</p>
      <p class="tile-sub">permits over five years (range ${int(s.baseline_low_total)}–${int(s.baseline_high_total)}) ${pill("calculated")}</p>
      <p class="tile-note">Each place held at its 2023–2025 average (Milwaukee's apartments: 2023–2024). Places with no Census report, or a clear under-report (Wauwatosa, Caledonia and others), get the typical rate of similar places. The range comes from Wisconsin's own five-year swings since 1990.</p></section>
    <section class="tile"><h2 class="tile-label">Places with no parking minimums for housing</h2>
      <p class="tile-num" data-testid="bench-count">${bench.filter((x) => x.rating === "at").length}</p>
      <p class="tile-sub">cities and villages, plus ${bench.filter((x) => x.rating === "near").length} with conditions ${pill("observed")}</p>
      <p class="tile-note">From the Parking Reform Network's reform map. A statewide law adds nothing in these places.</p></section>
  </div>
  ${s.parking_checkup ? parkingCheckupHTML(s.parking_checkup) : ""}
  ${s.checkup ? checkupHTML(s.checkup) : ""}
  <section class="card"><h2>New homes permitted each year: past and current law</h2><div class="chart-box" id="pk-today-chart"></div>
    ${legendHTML([{ name: "Observed", color: C.observed, width: 2 }, { name: "Current law (range shaded)", color: C.baseline, dash: "7 5" }])}
    <p class="small muted">Observed 2015–2025 from Census building permits, with Milwaukee's apartments estimated from the city's property file. 2026 is a bridge year; the law's window is 2027–2031.</p></section>
  <section class="card"><h2>Current-law permits by building size, 2027–2031</h2>
    <div class="table-wrap"><table class="data"><caption class="sr-only">Expected permits under current law by building size</caption>
    <thead><tr><th scope="col">Building size</th><th scope="col" class="num">Low</th><th scope="col" class="num">Central</th><th scope="col" class="num">High</th></tr></thead>
    <tbody>${s.baseline_by_type.map((t) => `<tr><th scope="row">${esc(TYPE_LABEL[t.type] ?? t.type)}</th><td class="num">${int(t.low)}</td><td class="num">${int(t.central)}</td><td class="num">${int(t.high)}</td></tr>`).join("")}</tbody></table></div>
    <p class="small muted">Minimum parking rules matter most for buildings of 2 or more units; houses usually come with parking anyway.</p></section>
  <section class="card"><h2>Places that already have no parking minimums for housing</h2>
    <p>${bench.filter((x) => x.rating === "at").map((x) => `${esc(x.name)}${x.adopted ? ` (${esc(x.adopted.slice(0, 4))})` : ""}`).join(", ")}.</p>
    ${more("Places that removed minimums with conditions", `<p>${bench.filter((x) => x.rating === "near").map((x) => esc(x.name)).join(", ")}. Madison and Milwaukee have partial reforms (downtown and some districts; Madison's 2023 transit overlay) and still require parking elsewhere.</p>`)}
  </section>
  <p><a class="button" href="${env.link("/summary")}">What a statewide parking law would add →</a></p>`;
  const ys = s.years;
  xyChart(document.getElementById("pk-today-chart")!, {
    title: "New homes permitted each year in Wisconsin: observed and current law",
    desc: `Observed 2015–2025; current law ${int(s.baseline_total)} over 2027–2031 (range ${int(s.baseline_low_total)}–${int(s.baseline_high_total)}).`,
    yLabel: "Permits per year", xTicks: ys.map((y) => y.year),
    xFormat: (x: number) => (window.innerWidth < 600 && (x - 2015) % 4 !== 0 ? "" : String(x)),
    series: [
      { name: "Observed", values: ys.map((y) => ({ x: y.year, y: y.observed ?? null })), color: C.observed, width: 2, marker: "circle" },
      { name: "Current law", values: ys.map((y) => ({ x: y.year, y: y.baseline ?? null })), color: C.baseline, dash: "7 5" },
    ],
    band: { name: "Current-law range", lo: ys.map((y) => ({ x: y.year, y: y.baseline_low ?? null })), hi: ys.map((y) => ({ x: y.year, y: y.baseline_high ?? null })), color: C.baseline },
  });
}

const PK_UNIT = "extra homes permitted over 2027–2031";
/** Each area's share of the statewide range: the law spreads one rate per eligible home, so every area holds the
 *  same share of the low end and of the high end. The bundle's per-area figure is the high end's share. */
function pkShare(b: ParkingBundle, addUpper: number): number {
  const up = b.statewide.scenarios.find((x) => x.id === "upper")!.additional_total;
  return up ? addUpper / up : 0;
}

/** The parking Summary: the shared component. Parking's measured effect is the same every year (no ramp), so the
 *  timing toggle is disabled. */
function summaryInput(b: ParkingBundle): SummaryInput {
  const s = b.statewide, fy = s.years.filter((y) => YEARS.includes(y.year));
  return {
    id: "parking", title: "Parking requirement reduction", law: "removes minimum parking requirements for all housing", unit: "homes",
    range: s.range90, rangeFlat: "none", sideLines: s.side_lines.filter((x) => x.where === "chart"),
    base: { central: fy.map((y) => y.baseline ?? 0), low: fy.map((y) => y.baseline_low ?? 0), high: fy.map((y) => y.baseline_high ?? 0) },
    baseName: "homes of all kinds permitted under current law", homes: b.homes,
  };
}

/** The former Statewide comparison, now How sure's Details: the range card, every side line, the yearly table and
 *  "How big is that?". The chart is on Summary. */
function details(b: ParkingBundle, env: ShellEnv): string {
  const s = b.statewide;
  const R = s.range90;
  const fy = s.years.filter((y) => YEARS.includes(y.year));
  return `
  <h2 class="section-h" id="h-details" data-testid="details">Details</h2>
  ${rangeCardHTML({ title: "Extra homes from the law: the 90% range", range: R, baselineTotal: s.baseline_total, testid: "range-card", headingLevel: 3 })}
  <section class="card" aria-labelledby="h-pk-side"><h3 id="h-pk-side">Side lines</h3>
    ${sideLinesHTML(s.side_lines.filter((x) => x.where === "chart"), PK_UNIT, "side-lines", "Drawn on the Summary chart. Lines can sit outside the range; they do not change it.")}
    ${sideLinesHTML(s.side_lines.filter((x) => x.where !== "chart"), PK_UNIT, "howsure-side-lines", "Shown here only. None changes the 90% range.")}</section>
  <section class="card" aria-labelledby="h-pk-years"><h3 id="h-pk-years">New homes permitted each year</h3>
    <div class="table-wrap"><table class="data" data-testid="compare-table"><caption>Homes permitted in Wisconsin: current law, and the law's extra homes as a 90% range</caption>
      <thead><tr><th scope="col">Year</th><th scope="col" class="num">Current law</th><th scope="col" class="num">Current law: low</th><th scope="col" class="num">Current law: high</th><th scope="col" class="num">Extra with the law: low end</th><th scope="col" class="num">Extra with the law: high end</th></tr></thead>
      <tbody>${fy.map((y) => { const r = R.years.find((x) => x.year === y.year)!; return `<tr><th scope="row">${y.year}</th><td class="num">${int(y.baseline)}</td><td class="num">${int(y.baseline_low)}</td><td class="num">${int(y.baseline_high)}</td><td class="num">${num(r.low)}</td><td class="num">${num(r.high)}</td></tr>`; }).join("")}
      <tr><th scope="row">2027–2031</th><td class="num">${int(s.baseline_total)}</td><td class="num">${int(s.baseline_low_total)}</td><td class="num">${int(s.baseline_high_total)}</td><td class="num" data-testid="table-range-low">${num(R.low)}</td><td class="num" data-testid="table-range-high">${num(R.high)}</td></tr></tbody></table></div>
    <p class="small muted">Homes in issued building permits, all building sizes. Current law holds each place at its 2023–2025 average; its range (${int(s.baseline_low_total)} to ${int(s.baseline_high_total)} homes over five years) comes from Wisconsin's own five-year swings and is not added to the law's range. The law's range is the same each year, one fifth of the five-year range. Observed years are on <a href="#/wisconsin-today?section=parking">Wisconsin today</a>. Yearly rows may not add exactly to the totals because of rounding.</p></section>
  <section class="card" aria-labelledby="h-pk-big"><h3 id="h-pk-big">How big is that?</h3>
    <p data-testid="compare-size">About ${num(R.years[0].low)} to ${num(R.years[0].high)} extra homes permitted a year, against about ${int(fy[0].baseline)} homes a year Wisconsin is expected to permit under current law (all homes, all places). These are homes in issued building permits, not completed homes.</p></section>
  <p class="small"><a href="${env.link("/summary")}">The range and its side lines on the chart →</a></p>`;
}

// ---- map (shared geography from the ADU bundle: county, municipality and district outlines) ----
let mapH: MapHandle | null = null;
let geoCache: Record<GeoKind, unknown> | null = null;

function leaveMap(): void { mapH?.destroy(); mapH = null; }

function quintiles(vals: number[]): number[] {
  const v = vals.filter((x) => Number.isFinite(x)).sort((a, z) => a - z);
  if (!v.length) return [1, 2, 3, 4];
  const q = (f: number) => v[Math.min(v.length - 1, Math.floor(f * v.length))];
  const out = [q(0.2), q(0.4), q(0.6), q(0.8)].map((x) => Math.max(1, Math.round(x)));
  for (let i = 1; i < 4; i++) if (out[i] <= out[i - 1]) out[i] = out[i - 1] + 1;
  return out;
}

async function loadGeo(): Promise<Record<GeoKind, unknown>> {
  if (geoCache) return geoCache;
  const base = `${import.meta.env.BASE_URL}runs/`;
  const { run_id } = await (await fetch(`${base}latest.json`)).json();
  const [counties, munis, assembly, senate] = await Promise.all(["geo_counties", "geo_munis", "geo_assembly", "geo_senate"]
    .map((f) => fetch(`${base}${run_id}/${f}.json`).then((r) => r.json())));
  geoCache = { counties, munis, assembly, senate };
  return geoCache;
}

function where(b: ParkingBundle, env: ShellEnv, params: URLSearchParams, main: HTMLElement): void {
  const level = params.get("level") ?? "county";
  const q = (params.get("q") ?? "").toLowerCase();
  const A = b.areas;
  const R = b.statewide.range90;
  let rows: { name: string; homes: number; baseline: number; add: number; acres?: number; note?: string }[];
  if (level === "municipality") rows = A.munis.filter((m) => !q || m.name.toLowerCase().includes(q)).map((m) => ({ name: `${m.name}, ${m.county}`, homes: m.eligible_homes, baseline: m.baseline, add: m.add_upper, acres: m.acres, note: m.at_benchmark ? "already has no parking minimums for housing" : m.near_benchmark ? "removed minimums with conditions" : "" }));
  else if (level === "assembly" || level === "senate") rows = A.districts[level].map((d) => ({ name: `${level === "assembly" ? "Assembly" : "Senate"} District ${d.id}`, homes: d.homes, baseline: d.baseline, add: d.add_upper }));
  else rows = A.counties.map((c) => ({ name: c.name, homes: c.homes, baseline: c.baseline, add: c.add_upper, acres: c.acres }));
  rows.sort((a, z) => (z.add || 0) - (a.add || 0));   // by share of the range: the low end ascending, the high end descending
  const lowOf = (add: number) => pkShare(b, add) * R.low, highOf = (add: number) => pkShare(b, add) * R.high;
  const perAcres = level === "county" || level === "municipality";
  const shown = level === "municipality" && !q ? rows.slice(0, 50) : rows;
  main.innerHTML = `
  <h1>Where the added homes would be</h1>
  <p class="lede">The law's range is spread over places by one rate per existing home, everywhere except places that already have no parking minimums for housing. So it is largest where most people live, and every area holds the same share of the low end as of the high end. Totals are 2027–2031.</p>
  <p class="small" data-testid="where-range-note">Each area's 90% range is the statewide 90% range (${num(R.low)} to ${num(R.high)} extra homes permitted, 2027–2031) times the area's share of eligible homes, because the law is applied as one rate per eligible home.</p>
  <form class="card" id="where-form"><fieldset class="seg"><legend>Show by</legend>
    ${[["county", "County"], ["municipality", "City, village or town"], ["assembly", "Assembly district"], ["senate", "Senate district"]].map(([v, l]) => `<label><input type="radio" name="level" value="${v}" ${level === v ? "checked" : ""}> ${l}</label>`).join("")}</fieldset>
    ${level === "municipality" ? `<p><label>Find a place <input type="search" name="q" value="${esc(q)}" data-testid="where-search"></label></p>` : ""}</form>
  <section class="card" aria-labelledby="h-pkmap"><h2 id="h-pkmap">Map: the high end of each area's 90% range, extra homes permitted, 2027–2031</h2>
    <div class="map" id="pk-map" data-testid="parking-map"><div class="map-tip" hidden></div></div>
    <div id="pk-legend"></div>
    <p class="small muted">The low end has the same pattern, below zero: each area's low end is the same share of the statewide low end (${num(R.low)}). The table below has both ends. Boundaries: U.S. Census Bureau cartographic boundary files and Wisconsin Legislative Technology Services Bureau districts.</p></section>
  <div class="table-wrap"><table class="data" data-testid="where-table"><caption>${level === "municipality" && !q ? "The 50 places with the largest share of the range" : "Extra homes permitted"}, 2027–2031, as a 90% range (statewide ${num(R.low)} to ${num(R.high)}); sorted by share of the range, largest first</caption>
    <thead><tr><th scope="col">Area</th><th scope="col" class="num">Homes it applies to</th><th scope="col" class="num">Current-law permits</th><th scope="col" class="num">Extra homes: low end</th><th scope="col" class="num">Extra homes: high end</th>${perAcres ? `<th scope="col" class="num">Extra homes per 1,000 acres of land, 90% range</th>` : ""}</tr></thead>
    <tbody>${shown.map((r) => `<tr><th scope="row">${esc(r.name)}${r.note ? ` <span class="small muted">(${esc(r.note)})</span>` : ""}</th><td class="num">${int(r.homes)}</td><td class="num">${int(r.baseline)}</td><td class="num">${num(lowOf(r.add))}</td><td class="num">${num(highOf(r.add))}</td>${perAcres ? `<td class="num">${r.acres ? `${dec((lowOf(r.add) / r.acres) * 1000, 1).replace(/^-/, "−")} to ${dec((highOf(r.add) / r.acres) * 1000, 1)}` : "—"}</td>` : ""}</tr>`).join("")}</tbody></table></div>
  <p class="small muted">"Homes it applies to" is 0 where a place already has no parking minimums for housing, so its range is 0 to 0. "Per 1,000 acres" divides the five-year range by each area's land area (Census), for comparison with density measures; it is low where land is mostly farms or forest. District figures are estimated from where each place's homes sit, an approximation. Towns are included; a case on "How sure" leaves them out. Rows may not add exactly because of rounding.</p>`;
  // map values by geography (ids as in the shared outline files)
  const geoKind: GeoKind = level === "municipality" ? "munis" : level === "assembly" ? "assembly" : level === "senate" ? "senate" : "counties";
  const vals = new Map<string, number | null>();
  const names = new Map<string, string>();
  // the high end of each area's range (the bundle's per-area figure scaled to the range's high end)
  const hi = (v: number) => pkShare(b, v) * R.high;
  if (geoKind === "munis") for (const m of A.munis) { vals.set(m.id, hi(m.add_upper)); names.set(m.id, `${m.name}, ${m.county}`); }
  else if (geoKind === "counties") for (const c of A.counties) { vals.set(c.id, hi(c.add_upper)); names.set(c.id, c.name); }
  else for (const d of A.districts[geoKind as "assembly" | "senate"]) {
    const id = `${geoKind === "assembly" ? "asm" : "sen"}:${d.id}`;
    vals.set(id, hi(d.add_upper)); names.set(id, `${geoKind === "assembly" ? "Assembly" : "Senate"} District ${d.id}`);
  }
  const br = quintiles([...vals.values()].filter((v): v is number => v !== null && v > 0));
  const lab = (i: number) => i === 0 ? `under ${int(br[0])}` : i === 4 ? `${int(br[3])} or more` : `${int(br[i - 1])} to ${int(br[i] - 1)}`;
  main.querySelector("#pk-legend")!.innerHTML = `<ul class="legend map-legend" aria-label="Map legend: high end of the 90% range, extra homes permitted, five classes with about equal numbers of areas">${RAMP.map((c, i) => `<li><span class="lg-sw" style="background:${c}"></span>${esc(lab(i))}</li>`).join("")}<li><span class="lg-sw" style="background:${WATER}"></span>lakes and outside Wisconsin</li></ul>`;
  const mapEl = main.querySelector<HTMLElement>("#pk-map")!;
  const tip = mapEl.querySelector<HTMLElement>(".map-tip")!;
  leaveMap();
  loadGeo().then((g) => {
    if (!mapEl.isConnected) return;
    mapH = createMap(mapEl, g, () => { /* the table holds the details */ }, (id, x, y) => {
      if (!id) { tip.hidden = true; return; }
      tip.hidden = false;
      tip.style.left = `${Math.min(x + 12, mapEl.clientWidth - 200)}px`;
      tip.style.top = `${y + 12}px`;
      const v = vals.get(id);
      tip.textContent = v == null ? `${names.get(id) ?? id}: no data` : `${names.get(id) ?? id}: ${num((v / R.high) * R.low)} to ${num(v)} extra homes permitted (90% range)`;
    });
    mapH.setGeography(geoKind);
    mapH.setData(vals, br);
    mapEl.querySelector("canvas")?.setAttribute("aria-label", `Map of the high end of each area's 90% range of extra homes permitted by ${level === "municipality" ? "city, village and town" : level}; the same values are in the table below.`);
  }).catch(() => { mapEl.innerHTML = `<p class="small muted">The map could not load; the table below has the same values.</p>`; });
  const f = document.getElementById("where-form") as HTMLFormElement;
  f.addEventListener("change", () => {
    const nq = new URLSearchParams();
    const fd = new FormData(f);
    nq.set("level", String(fd.get("level")));
    if (fd.get("q")) nq.set("q", String(fd.get("q")));
    env.replaceQuery(nq);
    env.refresh();
    env.announce("Table updated.");
  });
}

function howSure(b: ParkingBundle, env: ShellEnv, main: HTMLElement): void {
  const H = b.howsure;
  const R = b.statewide.range90;
  // The two former headline rows are not repeated: the high end is the range's own high end, and the former low line
  // (the measured average) is now a side line.
  const cases = H.sensitivities.filter((x) => !/\(headline\)/.test(x.case));
  const groups = [...new Set(cases.map((x) => x.moves))];
  const lawCases = cases.filter((x) => x.moves !== "current law only").sort((a, z) => z.value - a.value);
  main.innerHTML = `
  <h1>How sure are we?</h1>
  <p class="lede">The law's extra homes are one 90% range, ${num(R.low)} to ${num(R.high)} over 2027–2031, and it includes zero: the evidence found no measurable effect. This page puts every what-if against that range, shows how stable the finding is, and which parts rest on data and which on judgment. The range card, the side lines and the yearly table are under Details at the end.</p>
  <section class="card" aria-labelledby="h-pk-tornado"><h2 id="h-pk-tornado">What-ifs against the range</h2>
    <p>Each row is one what-if: a dot at its own statewide extra homes over 2027–2031, with a bar from zero. The shaded band is the 90% range, ${num(R.low)} to ${num(R.high)}. A hollow dot sits outside the range. No what-if changes the range.</p>
    ${againstBandHTML(lawCases.map((x) => ({ label: x.case, value: x.value })), R, "Each what-if's own extra homes permitted in Wisconsin, 2027–2031", "pk-tornado")}
    <p class="small muted" data-testid="pk-tornado-note">Not repeated here: the former high line (the range's high end, ${num(R.high)}) and the former low line (now the side line "${esc(b.statewide.side_lines.find((x) => x.id === "measured_average")?.label ?? "Measured average")}"). What-ifs about current law alone are in a table below; they do not change the law's extra homes. <a href="${env.link("/summary")}">The range and its side lines on the chart →</a></p></section>
  ${groups.map((g) => `<section class="card"><h2>Cases that change ${esc(g)}</h2><div class="table-wrap"><table class="data"><caption class="sr-only">${esc(g)}</caption>
    <thead><tr><th scope="col">Case</th><th scope="col" class="num">${g === "current law only" ? "Current-law permits, 2027–2031" : "Extra homes permitted, 2027–2031"}</th><th scope="col">What it means</th></tr></thead>
    <tbody>${cases.filter((x) => x.moves === g).map((x) => `<tr><th scope="row">${esc(x.case)}</th><td class="num">${num(x.value)}</td><td>${esc(x.description)}</td></tr>`).join("")}</tbody></table></div></section>`).join("")}
  <section class="card"><h2>Is the finding stable?</h2>
    <p>The average effect stays near zero however it is cut. Across all ${int(H.average_views.places)} places, weighting each by its homes gives ${signed(H.average_views.weighted)}, counting each place equally gives ${signed(H.average_views.equal)}, and the middle place is ${signed(H.average_views.median)} permits per 1,000 existing homes per year. A few big cities, whose repeals met market slumps, pull the weighted figure down. In the first 24 places, leaving out one state at a time gave ${signed(H.leave_one_state.min)} (without ${esc(H.leave_one_state.min_state)}) to ${signed(H.leave_one_state.max)} (without ${esc(H.leave_one_state.max_state)}) permits per 1,000 existing homes per year.</p>
    <div class="table-wrap"><table class="data"><caption>Average effect, permits per 1,000 existing homes per year</caption>
      <thead><tr><th scope="col">Check</th><th scope="col" class="num">Places</th><th scope="col" class="num">Effect</th><th scope="col" class="num">Likely range</th></tr></thead>
      <tbody>${H.robustness.map((x) => `<tr><th scope="row">${esc(x.check)}</th><td class="num">${x.places}</td><td class="num">${signed(x.effect)}</td><td class="num">${x.p05 === null ? "—" : `${signed(x.p05)} to ${signed(x.p95!)}`}</td></tr>`).join("")}</tbody></table></div>
    <p class="small muted"><strong>Do different kinds of places respond differently?</strong> In the first 24 places, we tested this by predicting each repeal place from all the others. One average for all places missed by ${dec(H.models.one_average, 2)} permits per 1,000 homes per year on average. Using ${esc(H.models.best)} missed by ${dec(H.models.best_error, 2)}, and splitting places by size missed by ${dec(H.models.best_band, 2)}. The gain was too small to rely on, so one average is used. "Likely range" means 90 times in 100 the true average would fall inside it.</p></section>
  <section class="card"><h2>A check with cities that never repealed</h2>
    <p>We gave ${int(H.placebo.placebo_places)} cities that kept their parking minimums the same "repeal" years as the real places and ran the same calculation, 20,000 times. Each real place had at least 20 look-alikes to draw from. ${dec(H.placebo.share_placebo_at_or_below_real * 100, 0)}% of those placebo studies came out as low as the real places (${signed(H.placebo.real_average)} permits per 1,000 existing homes per year; placebo middle ${signed(H.placebo.placebo_p50)}). So the real result is ordinary for cities that never repealed: no sign that a repeal raised or lowered permits. The spread of these placebo studies, centred on the real average, sets the 90% range used here: ${signed(R.rate_low)} to ${signed(R.rate_high)} permits per 1,000 existing homes per year, or ${num(R.low)} to ${num(R.high)} extra homes permitted in Wisconsin over 2027–2031. Resampling the real places alone gave a similar high end, shown above as a what-if.</p></section>
  <section class="card"><h2>Do prediction tools do better than one average?</h2>
    <p>With 74 places, we tried tools that look at ten traits at once. Each was scored on places left out of the fit, in the US places and in California's cities. None beat one average, so every place gets the same average.</p>
    <div class="table-wrap"><table class="data"><caption>Change in prediction error compared with one average (negative = worse)</caption>
      <thead><tr><th scope="col">Tool</th><th scope="col" class="num">US repeal places</th><th scope="col" class="num">California near transit</th></tr></thead>
      <tbody>${H.tools.filter((t) => t.tool !== "one average").map((t) => `<tr><th scope="row">${esc(t.tool)}</th><td class="num">${signed(t.us_gain * 100, 0)}%</td><td class="num">${signed(t.ca_gain * 100, 0)}%</td></tr>`).join("")}</tbody></table></div></section>
  <section class="card"><h2>Do city traits explain the differences?</h2>
    <p>We tested six traits one at a time, in US repeal places and in California cities near transit, with the test written down first. A trait had to predict left-out places at least 5% better than one average in both. ${H.traits.some((t) => t.passes) ? "Some passed." : "None did, so every place gets the same average."}</p>
    <div class="table-wrap"><table class="data"><caption>Improvement in predicting left-out places, compared with one average</caption>
      <thead><tr><th scope="col">Trait</th><th scope="col" class="num">US repeal places</th><th scope="col" class="num">California near transit</th></tr></thead>
      <tbody>${[...new Set(H.traits.map((t) => t.label))].map((l) => { const a = H.traits.find((t) => t.label === l && t.dataset.startsWith("A")); const c = H.traits.find((t) => t.label === l && t.dataset.startsWith("B")); return `<tr><th scope="row">${esc(l)}</th><td class="num">${a ? `${signed(a.gain * 100, 0)}%` : "—"}</td><td class="num">${c ? `${signed(c.gain * 100, 0)}%` : "—"}</td></tr>`; }).join("")}</tbody></table></div></section>
  <section class="card"><h2>Does the effect grow over time? (first 24 places)</h2>
    <div class="table-wrap"><table class="data"><caption>Effect by year since repeal, permits per 1,000 existing homes per year</caption>
      <thead><tr><th scope="col">Year since repeal</th><th scope="col" class="num">Places</th><th scope="col" class="num">Average</th><th scope="col" class="num">Median place</th></tr></thead>
      <tbody>${H.event_path.map((x) => `<tr><th scope="row">${x.year_since}</th><td class="num">${x.places}</td><td class="num">${signed(x.effect)}</td><td class="num">${signed(x.median)}</td></tr>`).join("")}</tbody></table></div>
    <p class="small muted">No: it drifts lower, though few places reach years 4 and 5. Holding the range's high end flat to 2031 is generous. This path was computed after the plan was registered and changes no number.</p></section>
  <section class="card"><h2>What rests on data and what on judgment</h2>
    <ul class="plain">${H.trace.map((t) => `<li>${pill(t.status)} <strong>${esc(t.part)}.</strong> ${esc(t.text)}</li>`).join("")}</ul></section>
  ${details(b, env)}`;
}

function why(b: ParkingBundle, main: HTMLElement): void {
  const W = b.why;
  const a = W.average.all, m = W.average["2plus"];
  main.innerHTML = `
  <h1>Why: the evidence</h1>
  <p class="lede">No state has removed parking minimums for all housing long enough to measure, so the evidence comes from cities and villages that did. We compared each with similar places in the same state that kept their minimums.</p>
  <section class="card"><h2>What happened after US places removed parking minimums</h2>
    <p data-testid="why-average">In the three years after a repeal, the repeal places' permit rate changed by ${signed(a.effect)} per 1,000 existing homes per year compared with similar places (likely range ${signed(a.p05)} to ${signed(a.p95)}). For buildings of 2 or more units: ${signed(m.effect)} (${signed(m.p05)} to ${signed(m.p95)}). Neither is a measurable change.</p>
    ${more(`All ${W.places.length} places`, `<div class="table-wrap"><table class="data" data-testid="why-places"><caption>Permits per 1,000 existing homes per year, before and after repeal</caption>
      <thead><tr><th scope="col">Place</th><th scope="col">Repeal year</th><th scope="col" class="num">Before</th><th scope="col" class="num">After</th><th scope="col" class="num">Comparison places before → after</th><th scope="col" class="num">Effect</th><th scope="col">Notes</th></tr></thead>
      <tbody>${W.places.map((p) => `<tr><th scope="row">${esc(p.place)}, ${esc(p.state)}</th><td>${p.year}</td><td class="num">${dec(p.before)}</td><td class="num">${dec(p.after)}</td><td class="num">${dec(p.cmp_before)} → ${dec(p.cmp_after)} (${p.comparisons})</td><td class="num">${signed(p.effect)}</td><td class="small">${p.after_years} after-year${p.after_years === 1 ? "" : "s"}. ${p.group === "main" ? "" : "Removed with conditions. "}${p.rewrite ? "Zoning rewrite at the same time." : ""}</td></tr>`).join("")}</tbody></table></div>`)}</section>
  <section class="card"><h2>A second check: California's transit-area law</h2>
    <p data-testid="why-california">${esc(W.california.text)} Across ${W.california.jurisdictions} California jurisdictions, the change near transit was ${signed(W.california.all_units.effect)} permits per 1,000 existing homes per year (90% range ${signed(W.california.all_units.p05)} to ${signed(W.california.all_units.p95)}); for buildings of 2 or more units, ${signed(W.california.units_2plus.effect)} (${signed(W.california.units_2plus.p05)} to ${signed(W.california.units_2plus.p95)}).</p>
    <p class="small muted">${esc(W.california.caveats)}</p></section>
  <section class="card"><h2>How much parking developers build without a mandate</h2>
    <p data-testid="developer-parking"><strong>${esc(W.developer_parking.split(":")[0])}:</strong>${esc(W.developer_parking.slice(W.developer_parking.indexOf(":") + 1))}</p>
    <ul class="plain">${W.studies.map((s) => `<li>${s.status === "observed" ? pill("observed") : `<span class="pill pill-assumed">Not yet checked</span>`} <strong>${esc(s.case)}.</strong> ${esc(s.finding)} <a href="${esc(s.url)}" target="_blank" rel="noopener">${esc(s.source)}<span class="sr-only"> (opens in a new tab)</span> ↗</a></li>`).join("")}</ul>
    <p class="small muted">"Not yet checked" means read from a summary, not the full paper.</p></section>
  ${W.how_it_works ? `<section class="card" data-testid="how-it-works"><h2>How a repeal changes what gets built</h2><ul class="plain">${W.how_it_works.map((t) => `<li>${esc(t)}</li>`).join("")}</ul></section>` : ""}
  <section class="card"><h2>The closest real law</h2><p>${esc(W.north_carolina)}</p></section>
  <p class="small">${W.docs.map((d) => `<a href="${esc(d.url)}" target="_blank" rel="noopener">${esc(d.label)} ↗</a>`).join(" · ")}</p>`;
}

function pilot(b: ParkingBundle, env: ShellEnv, slug: string, main: HTMLElement): void {
  const p = b.pilots.find((x) => x.slug === slug) ?? b.pilots[0];
  main.innerHTML = `
  <h1>Pilot: ${esc(p.name.replace(/ (city|village|town)$/, " ($1)"))}</h1>
  <nav aria-label="Pilot places"><p>${b.pilots.map((x) => x.slug === p.slug ? `<strong>${esc(x.name)}</strong>` : `<a href="${env.link(`/pilot/${x.slug}`)}">${esc(x.name)}</a>`).join(" · ")}</p></nav>
  <div class="tiles tiles-3">
    <section class="tile"><h2 class="tile-label">Homes</h2><p class="tile-num">${int(p.homes)}</p><p class="tile-sub">ACS 2020–2024 ${pill("observed")}</p></section>
    <section class="tile"><h2 class="tile-label">Current-law permits, 2027–2031</h2><p class="tile-num" data-testid="pilot-baseline">${int(p.baseline)}</p><p class="tile-sub">${pill("calculated")}</p></section>
    <section class="tile"><h2 class="tile-label">Extra homes from the law, 2027–2031</h2><p class="tile-num"><span data-testid="pilot-low">${num(pkShare(b, p.add_upper) * b.statewide.range90.low)}</span> to <span data-testid="pilot-upper">${int(p.add_upper)}</span></p><p class="tile-sub">${p.at_benchmark ? "already has no parking minimums for housing, so the law adds nothing" : "permits, 90% range: the place's share of the statewide range"} ${pill("calculated")}</p></section>
  </div>
  <section class="card"><h2>Permits by building size, 2015–2025</h2><div class="table-wrap"><table class="data"><caption class="sr-only">Permits by year and building size</caption>
    <thead><tr><th scope="col">Year</th><th scope="col" class="num">1 unit</th><th scope="col" class="num">2 units</th><th scope="col" class="num">3–4 units</th><th scope="col" class="num">5+ units</th></tr></thead>
    <tbody>${p.history.map((h) => `<tr><th scope="row">${h.year}</th><td class="num">${int(h.units_1)}${h.split ? "†" : ""}</td><td class="num">${int(h.units_2)}${h.split ? "†" : ""}</td><td class="num">${int(h.units_3_4)}${h.adjusted ? "*" : ""}</td><td class="num">${int(h.units_5)}${h.adjusted ? "*" : ""}</td></tr>`).join("")}</tbody></table></div>
    ${p.history.some((h) => h.adjusted) ? `<p class="small muted">* Estimated from the city's property file (year built, one year earlier), because the Census permit file misses most of Milwaukee's apartments. A dash means not available.</p>` : ""}${p.history.some((h) => h.split) ? `<p class="small muted">† The city crosses county lines; its Census total is split between counties by homes, so these are estimates.</p>` : ""}</section>
  <section class="card"><h2>Parking rules on record</h2>${p.rules.length ? `<ul class="plain">${p.rules.map((r) => `<li><strong>${esc(r.rating === "at" ? "Removed for all housing" : r.rating === "plan_only" ? "Recommended in a plan" : r.rating === "near" ? "Removed with conditions" : "Partial reform")}</strong>${r.date ? ` (${esc(r.date)})` : ""}: ${esc(r.summary)}</li>`).join("")}</ul>` : "<p>None recorded.</p>"}
    <p class="small muted">From the Parking Reform Network's reform map (MIT licence), quoted as written. "TDM" is transportation demand management (measures such as transit passes that reduce driving); "C9A" is a Milwaukee downtown zoning district.</p></section>`;
}

function brief(b: ParkingBundle, main: HTMLElement): void {
  const s = b.statewide, R = s.range90, W = b.why.average.all;
  main.innerHTML = `
  <h1>Brief: a statewide parking law for Wisconsin</h1>
  <section class="card" data-testid="brief">
    <p><strong>The question.</strong> If Wisconsin removed minimum parking requirements for all housing from 1 January 2027, how many more homes would be permitted over 2027–2031?</p>
    <p data-testid="brief-headline"><strong>The answer.</strong> ${num(R.low)} to ${num(R.high)} extra homes permitted in Wisconsin over 2027–2031 (90% range), on top of the ${int(s.baseline_total)} homes expected under current law. The range includes zero: the data can't tell whether removing parking minimums alone adds or removes homes. US places that removed their minimums did not permit measurably more homes in the three years after than similar places that kept them (${signed(W.effect)} permits per 1,000 existing homes per year; likely range ${signed(W.p05)} to ${signed(W.p95)}).</p>
    <p><strong>Lines across the range.</strong> ${s.side_lines.map((x) => `${esc(x.label)}: ${sideValue(x)} ${PK_UNIT}.`).join(" ")} None of them is "the" estimate.</p>
    <p class="small"><strong>How the range is built.</strong> ${esc(R.method)} ${esc(R.coverage)} By year, 2027–2031: ${R.years.map((y) => `${num(y.low)} to ${num(y.high)}`).join("; ")} extra homes permitted.${R.caveat ? ` ${esc(R.caveat)}` : ""}</p>
    <p><strong>Why so small.</strong> Developers keep building parking that renters, buyers and lenders want. In Buffalo, major projects built 79% of the old minimum after it was repealed. In Los Angeles projects that could cut parking, the typical one still built 0.81 spaces per home. Family-size buildings kept nearly all their parking, while studio and one-bedroom buildings dropped about half.</p>
    <p><strong>What it cannot tell you.</strong> Effects beyond three years, effects in places where minimums bind hard, and what a repeal does to rents or parking supply. These are homes in issued building permits, not completed homes.</p>
    <p class="small muted">Run ${esc(b.manifest.run_id)}.</p>
  </section>`;
}

// ---- module -----------------------------------------------------------------------------------
function mount(env: ShellEnv, data: unknown): MountedReform {
  const b = data as ParkingBundle;
  const m = b.manifest;
  return {
    routes: ROUTES,
    defaultPath: "/summary",
    titleSuffix: "Wisconsin parking law",
    statusStrip: `<span><strong>Accepted model</strong> (27 October 2026)</span><span>Run <code data-testid="run-id">${esc(m.run_id)}</code></span><span>Last observed year ${m.dates.last_observed_year}</span><span>Forecast 2027–2031</span><span>Law in effect 1 Jan 2027 (illustrative)</span>`,
    footer: `<p><strong>Outcome:</strong> ${esc(m.outcome.short)}</p>
      <p class="pill-key"><span class="pill pill-observed">Observed</span> counted in a published source. <span class="pill pill-calculated">Calculated</span> computed from observed inputs and stated rules. <span class="pill pill-assumed">Assumed</span> a judgment where no data decide it. A dash (—) means missing, never zero.</p>
      <p class="muted">Run <code>${esc(m.run_id)}</code> · Validation: ${m.validation.passed} checks passed · <a href="${esc(m.repo_url)}" target="_blank" rel="noopener">Source code and documentation<span class="sr-only"> (opens GitHub in a new tab)</span> ↗</a> · Apache-2.0</p>`,
    extra: "",
    bind() { /* nothing to bind */ },
    leave: () => leaveMap(),
    render(path: string, params: URLSearchParams, main: HTMLElement) {
      if (!path.startsWith("/where")) leaveMap();
      if (path.startsWith("/where")) where(b, env, params, main);
      else if (path.startsWith("/how-sure")) howSure(b, env, main);
      else if (path.startsWith("/why")) why(b, main);
      else if (path.startsWith("/pilot")) pilot(b, env, path.split("/")[2] ?? "milwaukee", main);
      else if (path.startsWith("/brief")) brief(b, main);
      else renderSummary(main, summaryInput(b), env, params);
    },
  };
}

export const parkingReform: ReformModule = { load, mount };
