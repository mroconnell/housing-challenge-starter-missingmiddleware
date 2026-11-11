// Middle housing screens (owned by the middle housing thread). Every expected number is read from the middle bundle.
import { expect, test } from "@playwright/test";

const num = (v: number) => (v < 0 ? `−${Math.round(-v).toLocaleString("en-US")}` : Math.round(v).toLocaleString("en-US"));

async function statewide(page: import("@playwright/test").Page) {
  const root = "scenarios/middle/runs/";
  const { run_id } = await (await page.request.get(`${root}latest.json`)).json();
  return (await page.request.get(`${root}${run_id}/statewide.json`)).json();
}

test("middle housing shows one 90% range with side lines, and the timing switch changes it", async ({ page }) => {
  const s = await statewide(page);
  const errors: string[] = [];
  page.on("console", (m) => { if (m.type() === "error") errors.push(m.text()); });
  await page.goto("#/middle/summary");
  await expect(page.getByTestId("range-low")).toHaveText(num(s.range90.low));
  await expect(page.getByTestId("range-high")).toHaveText(num(s.range90.high));
  for (const l of s.side_lines.filter((x: { where: string; id: string }) => x.where === "chart" && x.id !== "all"))
    await expect(page.locator(`[data-testid="summary-legend"] [data-side="${l.id}"]`)).toContainText(num(l.value));
  // the all-building-sizes line is listed, not drawn (far above the scale)
  await expect(page.getByTestId("summary-timing-note")).toContainText("Not drawn");
  await expect(page.getByText(/\bCentral\b/)).toHaveCount(0);
  await page.getByTestId("toggle-timing").getByLabel("Flat").check();
  await expect(page).toHaveURL(/timing=flat/);
  await expect(page.getByTestId("range-low")).toHaveText(num(s.range90_flat.low));
  await expect(page.getByTestId("range-high")).toHaveText(num(s.range90_flat.high));
  // How sure's Details: both timings, the yearly table and every chart side line
  await page.goto("#/middle/how-sure");
  await expect(page.getByTestId("range-card").getByTestId("range-low")).toHaveText(num(s.range90.low));
  await expect(page.getByTestId("flat-range")).toHaveText(`${num(s.range90_flat.low)} to ${num(s.range90_flat.high)}`);
  for (const l of s.side_lines.filter((x: { where: string }) => x.where === "chart"))
    await expect(page.locator(`[data-testid="side-lines"] [data-side="${l.id}"]`)).toContainText(num(l.value));
  await page.goto("#/middle/why");
  await expect(page.getByTestId("law-text")).toContainText("2–6 homes");
  for (const p of ["where", "how-sure", "why"]) { await page.goto(`#/middle/${p}`); await expect(page.locator("main h1")).toBeVisible(); }
  expect(errors).toEqual([]);
});
