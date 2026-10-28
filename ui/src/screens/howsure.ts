import { bindUnknownPicker, details, unknownPicker, unknownVariant, type Ctx } from "../app";
import { stackHTML, tornadoHTML } from "../charts";
import { dec, esc, int, missing, pct, pill } from "../format";

export function renderHowSure(ctx: Ctx, main: HTMLElement): void {
  const u = ctx.b.uncertainty;
  const cen = ctx.scen("central");
  const homes = u.coverage_rates.reduce((a, c) => a + c.homes, 0);
  const add = u.coverage_rates.reduce((a, c) => a + c.additional_central, 0);
  const st = { observed: "observed", estimated: "calculated", assumed: "assumed" } as Record<string, string>;
  const G = u.sensitivity_groups;
  const sign = (v: number) => (v > 0 ? "+" : v < 0 ? "−" : "") + int(Math.abs(v));
  const cases = u.sensitivity_cases.filter((c) => c.id !== "adopted" && c.group === "addition");
  const sorted = [...cases].sort((a, b) => Math.abs(b.difference_central) - Math.abs(a.difference_central));
  const rights = u.coverage_rights;
  // Trace (places with homes, reference/gate5_trace.csv): the central addition by the basis of the current-law rate
  const tr = Object.fromEntries(u.trace.map((t) => [t.status, t]));
  const trAdd = u.trace.reduce((a, t) => a + t.additional_central, 0);
  const share = (k: string) => pct(tr[k].additional_central / trAdd, 1);
  // Unknown-rules switch: three precomputed runs; the adopted one equals every other number in the tool
  const U = ctx.b.unknown;
  const v = unknownVariant(ctx);
  const ad = U.variants.find((x) => x.adopted)!;
  const dSign = (x: number) => (Math.abs(x) < 0.5 ? "no change" : `${x > 0 ? "+" : "−"}${int(Math.abs(x))} vs adopted`);
  const CTX_LABEL: Record<string, string> = { urban: "Urban", suburban: "Suburban", small_community: "Small communities", rural: "Rural" };
  const sameFrom = (() => { // first year from which the three totals with the law are equal (to the permit)
    const t = U.variants.map((x) => x.with_law_by_year.central);
    for (let i = 0; i < 5; i++) if (t.every((s) => t.every((o) => o.slice(i).every((val, j) => Math.abs(val - s[i + j]) < 0.5)))) return 2027 + i;
    return null;
  })();

  main.innerHTML = `
  <h1>How sure are we?</h1>
  <p class="lede">How much of the estimate rests on observed facts, and how much it moves when one assumption changes. Three terms: the <strong>scenarios</strong> (lower, central, strong adoption) show how states differ; a <strong>sensitivity case</strong> changes one assumption and reruns the model; a <strong>robustness check</strong> tests a method by predicting states the model did not see.</p>

  <section class="card" aria-labelledby="h-trace">
    <h2 id="h-trace">What the law's addition rests on</h2>
    <p class="summary" data-testid="trace-summary">Of the <strong>${int(trAdd)}</strong> permits the law adds over 2027–2031 (central scenario), <strong>${share("observed")}</strong> (${int(tr.observed.additional_central)} permits) are in places whose current rate comes from their <strong>own permit records</strong>, <strong>${share("estimated")}</strong> (${int(tr.estimated.additional_central)}) in places whose rate is <strong>calculated</strong> from places with the same coded rules, and <strong>${share("assumed")}</strong> (${int(tr.assumed.additional_central)}) in places whose local rules we have <strong>not coded</strong>, so their rate is assumed.</p>
    ${stackHTML(u.trace.map((t) => ({ label: `${st[t.status]}: ${int(t.additional_central)} added permits`, value: t.additional_central, cls: `seg-${st[t.status]}` })), u.trace.map((t) => `${st[t.status]} ${pct(t.additional_central / trAdd, 1)} of the central addition`).join(", "))}
    <p>Every place's rate <em>with</em> the law is transferred from other states: what similar places reached after their statewide ADU laws (Madison: what similar cities in Washington and Oregon reached). No Wisconsin place has a rate measured under such a law.</p>
    ${details("Show the numbers", `<div class="table-wrap"><table class="data" data-testid="trace-table"><caption>Added permits over 2027–2031 by the basis of each place's current-law rate (places with single-family homes)</caption>
      <thead><tr><th scope="col">Current-law rate</th><th scope="col" class="num">Places with homes</th><th scope="col" class="num">Single-family homes</th><th scope="col" class="num">Baseline</th><th scope="col" class="num">Added: lower</th><th scope="col" class="num">central</th><th scope="col" class="num">strong adoption</th><th scope="col" class="num">Share of central</th></tr></thead>
      <tbody>${u.trace.map((t) => `<tr><th scope="row">${pill(t.status)}</th><td class="num">${int(t.areas)}</td><td class="num">${int(t.homes)}</td><td class="num">${int(t.baseline)}</td><td class="num">${int(t.additional_lower)}</td><td class="num">${int(t.additional_central)}</td><td class="num">${int(t.additional_upper)}</td><td class="num">${pct(t.additional_central / trAdd, 1)}</td></tr>`).join("")}</tbody></table></div>
      <p class="small">Source: reference/gate5_trace.csv. The lower and strong adoption scenarios split the same way, because each place's lower and strong levels are fixed multiples of its central level.</p>`)}
  </section>

  <section class="card" aria-labelledby="h-unk">
    <h2 id="h-unk">What if places with uncoded rules behave differently?</h2>
    <p class="summary"><strong>${int(U.uncoded_areas)}</strong> of Wisconsin's 1,925 cities, villages and towns, holding <strong>${pct(U.uncoded_homes / U.state_homes)}</strong> of its single-family homes (${int(U.uncoded_homes)} of ${int(U.state_homes)}), have local ADU rules we have not coded. The model treats them like places that allow ADUs with restrictions. Pick another assumption to see what changes.</p>
    ${unknownPicker(ctx, "unk-howsure")}
    <div class="tiles tiles-3" data-testid="unknown-tiles">
      <section class="tile"><h3 class="tile-label">Without statewide reform (baseline)</h3><p class="tile-num" data-testid="unk-baseline">${int(v.baseline_total)}</p><p class="tile-sub">permits over 2027–2031</p><p class="delta">${dSign(v.d_baseline)}</p></section>
      <section class="tile"><h3 class="tile-label">Added by the law (central scenario)</h3><p class="tile-num" data-testid="unk-additional">+${int(v.additional_total.central)}</p><p class="tile-sub">permits over 2027–2031</p><p class="delta">${dSign(v.d_additional.central)}</p></section>
      <section class="tile"><h3 class="tile-label">Total with the law (central scenario)</h3><p class="tile-num" data-testid="unk-total">${int(v.with_law_total.central)}</p><p class="tile-sub">permits over 2027–2031</p><p class="delta">${dSign(v.d_with_law.central)}</p></section>
    </div>
    <p><strong>What changes:</strong> the baseline moves a lot, the law's addition moves the other way, and the total with the law barely moves. A place's rate with the law comes from what similar places reached in other states, not from its current rules, so a lower current rate means a bigger addition and a higher one a smaller addition.${sameFrom ? ` From ${sameFrom}, when the law is fully in effect, the three totals are the same.` : ""}</p>
    <div class="table-wrap"><table class="data" data-testid="unknown-table"><caption>The three assumptions for places with uncoded rules: permits over 2027–2031</caption>
      <thead><tr><th scope="col">Places with uncoded rules behave…</th><th scope="col" class="num">Their current rate (per 1,000 homes per year)</th><th scope="col" class="num">Baseline</th><th scope="col" class="num">Added: lower</th><th scope="col" class="num">central</th><th scope="col" class="num">strong adoption</th><th scope="col" class="num">Total with the law, central</th></tr></thead>
      <tbody>${U.variants.map((x) => `<tr class="${x.id === v.id ? "hl-row" : ""}" data-variant="${x.id}"><th scope="row">${esc(x.label)}</th><td class="num">${dec(x.x_rate_uncoded, 3)}</td><td class="num">${int(x.baseline_total)}</td><td class="num">${int(x.additional_total.lower)}</td><td class="num">${int(x.additional_total.central)}</td><td class="num">${int(x.additional_total.upper)}</td><td class="num">${int(x.with_law_total.central)}</td></tr>`).join("")}</tbody></table></div>
    ${details("By year and by type of place", `<div class="table-wrap"><table class="data"><caption>Total with the law by year, central scenario (permits)</caption>
      <thead><tr><th scope="col">Assumption</th>${[2027, 2028, 2029, 2030, 2031].map((y) => `<th scope="col" class="num">${y}</th>`).join("")}</tr></thead>
      <tbody>${U.variants.map((x) => `<tr><th scope="row">${esc(x.label)}</th>${x.with_law_by_year.central.map((t) => `<td class="num">${int(t)}</td>`).join("")}</tr>`).join("")}</tbody></table></div>
      <div class="table-wrap"><table class="data"><caption>${esc(v.label)}: by type of place, permits over 2027–2031 (central scenario; change from the adopted assumption in brackets)</caption>
      <thead><tr><th scope="col">Type of place</th><th scope="col" class="num">Single-family homes (uncoded)</th><th scope="col" class="num">Baseline</th><th scope="col" class="num">Added, central</th></tr></thead>
      <tbody>${v.contexts.map((c) => { const a0 = ad.contexts.find((z) => z.id === c.id)!; const d = (x: number, y: number) => (v.adopted ? "" : ` (${Math.abs(x - y) < 0.5 ? "0" : `${x > y ? "+" : "−"}${int(Math.abs(x - y))}`})`); return `<tr><th scope="row">${esc(CTX_LABEL[c.id] ?? c.id)}</th><td class="num">${int(c.homes)} (${int(c.uncoded_homes)})</td><td class="num">${int(c.baseline)}${d(c.baseline, a0.baseline)}</td><td class="num">${int(c.additional_central)}${d(c.additional_central, a0.additional_central)}</td></tr>`; }).join("")}</tbody></table></div>
      <p class="small">Each assumption is a full rerun of the model that changes only the current rate of places with uncoded rules: like places that restrict ADUs (Madison 2014–2023 and Fitchburg; adopted), like places that prohibit them (Pleasant Prairie and Sun Prairie before reform), or like places that already allow them as the bill would (Madison 2022–2025). The Where map uses the same switch for counties and municipalities; legislative districts are shown for the adopted assumption only. Run group ${esc(U.run_group_id)}; ${esc(U.source)}.</p>`)}
  </section>

  <section class="card" aria-labelledby="h-cov">
    <h2 id="h-cov">What each place's current-law rate rests on</h2>
    <p class="muted">Share of Wisconsin's ${int(homes)} single-family homes by the basis of their current ADU permit rate.</p>
    ${stackHTML(u.coverage_rates.map((c) => ({ label: `${c.status}: ${int(c.homes)} homes`, value: c.homes, cls: `seg-${st[c.status]}` })), u.coverage_rates.map((c) => `${st[c.status]} ${pct(c.homes / homes)} of homes`).join(", "))}
    <div class="table-wrap"><table class="data" data-testid="coverage-table"><caption>Areas, homes and permits by basis of the current-law rate (central scenario for additional permits)</caption>
      <thead><tr><th scope="col">Basis</th><th scope="col" class="num">Areas</th><th scope="col" class="num">Single-family homes</th><th scope="col" class="num">Share of homes</th><th scope="col" class="num">Baseline, 2027–2031</th><th scope="col" class="num">Additional, 2027–2031</th><th scope="col" class="num">Share of additional</th></tr></thead>
      <tbody>${u.coverage_rates.map((c) => `<tr><th scope="row">${pill(c.status)} <span class="small">${esc(c.label.split(": ")[1] ?? c.label)}</span></th><td class="num">${int(c.areas)}</td><td class="num">${int(c.homes)}</td><td class="num">${pct(c.homes / homes)}</td><td class="num">${int(c.baseline)}</td><td class="num">${int(c.additional_central)}</td><td class="num">${pct(c.additional_central / add)}</td></tr>`).join("")}</tbody>
      <tfoot><tr><th scope="row">Wisconsin</th><td class="num">${int(u.coverage_rates.reduce((a, c) => a + c.areas, 0))}</td><td class="num">${int(homes)}</td><td class="num">100%</td><td class="num">${int(u.coverage_rates.reduce((a, c) => a + c.baseline, 0))}</td><td class="num">${int(add)}</td><td class="num">100%</td></tr></tfoot>
    </table></div>
    <h3>Local ADU rules</h3>
    <div class="table-wrap"><table class="data"><caption>Areas by how their local ADU rules were established</caption>
      <thead><tr><th scope="col">Rules</th><th scope="col" class="num">Areas</th><th scope="col" class="num">Single-family homes</th><th scope="col" class="num">Share of homes</th><th scope="col" class="num">Additional, central</th></tr></thead>
      <tbody>${rights.map((r) => `<tr><th scope="row">${pill(r.status === "assumed" ? "assumed" : "observed")} ${esc(r.label)}</th><td class="num">${int(r.areas)}</td><td class="num">${int(r.homes)}</td><td class="num">${pct(r.homes / homes)}</td><td class="num">${int(r.additional_central)}</td></tr>`).join("")}</tbody></table></div>
    <h3>By current local rules</h3>
    <div class="table-wrap"><table class="data"><caption>Additional permits over 2027–2031 by each place's current ADU rules</caption>
      <thead><tr><th scope="col">Current rules</th><th scope="col" class="num">Areas</th><th scope="col" class="num">Single-family homes</th><th scope="col" class="num">Baseline</th><th scope="col" class="num">Additional: lower</th><th scope="col" class="num">central</th><th scope="col" class="num">strong adoption</th></tr></thead>
      <tbody>${u.classes.map((c) => `<tr><th scope="row">${esc(c.label)}</th><td class="num">${int(c.areas)}</td><td class="num">${int(c.homes)}</td><td class="num">${int(c.baseline)}</td><td class="num">${int(c.additional_lower)}</td><td class="num">${int(c.additional_central)}</td><td class="num">${int(c.additional_upper)}</td></tr>`).join("")}</tbody></table></div>
    <p class="muted small">How much the baseline moves if these defaults are wrong is in the sensitivity analysis below, group (b).</p>
  </section>

  <section class="card" aria-labelledby="h-sens">
    <h2 id="h-sens">Sensitivity analysis: what moves the estimate</h2>
    <p class="summary">Each case changes one assumption and reruns the model. The cases are grouped by which number they move: what the law adds statewide, today's rates (the baseline), or only where permits land. The central scenario adds <strong data-testid="sens-central">${int(cen.additional_total)}</strong> permits over 2027–2031 on top of a baseline of ${int(ctx.b.state.baseline.total)}.</p>

    <h3 data-testid="sens-group-addition">(a) ${esc(G.addition.title)}</h3>
    <p class="muted">${esc(G.addition.intro)} The largest: ${esc(sorted[0].label.toLowerCase())} (${sign(sorted[0].difference_central)}).</p>
    ${tornadoHTML(sorted.map((c) => ({ label: c.label, value: c.difference_central })), "added permits over 2027–2031")}
    <div class="table-wrap"><table class="data" data-testid="sens-table"><caption>Cases that change the addition: added permits over 2027–2031</caption>
      <thead><tr><th scope="col">Case</th><th scope="col">What it means</th><th scope="col" class="num">Lower</th><th scope="col" class="num">Central</th><th scope="col" class="num">Strong adoption</th><th scope="col" class="num">Change in central</th></tr></thead>
      <tbody>${u.sensitivity_cases.filter((c) => c.group === "addition").map((c) => `<tr class="${c.id === "adopted" ? "hl-row" : ""}"><th scope="row">${esc(c.label)}</th><td class="small">${esc(c.what)}</td><td class="num">${c.lower === null ? missing(c.missing_reason ?? "not run") : int(c.lower)}</td><td class="num">${int(c.central)}</td><td class="num">${c.upper === null ? missing(c.missing_reason ?? "not run") : int(c.upper)}</td><td class="num">${c.difference_central === 0 ? "—" : sign(c.difference_central)}</td></tr>`).join("")}</tbody></table></div>

    <h3 data-testid="sens-group-baseline">(b) ${esc(G.baseline.title)}</h3>
    <p class="muted">${esc(G.baseline.intro)}</p>
    <div class="table-wrap"><table class="data" data-testid="baseline-only-table"><caption>Cases that change only the current-law baseline: permits over 2027–2031, central scenario</caption>
      <thead><tr><th scope="col">Case</th><th scope="col">What it means</th><th scope="col" class="num">Baseline</th><th scope="col" class="num">Change in baseline</th><th scope="col" class="num">Change in added</th><th scope="col" class="num">Change in total with the law</th></tr></thead>
      <tbody>${u.baseline_only.map((c) => `<tr><th scope="row">${esc(c.label)}</th><td class="small">${esc(c.what)}</td><td class="num">${int(c.baseline)}</td><td class="num"><strong>${sign(c.d_baseline)}</strong></td><td class="num">${sign(c.d_additional)}</td><td class="num">${sign(c.d_with_law)}</td></tr>`).join("")}</tbody></table></div>

    <h3 data-testid="sens-group-local">(c) ${esc(G.local.title)}</h3>
    <p>${esc(G.local.intro)} ${esc(u.local_effects.text)}</p>
    <p class="small">${esc(u.local_effects.example)} ${esc(u.local_effects.not_computed)}</p>
    ${u.sensitivity_cases.filter((c) => c.group === "local").map((c) => `<p class="small" data-testid="sens-local-case"><strong>${esc(c.label)}.</strong> ${esc(c.what)} Central ${int(c.central)} added permits (${c.difference_central === 0 ? "no change" : sign(c.difference_central)}).</p>`).join("")}
    ${details("Technical names of the cases", `<ul class="small">${u.sensitivity_cases.map((c) => `<li><strong>${esc(c.label)}</strong>: ${esc(c.change_as_recorded)} (${esc(c.source)})</li>`).join("")}<li>Baseline-only cases: reference/wi_baseline_sensitivities.csv (baseline) and reference/adu_model_baseline_only_effects.csv (effect on the addition, from the adopted engine with only the current-law rate changed).</li></ul>`)}
  </section>

  <section class="card" aria-labelledby="h-rob">
    <h2 id="h-rob">Robustness checks: predicting states the model did not see</h2>
    <p class="muted">Each of the ${u.robustness.n_states} non-California statewide-law states was left out in turn and predicted from the rest. The number is the ${esc(u.robustness.units)}. Column A keeps California in the eight states' typical level (adopted); B takes it out.</p>
    <div class="table-wrap"><table class="data" data-testid="robust-table"><caption>Robustness checks</caption>
      <thead><tr><th scope="col">Alternative</th><th scope="col" class="num">Error, California in (A)</th><th scope="col" class="num">Error, California out (B)</th><th scope="col">Result</th></tr></thead>
      <tbody>${u.robustness.rows.map((r) => `<tr class="${r.adopted ? "hl-row" : ""}"><th scope="row">${esc(r.label)}</th><td class="num">${dec(r.a, 3)}</td><td class="num">${dec(r.b, 3)}</td><td>${esc(r.result)}</td></tr>`).join("")}</tbody></table></div>
    <p class="muted small">Keeping California in (A) gave the lower error in ${pct(u.robustness.a_win_share)} of 5,000 resamples of the 7 states: better, but within noise. Source: ${esc(u.robustness.source)}.</p>
  </section>

  <section class="card" aria-labelledby="h-ch">
    <h2 id="h-ch">The strongest challenges to these numbers</h2>
    <ol class="plain-ol">${u.challenges.map((c) => `<li><strong>${esc(c.title)}.</strong> ${esc(c.text)}</li>`).join("")}</ol>
    <p><a href="${ctx.link("/why")}">See the evidence and the assumptions you can challenge →</a></p>
  </section>`;
  bindUnknownPicker(ctx, main, "unk-howsure");
}
