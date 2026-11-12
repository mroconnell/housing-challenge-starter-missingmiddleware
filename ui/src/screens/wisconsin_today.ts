// The shared "Wisconsin today" page (route "#/wisconsin-today"), at the shell level like the Introduction (owner,
// 2026-11-11). Section 1 is the shared all-housing baseline under current law, read from the same reference CSVs as
// the Introduction; then all housing in Wisconsin; then one section per reform, in the fixed order ADUs, Middle
// housing, TOD, each reusing that reform's existing "today" content from its own bundle.
//
// Headings: the page has one h1 and an h2 per section; each reform's content is shifted down so its own h1 becomes
// an h3 under the section's h2.
//
// Parking reform is off the tool for now (owner, 2026-11-12), so it has no section here; the last version with one
// is the git tag parking-ui-before-removal-2026-11-12.
import { legendHTML, xyChart } from "../charts";
import type { Bundle } from "../data";
import { esc, int, pct, pill } from "../format";
import { today as todToday } from "../scenarios/tod/screens";
import type { TodBundle } from "../scenarios/tod/types";
import type { ShellEnv } from "../scenarios/types";
import { aduTodayHTML, allHousingHTML, drawAllHousingCharts } from "./today";
import { baselineFromCsv, baselineYearsFromCsv } from "./intro";

/** Each reform's loaded bundle, or null when it could not load (that section then says "not yet available"). */
export interface TodayData { adu: Bundle | null; tod: TodBundle | null }

/** Shift every heading inside `root` down by `by` levels (h1 → h3 with by = 2), keeping attributes and children. */
function demote(root: HTMLElement, by: number): void {
  root.querySelectorAll<HTMLElement>("h1,h2,h3,h4,h5").forEach((h) => {
    const lvl = Math.min(6, Number(h.tagName[1]) + by);
    const n = document.createElement(`h${lvl}`);
    for (const a of [...h.attributes]) n.setAttribute(a.name, a.value);
    while (h.firstChild) n.appendChild(h.firstChild);
    h.replaceWith(n);
  });
}

const NA = (what: string) => `<p class="muted" data-testid="not-available">${esc(what)}: not yet available.</p>`;

export const SECTIONS: { id: "adu" | "middle" | "tod"; title: string }[] = [
  { id: "adu", title: "Accessory dwelling units (ADUs)" },
  { id: "middle", title: "Middle housing" },
  { id: "tod", title: "Transit-oriented density (TOD)" },
];

/** Render the page. `envFor` gives each reform's links and query handling; `params` is the page's query. */
export function renderWisconsinToday(main: HTMLElement, d: TodayData, envFor: (id: string) => ShellEnv, params: URLSearchParams): void {
  const b = baselineFromCsv();
  const by = baselineYearsFromCsv();
  const proj = by.projected.filter((r) => !r.bridge);
  const lastObs = by.observed[by.observed.length - 1];
  main.innerHTML = `
  <article class="wi-today" data-testid="wisconsin-today">
  <h1>Wisconsin today</h1>
  <p class="lede">Where Wisconsin's housing stands now, and how many homes it would permit under current law, before any reform. Then, for each reform, what Wisconsin looks like today on the thing that reform changes.</p>

  <section class="card range-card" aria-labelledby="wt-base-h" data-testid="wt-baseline">
    <h2 id="wt-base-h">Homes permitted under current law, 2027–2031</h2>
    <p class="range-ends"><span class="range-end"><span class="range-end-label">About</span><span class="range-end-num" data-testid="wt-baseline-total">${int(b.central)}</span></span></p>
    <p class="range-unit">homes of all kinds permitted in Wisconsin over 2027–2031 under current law (90% range <span data-testid="wt-baseline-range">${int(b.low)} to ${int(b.high)}</span>)</p>
    <p class="small">This is the shared baseline every reform is compared with. It holds each place at its 2023–2025 average. Its 90% range comes from how far five-year totals strayed from such forecasts in the other 50 states, 1992–2020. ${pill("calculated")}</p>
    <div class="chart-box" id="wt-base-chart"></div>
    ${legendHTML([{ name: "Observed homes permitted (Milwaukee's apartments estimated)", color: "#4b5450", width: 2 }, { name: "Current law (90% range shaded)", color: "#17644f", dash: "7 5" }])}
    <details><summary>Show the data</summary>
      <div class="table-wrap"><table class="data" data-testid="wt-baseline-table"><caption>Homes permitted in Wisconsin, all sizes: observed, then current law with its 90% range</caption>
        <thead><tr><th scope="col">Year</th><th scope="col">Kind</th><th scope="col" class="num">Homes permitted</th><th scope="col" class="num">Low end</th><th scope="col" class="num">High end</th></tr></thead>
        <tbody>${by.observed.map((r) => `<tr><th scope="row">${r.year}</th><td>Observed</td><td class="num">${int(r.value)}</td><td class="num">—</td><td class="num">—</td></tr>`).join("")}
        ${by.projected.map((r) => `<tr><th scope="row">${r.year}</th><td>${r.bridge ? "Current law (bridge year)" : "Current law"}</td><td class="num">${int(r.central)}</td><td class="num">${int(r.low)}</td><td class="num">${int(r.high)}</td></tr>`).join("")}
        <tr><th scope="row">2027–2031</th><td>Current law</td><td class="num">${int(b.central)}</td><td class="num">${int(b.low)}</td><td class="num">${int(b.high)}</td></tr></tbody></table></div>
      <p class="small muted">Sources: reference/housing_baseline_statewide_by_year.csv and reference/housing_baseline_band.csv (shared baseline v4). The five-year ends are the total times the range's two multipliers; yearly rows may not add exactly to them because of rounding. A dash means no range: observed years are counts.</p>
    </details>
  </section>

  <section class="wt-section" aria-labelledby="wt-all-h" data-testid="wt-section-all">
    <h2 class="section-h" id="wt-all-h">All housing in Wisconsin</h2>
    <div id="wt-all">${d.adu ? allHousingHTML(d.adu.state) : NA("All-housing figures")}</div>
  </section>

  ${SECTIONS.map((s) => `<section class="wt-section" aria-labelledby="wt-${s.id}-h" data-testid="wt-section-${s.id}" id="wt-${s.id}">
    <h2 class="section-h" id="wt-${s.id}-h">${esc(s.title)}</h2>
    <div class="wt-body" id="wt-${s.id}-body"></div>
  </section>`).join("")}
  </article>`;

  // Section 1 chart: observed, then current law with its range
  const proj6 = by.projected;
  xyChart(main.querySelector<HTMLElement>("#wt-base-chart")!, {
    title: `Homes permitted in Wisconsin each year, ${by.observed[0].year} to ${proj[proj.length - 1].year}: observed, then current law`,
    desc: `Observed ${by.observed[0].year}–${lastObs.year}: from ${int(Math.min(...by.observed.map((r) => r.value)))} to ${int(Math.max(...by.observed.map((r) => r.value)))} homes a year (${int(lastObs.value)} in ${lastObs.year}). Current law: about ${int(proj[0].central)} a year (90% range ${int(proj[0].low)} to ${int(proj[0].high)}), ${int(b.central)} over 2027–2031. The table below has every value.`,
    yLabel: "Homes permitted per year", xTicks: [...by.observed.map((r) => r.year), ...proj6.map((r) => r.year)],
    xFormat: (x: number) => (window.innerWidth < 600 && (x - by.observed[0].year) % 4 !== 0 ? "" : String(x)),
    series: [
      { name: "Observed", values: by.observed.map((r) => ({ x: r.year, y: r.value })), color: "#4b5450", width: 2, marker: "circle" },
      { name: "Current law", values: [{ x: lastObs.year, y: lastObs.value }, ...proj6.map((r) => ({ x: r.year, y: r.central }))], color: "#17644f", dash: "7 5" },
    ],
    band: { name: "Current-law range", lo: proj6.map((r) => ({ x: r.year, y: r.low })), hi: proj6.map((r) => ({ x: r.year, y: r.high })), color: "#17644f" },
    vline: { x: 2026.5, label: "2027–2031" },
  });
  if (d.adu) drawAllHousingCharts(main.querySelector<HTMLElement>("#wt-all")!, d.adu.state);

  // ADUs: current law, current local rules, recent ADU permits
  const aduEl = main.querySelector<HTMLElement>("#wt-adu-body")!;
  aduEl.innerHTML = d.adu ? aduTodayHTML(d.adu, envFor("adu").link) : NA("ADU figures");

  // Middle housing: recent permits for homes in 2–4 unit buildings (Census, from the shared permits series)
  const midEl = main.querySelector<HTMLElement>("#wt-middle-body")!;
  midEl.innerHTML = d.adu ? middleTodayHTML(d.adu, envFor("middle").link) : NA("Recent 2–4 unit permits");
  if (d.adu) drawMiddleChart(midEl, d.adu);

  // TOD: its own Wisconsin today content (density near stops, the stops and lines that qualify)
  const todEl = main.querySelector<HTMLElement>("#wt-tod-body")!;
  if (d.tod) { todToday(d.tod, envFor("tod"), params, todEl); demote(todEl, 2); } else todEl.innerHTML = NA("TOD figures");
}

/** Middle housing today: homes in 2–4 unit buildings permitted each year (Census Building Permits Survey). */
function middleTodayHTML(b: Bundle, link: (p: string) => string): string {
  const bps = b.state.bps.filter((r) => r["2_4"] !== null);
  const last = bps[bps.length - 1];
  const recent = bps.slice(-5);
  const avg = recent.reduce((a, r) => a + (r["2_4"] ?? 0), 0) / recent.length;
  return `
  <p class="muted">Middle housing here means homes in buildings of 2 to 4 units, the measure the middle housing range uses. These are counted when the building permit is issued.</p>
  <div class="tiles tiles-3">
    <section class="tile tile-accent" aria-labelledby="t-mid-last">
      <h3 id="t-mid-last" class="tile-label">Homes in 2–4 unit buildings permitted in ${last.year}</h3>
      <p class="tile-num" data-testid="wt-middle-last">${int(last["2_4"])}</p>
      <p class="tile-sub">of ${int(last.total)} homes of all sizes (${pct((last["2_4"] ?? 0) / (last.total || 1), 1)}) ${pill("observed")}</p>
      <p class="tile-note">${esc(last.source ?? "")}, ${esc(last.vintage ?? "")}.</p>
    </section>
    <section class="tile" aria-labelledby="t-mid-avg">
      <h3 id="t-mid-avg" class="tile-label">Average a year, ${recent[0].year}–${last.year}</h3>
      <p class="tile-num" data-testid="wt-middle-avg">${int(avg)}</p>
      <p class="tile-sub">homes in 2–4 unit buildings a year ${pill("calculated")}</p>
      <p class="tile-note">The mean of the ${recent.length} years' counts.</p>
    </section>
    <section class="tile" aria-labelledby="t-mid-sf">
      <h3 id="t-mid-sf" class="tile-label">Single-family homes the law would reach</h3>
      <p class="tile-num">${int(b.state.homes.value)}</p>
      <p class="tile-sub">single-family homes ${pill("observed")}</p>
      <p class="tile-note">The middle housing rate is per 1,000 of these homes. ACS 2020–2024.</p>
    </section>
  </div>
  <section class="card" aria-labelledby="h-mid-years">
    <h3 id="h-mid-years">Homes in 2–4 unit buildings permitted each year</h3>
    <div class="chart-box" id="wt-mid-chart"></div>
    ${legendHTML([{ name: "Homes in 2–4 unit buildings permitted", color: "#17644f", kind: "bar" }])}
    <details><summary>Show the data</summary><div class="table-wrap"><table class="data" data-testid="wt-middle-table"><caption>Homes permitted in Wisconsin in 2–4 unit buildings, and their share of all homes permitted, by year</caption>
      <thead><tr><th scope="col">Year</th><th scope="col" class="num">Homes in 2–4 unit buildings</th><th scope="col" class="num">All homes</th><th scope="col" class="num">Share</th></tr></thead>
      <tbody>${bps.map((r) => `<tr><th scope="row">${r.year}</th><td class="num">${int(r["2_4"])}</td><td class="num">${int(r.total)}</td><td class="num">${pct((r["2_4"] ?? 0) / (r.total || 1), 1)}</td></tr>`).join("")}</tbody></table></div></details>
    <p class="small muted">Census Building Permits Survey, state totals, as published (the same series as All housing above). The Census files townhouses, side-by-side duplexes and split-lot homes as 1-unit homes, so these counts miss part of middle housing.</p>
  </section>
  <p><a class="button" href="${link("/summary")}">What a statewide middle housing law would add →</a></p>`;
}

function drawMiddleChart(root: HTMLElement, b: Bundle): void {
  const bps = b.state.bps.filter((r) => r["2_4"] !== null);
  xyChart(root.querySelector<HTMLElement>("#wt-mid-chart")!, {
    title: `Homes in 2–4 unit buildings permitted in Wisconsin, ${bps[0].year} to ${bps[bps.length - 1].year}`,
    desc: `From ${int(Math.min(...bps.map((r) => r["2_4"] ?? Infinity)))} to ${int(Math.max(...bps.map((r) => r["2_4"] ?? 0)))} homes a year. The table below has every value.`,
    yLabel: "Homes per year", xTicks: bps.map((r) => r.year), height: 220,
    bars: { name: "Homes in 2–4 unit buildings", color: "#17644f", values: bps.map((r) => ({ x: r.year, y: r["2_4"] })) },
    series: [],
  });
}
