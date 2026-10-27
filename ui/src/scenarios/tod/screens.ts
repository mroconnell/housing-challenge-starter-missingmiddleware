// The seven TOD screens. Every number comes from the bundle (scripts/build_tod_bundle.py); the browser only selects,
// sorts and formats. Plain language first: each screen opens with what the reader is looking at.
import { legendHTML, xyChart } from "../../charts";
import { dec, esc, int, pill, small } from "../../format";
import type { ShellEnv } from "../types";
import { mapKey, stationMap } from "./map";
import { SCEN_IDS, type AggRow, type Muni, type Pilot, type ScenId, type TodBundle } from "./types";

const YEARS = [2027, 2028, 2029, 2030, 2031];
const C: Record<string, string> = { baseline: "#4b5450", little: "#2f6db5", typical: "#17644f", strong: "#7b3fb0", ref: "#b0501a" };
const DASH: Record<string, string | undefined> = { baseline: "7 5", little: "2 4", typical: undefined, strong: "9 3 2 3", ref: "1 5" };

/** A share: three significant figures from 1% (11.5%, 5.47%), two below (0.055%, 0.8%). */
export function sharePct(v: number): string {
  const p = v * 100;
  if (p === 0) return "0%";
  return `${Number(p.toPrecision(p >= 1 ? 3 : 2)).toLocaleString("en-US", { maximumFractionDigits: 3 })}%`;
}
const more = (summary: string, html: string) => `<details class="more"><summary>${esc(summary)}</summary>${html}</details>`;
const scen = (b: TodBundle, id: ScenId) => b.statewide.scenarios.find((s) => s.id === id)!;
const signed = (v: number, d = 3) => `${v > 0 ? "+" : v < 0 ? "−" : ""}${dec(Math.abs(v), d)}`;
const placeName = (n: string) => n.replace(/ (city|village|town)$/, " ($1)");
const ext = (url: string, label: string) => `<a href="${esc(url)}" target="_blank" rel="noopener">${esc(label)}<span class="sr-only"> (opens in a new tab)</span> ↗</a>`;

// ---- 1. Wisconsin today ------------------------------------------------------------------------
export function today(b: TodBundle, env: ShellEnv, main: HTMLElement): void {
  const s = b.statewide;
  const max = Math.max(...s.ladder.map((l) => l.homes));
  main.innerHTML = `
  <h1>Homes near major transit stops in Wisconsin today</h1>
  <p class="lede">The law would allow taller, denser housing near Wisconsin's busiest transit: rail and bus rapid transit stations, and bus routes that come every 15 minutes. This page shows how many homes are near those stops today, how many new homes are expected there without the law, and which transit lines count. Homes are housing units; new homes are counted when the building permit is issued.</p>
  <div class="tiles tiles-3">
    <section class="tile tile-accent"><h2 class="tile-label">Homes near qualifying stops</h2>
      <p class="tile-num" data-testid="stock-homes">${int(s.stock_homes)}</p>
      <p class="tile-sub">of ${int(s.state_homes)} homes in Wisconsin (${sharePct(s.stock_homes / s.state_homes)}), 2020 census ${pill("observed")}</p>
      <p class="tile-note">Within ½ mile of a rail or rapid transit station, or ¼ mile of a stop on a bus route every 15 minutes (the main case).</p></section>
    <section class="tile"><h2 class="tile-label">New homes expected near these stops under current law, 2027–2031</h2>
      <p class="tile-num" data-testid="baseline-total">${int(s.baseline.total)}</p>
      <p class="tile-sub">homes permitted over five years (range ${int(s.baseline.low_total)}–${int(s.baseline.high_total)}) ${pill("calculated")}</p>
      <p class="tile-note">That is ${sharePct(s.baseline.total / s.state_baseline_total)} of the ${int(s.state_baseline_total)} homes Wisconsin is expected to permit statewide over 2027–2031: each place's expected permits times its share of homes near stops.</p></section>
    <section class="tile"><h2 class="tile-label">Share in the cities of Milwaukee and Madison</h2>
      <p class="tile-num" data-testid="two-cities-share">${sharePct(s.homes_two_cities.share)}</p>
      <p class="tile-sub">${int(s.homes_two_cities.milwaukee)} homes in Milwaukee and ${int(s.homes_two_cities.madison)} in Madison, of the ${int(s.stock_homes)} ${pill("observed")}</p>
      <p class="tile-note">No bus route outside the Milwaukee and Madison areas runs every 15 minutes. The Kenosha streetcar is the one qualifying line elsewhere.</p></section>
  </div>
  <section class="card"><h2>How many homes count as "near a major transit stop"</h2>
    <p>It depends on the definition. From the narrowest to the widest, with the main case in bold:</p>
    <div class="tod-bars" role="img" aria-label="${esc(`Homes near stops by definition, 2020 census: ${s.ladder.map((l) => `${l.label}: ${int(l.homes)}`).join("; ")}. The table below has the same values.`)}">
      ${s.ladder.map((l) => `<div class="tod-bar-row${l.main ? " is-main" : ""}${l.context ? " is-context" : ""}" aria-hidden="true"><span>${esc(l.label)}</span><span class="tod-bar-track"><span class="tod-bar-fill" style="width:${(l.homes / max) * 100}%"></span></span><span class="tod-bar-val">${int(l.homes)}</span></div>`).join("")}
    </div>
    <div class="table-wrap"><table class="data" data-testid="ladder-table"><caption>Homes near stops by definition, narrowest to widest (2020 census)</caption>
      <thead><tr><th scope="col">Definition</th><th scope="col" class="num">Qualifying stops</th><th scope="col" class="num">Homes nearby</th><th scope="col" class="num">Share of Wisconsin's ${int(s.state_homes)} homes</th></tr></thead>
      <tbody>${s.ladder.map((l) => `<tr><th scope="row">${l.main ? `<strong>${esc(l.label)}</strong>` : esc(l.label)}</th><td class="num">${int(l.stops)}</td><td class="num">${int(l.homes)}</td><td class="num">${sharePct(l.share_of_state)}</td></tr>`).join("")}</tbody></table></div>
    <p class="small muted">Stops counted as boarding points (each direction of a street counts once). Rail and rapid transit means The Hop and Kenosha streetcars, CONNECT 1 and Madison's Rapid Route A; Amtrak stations are left out because their service is too infrequent. ${pill("observed")}</p></section>
  <section class="card"><h2>What the modelled law allows near stops</h2>
    <div class="table-wrap"><table class="data" data-testid="law-table"><caption>Minimum height and density the law allows, by distance from the stop</caption>
      <thead><tr><th scope="col">Where</th><th scope="col" class="num">Height</th><th scope="col" class="num">Homes per acre</th><th scope="col" class="num">Floor area ratio</th></tr></thead>
      <tbody>${s.law.map((l) => `<tr><th scope="row">${esc(l.label)}</th><td class="num">${l.height_ft} feet</td><td class="num">${l.homes_per_acre}</td><td class="num">${dec(l.far, 1)}</td></tr>`).join("")}</tbody></table></div>
    <p class="small muted">Taken from California's 2025 transit law (SB 79). Floor area ratio is the building's floor area divided by its lot area. The modelled law does not change parking rules (that is the parking reform) and requires no affordable homes. Where local zoning already allows as much, the law changes nothing.</p></section>
  <section class="card"><h2>The transit lines that qualify</h2>
    <div class="table-wrap"><table class="data" data-testid="agencies-table"><caption>Qualifying stops by transit system (main case unless marked)</caption>
      <thead><tr><th scope="col">Transit system and lines</th><th scope="col" class="num">Rail or rapid stops</th><th scope="col" class="num">15-minute bus stops</th><th scope="col" class="num">20-minute bus stops (wider case only)</th></tr></thead>
      <tbody>${s.agencies.map((a) => `<tr><th scope="row"><strong>${esc(a.agency)}</strong><br><span class="small">${esc(a.lines)}</span></th><td class="num">${int(a.rapid)}</td><td class="num">${int(a.bus15)}</td><td class="num">${int(a.bus20_only)}</td></tr>`).join("")}</tbody></table></div>
    <p class="small muted">Green Bay has no current schedule file, so none of its routes could be tested and none counts. A map of the station areas is on <a href="${env.link("/where")}">Where</a>.</p></section>
  <p><a class="button" href="${env.link("/compare")}">Next: what the law would add →</a></p>`;
}

// ---- 2. Statewide comparison --------------------------------------------------------------------
export function compare(b: TodBundle, env: ShellEnv, main: HTMLElement): void {
  const s = b.statewide;
  const base = s.baseline;
  const typ = scen(b, "typical");
  main.innerHTML = `
  <h1>A statewide transit-oriented density law: what it adds</h1>
  <p class="lede">If Wisconsin allowed taller, denser housing near major transit stops from 1 January 2027 (an illustrative start date), how many more homes would be permitted near those stops over 2027–2031 than under current law? There are three scenarios, each named after the study whose result it uses, because the evidence disagrees by about a hundredfold.</p>
  <div class="note-box" role="note" data-testid="timing-caveat"><p><strong>About timing.</strong> ${esc(s.timing_caveat)}</p></div>
  <div class="tiles tiles-3 tod-scen-tiles">
    ${SCEN_IDS.map((id) => { const x = scen(b, id); return `<section class="tile${id === "typical" ? " tile-accent" : ""}"><h2 class="tile-label">${esc(x.label)}, ${esc(x.evidence)}</h2>
      <p class="tile-num" data-testid="add-${id}">${int(x.additional_total)}</p>
      <p class="tile-sub">extra homes permitted, 2027–2031${x.range_low !== undefined ? ` (range ${int(x.range_low)}–${int(x.range_high)})` : ""} ${pill("calculated")}</p>
      <p class="tile-sub">${sharePct(x.share_of_stock)} of the ${int(s.stock_homes)} homes near stops</p>
      <p class="tile-note">${esc(x.info)}</p></section>`; }).join("")}
  </div>
  <section class="card"><h2>Homes permitted near stops each year</h2>
    <p class="muted">Current law alone (grey, with its range shaded), and current law plus each scenario's extra homes.</p>
    <div class="chart-box" id="tod-chart"></div>
    ${legendHTML([{ name: "Current law (range shaded)", color: C.baseline, dash: DASH.baseline }, ...SCEN_IDS.map((id) => ({ name: `With the law: ${scen(b, id).label.toLowerCase()}`, color: C[id], dash: DASH[id] })), { name: `${s.reference_line.label} (dotted; equals the typical response)`, color: C.ref, dash: DASH.ref, width: 3 }])}
    <div class="table-wrap"><table class="data" data-testid="compare-table"><caption>Homes permitted near major transit stops: current law and the extra homes the law adds</caption>
      <thead><tr><th scope="col">Year</th><th scope="col" class="num">Current law</th>${SCEN_IDS.map((id) => `<th scope="col" class="num">Extra: ${esc(scen(b, id).label.toLowerCase())}</th>`).join("")}</tr></thead>
      <tbody>${base.years.map((y, i) => `<tr><th scope="row">${y.year}</th><td class="num">${int(y.central)}</td>${SCEN_IDS.map((id) => `<td class="num">${int(scen(b, id).by_year[i])}</td>`).join("")}</tr>`).join("")}
      <tr><th scope="row">2027–2031</th><td class="num">${int(base.total)}</td>${SCEN_IDS.map((id) => `<td class="num">${int(scen(b, id).additional_total)}</td>`).join("")}</tr>
      <tr><th scope="row">With the law, 2027–2031</th><td class="num">—</td>${SCEN_IDS.map((id) => `<td class="num">${int(scen(b, id).with_law_total)}</td>`).join("")}</tr></tbody></table></div>
    <p class="small muted">${esc(s.reference_line.info)} Current law near stops is held at each place's 2023–2025 average, so it is flat; its range (${int(base.low_total)}–${int(base.high_total)} over five years) comes from Wisconsin's own five-year swings. The typical response's 2031 dip comes from the build-up measured after the New York rezonings, fixed before the results; a smoothed version is on <a href="${env.link("/how-sure")}">How sure</a>. Yearly rows may not add exactly to the totals because of rounding.</p></section>
  <section class="card"><h2>How big is that?</h2>
    <p data-testid="compare-size">In the typical response, the law adds ${int(typ.additional_total)} homes to the ${int(base.total)} expected near stops under current law: ${sharePct(typ.additional_total / base.total)} more over five years. The little response adds ${sharePct(scen(b, "little").additional_total / base.total)} and the strong response ${sharePct(scen(b, "strong").additional_total / base.total)}.</p>
    <p class="small muted">These are homes in issued building permits, not completed homes, and they are compared with current law in the same places. The scenarios are not a statistical interval: each is what happened in one body of evidence.</p></section>
  <p><a class="button" href="${env.link("/where")}">Next: where the homes would be →</a></p>`;
  const yrs = base.years;
  xyChart(document.getElementById("tod-chart")!, {
    title: "Homes permitted near major transit stops each year, 2027–2031",
    desc: `Current law ${int(base.total)} over 2027–2031. With the law: ${SCEN_IDS.map((id) => `${scen(b, id).label.toLowerCase()} ${int(scen(b, id).with_law_total)}`).join(", ")}. The table below has the same values.`,
    yLabel: "Homes permitted per year", xTicks: YEARS,
    series: [
      { name: "Current law", values: yrs.map((y) => ({ x: y.year, y: y.central })), color: C.baseline, dash: DASH.baseline },
      ...SCEN_IDS.map((id) => ({ name: scen(b, id).label, values: yrs.map((y, i) => ({ x: y.year, y: y.central + scen(b, id).by_year[i] })), color: C[id], dash: DASH[id], marker: "circle" as const })),
      { name: s.reference_line.label, values: yrs.map((y, i) => ({ x: y.year, y: y.central + s.reference_line.by_year[i] })), color: C.ref, dash: DASH.ref, width: 3 },
    ],
    band: { name: "Current-law range", lo: yrs.map((y) => ({ x: y.year, y: y.low })), hi: yrs.map((y) => ({ x: y.year, y: y.high })), color: C.baseline },
  });
}

// ---- 3. Where ------------------------------------------------------------------------------------
type Level = "place" | "county" | "assembly" | "senate";
const LEVELS: [Level, string][] = [["place", "Cities, villages and towns"], ["county", "Counties"], ["assembly", "Assembly districts"], ["senate", "Senate districts"]];
const VIEWS: [string, string][] = [["milwaukee", "Milwaukee area"], ["madison", "Madison area"], ["kenosha", "Kenosha"]];

function scenRadios(b: TodBundle, name: string, current: ScenId): string {
  return `<fieldset class="seg"><legend>Scenario</legend>${SCEN_IDS.map((id) => `<label><input type="radio" name="${name}" value="${id}" ${current === id ? "checked" : ""}> ${esc(scen(b, id).label)}</label>`).join("")}</fieldset>`;
}

export function where(b: TodBundle, env: ShellEnv, params: URLSearchParams, main: HTMLElement): void {
  const sid = (SCEN_IDS.includes(params.get("s") as ScenId) ? params.get("s") : "typical") as ScenId;
  const level = (LEVELS.some(([l]) => l === params.get("level")) ? params.get("level") : "place") as Level;
  const view = VIEWS.some(([v]) => v === params.get("view")) ? params.get("view")! : "milwaukee";
  const sortKey = ["name", "homes", "baseline", "add"].includes(params.get("sort") ?? "") ? params.get("sort")! : "add";
  const dir = params.get("dir") === "asc" ? "asc" : "desc";
  const A = b.areas;
  const sc = scen(b, sid);
  const metroName = Object.fromEntries(A.metros.map((m) => [m.id, m.name]));
  type Row = { name: string; sub?: string; homes?: number; baseline: number; add: number; county?: string; metro?: string; coded?: boolean };
  let rows: Row[];
  let others = 0;
  if (level === "place") rows = A.munis.map((m: Muni) => ({ name: placeName(m.name), county: m.county, metro: metroName[m.metro], homes: m.homes_near, baseline: m.baseline, add: m.add[sid], coded: m.coded }));
  else {
    const src = level === "county" ? A.counties : level === "assembly" ? A.assembly : A.senate;
    rows = src.rows.map((r: AggRow) => ({ name: r.name, baseline: r.baseline, add: r.add[sid] }));
    others = src.total_count - src.rows.length;
  }
  const val = (r: Row) => (sortKey === "name" ? r.name : sortKey === "homes" ? r.homes ?? 0 : sortKey === "baseline" ? r.baseline : r.add);
  rows.sort((a, z) => { const x = val(a), y = val(z); const c = typeof x === "string" ? x.localeCompare(y as string) : (x as number) - (y as number); return dir === "asc" ? c : -c; });
  const cols: [string, string, boolean][] = [["name", level === "place" ? "Place" : level === "county" ? "County" : "District", false]];
  if (level === "place") cols.push(["homes", "Homes near stops", true]);
  cols.push(["baseline", "Current-law permits near stops", true], ["add", `Extra homes (${sc.label.toLowerCase().replace(" response", "")})`, true]);
  const head = cols.map(([k, label, num]) => {
    const on = sortKey === k;
    return `<th scope="col" class="${num ? "num" : ""}"${on ? ` aria-sort="${dir === "asc" ? "ascending" : "descending"}"` : ""}><button type="button" class="sort-btn" id="sort-${k}" data-sort="${k}">${esc(label)}<span class="sort-ind" aria-hidden="true">${on ? (dir === "asc" ? "▲" : "▼") : "↕"}</span></button></th>`;
  });
  if (level === "place") head.splice(1, 0, `<th scope="col">County and area</th>`, `<th scope="col">Zoning</th>`);
  const labels = A.munis.slice(0, 10).map((m) => m.name);
  main.innerHTML = `
  <h1>Where the extra homes would be</h1>
  <p class="lede">Almost every home near a qualifying stop is in the Milwaukee or Madison area, so that is where the law adds homes. The Kenosha streetcar is the one qualifying line elsewhere. Pick a scenario; every table on this page follows it. Totals are 2027–2031.</p>
  <form class="card" id="tod-where-scen">${scenRadios(b, "tod-scen", sid)}</form>
  <section class="card"><h2>Two metro areas and the rest of the state</h2>
    <div class="table-wrap"><table class="data" data-testid="metro-table"><caption>Homes near stops, current-law permits and extra homes by area, 2027–2031</caption>
      <thead><tr><th scope="col">Area</th><th scope="col" class="num">Homes near stops (2020)</th><th scope="col" class="num">Current-law permits near stops</th>${SCEN_IDS.map((id) => `<th scope="col" class="num">${id === sid ? "<strong>" : ""}Extra: ${esc(scen(b, id).label.toLowerCase())}${id === sid ? "</strong>" : ""}</th>`).join("")}</tr></thead>
      <tbody>${A.metros.map((m) => `<tr><th scope="row">${esc(m.name)}<br><span class="small muted">${esc(m.counties.join(", "))}; ${m.places} ${m.places === 1 ? "place" : "places"} with qualifying stops</span></th><td class="num">${int(m.homes_near)}</td><td class="num">${int(m.baseline)}</td>${SCEN_IDS.map((id) => `<td class="num">${int(m.add[id])}</td>`).join("")}</tr>`).join("")}
      <tr><th scope="row">Wisconsin</th><td class="num">${int(A.metros.reduce((a, m) => a + m.homes_near, 0))}</td><td class="num">${int(b.statewide.baseline.total)}</td>${SCEN_IDS.map((id) => `<td class="num">${int(scen(b, id).additional_total)}</td>`).join("")}</tr></tbody></table></div>
    <p class="small muted">Metro areas as the federal government defines them (Milwaukee, Waukesha, Ozaukee and Washington counties; Dane, Columbia, Green and Iowa counties). Homes near stops count the places the model gives homes to; a few homes near stops in other places are left out.</p></section>
  <section class="card"><h2>Station areas on a map</h2>
    <form id="tod-where-view"><fieldset class="seg"><legend>Map area</legend>${VIEWS.map(([v, l]) => `<label><input type="radio" name="tod-view" value="${v}" ${view === v ? "checked" : ""}> ${l}</label>`).join("")}</fieldset></form>
    ${stationMap(b.map, { view, labels, title: `Station areas: ${VIEWS.find(([v]) => v === view)![1]}`, desc: `Shaded circles show land within ½ mile of rail and rapid transit stations and ¼ mile of 15-minute bus stops. Tinted places are those the model gives extra homes. The table below has the numbers by place.` })}
    ${mapKey()}
    <p class="small muted">Stops from the federal National Transit Map. Place outlines are simplified. The map shows where the law would apply, not where homes will be built.</p></section>
  <section class="card"><h2>By place and district</h2>
    <form id="tod-where-level"><fieldset class="seg"><legend>Show by</legend>${LEVELS.map(([l, t]) => `<label><input type="radio" name="tod-level" value="${l}" ${level === l ? "checked" : ""}> ${t}</label>`).join("")}</fieldset></form>
    <div class="table-wrap"><table class="data" data-testid="where-table"><caption>Extra homes, ${esc(sc.label.toLowerCase())}, by ${esc(LEVELS.find(([l]) => l === level)![1].toLowerCase())}, 2027–2031 (statewide total ${int(sc.additional_total)}). Select a column heading to sort.</caption>
      <thead><tr>${head.join("")}</tr></thead>
      <tbody>${rows.map((r) => `<tr><th scope="row">${esc(r.name)}</th>${level === "place" ? `<td>${esc(r.county ?? "")}<br><span class="small muted">${esc(r.metro ?? "")}</span></td><td>${r.coded ? "Coded" : "Estimated"}</td><td class="num">${int(r.homes)}</td>` : ""}<td class="num">${small(r.baseline)}</td><td class="num">${small(r.add)}</td></tr>`).join("")}</tbody></table></div>
    <p class="small muted">${others ? `The other ${others} ${level === "county" ? "counties" : "districts"} have no qualifying stops and are left out. ` : ""}"Coded" means the place's zoning was coded rule by rule (Milwaukee and Madison). "Estimated" means its room for new homes was estimated from existing buildings and scaled down by the ratio measured in the two coded cities. District figures split each place's numbers as its detached homes are split, an approximation. "under 1" means more than zero but less than half a home. Rows may not add exactly because of rounding.</p></section>`;
  const setQ = (k: string, v: string, msg: string) => {
    const q = new URLSearchParams(params);
    q.set(k, v);
    if (k === "level") { q.delete("sort"); q.delete("dir"); }
    env.replaceQuery(q); env.refresh(); env.announce(msg);
  };
  main.querySelectorAll<HTMLInputElement>('input[name="tod-scen"]').forEach((i) => i.addEventListener("change", () => setQ("s", i.value, `Scenario: ${scen(b, i.value as ScenId).label}. Extra homes statewide ${int(scen(b, i.value as ScenId).additional_total)}.`)));
  main.querySelectorAll<HTMLInputElement>('input[name="tod-view"]').forEach((i) => i.addEventListener("change", () => setQ("view", i.value, `Map: ${VIEWS.find(([v]) => v === i.value)![1]}.`)));
  main.querySelectorAll<HTMLInputElement>('input[name="tod-level"]').forEach((i) => i.addEventListener("change", () => setQ("level", i.value, `Table: ${LEVELS.find(([l]) => l === i.value)![1]}.`)));
  main.querySelectorAll<HTMLButtonElement>("button[data-sort]").forEach((btn) => btn.addEventListener("click", () => {
    const k = btn.dataset.sort!;
    const nd = k === sortKey ? (dir === "asc" ? "desc" : "asc") : k === "name" ? "asc" : "desc";
    const q = new URLSearchParams(params);
    q.set("sort", k); q.set("dir", nd);
    env.replaceQuery(q); env.refresh();
    env.announce(`Table sorted by ${btn.textContent!.replace(/[▲▼↕]/g, "").trim()}, ${nd === "asc" ? "ascending" : "descending"}.`);
  }));
}

// ---- 4. How sure ---------------------------------------------------------------------------------
export function howSure(b: TodBundle, env: ShellEnv, main: HTMLElement): void {
  const H = b.howsure;
  const s = b.statewide;
  const cell = (v: number | undefined) => (v === undefined ? `<td class="num">—</td>` : `<td class="num">${int(v)}</td>`);
  const mainRow = `<tr class="muted"><th scope="row">Main result</th><td>As on the other screens.</td><td class="num">${int(H.main_baseline)}</td>${SCEN_IDS.map((id) => cell(scen(b, id).additional_total)).join("")}</tr>`;
  const groupTable = (g: (typeof H.groups)[number]) => {
    const where_ = g.id === "where_homes_land";
    const mm = b.areas.metros;
    return `<section class="card"><h2>${esc(g.label)}</h2>
    <div class="table-wrap"><table class="data" data-testid="sens-${esc(g.id)}"><caption>${esc(g.label)}: homes permitted near stops, 2027–2031</caption>
      <thead><tr><th scope="col">Case</th><th scope="col">What it means</th><th scope="col" class="num">Current law</th>${SCEN_IDS.map((id) => `<th scope="col" class="num">Extra: ${esc(scen(b, id).label.toLowerCase())}</th>`).join("")}${where_ ? `<th scope="col" class="num">Milwaukee metro (typical)</th><th scope="col" class="num">Madison metro (typical)</th>` : ""}</tr></thead>
      <tbody>${where_ ? mainRow.replace("</tr>", `<td class="num">${int(mm[0].add.typical)}</td><td class="num">${int(mm[1].add.typical)}</td></tr>`) : mainRow}${g.rows.map((r) => `<tr><th scope="row">${esc(r.label)}</th><td>${esc(r.text)}${r.id === "ramp_year5_alt" && r.year_2031 ? ` Typical response in 2031: ${int(r.year_2031.typical)} instead of ${int(scen(b, "typical").by_year[4])}.` : ""}</td><td class="num">${int(r.baseline)}</td>${r.id === "typical_range"
        ? `<td class="num">—</td><td class="num">${int(r.add.typical_low)} to ${int(r.add.typical_high)}</td><td class="num">—</td>`
        : SCEN_IDS.map((id) => cell(r.add[id])).join("")}${where_ ? `<td class="num">${r.milwaukee_metro === null ? "—" : int(r.milwaukee_metro)}</td><td class="num">${r.madison_metro === undefined ? "—" : int(r.madison_metro)}</td>` : ""}</tr>`).join("")}</tbody></table></div></section>`;
  };
  const sb = H.scale_benchmarks;
  const ms = H.madison_share;
  main.innerHTML = `
  <h1>How sure are we?</h1>
  <p class="lede">The three scenarios differ about a hundredfold because the studies behind them disagree, not because the model adds noise. This page shows which choices move the numbers, whether the results are believable for Milwaukee and Madison, and which parts rest on data and which on judgment.</p>
  ${H.groups.map(groupTable).join("")}
  <section class="card"><h2>A sizing method that was tested and set aside</h2>
    <p data-testid="per-acre">The model was first sized from the extra homes per acre measured right where cities upzoned. Spread over all the land near Wisconsin's stops, that gave ${int(H.per_acre.add.little)}, ${int(H.per_acre.add.typical)} and ${int(H.per_acre.add.strong)} extra homes over 2027–2031: even the smallest would have taken Madison's apartment permitting above its own record. Upzoning one block partly moves building there from nearby blocks, so block-level gains overstate a city's net gain. Using the per-acre response measured in Madison and Chicago instead gives ${int(H.per_acre.wisconsin_uncapped)}, or ${int(H.per_acre.wisconsin_capped)} if each metro is capped at what 95% of comparable metros have ever permitted. The owner chose citywide net effects instead (decision AQ-050).</p></section>
  <section class="card"><h2>Scale check: could the metros absorb this?</h2>
    <p>Apartment homes (in buildings of 5 or more) permitted per 1,000 existing homes per year, in each scenario's busiest year, current law plus the law's addition, against the metro's own best year.</p>
    <div class="table-wrap"><table class="data" data-testid="scale-table"><caption>Apartment homes permitted per 1,000 existing homes per year, busiest year of 2027–2031</caption>
      <thead><tr><th scope="col">Metro</th><th scope="col" class="num">Current law</th>${SCEN_IDS.map((id) => `<th scope="col" class="num">${esc(scen(b, id).label)}</th>`).join("")}<th scope="col" class="num">The metro's own record</th></tr></thead>
      <tbody>${H.scale.map((m) => `<tr><th scope="row">${esc(m.name)}</th><td class="num">${dec(m.baseline_per_1000, 2)}</td>${SCEN_IDS.map((id) => `<td class="num">${dec(m.peak[id].total_per_1000, 2)} <span class="small muted">(${m.peak[id].year})</span>${m.peak[id].exceeds_own_max ? " <strong>above record</strong>" : ""}</td>`).join("")}<td class="num">${dec(m.own_max, 2)} <span class="small muted">(${m.own_max_year})</span></td></tr>`).join("")}</tbody></table></div>
    <p class="small muted">The highest year any of 79 comparable US metros (500,000 to 2.5 million people, 2000–2025) has recorded is ${esc(sb.observed_max_metro)} in ${sb.observed_max_year}: ${dec(sb.observed_max, 1)} per 1,000. No scenario reaches it; only the strong response beats the two metros' own records. Census Building Permits Survey and housing-unit estimates.</p></section>
  <section class="card"><h2>A check against Madison's own overlay (not set in advance)</h2>
    <p data-testid="madison-share">In 2023 Madison raised allowed density along its transit corridors. Over 2023–2025, the extra homes permitted on the overlay's lots were about ${sharePct(ms.judged.share)} of the ${int(ms.judged.stock)} homes on those lots (likely range ${sharePct(ms.judged.low)} to ${sharePct(ms.judged.high)}; ${sharePct(ms.main.share)} on the narrower main estimate). Over their first three years, the scenarios give ${SCEN_IDS.map((id) => `${sharePct(ms.scenarios[id])} (${scen(b, id).label.toLowerCase()})`).join(", ")} of station-area homes. Madison's range includes zero and all three, so it cannot pick between them.</p>
    <p class="small muted">This comparison was added after the results were known and has no pass rule; the pre-registered Madison test is on <a href="${env.link("/why")}">Why</a>.</p></section>
  <section class="card"><h2>What rests on data and what on judgment</h2>
    <ul class="plain" data-testid="trace">${H.trace.map((t) => `<li>${pill(t.status)} <strong>${esc(t.part)}.</strong> ${esc(t.text)}</li>`).join("")}</ul></section>
  <section class="card"><h2>What the model cannot tell you</h2>
    <ul class="plain">${H.cannot_tell.map((c) => `<li><strong>${esc(c.title)}.</strong> ${esc(c.text)}</li>`).join("")}</ul>
    <p class="small muted">Current law near stops is ${int(s.baseline.total)} homes over 2027–2031 in the main case; the cases above that change it are marked "Current law".</p></section>`;
}

// ---- 5. Why --------------------------------------------------------------------------------------
function ciChart(rows: { label: string; v: number; lo: number; hi: number; color: string }[], aria: string): string {
  const min = Math.min(0, ...rows.map((r) => r.lo)), max = Math.max(...rows.map((r) => r.hi));
  const P = (x: number) => ((x - min) / (max - min)) * 100;
  return `<div class="tod-ci" role="img" aria-label="${esc(aria)}">${rows.map((r) => `<div class="tod-ci-row" aria-hidden="true"><span>${esc(r.label)}</span><span class="tod-ci-track"><span class="tod-ci-zero" style="left:${P(0)}%"></span><span class="tod-ci-range" style="left:${P(r.lo)}%;width:${P(r.hi) - P(r.lo)}%;background:${r.color}"></span><span class="tod-ci-pt" style="left:${P(r.v)}%;background:${r.color}"></span></span></div>`).join("")}</div>`;
}

export function why(b: TodBundle, main: HTMLElement): void {
  const W = b.why;
  const M = W.madison;
  const fmtCI = (v: number | null, lo: number | null, hi: number | null) => (v === null ? "—" : `${signed(v)} <span class="small muted">(${lo === null ? "—" : signed(lo)} to ${hi === null ? "—" : signed(hi)})</span>`);
  main.innerHTML = `
  <h1>Why: the evidence</h1>
  <p class="lede">No US state has passed a transit-oriented density law long enough ago to measure. So the size of each scenario comes from three studies of whole cities that upzoned, and where the homes go comes from comparisons of rezoned and nearby land in US cities. A test in Madison checked the second part.</p>
  <section class="card"><h2>The three studies behind the scenarios</h2>
    <div class="tod-studies">${W.sources.map((x) => `<div class="card"><h3>${esc(scen(b, x.scenario).label)}: ${esc(x.study)}</h3><p>${esc(x.finding)}</p><p class="small">${pill(x.status)} ${ext(x.url, x.citation)}</p><p class="small muted">Used as ${sharePct(scen(b, x.scenario).share_of_stock)} of station-area homes over five years.</p></div>`).join("")}</div>
    <p class="small muted">Each result is a whole city's net gain, after building moved from elsewhere in the city. Los Angeles's and Auckland's are divided by the share of the city their reform covered, so they apply per home in an upzoned area. Stacy and others did not measure coverage, so theirs is used as published. Every figure was checked against the original paper.</p></section>
  <section class="card"><h2>The Madison test: prediction against what happened</h2>
    <p data-testid="madison-test">Before counting any Madison permit, the model predicted that Madison's 2023 transit overlay would add ${dec(M.prediction.value, 2)} homes per acre of eligible overlay land per year (likely range ${dec(M.prediction.low, 2)} to ${dec(M.prediction.high, 2)}). Measured over 2023–2025 against nearby land that was not rezoned, it added ${signed(M.measured.value, 2)} (likely range ${signed(M.measured.low, 2)} to ${signed(M.measured.high, 2)}). The prediction lies inside the measured range, so the test ${M.confirmed ? "passes" : "fails"} the rule written in advance, but only weakly: the measured range also includes zero, and the measured value is about a third of the prediction. This test checked the method that now decides where homes go, not the size of the statewide total.</p>
    ${ciChart([{ label: "Predicted before counting", v: M.prediction.value, lo: M.prediction.low, hi: M.prediction.high, color: C.strong }, { label: "Measured, 2023–2025", v: M.measured.value, lo: M.measured.low, hi: M.measured.high, color: C.typical }],
      `Predicted ${dec(M.prediction.value, 2)} (${dec(M.prediction.low, 2)} to ${dec(M.prediction.high, 2)}) and measured ${signed(M.measured.value, 2)} (${signed(M.measured.low, 2)} to ${signed(M.measured.high, 2)}) extra homes per acre per year; the vertical line is zero.`)}
    <h3>Homes permitted per acre each year, rezoned land and nearby land</h3>
    <div class="chart-box" id="tod-madison-chart"></div>
    ${legendHTML([{ name: "Overlay land whose allowed density rose", color: C.typical }, { name: "Nearby land with no zoning change (within ¼ mile)", color: C.baseline, dash: DASH.baseline }])}
    <div class="table-wrap"><table class="data" data-testid="madison-years"><caption>Madison: homes permitted by year on rezoned and nearby land (homes, and homes per acre)</caption>
      <thead><tr><th scope="col">Year</th><th scope="col">Period</th><th scope="col" class="num">Rezoned land: homes</th><th scope="col" class="num">per acre</th><th scope="col" class="num">Nearby land: homes</th><th scope="col" class="num">per acre</th></tr></thead>
      <tbody>${M.years.map((y) => `<tr><th scope="row">${y.year}</th><td>${y.period.startsWith("shown") ? "partial year, shown only" : esc(y.period)}</td><td class="num">${int(y.treatment.units)}</td><td class="num">${dec(y.treatment.rate, 2)}</td><td class="num">${int(y.comparison.units)}</td><td class="num">${dec(y.comparison.rate, 2)}</td></tr>`).join("")}</tbody></table></div>
    <p class="small muted">Rezoned land: ${int(M.years[0].treatment.acres)} eligible acres; nearby land: ${int(M.years[0].comparison.acres)} acres. Each area has only a handful of projects a year, so one building moves a year a lot. Rapid Route A opened in September 2024. The test was registered before counting (the order is in the commit history).</p></section>
  <section class="card"><h2>Comparison cases: extra homes per acre after rezoning</h2>
    <div class="table-wrap"><table class="data" data-testid="cases-table"><caption>Extra homes permitted per acre of eligible land per year, rezoned land against nearby land (likely range in brackets)</caption>
      <thead><tr><th scope="col">Case</th><th scope="col">Role</th><th scope="col" class="num">Extra homes per acre per year</th><th scope="col" class="num">Per 1.0 of added floor area ratio</th><th scope="col">Parking minimums</th><th scope="col">Affordability mandate</th></tr></thead>
      <tbody>${W.cases.map((c) => `<tr><th scope="row">${esc(c.name)}</th><td>${esc(c.role_label)}${c.status && c.status !== "measured" ? `<br><span class="small muted">${esc(c.status.split(":")[0].replace(/_/g, " "))}</span>` : ""}</td><td class="num">${fmtCI(c.estimate, c.low, c.high)}</td><td class="num">${fmtCI(c.per_far, c.per_far_low, c.per_far_high)}</td><td>${esc(c.parking ?? "—")}</td><td>${esc(c.mandate ?? "—")}</td></tr>`).join("")}</tbody></table></div>
    <p class="small muted">These measure the effect right where land was rezoned, which counts building pulled from nearby blocks as new. That is why they now only decide where homes go within Wisconsin, not how many. Chicago was held out: its effect per added floor area (${signed(W.cases.find((c) => c.id.startsWith("chicago"))?.per_far ?? 0, 2)}) is close to Madison's measured ${signed(M.per_far.measured, 2)}.</p></section>
  <section class="card"><h2>How the policies were classified</h2>
    <p data-testid="classification">${W.classification.length} transit-oriented reforms were rated against the benchmark: a plain height or floor-area increase, approved by right, with no affordability mandate. ${int(W.strength_counts.strong ?? 0)} were strong, ${int(W.strength_counts.medium ?? 0)} medium and ${int(W.strength_counts.weak ?? 0)} weak (most weak ones bundled an affordability mandate). Parking cuts were recorded but did not lower a rating.</p>
    ${more(`All ${W.classification.length} reforms`, `<div class="table-wrap"><table class="data" data-testid="classification-table"><caption>Transit-oriented reforms and how they were rated</caption>
      <thead><tr><th scope="col">Place and reform</th><th scope="col">Strength</th><th scope="col">Permit data</th><th scope="col">Parking cut</th><th scope="col">Mandate</th><th scope="col">Use here</th></tr></thead>
      <tbody>${W.classification.map((c) => `<tr><th scope="row"><strong>${esc(c.city)}</strong><br><span class="small">${esc(c.reform)}</span></th><td>${esc(c.strength)}</td><td>${esc(c.data)}</td><td>${esc(c.parking)}</td><td>${esc(c.mandate)}</td><td class="small">${esc(c.use)}</td></tr>`).join("")}</tbody></table></div>
      <p class="small muted">Permit data: A = permits with dates and unit counts by lot, and the rezoned boundary, both open; B = one of the two missing; C = a published study only.</p>`)}</section>
  <p class="small">${W.docs.map((d) => ext(d.url, d.label)).join(" · ")}</p>`;
  xyChart(document.getElementById("tod-madison-chart")!, {
    title: "Madison: homes permitted per acre per year, overlay land and nearby land, 2017–2026",
    desc: "The overlay took effect in 2023. 2026 is a partial year. The table below has the same values.",
    yLabel: "Homes per acre per year", xTicks: M.years.map((y) => y.year), yFormat: (v) => dec(v, 1),
    series: [
      { name: "Rezoned land", values: M.years.map((y) => ({ x: y.year, y: y.treatment.rate })), color: C.typical, marker: "circle" },
      { name: "Nearby land", values: M.years.map((y) => ({ x: y.year, y: y.comparison.rate })), color: C.baseline, dash: DASH.baseline, marker: "square" },
    ],
    vline: { x: 2022.5, label: "Overlay in effect" },
  });
}

// ---- 6. Pilot examples ---------------------------------------------------------------------------
export function pilot(b: TodBundle, env: ShellEnv, slug: string, main: HTMLElement): void {
  const p: Pilot = b.pilots.find((x) => x.slug === slug) ?? b.pilots[0];
  const nav = `<nav aria-label="Pilot examples"><p>${b.pilots.map((x) => x.slug === p.slug ? `<strong aria-current="page">${esc(x.title)}</strong>` : `<a href="${env.link(`/pilot/${x.slug}`)}">${esc(x.title)}</a>`).join(" · ")}</p></nav>`;
  const banner = `<p class="banner banner-pilot"><strong>Pilot example, not a statewide result.</strong> Pilot pages show how the statewide model plays out in one place. Their figures are already inside the Wisconsin totals and are never added to them.</p>`;
  const stops = Object.entries(p.stops).map(([k, v]) => `${int(v)} ${esc(k)} stops`).join(", ");
  const rng = (o: Record<ScenId, number>) => `${scen(b, "little").label.toLowerCase()} ${int(o.little)}, strong ${int(o.strong)}`;
  if (p.corridor) {
    const c = p.corridor;
    const labels = c.places.map((x) => x.name);
    main.innerHTML = `
    <h1>${esc(p.title)}</h1>
    ${nav}${banner}
    <p class="lede">${esc(p.intro)}</p>
    <div class="tiles tiles-3">
      <section class="tile tile-accent"><h2 class="tile-label">Extra homes near the corridor's stations, 2027–2031</h2>
        <p class="tile-num" data-testid="pilot-corridor-typical">${int(c.add.typical)}</p>
        <p class="tile-sub">typical response (${rng(c.add)}) ${pill("calculated")}</p>
        <p class="tile-note">Each place's extra homes, times the corridor's share of the room the law adds in that place.</p></section>
      <section class="tile"><h2 class="tile-label">Extra homes near all qualifying stops in ${esc(placeName(p.city))}</h2>
        <p class="tile-num" data-testid="pilot-city-typical">${int(p.city_add.typical)}</p>
        <p class="tile-sub">typical response (${rng(p.city_add)}) ${pill("calculated")}</p></section>
      <section class="tile"><h2 class="tile-label">Current-law permits near stops in ${esc(placeName(p.city))}, 2027–2031</h2>
        <p class="tile-num" data-testid="pilot-baseline">${int(p.city_baseline)}</p>
        <p class="tile-sub">of ${int(p.city_homes_near)} homes near stops, out of ${int(p.city_homes)} in the city (2020) ${pill("calculated")}</p></section>
    </div>
    <section class="card"><h2>The corridor</h2>
      <p>${esc(p.line)}: ${stops}.</p>
      ${stationMap(b.map, { view: p.view, labels, emphasizeRapid: true, title: `${p.title}: station areas`, desc: `Purple circles are land within ½ mile of the corridor's stations; green circles are ¼ mile from 15-minute bus stops. The tables below have the numbers.` })}
      ${mapKey()}</section>
    <section class="card"><h2>Land near the corridor's stations</h2>
      <div class="table-wrap"><table class="data" data-testid="pilot-places"><caption>Land within ½ mile of the corridor's stations, by place, and its share of each place's extra homes (typical response, 2027–2031)</caption>
        <thead><tr><th scope="col">Place</th><th scope="col" class="num">Acres</th><th scope="col" class="num">Acres where the law adds room</th><th scope="col" class="num">Existing homes</th><th scope="col" class="num">Share of the place's extra homes</th><th scope="col" class="num">Extra homes</th></tr></thead>
        <tbody>${c.places.map((x) => `<tr><th scope="row">${esc(placeName(x.name))}<br><span class="small muted">${x.coded ? `zoning coded${x.overlay_share ? `; ${sharePct(x.overlay_share)} of this land is in Madison's 2023 overlay` : ""}` : "room estimated"}</span></th><td class="num">${int(x.acres)}</td><td class="num">${int(x.eligible_acres)}</td><td class="num">${int(x.existing_homes)}</td><td class="num">${sharePct(x.share_of_place)}</td><td class="num">${small(x.add_typical)}</td></tr>`).join("")}
        <tr><th scope="row">Corridor</th><td class="num">${int(c.acres)}</td><td class="num">—</td><td class="num">${int(c.existing_homes)}</td><td class="num">—</td><td class="num">${int(c.add.typical)}</td></tr></tbody></table></div>
      <p class="small muted">${esc(p.zoning_note ?? "")} Existing homes are counted from parcel records, so they differ slightly from the census count used elsewhere.</p></section>
    <section class="card"><h2>Extra homes near the corridor by year</h2>
      <div class="table-wrap"><table class="data" data-testid="pilot-years"><caption>Extra homes permitted near the corridor's stations by year and scenario</caption>
        <thead><tr><th scope="col">Scenario</th>${YEARS.map((y) => `<th scope="col" class="num">${y}</th>`).join("")}<th scope="col" class="num">2027–2031</th></tr></thead>
        <tbody>${SCEN_IDS.map((id) => `<tr><th scope="row">${esc(scen(b, id).label)}</th>${c.add_years[id].map((v) => `<td class="num">${small(v)}</td>`).join("")}<td class="num">${int(c.add[id])}</td></tr>`).join("")}</tbody></table></div>
      <p class="small muted">${esc(b.statewide.timing_caveat)}</p></section>`;
    return;
  }
  main.innerHTML = `
  <h1>${esc(p.title)}</h1>
  ${nav}${banner}
  <p class="lede">${esc(p.intro)}</p>
  <div class="tiles tiles-3">
    <section class="tile"><h2 class="tile-label">Homes near qualifying stops</h2>
      <p class="tile-num" data-testid="pilot-homes-near">${int(p.city_homes_near)}</p>
      <p class="tile-sub">of ${int(p.city_homes)} homes in the city (2020) ${pill("observed")}</p></section>
    <section class="tile tile-accent"><h2 class="tile-label">Extra homes from the law, 2027–2031</h2>
      <p class="tile-num" data-testid="pilot-eau-claire-add">${int(p.city_add.typical)}</p>
      <p class="tile-sub">in every scenario ${pill("calculated")}</p></section>
    <section class="tile"><h2 class="tile-label">Homes Eau Claire is expected to permit anyway, 2027–2031</h2>
      <p class="tile-num" data-testid="pilot-baseline-all">${int(p.city_baseline_all)}</p>
      <p class="tile-sub">all homes in the city under current law ${pill("calculated")}</p></section>
  </div>
  <div class="note-box" role="note" data-testid="pilot-reason"><p><strong>Why zero.</strong> ${esc(p.reason ?? "")}</p></div>
  <section class="card"><h2>Eau Claire's bus stops</h2>
    <p>${stops}. If the law counted buses every 20 minutes, ${int(p.homes_near_high)} Eau Claire homes (${sharePct((p.homes_near_high ?? 0) / p.city_homes)}) on about ${int(p.high_case_acres)} acres would be near a qualifying stop. The statewide effect of that wider definition is on <a href="${env.link("/how-sure")}">How sure</a>.</p>
    ${stationMap(b.map, { view: p.view, labels: ["Eau Claire city"], showWide: true, title: "Eau Claire: stops on 20-minute bus routes", desc: `Brown circles show land within ¼ mile of stops on Eau Claire's 20-minute routes, which count only under the wider definition. No stop qualifies in the main case.` })}
    ${mapKey(true)}
    <p class="small muted">The lesson for other mid-size Wisconsin cities: a law tied to 15-minute service reaches only places that already run it. No bus route outside the Milwaukee and Madison areas was found to run every 15 minutes (Green Bay's schedule could not be tested).</p></section>`;
}

// ---- 7. Brief --------------------------------------------------------------------------------------
export function brief(b: TodBundle, main: HTMLElement): void {
  const s = b.statewide, A = b.areas, H = b.howsure;
  const typ = scen(b, "typical"), lit = scen(b, "little"), str = scen(b, "strong");
  const top = A.munis.slice(0, 6);
  main.innerHTML = `
  <div class="brief-tools no-print">
    <p>A one-page summary for a hearing or a colleague, with the same numbers and run id as the tool.</p>
    <button type="button" class="button" id="tod-print">Print or save as PDF</button>
  </div>
  <article class="brief tod-brief" aria-labelledby="tod-brief-h" data-testid="brief">
    <header class="brief-head">
      <p class="eyebrow">Policy brief · Wisconsin · transit-oriented density</p>
      <h1 id="tod-brief-h">A statewide transit-oriented density law could add about ${int(typ.additional_total)} homes permitted near major transit stops over 2027–2031</h1>
      <p class="brief-sub">On top of about ${int(s.baseline.total)} expected there without the law. Scenarios: ${int(lit.additional_total)} (little response) to ${int(str.additional_total)} (strong response).</p>
    </header>
    <h2>What the law does</h2>
    <p>It allows at least ${s.law.map((l) => `${l.height_ft} feet and ${l.homes_per_acre} homes per acre ${esc(l.label.charAt(0).toLowerCase() + l.label.slice(1))}`).join("; ")}. It covers ${int(s.stock_homes)} of Wisconsin's ${int(s.state_homes)} homes (${sharePct(s.stock_homes / s.state_homes)}), ${sharePct(s.homes_two_cities.share)} of them in the cities of Milwaukee and Madison. Parking rules and affordability requirements are unchanged.</p>
    <h2>The numbers</h2>
    <div class="table-wrap"><table class="data" data-testid="brief-table"><caption>Homes permitted near major transit stops, 2027–2031</caption>
      <thead><tr><th scope="col">Scenario</th><th scope="col">Evidence</th><th scope="col" class="num">Extra homes</th><th scope="col" class="num">Total with current law</th></tr></thead>
      <tbody><tr><th scope="row">Current law</th><td>Each place's 2023–2025 permits, share near stops</td><td class="num">—</td><td class="num">${int(s.baseline.total)}</td></tr>
      ${SCEN_IDS.map((id) => { const x = scen(b, id); return `<tr><th scope="row">${esc(x.label)}</th><td>${esc(x.evidence.charAt(0).toUpperCase() + x.evidence.slice(1))}</td><td class="num">${int(x.additional_total)}</td><td class="num">${int(x.with_law_total)}</td></tr>`; }).join("")}</tbody></table></div>
    <p class="small">Typical response by year, 2027–2031: ${typ.by_year.map((v) => int(v)).join(", ")}. Its range is ${int(typ.range_low)} to ${int(typ.range_high)}. These are homes in issued permits, not completed homes.</p>
    <h2>Where</h2>
    <p>${A.metros.map((m) => `${esc(m.name)} ${int(m.add.typical)}`).join("; ")} (typical response). By place: ${top.map((m) => `${esc(m.name.replace(/ (city|village|town)$/, ""))} ${int(m.add.typical)}`).join(", ")}. Eau Claire and other mid-size cities get none: they have no bus route every 15 minutes.</p>
    <h2>Why these numbers</h2>
    <p>Each scenario uses a study of a whole city's net gain after upzoning: Los Angeles's transit program (little), the average of loosening reforms in 1,136 US cities (typical), Auckland's 2016 upzoning (strong). Measuring only right where land was rezoned would give ${int(H.per_acre.add.little)} to ${int(H.per_acre.add.strong)}, more than Milwaukee and Madison have ever permitted, because upzoning partly moves building from nearby blocks.</p>
    <h2>What it cannot tell you</h2>
    <p>${esc(s.timing_caveat)} The sizing has no Wisconsin test of its own. The model does not cover rents, displacement, ridership, or the law combined with parking reform, and it predicts nothing for any single lot.</p>
    <p class="small muted brief-foot">Run ${esc(b.manifest.run_id)} · ${esc(b.manifest.outcome.short)} · ${esc(b.manifest.repo_url)}</p>
  </article>`;
  document.getElementById("tod-print")!.addEventListener("click", () => window.print());
}
