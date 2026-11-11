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
