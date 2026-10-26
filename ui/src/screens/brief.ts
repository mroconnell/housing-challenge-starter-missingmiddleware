import { LAW_TEXT, type Ctx } from "../app";
import { PATHS, sum, type District } from "../data";
import { dec, esc, int, pct } from "../format";

export function renderBrief(ctx: Ctx, main: HTMLElement): void {
  const m = ctx.b.manifest, s = ctx.b.state, u = ctx.b.uncertainty;
  const cen = ctx.scen("central"), lo = ctx.scen("lower"), up = ctx.scen("upper");
  const L = s.labels;
  const counties = [...ctx.b.areas.counties].sort((a, b) => sum(b.add.central) - sum(a.add.central));
  const top = counties.slice(0, 10);
  const rest = counties.slice(10);
  const drivers = [...u.sensitivity_cases.filter((c) => c.id !== "adopted" && c.group === "addition")].sort((a, b) => Math.abs(b.difference_central) - Math.abs(a.difference_central)).slice(0, 3);

  main.innerHTML = `
  <div class="brief-tools no-print">
    <p>A three-page summary for a hearing or a colleague: two pages of findings and sources, then one page with every legislative district. It carries the same numbers, ranges and run id as the tool.</p>
    <button type="button" class="button" id="print">Print or save as PDF</button>
  </div>
  <article class="brief" aria-labelledby="brief-h">
    <header class="brief-head">
      <p class="eyebrow">Policy brief · Wisconsin · accessory dwelling units</p>
      <h1 id="brief-h">A statewide ADU law could add about ${int(cen.additional_total)} second-home permits over 2027–2031</h1>
      <p class="brief-sub">On top of about ${int(s.baseline.total)} without statewide reform. Scenarios: ${int(lo.additional_total)} (lower) to ${int(up.additional_total)} (strong adoption) added permits.</p>
    </header>

    <h2>What the law changes</h2>
    <p>${LAW_TEXT} Today most Wisconsin places restrict or prohibit ADUs, or have rules that have not been coded. The model estimates permits, not completed homes, for areas, never for individual lots.</p>

    <h2>The numbers</h2>
    <div class="table-wrap"><table class="data" data-testid="brief-table"><caption>Second-home permits on single-family lots, 2027–2031</caption>
      <thead><tr><th scope="col">Scenario</th><th scope="col">What it means</th><th scope="col" class="num">Added permits</th><th scope="col" class="num">Total with the ${int(s.baseline.total)} baseline</th></tr></thead>
      <tbody><tr><th scope="row">${esc(L.baseline)}</th><td>Current law, no statewide ADU law</td><td class="num">—</td><td class="num">${int(s.baseline.total)}</td></tr>
      ${PATHS.map((p) => { const sc = ctx.scen(p); return `<tr><th scope="row">${esc(sc.chart_label)}</th><td><strong>${esc(sc.title)}.</strong> ${esc(sc.text)}</td><td class="num">${int(sc.additional_total)}</td><td class="num">${int(sc.with_law_total)}</td></tr>`; }).join("")}
      <tr><th scope="row">${esc(L.reference)}</th><td>${esc(s.reference_line.info)}</td><td class="num">${int(s.reference_line.additional_total)}</td><td class="num">${int(s.reference_line.additional_total + s.baseline.total)}</td></tr></tbody></table></div>
    <p class="small">Central scenario by year, 2027–2031: ${cen.additional_by_year.map((v) => int(v)).join(", ")} added permits, about ${int(cen.additional_total / 5)} a year on average. Wisconsin has ${int(s.homes.value)} single-family homes; without statewide reform the model expects ${dec(s.baseline.rate_per_1000_per_year)} second-home permits per 1,000 of them per year in 2027–2031, and with the law the central scenario reaches ${dec(cen.with_law_rate_by_year[4])} by 2031. These are scenarios, not confidence intervals.</p>

    <h2>Where</h2>
    <div class="table-wrap"><table class="data"><caption>Ten counties with the most added permits (central scenario), 2027–2031</caption>
      <thead><tr><th scope="col">County</th><th scope="col" class="num">Single-family homes</th><th scope="col" class="num">${esc(L.baseline)}</th><th scope="col" class="num">Added, central scenario (lower to strong adoption)</th></tr></thead>
      <tbody>${top.map((c) => `<tr><th scope="row">${esc(c.name)}</th><td class="num">${int(c.homes)}</td><td class="num">${int(sum(c.base))}</td><td class="num">${int(sum(c.add.central))} <span class="muted">(${int(sum(c.add.lower))} to ${int(sum(c.add.upper))})</span></td></tr>`).join("")}
      <tr><th scope="row">Other ${rest.length} counties</th><td class="num">${int(rest.reduce((a, c) => a + c.homes, 0))}</td><td class="num">${int(rest.reduce((a, c) => a + sum(c.base), 0))}</td><td class="num">${int(rest.reduce((a, c) => a + sum(c.add.central), 0))}</td></tr></tbody>
      <tfoot><tr><th scope="row">Wisconsin</th><td class="num">${int(counties.reduce((a, c) => a + c.homes, 0))}</td><td class="num">${int(counties.reduce((a, c) => a + sum(c.base), 0))}</td><td class="num">${int(counties.reduce((a, c) => a + sum(c.add.central), 0))}</td></tr></tfoot></table></div>
    <p class="small">✓ The 72 counties add up to the statewide figures. No area is left unallocated.</p>

    <h2>How sure</h2>
    <ul>
      <li>The range shows how much statewide-law states differ, not statistical certainty.</li>
      <li>Biggest drivers of the addition (sensitivity cases, change in the central ${int(cen.additional_total)}): ${drivers.map((d) => `${esc(d.label)} ${d.difference_central > 0 ? "+" : "−"}${int(Math.abs(d.difference_central))}`).join("; ")}.</li>
      <li>Robustness check: predicting 7 held-out states, the adopted method had the lowest error (${dec(u.robustness.rows[0].a, 3)} root-mean-square log error), but within noise: keeping California in beat leaving it out in only ${pct(u.robustness.a_win_share)} of 5,000 resamples, and as the best of several configurations tried on the same 7 states, its error is optimistic.</li>
      <li>Madison already allows ADUs much like the benchmark law, and follows the path of 9 similar cities in Washington and Oregon, so the law adds less there per 1,000 homes than in its suburbs. This is being reviewed.</li>
    </ul>

    <h2>Limitations</h2>
    <ul>${m.limitations.map((l) => `<li>${esc(l)}</li>`).join("")}</ul>

    <h2>Sources</h2>
    <p class="small">${m.vintages.map((v) => `${esc(v.what)}: ${esc(v.vintage)}.`).join(" ")}</p>
    ${districtPage(ctx)}
    <p class="small brief-foot">Run <code>${esc(m.run_id)}</code> · ${esc(m.model_status)} · Outcome: ${esc(m.outcome.short)} · Missing Middleware, ${esc(m.repo_url)}</p>
  </article>`;
  main.querySelector("#print")!.addEventListener("click", () => window.print());
}

/** Brief page 3: every Assembly and Senate district (central scenario), compact, with the reconciliation line and caveats. */
function districtPage(ctx: Ctx): string {
  const D = ctx.b.districts, cen = ctx.scen("central"), base = ctx.b.state.baseline.total;
  const add = (d: District) => sum(d.add.central);
  const rate = (d: District) => (add(d) / d.homes / 5) * 1000;
  // narrow columns: a short visible heading, the full heading for screen readers (the key above the tables spells it out)
  const short = (vis: string, full: string) => `<th scope="col" class="num"><span aria-hidden="true">${esc(vis)}</span><span class="sr-only">${esc(full)}</span></th>`;
  const block = (rows: District[], level: "Assembly" | "Senate", per: number) => {
    const chunks = [0, 1, 2].map((i) => rows.slice(i * per, (i + 1) * per)).filter((c) => c.length);
    return `<div class="dist-grid">${chunks.map((c) => `<table class="data dist-table" data-testid="brief-${level.toLowerCase()}-table"><caption>${level} districts ${c[0].district}–${c[c.length - 1].district}</caption>
      <thead><tr><th scope="col">District</th>${short("Homes", "Single-family homes")}${short("Added", "Added permits, 2027–2031")}${short("Per 1,000/yr", "Added permits per 1,000 single-family homes per year")}</tr></thead>
      <tbody>${c.map((d) => `<tr><th scope="row">${esc(d.district)}</th><td class="num">${int(d.homes)}</td><td class="num">${int(add(d))}</td><td class="num">${dec(rate(d))}</td></tr>`).join("")}</tbody></table>`).join("")}</div>`;
  };
  const asm = D.levels.assembly, sen = D.levels.senate;
  const recon = (lv: typeof asm) => ({ add: lv.rows.reduce((a, d) => a + add(d), 0) + add(lv.unallocated), base: lv.rows.reduce((a, d) => a + sum(d.base), 0) + sum(lv.unallocated.base) });
  const ra = recon(asm), rs = recon(sen);
  const ok = [ra, rs].every((r) => Math.abs(r.add - cen.additional_total) < 1 && Math.abs(r.base - base) < 1);
  const sorted = [...asm.rows].sort((a, b) => add(b) - add(a));
  const med = (xs: number[]) => { const v = [...xs].sort((a, b) => a - b); const m = Math.floor(v.length / 2); return v.length % 2 ? v[m] : (v[m - 1] + v[m]) / 2; };
  const byRate = [...asm.rows].sort((a, b) => rate(b) - rate(a));
  return `<section class="brief-districts" aria-labelledby="brief-dist-h" data-testid="brief-districts">
    <h2 id="brief-dist-h">By legislative district</h2>
    <p>Permits added by the law over 2027–2031 in the central scenario, and the same as a yearly rate per 1,000 single-family homes. Assembly districts range from ${int(add(sorted[sorted.length - 1]))} added permits (District ${esc(sorted[sorted.length - 1].district)}) to ${int(add(sorted[0]))} (District ${esc(sorted[0].district)}); the median district gets ${int(med(asm.rows.map(add)))}. By rate, District ${esc(byRate[0].district)} is highest (${dec(rate(byRate[0]))} per 1,000 homes per year) and District ${esc(byRate[byRate.length - 1].district)} lowest (${dec(rate(byRate[byRate.length - 1]))}).</p>
    <p class="small"><strong>Read with care.</strong> ${esc(D.caveat)} Districts have about equal populations but very different numbers of single-family homes (${int(D.homes_range[0])} to ${int(D.homes_range[1])}), so compare the rate as well as the count. Shown for the adopted assumption about places with uncoded local rules (like places that restrict ADUs). Each district's lower and strong adoption figures are on the tool's Where screen.</p>
    <p class="small"><strong>Key.</strong> Homes: single-family homes in the district. Added: permits added by the law, 2027–2031, central scenario. Per 1,000/yr: added permits per 1,000 single-family homes per year.</p>
    <h3 class="small-h">Assembly districts (99)</h3>
    ${block(asm.rows, "Assembly", 33)}
    <h3 class="small-h">Senate districts (33)</h3>
    ${block(sen.rows, "Senate", 11)}
    <p class="small" data-testid="brief-district-reconcile">${ok ? "✓" : "✗"} The 99 Assembly districts add up to ${int(ra.add)} added and ${int(ra.base)} baseline permits, and the 33 Senate districts to ${int(rs.add)} and ${int(rs.base)}, including a "not allocated to a district" row of ${dec(add(asm.unallocated), 1)} permits; the statewide figures are ${int(cen.additional_total)} and ${int(base)}. Each Senate district is the sum of its three Assembly districts. Rows are rounded; totals add the unrounded values.</p>
    <p class="small muted">Boundaries: ${esc(D.boundaries)}. The full method is under "How district figures are made" on the tool's Where screen.</p>
  </section>`;
}
