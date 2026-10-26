// The multi-reform shell: the reform picker, prefixed URLs, holding pages for reforms in development, and
// that the ADU screens are unchanged by the shell (same numbers, same URLs, same run id).
import { expect, test } from "@playwright/test";
import registry from "../src/scenarios/registry.json" with { type: "json" };

const fmt = (v: number) => Math.round(v).toLocaleString("en-US");

test("the picker lists every registered reform and marks the current one", async ({ page }) => {
  await page.goto("#/today");
  const nav = page.getByRole("navigation", { name: "Policy reform" });
  const links = nav.getByRole("link");
  await expect(links).toHaveCount(registry.reforms.length);
  for (const r of registry.reforms) await expect(nav.locator(`a[data-reform="${r.id}"]`)).toContainText(r.label);
  await expect(nav.locator('a[aria-current="page"]')).toHaveAttribute("data-reform", registry.default);
});

test("ADU links without a prefix still open the ADU screens with the same numbers", async ({ page }) => {
  const { run_id } = await (await page.request.get("runs/latest.json")).json();
  const state = await (await page.request.get(`runs/${run_id}/state.json`)).json();
  const central = state.scenarios.find((s: { id: string }) => s.id === "central");
  for (const url of ["#/today", "#/adu/today", "#"]) {
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
    await page.goto("#/compare?s=upper");
    await page.getByRole("navigation", { name: "Policy reform" }).locator(`a[data-reform="${r.id}"]`).click();
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
