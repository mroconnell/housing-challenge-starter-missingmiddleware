// Transit-oriented density screens (owned by the TOD conductor), opened through preview mode until the reform is
// "ready". Every expected number is read from the TOD bundle, never hard-coded.
import { expect, test, type Page } from "@playwright/test";
import registry from "../src/scenarios/registry.json" with { type: "json" };

const fmt = (v: number) => Math.round(v).toLocaleString("en-US");
const SCREENS = ["today", "compare", "where", "where?level=assembly&s=strong", "where?level=county&view=madison", "how-sure", "why",
  "pilot/milwaukee-connect-1", "pilot/madison-route-a", "pilot/eau-claire", "brief"];
const NAMED_ROLES = ["button", "link", "radio", "checkbox", "slider", "textbox", "searchbox", "combobox", "spinbutton", "img", "table", "region", "radiogroup", "dialog", "navigation"];

async function bundle(page: Page) {
  const root = "scenarios/tod/runs/";
  const { run_id } = await (await page.request.get(`${root}latest.json`)).json();
  const get = async (f: string) => (await page.request.get(`${root}${run_id}/${f}.json`)).json();
  return { run_id, manifest: await get("manifest"), statewide: await get("statewide"), areas: await get("areas"), pilots: await get("pilots") };
}

test("TOD holding page is still shown without preview mode", async ({ page }) => {
  const entry = registry.reforms.find((r) => r.id === "tod")!;
  test.skip(entry.status !== "in_development", "TOD is ready");
  await page.goto("#/tod/today?preview=0");
  await expect(page.getByTestId("in-development")).toBeVisible();
  await expect(page.getByTestId("preview-flag")).toHaveCount(0);
  await expect(page.locator("main")).not.toContainText(/\d{2,}/);
});

test("each TOD screen loads in preview with no console errors", async ({ page }) => {
  const errors: string[] = [];
  page.on("console", (m) => { if (m.type() === "error") errors.push(m.text()); });
  page.on("pageerror", (e) => errors.push(String(e)));
  await page.goto("#/tod/today?preview=1");
  await expect(page.getByTestId("preview-flag")).toBeVisible();
  for (const s of SCREENS) {
    await page.goto(`#/tod/${s}`);
    await expect(page.locator("main h1")).toBeVisible();
  }
  expect(errors).toEqual([]);
});

test("TOD headline numbers equal the bundle", async ({ page }) => {
  const b = await bundle(page);
  const sw = b.statewide;
  const sc = (id: string) => sw.scenarios.find((x: { id: string }) => x.id === id);
  await page.goto("#/tod/today?preview=1");
  await expect(page.getByTestId("run-id")).toHaveText(b.run_id);
  await expect(page.getByTestId("outcome")).toHaveText(b.manifest.outcome.short);
  await expect(page.getByTestId("stock-homes")).toHaveText(fmt(sw.stock_homes));
  await expect(page.getByTestId("baseline-total")).toHaveText(fmt(sw.baseline.total));
  await page.goto("#/tod/compare");
  for (const id of ["little", "typical", "strong"]) await expect(page.getByTestId(`add-${id}`)).toHaveText(fmt(sc(id).additional_total));
  await expect(page.getByTestId("compare-table")).toContainText(fmt(sc("strong").with_law_total));
  await expect(page.getByTestId("timing-caveat")).toContainText(sw.timing_caveat);
  await page.goto("#/tod/where");
  await expect(page.getByTestId("where-table")).toContainText(`statewide total ${fmt(sc("typical").additional_total)}`);
  const top = b.areas.munis[0];
  await expect(page.getByTestId("where-table").locator("tbody tr").first()).toContainText(fmt(top.add.typical));
  for (const m of b.areas.metros) await expect(page.getByTestId("metro-table")).toContainText(fmt(m.add.typical));
  // switching the scenario changes the table and announces it
  await page.getByRole("radio", { name: sc("strong").label }).check();
  await expect(page.getByTestId("where-table")).toContainText(`statewide total ${fmt(sc("strong").additional_total)}`);
  await expect(page.getByTestId("announce")).toContainText(fmt(sc("strong").additional_total));
  // sorting by name puts the alphabetically first place on top
  await page.getByRole("button", { name: /^Place/ }).click();
  await expect(page.locator('th[aria-sort="ascending"]')).toHaveCount(1);
  for (const p of b.pilots) {
    await page.goto(`#/tod/pilot/${p.slug}`);
    if (p.corridor) {
      await expect(page.getByTestId("pilot-corridor-typical")).toHaveText(fmt(p.corridor.add.typical));
      await expect(page.getByTestId("pilot-city-typical")).toHaveText(fmt(p.city_add.typical));
      await expect(page.getByTestId("pilot-baseline")).toHaveText(fmt(p.city_baseline));
      await expect(page.getByTestId("pilot-places")).toContainText(fmt(p.corridor.gain_acres));
      await expect(page.getByTestId("pilot-method")).toHaveText(p.method);
    } else {
      await expect(page.getByTestId("pilot-homes-near")).toHaveText(fmt(p.city_homes_near));
      await expect(page.getByTestId("pilot-eau-claire-add")).toHaveText(fmt(p.city_add.typical));
      await expect(page.getByTestId("pilot-reason")).toContainText(p.reason);
    }
  }
  await page.goto("#/tod/brief");
  await expect(page.getByTestId("brief")).toContainText(fmt(sc("typical").additional_total));
  await expect(page.getByTestId("brief")).toContainText(b.run_id);
});

test("TOD styles leave the ADU Where sort headers unchanged", async ({ page }) => {
  // the TOD stylesheet is bundled with every screen; it must not restyle ADU's sort buttons
  await page.goto("#/where");
  const btn = page.locator("th[aria-sort] button.sort").first();
  await expect(btn).toBeVisible();
  const st = await btn.evaluate((e) => { const s = getComputedStyle(e); return { pad: s.paddingTop, display: s.display, width: e.getBoundingClientRect().width, th: e.parentElement!.getBoundingClientRect().width }; });
  expect(st.pad).toBe("8px");
  expect(st.display).toBe("block");
  expect(Math.abs(st.width - st.th)).toBeLessThan(20);
});

test("an unknown TOD pilot shows a not-found message", async ({ page }) => {
  await page.goto("#/tod/pilot/no-such-place?preview=1");
  await expect(page.getByTestId("pilot-not-found")).toBeVisible();
  await expect(page.locator("main h1")).toHaveText("Pilot example not found");
});

for (const s of SCREENS) {
  test(`TOD a11y structure: ${s}`, async ({ page }) => {
    await page.goto(`#/tod/${s.includes("?") ? `${s}&preview=1` : `${s}?preview=1`}`);
    await expect(page.locator("h1").first()).toBeVisible();
    await page.evaluate(() => document.querySelectorAll("details").forEach((d) => { d.open = true; }));
    const dom = await page.evaluate(() => {
      const hs = [...document.querySelectorAll("h1,h2,h3,h4,h5,h6")].map((h) => Number(h.tagName[1]));
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
        positiveTabindex: [...document.querySelectorAll("[tabindex]")].filter((e) => Number(e.getAttribute("tabindex")) > 0).length,
        fieldsetNoLegend: [...document.querySelectorAll("fieldset")].filter((f) => !f.querySelector("legend")?.textContent?.trim()).length,
        svgNoName: [...document.querySelectorAll('main svg[role="img"]')].filter((e) => !e.getAttribute("aria-labelledby") && !e.getAttribute("aria-label")).length,
        lang: document.documentElement.lang,
      };
    });
    expect(dom.h1, "exactly one h1").toBe(1);
    expect(dom.firstHeading, "the first heading is the h1").toBe(1);
    expect(dom.skips, "no skipped heading levels").toEqual([]);
    expect(dom.landmarks).toEqual([1, 1, 1, 1]);
    expect(dom.tablesNoCaption, "every table has a caption").toBe(0);
    expect(dom.thNoScope, "every table header has a scope").toBe(0);
    expect(dom.dupIds, "ids are unique").toEqual([]);
    expect(dom.positiveTabindex).toBe(0);
    expect(dom.fieldsetNoLegend, "every group of radios has a legend").toBe(0);
    expect(dom.svgNoName, "charts and maps are named").toBe(0);
    expect(dom.lang).toBe("en");
    const snap = await page.locator("body").ariaSnapshot();
    const unnamed = snap.split("\n").filter((l) => new RegExp(`^\\s*- (${NAMED_ROLES.join("|")})(:|$| \\[)`).test(l));
    expect(unnamed, "every control, chart, table and region has an accessible name").toEqual([]);
  });
}
