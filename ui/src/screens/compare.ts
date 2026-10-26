import { COLORS, DASH, LAW_TEXT, bindScenarioPicker, details, scenarioPicker, scenKey, scenPhrase, scenShort, type Ctx } from "../app";
import { legendHTML, xyChart } from "../charts";
import { PATHS } from "../data";
import { dec, esc, int, pct, pill, YEARS } from "../format";

export function renderCompare(ctx: Ctx, main: HTMLElement, units: "permits" | "rate" = "permits"): void {
  const s = ctx.b.state;
  const sel = ctx.scen();
  const homesK = (s.homes.value ?? 0) / 1000;
  const base = s.baseline;
  const ref = s.reference_line;
  const lo = ctx.scen("lower"), cen = ctx.scen("central"), up = ctx.scen("upper");
  const totalCtx = s.contexts.reduce((a, c) => a + c.additional_central, 0);
  const homesCtx = s.contexts.reduce((a, c) => a + c.homes, 0);

  const L = s.labels;
  // TODO(lower scenario): the lower scenario's definition is being revised (docs/gate4/SCENARIO_OPTIONS.md). Its name,
  // title, text and method all come from the bundle (scripts/build_ui_bundle.py, DISPLAY block), so only that changes.
  main.innerHTML = `
  <h1>A statewide ADU law: what it adds</h1>
  <p class="lede" data-testid="compare-intro">${esc(s.page_intro.compare)}</p>

  <section class="card" aria-labelledby="h-path">
    <div class="card-head">
      <h2 id="h-path">Second-home permits each year, with and without the law</h2>
      <fieldset class="seg" aria-label="Units"><legend class="sr-only">Units</legend>
        <label><input type="radio" name="units" value="permits" ${units === "permits" ? "checked" : ""}> Permits per year</label>
        <label><input type="radio" name="units" value="rate" ${units === "rate" ? "checked" : ""}> Per 1,000 single-family homes</label>
      </fieldset>
    </div>
    <div class="chart-box" id="path-chart"></div>
    ${legendHTML([
      { name: L.baseline, color: COLORS.baseline, dash: DASH.baseline },
      ...PATHS.map((p) => ({ name: scenKey(ctx, p), color: COLORS[p], dash: DASH[p], width: p === ctx.ui.scenario ? 4 : 2 })),
      { name: L.band, color: COLORS.central, kind: "band" as const },
      { name: L.reference, color: COLORS.ref },
      ...(ref.carried_forward_years?.length ? [{ name: `${ref.carried_forward_years.join(", ")}: carried forward`, color: COLORS.ref, dash: "4 4" }] : []),
    ])}
    <p class="summary" data-testid="compare-summary">Over 2027–2031, ${esc(scenPhrase(ctx))} adds about <strong>${int(sel.additional_total)}</strong> permits on top of <strong>${int(base.total)}</strong> without statewide reform. The three scenarios run from ${int(lo.additional_total)} to ${int(up.additional_total)} added permits. The ${esc(L.reference.charAt(0).toLowerCase() + L.reference.slice(1))} gives ${int(ref.additional_total)}.</p>
    <p class="muted small">${esc(ref.info)} 2026 is a bridge year without reform (${int(base.bridge_2026.central)} permits, ${int(base.bridge_2026.low)}–${int(base.bridge_2026.high)}). The 1 January 2027 start date is stylized.</p>
  </section>

  <p class="law"><strong>The law.</strong> ${LAW_TEXT}</p>

  ${scenarioPicker(ctx, "scen-compare")}

  <div class="tiles tiles-3" aria-live="polite">
    <section class="tile">
      <h2 class="tile-label">${esc(L.baseline)}</h2>
      <p class="tile-num" data-testid="baseline-total">${int(base.total)}</p>
      <p class="tile-sub">permits over 2027–2031 ${pill("calculated")}</p>
      <p class="tile-note">Range ${int(base.low_total)}–${int(base.high_total)}. The same in every scenario.</p>
    </section>
    <section class="tile tile-accent">
      <h2 class="tile-label">Added by statewide ADU reform (${esc(scenShort(ctx))})</h2>
      <p class="tile-num" data-testid="additional-total">+${int(sel.additional_total)}</p>
      <p class="tile-sub">additional permits over 2027–2031 ${pill("calculated")}</p>
      <p class="tile-note">About ${int(sel.additional_total / 5)} a year. Lower / central / strong adoption: ${int(lo.additional_total)} / ${int(cen.additional_total)} / ${int(up.additional_total)}.</p>
    </section>
    <section class="tile">
      <h2 class="tile-label">Total with statewide ADU reform</h2>
      <p class="tile-num" data-testid="withlaw-total">${int(sel.with_law_total)}</p>
      <p class="tile-sub">permits over 2027–2031 (baseline plus added) ${pill("calculated")}</p>
      <p class="tile-note">In 2031: ${dec(sel.with_law_rate_by_year[4])} permits per 1,000 single-family homes per year, against ${dec(base.by_year[4] / homesK)} without reform.</p>
    </section>
  </div>

  <section class="card" aria-labelledby="h-tbl">
    <h2 id="h-tbl">Permits by year</h2>
    <div class="table-wrap">
    <table class="data" data-testid="compare-table"><caption>Second-home permits by year. Added permits are on top of the baseline.</caption>
      <thead><tr><th scope="col">Year</th><th scope="col" class="num">${esc(L.baseline)}</th>${PATHS.map((p) => `<th scope="col" class="num ${p === ctx.ui.scenario ? "hl" : ""}">${esc(scenKey(ctx, p))}: ${esc(L.added)}</th>`).join("")}<th scope="col" class="num">${esc(L.reference)}: ${esc(L.added)}</th><th scope="col" class="num">Total with ${esc(scenKey(ctx))}</th></tr></thead>
      <tbody>${YEARS.map((y, i) => `<tr><th scope="row">${y}</th><td class="num">${int(base.by_year[i])}</td>${PATHS.map((p) => `<td class="num ${p === ctx.ui.scenario ? "hl" : ""}">${int(ctx.scen(p).additional_by_year[i])}</td>`).join("")}<td class="num">${int(ref.additional_by_year[i])}</td><td class="num">${int(base.by_year[i] + sel.additional_by_year[i])}</td></tr>`).join("")}</tbody>
      <tfoot><tr><th scope="row">2027–2031</th><td class="num">${int(base.total)}</td>${PATHS.map((p) => `<td class="num ${p === ctx.ui.scenario ? "hl" : ""}" data-testid="total-${p}">${int(ctx.scen(p).additional_total)}</td>`).join("")}<td class="num">${int(ref.additional_total)}</td><td class="num">${int(sel.with_law_total)}</td></tr></tfoot>
    </table></div>
    ${details("Statewide rates (permits per 1,000 single-family homes per year)", `
      <div class="table-wrap"><table class="data"><caption>(baseline + added permits in the year) ÷ ${dec(homesK, 3)} thousand single-family homes</caption>
      <thead><tr><th scope="col">Year</th><th scope="col" class="num">${esc(L.baseline)}</th>${PATHS.map((p) => `<th scope="col" class="num">${esc(scenKey(ctx, p))}</th>`).join("")}<th scope="col" class="num">${esc(L.reference)}</th></tr></thead>
      <tbody>${YEARS.map((y, i) => `<tr><th scope="row">${y}</th><td class="num">${dec(base.by_year[i] / homesK)}</td>${PATHS.map((p) => `<td class="num">${dec(ctx.scen(p).with_law_rate_by_year[i])}</td>`).join("")}<td class="num">${dec(ref.rate_by_year[i])}</td></tr>`).join("")}</tbody></table></div>`)}
    ${details("How each scenario is calculated", `<ul class="plain small" data-testid="scenario-method">${PATHS.map((p) => { const sc = ctx.scen(p); return `<li><strong>${esc(sc.chart_label)}.</strong> ${esc(sc.info)}${sc.todo ? ` <em>Note: ${esc(sc.todo)}.</em>` : ""}</li>`; }).join("")}
      <li><strong>${esc(L.reference)}.</strong> ${esc(ref.detail)} ${esc(ref.why_central_differs)}</li>
      <li><strong>The law never subtracts.</strong> ${esc(ctx.b.manifest.terms.never_subtracts ?? "")}</li>
      <li><strong>Madison.</strong> ${esc(ctx.b.areas.munis.find((a) => a.note)?.note ?? "")} See <a href="${ctx.link("/pilot/madison")}">the Madison pilot</a>.</li></ul>
      <p class="muted small">Scenarios, not confidence intervals: ${esc(ctx.b.manifest.terms.scenarios)}</p>`)}
    <p><a href="${ctx.link("/how-sure")}">What drives the range? See the sensitivity analysis →</a></p>
  </section>

  <section class="card" aria-labelledby="h-ctx">
    <h2 id="h-ctx">By type of place</h2>
    <p class="muted">Added permits over 2027–2031 in ${esc(scenPhrase(ctx))}; the range in brackets runs from the lower to the strong adoption scenario.</p>
    <div class="table-wrap"><table class="data"><caption class="sr-only">Added permits by type of place</caption>
      <thead><tr><th scope="col">Type of place</th><th scope="col" class="num">Single-family homes</th><th scope="col" class="num">Share of homes</th><th scope="col" class="num">${esc(L.baseline)}</th><th scope="col" class="num">Added (lower to strong adoption)</th><th scope="col" class="num">Share of added</th></tr></thead>
      <tbody>${s.contexts.map((c) => { const v = (c as unknown as Record<string, number>)[`additional_${ctx.ui.scenario}`]; const tot = s.contexts.reduce((a, x) => a + (x as unknown as Record<string, number>)[`additional_${ctx.ui.scenario}`], 0); return `<tr><th scope="row">${esc(c.label)}</th><td class="num">${int(c.homes)}</td><td class="num">${pct(c.homes / homesCtx)}</td><td class="num">${int(c.baseline)}</td><td class="num">${int(v)} <span class="muted">(${int(c.additional_lower)} to ${int(c.additional_upper)})</span></td><td class="num">${pct(v / tot)}</td></tr>`; }).join("")}</tbody>
      <tfoot><tr><th scope="row">Wisconsin</th><td class="num">${int(homesCtx)}</td><td class="num">100%</td><td class="num">${int(base.total)}</td><td class="num">${int(sel.additional_total)}</td><td class="num">100%</td></tr></tfoot>
    </table></div>
    <p class="muted small">Rural areas get ${pct(s.contexts.find((c) => c.id === "rural")!.additional_central / totalCtx)} of the central scenario's added permits with ${pct(s.contexts.find((c) => c.id === "rural")!.homes / homesCtx)} of single-family homes, partly because rural home values include acreage. Town figures are rough shares of the statewide result, not local forecasts.</p>
  </section>`;

  bindScenarioPicker(ctx, main, "scen-compare");
  main.querySelectorAll<HTMLInputElement>('input[name="units"]').forEach((i) =>
    i.addEventListener("change", () => { renderCompare(ctx, main, i.value as "permits" | "rate"); (main.querySelector(`input[name="units"][value="${i.value}"]`) as HTMLInputElement)?.focus(); }));

  const f = units === "rate" ? (v: number) => v / homesK : (v: number) => v;
  const pts = (arr: number[]) => YEARS.map((y, i) => ({ x: y, y: f(arr[i]) }));
  const withLaw = (p: string) => YEARS.map((_, i) => base.by_year[i] + ctx.scen(p as never).additional_by_year[i]);
  const prior = [{ x: 2026, y: f(base.bridge_2026.central) }];
  const cf = ref.carried_forward_years ?? [];
  xyChart(main.querySelector("#path-chart")!, {
    title: units === "rate" ? "Statewide second-home permit rate per 1,000 single-family homes per year, 2026 to 2031" : "Statewide second-home permits per year, 2026 to 2031",
    desc: `${L.baseline}: about ${int(base.by_year[0])} to ${int(base.by_year[4])} permits a year. With the law in 2031: ${PATHS.map((p) => `${ctx.scen(p).name} ${int(withLaw(p)[4])}`).join(", ")} permits. ${L.reference}: ${int(ref.with_law_by_year[4])}.`,
    yLabel: units === "rate" ? "Permits per 1,000 single-family homes per year" : "Permits per year",
    yFormat: units === "rate" ? (y) => y.toFixed(1) : undefined,
    xTicks: [2026, ...YEARS], xPad: 0.4,
    vline: { x: 2026.5, label: "law takes effect (stylized)" },
    band: { name: "range", lo: pts(withLaw("lower")), hi: pts(withLaw("upper")), color: COLORS.central },
    series: [
      { name: "Baseline", color: COLORS.baseline, dash: DASH.baseline, values: [...prior, ...pts(base.by_year)], width: 2.5 },
      ...PATHS.map((p) => ({ name: p, color: COLORS[p], dash: DASH[p], width: p === ctx.ui.scenario ? 4 : 2, values: [...prior, ...pts(withLaw(p))], marker: p === ctx.ui.scenario ? ("circle" as const) : undefined })),
      // reference line: solid through the last drawn year, then dashed where values are carried forward
      { name: "Reference", color: COLORS.ref, width: 2, values: YEARS.map((y, i) => ({ x: y, y: cf.includes(y) ? null : f(ref.with_law_by_year[i]) })) },
      ...(cf.length ? [{ name: "Reference, carried forward", color: COLORS.ref, dash: "4 4", width: 2, values: YEARS.map((y, i) => ({ x: y, y: cf.includes(y) || cf.includes(y + 1) ? f(ref.with_law_by_year[i]) : null })) }] : []),
    ],
  });
}
