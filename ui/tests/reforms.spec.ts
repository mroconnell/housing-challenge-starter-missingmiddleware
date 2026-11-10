// The multi-reform shell: the reform picker, prefixed URLs, holding pages for reforms in development, and
// that the ADU screens are unchanged by the shell (same numbers, same URLs, same run id).
import { expect, test } from "@playwright/test";
import registry from "../src/scenarios/registry.json" with { type: "json" };

const fmt = (v: number) => Math.round(v).toLocaleString("en-US");

test("the picker lists every registered reform and marks the current one", async ({ page }) => {
  await page.goto("#/today");
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
  const central = state.scenarios.find((s: { id: string }) => s.id === "central");
  for (const url of ["#/today", "#/adu/today", "#/adu/"]) {
    await page.goto(url);
    await expect(page.getByTestId("run-id")).toHaveText(run_id);
    await expect(page.getByTestId("today-central")).toHaveText("+" + fmt(central.additional_total));
  }
  await expect(page).toHaveTitle("Wisconsin today · Wisconsin ADU law · Missing Middleware");
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
    await expect(page.getByTestId("today-central")).toBeVisible();
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
  await page.goto("#/today");
  await expect(page.getByTestId("preview-flag")).toHaveCount(0);
  await page.goto("#/parking/?preview=0");
  await expect(page.getByTestId("in-development")).toBeVisible();
});
