// Smoke tests for the Gate 4 ADU tool: headline numbers equal the bundle, scenario switching,
// map/table reconciliation, pilots, keyboard access and the mobile layout.
import { expect, test, type Page } from "@playwright/test";

const fmt = (v: number) => Math.round(v).toLocaleString("en-US");
const sum = (xs: number[]) => xs.reduce((a, b) => a + b, 0);

async function bundle(page: Page) {
  const { run_id } = await (await page.request.get("runs/latest.json")).json();
  const get = async (f: string) => (await page.request.get(`runs/${run_id}/${f}`)).json();
  return { run_id, state: await get("state.json"), pilots: await get("pilots.json"), areas: await get("areas.json") };
}
const SCREENS = ["today", "compare", "where", "how-sure", "why", "pilot/madison", "pilot/pleasant-prairie", "pilot/sun-prairie", "brief"];

test("every screen loads without errors and shows the run id", async ({ page }) => {
  const errors: string[] = [];
  page.on("pageerror", (e) => errors.push(String(e)));
  page.on("console", (m) => { if (m.type() === "error") errors.push(m.text()); });
  const b = await bundle(page);
  for (const s of SCREENS) {
    await page.goto(`#/${s}`);
    await expect(page.locator("h1").first()).toBeVisible();
    await expect(page.getByTestId("run-id")).toHaveText(b.run_id);
    await expect(page.locator("footer")).toContainText("Not completed homes");
  }
  expect(errors).toEqual([]);
});

test("headline numbers match the bundle", async ({ page }) => {
  const b = await bundle(page);
  const sc = Object.fromEntries(b.state.scenarios.map((s: { id: string }) => [s.id, s]));
  await page.goto("#/today");
  await expect(page.getByTestId("today-baseline")).toHaveText(fmt(b.state.baseline.total));
  await expect(page.getByTestId("today-central")).toHaveText("+" + fmt(sc.central.additional_total));
  await expect(page.getByTestId("sf-homes")).toHaveText(fmt(b.state.homes.value));
  // the adopted Gate 3 packet values
  expect(fmt(sc.lower.additional_total)).toBe("4,407");
  expect(fmt(sc.central.additional_total)).toBe("8,721");
  expect(fmt(sc.upper.additional_total)).toBe("16,853");
  expect(fmt(b.state.baseline.total)).toBe("645");

  await page.goto("#/compare");
  for (const p of ["lower", "central", "upper"]) await expect(page.getByTestId(`total-${p}`)).toHaveText(fmt(sc[p].additional_total));
  await expect(page.getByTestId("baseline-total")).toHaveText(fmt(b.state.baseline.total));
  await expect(page.getByTestId("additional-total")).toHaveText("+" + fmt(sc.central.additional_total));
  const rows = page.getByTestId("compare-table").locator("tbody tr");
  await expect(rows).toHaveCount(5);
  for (let i = 0; i < 5; i++) await expect(rows.nth(i).locator("td").nth(2)).toHaveText(fmt(sc.central.additional_by_year[i]));
});

test("scenario switch updates every headline", async ({ page }) => {
  const b = await bundle(page);
  const up = b.state.scenarios.find((s: { id: string }) => s.id === "upper");
  await page.goto("#/compare");
  await page.getByLabel(/Strong adoption/).first().check();
  await expect(page.getByTestId("additional-total")).toHaveText("+" + fmt(up.additional_total));
  await expect(page.getByTestId("withlaw-total")).toHaveText(fmt(up.with_law_total));
  await page.goto("#/pilot/pleasant-prairie");
  const pp = b.pilots.find((p: { slug: string }) => p.slug === "pleasant-prairie");
  await expect(page.getByTestId("pilot-additional")).toHaveText("+" + fmt(sum(pp.add.upper)));
});

test("map table reconciles to the state for each year and geography", async ({ page }) => {
  const b = await bundle(page);
  const cen = b.state.scenarios.find((s: { id: string }) => s.id === "central");
  await page.goto("#/where");
  const rec = page.getByTestId("reconcile");
  await expect(rec).toContainText("✓");
  await expect(rec).toContainText(fmt(cen.additional_total));
  const slider = page.locator("#year");
  await slider.focus();
  await page.keyboard.press("ArrowLeft");
  await page.keyboard.press("ArrowLeft");
  await expect(page.locator("#year-out")).toHaveText("2029");
  await expect(rec).toContainText(fmt(sum(cen.additional_by_year.slice(0, 3))));
  await expect(rec).toContainText("✓");
  await page.getByRole("radio", { name: "Cities, villages and towns" }).check();
  await expect(page.getByTestId("reconcile")).toContainText("✓");
  await expect(page.getByTestId("reconcile")).toContainText("1,925 areas");
  // missing is a dash with a reason, never 0
  await page.locator("#q").fill("County subdivisions not defined");
  const first = page.getByTestId("where-table").locator("tbody tr").first();
  await expect(first).toContainText("—");
  await expect(first).toContainText("no homes");
  // no point markers: the map only draws area fills
  await expect(page.locator("#map .maplibregl-marker")).toHaveCount(0);
});

test("pilot pages show baselines and additions from the bundle", async ({ page }) => {
  const b = await bundle(page);
  for (const p of b.pilots) {
    await page.goto(`#/pilot/${p.slug}`);
    await expect(page.locator(".banner-pilot")).toContainText("Pilot example, not a statewide result");
    await expect(page.getByTestId("pilot-baseline")).toHaveText(fmt(sum(p.base)));
    for (const k of ["lower", "central", "upper"]) await expect(page.getByTestId(`pilot-total-${k}`)).toHaveText(sum(p.add[k]).toFixed(1));
    const obs = page.getByTestId("pilot-observed").locator("tbody tr");
    await expect(obs).toHaveCount(p.permits.years.length);
  }
  const mad = b.pilots.find((p: { slug: string }) => p.slug === "madison");
  expect(sum(mad.add.central).toFixed(1)).toBe("134.9");
});

test("keyboard: skip link, tab navigation and scenario radios", async ({ page, isMobile }) => {
  test.skip(isMobile, "keyboard test runs on desktop");
  await page.goto("#/today");
  await expect(page.locator("h1")).toBeVisible();
  await page.keyboard.press("Tab");
  await expect(page.locator(".skip")).toBeFocused();
  await page.keyboard.press("Enter");
  await expect(page.locator("main")).toBeFocused();
  await expect(page).toHaveURL(/#\/today/);
  // tab to the "Statewide comparison" nav link and open it with Enter
  await page.goto("#/today");
  const link = page.locator('nav.tabs a[href="#/compare"]');
  for (let i = 0; i < 20 && !(await link.evaluate((el) => el === document.activeElement)); i++) await page.keyboard.press("Tab");
  await expect(link).toBeFocused();
  await page.keyboard.press("Enter");
  await expect(page).toHaveURL(/#\/compare/);
  await expect(page.locator('nav.tabs a[aria-current="page"]')).toHaveText(/Statewide comparison/);
  const central = page.locator('input[name="scen-compare"][value="central"]');
  await central.focus();
  await page.keyboard.press("ArrowRight");
  await expect(page.locator('input[name="scen-compare"][value="upper"]')).toBeChecked();
  await expect(page.locator('input[name="scen-compare"][value="upper"]')).toBeFocused();
  // sortable table headers are buttons
  await page.goto("#/where");
  const sortBtn = page.locator('button.sort[data-k="homes"]');
  await sortBtn.focus();
  await page.keyboard.press("Enter");
  await expect(page.locator('th[aria-sort="descending"] button[data-k="homes"]')).toHaveCount(1);
});

test("no horizontal scrolling on any screen", async ({ page }) => {
  for (const s of SCREENS) {
    await page.goto(`#/${s}`);
    await page.waitForTimeout(s === "where" ? 1200 : 200);
    const [sw, cw] = await page.evaluate(() => [document.documentElement.scrollWidth, document.documentElement.clientWidth]);
    expect(sw, `${s} scrollWidth`).toBeLessThanOrEqual(cw);
  }
});

test("brief carries the headline numbers", async ({ page }) => {
  const b = await bundle(page);
  await page.goto("#/brief");
  const t = page.getByTestId("brief-table");
  for (const s of b.state.scenarios) await expect(t).toContainText(fmt(s.additional_total));
  await expect(page.locator(".brief")).toContainText(b.run_id);
});

test("Madison's different treatment is explained on its pilot page, details panel and map", async ({ page }) => {
  await page.goto("#/pilot/madison");
  await expect(page.getByTestId("madison-note")).toContainText("Gate 5");
  await expect(page.getByTestId("madison-2026")).toContainText("provisional");
  await page.goto("#/where");
  await expect(page.getByTestId("map-madison-note")).toContainText("Madison alone");
  await page.getByRole("radio", { name: "Cities, villages and towns" }).check();
  await page.locator("#q").fill("Madison city");
  await page.getByRole("button", { name: "Details for Madison city" }).click();
  await expect(page.getByTestId("detail-madison-note")).toContainText("Gate 5");
});

test("scenario choice is kept in the URL and the current tab is in view", async ({ page }) => {
  await page.goto("#/compare");
  await page.getByLabel(/Strong adoption/).first().check();
  await expect(page).toHaveURL(/s=upper/);
  await page.goto("#/brief");
  const tab = page.locator('nav.tabs a[aria-current="page"]');
  await expect(tab).toBeInViewport();
});
