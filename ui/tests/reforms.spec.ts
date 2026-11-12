// The multi-reform shell: the reform picker, prefixed URLs, holding pages for reforms in development, and
// that the ADU screens are unchanged by the shell (same numbers, same URLs, same run id).
import { expect, test } from "@playwright/test";
import registry from "../src/scenarios/registry.json" with { type: "json" };

const fmt = (v: number) => Math.round(v).toLocaleString("en-US");

test("the picker lists every registered reform and marks the current one", async ({ page }) => {
  await page.goto("#/summary");
  const nav = page.getByRole("navigation", { name: "Policy reform" });
  const links = nav.getByRole("link");
  const inNav = registry.reforms.filter((r) => (r as { in_nav?: boolean }).in_nav !== false);
  await expect(links).toHaveCount(inNav.length);
  for (const r of inNav) await expect(nav.locator(`a[data-reform="${r.id}"]`)).toHaveAccessibleName(r.label + (r.status === "ready" ? "" : " (in development)"));
  // the combined view is out of the picker (owner, 2026-11-10); its routes still work
  await expect(nav.locator('a[data-reform="combined"]')).toHaveCount(0);
  await expect(nav.locator('a[aria-current="page"]')).toHaveAttribute("data-reform", registry.default);
});

test("ADU links without a prefix still open the ADU screens with the same numbers (the bare root is the Introduction)", async ({ page }) => {
  const { run_id } = await (await page.request.get("runs/latest.json")).json();
  const state = await (await page.request.get(`runs/${run_id}/state.json`)).json();
  for (const url of ["#/summary", "#/adu/summary", "#/adu/", "#/compare", "#/adu/compare"]) {
    await page.goto(url);
    await expect(page.getByTestId("run-id")).toHaveText(run_id);
    await expect(page.getByTestId("range-low")).toHaveText(fmt(state.range90.low));
    await expect(page.getByTestId("range-high")).toHaveText(fmt(state.range90.high));
  }
  await expect(page).toHaveTitle("Summary · Wisconsin ADU law · Missing Middleware");
});

for (const r of registry.reforms.filter((x) => x.status === "in_development")) {
  test(`${r.id}: holding page shows the benchmark and no numbers, and the picker returns to ADUs`, async ({ page }) => {
    const errors: string[] = [];
    page.on("pageerror", (e) => errors.push(String(e)));
    if ((r as { in_nav?: boolean }).in_nav === false) await page.goto(`#/${r.id}/`);   // not in the picker: open by its address
    else {
      await page.goto("#/compare?s=upper");
      await page.getByRole("navigation", { name: "Policy reform" }).locator(`a[data-reform="${r.id}"]`).click();
    }
    await expect(page).toHaveURL(new RegExp(`#/${r.id}/`));
    await expect(page.getByTestId("reform-title")).toHaveText(r.label);
    await expect(page.getByTestId("in-development")).toBeVisible();
    await expect(page.getByTestId("benchmark")).toHaveText(r.benchmark);
    await expect(page.locator("main")).not.toContainText(/\d{2,}/);
    await expect(page.getByRole("navigation", { name: "Screens" })).toBeVisible();
    await page.getByRole("navigation", { name: "Policy reform" }).locator(`a[data-reform="${registry.default}"]`).click();
    await expect(page.getByTestId("summary")).toBeVisible();
    expect(errors).toEqual([]);
  });
}

test("preview mode shows a reform's own screens before it is ready, flagged, and only in this tab", async ({ page }) => {
  const dev = registry.reforms.filter((x) => x.status === "in_development" && x.id === "parking");
  test.skip(dev.length === 0, "no in-development reform with its own screens");
  await page.goto("#/parking/");
  await expect(page.getByTestId("in-development")).toBeVisible();
  await expect(page.getByTestId("preview-flag")).toHaveCount(0);
  await page.goto("#/parking/?preview=1");
  await expect(page.getByTestId("preview-flag")).toBeVisible();
  await expect(page.getByTestId("in-development")).toHaveCount(0);
  // the ADU screens never show the preview flag
  await page.goto("#/summary");
  await expect(page.getByTestId("preview-flag")).toHaveCount(0);
  await page.goto("#/parking/?preview=0");
  await expect(page.getByTestId("in-development")).toBeVisible();
});

test("every reform has the same tabs in the same order; a reform without one omits it", async ({ page }) => {
  const ORDER = ["Summary", "Where", "How sure", "Why", "Pilots", "Brief"];
  for (const [id, pre] of [["adu", ""], ["middle", "/middle"], ["tod", "/tod"], ["parking", "/parking"]]) {
    await page.goto(`#${pre}/summary`);
    await expect(page.getByTestId("summary")).toHaveAttribute("data-reform", id);
    const tabs = (await page.locator("nav.tabs a").allTextContents()).map((t) => t.replace(/^\s*\d+\s*/, "").trim());
    expect(tabs, id).toEqual(ORDER.filter((t) => tabs.includes(t)));
    expect(tabs[0], `${id}: Summary is first`).toBe("Summary");
    for (const t of ["Summary", "Where", "How sure", "Why"]) expect(tabs, `${id} has ${t}`).toContain(t);
    expect(tabs, `${id}: no Wisconsin today tab`).not.toContain("Wisconsin today");
    expect(tabs, `${id}: no Statewide comparison tab`).not.toContain("Statewide comparison");
    // the bare reform address lands on Summary
    await page.goto(`#${pre || "/adu"}/`);
    await expect(page.getByTestId("summary")).toHaveAttribute("data-reform", id);
  }
  await page.goto("#/middle/summary");
  await expect(page.getByTestId("summary")).toHaveAttribute("data-reform", "middle");
  expect((await page.locator("nav.tabs a").allTextContents()).map((t) => t.replace(/^\s*\d+\s*/, "").trim())).toEqual(["Summary", "Where", "How sure", "Why", "Brief"]);   // no pilots; Brief holds the estimate card (owner 2026-11-12)
});

test("old addresses keep working: /compare opens Summary, /today opens the reform's part of Wisconsin today", async ({ page }) => {
  for (const [pre, id] of [["", "adu"], ["/middle", "middle"], ["/tod", "tod"], ["/parking", "parking"]]) {
    await page.goto(`#${pre}/compare?timing=flat`);
    await expect(page).toHaveURL(new RegExp(`#${pre}/summary\\?timing=flat$`));
    await expect(page.getByTestId("summary")).toHaveAttribute("data-reform", id);
    await page.goto(`#${pre}/today`);
    await expect(page).toHaveURL(new RegExp(`#/wisconsin-today\\?section=${id}$`));
    await expect(page.getByTestId("wisconsin-today")).toBeVisible();
    await expect(page.getByTestId(`wt-section-${id}`)).toBeInViewport();
  }
  // the TOD map view carries over
  await page.goto("#/tod/today?view=madison");
  await expect(page).toHaveURL(/#\/wisconsin-today\?section=tod&view=madison$/);
  await expect(page.locator('input[name="tod-today-view"][value="madison"]')).toBeChecked();
});

test("the header links to Wisconsin today from every page", async ({ page }) => {
  for (const url of ["#/", "#/summary", "#/tod/where", "#/parking/how-sure"]) {
    await page.goto(url);
    await page.getByTestId("head-today").click();
    await expect(page).toHaveURL(/#\/wisconsin-today$/);
    await expect(page.getByTestId("wisconsin-today")).toBeVisible();
    await expect(page.getByTestId("head-today")).toHaveAttribute("aria-current", "page");
  }
});
