import { LAW_TEXT, details, labelScrollers, type Ctx } from "../app";
import { bindChartMode, chartModeToggleHTML, type ChartMode } from "../charts";
import { dec, esc, int, pct, YEARS } from "../format";
import { ALL_HOUSING_BASELINE_2027_2031, drawRangeChart, num, rangeCardHTML, rangeCaveatHTML, sideLinesHTML } from "../range";

/** "Why places differ": one plain paragraph, the rural note, and the numbers one click away (docs/gate5/MODEL_CHECKS.md, 3b). */
function whyDiffer(ctx: Ctx, totalCtx: number, homesCtx: number): string {
  const s = ctx.b.state, W = s.context_why;
  const c = Object.fromEntries(s.contexts.map((x) => [x.id, x]));
  const d = Object.fromEntries(W.drivers.map((x) => [x.term, x]));
  const up = (r: number) => `${Math.round((r - 1) * 100)}%`;
  const down = (r: number) => `${Math.round((1 - r) * 100)}%`;
  const money = (v: number) => `$${int(Math.round(v / 100) * 100)}`;
  const ex = (g: string) => W.examples.filter((e) => e.context === g).map((e) => `${esc(e.name)} ${dec(e.additional_rate_central)} (median home value ${money(e.median_home_value)})`).join(", ");
  const rows = [...s.contexts.map((x) => ({ label: x.label, r: x as typeof W.state })), { label: "Wisconsin", r: W.state }];
  return `<div class="why-differ" data-testid="why-differ">
    <p><strong>Why places differ.</strong> The model first sets Wisconsin's statewide rate with the law, then spreads it across places by home value alone: a place whose median home value is 10% above Wisconsin's average gets about a ${up(d.alloc_value_dev.ratio_10pct)} higher rate with the law. Income and the number of homes help set the statewide total but do not move one place against another. That is why, in the central scenario, the law adds ${dec(c.suburban.additional_rate_central)} permits per 1,000 single-family homes per year in suburban places and ${dec(c.rural.additional_rate_central)} in rural places, against ${dec(c.small_community.additional_rate_central)} in small communities and ${dec(c.urban.additional_rate_central)} in urban places (Wisconsin ${dec(W.state.additional_rate_central)}; 2027–2031 average).</p>
    <p class="muted small">Rural areas get ${pct(c.rural.additional_central / totalCtx)} of the central scenario's added permits with ${pct(c.rural.homes / homesCtx)} of single-family homes, partly because a rural home's value includes its land (acreage), which raises value compared with income. Town figures are rough shares of the statewide result, not local forecasts.</p>
    ${details("Why places differ: the numbers", `<div class="table-wrap"><table class="data" data-testid="why-differ-table"><caption>Home values, incomes and rates by type of place (rates: permits per 1,000 single-family homes per year; central scenario)</caption>
      <thead><tr><th scope="col">Type of place</th><th scope="col" class="num">Median home value</th><th scope="col" class="num">Median household income</th><th scope="col" class="num">Current-law rate</th><th scope="col" class="num">Rate with the law, 2031</th><th scope="col" class="num">Added by the law, 2027–2031 average</th></tr></thead>
      <tbody>${rows.map((x) => `<tr><th scope="row">${esc(x.label)}</th><td class="num">${money(x.r.median_home_value)}</td><td class="num">${money(x.r.median_income)}</td><td class="num">${dec(x.r.x_rate, 3)}</td><td class="num">${dec(x.r.y_rate_2031_central)}</td><td class="num">${dec(x.r.additional_rate_central)}</td></tr>`).join("")}</tbody></table></div>
      <ul class="plain small">
        <li><strong>Home value (spreads the total across places).</strong> 10% above Wisconsin's average: a ${up(d.alloc_value_dev.ratio_10pct)} higher rate with the law (coefficient ${dec(d.alloc_value_dev.coefficient)} on the log scale, standard error ${dec(d.alloc_value_dev.se)}). A few small villages with home values far above any California place's are capped at California's largest gap.</li>
        <li><strong>Statewide rate only.</strong> The statewide rate comes from a fit with home value, income and size, within each statewide-law state: 10% higher value ${up(d.value_dev.ratio_10pct)} higher rate (${dec(d.value_dev.coefficient)}, standard error ${dec(d.value_dev.se)}); 10% higher income at the same value ${down(d.income_dev.ratio_10pct)} lower (${dec(d.income_dev.coefficient)}, standard error ${dec(d.income_dev.se)}); 10% more homes ${dec((d.log_homes.ratio_10pct - 1) * 100, 1)}% higher (${dec(d.log_homes.coefficient)}, standard error ${dec(d.log_homes.se)}). These set Wisconsin's total, not each place's share.</li>
        <li><strong>Current law.</strong> Urban places already permit the most (${dec(c.urban.x_rate, 3)} per 1,000 homes per year, from Milwaukee's and Madison's own records), which leaves less for the law to add.</li>
        <li><strong>Largest places in each group</strong> (added by the law, permits per 1,000 single-family homes per year). Urban: ${ex("urban")}. Suburban: ${ex("suburban")}. Small communities: ${ex("small_community")}. Rural: ${ex("rural")}.</li>
        <li><strong>The type of place is only a label.</strong> The model never uses it: it uses each place's home value, so the groups differ because their places' home values do.</li>
      </ul>
      <p class="muted small">Home values and incomes: homes-weighted geometric means of ACS 2020–2024 medians for each city, village and town. Rate effects: the adopted model's two fits to places in the statewide-law states, within each state. Sources: ${esc(W.source)}.</p>`)}
  </div>`;
}

/** The ADU range card and its chart side lines (shared with the brief and How sure). */
export const ADU_SCOPE = "These are ADU permits: second homes on single-family lots, not all homes.";
export function aduRangeCard(ctx: Ctx, headingLevel: 2 | 3 = 2, testid = "range-card"): string {
  return rangeCardHTML({ title: "Extra ADU permits from the law: the 90% range", range: ctx.b.state.range90, baselineTotal: ALL_HOUSING_BASELINE_2027_2031, scopeNote: ADU_SCOPE, testid, headingLevel, caveatInCard: false });
}

export function renderCompare(ctx: Ctx, main: HTMLElement, units: "permits" | "rate" = "permits"): void {
  const s = ctx.b.state;
  const R = s.range90;
  const homesK = (s.homes.value ?? 0) / 1000;
  const base = s.baseline;
  const chartLines = s.side_lines.filter((x) => x.where === "chart");
  const totalCtx = s.contexts.reduce((a, c) => a + c.additional_central, 0);
  const homesCtx = s.contexts.reduce((a, c) => a + c.homes, 0);
  const L = s.labels;
  main.innerHTML = `
  <h1>A statewide ADU law: what it adds</h1>
  <p class="lede" data-testid="compare-intro">How many more second-home (ADU) permits Wisconsin would issue over 2027–2031 with a statewide ADU law than under current law. The answer is one 90% range. The thin lines across it are other ways of reaching the number, shown as reasons to believe; none of them is "the" estimate.</p>

  ${aduRangeCard(ctx)}

  <section class="card" aria-labelledby="h-side">
    <h2 id="h-side">Lines across the range</h2>
    ${sideLinesHTML(chartLines, "ADU permits over 2027–2031", "side-lines", "Each line is drawn on the chart below. Lines can sit outside the range; they do not change it.")}
    ${rangeCaveatHTML(ctx.b.state.range90)}
    <p class="small"><a href="${ctx.link("/how-sure")}">More lines and what-ifs are on How sure →</a></p>
  </section>

  <section class="card" aria-labelledby="h-path">
    <div class="card-head">
      <h2 id="h-path">Second-home permits each year, with and without the law</h2>
      <fieldset class="seg" aria-label="Units"><legend class="sr-only">Units</legend>
        <label><input type="radio" name="units" value="permits" ${units === "permits" ? "checked" : ""}> Permits per year</label>
        <label><input type="radio" name="units" value="rate" ${units === "rate" ? "checked" : ""}> Per 1,000 single-family homes</label>
      </fieldset>
    </div>
    ${chartModeToggleHTML("adu-chart-mode")}
    <div class="chart-box" id="path-chart"></div>
    <div id="path-legend"></div>
    <p class="summary" data-testid="compare-summary">Over 2027–2031, the law adds <strong>${num(R.low)} to ${num(R.high)}</strong> ADU permits (90% range) on top of <strong>${int(base.total)}</strong> without statewide reform (range ${int(base.low_total)} to ${int(base.high_total)}).</p>
    <p class="muted small">The band and the side lines are spread over the years by one fixed yearly profile, so each year's share of the five-year total is the same for all of them. 2026 is a bridge year without reform (${int(base.bridge_2026.central)} permits, ${int(base.bridge_2026.low)}–${int(base.bridge_2026.high)}). The 1 January 2027 start date is stylized.</p>
  </section>

  <p class="law"><strong>The law.</strong> ${LAW_TEXT}</p>

  <section class="card" aria-labelledby="h-tbl">
    <h2 id="h-tbl">Permits by year</h2>
    <div class="table-wrap">
    <table class="data" data-testid="compare-table"><caption>Second-home (ADU) permits by year: current law, and the law's extra permits as a 90% range</caption>
      <thead><tr><th scope="col">Year</th><th scope="col" class="num">${esc(L.baseline)}</th><th scope="col" class="num">Current law: low</th><th scope="col" class="num">Current law: high</th><th scope="col" class="num">Extra with the law: low end</th><th scope="col" class="num">Extra with the law: high end</th></tr></thead>
      <tbody>${YEARS.map((y, i) => `<tr><th scope="row">${y}</th><td class="num">${int(base.by_year[i])}</td><td class="num">${int(base.low_by_year[i])}</td><td class="num">${int(base.high_by_year[i])}</td><td class="num">${int(R.years[i].low)}</td><td class="num">${int(R.years[i].high)}</td></tr>`).join("")}</tbody>
      <tfoot><tr><th scope="row">2027–2031</th><td class="num">${int(base.total)}</td><td class="num">${int(base.low_total)}</td><td class="num">${int(base.high_total)}</td><td class="num" data-testid="table-range-low">${num(R.low)}</td><td class="num" data-testid="table-range-high">${num(R.high)}</td></tr></tfoot>
    </table></div>
    <p class="small muted">Yearly ends are the five-year ends times each year's fixed share; they are not added to current law's own range. Rows may not add exactly because of rounding.</p>
    ${details("Statewide rates (permits per 1,000 single-family homes per year)", `
      <div class="table-wrap"><table class="data"><caption>Permits in the year ÷ ${dec(homesK, 3)} thousand single-family homes</caption>
      <thead><tr><th scope="col">Year</th><th scope="col" class="num">${esc(L.baseline)}</th><th scope="col" class="num">Extra with the law: low end</th><th scope="col" class="num">Extra with the law: high end</th></tr></thead>
      <tbody>${YEARS.map((y, i) => `<tr><th scope="row">${y}</th><td class="num">${dec(base.by_year[i] / homesK)}</td><td class="num">${dec(R.years[i].low / homesK)}</td><td class="num">${dec(R.years[i].high / homesK)}</td></tr>`).join("")}</tbody></table></div>`)}
    ${details("How the range and the lines are made", `<ul class="plain small" data-testid="scenario-method">
      <li><strong>The 90% range.</strong> ${esc(R.method)} ${esc(R.coverage)}</li>
      ${chartLines.map((x) => `<li><strong>${esc(x.label)}.</strong> ${esc(x.note)}</li>`).join("")}
      <li><strong>The law never subtracts.</strong> ${esc(ctx.b.manifest.terms.never_subtracts ?? "")}</li>
      <li><strong>Madison.</strong> ${esc(ctx.b.areas.munis.find((a) => a.note)?.note ?? "")} See <a href="${ctx.link("/pilot/madison")}">the Madison pilot</a>.</li></ul>
      <p class="muted small">Source of the range: ${esc(R.source)}.</p>`)}
    <p><a href="${ctx.link("/how-sure")}">What drives the range? See How sure →</a></p>
  </section>

  <section class="card" aria-labelledby="h-ctx">
    <h2 id="h-ctx">By type of place</h2>
    <p class="muted">Extra ADU permits over 2027–2031 by type of place. Each type's range is the statewide 90% range times its fixed share of the statewide addition.</p>
    <div class="table-wrap"><table class="data" data-testid="context-table"><caption class="sr-only">Extra permits by type of place</caption>
      <thead><tr><th scope="col">Type of place</th><th scope="col" class="num">Single-family homes</th><th scope="col" class="num">Share of homes</th><th scope="col" class="num">${esc(L.baseline)}</th><th scope="col" class="num">Share of the extra permits</th><th scope="col" class="num">Extra permits, 90% range</th></tr></thead>
      <tbody>${s.contexts.map((c) => { const sh = c.additional_central / totalCtx; return `<tr><th scope="row">${esc(c.label)}</th><td class="num">${int(c.homes)}</td><td class="num">${pct(c.homes / homesCtx)}</td><td class="num">${int(c.baseline)}</td><td class="num">${pct(sh)}</td><td class="num">${int(sh * R.low)} to ${int(sh * R.high)}</td></tr>`; }).join("")}</tbody>
      <tfoot><tr><th scope="row">Wisconsin</th><td class="num">${int(homesCtx)}</td><td class="num">100%</td><td class="num">${int(base.total)}</td><td class="num">100%</td><td class="num">${num(R.low)} to ${num(R.high)}</td></tr></tfoot>
    </table></div>
    ${whyDiffer(ctx, totalCtx, homesCtx)}
  </section>`;

  main.querySelectorAll<HTMLInputElement>('input[name="units"]').forEach((i) =>
    i.addEventListener("change", () => {
      renderCompare(ctx, main, i.value as "permits" | "rate");
      labelScrollers(main);
      (main.querySelector(`input[name="units"][value="${i.value}"]`) as HTMLInputElement)?.focus();
      ctx.announce(i.value === "rate" ? "Chart shows permits per 1,000 single-family homes per year." : "Chart shows permits per year.");
    }));

  const rate = units === "rate";
  const f = rate ? (v: number) => v / homesK : (v: number) => v;
  const draw = (mode: ChartMode) => {
    const legend = drawRangeChart(main.querySelector("#path-chart")!, {
      mode, range: R, sideLines: chartLines, f, noun: "ADU permits",
      base: { years: YEARS, central: base.by_year, low: base.low_by_year, high: base.high_by_year, prior: { year: 2026, value: base.bridge_2026.central } },
      title: mode === "extra"
        ? (rate ? "Extra second-home permits from the law per 1,000 single-family homes per year, 2026 to 2031" : "Extra second-home permits from the law per year, 2026 to 2031")
        : (rate ? "Statewide second-home permit rate per 1,000 single-family homes per year, 2026 to 2031" : "Statewide second-home permits per year, 2026 to 2031"),
      yLabel: mode === "extra" ? (rate ? "Extra permits per 1,000 single-family homes per year" : "Extra permits per year") : (rate ? "Permits per 1,000 single-family homes per year" : "Permits per year"),
      yFormat: rate ? (y: number) => y.toFixed(1) : undefined,
      xTicks: [2026, ...YEARS], vline: { x: 2026.5, label: "law takes effect (stylized)" },
    });
    main.querySelector("#path-legend")!.innerHTML = legend;
  };
  bindChartMode("adu-chart-mode", draw);
  main.querySelector("#adu-chart-mode")?.addEventListener("change", (e) =>
    ctx.announce((e.target as HTMLInputElement).value === "extra" ? "Chart shows only the extra permits from the law. Current law is the zero line." : "Chart shows total permits, with and without the law."));
}
