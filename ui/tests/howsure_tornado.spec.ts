// How sure's two what-if charts (owner, 2026-11-11 23:41; docs/shared/HOWSURE_TORNADO_CLASSIFICATION.md), for every
// reform: the model-inputs tornado is sorted by swing, its pivot is the number the 90% range is built on, and every
// what-if of the former single chart appears in exactly one of the two charts. Expected values come from the bundles.
import { expect, test, type Page } from "@playwright/test";

const fmt = (v: number) => (Math.round(v) < 0 ? `−${Math.abs(Math.round(v)).toLocaleString("en-US")}` : Math.round(v).toLocaleString("en-US"));
async function get(page: Page, path: string) { return (await page.request.get(path)).json(); }
async function run(page: Page, root: string) { const { run_id } = await get(page, `${root}latest.json`); return `${root}${run_id}/`; }

interface Case { name: string; url: string; prefix: string; pivotWords: string; expected: (page: Page) => Promise<{ pivot: number; original: string[] }> }

const CASES: Case[] = [
  { name: "ADU", url: "#/how-sure", prefix: "adu", pivotWords: "(typical adoption)", expected: async (page) => {
    const d = await run(page, "runs/");
    const st = await get(page, `${d}state.json`), u = await get(page, `${d}uncertainty.json`);
    return { pivot: st.scenarios.find((s: { id: string }) => s.id === "central").additional_total,
      original: u.sensitivity_cases.filter((c: { id: string; group: string }) => c.group === "addition" && c.id !== "adopted-model--the-scenarios").map((c: { id: string }) => c.id) };
  } },
  { name: "TOD", url: "#/tod/how-sure", prefix: "tod", pivotWords: "(the 11-place average)", expected: async (page) => {
    const d = await run(page, "scenarios/tod/runs/");
    const hs = await get(page, `${d}howsure.json`);
    return { pivot: hs.tornado.central, original: hs.tornado.rows.map((r: { id: string }) => r.id) };
  } },
  { name: "Parking", url: "#/parking/how-sure", prefix: "pk", pivotWords: "(the measured average of the 74 repeal places)", expected: async (page) => {
    const d = await run(page, "scenarios/parking/runs/");
    const st = await get(page, `${d}statewide.json`), hs = await get(page, `${d}howsure.json`);
    return { pivot: st.side_lines.find((s: { id: string }) => s.id === "measured_average").value,
      original: hs.sensitivities.filter((x: { case: string; moves: string }) => !/\(headline\)/.test(x.case) && x.moves !== "current law only").map((x: { case: string }) => x.case) };
  } },
  { name: "Middle housing", url: "#/middle/how-sure", prefix: "mid", pivotWords: "(the four-state result)", expected: async (page) => {
    const d = await run(page, "scenarios/middle/runs/");
    const st = await get(page, `${d}statewide.json`), hs = await get(page, `${d}howsure.json`);
    // the range is built on the four-state result: the core central, which is also the four-state side line
    expect(st.side_lines.find((s: { id: string }) => s.id === "four_state").value).toBe(st.core.central);
    return { pivot: st.core.central, original: hs.bars.map((x: { id: string }) => x.id) };
  } },
];

for (const c of CASES) {
  test(`${c.name} How sure: the inputs tornado and the other ways, at the top`, async ({ page }) => {
    const { pivot, original } = await c.expected(page);
    expect(original.length).toBeGreaterThan(0);
    await page.goto(c.url);
    const inputs = page.getByTestId(`${c.prefix}-inputs`), other = page.getByTestId(`${c.prefix}-other`);
    await expect(inputs).toBeVisible();
    await expect(other).toBeVisible();
    // both charts come before every other card on the page, and before Details
    const card = page.getByTestId(`${c.prefix}-whatifs`);
    expect(await card.evaluate((el) => !el.previousElementSibling || el.previousElementSibling.matches("h1, p.lede"))).toBe(true);
    await expect(card.getByRole("heading", { name: "What moves the estimate: model inputs" })).toBeVisible();
    await expect(card.getByRole("heading", { name: "Other ways to estimate it" })).toBeVisible();
    // the pivot: its plain label and value
    const pv = page.getByTestId(`${c.prefix}-pivot`);
    await expect(pv).toHaveText(`The number the 90% range is built on: ${fmt(pivot)} ${c.pivotWords}`);
    expect(Number(await pv.getAttribute("data-value"))).toBeCloseTo(pivot, 6);
    // rows sorted by swing, largest first (the flat rows, swing 0, come last)
    const swings = (await inputs.locator("[data-swing]").evaluateAll((els) => els.map((e) => Number(e.getAttribute("data-swing")))));
    expect(swings.length).toBeGreaterThan(0);
    for (let i = 1; i < swings.length; i++) expect(swings[i]).toBeLessThanOrEqual(swings[i - 1]);
    // each drawn bar is named in words with its low and high values
    for (const r of await inputs.locator(".tn-row").all()) await expect(r).toContainText(/to/);
    // every former what-if is in exactly one chart, and no id is drawn twice
    const inIds = (await inputs.locator("[data-whatif]").evaluateAll((els) => els.map((e) => e.getAttribute("data-whatif")!))).flatMap((s) => s.split("|"));
    const otherIds = await other.locator("[data-whatif]").evaluateAll((els) => els.map((e) => e.getAttribute("data-whatif")!));
    const all = [...inIds, ...otherIds];
    expect(new Set(all).size).toBe(all.length);
    for (const id of original) expect(all.filter((x) => x === id), id).toHaveLength(1);
    // the table fallbacks hold every row
    await inputs.getByText("Show as a table").click();
    await expect(page.getByTestId(`${c.prefix}-inputs-table`).locator("tbody tr")).toHaveCount(await inputs.locator("[data-whatif]").count());
    await other.getByText("Show as a table").click();
    await expect(page.getByTestId(`${c.prefix}-other-table`).locator("tbody tr")).toHaveCount(otherIds.length);
  });

  test(`${c.name} How sure charts fit a 375 px screen`, async ({ page }) => {
    await page.setViewportSize({ width: 375, height: 800 });
    await page.goto(c.url);
    await expect(page.getByTestId(`${c.prefix}-inputs`)).toBeVisible();
    const over = await page.evaluate(() => document.documentElement.scrollWidth - document.documentElement.clientWidth);
    expect(over).toBeLessThanOrEqual(0);
    const box = await page.getByTestId(`${c.prefix}-whatifs`).boundingBox();
    expect(box!.x + box!.width).toBeLessThanOrEqual(375);
  });
}

// Placement reviews (2026-11-11): the ADU thread's review, middle housing's input what-ifs, parking's measured averages.
const ids = async (page: Page, testid: string, sel: string) =>
  (await page.getByTestId(testid).locator(sel).evaluateAll((els) => els.map((e) => e.getAttribute("data-whatif")!))).flatMap((s) => s.split("|"));

test("ADU How sure: review placements, counts and the side lines in Other ways", async ({ page }) => {
  const d = await run(page, "runs/");
  const st = await get(page, `${d}state.json`);
  await page.goto("#/how-sure");
  await expect(page.getByTestId("adu-inputs")).toBeVisible();
  const bars = await ids(page, "adu-inputs", ".tn-row"), flat = await ids(page, "adu-inputs", ".tn-flat [data-whatif]"), other = await ids(page, "adu-other", "[data-whatif]");
  // the lower scenario is tested and leaves the total alone; it only moves the OR & RI side line
  expect(flat).toContain("lower-scenario-at-the-10th-percentile-of");
  await expect(page.getByTestId("adu-inputs").locator(".tn-flat")).toContainText("changes only the OR & RI side line (6,321 → 5,401)");
  // Gate 4's three data settings are one bar at 8,402
  expect(bars).toContain("comparison-state-counts-and-coding-as-at");
  const g4 = page.getByTestId("adu-inputs").locator('.tn-row[data-whatif="comparison-state-counts-and-coding-as-at"]');
  await expect(g4).toContainText("Three data settings at once (as at Gate 4)");
  await expect(g4).toContainText("8,402");
  await expect(page.getByTestId("adu-inputs")).toContainText("no scale-up for non-reporting towns, Washington from enactment, Massachusetts at 11/12");
  // no slow start stays an input
  expect([...bars, ...flat]).toContain("no-slow-start--full-effect-from-2027");
  // other ways: count per eligible property (with its note) and the five How-sure-only side lines, not the two that repeat cases
  expect(other).toContain("count-per-eligible-property--not-per-sin");
  for (const id of ["drift_main", "drift_heat_only", "drift_equal_weight", "ca_high", "bias_corrected"]) expect(other.filter((x) => x === `side:${id}`), id).toHaveLength(1);
  expect(other).not.toContain("side:whatif_791");
  expect(other).not.toContain("side:whatif_2255");
  const want: Record<string, string> = { drift_main: "11,318", drift_heat_only: "10,441", drift_equal_weight: "10,746", ca_high: "19,784", bias_corrected: "7,517 to 13,318" };
  for (const [id, v] of Object.entries(want)) {
    const r = page.getByTestId("adu-other").locator(`[data-whatif="side:${id}"]`);
    await expect(r).toContainText(st.side_lines.find((s: { id: string }) => s.id === id).label);
    await expect(r).toContainText(v);
  }
  // the corrected range is a bar from its low to its high, not a dot
  await expect(page.getByTestId("adu-other").locator('[data-whatif="side:bias_corrected"] .vs-span')).toHaveCount(1);
  await expect(page.getByTestId("adu-other").locator('[data-whatif="side:bias_corrected"] .vs-dot')).toHaveCount(0);
  // counts: 13 + 2 moved = 15 former rows in Inputs, 3 former rows + 5 side lines in Other ways
  expect(other).toHaveLength(8);
  await page.getByTestId("adu-other").getByText("Show as a table").click();
  await expect(page.getByTestId("adu-other-table")).toContainText("a separate model with its own baseline (636)");
  await expect(page.getByTestId("adu-other-table")).toContainText("post hoc");
});

test("Middle housing How sure: the bundle's input what-ifs are bars around 1,570", async ({ page }) => {
  await page.goto("#/middle/how-sure");
  await expect(page.getByTestId("mid-inputs")).toBeVisible();
  const want: Record<string, string> = { match_nationally: "1,560 to 1,570", oregon_before: "1,454 to 1,570", census_filled: "−382 to 1,570",
    leave_one_state: "788 to 1,984", first_year_share: "1,515 to 1,658", flat_timing: "to" };
  for (const [id, v] of Object.entries(want)) await expect(page.getByTestId("mid-inputs").locator(`.tn-row[data-whatif="${id}"]`), id).toContainText(v);
  await expect(page.getByTestId("mid-inputs")).toContainText("failed the fake-years check");
  expect(await ids(page, "mid-inputs", "[data-whatif]")).toHaveLength(6);
  expect(await ids(page, "mid-other", "[data-whatif]")).toHaveLength(4);
});

test("Parking How sure: measured averages, and the cleaned-data rounds as inputs", async ({ page }) => {
  await page.goto("#/parking/how-sure");
  const inputs = page.getByTestId("pk-inputs");
  await expect(inputs).toBeVisible();
  await expect(inputs).not.toContainText("Scaled from");
  const bar = (id: string) => inputs.locator(`.tn-row[data-whatif*="${id}"]`);
  const want: [string, string][] = [["High end, with towns left out", "−15,380 to −10,760"], ["Near-benchmark places at the full rate", "−15,472 to −15,380"],
    ["Cleaned data, undated reforms kept as comparisons (placebo)", "−15,380 to −11,035"], ["Cleaned data, strict comparison cleaning (placebo)", "−15,380 to −3,691"],
    ["Cleaned data, only apartment-scale reforms disqualify comparisons (placebo)", "−15,380 to −5,389"],
    ["As above, plus state laws in California, Oregon and Washington (placebo)", "−15,380 to −7,073"]];
  for (const [id, v] of want) await expect(bar(id), id).toContainText(v);
  // the two strict-cleaning readings share one average and one bar
  await expect(inputs.locator('.tn-row[data-whatif="Cleaned data, strict comparison cleaning (placebo)|Cleaned data, strict comparison cleaning (resampling)"]')).toHaveCount(1);
  await expect(inputs.locator(".tn-row").filter({ hasText: "earlier 76-place sample (73 matched)" })).toHaveCount(4);
  expect(await ids(page, "pk-inputs", ".tn-row")).toHaveLength(7);
  expect(await ids(page, "pk-other", "[data-whatif]")).toHaveLength(6);
});
