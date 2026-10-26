// Accessibility checks that can be automated (docs/gate5/ACCESSIBILITY.md): one h1 per screen and no skipped
// heading levels, landmarks, an accessible name on every control, captions and scoped headers on every table,
// named charts and map, unique ids, and a polite live-region announcement when a switch changes the numbers.
// They do not replace the manual screen-reader pass in ACCESSIBILITY.md.
import { expect, test, type Page } from "@playwright/test";

const SCREENS: [string, string?, ((p: Page) => Promise<void>)?][] = [
  ["today"], ["compare"], ["where"],
  ["where", "municipalities", async (p) => { await p.getByRole("radio", { name: "Cities, villages and towns" }).check(); }],
  ["where", "Assembly districts", async (p) => { await p.getByRole("radio", { name: "Assembly districts" }).check(); }],
  ["how-sure"], ["why"], ["pilot/madison"], ["pilot/pleasant-prairie"], ["pilot/sun-prairie"], ["brief"],
];
// roles that must always carry a name (a <details> is a "group" whose name is its summary text, so it is not listed)
const NAMED_ROLES = ["button", "link", "radio", "checkbox", "slider", "textbox", "searchbox", "combobox", "spinbutton", "img", "table", "region", "radiogroup", "dialog", "navigation"];

async function open(page: Page, path: string, act?: (p: Page) => Promise<void>) {
  await page.goto(`#/${path}`);
  await expect(page.locator("h1").first()).toBeVisible();
  if (act) { await act(page); await page.waitForTimeout(300); }
  // open every disclosure so its content is checked too
  await page.evaluate(() => document.querySelectorAll("details").forEach((d) => { d.open = true; }));
}

for (const [path, view, act] of SCREENS) {
  const name = `${path}${view ? ` (${view})` : ""}`;
  test(`a11y structure: ${name}`, async ({ page }) => {
    await open(page, path, act);
    const dom = await page.evaluate(() => {
      const vis = (e: Element) => !e.closest("dialog:not([open])");
      const hs = [...document.querySelectorAll("h1,h2,h3,h4,h5,h6")].filter(vis).map((h) => Number(h.tagName[1]));
      const skips: string[] = [];
      hs.forEach((l, i) => { if (i && l > hs[i - 1] + 1) skips.push(`h${hs[i - 1]} -> h${l}`); });
      const ids: Record<string, number> = {};
      document.querySelectorAll("[id]").forEach((e) => { ids[e.id] = (ids[e.id] ?? 0) + 1; });
      return {
        h1: hs.filter((l) => l === 1).length, firstHeading: hs[0], skips,
        landmarks: [document.querySelectorAll("header.site-head").length, document.querySelectorAll("main").length, document.querySelectorAll("footer.site-foot").length, document.querySelectorAll('nav[aria-label="Screens"]').length],
        tablesNoCaption: [...document.querySelectorAll("table")].filter((t) => !t.querySelector("caption")?.textContent?.trim()).length,
        thNoScope: [...document.querySelectorAll("table th")].filter((th) => !th.getAttribute("scope")).length,
        dupIds: Object.entries(ids).filter(([, n]) => n > 1).map(([k]) => k),
        imgNoAlt: [...document.querySelectorAll("img:not([alt])")].length,
        positiveTabindex: [...document.querySelectorAll("[tabindex]")].filter((e) => Number(e.getAttribute("tabindex")) > 0).length,
        fieldsetNoLegend: [...document.querySelectorAll("fieldset")].filter((f) => !f.querySelector("legend")?.textContent?.trim()).length,
        lang: document.documentElement.lang,
        live: !!document.querySelector('#announce[role="status"][aria-live="polite"]'),
      };
    });
    expect(dom.h1, "exactly one h1").toBe(1);
    expect(dom.firstHeading, "the first heading is the h1").toBe(1);
    expect(dom.skips, "no skipped heading levels").toEqual([]);
    expect(dom.landmarks, "banner, main, footer and the screens navigation").toEqual([1, 1, 1, 1]);
    expect(dom.tablesNoCaption, "every table has a caption").toBe(0);
    expect(dom.thNoScope, "every table header has a scope").toBe(0);
    expect(dom.dupIds, "ids are unique").toEqual([]);
    expect(dom.imgNoAlt).toBe(0);
    expect(dom.positiveTabindex, "no positive tabindex (focus follows the page order)").toBe(0);
    expect(dom.fieldsetNoLegend, "every group of radios has a legend").toBe(0);
    expect(dom.lang).toBe("en");
    expect(dom.live, "a polite live region exists for announcements").toBe(true);

    // accessible names, from the browser's accessibility tree
    const snap = await page.locator("body").ariaSnapshot();
    const unnamed = snap.split("\n").filter((l) => new RegExp(`^\\s*- (${NAMED_ROLES.join("|")})(:|$| \\[)`).test(l));
    expect(unnamed, "every control, chart, table and region has an accessible name").toEqual([]);
  });
}

test("a11y: switch and slider names are short and describe the choice", async ({ page }) => {
  await page.goto("#/compare");
  for (const n of ["Lower", "Central", "Strong adoption"]) await expect(page.getByRole("radio", { name: n, exact: true })).toHaveCount(1);
  await expect(page.getByRole("radio", { name: "Central", exact: true })).toHaveAccessibleDescription(/additional permits over 2027–2031/);
  await expect(page.getByRole("group", { name: "Scenario" })).toBeVisible();
  await expect(page.getByRole("group", { name: "Units" })).toBeVisible();
  await page.goto("#/where");
  for (const g of ["Areas", "Show", "Measure", "Scenario"]) await expect(page.getByRole("group", { name: g, exact: true })).toBeVisible();
  await expect(page.getByRole("group", { name: /Places whose local ADU rules we have not coded/ })).toBeVisible();
  await expect(page.getByRole("slider", { name: /Through year/ })).toHaveAttribute("aria-valuetext", "through 2031");
  await expect(page.locator("#map canvas")).toHaveAttribute("aria-label", /Map of counties.*table below/);
  await expect(page.getByRole("searchbox", { name: "Search" })).toBeVisible();
});

test("a11y: charts and the map have text equivalents", async ({ page }) => {
  for (const s of ["today", "compare", "how-sure", "why", "pilot/madison"]) {
    await page.goto(`#/${s}`);
    const imgs = page.getByRole("img");
    await expect(imgs.first()).toBeVisible();
    for (const n of await imgs.all()) expect((await n.getAttribute("aria-label")) ?? (await n.getAttribute("aria-labelledby")), `${s}: chart is named`).toBeTruthy();
    expect(await page.locator("main table").count(), `${s}: charts are paired with tables`).toBeGreaterThan(0);
  }
  await page.goto("#/where");
  await expect(page.getByTestId("where-table")).toBeVisible();
  await expect(page.locator("#map")).toHaveAttribute("aria-label", /table below has the same values/);
});

test("a11y: switches announce the new numbers in a polite live region", async ({ page }) => {
  const fmt = (v: number) => Math.round(v).toLocaleString("en-US");
  const { run_id } = await (await page.request.get("runs/latest.json")).json();
  const state = await (await page.request.get(`runs/${run_id}/state.json`)).json();
  const unk = await (await page.request.get(`runs/${run_id}/unknown_rules.json`)).json();
  const up = state.scenarios.find((s: { id: string }) => s.id === "upper");
  const live = page.getByTestId("announce");
  await page.goto("#/compare");
  await page.getByRole("radio", { name: "Strong adoption", exact: true }).check();
  await expect(live).toContainText(`Strong adoption scenario: ${fmt(up.additional_total)} permits added`);
  await expect(page.getByRole("radio", { name: "Strong adoption", exact: true })).toBeFocused();
  await page.getByRole("radio", { name: "Per 1,000 single-family homes" }).check();
  await expect(live).toContainText("per 1,000 single-family homes per year");
  await page.goto("#/how-sure");
  const pr = unk.variants.find((v: { id: string }) => v.id === "like_prohibited");
  await page.getByRole("radio", { name: "Like places that prohibit ADUs" }).check();
  await expect(live).toContainText(`added by the law ${fmt(pr.additional_total.central)}`);
  await page.goto("#/where");
  await page.getByRole("radio", { name: "Senate districts" }).check();
  await expect(live).toContainText("Map and table: Senate districts");
  await page.getByRole("radio", { name: "Existing homes" }).check();
  await expect(live).toContainText("Existing single-family homes");
});

test("a11y: the brief's district tables are captioned and reconcile", async ({ page }) => {
  await page.goto("#/brief");
  await expect(page.getByTestId("brief-assembly-table")).toHaveCount(3);
  await expect(page.getByTestId("brief-senate-table")).toHaveCount(3);
  await expect(page.getByTestId("brief-assembly-table").locator("tbody tr")).toHaveCount(99);
  await expect(page.getByTestId("brief-senate-table").locator("tbody tr")).toHaveCount(33);
  await expect(page.getByRole("table", { name: "Assembly districts 1–33" })).toBeVisible();
  await expect(page.getByRole("columnheader", { name: "Added permits per 1,000 single-family homes per year" }).first()).toBeAttached();
  await expect(page.getByTestId("brief-district-reconcile")).toContainText("✓");
});
