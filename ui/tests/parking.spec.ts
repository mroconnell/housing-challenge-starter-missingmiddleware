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
  const [cen, up] = b.statewide.scenarios;
  await page.goto("#/parking/today?preview=1");
  await expect(page.getByTestId("run-id")).toHaveText(b.run_id);
  await expect(page.getByTestId("baseline-total")).toHaveText(fmt(b.statewide.baseline_total));
  await page.goto("#/parking/compare");
  await expect(page.getByTestId("add-central")).toHaveText(fmt(cen.additional_total));
  await expect(page.getByTestId("add-upper")).toHaveText(fmt(up.additional_total));
  await expect(page.getByTestId("compare-table")).toContainText(fmt(up.with_law_total));
  await page.goto("#/parking/where?level=county");
  await expect(page.getByTestId("where-table")).toContainText(`statewide total ${fmt(up.additional_total)}`);
  for (const p of b.pilots) {
    await page.goto(`#/parking/pilot/${p.slug}`);
    await expect(page.getByTestId("pilot-baseline")).toHaveText(fmt(p.baseline));
    await expect(page.getByTestId("pilot-upper")).toHaveText(fmt(p.add_upper));
  }
  for (const path of ["how-sure", "why", "brief"]) {
    await page.goto(`#/parking/${path}`);
    await expect(page.locator("main h1")).toBeVisible();
  }
  await expect(page.getByTestId("brief")).toContainText(fmt(up.additional_total));
});
