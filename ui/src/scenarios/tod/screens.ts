// The seven TOD screens. Every number comes from the bundle (scripts/build_tod_bundle.py); the browser only selects,
// sorts and formats. Plain language first: each screen opens with what the reader is looking at.
import { legendHTML, xyChart } from "../../charts";
import { dec, esc, int, pill, small } from "../../format";
import { estimateCardHTML } from "../../estimate";
import { num, rangeCardHTML, sideLinesHTML, sideValue } from "../../range";
import { howSureChartsHTML, type InputRow, type OtherRow } from "../../tornado";
import { flatRange, type SummaryInput, type WiHomes } from "../../summary";
import type { ShellEnv } from "../types";
import { mapKey, rapidMapKey, stationMap } from "./map";
import { SCEN_IDS, type AggRow, type DensityBands, type Muni, type Pilot, type ScenId, type TodBundle } from "./types";

const YEARS = [2027, 2028, 2029, 2030, 2031];
/** The rail and rapid lines whose stops count as major transit stops in the modelled law. */
const RAPID_LINES = "Rail and rapid transit means The Hop and Kenosha streetcars, CONNECT 1 and Madison's Rapid Route A.";
const C: Record<string, string> = { baseline: "#4b5450", little: "#2f6db5", typical: "#17644f", strong: "#7b3fb0" };
const DASH: Record<string, string | undefined> = { baseline: "7 5", little: "2 4", typical: undefined, strong: "9 3 2 3" };

/** A share: three significant figures from 1% (11.5%, 5.47%), two below (0.055%, 0.8%). */
export function sharePct(v: number): string {
  const p = v * 100;
  if (p === 0) return "0%";
  const a = Math.abs(p);
  return `${p < 0 ? "−" : ""}${Number(a.toPrecision(a >= 1 ? 3 : 2)).toLocaleString("en-US", { maximumFractionDigits: 3 })}%`;
}
const more = (summary: string, html: string) => `<details class="more"><summary>${esc(summary)}</summary>${html}</details>`;
const lcFirst = (s: string) => s.charAt(0).toLowerCase() + s.slice(1);
const scen = (b: TodBundle, id: ScenId) => b.statewide.scenarios.find((s) => s.id === id)!;
const signed = (v: number, d = 3) => `${v > 0 ? "+" : v < 0 ? "−" : ""}${dec(Math.abs(v), d)}`;
const placeName = (n: string) => n.replace(/ (city|village|town)$/, " ($1)");
/** AQ-054 shared unit: one plain line per scenario against the statewide all-housing baseline, never added to other reforms. */
function sharedLine(b: TodBundle): string {
  const s = b.statewide;
  const t = scen(b, "typical"), l = scen(b, "little"), g = scen(b, "strong");
  return `On the central line the law adds about ${int(t.per_year)} homes a year statewide, about ${sharePct(t.share_of_state_baseline)} above the ${int(s.state_baseline_per_year)} homes a year Wisconsin is expected to permit under current law (all homes, all places, 2027–2031), or ${sharePct(t.share_of_acs_homes)} of Wisconsin's ${int(s.acs_homes)} homes (ACS 2020–2024). The lower line adds about ${int(l.per_year)} a year (${sharePct(l.share_of_state_baseline)} above) and the upper line about ${int(g.per_year)} a year (${sharePct(g.share_of_state_baseline)} above).`;
}
const ext = (url: string, label: string) => `<a href="${esc(url)}" target="_blank" rel="noopener">${esc(label)}<span class="sr-only"> (opens in a new tab)</span> ↗</a>`;

// ---- 1. Wisconsin today ------------------------------------------------------------------------
/** Order of the two density measures on the today screen (owner has not chosen which leads; swap to reorder). */
const TODAY_MEASURES: ("raw" | "ring")[] = ["raw", "ring"];
const TODAY_VIEWS: [string, string][] = [["milwaukee", "Milwaukee area"], ["madison", "Madison area"], ["kenosha", "Kenosha"]];
/** Homes per acre of land, one decimal. */
const hpa = (v: number) => dec(v, 1);
/** "Times as dense", one decimal with a times sign. */
const times = (v: number) => `${dec(v, 1)}×`;

/** The 2020 snapshot: existing homes per acre of land near Wisconsin's rail and rapid stops, beside five older non-industrial reform places. */
function densityToday(b: TodBundle, view: string): string {
  const t = b.today;
  const half = t.context.half, qtr = t.context.quarter;
  const n = t.reforms.length;
  const years = `${t.reform_years[0]}–${t.reform_years[1]}`;
  const reformName = (x: { place: string; area: string | null }) => x.area ? `${x.place} (${x.area})` : x.place;
  const cells = (x: DensityBands) => `<td class="num">${hpa(x.quarter.homes_per_acre)}</td><td class="num">${hpa(x.half.homes_per_acre)}</td>`;
  const sysByName = (nm: string) => t.systems.find((x) => x.name === nm)?.half.stops ?? 0;
  const together = `Five places together (${years})`;
  const allRows: [string, DensityBands][] = [["Wisconsin, all rail and rapid stops", t.state], ...t.systems.map((x) => [x.label, x] as [string, DensityBands]),
    [together, t.five_places], ...t.reforms.map((x) => [`${reformName(x)}, ${x.year}`, x] as [string, DensityBands])];
  const leftOut = t.left_out.map((x) => `${reformName(x)}, ${x.year}`).join("; ");
  const qtrLine = qtr.difference < 0
    ? `<li>Within ¼ mile: Wisconsin already denser (${hpa(qtr.wisconsin)} vs ${hpa(qtr.five_places)}).</li>`
    : `<li>Within ¼ mile: about ${int(qtr.extra_homes_rounded)} more homes (${hpa(qtr.wisconsin)} vs ${hpa(qtr.five_places)}).</li>`;
  // measure 1: raw homes per acre near the stops
  const rawBlock = `<div data-testid="density-raw">
  <div>
    <section class="card" aria-labelledby="h-density-wi"><h3 id="h-density-wi">Wisconsin, by transit system</h3>
      <div class="table-wrap"><table class="data tod-density" data-testid="density-wi-table"><caption>Existing homes per acre of land near rail and rapid stops, ${t.year} census</caption>
        <thead><tr><th scope="col">Transit system</th><th scope="col" class="num">Stops</th><th scope="col" class="num">Homes per acre, within ¼ mile</th><th scope="col" class="num">Homes per acre, within ½ mile</th></tr></thead>
        <tbody>${t.systems.map((x) => `<tr><th scope="row">${esc(x.label)}<br><span class="small muted">${esc(x.lines)}</span></th><td class="num">${int(x.half.stops)}</td>${cells(x)}</tr>`).join("")}
        <tr><th scope="row"><strong>Wisconsin, all</strong></th><td class="num"><strong>${int(t.state.half.stops)}</strong></td>${cells(t.state)}</tr></tbody></table></div>
      <p class="small muted">BRT is bus rapid transit.</p></section>
    <section class="card" aria-labelledby="h-density-five"><h3 id="h-density-five">Five places that upzoned near rail, ${years}</h3>
      <div class="table-wrap"><table class="data tod-density" data-testid="density-five-table"><caption>Existing homes per acre of land near each place's reform stops, ${t.year} census</caption>
        <thead><tr><th scope="col">Place, year upzoned</th><th scope="col" class="num">Stops</th><th scope="col" class="num">Homes per acre, within ¼ mile</th><th scope="col" class="num">Homes per acre, within ½ mile</th></tr></thead>
        <tbody>${t.reforms.map((x) => `<tr><th scope="row">${esc(reformName(x))}, ${x.year}</th><td class="num">${int(x.half.stops)}</td>${cells(x)}</tr>`).join("")}
        <tr><th scope="row"><strong>Five places together</strong></th><td class="num"><strong>${int(t.five_places.half.stops)}</strong></td>${cells(t.five_places)}</tr></tbody></table></div>
      <p class="small muted">Only the stops each reform upzoned.${t.stops_counted_twice > 0 ? ` Together counts each stop once (${int(t.five_places.half.stops)}, not ${int(t.five_places.half.stops + t.stops_counted_twice)}).` : ""}${leftOut ? ` Industrial rezones left out: ${esc(leftOut)}.` : ""}</p></section>
  </div>
  ${more("Show homes and acres of land", `<div class="table-wrap"><table class="data tod-density" data-testid="density-detail-table"><caption>Existing homes and acres of land near the stops and ½ to 1 mile away, ${t.year} census</caption>
    <thead><tr><th scope="col">Stops</th><th scope="col" class="num">Homes, within ¼ mile</th><th scope="col" class="num">Land acres, within ¼ mile</th><th scope="col" class="num">Homes, within ½ mile</th><th scope="col" class="num">Land acres, within ½ mile</th><th scope="col" class="num">Homes, ½ to 1 mile away</th><th scope="col" class="num">Land acres, ½ to 1 mile away</th></tr></thead>
    <tbody>${allRows.map(([nm, x]) => `<tr><th scope="row">${esc(nm)}</th><td class="num">${int(x.quarter.homes)}</td><td class="num">${int(x.quarter.acres)}</td><td class="num">${int(x.half.homes)}</td><td class="num">${int(x.half.acres)}</td><td class="num">${int(x.ring.homes)}</td><td class="num">${int(x.ring.acres)}</td></tr>`).join("")}</tbody></table></div>`)}
</div>`;
  // measure 2: near the stops compared with the ring ½–1 mile away (the same city's nearby neighborhoods)
  const ringRow = (nm: string, x: DensityBands, strong = false) => {
    const w = (v: string) => strong ? `<strong>${v}</strong>` : v;
    return `<tr><th scope="row">${w(esc(nm))}</th><td class="num">${w(hpa(x.ring.homes_per_acre))}</td><td class="num">${w(times(x.vs_ring.quarter))}</td><td class="num">${w(times(x.vs_ring.half))}</td></tr>`;
  };
  const ringBlock = `<section class="card" aria-labelledby="h-density-ring" data-testid="density-ring"><h3 id="h-density-ring">Near the stops compared with ½ to 1 mile away</h3>
    <ul class="tod-points">
      <li>${esc(t.ring_caveats[0])}</li>
      <li>Within ½ mile, Wisconsin: <strong data-testid="ring-half-wi">${times(t.state.vs_ring.half)}</strong> the ring.</li>
      <li>Five places together: <strong data-testid="ring-half-five">${times(t.five_places.vs_ring.half)}</strong> the ring.</li>
      ${t.ring_caveats.slice(1).map((c) => `<li>${esc(c)}</li>`).join("")}
    </ul>
    <div class="table-wrap"><table class="data tod-density" data-testid="density-ring-table"><caption>Homes per acre of land ½ to 1 mile from the stops, and how many times as dense the land near the stops is, ${t.year} census</caption>
      <thead><tr><th scope="col">Stops</th><th scope="col" class="num">Homes per acre, ½ to 1 mile away</th><th scope="col" class="num">Times as dense within ¼ mile</th><th scope="col" class="num">Times as dense within ½ mile</th></tr></thead>
      <tbody><tr><th scope="rowgroup" colspan="4" class="tod-group">Wisconsin</th></tr>${t.systems.map((x) => ringRow(x.label, x)).join("")}${ringRow("Wisconsin, all", t.state, true)}</tbody>
      <tbody><tr><th scope="rowgroup" colspan="4" class="tod-group">${n === 5 ? "Five" : int(n)} places that upzoned near rail, ${years}</th></tr>${t.reforms.map((x) => ringRow(`${reformName(x)}, ${x.year}`, x)).join("")}${ringRow("Five places together", t.five_places, true)}</tbody></table></div>
    <p class="small muted">Times as dense = homes per acre near the stops ÷ homes per acre ½ to 1 mile away. ${pill("calculated")}</p>
  </section>`;
  return `
  <h2 class="section-h" id="h-density">How built-up the land near rail and rapid stops is</h2>
  <ul class="tod-points">
    <li>One snapshot: the ${t.year} census.</li>
    <li>Existing homes per acre of land.</li>
    <li>Beside five places that upzoned long ago.</li>
    <li>Industrial rezones left out.</li>
  </ul>
  <div class="tiles tiles-3" data-testid="density-tiles">
    <section class="tile" aria-labelledby="t-rapid-stops"><h3 id="t-rapid-stops" class="tile-label">Rail and rapid transit stops</h3>
      <p class="tile-num" data-testid="rapid-stops">${int(t.stops_total)}</p>
      <p class="tile-sub">Milwaukee ${int(sysByName("Milwaukee"))} · Madison ${int(sysByName("Madison"))} · Kenosha ${int(sysByName("Kenosha"))} ${pill("observed")}</p>
      <p class="tile-note">Bus rapid transit and streetcar stops. Each direction of a street counts once.</p></section>
    <section class="tile tile-accent" aria-labelledby="t-hpa-half"><h3 id="t-hpa-half" class="tile-label">Homes per acre within ½ mile</h3>
      <p class="tile-num" data-testid="hpa-half">${hpa(t.state.half.homes_per_acre)}</p>
      <p class="tile-sub">Five older reform places: <strong data-testid="hpa-half-five">${hpa(t.five_places.half.homes_per_acre)}</strong> ${pill("calculated")}</p>
      <p class="tile-note">Wisconsin: ${int(t.state.half.homes)} homes on ${int(t.state.half.acres)} acres of land.</p></section>
    <section class="tile" aria-labelledby="t-hpa-qtr"><h3 id="t-hpa-qtr" class="tile-label">Homes per acre within ¼ mile</h3>
      <p class="tile-num" data-testid="hpa-quarter">${hpa(t.state.quarter.homes_per_acre)}</p>
      <p class="tile-sub">Five older reform places: <strong data-testid="hpa-quarter-five">${hpa(t.five_places.quarter.homes_per_acre)}</strong> ${pill("calculated")}</p>
      <p class="tile-note">Wisconsin: ${int(t.state.quarter.homes)} homes on ${int(t.state.quarter.acres)} acres of land.</p></section>
  </div>
  <section class="card" aria-labelledby="h-density-map"><h3 id="h-density-map">Where the stops are</h3>
    <form id="tod-today-view"><fieldset class="seg"><legend>Map area</legend>${TODAY_VIEWS.map(([v, l]) => `<label><input type="radio" name="tod-today-view" value="${v}" ${view === v ? "checked" : ""}> ${l}</label>`).join("")}</fieldset></form>
    ${stationMap(b.map, { view, rapidOnly: true, labels: ["Milwaukee city", "Wauwatosa city", "Madison city", "Kenosha city"], title: `Rail and rapid transit stops: ${TODAY_VIEWS.find(([v]) => v === view)![1]}`, desc: "Dots are rail and rapid transit stops. The darker circle is land within ¼ mile, the paler ring ¼ to ½ mile. The tables below give homes per acre of land in these circles." })}
    ${rapidMapKey()}
  </section>
${TODAY_MEASURES.map((m) => (m === "raw" ? rawBlock : ringBlock)).join("")}
  <div class="grid-2">
    <section class="card" aria-labelledby="h-density-gap" data-testid="density-context"><h3 id="h-density-gap">If Wisconsin matched the five places</h3>
      <ul class="tod-points">
        <li>Within ½ mile: ${hpa(half.wisconsin)} vs ${hpa(half.five_places)} homes per acre.</li>
        <li>At ${hpa(half.five_places)}: about <strong data-testid="density-extra">${int(half.extra_homes_rounded)}</strong> more homes (${half.extra_share >= 0 ? "+" : "−"}${Math.round(Math.abs(half.extra_share) * 100)}%).</li>
        ${qtrLine}
      </ul>
      <p class="small muted">${dec(half.difference, 3)} more homes per acre × ${int(half.acres)} acres of land within ½ mile ≈ ${int(half.extra_homes)} homes, beside ${int(half.homes)} there now. ${pill("calculated")} A what-if for scale, not a forecast.</p></section>
    <section class="card" aria-labelledby="h-density-care" data-testid="density-caveats"><h3 id="h-density-care">Read with care</h3>
      <ul class="tod-points">${t.caveats.map((c) => `<li>${esc(c)}</li>`).join("")}</ul>
      <p class="small muted">${esc(t.source)}</p></section>
  </div>
  <h2 class="section-h" id="h-law-counts">Which stops and homes the law counts</h2>`;
}

export function today(b: TodBundle, env: ShellEnv, params: URLSearchParams, main: HTMLElement): void {
  const s = b.statewide;
  const view = TODAY_VIEWS.some(([v]) => v === params.get("view")) ? params.get("view")! : "milwaukee";
  const max = Math.max(...s.ladder.map((l) => l.homes));
  main.innerHTML = `
  <h1>Homes near major transit stops in Wisconsin today</h1>
  <p class="lede">The modelled law: every Wisconsin city with rail or rapid transit stops zones a district for apartments, by right, on 15% of the land within ¼ mile of those stops. This page shows how many homes are near major transit stops today, how many new homes are expected there without the law, and which transit lines count. Homes are housing units; new homes are counted when the building permit is issued.</p>
  <div class="tiles tiles-3">
    <section class="tile tile-accent"><h2 class="tile-label">Homes near qualifying stops</h2>
      <p class="tile-num" data-testid="stock-homes">${int(s.stock_homes)}</p>
      <p class="tile-sub">of ${int(s.state_homes)} homes in Wisconsin in the 2020 census (${sharePct(s.stock_homes / s.state_homes)}) ${pill("observed")}</p>
      <p class="tile-note">Within ½ mile of a rail or rapid transit station, or ¼ mile of a stop on a bus route every 15 minutes (the main case). Counted from 2020 census blocks. To compare reforms, the tool uses Wisconsin's newer count of <span data-testid="acs-homes">${int(s.acs_homes)}</span> homes (ACS 2020–2024).</p></section>
    <section class="tile"><h2 class="tile-label">New homes expected near these stops under current law, 2027–2031</h2>
      <p class="tile-num" data-testid="baseline-total">${int(s.baseline.total)}</p>
      <p class="tile-sub">homes permitted over five years (range ${int(s.baseline.low_total)}–${int(s.baseline.high_total)}) ${pill("calculated")}</p>
      <p class="tile-note">That is ${sharePct(s.baseline.total / s.state_baseline_total)} of the ${int(s.state_baseline_total)} homes Wisconsin is expected to permit statewide over 2027–2031: each place's expected permits times its share of homes near stops.</p></section>
    <section class="tile"><h2 class="tile-label">Share in the cities of Milwaukee and Madison</h2>
      <p class="tile-num" data-testid="two-cities-share">${sharePct(s.homes_two_cities.share)}</p>
      <p class="tile-sub">${int(s.homes_two_cities.milwaukee)} homes in Milwaukee and ${int(s.homes_two_cities.madison)} in Madison, of the ${int(s.stock_homes)} ${pill("observed")}</p>
      <p class="tile-note">No bus route outside the Milwaukee and Madison areas runs every 15 minutes. The Kenosha streetcar is the one qualifying line elsewhere.</p></section>
  </div>
  ${densityToday(b, view)}
  <section class="card"><h2>How many homes count as "near a major transit stop"</h2>
    <p>It depends on the definition. From the narrowest to the widest, with the main case in bold:</p>
    <div class="tod-bars" role="img" aria-label="${esc(`Homes near stops by definition, 2020 census: ${s.ladder.map((l) => `${l.label}: ${int(l.homes)}`).join("; ")}. The table below has the same values.`)}">
      ${s.ladder.map((l) => `<div class="tod-bar-row${l.main ? " is-main" : ""}${l.context ? " is-context" : ""}" aria-hidden="true"><span>${esc(l.label)}</span><span class="tod-bar-track"><span class="tod-bar-fill" style="width:${(l.homes / max) * 100}%"></span></span><span class="tod-bar-val">${int(l.homes)}</span></div>`).join("")}
    </div>
    <div class="table-wrap"><table class="data" data-testid="ladder-table"><caption>Homes near stops by definition, narrowest to widest (2020 census)</caption>
      <thead><tr><th scope="col">Definition</th><th scope="col" class="num">Qualifying stops</th><th scope="col" class="num">Homes nearby</th><th scope="col" class="num">Share of Wisconsin's ${int(s.state_homes)} homes (2020 census)</th></tr></thead>
      <tbody>${s.ladder.map((l) => `<tr><th scope="row">${l.main ? `<strong>${esc(l.label)}</strong>` : esc(l.label)}</th><td class="num">${int(l.stops)}</td><td class="num">${int(l.homes)}</td><td class="num">${sharePct(l.share_of_state)}</td></tr>`).join("")}</tbody></table></div>
    <p class="small muted">Stops counted as boarding points (each direction of a street counts once). Rail and rapid transit means The Hop and Kenosha streetcars, CONNECT 1 and Madison's Rapid Route A; Amtrak stations are left out because their service is too infrequent. ${pill("observed")}</p></section>
  <section class="card" data-testid="law-district"><h2>What the modelled law does</h2>
    <ul class="tod-points">
      <li>Who: every city with rail or rapid stops.</li>
      <li>Where: ${esc(s.district.radius)} of those stops.</li>
      <li>How much: ${sharePct(s.district.share)} of the land there.</li>
      <li>What: apartments by right, ${int(s.district.min_homes_per_acre)}+ homes per acre.</li>
      <li>Which land: the city picks.</li>
    </ul>
    <p class="small muted">${esc(s.district.text)} Land beyond ¼ mile counts zero. ${esc(RAPID_LINES)} The modelled law does not change parking rules and requires no affordable homes. The 15% follows the ${int(s.district.places)} US places the numbers come from, whose districts covered about ${sharePct(s.district.places_mean_share)} of that land on average.</p></section>
  <section class="card"><h2>The transit lines that qualify</h2>
    <div class="table-wrap"><table class="data" data-testid="agencies-table"><caption>Qualifying stops by transit system (main case unless marked)</caption>
      <thead><tr><th scope="col">Transit system and lines</th><th scope="col" class="num">Rail or rapid stops</th><th scope="col" class="num">15-minute bus stops</th><th scope="col" class="num">20-minute bus stops (wider case only)</th></tr></thead>
      <tbody>${s.agencies.map((a) => `<tr><th scope="row"><strong>${esc(a.agency)}</strong><br><span class="small">${esc(a.lines)}</span></th><td class="num">${int(a.rapid)}</td><td class="num">${int(a.bus15)}</td><td class="num">${int(a.bus20_only)}</td></tr>`).join("")}</tbody></table></div>
    <p class="small muted">Green Bay has no current schedule file, so none of its routes could be tested and none counts. A map of the station areas is on <a href="${env.link("/where")}">Where</a>.</p></section>
  <p><a class="button" href="${env.link("/summary")}">What a statewide TOD law would add →</a></p>`;
  main.querySelectorAll<HTMLInputElement>('input[name="tod-today-view"]').forEach((i) => i.addEventListener("change", () => {
    const q = new URLSearchParams(params);
    q.set("view", i.value);
    env.replaceQuery(q); env.refresh(); env.announce(`Map: ${TODAY_VIEWS.find(([v]) => v === i.value)![1]}.`);
  }));
}

// ---- 2. Statewide comparison --------------------------------------------------------------------
const TOD_SCOPE_UNIT = "extra homes near major transit stops over 2027–2031";
export function todRangeCard(b: TodBundle, headingLevel: 2 | 3 = 2, testid = "range-card"): string {
  return rangeCardHTML({ title: "Extra homes from the law: the projected range (90%)", range: b.statewide.range90, baselineTotal: b.statewide.state_baseline_total, testid, headingLevel });
}
/** The record-year warning, checked at the range's high end. */
const andList = (xs: string[]): string => (xs.length < 2 ? xs.join("") : `${xs.slice(0, -1).join(", ")} and ${xs[xs.length - 1]}`);

function recordNote(b: TodBundle): string {
  const R = b.statewide.range90, rc = R.record_check_high ?? [];
  const over = rc.filter((x) => x.years_above_own_record.length);
  if (!over.length) return "";
  const top = rc.filter((x) => x.above_observed_max);
  return `<div class="note-box" role="note" data-testid="record-years"><p><strong>Above the metros' own records at the high end.</strong> At the range's high end (${num(R.high)} extra homes), apartment permitting (current law plus the law) would pass the metro's own record year in ${over.map((x) => `${esc(x.metro)} ${andList(x.years_above_own_record.map(String))}`).join("; ")}. ${top.length ? `In ${top.map((x) => `${esc(x.metro)} (${dec(x.peak_total_per_1000, 1)} apartment homes per 1,000 existing homes in ${x.peak_year})`).join(" and ")} it would also pass the busiest year any of 79 comparable US metros has recorded (${dec(top[0].observed_max, 1)} per 1,000).` : "No metro would pass the busiest year any comparable US metro has recorded."} The scale check above has the details.</p></div>`;
}

/** The TOD Summary: the shared component fed from the TOD bundle. */
/** "The policy" on the TOD Summary: the owner's text (2026-11-11 20:23), with the share, radius and density read from
 *  the bundle's district fields. */
export function todPolicyText(d: TodBundle["statewide"]["district"]): string {
  return `Requiring every Wisconsin city with rail or rapid-bus stops to zone ${sharePct(d.share)} of the land within ${d.radius} of those stops for apartments by right, at least ${int(d.min_homes_per_acre)} homes per acre.`;
}

export function todSummaryInput(b: TodBundle, homes: WiHomes, env: ShellEnv): SummaryInput {
  const s = b.statewide, y = s.baseline.years;
  return {
    id: "tod", title: "Transit-oriented density", law: `zones apartments by right on ${sharePct(s.district.share)} of the land within ${s.district.radius} of rail and rapid-bus stops`,
    modeled: [s.district.text, `A major transit stop here is a rail or rapid-bus stop, and the proximity threshold is ${s.district.radius}: land beyond it counts zero. ${RAPID_LINES}`],
    // owner, 2026-11-11 20:23: the ADU Summary pattern (policy beside the estimate; modeled + benchmark under the chart)
    policy: todPolicyText(s.district), sentence: false, policyBeside: true,
    scopeLink: { href: env.link(`/why?section=${TOD_IN_OUT_ID}`), label: "Why → In and out of the model", text: `For the ${b.why.in_out.places.length} places behind the range, and the places left out, see` },
    unit: "homes near major transit stops", chartName: "Homes permitted near major transit stops", range: s.range90, rangeFlat: flatRange(s.range90),
    sideLines: s.side_lines.filter((x) => x.where === "chart"),
    base: { central: y.map((r) => r.central), low: y.map((r) => r.low), high: y.map((r) => r.high) },
    baseName: "homes permitted near stops under current law", homes,
  };
}

/** The former Statewide comparison, now How sure's Details: timing, the range card, every side line, the record-year
 *  note, the yearly table and "How big is that?". The chart is on Summary. */
function todDetails(b: TodBundle): string {
  const s = b.statewide;
  const base = s.baseline;
  const R = s.range90;
  return `
  <h2 class="section-h" id="h-details" data-testid="details">Details</h2>
  <div class="note-box" role="note" data-testid="timing-caveat"><p><strong>About timing.</strong> ${esc(s.timing_caveat)}</p></div>
  ${todRangeCard(b, 3)}
  <section class="card" aria-labelledby="h-tod-side"><h3 id="h-tod-side">Comparison scenarios</h3>
    ${sideLinesHTML(s.side_lines.filter((x) => x.where === "chart"), TOD_SCOPE_UNIT, "side-lines", "Drawn on the Summary chart. Scenarios can sit outside the range; they do not change it.")}
    ${s.side_lines.some((x) => x.where !== "chart") ? sideLinesHTML(s.side_lines.filter((x) => x.where !== "chart"), TOD_SCOPE_UNIT, "howsure-side-lines", "Shown here only. None changes the projected range.") : ""}</section>
  ${recordNote(b)}
  <section class="card" aria-labelledby="h-tod-years"><h3 id="h-tod-years">Homes permitted near stops each year</h3>
    <div class="table-wrap"><table class="data" data-testid="compare-table"><caption>Homes permitted near major transit stops: current law, and the law's extra homes as a projected range</caption>
      <thead><tr><th scope="col">Year</th><th scope="col" class="num">Current law</th><th scope="col" class="num">Current law: low</th><th scope="col" class="num">Current law: high</th><th scope="col" class="num">Extra with the law: low end</th><th scope="col" class="num">Extra with the law: high end</th></tr></thead>
      <tbody>${base.years.map((y, i) => `<tr><th scope="row">${y.year}</th><td class="num">${int(y.central)}</td><td class="num">${int(y.low)}</td><td class="num">${int(y.high)}</td><td class="num">${int(R.years[i].low)}</td><td class="num">${int(R.years[i].high)}</td></tr>`).join("")}
      <tr><th scope="row">2027–2031</th><td class="num">${int(base.total)}</td><td class="num">${int(base.low_total)}</td><td class="num">${int(base.high_total)}</td><td class="num" data-testid="table-range-low">${num(R.low)}</td><td class="num" data-testid="table-range-high">${num(R.high)}</td></tr></tbody></table></div>
    <p class="small" data-testid="median-note">${esc(s.median_line.note)}</p>
    <p class="small muted">Current law near stops is held at each place's 2023–2025 average, so it is flat; its range (${int(base.low_total)}–${int(base.high_total)} over five years) comes from Wisconsin's own five-year swings. ${esc(R.years_method ?? "")} The yearly ends are not added to current law's own range. The yearly split follows the build-up measured across the 11 places, so 2028, the second year, dips slightly below zero. The former New York timing is in the tables above. Yearly rows may not add exactly to the totals because of rounding.</p></section>
  <section class="card" aria-labelledby="h-tod-big"><h3 id="h-tod-big">How big is that?</h3>
    <p data-testid="compare-size">The law adds ${num(R.low)} to ${num(R.high)} homes (projected range) to the ${int(base.total)} expected near stops under current law over 2027–2031: ${sharePct(R.low / base.total)} to ${sharePct(R.high / base.total)} more. Against all new homes in Wisconsin, that is about ${int(R.low / 5)} to ${int(R.high / 5)} extra homes a year, ${sharePct(R.low / s.state_baseline_total)} to ${sharePct(R.high / s.state_baseline_total)} of the ${int(s.state_baseline_per_year)} homes a year Wisconsin is expected to permit under current law (all homes, all places), or ${sharePct(R.low / s.acs_homes)} to ${sharePct(R.high / s.acs_homes)} of Wisconsin's ${int(s.acs_homes)} homes (ACS 2020–2024).</p>
    <p class="small muted" data-testid="shared-unit">These are homes in issued building permits, not completed homes, compared with current law in the same places. The homes near stops are part of Wisconsin's all-homes count, and the reforms overlap (homes near stops can gain from other reforms too), so the extra homes of different reforms are never added together. Station-area shares use the 2020 census, because the station areas are built from census blocks.</p></section>`;
}

// ---- 3. Where ------------------------------------------------------------------------------------
type Level = "place" | "county" | "assembly" | "senate";
const LEVELS: [Level, string][] = [["place", "Cities, villages and towns"], ["county", "Counties"], ["assembly", "Assembly districts"], ["senate", "Senate districts"]];
const VIEWS: [string, string][] = [["milwaukee", "Milwaukee area"], ["madison", "Madison area"], ["kenosha", "Kenosha"]];

/** Where page scenario names (owner, 2026-11-13): numbered 1–3 in SCEN_IDS order (rezoned lots only, then the
 *  11-place average, then scaled to 15%); each toggle shows its statewide total from the bundle, and keeps the full
 *  scenario name as its accessible name. */
const WHERE_NAMES: Record<ScenId, string> = { little: "rezoned lots only", typical: "the 11-place average", strong: "scaled to 15%" };
const whereNo = (id: ScenId): string => `Scenario ${SCEN_IDS.indexOf(id) + 1}`;
function scenRadios(b: TodBundle, name: string, current: ScenId): string {
  return `<fieldset class="seg"><legend>Scenario</legend>${SCEN_IDS.map((id) => `<label><input type="radio" name="${name}" value="${id}" ${current === id ? "checked" : ""} aria-label="${esc(`${whereNo(id)}, ${WHERE_NAMES[id]}: ${int(scen(b, id).additional_total)} extra homes`)}"> ${esc(whereNo(id))} (${int(scen(b, id).additional_total)} extra homes)</label>`).join("")}</fieldset>`;
}

export function where(b: TodBundle, env: ShellEnv, params: URLSearchParams, main: HTMLElement): void {
  const sid = (SCEN_IDS.includes(params.get("s") as ScenId) ? params.get("s") : "typical") as ScenId;
  const level = (LEVELS.some(([l]) => l === params.get("level")) ? params.get("level") : "place") as Level;
  const view = VIEWS.some(([v]) => v === params.get("view")) ? params.get("view")! : "milwaukee";
  const sortKey = ["name", "homes", "baseline", "add"].includes(params.get("sort") ?? "") ? params.get("sort")! : "add";
  const dir = params.get("dir") === "asc" ? "asc" : "desc";
  const A = b.areas;
  const sc = scen(b, sid);
  const metroName = Object.fromEntries(A.metros.map((m) => [m.id, m.name]));
  type Row = { name: string; sub?: string; homes?: number; baseline: number; all: number; add: number; county?: string; metro?: string; qacres?: number };
  let rows: Row[];
  let others = 0;
  if (level === "place") rows = A.munis.map((m: Muni) => ({ name: placeName(m.name), county: m.county, metro: metroName[m.metro], homes: m.homes_near, baseline: m.baseline, all: m.all_baseline, add: m.add[sid], qacres: m.quarter_acres }));
  else {
    const src = level === "county" ? A.counties : level === "assembly" ? A.assembly : A.senate;
    rows = src.rows.map((r: AggRow) => ({ name: r.name, baseline: r.baseline, all: r.all_baseline, add: r.add[sid] }));
    others = src.total_count - src.rows.length;
  }
  const val = (r: Row) => (sortKey === "name" ? r.name : sortKey === "homes" ? r.homes ?? 0 : sortKey === "baseline" ? r.baseline : r.add);
  rows.sort((a, z) => { const x = val(a), y = val(z); const c = typeof x === "string" ? x.localeCompare(y as string) : (x as number) - (y as number); return dir === "asc" ? c : -c; });
  const cols: [string, string, boolean][] = [["name", level === "place" ? "Place" : level === "county" ? "County" : "District", false]];
  if (level === "place") cols.push(["homes", "Homes near stops", true]);
  cols.push(["baseline", "Permitted near stops, current law", true], ["add", `Extra homes (${whereNo(sid)})`, true]);
  const head = cols.map(([k, label, num]) => {
    const on = sortKey === k;
    return `<th scope="col" class="${num ? "num" : ""}"${on ? ` aria-sort="${dir === "asc" ? "ascending" : "descending"}"` : ""}><button type="button" class="tod-sort-btn" id="sort-${k}" data-sort="${k}">${esc(label)}<span class="tod-sort-ind" aria-hidden="true">${on ? (dir === "asc" ? "▲" : "▼") : "↕"}</span></button></th>`;
  });
  if (level === "place") head.splice(1, 0, `<th scope="col">County and area</th>`, `<th scope="col" class="num">Land within ¼ mile of rail or rapid stops (acres)</th>`);
  head.push(`<th scope="col" class="num">Extra homes, projected range</th>`, `<th scope="col" class="num">Extra a year, of all new homes a year there</th>`);
  const R = b.statewide.range90;
  const rangeCell = (r: Row) => { const sh = r.add / sc.additional_total; return `<td class="num">${small(sh * R.low)} to ${small(sh * R.high)}</td>`; };
  // AQ-054 shared unit by area: extra homes a year against the area's all-housing baseline; no percentage where
  // fewer than MIN_ALL homes a year are expected (a percentage of almost nothing would mislead)
  const MIN_ALL = 5;
  const sharedCell = (r: Row) => { const a = r.add / 5, all = r.all / 5; return `<td class="num">${small(a)} <span class="small muted">of ${small(all)}${all >= MIN_ALL ? ` (+${sharePct(a / all)})` : ""}</span></td>`; };
  const labels = A.munis.slice(0, 10).map((m) => m.name);
  // the intro's land shares: each place's lot acres within ¼ mile of rail and rapid stops, largest first
  const landPlaces = A.munis.filter((m: Muni) => m.quarter_acres > 0).sort((x: Muni, y: Muni) => y.quarter_acres - x.quarter_acres);
  const landTotal = landPlaces.reduce((a: number, m: Muni) => a + m.quarter_acres, 0);
  const landTop = landPlaces.slice(0, 4), landRest = landPlaces.length - landTop.length;
  const landTxt = (m: Muni) => `${esc(m.name.replace(/ (city|village|town)$/, ""))} (${Math.round((m.quarter_acres / landTotal) * 100)}%)`;
  const io = b.why.in_out;
  const shMin = Math.min(...io.places.map((p) => p.share)), shMax = Math.max(...io.places.map((p) => p.share));
  main.innerHTML = `
  <h1>Where we expect the extra homes</h1>
  <p class="lede" data-testid="where-intro">The law would require cities to zone an apartment district on ${sharePct(b.statewide.district.share)} of the land within ¼ mile of rail and rapid-transit stops. Most of that land is in ${landTop.slice(0, 2).map(landTxt).join(" and ")}. The rest is in ${landTop.slice(2, 4).map(landTxt).join(", ")}${landRest ? ` and ${landRest} smaller ${landRest === 1 ? "place" : "places"}` : ""}. Each place gets the same share of the extra homes as its share of that land (in lot acres). Totals are 2027–2031.</p>
  <section class="card" data-testid="where-scenarios"><h2>Three scenarios</h2>
    <p>To build our projected range, we studied ${io.places.length} places that zoned a mapped apartment district within ¼ mile of their stops. Their districts covered about ${sharePct(io.mean_share)} of that land on average (from ${Math.round(shMin * 100)}% to ${Math.round(shMax * 100)}%). We also looked at ${io.out_broad.length} places that upzoned half or more of the land near their stops, but left them out, because the law zones a district, not most of the land.</p>
    <p>Pick a scenario to see the extra homes in each place:</p>
    <ul>
      <li><strong>${whereNo("little")}, rezoned lots only (${int(scen(b, "little").additional_total)} extra homes):</strong> only the gain on the rezoned lots themselves. We measured it just inside versus just outside district edges, in ${io.edge.places.length} places. A low-end check.</li>
      <li><strong>${whereNo("typical")}, the ${io.places.length}-place average (${int(scen(b, "typical").additional_total)} extra homes):</strong> how the ${io.places.length} district places did on average, at their ${sharePct(io.mean_share)} of land. Our projected range is built on this number.</li>
      <li><strong>${whereNo("strong")}, scaled to ${sharePct(b.statewide.district.share)} (${int(scen(b, "strong").additional_total)} extra homes):</strong> the same average, scaled up because the law covers ${sharePct(b.statewide.district.share)} of the land.</li>
    </ul>
    <p class="small muted">All figures are extra homes permitted over 2027–2031.</p>
  <form id="tod-where-scen">${scenRadios(b, "tod-scen", sid)}</form></section>
  <section class="card"><h2>Two metro areas and the rest of the state</h2>
    <div class="table-wrap"><table class="data" data-testid="metro-table"><caption>Homes near stops, current-law permits and extra homes by area, 2027–2031</caption>
      <thead><tr><th scope="col">Area</th><th scope="col" class="num">Homes near stops (2020 census)</th><th scope="col" class="num">Permitted near stops, current law</th>${SCEN_IDS.map((id) => `<th scope="col" class="num">${id === sid ? "<strong>" : ""}Extra: ${esc(whereNo(id))}${id === sid ? "</strong>" : ""}</th>`).join("")}</tr></thead>
      <tbody>${A.metros.map((m) => `<tr><th scope="row">${esc(m.name)}<br><span class="small muted">${esc(m.counties.join(", "))}; ${m.places} ${m.places === 1 ? "place" : "places"} with qualifying stops</span></th><td class="num">${int(m.homes_near)}</td><td class="num">${small(m.baseline)}</td>${SCEN_IDS.map((id) => `<td class="num">${small(m.add[id])}</td>`).join("")}</tr>`).join("")}
      <tr><th scope="row">Wisconsin</th><td class="num">${int(A.metros.reduce((a, m) => a + m.homes_near, 0))}</td><td class="num">${int(b.statewide.baseline.total)}</td>${SCEN_IDS.map((id) => `<td class="num">${int(scen(b, id).additional_total)}</td>`).join("")}</tr></tbody></table></div>
    <p class="small muted">Metro areas as the federal government defines them (Milwaukee, Waukesha, Ozaukee and Washington counties; Dane, Columbia, Green and Iowa counties).</p></section>
  <section class="card"><h2>Station areas on a map</h2>
    <form id="tod-where-view"><fieldset class="seg"><legend>Map area</legend>${VIEWS.map(([v, l]) => `<label><input type="radio" name="tod-view" value="${v}" ${view === v ? "checked" : ""}> ${l}</label>`).join("")}</fieldset></form>
    ${stationMap(b.map, { view, labels, title: `Station areas: ${VIEWS.find(([v]) => v === view)![1]}`, desc: `Shaded circles show land within ½ mile of rail and rapid transit stations and ¼ mile of 15-minute bus stops. Tinted places are those the model gives extra homes. The table below has the numbers by place.` })}
    ${mapKey()}
    <p class="small muted">Stops from the federal National Transit Map. Place outlines are simplified. The map shows where the law would apply, not where homes will be built.</p></section>
  <section class="card"><h2>By place and district</h2>
    <form id="tod-where-level"><fieldset class="seg"><legend>Show by</legend>${LEVELS.map(([l, t]) => `<label><input type="radio" name="tod-level" value="${l}" ${level === l ? "checked" : ""}> ${t}</label>`).join("")}</fieldset></form>
    <div class="table-wrap"><table class="data" data-testid="where-table"><caption>Extra homes, ${esc(whereNo(sid))}, by ${esc(LEVELS.find(([l]) => l === level)![1].toLowerCase())}, 2027–2031 (statewide total ${int(sc.additional_total)}). Select a column heading to sort.</caption>
      <thead><tr>${head.join("")}</tr></thead>
      <tbody>${rows.map((r) => `<tr><th scope="row">${esc(r.name)}</th>${level === "place" ? `<td>${esc(r.county ?? "")}<br><span class="small muted">${esc(r.metro ?? "")}</span></td><td class="num">${int(r.qacres ?? 0)}</td><td class="num">${int(r.homes)}</td>` : ""}<td class="num">${small(r.baseline)}</td><td class="num">${small(r.add)}</td>${rangeCell(r)}${sharedCell(r)}</tr>`).join("")}</tbody></table></div>
    ${A.few_homes_places.length ? `<p class="small" data-testid="few-homes-note">Some places get extra homes though few or no homes are near their stops today (${esc(A.few_homes_places.map((n) => n.replace(/ (city|village|town)$/, " ($1)")).join(", "))}). Extra homes are placed in proportion to land within ¼ mile of rail and rapid stops, which includes vacant and commercial land, not in proportion to existing homes.</p>` : ""}
    ${A.low_permit_places.length ? `<p class="small" data-testid="low-permit-note">Current-law permits come from Census building-permit counts. ${A.low_permit_places.map((x) => `${esc(x.name.replace(/ (city|village|town)$/, ""))} reported ${x.units.map((u) => int(u)).join(", ")} new homes a year in ${x.years[0]}–${x.years[x.years.length - 1]}, ${x.units_5plus ? `${int(x.units_5plus)} of them apartments` : "none of them apartments"}`).join("; ")}. Those low figures make current law there very small next to the law's extra homes, and may be an under-count like the one found for Milwaukee's apartments.</p>` : ""}
    <p class="small muted">${others ? `The other ${others} ${level === "county" ? "counties" : "districts"} have no qualifying stops and are left out. ` : ""}Each place's share of the statewide extra homes is its share of Wisconsin's land (lot acres) within ¼ mile of rail and rapid stops, because the model spreads the district at random over that land. District figures split each place's numbers as its detached homes are split, an approximation. The last column compares the extra homes a year with all the homes the area is expected to permit a year under current law (the statewide all-housing forecast, ${int(b.statewide.state_baseline_per_year)} a year); no percentage is shown where fewer than ${MIN_ALL} a year are expected. "under 1" means more than zero but less than half a home. Rows may not add exactly because of rounding.</p>
    <p class="small muted" data-testid="where-range-note">Each area's projected range is the statewide projected range (${num(b.statewide.range90.low)} to ${num(b.statewide.range90.high)} extra homes, 2027–2031) times the area's share.</p></section>`;
  const setQ = (k: string, v: string, msg: string) => {
    const q = new URLSearchParams(params);
    q.set(k, v);
    if (k === "level") { q.delete("sort"); q.delete("dir"); }
    env.replaceQuery(q); env.refresh(); env.announce(msg);
  };
  main.querySelectorAll<HTMLInputElement>('input[name="tod-scen"]').forEach((i) => i.addEventListener("change", () => setQ("s", i.value, `${whereNo(i.value as ScenId)}, ${WHERE_NAMES[i.value as ScenId]}. Extra homes statewide ${int(scen(b, i.value as ScenId).additional_total)}.`)));
  main.querySelectorAll<HTMLInputElement>('input[name="tod-view"]').forEach((i) => i.addEventListener("change", () => setQ("view", i.value, `Map: ${VIEWS.find(([v]) => v === i.value)![1]}.`)));
  main.querySelectorAll<HTMLInputElement>('input[name="tod-level"]').forEach((i) => i.addEventListener("change", () => setQ("level", i.value, `Table: ${LEVELS.find(([l]) => l === i.value)![1]}.`)));
  main.querySelectorAll<HTMLButtonElement>("button[data-sort]").forEach((btn) => btn.addEventListener("click", () => {
    const k = btn.dataset.sort!;
    const nd = k === sortKey ? (dir === "asc" ? "desc" : "asc") : k === "name" ? "asc" : "desc";
    const q = new URLSearchParams(params);
    q.set("sort", k); q.set("dir", nd);
    env.replaceQuery(q); env.refresh();
    env.announce(`Table sorted by ${btn.textContent!.replace(/[▲▼↕]/g, "").trim()}, ${nd === "asc" ? "ascending" : "descending"}.`);
  }));
}

/** TOD's what-ifs split for How sure's two charts. Inputs: the district share (10% or 25% of land instead of 15%) and
 *  the timing, stop-rule and current-law what-ifs, which leave the five-year total where it is. Every other row of
 *  the bundle's tornado (lines, their ranges, leave-one-out ends, the 2x2 readings, earlier methods) is an other way. */
const TOD_INPUT_IDS = ["district_10:strong", "district_25:strong"];
export function todWhatIfs(b: TodBundle): { inputs: InputRow[]; others: OtherRow[]; pivot: number } {
  const H = b.howsure, T = H.tornado, pivot = T.central;
  const byId = Object.fromEntries(T.rows.map((r) => [r.id, r]));
  const strong = scen(b, "strong").additional_total;
  const inputs: InputRow[] = [];
  if (TOD_INPUT_IDS.every((id) => byId[id])) inputs.push({ ids: TOD_INPUT_IDS, label: "Share of land near stops in the district (15% used)",
    settings: [{ name: "10% of land", value: byId["district_10:strong"].extra }, { name: "25% of land", value: byId["district_25:strong"].extra }],
    note: `Run on the upper line only (${int(strong)} at 15%); not yet run on the 11-place average.` });
  // Timing, stop-rule and current-law what-ifs: the law's extra homes over 2027-2031 at the 11-place average.
  const flat = H.groups.flatMap((g) => g.rows.filter((r) => (g.id === "law_addition" ? r.id.startsWith("ramp_") : g.id !== "law_addition") && r.add.typical !== undefined)
    .map((r) => ({ ids: [r.id], label: r.label, settings: [{ name: "with this change", value: r.add.typical! }] })));
  inputs.push(...flat);
  const others: OtherRow[] = T.rows.filter((r) => !TOD_INPUT_IDS.includes(r.id)).sort((a, z) => (a.kind === z.kind ? z.extra - a.extra : a.kind === "current" ? -1 : 1))
    .map((r) => ({ id: r.id, label: r.label, value: r.extra, group: r.kind === "current" ? "Current lines and checks" : "Earlier methods, for comparison" }));
  return { inputs, others, pivot };
}

// short column names for the How sure what-if tables (owner 2026-11-12: the long line names made the number columns too wide)
const SENS_SHORT: Record<string, string> = { little: "edge test", typical: "11-place average", strong: "scaled to 15%" };

// ---- 4. How sure ---------------------------------------------------------------------------------
export function howSure(b: TodBundle, env: ShellEnv, main: HTMLElement): void {
  const H = b.howsure;
  const s = b.statewide;
  const cell = (v: number | undefined) => (v === undefined ? `<td class="num">—</td>` : `<td class="num">${int(v)}</td>`);
  const mainRow = `<tr class="muted"><th scope="row">Main result</th><td>As on the other screens.</td><td class="num">${int(H.main_baseline)}</td>${SCEN_IDS.map((id) => cell(scen(b, id).additional_total)).join("")}</tr>`;
  const groupTable = (g: (typeof H.groups)[number]) => {
    const where_ = g.id === "where_homes_land";
    const mm = b.areas.metros;
    return `<section class="card"><h2>${esc(g.label)}</h2>
    <div class="table-wrap"><table class="data sens-table" data-testid="sens-${esc(g.id)}"><caption>${esc(g.label)}: homes permitted near stops, 2027–2031</caption>
      <colgroup><col class="sens-col-what"><col class="sens-col-means"></colgroup><thead><tr><th scope="col">What if</th><th scope="col">What it means</th><th scope="col" class="num">Current law</th>${SCEN_IDS.map((id) => `<th scope="col" class="num" title="${esc(scen(b, id).label)}">Extra: ${esc(SENS_SHORT[id] ?? lcFirst(scen(b, id).label))}</th>`).join("")}${where_ ? `<th scope="col" class="num">Milwaukee metro (central)</th><th scope="col" class="num">Madison metro (central)</th>` : ""}</tr></thead>
      <tbody>${where_ ? mainRow.replace("</tr>", `<td class="num">${int(mm[0].add.typical)}</td><td class="num">${int(mm[1].add.typical)}</td></tr>`) : mainRow}${g.rows.map((r) => `<tr><th scope="row">${esc(r.label)}</th><td>${esc(r.text)}${r.typical_by_year ? ` Central line by year, 2027–2031: ${r.typical_by_year.map((v) => int(v)).join(" / ")}, instead of ${scen(b, "typical").by_year.map((v) => int(v)).join(" / ")}.` : ""}</td><td class="num">${int(r.baseline)}</td>${r.id === "typical_range"
        ? `<td class="num">—</td><td class="num">${int(r.add.typical_low)} to ${int(r.add.typical_high)}</td><td class="num">—</td>`
        : r.id === "little_range"
        ? `<td class="num">${int(r.add.little_low)} to ${int(r.add.little_high)}</td><td class="num">—</td><td class="num">—</td>`
        : r.id === "strong_range"
        ? `<td class="num">—</td><td class="num">—</td><td class="num">${int(r.add.strong_low)} to ${int(r.add.strong_high)}</td>`
        : SCEN_IDS.map((id) => cell(r.add[id])).join("")}${where_ ? `<td class="num">${r.milwaukee_metro === null ? "—" : int(r.milwaukee_metro)}</td><td class="num">${r.madison_metro === undefined ? "—" : int(r.madison_metro)}</td>` : ""}</tr>`).join("")}</tbody></table></div></section>`;
  };
  const sb = H.scale_benchmarks;
  const ms = H.madison_share;
  // The two what-if charts (docs/shared/HOWSURE_TORNADO_CLASSIFICATION.md): inputs as a tornado around the 11-place
  // average, everything else in the former chart as other ways to estimate it.
  const R = s.range90;
  const w = todWhatIfs(b);
  const tornadoCard = howSureChartsHTML({ prefix: "tod", unit: "Extra homes near major transit stops, 2027–2031", range: R,
    pivot: w.pivot, pivotName: "as used", pivotLabel: `The number the projected range is built on: ${int(w.pivot)} (the 11-place average)`,
    inputs: w.inputs, others: w.others,
    inputsNote: "Inputs about timing, stop rules and current law are listed under the bars: they leave the five-year total unchanged." });
  main.innerHTML = `
  <h1>How sure are we?</h1>
  <p class="lede">The law's extra homes are one projected range (90%), ${num(s.range90.low)} to ${num(s.range90.high)} over 2027–2031. This page shows which model inputs move the projected range and how other ways to estimate it compare with that range, whether the results are believable for Milwaukee and Madison, and which parts rest on data and which on judgment. The tables further down still list the three former lines (lower, central, upper), which are now comparison scenarios. The range card, the comparison scenarios and the yearly table are under Details at the end.</p>
  ${tornadoCard}
  ${H.groups.map(groupTable).join("")}
  <section class="card"><h2>A sizing method that was tested and set aside</h2>
    <p data-testid="per-acre">For the broader law modelled before (upzoning most land near stops), the model was first sized from the extra homes per acre measured right where cities upzoned. Spread over all the land near Wisconsin's stops, that gave ${int(H.per_acre.add.little)}, ${int(H.per_acre.add.typical)} and ${int(H.per_acre.add.strong)} extra homes over 2027–2031: even the smallest would have taken Madison's apartment permitting above its own record. Upzoning one block partly moves building there from nearby blocks, so block-level gains overstate a city's net gain. Using the per-acre response measured in Madison and Chicago instead gives ${int(H.per_acre.wisconsin_uncapped)}. Capping each metro at the level comparable metros stayed under in 95% of years (${dec(H.scale_benchmarks.p95, 2)} apartment homes permitted per 1,000 existing homes a year) gives ${int(H.per_acre.wisconsin_capped)}, all in the Milwaukee metro: Madison gets none under the cap, because its current permitting is already above that level. The tool therefore moved to comparisons of reform stops with similar stops without reform.</p></section>
  <section class="card"><h2>Scale check: could the metros absorb this?</h2>
    <p>Apartment homes (in buildings of 5 or more) permitted per 1,000 existing homes per year, in each scenario's busiest year, current law plus the law's addition, against the metro's own best year.</p>
    <div class="table-wrap"><table class="data" data-testid="scale-table"><caption>Apartment homes permitted per 1,000 existing homes per year, busiest year of 2027–2031</caption>
      <thead><tr><th scope="col">Metro</th><th scope="col" class="num">Current law</th>${SCEN_IDS.map((id) => `<th scope="col" class="num">${esc(scen(b, id).label)}</th>`).join("")}<th scope="col" class="num">The metro's own record</th></tr></thead>
      <tbody>${H.scale.map((m) => `<tr><th scope="row">${esc(m.name)}</th><td class="num">${dec(m.baseline_per_1000, 2)}</td>${SCEN_IDS.map((id) => `<td class="num">${dec(m.peak[id].total_per_1000, 2)} <span class="small muted">(${m.peak[id].year})</span>${m.peak[id].exceeds_own_max ? " <strong>above record</strong>" : ""}</td>`).join("")}<td class="num">${dec(m.own_max, 2)} <span class="small muted">(${m.own_max_year})</span></td></tr>`).join("")}</tbody></table></div>
    <p class="small muted">The highest year any of 79 comparable US metros (500,000 to 2.5 million people, 2000–2025) has recorded is ${esc(sb.observed_max_metro)} in ${sb.observed_max_year}: ${dec(sb.observed_max, 1)} per 1,000. No scenario reaches it. ${(() => { const over = SCEN_IDS.filter((id) => H.scale.some((m) => m.peak[id].exceeds_own_max)); return over.length ? `Above a metro's own record in its busiest year: ${over.map((id) => lcFirst(scen(b, id).label)).join("; ")}.` : "No scenario beats the two metros' own records."; })()} Census Building Permits Survey and housing-unit estimates.</p></section>
  <section class="card"><h2>A check against Madison's own overlay (not set in advance)</h2>
    <p data-testid="madison-share">In 2023 Madison raised allowed density along its transit corridors. Over 2023–2025, the extra homes permitted on the overlay's lots were about ${sharePct(ms.judged.share)} of the ${int(ms.judged.stock)} homes on those lots (likely range ${sharePct(ms.judged.low)} to ${sharePct(ms.judged.high)}; ${sharePct(ms.main.share)} on the narrower main estimate). Over their first three years, the scenarios give ${SCEN_IDS.map((id) => `${sharePct(ms.scenarios[id])} (${lcFirst(scen(b, id).label)})`).join(", ")} of the homes near stops. Madison's range includes zero and all three, so it cannot pick between them.</p>
    <p class="small muted">This comparison was added after the results were known and has no pass rule; the Madison test, whose pass rule was written before counting, is on <a href="${env.link("/why")}">Why</a>.</p></section>
  <section class="card"><h2>What rests on data and what on judgment</h2>
    <ul class="plain" data-testid="trace">${H.trace.map((t) => `<li>${pill(t.status)} <strong>${esc(t.part)}.</strong> ${esc(t.text)}</li>`).join("")}</ul></section>
  <section class="card"><h2>What the model cannot tell you</h2>
    <ul class="plain">${H.cannot_tell.map((c) => `<li><strong>${esc(c.title)}.</strong> ${esc(c.text)}</li>`).join("")}</ul>
    <p class="small muted">Current law near stops is ${int(s.baseline.total)} homes over 2027–2031 in the main case; the "Current law" column above shows how each what-if changes it.</p></section>
  ${todDetails(b)}`;
}

// ---- 5. Why --------------------------------------------------------------------------------------
function ciChart(rows: { label: string; v: number; lo: number; hi: number; color: string }[], aria: string): string {
  const min = Math.min(0, ...rows.map((r) => r.lo)), max = Math.max(...rows.map((r) => r.hi));
  const P = (x: number) => ((x - min) / (max - min)) * 100;
  return `<div class="tod-ci" role="img" aria-label="${esc(aria)}">${rows.map((r) => `<div class="tod-ci-row" aria-hidden="true"><span>${esc(r.label)}</span><span class="tod-ci-track"><span class="tod-ci-zero" style="left:${P(0)}%"></span><span class="tod-ci-range" style="left:${P(r.lo)}%;width:${P(r.hi) - P(r.lo)}%;background:${r.color}"></span><span class="tod-ci-pt" style="left:${P(r.v)}%;background:${r.color}"></span></span></div>`).join("")}</div>`;
}

/** The anchor of the in/out card; the TOD Summary's "What we modeled" card links here (?section=tod-in-out). */
export const TOD_IN_OUT_ID = "tod-in-out";

/** "In and out of the model": the 11 places behind the central and upper lines, the 5 behind the lower line, and the
 *  places looked at but left out. Every value and reason comes from the bundle (build_in_out). */
function inOutHTML(b: TodBundle): string {
  const io = b.why.in_out;
  const out = [...io.out_broad, ...io.out_other];
  return `<section class="card in-out" id="${TOD_IN_OUT_ID}" tabindex="-1" aria-labelledby="h-tod-in-out" data-testid="tod-in-out">
    <h2 id="h-tod-in-out">In and out of the model</h2>
    <p class="muted">The places each line is learned from, and the places we looked at but left out.</p>
    <h3>In the range: ${io.places.length} district places (central and upper lines)</h3>
    <div class="table-wrap"><table class="data" data-testid="tod-in-places"><caption>Each place's district and its measured effect. Effect: ${esc(io.effect_units)}.</caption>
      <thead><tr><th scope="col">Place</th><th scope="col" class="num">Share of land within ¼ mile in the district</th><th scope="col" class="num">Measured effect (extra homes per 100 lot acres a year)</th></tr></thead>
      <tbody>${io.places.map((p) => `<tr><th scope="row">${esc(p.name)}</th><td class="num">${sharePct(p.share)}</td><td class="num">${signed(p.effect, 1)}</td></tr>`).join("")}</tbody>
      <tfoot><tr><th scope="row">Average of the ${io.places.length} places</th><td class="num">${sharePct(io.mean_share)}</td><td class="num" data-testid="tod-in-mean">${signed(io.mean_effect, 2)}</td></tr></tfoot></table></div>
    <p class="small muted">The central line is this plain average; the upper line scales it to a district of 15% of the land. New York and Philadelphia made many small rezonings each; each city's are pooled into one effect.</p>
    <h3>Edge check: ${io.edge.places.length} places (lower line)</h3>
    <ul class="plain in-out-list" data-testid="tod-edge-places">${io.edge.places.map((p) => `<li><strong>${esc(p.name)}</strong>: ${signed(p.effect, 1)}</li>`).join("")}</ul>
    <p class="small muted">Effect: ${esc(io.edge.units)}. Average of the ${io.edge.places.length}: ${signed(io.edge.pooled, 1)} (90% range ${signed(io.edge.low, 1)} to ${signed(io.edge.high, 1)}). Only these ${io.edge.places.length} of the 11 passed the balance check: their lots on both sides of the line were alike before the rezoning.</p>
    <h3>Left out: ${out.length} places</h3>
    <ul class="plain in-out-list" data-testid="tod-out-places">${out.map((c) => `<li><strong>${esc(c.name)}</strong>: ${esc(c.why)}.</li>`).join("")}</ul>
    <p class="links">${ext(`${b.manifest.repo_url}/blob/main/` + "docs/tod/OPTION_D_PLAN.md", "Option D plan")} · ${ext(`${b.manifest.repo_url}/blob/main/` + "docs/tod/CAUSAL_FRAMEWORK_PLAN.md", "Causal framework")} · ${ext(`${b.manifest.repo_url}/blob/main/` + "docs/tod/CASE_ANALYSIS_PLAN.md", "Case analysis plan")}</p>
  </section>`;
}

export function why(b: TodBundle, main: HTMLElement): void {
  const W = b.why;
  const M = W.madison;
  const fmtCI = (v: number | null, lo: number | null, hi: number | null) => (v === null ? "—" : `${signed(v)} <span class="small muted">(${lo === null ? "—" : signed(lo)} to ${hi === null ? "—" : signed(hi)})</span>`);
  main.innerHTML = `
  <h1>Why: the evidence</h1>
  <p class="lede">No US state has required transit districts long enough ago to measure. So the size of each scenario comes from US places that zoned a district for denser housing near some of their rail or rapid stops: the central from 11 places measured against similar stops without reform, the lower from just inside versus just outside district boundaries, the upper from the same 11 places scaled up to a district of 15% of the land. Where the homes go follows the land within ¼ mile of Wisconsin's rail and rapid stops.</p>
  <section class="card"><h2>The evidence behind the three scenarios</h2>
    <div class="tod-studies">${W.sources.map((x) => `<div class="card"><h3>${esc(scen(b, x.scenario).label)}: ${esc(x.study)}</h3><p>${esc(x.finding)}</p><p class="small">${pill(x.status)} ${ext(x.url, x.citation)}</p><p class="small muted">Used as ${sharePct(scen(b, x.scenario).share_of_stock)} of the homes near stops over five years.</p></div>`).join("")}</div>
    <p class="small muted">Effects are extra new homes per 100 acres of lots a year, before and after. Those cities chose their district land, often land builders already wanted, so a state mandate may do less. No model beat the plain average on places it had not seen. Growth from new lines alone belongs to current law, not the law. The former lines for a broader law (Auckland, Los Angeles and others) are on How sure.</p></section>
  ${inOutHTML(b)}
  ${W.city_checks?.length ? `<section class="card" data-testid="city-checks"><h2>Checking the scenarios against our own cities</h2>
    ${W.city_checks.map((c) => `<h3>${esc(c.title)}</h3><p>${esc(c.text)}</p><p class="small">${ext(c.doc.url, c.doc.label)}</p>`).join("")}
  </section>` : ""}
  <section class="card"><h2>The Madison test: prediction against what happened</h2>
    <p data-testid="madison-test">Before counting any Madison permit, the model predicted that Madison's 2023 transit overlay would add ${dec(M.prediction.value, 2)} homes per acre of eligible overlay land per year (likely range ${dec(M.prediction.low, 2)} to ${dec(M.prediction.high, 2)}). Measured over 2023–2025 against nearby land that was not rezoned, it added ${signed(M.measured.value, 2)} (likely range ${signed(M.measured.low, 2)} to ${signed(M.measured.high, 2)}). The prediction lies inside the measured range, so the test ${M.confirmed ? "passes" : "fails"} the rule written in advance, but only weakly: the measured range also includes zero, and the measured value is about a third of the prediction. This test checked the method that now decides where homes go, not the size of the statewide total.</p>
    ${ciChart([{ label: "Predicted before counting", v: M.prediction.value, lo: M.prediction.low, hi: M.prediction.high, color: C.strong }, { label: "Measured, 2023–2025", v: M.measured.value, lo: M.measured.low, hi: M.measured.high, color: C.typical }],
      `Predicted ${dec(M.prediction.value, 2)} (${dec(M.prediction.low, 2)} to ${dec(M.prediction.high, 2)}) and measured ${signed(M.measured.value, 2)} (${signed(M.measured.low, 2)} to ${signed(M.measured.high, 2)}) extra homes per acre per year; the vertical line is zero.`)}
    <h3>Homes permitted per acre each year, rezoned land and nearby land</h3>
    <div class="chart-box" id="tod-madison-chart"></div>
    ${legendHTML([{ name: "Overlay land whose allowed density rose", color: C.typical }, { name: "Nearby land with no zoning change (within ¼ mile)", color: C.baseline, dash: DASH.baseline }])}
    <div class="table-wrap"><table class="data" data-testid="madison-years"><caption>Madison: homes permitted by year on rezoned and nearby land (homes, and homes per acre)</caption>
      <thead><tr><th scope="col">Year</th><th scope="col">Period</th><th scope="col" class="num">Rezoned land: homes</th><th scope="col" class="num">per acre</th><th scope="col" class="num">Nearby land: homes</th><th scope="col" class="num">per acre</th></tr></thead>
      <tbody>${M.years.map((y) => `<tr><th scope="row">${y.year}</th><td>${y.period.startsWith("shown") ? "partial year, shown only" : esc(y.period)}</td><td class="num">${int(y.treatment.units)}</td><td class="num">${dec(y.treatment.rate, 2)}</td><td class="num">${int(y.comparison.units)}</td><td class="num">${dec(y.comparison.rate, 2)}</td></tr>`).join("")}</tbody></table></div>
    <p class="small muted">Rezoned land: ${int(M.years[0].treatment.acres)} eligible acres; nearby land: ${int(M.years[0].comparison.acres)} acres. Each area has only a handful of projects a year, so one building moves a year a lot. Rapid Route A opened in September 2024. The prediction and the pass rule were written down and saved before any Madison permit was counted.</p></section>
  <section class="card"><h2>Comparison cases: extra homes per acre after rezoning</h2>
    <div class="table-wrap"><table class="data" data-testid="cases-table"><caption>Extra homes permitted per acre of eligible land per year, rezoned land against nearby land (likely range in brackets)</caption>
      <thead><tr><th scope="col">Case</th><th scope="col">Role</th><th scope="col" class="num">Extra homes per acre per year</th><th scope="col" class="num">Per 1.0 of added floor area ratio (extra floor space equal to the lot's area)</th><th scope="col">Parking minimums</th><th scope="col">Affordability mandate</th></tr></thead>
      <tbody>${W.cases.map((c) => `<tr><th scope="row">${esc(c.name)}</th><td>${esc(c.role_label)}${c.note ? `<br><span class="small muted">${esc(c.note)}</span>` : ""}</td><td class="num">${fmtCI(c.estimate, c.low, c.high)}</td><td class="num">${fmtCI(c.per_far, c.per_far_low, c.per_far_high)}</td><td>${esc(c.parking ?? "—")}</td><td>${esc(c.mandate ?? "—")}</td></tr>`).join("")}</tbody></table></div>
    <p class="small muted">These measure the effect right where land was rezoned, which counts building pulled from nearby blocks as new. That is why they now only decide where homes go within Wisconsin, not how many. Chicago was kept aside to test the model: its effect per added floor area (${signed(W.cases.find((c) => c.id.startsWith("chicago"))?.per_far ?? 0, 2)}) is close to Madison's measured ${signed(M.per_far.measured, 2)}.</p></section>
  <section class="card"><h2>How the policies were classified</h2>
    <p data-testid="classification">${W.classification.length} transit-oriented reforms were rated against the benchmark: a plain height or floor-area increase, approved by right, with no affordability mandate. ${int(W.strength_counts.strong ?? 0)} were strong, ${int(W.strength_counts.medium ?? 0)} medium and ${int(W.strength_counts.weak ?? 0)} weak (most weak ones bundled an affordability mandate). Parking cuts were recorded but did not lower a rating.</p>
    ${more(`All ${W.classification.length} reforms`, `<div class="table-wrap"><table class="data" data-testid="classification-table"><caption>Transit-oriented reforms and how they were rated</caption>
      <thead><tr><th scope="col">Place</th><th scope="col">Year</th><th scope="col">Strength</th><th scope="col">Permit data</th><th scope="col">Parking minimums cut</th><th scope="col">Affordable homes required</th><th scope="col">How it is used here</th></tr></thead>
      <tbody>${W.classification.map((c) => `<tr><th scope="row">${esc(c.city)}</th><td>${esc(c.year ?? "—")}</td><td>${esc(c.strength)}</td><td>${esc(c.data)}</td><td>${esc(c.parking)}</td><td>${esc(c.mandate)}</td><td class="small">${esc(c.use)}</td></tr>`).join("")}</tbody></table></div>
      <p class="small muted">Permit data: A = permits with dates and unit counts by lot, and the rezoned boundary, both open; B = one of the two missing; C = a published study only.</p>`)}</section>
  <p class="small">${W.docs.map((d) => ext(d.url, d.label)).join(" · ")}</p>`;
  xyChart(document.getElementById("tod-madison-chart")!, {
    title: "Madison: homes permitted per acre per year, overlay land and nearby land, 2017–2026",
    desc: "The overlay took effect in 2023. 2026 is a partial year. The table below has the same values.",
    yLabel: "Homes per acre per year", xTicks: M.years.map((y) => y.year), yFormat: (v) => dec(v, 1),
    series: [
      { name: "Rezoned land", values: M.years.map((y) => ({ x: y.year, y: y.treatment.rate })), color: C.typical, marker: "circle" },
      { name: "Nearby land", values: M.years.map((y) => ({ x: y.year, y: y.comparison.rate })), color: C.baseline, dash: DASH.baseline, marker: "square" },
    ],
    vline: { x: 2022.5, label: "Overlay in effect" },
  });
}

// ---- 6. Pilot examples ---------------------------------------------------------------------------
export function pilot(b: TodBundle, env: ShellEnv, slug: string, main: HTMLElement): void {
  const found = b.pilots.find((x) => x.slug === slug);
  if (!found && slug) {
    main.innerHTML = `<h1>Pilot example not found</h1><p data-testid="pilot-not-found">There is no pilot example called "${esc(slug)}". Choose one of these:</p><ul>${b.pilots.map((x) => `<li><a href="${env.link(`/pilot/${x.slug}`)}">${esc(x.title)}</a></li>`).join("")}</ul>`;
    return;
  }
  const p: Pilot = found ?? b.pilots[0];
  const nav = `<nav aria-label="Pilot examples"><p>${b.pilots.map((x) => x.slug === p.slug ? `<strong aria-current="page">${esc(x.title)}</strong>` : `<a href="${env.link(`/pilot/${x.slug}`)}">${esc(x.title)}</a>`).join(" · ")}</p></nav>`;
  const banner = `<p class="banner banner-pilot"><strong>Pilot example, not a statewide result.</strong> Pilot pages show how the statewide model plays out in one place. Their figures are already inside the Wisconsin totals and are never added to them.</p>`;
  const stops = Object.entries(p.stops).map(([k, v]) => `${int(v)} ${esc(k)}`).join(", ");
  const rng = (o: Record<ScenId, number>) => `${lcFirst(scen(b, "little").label)} ${int(o.little)}, strong ${int(o.strong)}`;
  if (p.corridor) {
    const c = p.corridor;
    const labels = c.places.map((x) => x.name);
    main.innerHTML = `
    <h1>${esc(p.title)}</h1>
    ${nav}${banner}
    <p class="lede">${esc(p.intro)}</p>
    <div class="tiles tiles-3">
      <section class="tile tile-accent"><h2 class="tile-label">Extra homes near the corridor's stations, 2027–2031</h2>
        <p class="tile-num" data-testid="pilot-corridor-typical">${int(c.add.typical)}</p>
        <p class="tile-sub">central line (${rng(c.add)}) ${pill("calculated")}</p>
        </section>
      <section class="tile"><h2 class="tile-label">Extra homes near all qualifying stops in ${esc(placeName(p.city))}, 2027–2031</h2>
        <p class="tile-num" data-testid="pilot-city-typical">${int(p.city_add.typical)}</p>
        <p class="tile-sub">central line (${rng(p.city_add)}) ${pill("calculated")}</p></section>
      <section class="tile"><h2 class="tile-label">Homes permitted near all qualifying stops in ${esc(placeName(p.city))} under current law, 2027–2031</h2>
        <p class="tile-num" data-testid="pilot-baseline">${int(p.city_baseline)}</p>
        <p class="tile-sub">new homes in permits, without the law ${pill("calculated")}</p>
        <p class="tile-note">For scale: ${int(p.city_homes_near)} of the city's ${int(p.city_homes)} existing homes (2020 census) are near qualifying stops.</p></section>
    </div>
    <section class="card"><h2>The corridor</h2>
      <p>${esc(p.line)}: ${stops}.</p>
      <p class="small" data-testid="pilot-method">${esc(p.method ?? "")}</p>
      ${stationMap(b.map, { view: p.view, labels, emphasizeRapid: true, title: `${p.title}: station areas`, desc: `Purple circles are land within ½ mile of the corridor's stations; green circles are ¼ mile from 15-minute bus stops. The tables below have the numbers.` })}
      ${mapKey()}</section>
    <section class="card"><h2>Land near the corridor's stations</h2>
      <div class="table-wrap"><table class="data" data-testid="pilot-places"><caption>Land within ¼ mile of rail and rapid stops, by place, and the extra homes placed there (central line, 2027–2031)</caption>
        <thead><tr><th scope="col">Place</th><th scope="col" class="num">Acres within ¼ mile</th><th scope="col" class="num">District acres (15%)</th><th scope="col" class="num">Existing homes</th><th scope="col" class="num">Share of the place's extra homes</th><th scope="col" class="num">Extra homes</th></tr></thead>
        <tbody>${c.places.map((x) => `<tr><th scope="row">${esc(placeName(x.name))}</th><td class="num">${int(x.acres)}</td><td class="num">${int(x.district_acres)}</td><td class="num">${int(x.existing_homes)}</td><td class="num">${sharePct(x.share_of_place)}</td><td class="num">${small(x.add_typical)}</td></tr>`).join("")}
        <tr><th scope="row">Corridor</th><td class="num">${int(c.acres)}</td><td class="num">${int(c.district_acres)}</td><td class="num">${int(c.existing_homes)}</td><td class="num">—</td><td class="num">${small(c.add.typical)}</td></tr></tbody></table></div>
      <p class="small muted">Acres are lot acres. The district is 15% of them, spread at random in the model; the city would pick the actual land. ${esc(p.zoning_note ?? "")} Existing homes are counted from parcel records, so they differ slightly from the census count used elsewhere.</p></section>
    <section class="card"><h2>Extra homes near the corridor by year</h2>
      <div class="table-wrap"><table class="data" data-testid="pilot-years"><caption>Extra homes permitted near the corridor's stations by year and scenario</caption>
        <thead><tr><th scope="col">Scenario</th>${YEARS.map((y) => `<th scope="col" class="num">${y}</th>`).join("")}<th scope="col" class="num">2027–2031</th></tr></thead>
        <tbody>${SCEN_IDS.map((id) => `<tr><th scope="row">${esc(scen(b, id).label)}</th>${c.add_years[id].map((v) => `<td class="num">${small(v)}</td>`).join("")}<td class="num">${small(c.add[id])}</td></tr>`).join("")}</tbody></table></div>
      <p class="small muted">${esc(b.statewide.timing_caveat)}</p></section>`;
    return;
  }
  main.innerHTML = `
  <h1>${esc(p.title)}</h1>
  ${nav}${banner}
  <p class="lede">${esc(p.intro)}</p>
  <div class="tiles tiles-3">
    <section class="tile"><h2 class="tile-label">Homes near qualifying stops</h2>
      <p class="tile-num" data-testid="pilot-homes-near">${int(p.city_homes_near)}</p>
      <p class="tile-sub">of ${int(p.city_homes)} homes in the city (2020) ${pill("observed")}</p></section>
    <section class="tile tile-accent"><h2 class="tile-label">Extra homes from the law, 2027–2031</h2>
      <p class="tile-num" data-testid="pilot-eau-claire-add">${int(p.city_add.typical)}</p>
      <p class="tile-sub">in every scenario ${pill("calculated")}</p></section>
    <section class="tile"><h2 class="tile-label">Homes Eau Claire is expected to permit anyway, 2027–2031</h2>
      <p class="tile-num" data-testid="pilot-baseline-all">${int(p.city_baseline_all)}</p>
      <p class="tile-sub">all homes in the city under current law ${pill("calculated")}</p></section>
  </div>
  <div class="note-box" role="note" data-testid="pilot-reason"><p><strong>Why zero.</strong> ${esc(p.reason ?? "")}</p></div>
  <section class="card"><h2>Eau Claire's bus stops</h2>
    <p>${stops}. If the law counted buses every 20 minutes, ${int(p.homes_near_high)} Eau Claire homes (${sharePct((p.homes_near_high ?? 0) / p.city_homes)}) on about ${int(p.high_case_acres)} acres would be near a qualifying stop. The statewide effect of that wider definition is on <a href="${env.link("/how-sure")}">How sure</a>.</p>
    ${stationMap(b.map, { view: p.view, labels: ["Eau Claire city"], showWide: true, title: "Eau Claire: stops on 20-minute bus routes", desc: `Brown circles show land within ¼ mile of stops on Eau Claire's 20-minute routes, which count only under the wider definition. No stop qualifies in the main case.` })}
    ${mapKey(true)}
    <p class="small muted">The lesson for other mid-size Wisconsin cities: a law tied to 15-minute service reaches only places that already run it. No bus route outside the Milwaukee and Madison areas was found to run every 15 minutes (Green Bay's schedule could not be tested).</p></section>`;
}

// ---- 7. Brief --------------------------------------------------------------------------------------
export function brief(b: TodBundle, main: HTMLElement): void {
  const s = b.statewide, A = b.areas;
  const top = A.munis.slice(0, 6);
  main.innerHTML = `
  <div class="brief-tools no-print">
    <p>A one-page summary for a hearing or a colleague, with the same numbers and run id as the tool.</p>
    <button type="button" class="button" id="tod-print">Print or save as PDF</button>
  </div>
  <article class="brief tod-brief" aria-labelledby="tod-brief-h" data-testid="brief">
    <header class="brief-head">
      <p class="eyebrow">Policy brief · Wisconsin · transit-oriented density</p>
      <h1 id="tod-brief-h" data-testid="brief-headline">A statewide transit-oriented density law could add ${num(s.range90.low)} to ${num(s.range90.high)} homes permitted near major transit stops over 2027–2031 (projected range, 90%)</h1>
      <p class="brief-sub">On top of about ${int(s.baseline.total)} expected there without the law. Comparison scenarios: ${s.side_lines.map((x) => `${esc(lcFirst(x.label))}, ${sideValue(x)}`).join("; ")}. ${esc(s.range90.coverage)}</p>
    </header>
    ${estimateCardHTML("tod", s.range90, "extra homes permitted near transit")}
    <h2>What the law does</h2>
    <p>${esc(s.district.text)} Results are counted near major transit stops, which hold ${int(s.stock_homes)} of Wisconsin's ${int(s.state_homes)} homes in the 2020 census (${sharePct(s.stock_homes / s.state_homes)}), ${sharePct(s.homes_two_cities.share)} of them in the cities of Milwaukee and Madison. Parking rules and affordability requirements are unchanged.</p>
    <h2>The numbers</h2>
    <div class="table-wrap"><table class="data" data-testid="brief-table"><caption>Homes permitted near major transit stops, 2027–2031</caption>
      <thead><tr><th scope="col">Item</th><th scope="col">What it is</th><th scope="col" class="num">Homes, 2027–2031</th></tr></thead>
      <tbody><tr><th scope="row">Current law</th><td>Each place's 2023–2025 permits, share near stops</td><td class="num">${int(s.baseline.total)}</td></tr>
      <tr><th scope="row">Extra with the law: projected range</th><td>${esc(s.range90.method)}</td><td class="num">${num(s.range90.low)} to ${num(s.range90.high)}</td></tr>
      ${s.side_lines.map((x) => `<tr><th scope="row">Comparison scenario: ${esc(x.label)}</th><td>${esc(x.note)}</td><td class="num">${sideValue(x)}</td></tr>`).join("")}</tbody></table></div>
    <p class="small">The projected range by year, 2027–2031: ${s.range90.years.map((y) => `${int(y.low)} to ${int(y.high)}`).join("; ")}. ${esc(s.range90.coverage)} These are homes in issued permits, not completed homes.</p>
    <p class="small" data-testid="brief-shared">${sharedLine(b)} Reforms overlap, so their extra homes are never added together.</p>
    <h2>Where</h2>
    <p>${A.metros.map((m) => `${esc(m.name)} ${int(m.add.typical)}`).join("; ")} (central line). By place: ${top.map((m) => `${esc(m.name.replace(/ (city|village|town)$/, ""))} ${int(m.add.typical)}`).join(", ")}. Eau Claire and other mid-size cities get none: they have no rail or rapid transit stops.</p>
    <h2>Why these numbers</h2>
    <p>All three lines use our own lot data on ${int(s.district.places)} US places that zoned a district near some of their rail or rapid stops (about ${sharePct(s.district.places_mean_share)} of the land within ¼ mile, on average), compared with similar stops without reform. Central: the places' average effect, about ${dec(s.district.effect_per_100_acres, 1)} extra homes per 100 lot acres a year within ¼ mile, applied to Wisconsin's land there. Lower: the rezoned lots' own gain at district boundaries, a floor. Upper: the same average scaled up to the law's 15% of the land; bigger districts gained less per acre, so it is the upside. No model beat the plain average on places it had not seen. Land beyond ¼ mile counts zero. The cities chose their district land; a state mandate may do less. The former lines for a broader law (average reform city, Auckland, station-area model) are on How sure.</p>
    <h2>What it cannot tell you</h2>
    <p>${esc(s.timing_caveat)} The sizing has no Wisconsin test of its own. The model does not cover rents, displacement, ridership, or the law combined with parking reform, and it predicts nothing for any single lot.</p>
    <p class="small muted brief-foot">Run ${esc(b.manifest.run_id)} · ${esc(b.manifest.outcome.short)} · ${esc(b.manifest.repo_url)}</p>
  </article>`;
  document.getElementById("tod-print")!.addEventListener("click", () => window.print());
}
