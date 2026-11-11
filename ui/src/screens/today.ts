// The ADU bundle's "today" content, shown on the shared Wisconsin today page (ui/src/screens/wisconsin_today.ts):
// all housing in Wisconsin (Census and ACS figures the ADU bundle carries), and the ADU section: second-home permits
// under current law, current local ADU rules and recent ADU permits in the pilot places. Headings start at h3: the
// page gives each part its own h2.
import { xyChart, legendHTML } from "../charts";
import type { Bundle, StateData } from "../data";
import { dec, esc, int, pct, pill } from "../format";

const acs5 = (v: string) => v.replace(/ACS (\d{4})-(\d{4}) 5-year/, "ACS $1–$2, five-year average");

/** All housing in Wisconsin: homes, single-family homes, vacancy, homes permitted, the housing mix and two charts. */
export function allHousingHTML(s: StateData): string {
  const pep = s.housing_units_pep;
  const pepLast = pep[pep.length - 1];
  const bps = s.bps;
  const bLast = bps[bps.length - 1];
  const vr = s.vacancy_rate;
  const mixTotal = s.mix.reduce((a, m) => a + (m.value ?? 0), 0);
  const pr = s.production_rate;
  return `
  <p class="muted">Every figure shows its source year and status. Survey figures from the American Community Survey (ACS) are averages over 2020–2024, not a 2024 count.</p>
  <div class="tiles tiles-4">
    <section class="tile" aria-labelledby="t-units">
      <h3 id="t-units" class="tile-label">Homes in Wisconsin</h3>
      <p class="tile-num" data-testid="pep-units">${int(pepLast.value)}</p>
      <p class="tile-sub">housing units on 1 July ${pepLast.year} ${pill("observed")}</p>
      <p class="tile-note">Up ${int(pepLast.value - pep[0].value)} since ${pep[0].year}. ${esc(pepLast.vintage)}; no published margin of error.</p>
    </section>
    <section class="tile" aria-labelledby="t-sf">
      <h3 id="t-sf" class="tile-label">Single-family homes</h3>
      <p class="tile-num" data-testid="sf-homes">${int(s.homes.value)}</p>
      <p class="tile-sub">one-unit detached homes, ±${int(s.homes.moe)} ${pill("observed")}</p>
      <p class="tile-note">The base for every ADU rate in this tool. ${esc(acs5(s.homes.vintage))}.</p>
    </section>
    <section class="tile" aria-labelledby="t-vac">
      <h3 id="t-vac" class="tile-label">Vacant homes, including seasonal</h3>
      <p class="tile-num" data-testid="vacancy">${pct(vr.value, 1)}</p>
      <p class="tile-sub">of ${int(s.acs_total_units.value)} housing units (${int(s.vacant.value)} vacant), ±${pct(vr.moe, 1)} ${pill("calculated")}</p>
      <p class="tile-note">All vacant homes, including seasonal and recreational cabins, which are common in Wisconsin. Not a for-rent or for-sale vacancy rate. ${esc(acs5(vr.vintage))}.</p>
    </section>
    <section class="tile" aria-labelledby="t-bps">
      <h3 id="t-bps" class="tile-label">New homes permitted in ${bLast.year}, all types</h3>
      <p class="tile-num">${int(bLast.total)}</p>
      <p class="tile-sub">homes (units) in building permits, of which ${int(bLast["1unit"])} single-family ${pill("observed")}</p>
      <p class="tile-sub" data-testid="production-rate"><strong>${dec(pr.value, 1)}</strong> per 1,000 housing units (${int(pr.numerator)} ÷ ${int(pr.denominator)} on 1 July ${pr.year}) ${pill(pr.status)}</p>
      <p class="tile-note">${esc(bLast.source ?? "")}, ${bLast.year} final; ${pct(bLast.reported_share ?? null)} reported by places, the rest imputed by the Census Bureau. The rate divides by the Census housing-unit estimate for 1 July.</p>
    </section>
  </div>

  <div class="grid-2">
    <section class="card" aria-labelledby="h-pep">
      <h3 id="h-pep">Housing units, ${pep[0].year}–${pepLast.year}</h3>
      <div class="chart-box" id="pep-chart"></div>
      ${legendHTML([{ name: "Housing units (Census estimates)", color: "#17644f" }])}
      <details><summary>Show the data</summary>
        <div class="table-wrap"><table class="data"><caption>Housing units in Wisconsin, ${esc(pepLast.vintage)}</caption>
        <thead><tr><th scope="col">Year</th><th scope="col" class="num">Housing units</th><th scope="col">Status</th></tr></thead>
        <tbody>${pep.map((p) => `<tr><th scope="row">${p.year}</th><td class="num">${int(p.value)}</td><td>${pill(p.status)}</td></tr>`).join("")}</tbody></table></div>
      </details>
    </section>
    <section class="card" aria-labelledby="h-mix">
      <h3 id="h-mix">Housing mix</h3>
      <p class="muted">Share of ${int(mixTotal)} homes in these five types. ${esc(acs5(s.mix[0].vintage))}.</p>
      <div class="table-wrap"><table class="data mix"><caption class="sr-only">Housing units by type</caption>
        <thead><tr><th scope="col">Type</th><th scope="col" class="num">Homes</th><th scope="col" class="num">Share</th><th scope="col">Status</th></tr></thead>
        <tbody>${s.mix.map((m) => `<tr><th scope="row">${esc(m.label)}<span class="bar" style="width:${((m.value ?? 0) / mixTotal) * 100}%" aria-hidden="true"></span></th><td class="num">${int(m.value)} <span class="muted">±${int(m.moe)}</span></td><td class="num">${pct((m.value ?? 0) / mixTotal)}</td><td>${pill(m.status)}</td></tr>`).join("")}</tbody>
      </table></div>
    </section>
  </div>

  <section class="card" aria-labelledby="h-bps">
    <h3 id="h-bps">New homes permitted each year, all types</h3>
    <p class="muted">Census Building Permits Survey: homes (units) in permits issued by Wisconsin's permit-issuing places. This counts all new homes, not ADUs; there is no published statewide ADU series for Wisconsin. In ${pr.year}: ${dec(pr.value, 1)} homes permitted per 1,000 housing units.</p>
    <div class="chart-box" id="bps-chart"></div>
    ${legendHTML([{ name: "All homes permitted", color: "#17644f", kind: "bar" }, { name: "Single-family homes permitted", color: "#4b5450" }])}
    <details><summary>Show the data</summary>
      <div class="table-wrap"><table class="data" data-testid="bps-table"><caption>Homes permitted per year in Wisconsin</caption>
      <thead><tr><th scope="col">Year</th><th scope="col" class="num">All homes</th><th scope="col" class="num">Single-family</th><th scope="col" class="num">2–4 homes</th><th scope="col" class="num">5 or more</th><th scope="col" class="num">Reported share</th><th scope="col">Source</th></tr></thead>
      <tbody>${bps.map((b) => `<tr><th scope="row">${b.year}</th><td class="num">${int(b.total)}</td><td class="num">${int(b["1unit"])}</td><td class="num">${int(b["2_4"])}</td><td class="num">${int(b["5plus"])}</td><td class="num">${pct(b.reported_share ?? null)}</td><td class="small">${esc(b.source ?? "")}, ${esc(b.vintage ?? "")} <code>${esc(b.source_id ?? "")}</code></td></tr>`).join("")}</tbody></table></div>
    </details>
  </section>`;
}

export function drawAllHousingCharts(root: HTMLElement, s: StateData): void {
  const pep = s.housing_units_pep, pepLast = pep[pep.length - 1], bps = s.bps, bLast = bps[bps.length - 1];
  xyChart(root.querySelector<HTMLElement>("#pep-chart")!, {
    title: "Wisconsin housing units by year",
    desc: `Housing units rose from ${int(pep[0].value)} in ${pep[0].year} to ${int(pepLast.value)} in ${pepLast.year}.`,
    yLabel: "Housing units", xTicks: pep.map((p) => p.year), height: 220,
    yFormat: (y) => (y / 1e6).toFixed(1) + "M", yMax: 3e6,
    series: [{ name: "Housing units", color: "#17644f", values: pep.map((p) => ({ x: p.year, y: p.value })), marker: "circle" }],
  });
  xyChart(root.querySelector<HTMLElement>("#bps-chart")!, {
    title: `Homes permitted per year in Wisconsin, ${bps[0].year} to ${bLast.year}`,
    desc: `All homes permitted ranged from ${int(Math.min(...bps.map((b) => b.total ?? Infinity)))} to ${int(Math.max(...bps.map((b) => b.total ?? 0)))} a year; ${int(bLast.total)} in ${bLast.year}.`,
    yLabel: "Homes permitted per year", xTicks: bps.map((b) => b.year), height: 260,
    bars: { name: "All homes", color: "#17644f", values: bps.map((b) => ({ x: b.year, y: b.total })) },
    series: [{ name: "Single-family", color: "#4b5450", values: bps.map((b) => ({ x: b.year, y: b["1unit"] })), marker: "circle", width: 2 }],
  });
}

/** The ADU section: second-home permits under current law, current local ADU rules, recent permits in the pilot places. */
export function aduTodayHTML(b: Bundle, link: (path: string) => string): string {
  const s = b.state;
  const A = b.areas;
  // places and single-family homes by current local ADU rules (the Prohibited codings are shown together)
  const order = ["scenario_benchmark", "restricted", "prohibited", "undetermined"];
  const label: Record<string, string> = { scenario_benchmark: A.class_text.scenario_benchmark, restricted: A.class_text.restricted, prohibited: "Prohibits ADUs (explicitly, or no provision allows them)", undetermined: A.class_text.undetermined };
  const groups = new Map<string, { places: number; homes: number }>();
  for (const m of A.munis) {
    const k = m.current_class.startsWith("prohibited") ? "prohibited" : m.current_class;
    const g = groups.get(k) ?? { places: 0, homes: 0 };
    g.places += 1; g.homes += m.homes ?? 0;
    groups.set(k, g);
  }
  const keys = [...order.filter((k) => groups.has(k)), ...[...groups.keys()].filter((k) => !order.includes(k))];
  const totP = [...groups.values()].reduce((a, g) => a + g.places, 0), totH = [...groups.values()].reduce((a, g) => a + g.homes, 0);
  const recent = (b.pilots[0]?.permits.years ?? []).slice(-5).map((y) => y.year);
  return `
  <p class="muted">Accessory dwelling units (ADUs) plus single-family-to-duplex conversions on lots that already have a home, counted when the permit is issued. Their rates use a different base: per 1,000 <em>single-family</em> homes per year, not per 1,000 housing units of all types.</p>
  <div class="tiles tiles-3">
    <section class="tile tile-accent" aria-labelledby="t-adu-base">
      <h3 id="t-adu-base" class="tile-label">ADU permits expected under current law, 2027–2031</h3>
      <p class="tile-num" data-testid="today-baseline">${int(s.baseline.total)}</p>
      <p class="tile-sub">permits over five years, about ${int(s.baseline.total / 5)} a year (range ${int(s.baseline.low_total)} to ${int(s.baseline.high_total)}) ${pill("calculated")}</p>
      <p class="tile-note">The model's 2027–2031 average under current law: ${dec(s.baseline.rate_per_1000_per_year)} permits per 1,000 single-family homes per year. There is no observed statewide ADU series.</p>
    </section>
    <section class="tile" aria-labelledby="t-adu-allow">
      <h3 id="t-adu-allow" class="tile-label">Places that already allow ADUs much like the law</h3>
      <p class="tile-num" data-testid="today-benchmark-places">${int(groups.get("scenario_benchmark")?.places ?? 0)}</p>
      <p class="tile-sub">of ${int(totP)} cities, villages and towns, with ${int(groups.get("scenario_benchmark")?.homes ?? 0)} of Wisconsin's ${int(totH)} single-family homes ${pill("observed")}</p>
      <p class="tile-note">From the local ADU rules coded so far.</p>
    </section>
    <section class="tile" aria-labelledby="t-adu-uncoded">
      <h3 id="t-adu-uncoded" class="tile-label">Places whose ADU rules are not coded</h3>
      <p class="tile-num">${int(groups.get("undetermined")?.places ?? 0)}</p>
      <p class="tile-sub">with ${int(groups.get("undetermined")?.homes ?? 0)} single-family homes (${pct((groups.get("undetermined")?.homes ?? 0) / (totH || 1))}) ${pill("assumed")}</p>
      <p class="tile-note">The model treats them like places that allow ADUs with restrictions.</p>
    </section>
  </div>
  <section class="card" aria-labelledby="h-adu-rules">
    <h3 id="h-adu-rules">Current local ADU rules</h3>
    <div class="table-wrap"><table class="data" data-testid="today-adu-rules"><caption>Wisconsin cities, villages and towns by their current ADU rules, and their single-family homes (ACS 2020–2024)</caption>
      <thead><tr><th scope="col">Current rules</th><th scope="col" class="num">Places</th><th scope="col" class="num">Single-family homes</th><th scope="col" class="num">Share of single-family homes</th></tr></thead>
      <tbody>${keys.map((k) => { const g = groups.get(k)!; return `<tr><th scope="row">${esc(label[k] ?? A.class_text[k] ?? k)}</th><td class="num">${int(g.places)}</td><td class="num">${int(g.homes)}</td><td class="num">${pct(g.homes / (totH || 1))}</td></tr>`; }).join("")}</tbody>
      <tfoot><tr><th scope="row">Wisconsin</th><td class="num">${int(totP)}</td><td class="num">${int(totH)}</td><td class="num">100%</td></tr></tfoot></table></div>
    <p class="small muted">"Allows ADUs much like the law" is a partial reform: the statewide law could still add rights there. Each place's coding is on <a href="${link("/where")}">Where</a>.</p>
  </section>
  <section class="card" aria-labelledby="h-adu-recent">
    <h3 id="h-adu-recent">Recent ADU permits in the pilot places</h3>
    <p class="muted">There is no statewide count of ADU permits. These are the places whose own permit records we have.</p>
    <div class="table-wrap"><table class="data" data-testid="today-adu-permits"><caption>Second homes permitted on single-family lots (ADUs plus single-family-to-duplex conversions), homes, by year</caption>
      <thead><tr><th scope="col">Place</th>${recent.map((y) => `<th scope="col" class="num">${y}</th>`).join("")}</tr></thead>
      <tbody>${b.pilots.map((p) => `<tr><th scope="row"><a href="${link(`/pilot/${p.slug}`)}">${esc(p.name)}</a></th>${recent.map((y) => { const r = p.permits.years.find((x) => x.year === y); return `<td class="num">${r ? `${int(r.units)}${r.status === "provisional" ? " (provisional, partial year)" : ""}` : "—"}</td>`; }).join("")}</tr>`).join("")}</tbody></table></div>
    <p class="small muted">${esc(b.pilots[0]?.permits.label ?? "")}. Issued permits, from each city's own records.</p>
  </section>
  <p><a class="button" href="${link("/summary")}">What a statewide ADU law would add →</a></p>`;
}
