// The Introduction: the tool's landing page (root route "#/"), above the per-reform screens. The words are the
// owner-approved copy (Claude Doc rev 180, audit-cleared, with the coordinator's approved parking-line change).
//
// Every number comes from a source, never typed here:
//   - ADU range: the ADU bundle's state.json range90 (low, high).
//   - TOD range: the TOD bundle's statewide.json range90 (low, high).
//   - Parking range: the parking bundle's statewide.json range90 (low, high).
//   - Missing Middle range: the middle housing bundle's statewide.json core (lower, upper), the
//     90% range for homes in 2–4 unit buildings; its unit comes from core.label. Only the core range is shown.
//   - Baseline: reference/housing_baseline_statewide_by_year.csv ("all" rows, 2027–2031, central) and the v4
//     multipliers in reference/housing_baseline_band.csv.
// The two baseline CSVs are bundled at build time; tests/test_intro_sources.py and ui/tests/intro.spec.ts check the numbers.
import bandCsv from "../../../reference/housing_baseline_band.csv?raw";
import baselineCsv from "../../../reference/housing_baseline_statewide_by_year.csv?raw";
import { esc, int } from "../format";
import { HOW_WE_COUNT } from "../howwecount";
import { num } from "../range";
import { introCarouselHTML, mountIntroCarousel } from "./intro_carousel";

const YEARS = [2027, 2028, 2029, 2030, 2031];

/** Header and rows of a simple CSV (no quoted commas in the columns read here). */
function rows(csv: string): Record<string, string>[] {
  const [head, ...lines] = csv.trim().split(/\r?\n/);
  const cols = head.split(",");
  return lines.map((l) => { const v = l.split(","); return Object.fromEntries(cols.map((c, i) => [c, v[i]])); });
}

/** The shared all-housing baseline (v4) for Wisconsin, 2027–2031: central, low and high. */
export function baselineFromCsv(): { central: number; low: number; high: number } {
  const central = rows(baselineCsv)
    .filter((r) => r.structure_type === "all" && r.kind === "projected" && YEARS.includes(Number(r.year)))
    .reduce((a, r) => a + Number(r.central), 0);
  const band = rows(bandCsv).find((r) => r.structure_type === "1unit")!;
  return { central, low: central * Number(band.low), high: central * Number(band.high) };
}

/** The baseline year by year, for the Wisconsin today chart: observed homes permitted (all sizes, with Milwaukee's
 *  apartments estimated) and the current-law projection (2026 bridge year, then 2027–2031) with its yearly range. */
export function baselineYearsFromCsv(): { observed: { year: number; value: number }[]; projected: { year: number; central: number; low: number; high: number; bridge: boolean }[] } {
  const all = rows(baselineCsv).filter((r) => r.structure_type === "all");
  return {
    observed: all.filter((r) => r.kind === "observed_adjusted_for_milwaukee").map((r) => ({ year: Number(r.year), value: Number(r.central) })),
    projected: all.filter((r) => r.kind === "projected" || r.kind === "projected_bridge_year")
      .map((r) => ({ year: Number(r.year), central: Number(r.central), low: Number(r.low), high: Number(r.high), bridge: r.kind === "projected_bridge_year" }))
      .sort((a, b) => a.year - b.year),
  };
}

export interface IntroNumbers {
  adu: { low: number; high: number };
  tod: { low: number; high: number };
  parking: { low: number; high: number };
  /** null when the middle housing bundle cannot be read: the row then says "not yet available". */
  middle: { low: number; high: number; unit: string } | null;
  baseline: { central: number; low: number; high: number };
}

async function getJSON<T>(url: string): Promise<T> {
  const res = await fetch(url);
  if (!res.ok) throw new Error(`Could not load ${url} (${res.status})`);
  return (await res.json()) as T;
}

async function runBase(root: string): Promise<string> {
  const { run_id } = await getJSON<{ run_id: string }>(`${root}latest.json`);
  return `${root}${run_id}/`;
}

/** Middle housing's 90% range (core.lower, core.upper) and its unit, from core.label without "(predicted range)".
 *  A missing middle housing bundle leaves the row "not yet available" instead of failing the page. */
async function loadMiddle(): Promise<IntroNumbers["middle"]> {
  try {
    const midBase = await runBase("scenarios/middle/runs/");
    const { core } = await getJSON<{ core: { label: string; lower: number; upper: number } }>(`${midBase}statewide.json`);
    if (!Number.isFinite(core?.lower) || !Number.isFinite(core?.upper)) return null;
    return { low: core.lower, high: core.upper, unit: core.label.replace(/\s*\(.*?\)\s*$/, "") };
  } catch {
    return null;
  }
}

let cached: Promise<IntroNumbers> | null = null;

export function loadIntro(): Promise<IntroNumbers> {
  cached ??= (async () => {
    const [aduBase, todBase, pkBase] = await Promise.all([runBase("runs/"), runBase("scenarios/tod/runs/"), runBase("scenarios/parking/runs/")]);
    const [state, tod, parking, middle] = await Promise.all([
      getJSON<{ range90: { low: number; high: number } }>(`${aduBase}state.json`),
      getJSON<{ range90: { low: number; high: number } }>(`${todBase}statewide.json`),
      getJSON<{ range90: { low: number; high: number } }>(`${pkBase}statewide.json`),
      loadMiddle(),
    ]);
    return {
      adu: { low: state.range90.low, high: state.range90.high },
      tod: { low: tod.range90.low, high: tod.range90.high },
      parking: { low: parking.range90.low, high: parking.range90.high },
      middle,
      baseline: baselineFromCsv(),
    };
  })();
  cached.catch(() => { cached = null; });
  return cached;
}

/** A signed whole number with a true minus sign: "−1,234", "+5,678". */
const signed = (v: number) => (Math.round(v) > 0 ? `+${int(v)}` : num(v));

/** Links: the shared Wisconsin today page, and each reform's Summary tab (ADU screens have no prefix). */
export const INTRO_LINKS = {
  today: "#/wisconsin-today",
  adu: "#/summary",
  middle: "#/middle/summary",
  tod: "#/tod/summary",
  parking: "#/parking/summary",
};

/** One row of the ranges table. A range that dips below zero shows a sign on both ends (minus and plus). */
function rangeRow(id: string, name: string, r: { low: number; high: number } | null, how: string): string {
  const f = r && r.low < 0 ? signed : int;
  const cell = (v: number | undefined, end: string) =>
    `<td class="num intro-num" data-label="${end}" data-testid="intro-${id}-${end === "Low end" ? "low" : "high"}">${r && v !== undefined ? f(v) : "not yet available"}</td>`;
  return `<tr data-testid="intro-${id}"><th scope="row">${esc(name)}</th>${cell(r?.low, "Low end")}${cell(r?.high, "High end")}<td class="intro-how" data-label="How we count">${esc(how)}</td></tr>`;
}

export function renderIntro(main: HTMLElement, n: IntroNumbers): void {
  const L = INTRO_LINKS;
  const b = n.baseline;
  main.innerHTML = `
  <article class="intro" data-testid="intro">
  <h1 id="intro-h">Let's build some housing!</h1>
  <p class="intro-sub">If Wisconsin adopts new housing bills, how many more homes would it permit?</p>
  <p class="lede intro-lede">Missing Middleware estimates how many extra homes different housing reforms could add. We study real places that already adopted each reform and compare them with places that didn’t. We test how well that comparison holds up. Then we carry what we learned to Wisconsin, and give a range of extra home permits for the first five years, assuming a law takes effect on 1 January 2027.</p>

  <section class="card" aria-labelledby="intro-see-h">
    <h2 id="intro-see-h">What you'll see</h2>
    <ul class="intro-see">
      <li><strong>A range for each reform, with its low and high ends.</strong> We show no single best guess, because the evidence supports a range, not a point.</li>
      <li><strong>Side lines across each range.</strong> They give a plain reason to believe the range. Some are real cases, like the median of 8 states that passed ADU laws. Others are our earlier scenario estimates.</li>
      <li><strong>A map of where homes might land.</strong> It shows how ADU reform spreads homes differently from TOD reform. It is an illustration, not a prediction of which lots will build.</li>
      <li><strong>Sensitivities.</strong> Other choices that could push a range up or down. Some are reasonable alternative assumptions. Others show other ways to look at the reform that failed to pass our rigorous test design standards.</li>
    </ul>
    ${introCarouselHTML()}
  </section>

  <section class="card" aria-labelledby="intro-how-h">
    <h2 id="intro-how-h">How we got there</h2>
    <ol class="intro-steps">
      <li data-testid="intro-step-1"><strong>Pick a state.</strong> <span class="intro-state" data-testid="intro-state">Wisconsin</span></li>
      <li data-testid="intro-step-2"><strong>Set a baseline.</strong> We estimate what the state would permit under current law. For Wisconsin that is about <span data-testid="intro-baseline">${int(b.central)}</span> homes over 2027–2031 (90% range <span data-testid="intro-baseline-range">${int(b.low)} to ${int(b.high)}</span>). <a href="${L.today}" data-testid="intro-link-today">Wisconsin Today</a></li>
      <li data-testid="intro-step-3"><strong>Define each reform.</strong>
        <ul class="intro-reform-links" aria-label="The modelled law for each reform">
          <li><a href="${L.adu}" data-testid="intro-link-adu">ADU reform<span class="sr-only">: the modelled law and what it adds</span></a></li>
          <li><a href="${L.middle}" data-testid="intro-link-middle">Middle housing reform<span class="sr-only">: what the modelled law adds</span></a></li>
          <li><a href="${L.tod}" data-testid="intro-link-tod">TOD reform<span class="sr-only">: the modelled law and the homes near transit today</span></a></li>
          <li><a href="${L.parking}" data-testid="intro-link-parking">Parking reform<span class="sr-only">: the modelled law and what it adds</span></a></li>
        </ul></li>
      <li><strong>Measure the effect where it really happened.</strong> We measure what happened where a reform passed, against places or years without it. The difference is our estimate of the reform's effect.</li>
      <li><strong>Test the method.</strong>
        <ol class="intro-substeps">
          <li>We hide data from some places and try to predict them, then check how close we got.</li>
          <li>We run placebo tests in places that never reformed by pretending they reformed in a given year. The method should find no effect there.</li>
          <li>A 90% range should hold the true answer about 9 times in 10. Where a test showed it held less often, we widened the range or say so on the page.</li>
        </ol></li>
      <li data-testid="intro-step-6"><strong>Carry the effect to Wisconsin.</strong> We apply each measured effect to Wisconsin's own places and homes. ADU's rate adjusts for home values and incomes. Middle housing applies the same rate to every single-family home, measured in the 4 states that passed laws against similar places without them. The first year starts weak: in the 3 states with a separate first year, it averaged slightly below zero, too noisy to tell its sign. TOD and parking use one average rate, because no local trait predicted the effect better than a plain average. TOD's extra homes land only within ¼ mile of rail and rapid-bus stops.</li>
    </ol>
  </section>

  <section class="card intro-ranges" aria-labelledby="intro-ranges-cap">
    <div class="table-wrap">
    <table class="data intro-range-table" data-testid="intro-range-table">
      <caption id="intro-ranges-cap">Wisconsin, extra permits 2027–2031, 90% range</caption>
      <thead><tr><th scope="col">Reform</th><th scope="col" class="num">Low end</th><th scope="col" class="num">High end</th><th scope="col">How we count</th></tr></thead>
      <tbody>
        ${rangeRow("adu", "ADUs by right", n.adu, HOW_WE_COUNT.adu)}
        ${rangeRow("middle", "Missing Middle", n.middle, n.middle ? HOW_WE_COUNT.middle : "Not yet available.")}
        ${rangeRow("tod", "TOD Upzoning", n.tod, HOW_WE_COUNT.tod)}
        ${rangeRow("parking", "Parking Minimum Repeal", n.parking, HOW_WE_COUNT.parking)}
      </tbody>
    </table>
    </div>
  </section>
  </article>`;
  mountIntroCarousel(main);
}

/** Shown while the bundles load. */
export function introLoading(main: HTMLElement): void {
  main.innerHTML = `<h1>Let's build some housing!</h1><p class="muted" data-testid="intro-loading">${esc("Loading the ranges…")}</p>`;
}
