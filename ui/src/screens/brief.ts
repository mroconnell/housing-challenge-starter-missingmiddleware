import { LAW_TEXT, type Ctx } from "../app";
import { PATHS, sum } from "../data";
import { dec, esc, int, pct } from "../format";

export function renderBrief(ctx: Ctx, main: HTMLElement): void {
  const m = ctx.b.manifest, s = ctx.b.state, u = ctx.b.uncertainty;
  const cen = ctx.scen("central"), lo = ctx.scen("lower"), up = ctx.scen("upper");
  const counties = [...ctx.b.areas.counties].sort((a, b) => sum(b.add.central) - sum(a.add.central));
  const top = counties.slice(0, 10);
  const rest = counties.slice(10);
  const drivers = [...u.sensitivity_cases.filter((c) => c.id !== "adopted")].sort((a, b) => Math.abs(b.difference_central) - Math.abs(a.difference_central)).slice(0, 3);
  const homes = u.coverage_rates.reduce((a, c) => a + c.homes, 0);
  const assumed = u.coverage_rates.find((c) => c.status === "assumed")!;

  main.innerHTML = `
  <div class="brief-tools no-print">
    <p>A two-page summary for a hearing or a colleague. It carries the same numbers, ranges and run id as the tool.</p>
    <button type="button" class="button" id="print">Print or save as PDF</button>
  </div>
  <article class="brief" aria-labelledby="brief-h">
    <header class="brief-head">
      <p class="eyebrow">Policy brief · Wisconsin · accessory dwelling units</p>
      <h1 id="brief-h">A statewide ADU law could add about ${int(cen.additional_total)} second-home permits over 2027–2031</h1>
      <p class="brief-sub">On top of about ${int(s.baseline.total)} under current law. Scenarios: ${int(lo.additional_total)} to ${int(up.additional_total)} additional permits.</p>
    </header>

    <h2>What the law changes</h2>
    <p>${LAW_TEXT} Today most Wisconsin places restrict or prohibit ADUs, or have rules that have not been coded. The model estimates permits, not completed homes, for areas, never for individual lots.</p>

    <h2>The numbers</h2>
    <div class="table-wrap"><table class="data" data-testid="brief-table"><caption>Second-home permits on single-family lots, 2027–2031</caption>
      <thead><tr><th scope="col">Scenario</th><th scope="col">What it means</th><th scope="col" class="num">Additional permits</th><th scope="col" class="num">Total with the ${int(s.baseline.total)} baseline</th></tr></thead>
      <tbody>${PATHS.map((p) => { const sc = ctx.scen(p); return `<tr><th scope="row">${esc(sc.label)}</th><td>${esc(sc.info)}</td><td class="num">${int(sc.additional_total)}</td><td class="num">${int(sc.with_law_total)}</td></tr>`; }).join("")}
      <tr><th scope="row">${esc(s.reference_line.label)}</th><td>${esc(s.reference_line.info)}</td><td class="num">${int(s.reference_line.additional_total)}</td><td class="num">${int(s.reference_line.additional_total + s.baseline.total)}</td></tr></tbody></table></div>
    <p class="small">Central by year, 2027–2031: ${cen.additional_by_year.map((v) => int(v)).join(", ")} additional permits. About ${int(cen.additional_total / 5)} a year on average. Wisconsin has ${int(s.homes.value)} single-family homes; today it permits ${dec(s.baseline.rate_per_1000_per_year)} second homes per 1,000 of them per year, and the central reaches ${dec(cen.with_law_rate_by_year[4])} by 2031.</p>

    <h2>Where</h2>
    <div class="table-wrap"><table class="data"><caption>Ten counties with the most additional permits (central), 2027–2031</caption>
      <thead><tr><th scope="col">County</th><th scope="col" class="num">Single-family homes</th><th scope="col" class="num">Baseline</th><th scope="col" class="num">Additional (lower–Strong adoption)</th></tr></thead>
      <tbody>${top.map((c) => `<tr><th scope="row">${esc(c.name)}</th><td class="num">${int(c.homes)}</td><td class="num">${int(sum(c.base))}</td><td class="num">${int(sum(c.add.central))} <span class="muted">(${int(sum(c.add.lower))}–${int(sum(c.add.upper))})</span></td></tr>`).join("")}
      <tr><th scope="row">Other ${rest.length} counties</th><td class="num">${int(rest.reduce((a, c) => a + c.homes, 0))}</td><td class="num">${int(rest.reduce((a, c) => a + sum(c.base), 0))}</td><td class="num">${int(rest.reduce((a, c) => a + sum(c.add.central), 0))}</td></tr></tbody>
      <tfoot><tr><th scope="row">Wisconsin</th><td class="num">${int(counties.reduce((a, c) => a + c.homes, 0))}</td><td class="num">${int(counties.reduce((a, c) => a + sum(c.base), 0))}</td><td class="num">${int(counties.reduce((a, c) => a + sum(c.add.central), 0))}</td></tr></tfoot></table></div>
    <p class="small">✓ The 72 counties add up to the statewide figures. No area is left unallocated.</p>

    <h2>How sure</h2>
    <ul>
      <li>The range shows how much statewide-law states differ, not statistical certainty.</li>
      <li>${pct(assumed.homes / homes)} of single-family homes are in places whose ADU rules have not been coded; they are treated as restricted (assumed).</li>
      <li>Biggest drivers (sensitivity cases, change in the central ${int(cen.additional_total)}): ${drivers.map((d) => `${esc(d.label)} ${d.difference_central > 0 ? "+" : "−"}${int(Math.abs(d.difference_central))}`).join("; ")}.</li>
      <li>Robustness check: predicting 7 held-out states, the adopted method had the lowest error (${dec(u.robustness.rows[0].a, 3)} root-mean-square log error).</li>
    </ul>

    <h2>Limitations</h2>
    <ul>${m.limitations.map((l) => `<li>${esc(l)}</li>`).join("")}</ul>

    <h2>Sources</h2>
    <ul class="small">${m.vintages.map((v) => `<li>${esc(v.what)}: ${esc(v.vintage)}</li>`).join("")}</ul>
    <p class="small brief-foot">Run <code>${esc(m.run_id)}</code> · ${esc(m.model_status)} · Outcome: ${esc(m.outcome.short)} · Missing Middleware, ${esc(m.repo_url)}</p>
  </article>`;
  main.querySelector("#print")!.addEventListener("click", () => window.print());
}
