import { COLORS, DASH, details, pilotBanner, scenKey, scenPhrase, scenShort, type Ctx } from "../app";
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
  const prov = obs.find((o) => o.status === "provisional" && o.units !== null);
  const provWhen = p.provisional_through ? `1 January to ${p.provisional_through}` : "partial year";
  const with2027 = p.base[0] + p.add[sel][0];
  // Madison only: its neighbours' with-law rates (Dane County places over 2,000 homes), for the note
  const rate5 = (a: { base: number[]; add: Record<string, number[]>; homes: number }) => ((sum(a.base) + sum(a.add[sel])) / a.homes / 5) * 1000;
  const nbrs = p.note ? ctx.b.areas.munis.filter((a) => a.county === p.county && a.homes > 2000 && a.id !== p.area_id).sort((a, b) => rate5(a) - rate5(b)) : [];
  const ruleRow = (r: (typeof p.rules)[number]) => `<tr><th scope="row">${esc(PROV[r.provision] ?? r.provision)}</th><td>${esc(VAL[r.value ?? ""] ?? r.value ?? "—")}</td><td>${r.from ? esc(r.from) : missing("date not coded")}${r.to ? ` to ${esc(r.to)}` : ""}</td><td>${r.source_url ? `<a href="${esc(r.source_url)}" target="_blank" rel="noopener">${esc(r.section ?? "source")}<span class="sr-only"> (opens the ordinance in a new tab)</span> ↗</a>` : esc(r.section ?? "—")}</td><td>${esc(r.retrieved ?? "—")}</td><td>${r.verification === "verified" ? `<span class="pill pill-observed">Checked</span>` : r.verification === "source_lead" ? `<span class="pill pill-assumed">Source lead</span>` : `<span class="pill pill-assumed">Unknown</span>`}</td></tr>`;

  const intro = ctx.b.manifest.pilot_intro;
  const L = ctx.b.state.labels;
  const bo2026 = ctx.b.uncertainty.baseline_only.find((x) => x.id === "madison-2026");
  const addRate = (a: { add: Record<string, number[]>; homes: number }) => (sum(a.add[sel]) / a.homes / 5) * 1000;
  const nbrsAdd = [...nbrs].sort((a, b) => addRate(a) - addRate(b));
  main.innerHTML = `
  <h1>Pilot examples</h1>
  <section class="card pilot-intro" aria-labelledby="h-intro" data-testid="pilot-intro">
    <h2 id="h-intro">${esc(intro.title)}</h2>
    <p>${esc(intro.text)}</p>
    <p>${esc(intro.how)}</p>
  </section>
  <nav class="pilot-tabs" aria-label="Pilot examples">${ctx.b.pilots.map((x) => `<a href="${ctx.link(`/pilot/${x.slug}`)}" ${x.slug === p.slug ? 'aria-current="page"' : ""}>${esc(x.name.replace(/ (city|village)$/, ""))}${x.role === "same_market_check" ? "&nbsp;<span class=\"muted\">(same-market check)</span>" : ""}</a>`).join("")}</nav>
  ${pilotBanner(p.role)}
  <h2 class="pilot-name" data-testid="pilot-name">${esc(p.name)}, ${esc(p.county)}</h2>
  <p class="lede" data-testid="pilot-takeaway">${esc(p.description)}</p>
  ${p.like ? `<div class="note-box" role="note" data-testid="madison-note"><p><strong>${esc(p.like.title)}.</strong> ${esc(p.like.text)}</p>
    ${details("Details", `<p class="small">${esc(p.like.detail)}</p><p class="small">${esc(ctx.b.manifest.terms.never_subtracts ?? "")}</p>${nbrs.length ? `<p class="small" data-testid="madison-neighbours">With the law, 2027–2031, ${esc(scenPhrase(ctx))}: the law adds ${dec(addRate(p))} permits per 1,000 single-family homes per year in Madison, against ${dec(addRate(nbrsAdd[0]))} (${esc(nbrsAdd[0].name)}) to ${dec(addRate(nbrsAdd[nbrsAdd.length - 1]))} (${esc(nbrsAdd[nbrsAdd.length - 1].name)}) in the ${nbrs.length} other ${esc(p.county)} places with more than 2,000 single-family homes. Rate with the law: Madison ${dec(rate5(p))}; those places ${dec(rate5(nbrs[0]))} to ${dec(rate5(nbrs[nbrs.length - 1]))}.</p>` : ""}`)}</div>` : ""}

  <div class="tiles tiles-4">
    <section class="tile"><h2 class="tile-label">Single-family homes</h2><p class="tile-num">${int(p.homes)}</p><p class="tile-sub">one-unit detached homes ${pill("observed")}</p><p class="tile-note">ACS 2020–2024.</p></section>
    <section class="tile"><h2 class="tile-label">Current-law rate used by the model</h2><p class="tile-num" data-testid="pilot-x">${dec(p.x_rate)}</p><p class="tile-sub">permits per 1,000 single-family homes per year ${pill(p.x_status)}</p><p class="tile-note">Basis: ${esc(p.basis_text)}. Range ${dec(p.x_low)}–${dec(p.x_high)}.${prov && p.note ? ` <strong>2026 so far</strong> (provisional, ${esc(provWhen)}): ${int(prov.units)} second homes, more than any full year.` : ""}</p></section>
    <section class="tile"><h2 class="tile-label">${esc(L.baseline)}, 2027–2031</h2><p class="tile-num" data-testid="pilot-baseline">${int(base5)}</p><p class="tile-sub">permits without statewide reform ${pill("calculated")}</p><p class="tile-note">Range ${int(p.base_low_5yr)}–${int(p.base_high_5yr)}.</p></section>
    <section class="tile tile-accent"><h2 class="tile-label">Added by statewide ADU reform (${esc(scenShort(ctx))})</h2><p class="tile-num" data-testid="pilot-additional">+${int(add5(sel))}</p><p class="tile-sub">additional permits over 2027–2031 ${pill("calculated")}</p><p class="tile-note">Lower / central / strong adoption: ${PATHS.map((k) => int(add5(k))).join(" / ")}.</p></section>
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
    <p class="muted">${esc(p.permits.label)}, from the city's ${esc(stage)}. Bars are observed counts; the hatched bar is a provisional, partial-year count. Lines are the model for 2027–2031.</p>
    ${p.measured ? `<p class="small" data-testid="pilot-window"><strong>${p.measured.used_by_model ? `Window the model uses, ${esc(p.measured.window)}` : `Recent window, ${esc(p.measured.window)} (not used by the model, which uses ${esc(p.basis_text)})`}:</strong> ${int(p.measured.permits)} ${p.permits.stage === "application" ? (p.measured.permits === 1 ? "application" : "applications") : "second homes"} over ${dec(p.measured.thousand_home_years, 1)} thousand home-years = ${dec(p.measured.rate)} per 1,000 single-family homes per year.</p>` : ""}
    ${prov && p.programme ? `<div class="note-box" role="note" data-testid="madison-2026"><p><strong>${esc(p.programme.title)}.</strong> ${esc(p.programme.text)}</p>
      <p class="small">2026 is provisional and partial (${esc(provWhen)}). The drop from the 2026 bar to the 2027 line is not the law cutting permits: the forecast starts from Madison's complete years 2022–2025, and Madison's 2026 count so far (${int(prov.units)} second homes on ${int(prov.permits ?? null)} permits) already exceeds the forecast for 2027 with the law (${int(with2027)}).</p>
      ${details("Details", `<p class="small">${esc(p.programme.detail)}</p>${bo2026 ? `<p class="small">If Madison's 2026 pace held as its current-law rate, the statewide baseline would be ${int(bo2026.baseline)} permits over 2027–2031 (${bo2026.d_baseline > 0 ? "+" : "−"}${int(Math.abs(bo2026.d_baseline))}), the law's addition ${bo2026.d_additional > 0 ? "+" : "−"}${int(Math.abs(bo2026.d_additional))} and the total with the law ${bo2026.d_with_law > 0 ? "+" : "−"}${int(Math.abs(bo2026.d_with_law))} (central scenario); see How sure.</p>` : ""}`)}</div>` : ""}
    <p class="summary">Without statewide reform the model expects about ${int(base5)} permits over 2027–2031. With the law, ${esc(scenPhrase(ctx))} adds ${int(add5(sel))}${p.like ? " (Madison follows the path of similar cities in Washington and Oregon, so all three scenarios are the same)" : `, with ${int(add5("lower"))} to ${int(add5("upper"))} from the lower to the strong adoption scenario`}.</p>
    <div class="chart-box" id="pilot-chart"></div>
    ${legendHTML([{ name: `Observed ${stage}`, color: COLORS.observed, kind: "bar" }, { name: `2026: provisional, partial year (${provWhen})`, color: COLORS.observed, kind: "hatch" }, { name: L.baseline, color: COLORS.baseline, dash: DASH.baseline },
      ...PATHS.map((k) => ({ name: scenKey(ctx, k), color: COLORS[k], dash: DASH[k], width: k === sel ? 4 : 2 }))])}
    <div class="grid-obs">
    <div class="table-wrap"><table class="data" data-testid="pilot-observed"><caption>Observed ${esc(stage)}, by year</caption>
      <thead><tr><th scope="col">Year</th><th scope="col" class="num">Second homes (units)</th><th scope="col" class="num">Permits</th><th scope="col">Status</th></tr></thead>
      <tbody>${obs.map((o) => `<tr><th scope="row">${o.year}</th><td class="num">${o.units === null ? missing(o.reason ?? "no record") : int(o.units)}</td><td class="num">${o.permits === null || o.permits === undefined ? "—" : int(o.permits)}</td><td>${o.units === null ? "" : o.status === "provisional" ? `${pill("observed")} provisional, partial year` : pill("observed")}</td></tr>`).join("")}</tbody></table></div>
    <div class="table-wrap"><table class="data" data-testid="pilot-table"><caption>Forecast permits by year (model)</caption>
      <thead><tr><th scope="col">Year</th><th scope="col" class="num">${esc(L.baseline)}</th>${PATHS.map((k) => `<th scope="col" class="num">${esc(scenKey(ctx, k))}: ${esc(L.added)}</th>`).join("")}</tr></thead>
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
    notes: [
      ...(prov ? [{ x: prov.year, y: prov.units ?? 0, text: p.note ? "2026: provisional,\npartial year" : "provisional", anchor: "end" as const }] : []),
      ...(p.note ? [{ x: 2027, y: with2027, text: `2027 with the law: ${int(with2027)}\n(path of cities like Madison)`, anchor: "start" as const, dy: 32 }] : []),
    ],
    bars: { name: "observed", color: COLORS.observed, values: obs.map((o) => ({ x: o.year, y: o.units, hatch: o.status === "provisional" })) },
    series: [
      { name: "baseline", color: COLORS.baseline, dash: DASH.baseline, values: YEARS.map((y, i) => ({ x: y, y: p.base[i] })) },
      ...PATHS.map((k) => ({ name: k, color: COLORS[k], dash: DASH[k], width: k === sel ? 4 : 2, marker: k === sel ? ("circle" as const) : undefined, values: YEARS.map((y, i) => ({ x: y, y: p.base[i] + p.add[k][i] })) })),
    ],
  });
}
