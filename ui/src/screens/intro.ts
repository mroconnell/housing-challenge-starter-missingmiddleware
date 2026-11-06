// The Introduction: the tool's landing page (root route "#/"), above the per-reform screens. The words are the
// owner-approved copy (Claude Doc rev 180, audit-cleared, with the coordinator's approved parking-line change).
//
// Every number comes from a source, never typed here:
//   - ADU range: the ADU bundle's state.json range90 (low, high).
//   - TOD range: the TOD bundle's statewide.json range90 (low, high).
//   - Parking range: reference/parking_placebo_full_summary.csv (range_from_placebo_low/high, permits per 1,000
//     homes a year) × the parking bundle's eligible homes (areas.json, sum over municipalities) × 5 years / 1,000.
//     reference/parking_uniform_range.csv is stale (76 places) and is not read.
//   - Baseline: reference/housing_baseline_statewide_by_year.csv ("all" rows, 2027–2031, central) and the v4
//     multipliers in reference/housing_baseline_band.csv.
// The two CSVs are bundled at build time; tests/test_intro_sources.py and ui/tests/intro.spec.ts check the numbers.
import bandCsv from "../../../reference/housing_baseline_band.csv?raw";
import baselineCsv from "../../../reference/housing_baseline_statewide_by_year.csv?raw";
import placeboCsv from "../../../reference/parking_placebo_full_summary.csv?raw";
import { esc, int } from "../format";
import { num } from "../range";

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

/** Parking's 90% range ends as rates (permits per 1,000 homes a year). */
export function parkingRates(): { low: number; high: number } {
  const r = rows(placeboCsv)[0];
  return { low: Number(r.range_from_placebo_low), high: Number(r.range_from_placebo_high) };
}

export interface IntroNumbers {
  adu: { low: number; high: number };
  tod: { low: number; high: number };
  parking: { low: number; high: number };
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

let cached: Promise<IntroNumbers> | null = null;

export function loadIntro(): Promise<IntroNumbers> {
  cached ??= (async () => {
    const [aduBase, todBase, pkBase] = await Promise.all([runBase("runs/"), runBase("scenarios/tod/runs/"), runBase("scenarios/parking/runs/")]);
    const [state, tod, areas] = await Promise.all([
      getJSON<{ range90: { low: number; high: number } }>(`${aduBase}state.json`),
      getJSON<{ range90: { low: number; high: number } }>(`${todBase}statewide.json`),
      getJSON<{ munis: { eligible_homes: number | null }[] }>(`${pkBase}areas.json`),
    ]);
    const homes = areas.munis.reduce((a, m) => a + (m.eligible_homes ?? 0), 0);
    const k = (homes * YEARS.length) / 1000;
    const r = parkingRates();
    return {
      adu: { low: state.range90.low, high: state.range90.high },
      tod: { low: tod.range90.low, high: tod.range90.high },
      parking: { low: r.low * k, high: r.high * k },
      baseline: baselineFromCsv(),
    };
  })();
  cached.catch(() => { cached = null; });
  return cached;
}

/** A signed whole number with a true minus sign: "−1,234", "+5,678". */
const signed = (v: number) => (Math.round(v) > 0 ? `+${int(v)}` : num(v));

/** Links: ADU screens have no prefix; the Wisconsin Today screen keeps its old route. */
export const INTRO_LINKS = {
  today: "#/today",
  adu: "#/compare",
  tod: "#/tod/today",
  parking: "#/parking/compare",
};

export function renderIntro(main: HTMLElement, n: IntroNumbers): void {
  const L = INTRO_LINKS;
  const b = n.baseline;
  main.innerHTML = `
  <article class="intro" data-testid="intro">
  <h1 id="intro-h">How would housing reform change the number of new homes?</h1>
  <p class="lede intro-lede">Missing Middleware studies how real reforms worked in places that adopted them. It compares them with places or years without the reform. Then it carries what it learned to one state, and gives a range of extra home permits for the five years after a law, 2027 to 2031.</p>

  <section class="card intro-ranges" aria-labelledby="intro-ranges-h">
    <h2 id="intro-ranges-h">Wisconsin, extra permits 2027–2031, 90% range</h2>
    <ul class="intro-range-list">
      <li data-testid="intro-adu"><strong>Statewide ADU reform:</strong> <span class="intro-num" data-testid="intro-adu-range">${int(n.adu.low)} to ${int(n.adu.high)} ADU permits</span>. This range covers only how far off the model was in other states. It leaves out uncertainty in Wisconsin's own current ADU rates.</li>
      <li data-testid="intro-tod"><strong>Statewide TOD reform:</strong> <span class="intro-num" data-testid="intro-tod-range">${int(n.tod.low)} to ${int(n.tod.high)} extra homes near transit</span></li>
      <li data-testid="intro-parking"><strong>Statewide parking reform:</strong> <span class="intro-num" data-testid="intro-parking-range">${signed(n.parking.low)} to ${signed(n.parking.high)} homes</span>. A range that includes zero means the data can't tell whether repealing parking minimums alone adds or removes homes. The evidence comes from city repeals, since no state has repealed them statewide. This range is the spread of fake-repeal results, placed around the measured average.</li>
    </ul>
  </section>

  <section class="card" aria-labelledby="intro-how-h">
    <h2 id="intro-how-h">How we got there</h2>
    <ol class="intro-steps">
      <li data-testid="intro-step-1"><strong>Pick a state.</strong> <span class="intro-state" data-testid="intro-state">Wisconsin</span></li>
      <li data-testid="intro-step-2"><strong>Set a baseline.</strong> We estimate what the state would permit under current law. For Wisconsin that is about <span data-testid="intro-baseline">${int(b.central)}</span> homes over 2027–2031 (90% range <span data-testid="intro-baseline-range">${int(b.low)} to ${int(b.high)}</span>). <a href="${L.today}" data-testid="intro-link-today">Wisconsin Today</a></li>
      <li data-testid="intro-step-3"><strong>Define each reform.</strong>
        <ul class="intro-reform-links" aria-label="The modelled law for each reform">
          <li><a href="${L.adu}" data-testid="intro-link-adu">ADU reform<span class="sr-only">: the modelled law and what it adds</span></a></li>
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
      <li><strong>Carry the effect to the state.</strong> We apply each measured effect to the state's own places and homes. ADU's rate adjusts for home values and incomes. TOD and parking use one average rate, because no local trait predicted the effect better than a plain average.</li>
    </ol>
  </section>

  <section class="card" aria-labelledby="intro-see-h">
    <h2 id="intro-see-h">What you'll see</h2>
    <ul class="intro-see">
      <li><strong>A range for each reform, with its low and high ends.</strong> We show no single best guess, because the evidence supports a range, not a point.</li>
      <li><strong>Side lines across each range.</strong> They give a plain reason to believe the range. Some are real cases, like the median of 8 states that passed ADU laws. Others are our earlier scenario estimates.</li>
      <li><strong>A map of where homes might land.</strong> It shows how ADU reform spreads homes differently from TOD reform. It is an illustration, not a prediction of which lots will build.</li>
      <li><strong>Sensitivities.</strong> Other choices that could push a range up or down. Some did not pass tests set in advance. Others are reasonable alternative assumptions. Neither changes the range.</li>
    </ul>
  </section>
  </article>`;
}

/** Shown while the bundles load. */
export function introLoading(main: HTMLElement): void {
  main.innerHTML = `<h1>How would housing reform change the number of new homes?</h1><p class="muted" data-testid="intro-loading">${esc("Loading the ranges…")}</p>`;
}
