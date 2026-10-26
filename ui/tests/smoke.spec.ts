// Smoke tests for the Gate 4 ADU tool: headline numbers equal the bundle, scenario switching,
// map/table reconciliation, pilots, keyboard access and the mobile layout.
import { expect, test, type Page } from "@playwright/test";

const fmt = (v: number) => Math.round(v).toLocaleString("en-US");
const sum = (xs: number[]) => xs.reduce((a, b) => a + b, 0);

async function bundle(page: Page) {
  const { run_id } = await (await page.request.get("runs/latest.json")).json();
  const get = async (f: string) => (await page.request.get(`runs/${run_id}/${f}`)).json();
  return { run_id, state: await get("state.json"), pilots: await get("pilots.json"), areas: await get("areas.json"),
    unknown: await get("unknown_rules.json"), districts: await get("districts.json") };
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
  // ordering of the adopted values (the values themselves are checked against reference/adu_model_*.csv in tests/test_ui_bundle.py)
  expect(sc.lower.additional_total).toBeLessThan(sc.central.additional_total);
  expect(sc.central.additional_total).toBeLessThan(sc.upper.additional_total);

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

test("Madison's different treatment is explained on its pilot page and only when Madison or Dane County is picked", async ({ page }) => {
  await page.goto("#/pilot/madison");
  await expect(page.getByTestId("pilot-intro")).toContainText("What is a pilot page?");
  await expect(page.getByTestId("pilot-intro")).toContainText("already inside the Wisconsin total");
  await expect(page.getByTestId("madison-note")).toContainText("Cities like Madison");
  await expect(page.getByTestId("madison-note")).toContainText("Spokane");
  await expect(page.getByTestId("madison-2026")).toContainText("provisional");
  await expect(page.getByTestId("madison-2026")).toContainText("twin home ADU");
  await page.goto("#/where");
  await expect(page.getByTestId("detail-madison-note")).toHaveCount(0);
  await page.locator("#q").fill("Dane");
  await page.getByRole("button", { name: "Details for Dane County" }).click();
  await expect(page.getByTestId("detail-madison-note")).toContainText("Madison");
  await page.getByRole("radio", { name: "Cities, villages and towns" }).check();
  await page.locator("#q").fill("Madison city");
  await page.getByRole("button", { name: "Details for Madison city" }).click();
  await expect(page.getByTestId("detail-madison-note")).toContainText("December 2026");
  await page.locator("#q").fill("Middleton city");
  await page.getByRole("button", { name: "Details for Middleton city" }).click();
  await expect(page.getByTestId("detail-madison-note")).toHaveCount(0);
});

test("chart key, tables and brief use the bundle's labels", async ({ page }) => {
  const b = await bundle(page);
  const L = b.state.labels;
  await page.goto("#/compare");
  await expect(page.getByTestId("compare-intro")).toContainText("not confidence intervals");
  const legend = page.locator("#h-path").locator("xpath=ancestor::section").locator(".legend");
  await expect(legend).toContainText(L.baseline);
  await expect(legend).toContainText(L.band);
  await expect(legend).toContainText(L.reference);
  for (const s of b.state.scenarios) {
    await expect(legend).toContainText(s.chart_label);
    await expect(page.getByTestId("compare-table")).toContainText(s.chart_label);
  }
  await page.goto("#/brief");
  for (const s of b.state.scenarios) await expect(page.getByTestId("brief-table")).toContainText(s.chart_label);
  await expect(page.getByTestId("brief-table")).toContainText(L.reference);
});

test("map defaults and county labels", async ({ page }) => {
  await page.goto("#/where");
  await expect(page.locator('input[name="geo"][value="counties"]')).toBeChecked();
  await expect(page.locator('input[name="measure"][value="count"]')).toBeChecked();
  await expect(page.locator('input[name="layer"][value="additional"]')).toBeChecked();
  await expect(page.locator('input[name="scen-where"][value="central"]')).toBeChecked();
  await expect(page.locator("#year-out")).toHaveText("2031");
  await expect(page.locator("#map-title")).toContainText("2027–2031");
  await expect(page.locator("#lbl")).toBeChecked();
  // the glyphs are self-hosted: the first label range loads from the tool's own server
  const glyph = await page.request.get("fonts/open-sans-semibold/0-255.pbf");
  expect(glyph.status()).toBe(200);
  await page.locator("#lbl").uncheck();
  await expect(page.locator("#lbl")).not.toBeChecked();
});

test("sensitivity cases are grouped by the number they move", async ({ page }) => {
  await page.goto("#/how-sure");
  await expect(page.getByTestId("sens-group-addition")).toBeVisible();
  await expect(page.getByTestId("sens-group-baseline")).toBeVisible();
  await expect(page.getByTestId("sens-group-local")).toBeVisible();
  await expect(page.getByTestId("baseline-only-table")).toContainText("+209");
});

test("scenario choice is kept in the URL and the current tab is in view", async ({ page }) => {
  await page.goto("#/compare");
  await page.getByLabel(/Strong adoption/).first().check();
  await expect(page).toHaveURL(/s=upper/);
  await page.goto("#/brief");
  const tab = page.locator('nav.tabs a[aria-current="page"]');
  await expect(tab).toBeInViewport();
});

// ---- Gate 5 -------------------------------------------------------------------------------
test("unknown-rules switch shows each precomputed run", async ({ page }) => {
  const b = await bundle(page);
  await page.goto("#/how-sure");
  await expect(page.getByTestId("trace-summary")).toContainText("73.4%");
  await expect(page.getByTestId("trace-summary")).toContainText("5.5%");
  await expect(page.getByTestId("trace-summary")).toContainText("21.1%");
  for (const v of b.unknown.variants) {
    await page.locator(`input[name="unk-howsure"][value="${v.id}"]`).check();
    await expect(page.getByTestId("unk-baseline")).toHaveText(fmt(v.baseline_total));
    await expect(page.getByTestId("unk-additional")).toHaveText("+" + fmt(v.additional_total.central));
    await expect(page.getByTestId("unk-total")).toHaveText(fmt(v.with_law_total.central));
  }
  // the choice carries to the Where map, where counties reconcile to that run's statewide figures
  await expect(page).toHaveURL(/u=like_benchmark/);
  await page.goto("#/where?u=like_benchmark");
  const ben = b.unknown.variants.find((v: { id: string }) => v.id === "like_benchmark");
  await expect(page.getByTestId("reconcile")).toContainText("✓");
  await expect(page.getByTestId("reconcile")).toContainText(fmt(ben.additional_by_year.central.reduce((a: number, x: number) => a + x, 0)));
  await expect(page.getByTestId("reconcile")).toContainText(fmt(ben.baseline_by_year.reduce((a: number, x: number) => a + x, 0)));
});

test("districts reconcile to the state and disable the unknown-rules switch", async ({ page }) => {
  const b = await bundle(page);
  const cen = b.state.scenarios.find((s: { id: string }) => s.id === "central");
  await page.goto("#/where?u=like_prohibited");
  for (const i of await page.getByTestId("unknown-switch").locator("input").all()) await expect(i).toBeEnabled();
  for (const [name, n] of [["Assembly districts", 99], ["Senate districts", 33]] as const) {
    await page.getByRole("radio", { name }).check();
    const sw = page.getByTestId("unknown-switch");
    for (const i of await sw.locator("input").all()) await expect(i).toBeDisabled();
    await expect(sw.locator('input[value="like_restricted"]')).toBeChecked();
    await expect(page.getByTestId("unknown-note")).toContainText("adopted assumption only");
    const rec = page.getByTestId("reconcile");
    await expect(rec).toContainText("✓");
    await expect(rec).toContainText(`${n} ${name}`);
    await expect(rec).toContainText("not allocated to a district");
    await expect(rec).toContainText(fmt(cen.additional_total));
    await expect(page.getByTestId("unallocated-row")).toContainText("Not allocated to a district");
    await expect(page.getByTestId("where-table").locator("tbody tr")).toHaveCount(n);
    await expect(page.getByTestId("district-caveat")).toContainText("2020 census blocks");
  }
  await page.getByRole("button", { name: "Details for Senate District 26" }).click();
  await expect(page.getByTestId("district-places")).toContainText("Madison city");
  // back to municipalities: the switch is live again with the reader's choice
  await page.getByRole("radio", { name: "Cities, villages and towns" }).check();
  for (const i of await page.getByTestId("unknown-switch").locator("input").all()) await expect(i).toBeEnabled();
  await expect(page.locator('input[name="unk-where"][value="like_prohibited"]')).toBeChecked();
});

test("keyboard: unknown-rules switch and district view", async ({ page, isMobile }) => {
  test.skip(isMobile, "keyboard test runs on desktop");
  const b = await bundle(page);
  await page.goto("#/how-sure");
  const first = page.locator('input[name="unk-howsure"][value="like_restricted"]');
  await first.focus();
  await page.keyboard.press("ArrowRight");
  const pro = page.locator('input[name="unk-howsure"][value="like_prohibited"]');
  await expect(pro).toBeChecked();
  await expect(pro).toBeFocused();
  const v = b.unknown.variants.find((x: { id: string }) => x.id === "like_prohibited");
  await expect(page.getByTestId("unk-baseline")).toHaveText(fmt(v.baseline_total));
  await page.goto("#/where");
  const munis = page.locator('input[name="geo"][value="munis"]');
  await munis.focus();
  await page.keyboard.press("ArrowRight");
  await expect(page.locator('input[name="geo"][value="assembly"]')).toBeChecked();
  await expect(page.locator('input[name="geo"][value="assembly"]')).toBeFocused();
  for (const i of await page.getByTestId("unknown-switch").locator("input").all()) await expect(i).toBeDisabled();
  await page.locator('button[data-sel="asm:79"]').focus();
  await page.keyboard.press("Enter");
  await expect(page.locator("#detail-h")).toHaveText("Assembly District 79");
});

test("landing screen labels general production apart from ADU forecasts", async ({ page }) => {
  const b = await bundle(page);
  await page.goto("#/today");
  await expect(page.getByTestId("production-rate")).toContainText("9.0");
  await expect(page.getByTestId("production-rate")).toContainText("per 1,000 housing units");
  await expect(page.locator("#t-vac")).toContainText("including seasonal");
  await expect(page.locator("main")).toContainText("five-year average");
  await expect(page.locator("#adu-sum")).toContainText("ADU forecasts");
  await page.getByText("Show the data").nth(1).click();
  await expect(page.getByTestId("bps-table")).toContainText("census_bps_state");
  expect(b.state.production_rate.numerator).toBe(25569);
});
