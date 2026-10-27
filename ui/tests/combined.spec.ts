// TOD and parking together (owned by the TOD conductor; docs/shared/SCENARIO_CONTRACT.md section 9), opened through
// preview mode until the view is "ready". Every expected number is read from the bundles, never hard-coded.
import { expect, test, type Page } from "@playwright/test";
import registry from "../src/scenarios/registry.json" with { type: "json" };

const fmt = (v: number) => Math.round(v).toLocaleString("en-US");
const SCREENS = ["compare", "compare?p=central", "where", "where?level=county&p=lower", "about"];
const NAMED_ROLES = ["button", "link", "radio", "checkbox", "slider", "textbox", "searchbox", "combobox", "spinbutton", "img", "table", "region", "radiogroup", "dialog", "navigation"];

async function get(page: Page, root: string, files: string[]) {
  const { run_id } = await (await page.request.get(`${root}latest.json`)).json();
  const out: Record<string, any> = { run_id };
  for (const f of files) out[f] = await (await page.request.get(`${root}${run_id}/${f}.json`)).json();
  return out;
}
const combined = (page: Page) => get(page, "scenarios/combined/runs/", ["manifest", "statewide", "areas"]);

test("combined holding page is shown without preview mode", async ({ page }) => {
  const entry = registry.reforms.find((r) => r.id === "combined")!;
  test.skip(entry.status !== "in_development", "combined view is ready");
  await page.goto("#/combined/compare?preview=0");
  await expect(page.getByTestId("in-development")).toBeVisible();
  await expect(page.getByTestId("benchmark")).toHaveText(entry.benchmark);
  await expect(page.locator("main")).toContainText(entry.benchmark_note!);
  await expect(page.locator("main")).not.toContainText(/\d{2,}/);
});

test("each combined screen loads in preview with no console errors", async ({ page }) => {
  const errors: string[] = [];
  page.on("console", (m) => { if (m.type() === "error") errors.push(m.text()); });
  page.on("pageerror", (e) => errors.push(String(e)));
  await page.goto("#/combined/compare?preview=1");
  await expect(page.getByTestId("preview-flag")).toBeVisible();
  for (const s of SCREENS) {
    await page.goto(`#/combined/${s}`);
    await expect(page.locator("main h1")).toBeVisible();
  }
  expect(errors).toEqual([]);
});

test("combined numbers equal the bundle, by pairing and rule", async ({ page }) => {
  const b = await combined(page);
  const sw = b.statewide;
  await page.goto("#/combined/compare?preview=1");
  await expect(page.getByTestId("run-id")).toHaveText(b.run_id);
  await expect(page.getByTestId("outcome")).toHaveText(b.manifest.outcome.short);
  for (const x of sw.roles) {
    await page.goto(`#/combined/compare?p=${x.role}`);
    await expect(page.getByTestId("alone-tod")).toHaveText(fmt(x.total.tod));
    await expect(page.getByTestId("alone-parking")).toHaveText(fmt(x.total.parking));
    await expect(page.getByTestId("both-a")).toHaveText(fmt(x.total.both_a));
    await expect(page.getByTestId("both-b")).toHaveText(fmt(x.total.both_b));
    expect(x.total.both_b).toBeLessThanOrEqual(x.total.both_a);
    const yrs = page.getByTestId("combined-years").locator("tbody tr");
    for (let i = 0; i < sw.years.length; i++) {
      const cells = yrs.nth(i).locator("td");
      await expect(cells.nth(2)).toHaveText(fmt(x.by_year.both_a[i]));
      await expect(cells.nth(3)).toHaveText(fmt(x.by_year.both_b[i]));
    }
    await expect(yrs.last()).toContainText(fmt(x.total.both_a));
    await expect(page.getByTestId("combined-roles")).toContainText(fmt(x.total.both_b));
    if (Math.round(x.total.both_a) !== Math.round(x.total.both_b)) await expect(page.getByTestId("overlap")).toContainText(fmt(x.overlap_counted_twice));
  }
  // the double-counting explanation and the unmeasured third rule (no number)
  await expect(page.getByTestId("double-count")).toContainText(sw.double_count);
  await expect(page.getByTestId("rule-c")).toContainText(sw.rule_c);
  await expect(page.getByTestId("rule-c")).not.toContainText(/\d/);
  // switching the pairing re-renders and announces the new totals
  const up = sw.roles.find((r: { role: string }) => r.role === "upper");
  await page.goto("#/combined/compare?p=central");
  await page.getByRole("radio", { name: new RegExp(`^${sw.role_labels.upper}`) }).check();
  await expect(page.getByTestId("both-a")).toHaveText(fmt(up.total.both_a));
  await expect(page.getByTestId("announce")).toContainText(fmt(up.total.both_b));
});

test("combined by-place table matches the bundle and filters", async ({ page }) => {
  const b = await combined(page);
  const up = b.statewide.roles.find((r: { role: string }) => r.role === "upper");
  await page.goto("#/combined/where?p=upper&preview=1");
  const table = page.getByTestId("combined-where");
  await expect(page.getByTestId("where-total-a")).toHaveText(fmt(up.total.both_a));
  await expect(page.getByTestId("where-total-b")).toHaveText(fmt(up.total.both_b));
  const top = b.areas.munis[0];
  const first = table.locator("tbody tr").first();
  await expect(first.locator("th")).toHaveText(top.name);
  await expect(first).toContainText(top.county);
  await expect(first).toContainText(fmt(top.upper[3]));
  await expect(first).toContainText(fmt(top.upper[4]));
  // search filters rows in place
  await page.getByLabel(/Find a place/).fill(top.name);
  await expect(table.locator("tbody tr:visible").first().locator("th")).toHaveText(top.name);
  await expect(page.getByTestId("combined-count")).toContainText(/^\d+ of /);
  // counties
  await page.goto("#/combined/where?p=upper&level=county");
  const c0 = b.areas.counties[0];
  await expect(table.locator("tbody tr").first().locator("th")).toHaveText(c0.name);
  await expect(table.locator("tbody tr").first()).toContainText(fmt(c0.upper[3]));
  // sorting by name puts the alphabetically first county on top
  await page.getByRole("button", { name: /^County/ }).click();
  await expect(page.locator('th[aria-sort="ascending"]')).toHaveCount(1);
});

test("the combined view leaves TOD, parking and ADU numbers unchanged", async ({ page }) => {
  const b = await combined(page);
  const tod = await get(page, "scenarios/tod/runs/", ["statewide"]);
  const park = await get(page, "scenarios/parking/runs/", ["statewide"]);
  expect(b.manifest.sources).toEqual({ tod: tod.run_id, parking: park.run_id });
  const up = b.statewide.roles.find((r: { role: string }) => r.role === "upper");
  const strong = tod.statewide.scenarios.find((x: { id: string }) => x.id === "strong");
  const pUp = park.statewide.scenarios.find((x: { id: string }) => x.id === "upper");
  expect(Math.abs(up.total.tod - strong.additional_total)).toBeLessThan(1);
  expect(Math.abs(up.total.parking - pUp.additional_total)).toBeLessThan(1);
  await page.goto("#/combined/compare?preview=1");
  await page.goto("#/tod/compare");
  await expect(page.getByTestId("add-strong")).toHaveText(fmt(strong.additional_total));
  await page.goto("#/parking/compare");
  await expect(page.getByTestId("add-upper")).toHaveText(fmt(pUp.additional_total));
  // the combined stylesheet must not restyle ADU's sort headers
  await page.goto("#/where");
  const btn = page.locator("th[aria-sort] button.sort").first();
  await expect(btn).toBeVisible();
  const st = await btn.evaluate((e) => { const s = getComputedStyle(e); return { pad: s.paddingTop, display: s.display }; });
  expect(st).toEqual({ pad: "8px", display: "block" });
});

for (const s of SCREENS) {
  test(`combined a11y structure: ${s}`, async ({ page }) => {
    await page.goto(`#/combined/${s.includes("?") ? `${s}&preview=1` : `${s}?preview=1`}`);
    await expect(page.locator("h1").first()).toBeVisible();
    const dom = await page.evaluate(() => {
      const hs = [...document.querySelectorAll("h1,h2,h3,h4,h5,h6")].map((h) => Number(h.tagName[1]));
      const skips: string[] = [];
      hs.forEach((l, i) => { if (i && l > hs[i - 1] + 1) skips.push(`h${hs[i - 1]} -> h${l}`); });
      const ids: Record<string, number> = {};
      document.querySelectorAll("[id]").forEach((e) => { ids[e.id] = (ids[e.id] ?? 0) + 1; });
      return {
        h1: hs.filter((l) => l === 1).length, firstHeading: hs[0], skips,
        tablesNoCaption: [...document.querySelectorAll("table")].filter((t) => !t.querySelector("caption")?.textContent?.trim()).length,
        thNoScope: [...document.querySelectorAll("table th")].filter((th) => !th.getAttribute("scope")).length,
        dupIds: Object.entries(ids).filter(([, n]) => n > 1).map(([k]) => k),
        fieldsetNoLegend: [...document.querySelectorAll("fieldset")].filter((f) => !f.querySelector("legend")?.textContent?.trim()).length,
        svgNoName: [...document.querySelectorAll('main svg[role="img"]')].filter((e) => !e.getAttribute("aria-labelledby") && !e.getAttribute("aria-label")).length,
        inputsNoLabel: [...document.querySelectorAll("main input")].filter((i) => !(i as HTMLInputElement).labels?.length).length,
        lang: document.documentElement.lang,
      };
    });
    expect(dom.h1, "exactly one h1").toBe(1);
    expect(dom.firstHeading).toBe(1);
    expect(dom.skips).toEqual([]);
    expect(dom.tablesNoCaption).toBe(0);
    expect(dom.thNoScope).toBe(0);
    expect(dom.dupIds).toEqual([]);
    expect(dom.fieldsetNoLegend).toBe(0);
    expect(dom.svgNoName).toBe(0);
    expect(dom.inputsNoLabel).toBe(0);
    expect(dom.lang).toBe("en");
    const snap = await page.locator("body").ariaSnapshot();
    const unnamed = snap.split("\n").filter((l) => new RegExp(`^\\s*- (${NAMED_ROLES.join("|")})(:|$| \\[)`).test(l));
    expect(unnamed, "every control, chart, table and region has an accessible name").toEqual([]);
  });
}
