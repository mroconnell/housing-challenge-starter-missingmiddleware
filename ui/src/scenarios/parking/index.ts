// The parking requirement reduction reform: seven screens over the bundle written by
// scripts/build_parking_bundle.py. The browser only selects, sums and formats bundle values.
import { legendHTML, xyChart } from "../../charts";
import { createMap, RAMP, WATER, type GeoKind, type MapHandle } from "../../map";
import { dec, esc, int, pill, YEARS } from "../../format";
import type { MountedReform, ReformEntry, ReformModule, Route, ShellEnv } from "../types";

// ---- bundle types --------------------------------------------------------------------------
interface YearRow { year: number; observed?: number; observed_published?: number; baseline_low?: number; baseline?: number; baseline_high?: number; bridge?: boolean; add_central?: number; add_upper?: number }
interface Scen { id: "central" | "upper"; label: string; info: string; additional_total: number; with_law_total: number; rate_per_1000_homes?: number }
interface Statewide {
  years: YearRow[]; baseline_total: number; baseline_low_total: number; baseline_high_total: number; baseline_published_total: number;
  baseline_by_type: { type: string; low: number; central: number; high: number }[]; observed_2021_2025: number;
  scenarios: Scen[]; reference_line: { label: string; value: number; info: string };
}
interface Muni { id: string; name: string; county: string; type: string; homes: number; eligible_homes: number; at_benchmark: boolean; near_benchmark: boolean; baseline: number; add_upper: number }
interface Areas {
  munis: Muni[]; counties: { id: string; name: string; homes: number; baseline: number; add_upper: number }[];
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
}
interface Why {
  places: { place: string; state: string; group: string; year: number; population: number; comparisons: number; before: number; after: number; cmp_before: number; cmp_after: number; effect: number; rewrite: boolean; evidence: string | null; confidence: string | null }[];
  average: Record<"all" | "2plus", { effect: number; p05: number; p95: number }>;
  studies: { case: string; finding: string; status: string; source: string; url: string }[];
  california: { all_units: { effect: number; p05: number; p95: number }; units_2plus: { effect: number; p05: number; p95: number }; jurisdictions: number; text: string; caveats: string };
  north_carolina: string; developer_parking: string; docs: { label: string; url: string }[];
}
interface Pilot { slug: string; id: string; name: string; homes: number; at_benchmark: boolean; baseline: number; add_upper: number; history: { year: number; units_1: number | null; units_2: number | null; units_3_4: number | null; units_5: number | null; adjusted: boolean; split: boolean }[]; rules: { rating: string; date: string | null; summary: string | null }[] }
interface Manifest { run_id: string; title: string; outcome: { short: string; long: string; rate_units: string }; dates: { last_observed_year: number; forecast_years: number[]; effective: string }; vintages: { what: string; vintage: string }[]; validation: { passed: number; failed: number; checks: { check: string; passed: boolean; detail: string }[] }; repo_url: string; inputs: unknown[] }
export interface ParkingBundle { manifest: Manifest; statewide: Statewide; areas: Areas; howsure: HowSure; why: Why; pilots: Pilot[] }

async function load(entry: ReformEntry): Promise<ParkingBundle> {
  const root = `${import.meta.env.BASE_URL}${entry.bundle_root}`;
  const get = async (p: string) => { const r = await fetch(p); if (!r.ok) throw new Error(`${p}: ${r.status}`); return r.json(); };
  const { run_id } = await get(`${root}latest.json`);
  const dir = `${root}${run_id}/`;
  const [manifest, statewide, areas, howsure, why, pilots] = await Promise.all(
    ["manifest", "statewide", "areas", "howsure", "why", "pilots"].map((f) => get(`${dir}${f}.json`)));
  return { manifest, statewide, areas, howsure, why, pilots };
}

// ---- helpers ----------------------------------------------------------------------------------
const C = { baseline: "#4b5450", central: "#17644f", upper: "#7b3fb0", observed: "#4b5450" };
const TYPE_LABEL: Record<string, string> = { "1unit": "1 unit", "2units": "2 units", "3_4units": "3–4 units", "5plus": "5+ units" };
const signed = (v: number, d = 2) => `${v > 0 ? "+" : v < 0 ? "−" : ""}${dec(Math.abs(v), d)}`;
const more = (summary: string, html: string) => `<details class="more"><summary>${esc(summary)}</summary>${html}</details>`;

const ROUTES: Route[] = [
  { path: "/today", label: "Wisconsin today", n: 1 },
  { path: "/compare", label: "Statewide comparison", n: 2 },
  { path: "/where", label: "Where", n: 3 },
  { path: "/how-sure", label: "How sure", n: 4 },
  { path: "/why", label: "Why", n: 5 },
  { path: "/pilot/milwaukee", label: "Pilot examples", n: 6, match: "/pilot" },
  { path: "/brief", label: "Brief", n: 7 },
];

// ---- screens --------------------------------------------------------------------------------
function today(b: ParkingBundle, env: ShellEnv, main: HTMLElement): void {
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
      <p class="tile-note">Each place held at its 2023–2025 average (Milwaukee's apartments: 2023–2024). The range comes from Wisconsin's own five-year swings since 1990.</p></section>
    <section class="tile"><h2 class="tile-label">Places with no parking minimums for housing</h2>
      <p class="tile-num" data-testid="bench-count">${bench.filter((x) => x.rating === "at").length}</p>
      <p class="tile-sub">cities and villages, plus ${bench.filter((x) => x.rating === "near").length} with conditions ${pill("observed")}</p>
      <p class="tile-note">From the Parking Reform Network's reform map. A statewide law adds nothing in these places.</p></section>
  </div>
  <section class="card"><h2>Current-law permits by building size, 2027–2031</h2>
    <div class="table-wrap"><table class="data"><caption class="sr-only">Expected permits under current law by building size</caption>
    <thead><tr><th scope="col">Building size</th><th scope="col" class="num">Low</th><th scope="col" class="num">Central</th><th scope="col" class="num">High</th></tr></thead>
    <tbody>${s.baseline_by_type.map((t) => `<tr><th scope="row">${esc(TYPE_LABEL[t.type] ?? t.type)}</th><td class="num">${int(t.low)}</td><td class="num">${int(t.central)}</td><td class="num">${int(t.high)}</td></tr>`).join("")}</tbody></table></div>
    <p class="small muted">Minimum parking rules matter most for buildings of 2 or more units; houses usually come with parking anyway.</p></section>
  <section class="card"><h2>Places that already have no parking minimums for housing</h2>
    <p>${bench.filter((x) => x.rating === "at").map((x) => `${esc(x.name)}${x.adopted ? ` (${esc(x.adopted.slice(0, 4))})` : ""}`).join(", ")}.</p>
    ${more("Places that removed minimums with conditions", `<p>${bench.filter((x) => x.rating === "near").map((x) => esc(x.name)).join(", ")}. Madison and Milwaukee have partial reforms (downtown and some districts; Madison's 2023 transit overlay) and still require parking elsewhere.</p>`)}
  </section>
  <p><a class="button" href="${env.link("/compare")}">Next: what a statewide law would add →</a></p>`;
}

function compare(b: ParkingBundle, main: HTMLElement): void {
  const s = b.statewide;
  const [cen, up] = s.scenarios;
  main.innerHTML = `
  <h1>A statewide parking law: what it adds</h1>
  <p class="lede">If Wisconsin removed minimum parking requirements for all housing from 1 January 2027 (an illustrative start date), how many more homes would be permitted over 2027–2031 than under current law?</p>
  <div class="tiles tiles-3">
    <section class="tile tile-accent"><h2 class="tile-label">${esc(cen.label)}</h2><p class="tile-num" data-testid="add-central">${int(cen.additional_total)}</p>
      <p class="tile-sub">additional permits, 2027–2031 ${pill("calculated")}</p><p class="tile-note">${esc(cen.info)}</p></section>
    <section class="tile"><h2 class="tile-label">${esc(up.label)}</h2><p class="tile-num" data-testid="add-upper">${int(up.additional_total)}</p>
      <p class="tile-sub">additional permits, 2027–2031 ${pill("calculated")}</p><p class="tile-note">${esc(up.info)}</p></section>
    <section class="tile"><h2 class="tile-label">Current law</h2><p class="tile-num">${int(s.baseline_total)}</p>
      <p class="tile-sub">permits, 2027–2031</p><p class="tile-note">"${esc(up.label)}" would add ${dec((up.additional_total / s.baseline_total) * 100, 0)}% to it.</p></section>
  </div>
  <section class="card"><h2>New homes permitted each year</h2><div class="chart-box" id="pk-chart"></div>
    ${legendHTML([{ name: "Observed", color: C.observed, width: 2 }, { name: "Current law (range shaded)", color: C.baseline, dash: "7 5" }, { name: up.label, color: C.upper, dash: "9 3 2 3" }])}
    <p class="small muted">"${esc(cen.label)}" is identical to current law, so it is not drawn separately.</p>
    <div class="table-wrap"><table class="data" data-testid="compare-table"><caption>Permits per year: current law and with the law</caption>
      <thead><tr><th scope="col">Year</th><th scope="col" class="num">Current law</th><th scope="col" class="num">${esc(cen.label)}</th><th scope="col" class="num">${esc(up.label)}</th></tr></thead>
      <tbody>${s.years.filter((y) => YEARS.includes(y.year)).map((y) => `<tr><th scope="row">${y.year}</th><td class="num">${int(y.baseline)}</td><td class="num">${int((y.baseline ?? 0) + (y.add_central ?? 0))}</td><td class="num">${int((y.baseline ?? 0) + (y.add_upper ?? 0))}</td></tr>`).join("")}
      <tr><th scope="row">2027–2031</th><td class="num">${int(s.baseline_total)}</td><td class="num">${int(cen.with_law_total)}</td><td class="num">${int(up.with_law_total)}</td></tr></tbody></table></div>
    <p class="small muted">${esc(s.reference_line.info)} Yearly rows may not add exactly to the totals because of rounding.</p></section>`;
  const ys = s.years;
  xyChart(document.getElementById("pk-chart")!, {
    title: "New homes permitted each year in Wisconsin", desc: `Observed 2015–2025; current law ${int(s.baseline_total)} over 2027–2031; with the law ${int(cen.with_law_total)} (no measurable change) or ${int(up.with_law_total)} (high end of the evidence).`,
    yLabel: "Permits per year", xTicks: ys.map((y) => y.year),
    xFormat: (x: number) => (window.innerWidth < 600 && (x - 2015) % 4 !== 0 ? "" : String(x)),
    series: [
      { name: "Observed", values: ys.map((y) => ({ x: y.year, y: y.observed ?? null })), color: C.observed, width: 2, marker: "circle" },
      { name: "Current law", values: ys.map((y) => ({ x: y.year, y: y.baseline ?? null })), color: C.baseline, dash: "7 5" },
      { name: up.label, values: ys.map((y) => ({ x: y.year, y: y.add_upper !== undefined ? (y.baseline ?? 0) + y.add_upper : null })), color: C.upper, dash: "9 3 2 3" },
    ],
    band: { name: "Current-law range", lo: ys.map((y) => ({ x: y.year, y: y.baseline_low ?? null })), hi: ys.map((y) => ({ x: y.year, y: y.baseline_high ?? null })), color: C.baseline },
    vline: { x: 2026.5, label: "Law in effect" },
  });
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
  const tot = b.statewide.scenarios[1].additional_total;
  let rows: { name: string; homes: number; baseline: number; add: number; note?: string }[];
  if (level === "municipality") rows = A.munis.filter((m) => !q || m.name.toLowerCase().includes(q)).map((m) => ({ name: `${m.name}, ${m.county}`, homes: m.eligible_homes, baseline: m.baseline, add: m.add_upper, note: m.at_benchmark ? "already has no parking minimums for housing" : m.near_benchmark ? "removed minimums with conditions" : "" }));
  else if (level === "assembly" || level === "senate") rows = A.districts[level].map((d) => ({ name: `${level === "assembly" ? "Assembly" : "Senate"} District ${d.id}`, homes: d.homes, baseline: d.baseline, add: d.add_upper }));
  else rows = A.counties.map((c) => ({ name: c.name, homes: c.homes, baseline: c.baseline, add: c.add_upper }));
  rows.sort((a, z) => (z.add || 0) - (a.add || 0));
  const shown = level === "municipality" && !q ? rows.slice(0, 50) : rows;
  main.innerHTML = `
  <h1>Where the added homes would be</h1>
  <p class="lede">"${esc(b.statewide.scenarios[0].label)}" adds nothing anywhere. "${esc(b.statewide.scenarios[1].label)}" adds the same rate per existing home everywhere except places that already have no parking minimums for housing, so it is largest where most people live. Totals are 2027–2031.</p>
  <form class="card" id="where-form"><fieldset class="seg"><legend>Show by</legend>
    ${[["county", "County"], ["municipality", "City, village or town"], ["assembly", "Assembly district"], ["senate", "Senate district"]].map(([v, l]) => `<label><input type="radio" name="level" value="${v}" ${level === v ? "checked" : ""}> ${l}</label>`).join("")}</fieldset>
    ${level === "municipality" ? `<p><label>Find a place <input type="search" name="q" value="${esc(q)}" data-testid="where-search"></label></p>` : ""}</form>
  <section class="card" aria-labelledby="h-pkmap"><h2 id="h-pkmap">Map: added homes in "${esc(b.statewide.scenarios[1].label)}", 2027–2031</h2>
    <div class="map" id="pk-map" data-testid="parking-map"><div class="map-tip" hidden></div></div>
    <div id="pk-legend"></div>
    <p class="small muted">The map shows the same values as the table below. Boundaries: U.S. Census Bureau cartographic boundary files and Wisconsin Legislative Technology Services Bureau districts.</p></section>
  <div class="table-wrap"><table class="data" data-testid="where-table"><caption>${level === "municipality" && !q ? "The 50 places with the most added homes" : "Added homes"} in "${esc(b.statewide.scenarios[1].label)}", 2027–2031 (statewide total ${int(tot)})</caption>
    <thead><tr><th scope="col">Area</th><th scope="col" class="num">Homes it applies to</th><th scope="col" class="num">Current-law permits</th><th scope="col" class="num">Added (high end)</th></tr></thead>
    <tbody>${shown.map((r) => `<tr><th scope="row">${esc(r.name)}${r.note ? ` <span class="small muted">(${esc(r.note)})</span>` : ""}</th><td class="num">${int(r.homes)}</td><td class="num">${int(r.baseline)}</td><td class="num">${int(r.add)}</td></tr>`).join("")}</tbody></table></div>
  <p class="small muted">"Homes it applies to" is 0 where a place already has no parking minimums for housing. District figures are estimated from where each place's homes sit, an approximation. Towns are included; a case on "How sure" leaves them out. Rows may not add exactly because of rounding.</p>`;
  // map values by geography (ids as in the shared outline files)
  const geoKind: GeoKind = level === "municipality" ? "munis" : level === "assembly" ? "assembly" : level === "senate" ? "senate" : "counties";
  const vals = new Map<string, number | null>();
  const names = new Map<string, string>();
  if (geoKind === "munis") for (const m of A.munis) { vals.set(m.id, m.add_upper); names.set(m.id, `${m.name}, ${m.county}`); }
  else if (geoKind === "counties") for (const c of A.counties) { vals.set(c.id, c.add_upper); names.set(c.id, c.name); }
  else for (const d of A.districts[geoKind as "assembly" | "senate"]) {
    const id = `${geoKind === "assembly" ? "asm" : "sen"}:${d.id}`;
    vals.set(id, d.add_upper); names.set(id, `${geoKind === "assembly" ? "Assembly" : "Senate"} District ${d.id}`);
  }
  const br = quintiles([...vals.values()].filter((v): v is number => v !== null && v > 0));
  const lab = (i: number) => i === 0 ? `under ${int(br[0])}` : i === 4 ? `${int(br[3])} or more` : `${int(br[i - 1])} to ${int(br[i] - 1)}`;
  main.querySelector("#pk-legend")!.innerHTML = `<ul class="legend map-legend" aria-label="Map legend: added homes, five classes with about equal numbers of areas">${RAMP.map((c, i) => `<li><span class="lg-sw" style="background:${c}"></span>${esc(lab(i))}</li>`).join("")}<li><span class="lg-sw" style="background:${WATER}"></span>lakes and outside Wisconsin</li></ul>`;
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
      tip.textContent = `${names.get(id) ?? id}: ${int(vals.get(id) ?? null)} added homes`;
    });
    mapH.setGeography(geoKind);
    mapH.setData(vals, br);
    mapEl.querySelector("canvas")?.setAttribute("aria-label", `Map of added homes by ${level === "municipality" ? "city, village and town" : level}; the same values are in the table below.`);
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

function howSure(b: ParkingBundle, main: HTMLElement): void {
  const H = b.howsure;
  const groups = [...new Set(H.sensitivities.map((x) => x.moves))];
  main.innerHTML = `
  <h1>How sure are we?</h1>
  <p class="lede">The comparison behind this scenario found no measurable effect, so the uncertainty is mostly about how large a small effect could be. Here is what moves the numbers, how stable the finding is, and what rests on data versus judgment.</p>
  ${groups.map((g) => `<section class="card"><h2>Cases that change ${esc(g)}</h2><div class="table-wrap"><table class="data"><caption class="sr-only">${esc(g)}</caption>
    <thead><tr><th scope="col">Case</th><th scope="col" class="num">Permits, 2027–2031</th><th scope="col">What it means</th></tr></thead>
    <tbody>${H.sensitivities.filter((x) => x.moves === g).map((x) => `<tr><th scope="row">${esc(x.case)}</th><td class="num">${int(x.value)}</td><td>${esc(x.description)}</td></tr>`).join("")}</tbody></table></div></section>`).join("")}
  <section class="card"><h2>Is the finding stable?</h2>
    <p>The average effect stays near or below zero however it is cut. Leaving out one state at a time gives ${signed(H.leave_one_state.min)} (without ${esc(H.leave_one_state.min_state)}) to ${signed(H.leave_one_state.max)} (without ${esc(H.leave_one_state.max_state)}) permits per 1,000 existing homes per year.</p>
    <div class="table-wrap"><table class="data"><caption>Average effect, permits per 1,000 existing homes per year</caption>
      <thead><tr><th scope="col">Check</th><th scope="col" class="num">Places</th><th scope="col" class="num">Effect</th><th scope="col" class="num">Likely range</th></tr></thead>
      <tbody>${H.robustness.map((x) => `<tr><th scope="row">${esc(x.check)}</th><td class="num">${x.places}</td><td class="num">${signed(x.effect)}</td><td class="num">${x.p05 === null ? "—" : `${signed(x.p05)} to ${signed(x.p95!)}`}</td></tr>`).join("")}</tbody></table></div>
    <p class="small muted"><strong>Do different kinds of places respond differently?</strong> We tested this by predicting each repeal place from all the others. One average for all places missed by ${dec(H.models.one_average, 2)} permits per 1,000 homes per year on average. Using ${esc(H.models.best)} missed by ${dec(H.models.best_error, 2)}, and splitting places by size missed by ${dec(H.models.best_band, 2)}. The gain was too small to rely on, so one average is used. "Likely range" means 90 times in 100 the true average would fall inside it.</p></section>
  <section class="card"><h2>Does the effect grow over time?</h2>
    <div class="table-wrap"><table class="data"><caption>Effect by year since repeal, permits per 1,000 existing homes per year</caption>
      <thead><tr><th scope="col">Year since repeal</th><th scope="col" class="num">Places</th><th scope="col" class="num">Average</th><th scope="col" class="num">Median place</th></tr></thead>
      <tbody>${H.event_path.map((x) => `<tr><th scope="row">${x.year_since}</th><td class="num">${x.places}</td><td class="num">${signed(x.effect)}</td><td class="num">${signed(x.median)}</td></tr>`).join("")}</tbody></table></div>
    <p class="small muted">No: it drifts lower, though few places reach years 4 and 5. Holding "High end of the evidence" flat to 2031 is generous. This path was computed after the plan was registered and changes no number.</p></section>
  <section class="card"><h2>What rests on data and what on judgment</h2>
    <ul class="plain">${H.trace.map((t) => `<li>${pill(t.status)} <strong>${esc(t.part)}.</strong> ${esc(t.text)}</li>`).join("")}</ul></section>`;
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
      <tbody>${W.places.map((p) => `<tr><th scope="row">${esc(p.place)}, ${esc(p.state)}</th><td>${p.year}</td><td class="num">${dec(p.before)}</td><td class="num">${dec(p.after)}</td><td class="num">${dec(p.cmp_before)} → ${dec(p.cmp_after)} (${p.comparisons})</td><td class="num">${signed(p.effect)}</td><td class="small">${p.group === "main" ? "" : "removed with conditions; not in the average. "}${p.rewrite ? "Whole zoning rewrite at the same time." : ""}</td></tr>`).join("")}</tbody></table></div>`)}</section>
  <section class="card"><h2>A second check: California's transit-area law</h2>
    <p data-testid="why-california">${esc(W.california.text)} Across ${W.california.jurisdictions} California jurisdictions, the change near transit was ${signed(W.california.all_units.effect)} permits per 1,000 existing homes per year (90% range ${signed(W.california.all_units.p05)} to ${signed(W.california.all_units.p95)}); for buildings of 2 or more units, ${signed(W.california.units_2plus.effect)} (${signed(W.california.units_2plus.p05)} to ${signed(W.california.units_2plus.p95)}).</p>
    <p class="small muted">${esc(W.california.caveats)}</p></section>
  <section class="card"><h2>How much parking developers build without a mandate</h2>
    <p data-testid="developer-parking"><strong>${esc(W.developer_parking.split(":")[0])}:</strong>${esc(W.developer_parking.slice(W.developer_parking.indexOf(":") + 1))}</p>
    <ul class="plain">${W.studies.map((s) => `<li>${s.status === "observed" ? pill("observed") : `<span class="pill pill-assumed">Not yet checked</span>`} <strong>${esc(s.case)}.</strong> ${esc(s.finding)} <a href="${esc(s.url)}" target="_blank" rel="noopener">${esc(s.source)}<span class="sr-only"> (opens in a new tab)</span> ↗</a></li>`).join("")}</ul>
    <p class="small muted">"Not yet checked" means read from a summary, not the full paper.</p></section>
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
    <section class="tile"><h2 class="tile-label">Added at the high end of the evidence</h2><p class="tile-num" data-testid="pilot-upper">${int(p.add_upper)}</p><p class="tile-sub">${p.at_benchmark ? "already has no parking minimums for housing, so the law adds nothing" : "\"No measurable change\" adds 0"}</p></section>
  </div>
  <section class="card"><h2>Permits by building size, 2015–2025</h2><div class="table-wrap"><table class="data"><caption class="sr-only">Permits by year and building size</caption>
    <thead><tr><th scope="col">Year</th><th scope="col" class="num">1 unit</th><th scope="col" class="num">2 units</th><th scope="col" class="num">3–4 units</th><th scope="col" class="num">5+ units</th></tr></thead>
    <tbody>${p.history.map((h) => `<tr><th scope="row">${h.year}</th><td class="num">${int(h.units_1)}${h.split ? "†" : ""}</td><td class="num">${int(h.units_2)}${h.split ? "†" : ""}</td><td class="num">${int(h.units_3_4)}${h.adjusted ? "*" : ""}</td><td class="num">${int(h.units_5)}${h.adjusted ? "*" : ""}</td></tr>`).join("")}</tbody></table></div>
    ${p.history.some((h) => h.adjusted) ? `<p class="small muted">* Estimated from the city's property file (year built, one year earlier), because the Census permit file misses most of Milwaukee's apartments. A dash means not available.</p>` : ""}${p.history.some((h) => h.split) ? `<p class="small muted">† The city crosses county lines; its Census total is split between counties by homes, so these are estimates.</p>` : ""}</section>
  <section class="card"><h2>Parking rules on record</h2>${p.rules.length ? `<ul class="plain">${p.rules.map((r) => `<li><strong>${esc(r.rating === "at" ? "Removed for all housing" : r.rating === "plan_only" ? "Recommended in a plan" : r.rating === "near" ? "Removed with conditions" : "Partial reform")}</strong>${r.date ? ` (${esc(r.date)})` : ""}: ${esc(r.summary)}</li>`).join("")}</ul>` : "<p>None recorded.</p>"}
    <p class="small muted">From the Parking Reform Network's reform map (MIT licence), quoted as written. "TDM" is transportation demand management (measures such as transit passes that reduce driving); "C9A" is a Milwaukee downtown zoning district.</p></section>`;
}

function brief(b: ParkingBundle, main: HTMLElement): void {
  const s = b.statewide, [cen, up] = s.scenarios, W = b.why.average.all;
  main.innerHTML = `
  <h1>Brief: a statewide parking law for Wisconsin</h1>
  <section class="card" data-testid="brief">
    <p><strong>The question.</strong> If Wisconsin removed minimum parking requirements for all housing from 1 January 2027, how many more homes would be permitted over 2027–2031?</p>
    <p><strong>The answer.</strong> Probably few or none that we can measure. Current law is expected to permit ${int(s.baseline_total)} homes over 2027–2031. US places that removed their minimums did not permit measurably more homes in the three years after than similar places that kept them (${signed(W.effect)} permits per 1,000 existing homes per year; likely range ${signed(W.p05)} to ${signed(W.p95)}). So "${esc(cen.label)}" adds ${int(cen.additional_total)}. At the high end of the evidence, the law would add ${int(up.additional_total)} permits (${dec((up.additional_total / s.baseline_total) * 100, 0)}% more than current law).</p>
    <p><strong>Why so small.</strong> Developers keep building parking that renters, buyers and lenders want. In Buffalo, stand-alone apartment buildings built more parking than the old minimum after it was repealed; mixed-use projects built less than half.</p>
    <p><strong>What it cannot tell you.</strong> Effects beyond three years, effects in places where minimums bind hard, and what a repeal does to rents or parking supply.</p>
    <p class="small muted">Run ${esc(b.manifest.run_id)}.</p>
  </section>`;
}

// ---- module -----------------------------------------------------------------------------------
function mount(env: ShellEnv, data: unknown): MountedReform {
  const b = data as ParkingBundle;
  const m = b.manifest;
  return {
    routes: ROUTES,
    defaultPath: "/today",
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
      if (path.startsWith("/compare")) compare(b, main);
      else if (path.startsWith("/where")) where(b, env, params, main);
      else if (path.startsWith("/how-sure")) howSure(b, main);
      else if (path.startsWith("/why")) why(b, main);
      else if (path.startsWith("/pilot")) pilot(b, env, path.split("/")[2] ?? "milwaukee", main);
      else if (path.startsWith("/brief")) brief(b, main);
      else today(b, env, main);
    },
  };
}

export const parkingReform: ReformModule = { load, mount };
