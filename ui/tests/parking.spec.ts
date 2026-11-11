// Parking requirement reduction screens (owned by the parking conductor). Every expected number is read
// from the parking bundle, never hard-coded. Opened through preview mode until the reform is "ready".
import { expect, test } from "@playwright/test";

const fmt = (v: number) => Math.round(v).toLocaleString("en-US");

async function bundle(page: import("@playwright/test").Page) {
  const root = "scenarios/parking/runs/";
  const { run_id } = await (await page.request.get(`${root}latest.json`)).json();
  const get = async (f: string) => (await page.request.get(`${root}${run_id}/${f}.json`)).json();
  return { run_id, statewide: await get("statewide"), pilots: await get("pilots") };
}

test("parking screens show the bundle's numbers", async ({ page }) => {
  const b = await bundle(page);
  const up = b.statewide.scenarios.find((x: { id: string }) => x.id === "upper");
  await page.goto("#/parking/summary?preview=1");
  await expect(page.getByTestId("run-id")).toHaveText(b.run_id);
  await page.goto("#/wisconsin-today");
  await expect(page.getByTestId("wt-section-parking").getByTestId("baseline-total")).toHaveText(fmt(b.statewide.baseline_total));
  // the uniform range display: one 90% range, no centre line, side lines across it
  const R = b.statewide.range90;
  const sig = (v: number) => (v < 0 ? `−${fmt(-v)}` : fmt(v));
  await page.goto("#/parking/how-sure");
  const card = page.getByTestId("range-card");
  await expect(card.getByTestId("range-low")).toHaveText(sig(R.low));
  await expect(card.getByTestId("range-high")).toHaveText(sig(R.high));
  await expect(card.getByTestId("range-unit")).toContainText("90% range");
  await expect(card.getByTestId("range-shares")).toContainText(`of the ${fmt(b.statewide.baseline_total)} homes`);
  await expect(page.getByTestId("table-range-low")).toHaveText(sig(R.low));
  await expect(page.getByTestId("table-range-high")).toHaveText(sig(R.high));
  for (const l of b.statewide.side_lines.filter((x: { where: string }) => x.where === "chart"))
    await expect(page.getByTestId("side-lines")).toContainText(`${l.label}: ${sig(l.value)}`);
  await expect(page.getByTestId("add-central")).toHaveCount(0);   // no centre line
  await expect(page.locator("main")).not.toContainText("No measurable change");
  await page.goto("#/parking/where?level=county");
  await expect(page.getByTestId("where-range-note")).toContainText(`${sig(R.low)} to ${sig(R.high)}`);
  await expect(page.getByTestId("where-table")).toContainText(`statewide ${sig(R.low)} to ${sig(R.high)}`);
  await expect(page.getByTestId("parking-map").locator("canvas")).toBeVisible();
  for (const p of b.pilots) {
    await page.goto(`#/parking/pilot/${p.slug}`);
    await expect(page.getByTestId("pilot-baseline")).toHaveText(fmt(p.baseline));
    await expect(page.getByTestId("pilot-upper")).toHaveText(fmt(p.add_upper));
  }
  await page.goto("#/parking/how-sure");
  await expect(page.getByTestId("details")).toBeVisible();
  const hs = b.statewide.side_lines.find((x: { where: string }) => x.where === "howsure");
  await expect(page.getByTestId("howsure-side-lines")).toContainText(`${hs.label}: ${sig(hs.low)} to ${sig(hs.high)}`);
  await expect(page.getByTestId("pk-inputs")).toBeVisible();
  await expect(page.getByTestId("pk-other")).toBeVisible();
  await page.goto("#/parking/why");
  await expect(page.locator("main h1")).toBeVisible();
  await page.goto("#/parking/brief");
  await expect(page.getByTestId("brief-headline")).toContainText(`${sig(R.low)} to ${sig(R.high)} extra homes permitted in Wisconsin over 2027–2031 (90% range)`);
  await expect(page.getByTestId("brief")).toContainText(fmt(up.additional_total));
});

test("parking Summary: the chart toggles, and the timing toggle is off (no measured ramp)", async ({ page }) => {
  await page.goto("#/parking/summary");
  const toggle = page.getByTestId("toggle-show");
  await expect(toggle.getByLabel("Extra homes only")).toBeChecked();   // the default (owner, 2026-11-11 20:42)
  await toggle.getByLabel("Totals with current law").check();
  await expect(page.locator("#sum-chart svg title")).toContainText("Homes each year");
  await expect(page.getByTestId("summary-legend")).toContainText("90% range");
  await toggle.getByLabel("Extra homes only").check();
  await expect(page.locator("#sum-chart svg title")).toContainText("Extra homes from the law");
  await expect(page.getByTestId("summary-legend")).toContainText("Current law: the zero line");
  for (const r of await page.getByTestId("toggle-timing").getByRole("radio").all()) await expect(r).toBeDisabled();
  await expect(page.getByTestId("no-ramp")).toHaveText("This reform has no measured ramp.");
});

test("parking's part of Wisconsin today shows the check-up against places after repeal", async ({ page }) => {
  await page.goto("#/wisconsin-today");
  const sec = page.getByTestId("wt-section-parking");
  await expect(sec.getByTestId("checkup")).toContainText("per 1,000 existing homes");
  await expect(sec.getByTestId("parking-checkup")).toContainText("parking spaces for every new apartment");
  await expect(page.locator("#pk-today-chart svg")).toBeVisible();
});
