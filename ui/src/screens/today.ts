import type { Ctx } from "../app";
import { xyChart, legendHTML } from "../charts";
import { dec, esc, int, pct, pill } from "../format";

export function renderToday(ctx: Ctx, main: HTMLElement): void {
  const s = ctx.b.state;
  const pep = s.housing_units_pep;
  const pepLast = pep[pep.length - 1];
  const bps = s.bps;
  const bLast = bps[bps.length - 1];
  const cen = ctx.scen("central"), lo = ctx.scen("lower"), up = ctx.scen("upper");
  const vr = s.vacancy_rate;
  const mixTotal = s.mix.reduce((a, m) => a + (m.value ?? 0), 0);

  main.innerHTML = `
  <h1>Wisconsin housing today</h1>
  <p class="lede">Where Wisconsin's housing stands now, and how many second homes on single-family lots it permits under current law. Every figure shows its source year and status.</p>

  <div class="tiles tiles-4">
    <section class="tile" aria-labelledby="t-units">
      <h2 id="t-units" class="tile-label">Homes in Wisconsin</h2>
      <p class="tile-num" data-testid="pep-units">${int(pepLast.value)}</p>
      <p class="tile-sub">housing units on 1 July ${pepLast.year} ${pill("observed")}</p>
      <p class="tile-note">Up ${int(pepLast.value - pep[0].value)} since ${pep[0].year}. ${esc(pepLast.vintage)}.</p>
    </section>
    <section class="tile" aria-labelledby="t-sf">
      <h2 id="t-sf" class="tile-label">Single-family homes</h2>
      <p class="tile-num" data-testid="sf-homes">${int(s.homes.value)}</p>
      <p class="tile-sub">one-unit detached homes, ±${int(s.homes.moe)} ${pill("observed")}</p>
      <p class="tile-note">The base for every ADU rate in this tool. ${esc(s.homes.vintage)}.</p>
    </section>
    <section class="tile" aria-labelledby="t-vac">
      <h2 id="t-vac" class="tile-label">Vacant homes</h2>
      <p class="tile-num">${pct(vr.value, 1)}</p>
      <p class="tile-sub">of ${int(s.acs_total_units.value)} housing units, ±${pct(vr.moe, 1)} ${pill("calculated")}</p>
      <p class="tile-note">Includes seasonal and recreational homes. ${esc(vr.vintage)}.</p>
    </section>
    <section class="tile" aria-labelledby="t-bps">
      <h2 id="t-bps" class="tile-label">Homes permitted in ${bLast.year}</h2>
      <p class="tile-num">${int(bLast.total)}</p>
      <p class="tile-sub">homes (units) in building permits, of which ${int(bLast["1unit"])} single-family ${pill("observed")}</p>
      <p class="tile-note">${pct(bLast.reported_share ?? null)} reported by places, the rest imputed by the Census Bureau. ${esc(bLast.vintage ?? "")}.</p>
    </section>
  </div>

  <section class="card" aria-labelledby="adu-sum">
    <h2 id="adu-sum">Second homes on single-family lots, 2027–2031</h2>
    <p class="muted">Accessory dwelling units (ADUs) plus single-family-to-duplex conversions on lots that already have a home, counted when the permit is issued.</p>
    <div class="pair">
      <div class="pair-item">
        <p class="tile-label">Under current law (baseline)</p>
        <p class="tile-num" data-testid="today-baseline">${int(s.baseline.total)}</p>
        <p class="tile-sub">permits over 2027–2031, about ${int(s.baseline.total / 5)} a year ${pill("calculated")}</p>
        <p class="tile-note">The model's 2027–2031 average under current law: ${dec(s.baseline.rate_per_1000_per_year)} permits per 1,000 single-family homes per year (there is no observed statewide ADU series). Baseline range ${int(s.baseline.low_total)}–${int(s.baseline.high_total)}.</p>
      </div>
      <div class="pair-item">
        <p class="tile-label">Added by a statewide ADU law (${esc(cen.label.toLowerCase())} scenario)</p>
        <p class="tile-num" data-testid="today-central">+${int(cen.additional_total)}</p>
        <p class="tile-sub">additional permits over 2027–2031 ${pill("calculated")}</p>
        <p class="tile-note">${int(lo.additional_total)} (${esc(lo.label.toLowerCase())} scenario) to ${int(up.additional_total)} (${esc(up.label.toLowerCase())} scenario).</p>
      </div>
    </div>
    <p><a class="button" href="${ctx.link("/compare")}">Compare the scenarios →</a></p>
  </section>

  <div class="grid-2">
    <section class="card" aria-labelledby="h-pep">
      <h2 id="h-pep">Housing units, ${pep[0].year}–${pepLast.year}</h2>
      <div class="chart-box" id="pep-chart"></div>
      ${legendHTML([{ name: "Housing units (Census estimates)", color: "#17644f" }])}
      <details><summary>Show the data</summary>
        <div class="table-wrap"><table class="data"><caption>Housing units in Wisconsin, ${esc(pepLast.vintage)}</caption>
        <thead><tr><th scope="col">Year</th><th scope="col" class="num">Housing units</th><th scope="col">Status</th></tr></thead>
        <tbody>${pep.map((p) => `<tr><th scope="row">${p.year}</th><td class="num">${int(p.value)}</td><td>${pill(p.status)}</td></tr>`).join("")}</tbody></table></div>
      </details>
    </section>
    <section class="card" aria-labelledby="h-mix">
      <h2 id="h-mix">Housing mix</h2>
      <p class="muted">Share of ${int(mixTotal)} homes in these five types. ${esc(s.mix[0].vintage)}.</p>
      <div class="table-wrap"><table class="data mix"><caption class="sr-only">Housing units by type</caption>
        <thead><tr><th scope="col">Type</th><th scope="col" class="num">Homes</th><th scope="col" class="num">Share</th><th scope="col">Status</th></tr></thead>
        <tbody>${s.mix.map((m) => `<tr><th scope="row">${esc(m.label)}<span class="bar" style="width:${((m.value ?? 0) / mixTotal) * 100}%" aria-hidden="true"></span></th><td class="num">${int(m.value)} <span class="muted">±${int(m.moe)}</span></td><td class="num">${pct((m.value ?? 0) / mixTotal)}</td><td>${pill(m.status)}</td></tr>`).join("")}</tbody>
      </table></div>
    </section>
  </div>

  <section class="card" aria-labelledby="h-bps">
    <h2 id="h-bps">Homes permitted each year, all types</h2>
    <p class="muted">Census Building Permits Survey: homes (units) in permits issued by Wisconsin's permit-issuing places. This counts all new homes, not ADUs; there is no published statewide ADU series for Wisconsin.</p>
    <div class="chart-box" id="bps-chart"></div>
    ${legendHTML([{ name: "All homes permitted", color: "#17644f", kind: "bar" }, { name: "Single-family homes permitted", color: "#4b5450" }])}
    <details><summary>Show the data</summary>
      <div class="table-wrap"><table class="data"><caption>Homes permitted per year in Wisconsin</caption>
      <thead><tr><th scope="col">Year</th><th scope="col" class="num">All homes</th><th scope="col" class="num">Single-family</th><th scope="col" class="num">2–4 homes</th><th scope="col" class="num">5 or more</th><th scope="col" class="num">Reported share</th></tr></thead>
      <tbody>${bps.map((b) => `<tr><th scope="row">${b.year}</th><td class="num">${int(b.total)}</td><td class="num">${int(b["1unit"])}</td><td class="num">${int(b["2_4"])}</td><td class="num">${int(b["5plus"])}</td><td class="num">${pct(b.reported_share ?? null)}</td></tr>`).join("")}</tbody></table></div>
    </details>
  </section>`;

  xyChart(main.querySelector("#pep-chart")!, {
    title: "Wisconsin housing units by year",
    desc: `Housing units rose from ${int(pep[0].value)} in ${pep[0].year} to ${int(pepLast.value)} in ${pepLast.year}.`,
    yLabel: "Housing units", xTicks: pep.map((p) => p.year), height: 220,
    yFormat: (y) => (y / 1e6).toFixed(1) + "M", yMax: 3e6,
    series: [{ name: "Housing units", color: "#17644f", values: pep.map((p) => ({ x: p.year, y: p.value })), marker: "circle" }],
  });
  xyChart(main.querySelector("#bps-chart")!, {
    title: "Homes permitted per year in Wisconsin, 2015 to 2025",
    desc: `All homes permitted ranged from ${int(Math.min(...bps.map((b) => b.total ?? Infinity)))} to ${int(Math.max(...bps.map((b) => b.total ?? 0)))} a year; ${int(bLast.total)} in ${bLast.year}.`,
    yLabel: "Homes permitted per year", xTicks: bps.map((b) => b.year), height: 260,
    bars: { name: "All homes", color: "#17644f", values: bps.map((b) => ({ x: b.year, y: b.total })) },
    series: [{ name: "Single-family", color: "#4b5450", values: bps.map((b) => ({ x: b.year, y: b["1unit"] })), marker: "circle", width: 2 }],
  });
}
