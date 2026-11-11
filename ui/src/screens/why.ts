import { COLORS, DASH, LAW_TEXT, docLink, type Ctx } from "../app";
import { legendHTML, xyChart, type Series } from "../charts";
import type { Line } from "../data";
import { dec, esc, pill } from "../format";

const TYPE_LABEL: Record<string, string> = { descriptive: "Descriptive", transferred: "Transferred from other states", judgment: "Judgment", "quasi-experimental": "Quasi-experimental" };

function style(kind: string): Partial<Series> & { color: string } {
  switch (kind) {
    case "state": case "city": return { color: "#7d8682", width: 1.3, opacity: 0.55, marker: "circle" };
    case "california": return { color: COLORS.ref, width: 1.5, opacity: 0.8, marker: "circle" };
    case "median": return { color: "#2f6db5", width: 4 };
    case "wi_central": return { color: COLORS.central, width: 3, marker: "square" };
    case "wi_lower": return { color: COLORS.lower, width: 2, dash: DASH.lower };
    case "wi_upper": return { color: COLORS.upper, width: 2, dash: DASH.upper };
    case "wi_today": return { color: "#c2272d", width: 2, dash: "6 3 2 3", marker: "circle" };
    default: return { color: "#999" };
  }
}

function spaghetti(el: HTMLElement, lines: Line[], title: string, xLabel: string, units: string): void {
  const ks = Array.from(new Set(lines.flatMap((l) => l.points.map((p) => p.k)))).sort((a, b) => a - b);
  xyChart(el, {
    title, xTicks: ks, xFormat: (k) => String(k), yLabel: units, yFormat: (y) => y.toFixed(1),
    desc: `${lines.length} lines. ` + lines.filter((l) => l.kind !== "state" && l.kind !== "city").map((l) => `${l.name}: ${l.points.map((p) => `year ${p.k} ${dec(p.rate)}`).join(", ")}`).join(". "),
    vline: { x: 0.5, label: "law takes effect" },
    series: [...lines].sort((a, b) => (a.kind === "state" || a.kind === "city" ? -1 : 0) - (b.kind === "state" || b.kind === "city" ? -1 : 0))
      .map((l) => ({ name: l.name, values: l.points.map((p) => ({ x: p.k, y: p.rate })), ...style(l.kind) })),
  });
  void xLabel;
}

function dataTable(lines: Line[], caption: string): string {
  const ks = Array.from(new Set(lines.flatMap((l) => l.points.map((p) => p.k)))).sort((a, b) => a - b);
  return `<div class="table-wrap"><table class="data small"><caption>${esc(caption)}</caption><thead><tr><th scope="col">Line</th>${ks.map((k) => `<th scope="col" class="num">Year ${k}</th>`).join("")}</tr></thead>
  <tbody>${lines.map((l) => { const m = new Map(l.points.map((p) => [p.k, p.rate])); return `<tr><th scope="row">${esc(l.name)}</th>${ks.map((k) => `<td class="num">${m.has(k) ? dec(m.get(k)!) : ""}</td>`).join("")}</tr>`; }).join("")}</tbody></table></div>`;
}


/** The anchor of the in/out list; the ADU Summary's "What we modeled" card links here (?section=adu-in-out). */
export const ADU_IN_OUT_ID = "adu-in-out";

// The in/out list (owner, 2026-11-11 20:21). The 8 states and their levels come from the bundle (the "What statewide
// ADU laws did elsewhere" card's table); the rest is not in the bundle, so it is kept here, with its sources:
// - Measured area of each state and the five cities: docs/gate3/README.md, "How the central is built" step 1, and
//   docs/gate3/POOLED_MODEL.md (data table, and decisions 5 and 13).
// - Left out: docs/gate3/STATEWIDE_STATES.md, summary table and section 1 "The state list" (the 18 Mercatus states),
//   and POOLED_MODEL.md decision 13 (places not used); the Madison-like cities: evidence card "Cities like Madison
//   after a statewide law" (a sensitivity since AQ-066).
const IN_STATE_AREA: Record<string, string> = {
  California: "457 cities and counties",
  Washington: "its cities, excluding Seattle",
  Maine: "statewide",
  Utah: "reporting cities",
  Massachusetts: "statewide (293 of 351 towns reporting)",
  Vermont: "Chittenden County",
  "Rhode Island": "statewide",
  Oregon: "32 cities, excluding Portland",
};
const IN_CITIES: { name: string; why: string }[] = [
  { name: "Seattle, WA", why: "city ADU rules, then the state law" },
  { name: "Portland, OR", why: "city ADU rules alongside the state law" },
  { name: "Austin, TX", why: "city ADU rules; no state law" },
  { name: "Denver, CO", why: "city ADU rules, then the 2024 state law" },
  { name: "Minneapolis, MN", why: "city ADU rules; no state law" },
];
const OUT_PLACES: { name: string; why: string }[] = [
  { name: "Montana", why: "no state count; one city (Bozeman), one year" },
  { name: "Arizona", why: "no state count; city figures only, one year" },
  { name: "Colorado", why: "no state count; no year after the law yet" },
  { name: "Arkansas", why: "law from 2025; no data yet" },
  { name: "Iowa", why: "law from 2025; no data yet" },
  { name: "New Hampshire", why: "ADUs not counted apart from other homes until 2025" },
  { name: "Connecticut", why: "no ADU count; most towns opted out" },
  { name: "Hawaii", why: "cities need not comply until end of 2026" },
  { name: "Maryland", why: "cities need not comply until October 2026" },
  { name: "Nevada", why: "law from July 2026; no data yet" },
  { name: "Tucson, Spokane, Honolulu, Bozeman, Montgomery County (MD)", why: "city or county proxies, local rules or unverified figures" },
  { name: "11 cities like Madison (WA, OR, RI)", why: "shown on the chart above as a check; not used for the rate" },
];

/** The "In and out of the model" card: the states and cities the ADU rate is learned from, and those left out. */
function inOutHTML(states: string[]): string {
  return `<section class="card in-out" id="${ADU_IN_OUT_ID}" tabindex="-1" aria-labelledby="h-in-out" data-testid="adu-in-out">
    <h2 id="h-in-out">In and out of the model</h2>
    <p class="muted">Where the ADU rate with a statewide law is learned from, and the places we looked at but left out.</p>
    <div class="in-out-cols">
      <div>
        <h3>In the model: ${states.length} states</h3>
        <ul class="plain in-out-list" data-testid="in-states">${states.map((n) => `<li><strong>${esc(n)}</strong>${IN_STATE_AREA[n] ? `: ${esc(IN_STATE_AREA[n])}` : ""}</li>`).join("")}</ul>
        <h3>In the model: ${IN_CITIES.length} cities</h3>
        <ul class="plain in-out-list" data-testid="in-cities">${IN_CITIES.map((c) => `<li><strong>${esc(c.name)}</strong>: ${esc(c.why)}</li>`).join("")}</ul>
        <p class="small muted">The cities help measure what city rules and state laws add; only the ${states.length} states set the statewide level.</p>
      </div>
      <div>
        <h3>Left out: ${OUT_PLACES.length} entries</h3>
        <ul class="plain in-out-list" data-testid="out-places">${OUT_PLACES.map((c) => `<li><strong>${esc(c.name)}</strong>: ${esc(c.why)}</li>`).join("")}</ul>
      </div>
    </div>
    <p class="links">${docLink({ label: "Statewide-law states", path: "docs/gate3/STATEWIDE_STATES.md", url: "https://github.com/mroconnell/housing-challenge-starter-missingmiddleware/blob/main/docs/gate3/STATEWIDE_STATES.md" })} · ${docLink({ label: "Pooled model", path: "docs/gate3/POOLED_MODEL.md", url: "https://github.com/mroconnell/housing-challenge-starter-missingmiddleware/blob/main/docs/gate3/POOLED_MODEL.md" })}</p>
  </section>`;
}

export function renderWhy(ctx: Ctx, main: HTMLElement): void {
  const ev = ctx.b.evidence;
  const wiName = (kind: string) => ev.spaghetti_states.lines.find((l) => l.kind === kind)?.name ?? kind;
  const card = (c: (typeof ev.cards)[number]) => `<article class="card ev-card ev-${c.kind}">
    <p class="ev-meta">${pill(c.status)} <span class="tag">${esc(TYPE_LABEL[c.type] ?? c.type)}</span></p>
    <h3>${esc(c.title)}</h3>
    <p>${esc(c.text)}</p>
    ${c.table ? `<table class="data small"><caption>${esc(c.table_units ?? "")}</caption><thead><tr><th scope="col">State</th><th scope="col" class="num">Level</th></tr></thead><tbody>${c.table.map((r) => `<tr><th scope="row">${esc(r.state)}</th><td class="num">${dec(r.level)}</td></tr>`).join("")}</tbody></table>` : ""}
    ${c.challenge ? `<p class="challenge"><strong>Challenge this:</strong> ${esc(c.challenge)}</p>` : ""}
    <p class="links">${c.links.map(docLink).join(" · ")}</p></article>`;

  // the 8 states, in the bundle's order (highest level first)
  const inStates = ev.cards.find((c) => c.kind === "evidence" && c.table?.length)?.table?.map((r) => r.state) ?? [];
  main.innerHTML = `
  <h1>Why these numbers</h1>
  <p class="lede">The evidence behind the model, and the assumptions it makes where Wisconsin has no data. The two charts show what other states and cities actually permitted before and after a statewide ADU law, with Wisconsin's scenarios on the same scale. Each card says what kind of evidence it is and links to the full write-up and data on GitHub. Assumption cards carry a question you could put to the model.</p>
  <p class="law" data-testid="law-text"><strong>The law.</strong> ${LAW_TEXT}</p>


  <section class="card" aria-labelledby="h-sp1">
    <h2 id="h-sp1">Statewide ADU laws: each state, the median, and Wisconsin's scenarios</h2>
    <p class="muted">${esc(ev.spaghetti_states.units)}. ${esc(ev.spaghetti_states.x_label)}. Each grey line is one state's measured area; Maine and Massachusetts have one year so far.</p>
    <div class="chart-box" id="sp-states"></div>
    ${legendHTML([{ name: "One statewide-law state", color: "#7d8682", width: 1.3 }, { name: "California (2017 law)", color: COLORS.ref, width: 1.5 }, { name: "Median across states (California not included)", color: "#2f6db5", width: 4 },
      { name: wiName("wi_central"), color: COLORS.central, width: 3 }, { name: wiName("wi_lower"), color: COLORS.lower, dash: DASH.lower }, { name: wiName("wi_upper"), color: COLORS.upper, dash: DASH.upper }, { name: "Wisconsin under current law (model baseline for 2027)", color: "#c2272d", dash: "6 3 2 3" }])}
    <details><summary>Show the data</summary>${dataTable(ev.spaghetti_states.lines, "Rates by year since the statewide law, permits per 1,000 single-family homes per year")}</details>
    <p class="links">${docLink(ev.spaghetti_states.png)}</p>
  </section>

  <section class="card" aria-labelledby="h-sp2">
    <h2 id="h-sp2">Cities like Madison under statewide laws, and Madison</h2>
    <p class="muted">${esc(ev.spaghetti_cities.units)}. ${esc(ev.spaghetti_cities.x_label)}.</p>
    <div class="chart-box" id="sp-cities"></div>
    ${legendHTML([{ name: "One city like Madison (Washington, Oregon, Rhode Island)", color: "#7d8682", width: 1.3 }, { name: "Median of cities like Madison in Washington and Oregon", color: "#2f6db5", width: 4 },
      { name: "Madison, observed 2021–2025", color: "#c2272d", dash: "6 3 2 3" }, { name: "Madison's path in the model, all scenarios (being reviewed)", color: COLORS.central, width: 3 }])}
    <details><summary>Show the data</summary>${dataTable(ev.spaghetti_cities.lines, "Rates by year since the statewide law, permits per 1,000 single-family homes per year")}</details>
    <p class="links">${docLink(ev.spaghetti_cities.png)}</p>
  </section>

  ${inOutHTML(inStates)}

  <section aria-labelledby="h-ev"><h2 id="h-ev">Evidence</h2><div class="cards">${ev.cards.filter((c) => c.kind === "evidence").map(card).join("")}</div></section>
  <section aria-labelledby="h-as"><h2 id="h-as">Assumptions you can challenge</h2><div class="cards">${ev.cards.filter((c) => c.kind === "assumption").map(card).join("")}</div></section>

  <section class="card" aria-labelledby="h-docs"><h2 id="h-docs">Full documentation</h2><ul class="plain">${ev.docs.map((d) => `<li>${docLink(d)}</li>`).join("")}</ul></section>`;

  spaghetti(main.querySelector("#sp-states")!, ev.spaghetti_states.lines, "ADU permit rates before and after statewide laws, with Wisconsin's scenarios", ev.spaghetti_states.x_label, ev.spaghetti_states.units);
  spaghetti(main.querySelector("#sp-cities")!, ev.spaghetti_cities.lines, "Cities like Madison before and after statewide laws, with Madison", ev.spaghetti_cities.x_label, ev.spaghetti_cities.units);
}
