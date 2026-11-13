// The Introduction: the tool's landing page (root route "#/"), above the per-reform screens. The words are the
// owner-approved copy (Claude Doc rev 180, as changed by the owner on 2026-11-12: the ranges table moved to each
// reform's Brief tab as an estimate card, see ui/src/estimate.ts; "How we got there" is five short steps; "What you'll
// see" has four new bullets). Parking reform is off the tool for now (owner, 2026-11-12): step 3 lists three reforms.
//
// Every number comes from a source, never typed here:
//   - Baseline: reference/housing_baseline_statewide_by_year.csv ("all" rows, 2027–2031, central) and the v4
//     multipliers in reference/housing_baseline_band.csv.
// The two baseline CSVs are bundled at build time; tests/test_intro_sources.py and ui/tests/intro.spec.ts check the numbers.
import bandCsv from "../../../reference/housing_baseline_band.csv?raw";
import baselineCsv from "../../../reference/housing_baseline_statewide_by_year.csv?raw";
import { esc, int } from "../format";
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
  baseline: { central: number; low: number; high: number };
}

/** The Introduction's numbers: only the baseline now (the reform ranges are on each Brief tab). */
export function loadIntro(): Promise<IntroNumbers> {
  return Promise.resolve({ baseline: baselineFromCsv() });
}

/** Links: the shared Wisconsin today page, and each reform's Summary tab (ADU screens have no prefix). */
export const INTRO_LINKS = {
  today: "#/wisconsin-today",
  adu: "#/summary",
  middle: "#/middle/summary",
  tod: "#/tod/summary",
};

export function renderIntro(main: HTMLElement, n: IntroNumbers): void {
  const L = INTRO_LINKS;
  const b = n.baseline;
  main.innerHTML = `
  <article class="intro" data-testid="intro">
  <h1 id="intro-h">What would housing reforms mean for new home permits in Wisconsin?</h1>
  <p class="lede intro-lede"><i>Missing Middleware</i> estimates how different housing reforms would change the number of homes Wisconsin permits. We study real places that already adopted each reform and compare them to places that didn’t. We use what we learn to build a model and apply it to Wisconsin. The result is a range of extra home permits over the first five years after each reform, assuming the law takes effect on January 1, 2027.</p>

  <section class="card" aria-labelledby="intro-see-h">
    <h2 id="intro-see-h">What you'll see</h2>
    <ul class="intro-see">
      <li>How many permits we expect from each reform, with a low and high end.</li>
      <li>Comparison scenarios plotted across the timeline, in addition to our projected range.</li>
      <li>A map showing where the extra homes might go across Wisconsin.</li>
      <li>Sensitivity charts that show the biggest factors in our projected range, and charts that show how other ways of estimating compare.</li>
    </ul>
    ${introCarouselHTML()}
  </section>

  <section class="card" aria-labelledby="intro-how-h">
    <h2 id="intro-how-h">How we got there</h2>
    <ol class="intro-steps">
      <li data-testid="intro-step-1"><strong>Pick a state.</strong> <span class="intro-state" data-testid="intro-state">Wisconsin</span></li>
      <li data-testid="intro-step-2"><strong>Set a baseline in Wisconsin.</strong> We estimate what the state would permit under current law. For Wisconsin that is about <span data-testid="intro-baseline">${int(b.central)}</span> homes over 2027–2031 (projected range, 90%: <span data-testid="intro-baseline-range">${int(b.low)} to ${int(b.high)}</span>). <a href="${L.today}" data-testid="intro-link-today">Wisconsin Today</a></li>
      <li data-testid="intro-step-3"><strong>Define the proposed policies.</strong>
        <ul class="intro-reform-links" aria-label="The modelled law for each reform">
          <li><a href="${L.adu}" data-testid="intro-link-adu">ADU reform<span class="sr-only">: the modelled law and what it adds</span></a></li>
          <li><a href="${L.middle}" data-testid="intro-link-middle">Middle housing reform<span class="sr-only">: what the modelled law adds</span></a></li>
          <li><a href="${L.tod}" data-testid="intro-link-tod">TOD reform<span class="sr-only">: the modelled law and the homes near transit today</span></a></li>
        </ul></li>
      <li data-testid="intro-step-4"><strong>Look at cities and states outside Wisconsin to measure the effect of each proposed policy.</strong> Compare places where the reforms passed, and places that did not reform.</li>
      <li data-testid="intro-step-5"><strong>Carry the effect to Wisconsin.</strong> We apply each measured effect to Wisconsin, producing a range of new permits we expect to see from each policy.</li>
    </ol>
  </section>
  </article>`;
  mountIntroCarousel(main);
}

/** Shown while the bundles load. */
export function introLoading(main: HTMLElement): void {
  main.innerHTML = `<h1>What would housing reforms mean for new home permits in Wisconsin?</h1><p class="muted" data-testid="intro-loading">${esc("Loading…")}</p>`;
}
