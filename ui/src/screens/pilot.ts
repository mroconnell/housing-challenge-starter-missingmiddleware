import { COLORS, DASH, pilotBanner, type Ctx } from "../app";
import { legendHTML, xyChart } from "../charts";
import { PATHS, sum } from "../data";
import { dec, esc, int, missing, pill, YEARS } from "../format";

const PROV: Record<string, string> = {
  detached_allowed: "Detached ADU", attached_allowed: "Attached or internal ADU", owner_occupancy: "Owner must live on site",
  occupant_restriction: "Who may live in the ADU", max_size_sqft: "Maximum size (sq ft)", parking_required: "Extra parking spaces required",
  approval_type: "Approval type", approval_pathway: "Approval process", ordinance_status: "Ordinance mentions ADUs", other: "Other",
};
const VAL: Record<string, string> = {
  by_right: "Allowed by right", prohibited: "Prohibited", conditional: "Conditional use (hearing)", ongoing: "Required", none: "None",
  ministerial: "Staff approval, no hearing", discretionary: "Discretionary (hearing)", unknown: "Unknown", mentioned_allowed: "Yes, allows ADUs",
  unmentioned: "Not mentioned", permitted: "Permitted use",
};

export function renderPilot(ctx: Ctx, main: HTMLElement, slug: string): void {
  const p = ctx.b.pilots.find((x) => x.slug === slug) ?? ctx.b.pilots[0];
  const sel = ctx.ui.scenario;
  const base5 = sum(p.base);
  const add5 = (k: (typeof PATHS)[number]) => sum(p.add[k]);
  const obs = p.permits.years;
  const cur = p.rules.filter((r) => r.current);
  const hist = p.rules.filter((r) => !r.current);
  const stage = p.permits.stage === "application" ? "applications" : "issued permits";
  const ruleRow = (r: (typeof p.rules)[number]) => `<tr><th scope="row">${esc(PROV[r.provision] ?? r.provision)}</th><td>${esc(VAL[r.value ?? ""] ?? r.value ?? "—")}</td><td>${r.from ? esc(r.from) : missing("date not coded")}${r.to ? ` to ${esc(r.to)}` : ""}</td><td>${r.source_url ? `<a href="${esc(r.source_url)}" target="_blank" rel="noopener">${esc(r.section ?? "source")}<span class="sr-only"> (opens the ordinance in a new tab)</span> ↗</a>` : esc(r.section ?? "—")}</td><td>${esc(r.retrieved ?? "—")}</td><td>${r.verification === "verified" ? pill("observed") + " checked" : r.verification === "source_lead" ? `<span class="pill pill-assumed">Source lead</span>` : `<span class="pill pill-assumed">Unknown</span>`}</td></tr>`;

  main.innerHTML = `
  <nav class="pilot-tabs" aria-label="Pilot examples">${ctx.b.pilots.map((x) => `<a href="${ctx.link(`/pilot/${x.slug}`)}" ${x.slug === p.slug ? 'aria-current="page"' : ""}>${esc(x.name.replace(/ (city|village)$/, ""))}${x.role === "same_market_check" ? "&nbsp;<span class=\"muted\">(same-market check)</span>" : ""}</a>`).join("")}</nav>
  ${pilotBanner(p.role)}
  <h1>${esc(p.name)}, ${esc(p.county)}</h1>
  <p class="lede">${esc(p.description)}</p>

  <div class="tiles tiles-4">
    <section class="tile"><h2 class="tile-label">Single-family homes</h2><p class="tile-num">${int(p.homes)}</p><p class="tile-sub">one-unit detached homes ${pill("observed")}</p><p class="tile-note">ACS 2020–2024.</p></section>
    <section class="tile"><h2 class="tile-label">Permits today</h2><p class="tile-num">${dec(p.x_rate)}</p><p class="tile-sub">per 1,000 single-family homes per year ${pill(p.x_status)}</p><p class="tile-note">Range ${dec(p.x_low)}–${dec(p.x_high)}. ${esc(ctx.b.areas.x_status_text[p.x_status] ?? "")}${p.x_status === "observed" ? ` (${esc(p.x_basis)})` : ""}.</p></section>
    <section class="tile"><h2 class="tile-label">Baseline, 2027–2031</h2><p class="tile-num" data-testid="pilot-baseline">${int(base5)}</p><p class="tile-sub">permits under current law ${pill("calculated")}</p><p class="tile-note">Range ${int(p.base_low_5yr)}–${int(p.base_high_5yr)}.</p></section>
    <section class="tile tile-accent"><h2 class="tile-label">Added by the law: ${esc(ctx.scen().label)}</h2><p class="tile-num" data-testid="pilot-additional">+${int(add5(sel))}</p><p class="tile-sub">additional permits over 2027–2031 ${pill("calculated")}</p><p class="tile-note">All scenarios: ${PATHS.map((k) => int(add5(k))).join(" / ")}.</p></section>
  </div>

  <section class="card" aria-labelledby="h-rules">
    <h2 id="h-rules">Current ADU rules</h2>
    <p><strong>${esc(ctx.b.areas.class_text[p.current_class] ?? p.current_class)}.</strong> ${p.rights_added_text ? `What the benchmark law would change: ${esc(p.rights_added_text)}` : ""}</p>
    <div class="table-wrap"><table class="data"><caption>Rules in force now, with the ordinance section and the date it was read</caption>
      <thead><tr><th scope="col">Provision</th><th scope="col">Rule</th><th scope="col">In force</th><th scope="col">Source</th><th scope="col">Retrieved</th><th scope="col">Checked?</th></tr></thead>
      <tbody>${cur.map(ruleRow).join("")}</tbody></table></div>
    ${hist.length ? `<details><summary>Earlier rules (${hist.length})</summary><div class="table-wrap"><table class="data"><caption>Rules no longer in force</caption><thead><tr><th scope="col">Provision</th><th scope="col">Rule</th><th scope="col">In force</th><th scope="col">Source</th><th scope="col">Retrieved</th><th scope="col">Checked?</th></tr></thead><tbody>${hist.map(ruleRow).join("")}</tbody></table></div></details>` : ""}
  </section>

  <section class="card" aria-labelledby="h-hist">
    <h2 id="h-hist">Observed permits, then the forecast</h2>
    <p class="muted">${esc(p.permits.label)}, from the city's ${esc(stage)}. Bars are observed counts; hatched bars are provisional. Lines are the model for 2027–2031.${p.measured ? ` In ${esc(p.measured.window)}: ${int(p.measured.permits)} ${p.permits.stage === "application" ? (p.measured.permits === 1 ? "application" : "applications") : (p.measured.permits === 1 ? "permit" : "permits")} over ${dec(p.measured.thousand_home_years, 1)} thousand home-years = ${dec(p.measured.rate)} per 1,000 single-family homes per year.` : ""}</p>
    <p class="summary">Under current law the model expects about ${int(base5)} permits over 2027–2031. With the law, ${esc(ctx.scen().label.toLowerCase())} adds ${int(add5(sel))}${p.slug === "madison" ? " (Madison follows the observed path of Madison-like cities, so all three scenarios are the same)" : `, with ${int(add5("lower"))} to ${int(add5("upper"))} across the scenarios`}.</p>
    <div class="chart-box" id="pilot-chart"></div>
    ${legendHTML([{ name: `Observed ${stage}`, color: COLORS.observed, kind: "bar" }, { name: "Provisional (2026, partial year)", color: COLORS.observed, kind: "hatch" }, { name: "Current law (baseline)", color: COLORS.baseline, dash: DASH.baseline },
      ...PATHS.map((k) => ({ name: `With the law: ${ctx.scen(k).label}`, color: COLORS[k], dash: DASH[k], width: k === sel ? 4 : 2 }))])}
    <div class="grid-obs">
    <div class="table-wrap"><table class="data" data-testid="pilot-observed"><caption>Observed ${esc(stage)}, by year</caption>
      <thead><tr><th scope="col">Year</th><th scope="col" class="num">Second homes (units)</th><th scope="col" class="num">Permits</th><th scope="col">Status</th></tr></thead>
      <tbody>${obs.map((o) => `<tr><th scope="row">${o.year}</th><td class="num">${o.units === null ? missing(o.reason ?? "no record") : int(o.units)}</td><td class="num">${o.permits === null || o.permits === undefined ? "—" : int(o.permits)}</td><td>${o.units === null ? "" : o.status === "provisional" ? `${pill("observed")} provisional, partial year` : pill("observed")}</td></tr>`).join("")}</tbody></table></div>
    <div class="table-wrap"><table class="data" data-testid="pilot-table"><caption>Forecast permits by year (model)</caption>
      <thead><tr><th scope="col">Year</th><th scope="col" class="num">Baseline</th>${PATHS.map((k) => `<th scope="col" class="num">Additional: ${esc(ctx.scen(k).label)}</th>`).join("")}</tr></thead>
      <tbody>${YEARS.map((y, i) => `<tr><th scope="row">${y}</th><td class="num">${dec(p.base[i], 1)}</td>${PATHS.map((k) => `<td class="num">${dec(p.add[k][i], 1)}</td>`).join("")}</tr>`).join("")}</tbody>
      <tfoot><tr><th scope="row">2027–2031</th><td class="num">${dec(base5, 1)}</td>${PATHS.map((k) => `<td class="num" data-testid="pilot-total-${k}">${dec(add5(k), 1)}</td>`).join("")}</tr></tfoot></table></div>
    </div>
    <p class="muted small">Forecast values keep one decimal here so the pilot can be checked by hand against the Gate 3 packet; they are expected values for the whole ${esc(p.name.split(" ").pop() ?? "place")}, not counts for any lot. Source: ${esc(p.permits.source)} and the adopted model run.</p>
  </section>`;

  const years = [...obs.map((o) => o.year), ...YEARS];
  xyChart(main.querySelector("#pilot-chart")!, {
    title: `${p.name}: second-home permits per year, observed and forecast`,
    desc: `Observed ${obs.filter((o) => o.units !== null).map((o) => `${o.year} ${o.units}`).join(", ")}. Forecast 2027–2031 baseline about ${dec(p.base[0], 1)} a year; with the law in 2031: ${PATHS.map((k) => `${ctx.scen(k).label} ${dec(p.base[4] + p.add[k][4], 1)}`).join(", ")}.`,
    yLabel: "Permits per year", xTicks: years, xFormat: (x) => (x % 2 === 0 || x === 2027 ? String(x) : `’${String(x).slice(2)}`),
    vline: { x: 2026.5, label: "law (stylized)" },
    bars: { name: "observed", color: COLORS.observed, values: obs.map((o) => ({ x: o.year, y: o.units, hatch: o.status === "provisional" })) },
    series: [
      { name: "baseline", color: COLORS.baseline, dash: DASH.baseline, values: YEARS.map((y, i) => ({ x: y, y: p.base[i] })) },
      ...PATHS.map((k) => ({ name: k, color: COLORS[k], dash: DASH[k], width: k === sel ? 4 : 2, marker: k === sel ? ("circle" as const) : undefined, values: YEARS.map((y, i) => ({ x: y, y: p.base[i] + p.add[k][i] })) })),
    ],
  });
}
