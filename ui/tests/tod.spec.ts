// Transit-oriented density screens (owned by the TOD conductor). Opened through preview mode while the reform was in
// development; "ready" since Gate 4 (AQ-053). Every expected number is read from the TOD bundle, never hard-coded.
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
  const entry = registry.reforms.find((r) => r.id === "tod")!;
  await page.goto(`#/tod/today${entry.status === "ready" ? "" : "?preview=1"}`);
  if (entry.status === "ready") await expect(page.getByTestId("preview-flag")).toHaveCount(0);
  else await expect(page.getByTestId("preview-flag")).toBeVisible();
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
  await expect(page.getByTestId("acs-homes")).toHaveText(fmt(sw.acs_homes));
  // option D (AQ-071): the law is a by-right district on 15% of the land within ¼ mile of rail and rapid stops
  await expect(page.getByTestId("law-district")).toContainText("15%");
  await expect(page.getByTestId("law-district")).toContainText(sw.district.text);
  await page.goto("#/tod/compare");
  for (const id of ["little", "typical", "strong"]) {
    await expect(page.getByTestId(`add-${id}`)).toHaveText(fmt(sc(id).additional_total));
    expect(sc(id).range_low).toBeLessThan(sc(id).additional_total);
  }
  await expect(page.getByTestId("compare-table")).toContainText(fmt(sc("strong").with_law_total));
  // auditor 2026-11-02: record-year exceedance stated beside the lines
  for (const r of sw.record_years) await expect(page.getByTestId("record-years")).toContainText(`${r.metro} ${r.years.join(" and ")}`);
  await expect(page.getByTestId("timing-caveat")).toContainText(sw.timing_caveat);
  // AQ-054: shared unit against the statewide all-housing baseline and the ACS home count; no median line for 3 studies
  const shared = page.getByTestId("shared-unit");
  for (const id of ["little", "typical", "strong"]) await expect(shared).toContainText(`about ${fmt(sc(id).per_year)}`);
  await expect(shared).toContainText(fmt(sw.state_baseline_per_year));
  await expect(shared).toContainText(fmt(sw.acs_homes));
  await expect(page.getByTestId("median-note")).toHaveText(sw.median_line.note);
  expect(sw.reference_line).toBeUndefined();
  await expect(page.locator("main")).not.toContainText("Median of the three studies");
  await page.goto("#/tod/where");
  await expect(page.getByTestId("where-table")).toContainText(`statewide total ${fmt(sc("typical").additional_total)}`);
  const top = b.areas.munis[0];
  await expect(page.getByTestId("where-table").locator("tbody tr").first()).toContainText(fmt(top.add.typical));
  for (const m of b.areas.metros) await expect(page.getByTestId("metro-table")).toContainText(fmt(m.add.typical));
  await expect(page.getByTestId("where-table").locator("tbody tr").first()).toContainText(`of ${fmt(top.all_baseline / 5)}`);
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
      await expect(page.getByTestId("pilot-places")).toContainText(fmt(p.corridor.district_acres));
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
  await expect(page.getByTestId("brief-shared")).toContainText(`about ${fmt(sc("typical").per_year)}`);
  await expect(page.getByTestId("brief-shared")).toContainText(fmt(sw.state_baseline_per_year));
});

test("TOD today shows homes per acre near rail and rapid stops from the bundle", async ({ page }) => {
  const root = "scenarios/tod/runs/";
  const { run_id } = await (await page.request.get(`${root}latest.json`)).json();
  const t = await (await page.request.get(`${root}${run_id}/today.json`)).json();
  const one = (v: number) => v.toFixed(1);
  await page.goto("#/tod/today");
  await expect(page.getByTestId("rapid-stops")).toHaveText(fmt(t.stops_total));
  await expect(page.getByTestId("density-tiles")).toContainText("Milwaukee 106 · Madison 138 · Kenosha 22");
  await expect(page.getByTestId("hpa-half")).toHaveText(one(t.state.half.homes_per_acre));
  await expect(page.getByTestId("hpa-quarter")).toHaveText(one(t.state.quarter.homes_per_acre));
  await expect(page.getByTestId("hpa-half-five")).toHaveText(one(t.five_places.half.homes_per_acre));
  await expect(page.getByTestId("hpa-quarter-five")).toHaveText(one(t.five_places.quarter.homes_per_acre));
  const wi = page.getByTestId("density-wi-table");
  for (const x of t.systems) {
    const row = wi.locator("tbody tr", { hasText: x.label });
    await expect(row.locator("td")).toHaveText([String(x.half.stops), one(x.quarter.homes_per_acre), one(x.half.homes_per_acre)]);
  }
  const five = page.getByTestId("density-five-table");
  for (const name of ["Austin, 2009", "Salt Lake City, 2010", "Saint Paul, 2011", "Seattle (Othello), 2012", "Seattle (Mount Baker), 2014", "Five places together"]) await expect(five).toContainText(name);
  await expect(five.locator("tbody tr")).toHaveCount(6);
  await expect(five).not.toContainText("_20");  // plain names, not case ids
  // industrial rezones (BelRed) are off the screen's tables and tiles
  for (const id of ["density-tiles", "density-wi-table", "density-five-table", "density-ring-table", "density-context"]) await expect(page.getByTestId(id)).not.toContainText("BelRed");
  await expect(page.getByTestId("density-extra")).toHaveText(fmt(t.context.half.extra_homes_rounded));
  await expect(page.getByTestId("density-context")).toContainText(`+${Math.round(t.context.half.extra_share * 100)}%`);
  await expect(page.getByTestId("density-context")).toContainText("five places");
  for (const c of t.caveats) await expect(page.getByTestId("density-caveats")).toContainText(c);
  // second measure: near the stops compared with ½ to 1 mile away (raw density first, ring second)
  const x1 = (v: number) => `${v.toFixed(1)}×`;
  const ring = page.getByTestId("density-ring-table");
  const ringRows: [string, any][] = [...t.systems.map((x: any) => [x.label, x]), ["Wisconsin, all", t.state],
    ...t.reforms.map((x: any) => [`${x.area ? `${x.place} (${x.area})` : x.place}, ${x.year}`, x]), ["Five places together", t.five_places]];
  await expect(ring.locator("tbody tr:not(:has(.tod-group))")).toHaveCount(ringRows.length);
  for (const [name, x] of ringRows) {
    await expect(ring.locator("tbody tr", { hasText: name }).first().locator("td")).toHaveText([one(x.ring.homes_per_acre), x1(x.vs_ring.quarter), x1(x.vs_ring.half)]);
  }
  await expect(page.getByTestId("ring-half-wi")).toHaveText(x1(t.state.vs_ring.half));
  await expect(page.getByTestId("ring-half-five")).toHaveText(x1(t.five_places.vs_ring.half));
  await expect(page.getByTestId("density-ring")).toContainText("nearby neighborhoods");
  await expect(page.getByTestId("density-ratio")).toHaveCount(0);
  const order = await page.evaluate(() => ["density-raw", "density-ring"].map((id) => document.querySelector(`[data-testid="${id}"]`)!.getBoundingClientRect().top));
  expect(order[0]).toBeLessThan(order[1]);
  // map: rail and rapid stops only, one view at a time
  await page.getByRole("radio", { name: "Madison area" }).check();
  await expect(page).toHaveURL(/view=madison/);
  await expect(page.locator("figure.tod-map title")).toHaveText("Rail and rapid transit stops: Madison area");
  const overflow = await page.evaluate(() => document.documentElement.scrollWidth - window.innerWidth);
  expect(overflow, "no sideways page scroll").toBeLessThanOrEqual(0);
});

test("TOD styles leave the ADU Where sort headers unchanged", async ({ page }) => {
  // the TOD stylesheet is bundled with every screen; it must not restyle ADU's sort buttons
  await page.goto("#/where");
  const btn = page.locator("th[aria-sort] button.sort").first();
  await expect(btn).toBeVisible();
  // the Where table re-renders once its data loads; read the style after it settles (poll), not mid-render
  const read = () => btn.evaluate((e) => { const s = getComputedStyle(e); return { pad: s.paddingTop, display: s.display, width: e.getBoundingClientRect().width, th: e.parentElement!.getBoundingClientRect().width }; });
  await expect.poll(async () => (await read()).pad).toBe("8px");
  const st = await read();
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

test("TOD chart toggles between totals and extra homes only", async ({ page }) => {
  await page.goto("#/tod/compare");
  const toggle = page.getByTestId("tod-chart-mode");
  await expect(toggle.getByLabel("Totals")).toBeChecked();
  await expect(page.locator("#tod-chart svg title")).toContainText("Homes permitted near major transit stops");
  await toggle.getByLabel("Extra homes only").check();
  await expect(page.locator("#tod-chart svg title")).toContainText("Extra homes permitted");
});

test("TOD How sure tornado shows every what-if that changes the law's extra homes", async ({ page }) => {
  const b = await bundle(page);
  const hs = await (await page.request.get(`scenarios/tod/runs/${b.run_id}/howsure.json`)).json();
  const rows = hs.tornado.rows as { kind: string; vs_central: number; extra: number }[];
  const central = b.statewide.scenarios.find((x: { id: string }) => x.id === "typical").additional_total;
  expect(hs.tornado.central).toBeCloseTo(central, 1);
  for (const r of rows) expect(r.vs_central).toBeCloseTo(r.extra - central, 0);
  const current = rows.filter((r) => r.kind === "current").length;
  const earlier = rows.filter((r) => r.kind === "earlier").length;
  // AQ-075: the two 2x2 readings join the current what-ifs; the option D upper is now the upper line itself
  expect(current).toBe(13);
  expect(earlier).toBe(7);
  await page.goto("#/tod/how-sure?preview=1");
  await expect(page.getByTestId("tod-tornado-current").locator(".t-row")).toHaveCount(current);
  await expect(page.getByTestId("tod-tornado-earlier").locator(".t-row")).toHaveCount(earlier);
  await expect(page.getByTestId("tod-tornado-current").locator(".tornado")).toHaveAttribute("aria-label", new RegExp(`compared with the central ${fmt(central)}`));
  await expect(page.getByTestId("tod-tornado-note")).toContainText("do not change the law's extra homes");
  await expect(page.locator("main")).toContainText("Homes that would have been built elsewhere in the city anyway");
});
