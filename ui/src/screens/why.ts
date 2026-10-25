import { COLORS, DASH, docLink, type Ctx } from "../app";
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

export function renderWhy(ctx: Ctx, main: HTMLElement): void {
  const ev = ctx.b.evidence;
  const card = (c: (typeof ev.cards)[number]) => `<article class="card ev-card ev-${c.kind}">
    <p class="ev-meta">${pill(c.status)} <span class="tag">${esc(TYPE_LABEL[c.type] ?? c.type)}</span></p>
    <h3>${esc(c.title)}</h3>
    <p>${esc(c.text)}</p>
    ${c.table ? `<table class="data small"><caption>${esc(c.table_units ?? "")}</caption><thead><tr><th scope="col">State</th><th scope="col" class="num">Level</th></tr></thead><tbody>${c.table.map((r) => `<tr><th scope="row">${esc(r.state)}</th><td class="num">${dec(r.level)}</td></tr>`).join("")}</tbody></table>` : ""}
    ${c.challenge ? `<p class="challenge"><strong>Challenge this:</strong> ${esc(c.challenge)}</p>` : ""}
    <p class="links">${c.links.map(docLink).join(" · ")}</p></article>`;

  main.innerHTML = `
  <h1>Why these numbers</h1>
  <p class="lede">The evidence behind the model, and the assumptions it makes where Wisconsin has no data. Each card says what kind of evidence it is and links to the full write-up and data on GitHub. Assumption cards carry a question you could put to the model.</p>

  <section aria-labelledby="h-ev"><h2 id="h-ev">Evidence</h2><div class="cards">${ev.cards.filter((c) => c.kind === "evidence").map(card).join("")}</div></section>
  <section aria-labelledby="h-as"><h2 id="h-as">Assumptions you can challenge</h2><div class="cards">${ev.cards.filter((c) => c.kind === "assumption").map(card).join("")}</div></section>

  <section class="card" aria-labelledby="h-sp1">
    <h2 id="h-sp1">Statewide ADU laws: each state, the median, and Wisconsin's scenarios</h2>
    <p class="muted">${esc(ev.spaghetti_states.units)}. ${esc(ev.spaghetti_states.x_label)}. Each grey line is one state's measured area; Maine and Massachusetts have one year so far.</p>
    <div class="chart-box" id="sp-states"></div>
    ${legendHTML([{ name: "One statewide-law state", color: "#7d8682", width: 1.3 }, { name: "California (2017 law)", color: COLORS.ref, width: 1.5 }, { name: "Median across states (California not included)", color: "#2f6db5", width: 4 },
      { name: "Wisconsin: like a typical statewide-law state", color: COLORS.central, width: 3 }, { name: "Wisconsin: like the slower states", color: COLORS.lower, dash: DASH.lower }, { name: "Wisconsin: Strong adoption", color: COLORS.upper, dash: DASH.upper }, { name: "Wisconsin today, no statewide law", color: "#c2272d", dash: "6 3 2 3" }])}
    <details><summary>Show the data</summary>${dataTable(ev.spaghetti_states.lines, "Rates by year since the statewide law, permits per 1,000 single-family homes per year")}</details>
    <p class="links">${docLink(ev.spaghetti_states.png)}</p>
  </section>

  <section class="card" aria-labelledby="h-sp2">
    <h2 id="h-sp2">Madison-like cities under statewide laws, and Madison</h2>
    <p class="muted">${esc(ev.spaghetti_cities.units)}. ${esc(ev.spaghetti_cities.x_label)}.</p>
    <div class="chart-box" id="sp-cities"></div>
    ${legendHTML([{ name: "One Madison-like city (Washington, Oregon, Rhode Island)", color: "#7d8682", width: 1.3 }, { name: "Median of Madison-like cities in Washington and Oregon", color: "#2f6db5", width: 4 },
      { name: "Madison, observed 2021–2025", color: "#c2272d", dash: "6 3 2 3" }, { name: "Madison's adopted path, all scenarios", color: COLORS.central, width: 3 }])}
    <details><summary>Show the data</summary>${dataTable(ev.spaghetti_cities.lines, "Rates by year since the statewide law, permits per 1,000 single-family homes per year")}</details>
    <p class="links">${docLink(ev.spaghetti_cities.png)}</p>
  </section>

  <section class="card" aria-labelledby="h-docs"><h2 id="h-docs">Full documentation</h2><ul class="plain">${ev.docs.map((d) => `<li>${docLink(d)}</li>`).join("")}</ul></section>`;

  spaghetti(main.querySelector("#sp-states")!, ev.spaghetti_states.lines, "ADU permit rates before and after statewide laws, with Wisconsin's scenarios", ev.spaghetti_states.x_label, ev.spaghetti_states.units);
  spaghetti(main.querySelector("#sp-cities")!, ev.spaghetti_cities.lines, "Madison-like cities before and after statewide laws, with Madison", ev.spaghetti_cities.x_label, ev.spaghetti_cities.units);
}
