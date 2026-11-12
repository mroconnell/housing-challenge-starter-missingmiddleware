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
const SCREENS = ["summary", "where", "how-sure", "why", "pilot/madison", "pilot/pleasant-prairie", "pilot/sun-prairie", "brief"];

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
  await page.goto("#/wisconsin-today");
  await expect(page.getByTestId("today-baseline")).toHaveText(fmt(b.state.baseline.total));
  await expect(page.getByTestId("today-central")).toHaveCount(0);   // no centre line: the Summary has the range
  await expect(page.getByTestId("sf-homes")).toHaveText(fmt(b.state.homes.value));
  // ordering of the adopted values (the values themselves are checked against reference/adu_model_*.csv in tests/test_ui_bundle.py)
  expect(sc.lower.additional_total).toBeLessThan(sc.central.additional_total);
  expect(sc.central.additional_total).toBeLessThan(sc.upper.additional_total);

  await page.goto("#/how-sure");
  const R = b.state.range90;
  await expect(page.getByTestId("range-card").getByTestId("range-low")).toHaveText(fmt(R.low));
  await expect(page.getByTestId("range-card").getByTestId("range-high")).toHaveText(fmt(R.high));
  await expect(page.getByTestId("table-range-low")).toHaveText(fmt(R.low));
  await expect(page.getByTestId("table-range-high")).toHaveText(fmt(R.high));
  const rows = page.getByTestId("compare-table").locator("tbody tr");
  await expect(rows).toHaveCount(5);
  for (let i = 0; i < 5; i++) {
    await expect(rows.nth(i).locator("td").nth(0)).toHaveText(fmt(b.state.baseline.by_year[i]));
    await expect(rows.nth(i).locator("td").nth(3)).toHaveText(fmt(R.years[i].low));
    await expect(rows.nth(i).locator("td").nth(4)).toHaveText(fmt(R.years[i].high));
  }
});

test("Where shows the 90% range, not the three scenarios; pilots keep their scenario switch", async ({ page }) => {
  const b = await bundle(page);
  await page.goto("#/where");
  await expect(page.locator('input[name="scen-where"]')).toHaveCount(0);
  await expect(page.getByTestId("reconcile")).toContainText(`${fmt(b.state.range90.low)} to ${fmt(b.state.range90.high)}`);
  await page.goto("#/pilot/pleasant-prairie?s=upper");
  const pp = b.pilots.find((p: { slug: string }) => p.slug === "pleasant-prairie");
  await expect(page.getByTestId("pilot-additional")).toHaveText("+" + fmt(sum(pp.add.upper)));
});

test("map table reconciles to the state for each year and geography", async ({ page }) => {
  const b = await bundle(page);
  const cen = b.state.scenarios.find((s: { id: string }) => s.id === "central");
  await page.goto("#/where");
  const rec = page.getByTestId("reconcile");
  await expect(rec).toContainText("Checked:");
  const lo = b.state.range90.low / cen.additional_total, hi = b.state.range90.high / cen.additional_total;
  await expect(rec).toContainText(`${fmt(b.state.range90.low)} to ${fmt(b.state.range90.high)}`);
  const slider = page.locator("#year");
  await slider.focus();
  await page.keyboard.press("ArrowLeft");
  await page.keyboard.press("ArrowLeft");
  await expect(page.locator("#year-out")).toHaveText("2029");
  await expect(rec).toContainText(`${fmt(sum(cen.additional_by_year.slice(0, 3)) * lo)} to ${fmt(sum(cen.additional_by_year.slice(0, 3)) * hi)}`);
  await expect(rec).toContainText("Checked:");
  await page.getByRole("radio", { name: "Cities, villages and towns" }).check();
  await expect(page.getByTestId("reconcile")).toContainText("Checked:");
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
  expect(sum(mad.add.central).toFixed(1)).toBe("372.1");
});

test("keyboard: skip link, tab navigation and scenario radios", async ({ page, isMobile }) => {
  test.skip(isMobile, "keyboard test runs on desktop");
  await page.goto("#/summary");
  await expect(page.locator("h1")).toBeVisible();
  await page.keyboard.press("Tab");
  await expect(page.locator(".skip")).toBeFocused();
  await page.keyboard.press("Enter");
  await expect(page.locator("main")).toBeFocused();
  await expect(page).toHaveURL(/#\/summary/);
  // tab to the "Summary" nav link from another screen and open it with Enter
  await page.goto("#/why");
  await page.reload();   // focus starts at the top of the page
  await expect(page.locator("h1")).toBeVisible();
  const link = page.locator('nav.tabs a[href="#/summary"]');
  for (let i = 0; i < 20 && !(await link.evaluate((el) => el === document.activeElement)); i++) await page.keyboard.press("Tab");
  await expect(link).toBeFocused();
  await page.keyboard.press("Enter");
  await expect(page).toHaveURL(/#\/summary/);
  await expect(page.locator('nav.tabs a[aria-current="page"]')).toHaveText(/Summary/);
  // "Extra homes only" is the default (owner, 2026-11-11 20:42); the arrow key moves to Totals
  const extraOnly = page.getByTestId("toggle-show").getByLabel("Extra homes only");
  await extraOnly.focus();
  await extraOnly.press("ArrowLeft");
  await expect(page.getByTestId("toggle-show").getByLabel("Totals with current law")).toBeChecked();
  await expect(page.getByTestId("toggle-show").getByLabel("Totals with current law")).toBeFocused();
  await expect(page).toHaveURL(/show=totals/);
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
  await expect(page.getByTestId("brief-headline")).toContainText(`${fmt(b.state.range90.low)} to ${fmt(b.state.range90.high)}`);
  await expect(page.getByTestId("brief-headline")).toContainText("90% range");
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
  await expect(page.getByTestId("detail-madison-note")).toContainText("statewide estimate like every other place");
  await page.locator("#q").fill("Middleton city");
  await page.getByRole("button", { name: "Details for Middleton city" }).click();
  await expect(page.getByTestId("detail-madison-note")).toHaveCount(0);
});

test("chart key, tables and brief use the bundle's labels", async ({ page }) => {
  const b = await bundle(page);
  const L = b.state.labels;
  await page.goto("#/summary");
  const legend = page.getByTestId("summary-legend");
  await expect(legend).toContainText("90% range");
  // the Summary chart's own ADU labels (display only, owner 2026-11-11); "typical" is left off the chart
  const own: Record<string, string> = { median8: "Median path of the 8 statewide-law states", slow2: "Like OR & RI (lowest statewide adoption)", like_california: "Like CA (highest statewide adoption)" };
  for (const s of b.state.side_lines.filter((x: { where: string; id: string }) => x.where === "chart" && x.id !== "typical")) await expect(legend).toContainText(own[s.id] ?? s.label);
  await expect(legend).not.toContainText("Typical adoption");
  await page.goto("#/how-sure");
  await expect(page.getByTestId("compare-table")).toContainText(L.baseline);
  await page.goto("#/brief");
  for (const s of b.state.scenarios) await expect(page.getByTestId("brief-table")).toContainText(s.chart_label);
  await expect(page.getByTestId("brief-table")).toContainText(L.reference);
});

test("map defaults and county labels", async ({ page }) => {
  await page.goto("#/where");
  await expect(page.locator('input[name="geo"][value="counties"]')).toBeChecked();
  await expect(page.locator('input[name="measure"][value="count"]')).toBeChecked();
  await expect(page.locator('input[name="layer"][value="additional"]')).toBeChecked();
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
  await expect(page.getByTestId("baseline-only-table")).toContainText("+310");
});

test("Where choice is kept in the URL and the current tab is in view", async ({ page }) => {
  await page.goto("#/where");
  await page.getByTestId("spread-switch").getByLabel("Causal forest pattern").check();
  await expect(page).toHaveURL(/w=forest/);
  await page.goto("#/brief");
  const tab = page.locator('nav.tabs a[aria-current="page"]');
  await expect(tab).toBeInViewport();
});

// ---- Gate 5 -------------------------------------------------------------------------------
test("unknown-rules switch shows each precomputed run", async ({ page }) => {
  const b = await bundle(page);
  await page.goto("#/how-sure");
  // AQ-066 values (AQ-065: 73.9%, 4.9%, 21.2%; AQ-061: 73.6%, 5.2%, 21.2%)
  await expect(page.getByTestId("trace-summary")).toContainText("72.1%");
  await expect(page.getByTestId("trace-summary")).toContainText("7.3%");
  await expect(page.getByTestId("trace-summary")).toContainText("20.6%");
  for (const v of b.unknown.variants) {
    await page.locator(`input[name="unk-howsure"][value="${v.id}"]`).check();
    await expect(page.getByTestId("unk-baseline")).toHaveText(fmt(v.baseline_total));
    const lo = b.state.range90.low / b.unknown.variants.find((x: { adopted: boolean }) => x.adopted).additional_total.central;
    const hi = b.state.range90.high / b.unknown.variants.find((x: { adopted: boolean }) => x.adopted).additional_total.central;
    await expect(page.getByTestId("unk-additional")).toHaveText(`${fmt(v.additional_total.central * lo)} to ${fmt(v.additional_total.central * hi)}`);
    await expect(page.getByTestId("unk-total")).toHaveText(`${fmt(v.baseline_total + v.additional_total.central * lo)} to ${fmt(v.baseline_total + v.additional_total.central * hi)}`);
  }
  // the choice carries to the Where map, where counties reconcile to that run's statewide figures
  await expect(page).toHaveURL(/u=like_benchmark/);
  await page.goto("#/where?u=like_benchmark");
  const ben = b.unknown.variants.find((v: { id: string }) => v.id === "like_benchmark");
  await expect(page.getByTestId("reconcile")).toContainText("Checked:");
  const cen0 = b.state.scenarios.find((s: { id: string }) => s.id === "central");
  await expect(page.getByTestId("reconcile")).toContainText(fmt(ben.additional_by_year.central.reduce((a: number, x: number) => a + x, 0) * b.state.range90.low / cen0.additional_total));
  await expect(page.getByTestId("reconcile")).toContainText(fmt(ben.baseline_by_year.reduce((a: number, x: number) => a + x, 0)));
});

test("districts follow the unknown-rules assumption and reconcile to the state", async ({ page }) => {
  const b = await bundle(page);
  const D = await (await page.request.get(`runs/${b.run_id}/districts.json`)).json();
  const sum = (xs: number[]) => xs.reduce((a, x) => a + x, 0);
  await page.goto("#/where?u=like_prohibited");
  for (const [name, n, lv] of [["Assembly districts", 99, "assembly"], ["Senate districts", 33, "senate"]] as const) {
    await page.getByRole("radio", { name }).check();
    const sw = page.getByTestId("unknown-switch");
    for (const i of await sw.locator("input").all()) await expect(i).toBeEnabled();
    await expect(sw.locator('input[value="like_prohibited"]')).toBeChecked();
    await expect(page.locator("main")).not.toContainText("adopted assumption only");
    const v = b.unknown.variants.find((x: { id: string }) => x.id === "like_prohibited");
    const cen0 = b.state.scenarios.find((s: { id: string }) => s.id === "central");
    const rec = page.getByTestId("reconcile");
    await expect(rec).toContainText("Checked:");
    await expect(rec).toContainText(`${n} ${name}`);
    await expect(rec).toContainText("not allocated to a district");
    const stAdd = sum(v.additional_by_year.central);
    await expect(rec).toContainText(`${fmt(stAdd * b.state.range90.low / cen0.additional_total)} to ${fmt(stAdd * b.state.range90.high / cen0.additional_total)}`);
    await expect(page.getByTestId("unallocated-row")).toContainText("Not allocated to a district");
    await expect(page.getByTestId("where-table").locator("tbody tr")).toHaveCount(n);
    await expect(page.getByTestId("district-caveat")).toContainText("2020 census blocks");
    expect(Object.keys(D.levels[lv].by_unknown).sort()).toEqual(["like_benchmark", "like_prohibited", "like_restricted"]);
  }
  // each assumption shows that district's own figures and 90% range from by_unknown
  const id = "sen:26";
  for (const u of ["like_restricted", "like_prohibited", "like_benchmark"]) {
    await page.locator(`input[name="unk-where"][value="${u}"]`).check();
    await page.getByRole("button", { name: "Details for Senate District 26" }).click();
    const r = D.levels.senate.by_unknown[u][id].range90;
    await expect(page.getByTestId("detail-range90")).toHaveText(`${fmt(r.low)} to ${fmt(r.high)} permits`);
  }
  const lo = (u: string) => D.levels.senate.by_unknown[u][id].range90.low;
  expect(new Set(["like_restricted", "like_prohibited", "like_benchmark"].map((u) => Math.round(lo(u)))).size).toBe(3);
  await expect(page.getByTestId("district-places")).toContainText("Madison city");
  // back to municipalities: the reader's choice is kept
  await page.getByRole("radio", { name: "Cities, villages and towns" }).check();
  await expect(page.locator('input[name="unk-where"][value="like_benchmark"]')).toBeChecked();
});

test("causal forest view: same statewide range, counties match the bundle", async ({ page }) => {
  const b = await bundle(page);
  const forest = await (await page.request.get(`runs/${b.run_id}/where_forest.json`)).json();
  const cen = b.state.scenarios.find((s: { id: string }) => s.id === "central");
  await page.goto("#/where");
  const sw = page.getByTestId("spread-switch");
  await expect(sw.locator('input[value="model"]')).toBeChecked();
  await expect(page.getByTestId("forest-note")).toHaveCount(0);
  await sw.getByLabel("Causal forest pattern").check();
  await expect(page).toHaveURL(/w=forest/);
  await expect(page.getByTestId("forest-note")).toHaveText(forest.note);
  // the county whose central addition the forest moves most: its table value and details equal the bundle
  const county = b.areas.counties
    .map((c: { id: string; name: string; add: Record<string, number[]> }) => ({ ...c, d: forest.counties[c.id].total - sum(c.add.central) }))
    .sort((x: { d: number }, y: { d: number }) => Math.abs(y.d) - Math.abs(x.d))[0];
  const ft = forest.counties[county.id].total;
  const lo = b.state.range90.low / cen.additional_total, hi = b.state.range90.high / cen.additional_total;
  const row = page.getByTestId("where-table").locator("tbody tr").filter({ has: page.locator(`button[data-sel="${county.id}"]`) });
  await expect(row.locator("td").nth(2)).toHaveText(`${fmt(ft * lo)} to ${fmt(ft * hi)}`);
  await page.locator(`button[data-sel="${county.id}"]`).click();
  await expect(page.getByTestId("detail-forest-range")).toHaveText(`${fmt(ft * lo)} to ${fmt(ft * hi)} permits`);
  await expect(page.getByTestId("detail-model-range")).toHaveText(`${fmt(sum(county.add.central) * lo)} to ${fmt(sum(county.add.central) * hi)} permits`);
  // the statewide range does not change, and the table still reconciles
  const rec = page.getByTestId("reconcile");
  await expect(rec).toContainText("Checked:");
  await expect(rec).toContainText(`${fmt(b.state.range90.low)} to ${fmt(b.state.range90.high)}`);
  await expect(rec).toContainText("causal forest pattern");
  for (const [name] of [["Cities, villages and towns"], ["Assembly districts"], ["Senate districts"]] as const) {
    await page.getByRole("radio", { name }).check();
    await expect(page.getByTestId("reconcile")).toContainText("Checked:");
    await expect(page.getByTestId("reconcile")).toContainText(`${fmt(b.state.range90.low)} to ${fmt(b.state.range90.high)}`);
    await expect(page.getByTestId("reconcile")).toContainText("causal forest pattern");
  }
  // a non-adopted unknown-rules assumption turns it off
  await page.goto("#/where?w=forest&u=like_prohibited");
  await page.getByRole("radio", { name: "Counties", exact: true }).check();
  for (const i of await sw.locator("input").all()) await expect(i).toBeDisabled();
  await expect(page.getByTestId("forest-note")).toContainText("adopted assumption");
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
  // districts follow the assumption now (owner, 2026-11-11), so the switch stays usable
  for (const i of await page.getByTestId("unknown-switch").locator("input").all()) await expect(i).toBeEnabled();
  await page.locator('button[data-sel="asm:79"]').focus();
  await page.keyboard.press("Enter");
  await expect(page.locator("#detail-h")).toHaveText("Assembly District 79");
});

test("Wisconsin today labels general production apart from ADU permits", async ({ page }) => {
  const b = await bundle(page);
  await page.goto("#/wisconsin-today");
  await expect(page.getByTestId("production-rate")).toContainText("9.0");
  await expect(page.getByTestId("production-rate")).toContainText("per 1,000 housing units");
  await expect(page.locator("#t-vac")).toContainText("including seasonal");
  await expect(page.locator("main")).toContainText("five-year average");
  await expect(page.getByTestId("wt-section-adu")).toContainText("ADU permits expected under current law");
  await page.getByTestId("wt-section-all").getByText("Show the data").nth(1).click();
  await expect(page.getByTestId("bps-table")).toContainText("census_bps_state");
  expect(b.state.production_rate.numerator).toBe(25569);
});

test("How sure's Details explain why types of place differ, with the numbers one click away", async ({ page }) => {
  const { run_id } = await (await page.request.get("runs/latest.json")).json();
  const state = await (await page.request.get(`runs/${run_id}/state.json`)).json();
  const c = Object.fromEntries(state.contexts.map((x: { id: string }) => [x.id, x]));
  const d = Object.fromEntries(state.context_why.drivers.map((x: { term: string }) => [x.term, x]));
  await page.goto("#/how-sure");
  const box = page.getByTestId("why-differ");
  await expect(box).toContainText("Why places differ.");
  // places differ by home value only (the allocation fit); income and size set only the statewide rate (AQ-061)
  await expect(box).toContainText(`about a ${Math.round((d.alloc_value_dev.ratio_10pct - 1) * 100)}% higher`);
  await expect(box).toContainText("by home value alone");
  for (const g of ["urban", "suburban", "small_community", "rural"]) await expect(box).toContainText(c[g].additional_rate_central.toFixed(2));
  await expect(box).toContainText("acreage");
  const tbl = page.getByTestId("why-differ-table");
  await expect(tbl).toBeHidden();
  await page.getByText("Why places differ: the numbers").click();
  await expect(tbl.locator("tbody tr")).toHaveCount(5);
});

test("ADU Summary chart toggles between totals and extra homes only", async ({ page }) => {
  const b = await bundle(page);
  const R = b.state.range90;
  await page.goto("#/summary");
  const toggle = page.getByTestId("toggle-show");
  const title = page.locator("#sum-chart svg title"), desc = page.locator("#sum-chart svg desc");
  const legend = page.getByTestId("summary-legend");
  // "Extra homes only" is the default (owner, 2026-11-11 20:42)
  await expect(toggle.getByLabel("Extra homes only")).toBeChecked();
  await expect(title).toContainText("Extra ADU permits from the law");
  await toggle.getByLabel("Totals with current law").check();
  await expect(page).toHaveURL(/show=totals/);
  await expect(title).toContainText("ADU permits each year");
  await expect(legend).toContainText("Current law (ADU permits without statewide reform)");
  await expect(page.locator('#sum-chart svg path[data-band="range90"]')).toHaveCount(1);
  await expect(page.locator('#sum-chart svg path[data-band="current-law"]')).toHaveCount(1);
  await toggle.getByLabel("Extra homes only").check();
  await expect(page.getByTestId("announce")).toContainText("only the extra homes");
  await expect(title).toContainText("Extra ADU permits from the law");
  await expect(desc).toContainText(`${fmt(R.low)} to ${fmt(R.high)}`);
  await expect(legend).toContainText("the zero line");
  await expect(page.locator('#sum-chart svg path[data-band="range90"]')).toHaveCount(1);
  await expect(page.locator('#sum-chart svg path[data-band="current-law"]')).toHaveCount(0);
  // keyboard: arrow key moves back to Totals
  await page.getByTestId("toggle-show").getByLabel("Extra homes only").press("ArrowLeft");
  await expect(page.getByTestId("toggle-show").getByLabel("Totals with current law")).toBeChecked();
  await expect(title).toContainText("ADU permits each year");
  // pilot chart has its own toggle
  await page.goto("#/pilot/madison");
  const pt = page.getByTestId("adu-pilot-chart-mode");
  await pt.getByLabel("Extra homes only").check();
  await expect(page.locator("#pilot-chart svg title")).toContainText("extra second-home permits from the law");
});

test("ADU How sure and Where carry the 90% range, its coverage note and the How-sure-only lines", async ({ page }) => {
  const b = await bundle(page);
  const R = b.state.range90;
  await page.goto("#/how-sure");
  const card = page.getByTestId("range-card");
  await expect(card.getByTestId("range-low")).toHaveText(fmt(R.low));
  await expect(card.getByTestId("range-high")).toHaveText(fmt(R.high));
  await expect(card.getByTestId("range-coverage")).toContainText(R.coverage);
  const hs = b.state.side_lines.filter((s: { where: string }) => s.where === "howsure");
  await expect(page.getByTestId("howsure-side-lines").locator("li")).toHaveCount(hs.length);
  for (const s of hs) await expect(page.getByTestId("howsure-side-lines")).toContainText(s.label);
  await expect(page.getByTestId("howsure-side-lines")).toContainText("7,517 to 13,318");
  await page.goto("#/where");
  await expect(page.getByTestId("where-range-note")).toContainText(`${fmt(R.low)} to ${fmt(R.high)}`);
});

test("Where map key: its title states what is mapped and the unit, and follows Show and Measure (owner 2026-11-11)", async ({ page }) => {
  await page.goto("#/where");
  const t = page.getByTestId("map-legend-title");
  await expect(t).toHaveText("ADU permits added by the law, 2027–2031, low end of the 90% range (per area)");
  await page.getByRole("radio", { name: "Per 1,000 homes per year" }).check();
  await expect(t).toHaveText("ADU permits added by the law, 2027–2031, low end of the 90% range, per 1,000 single-family homes per year");
  await page.getByRole("radio", { name: "Permits", exact: true }).check();
  await expect(t).toContainText("(per area)");
  await page.getByRole("radio", { name: "Baseline growth" }).check();
  await expect(t).toHaveText("ADU permits without statewide reform (baseline growth), 2027–2031 (per area)");
  await page.getByRole("radio", { name: "Existing homes" }).check();
  await expect(t).toHaveText("Existing single-family homes (per area)");
  // classes below 1 permit keep one decimal; the title carries the unit
  await page.getByRole("radio", { name: "Additional from the law" }).check();
  await page.getByRole("radio", { name: "Cities, villages and towns" }).check();
  await expect(page.locator(".map-legend li").first()).toHaveText(/^under \d/);
});
