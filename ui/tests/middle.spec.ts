// Middle housing screens (owned by the middle housing thread). Every expected number is read from the middle bundle.
import { expect, test } from "@playwright/test";

const num = (v: number) => (v < 0 ? `−${Math.round(-v).toLocaleString("en-US")}` : Math.round(v).toLocaleString("en-US"));

const MIDDLE_LEGEND_NOTE = "Counts homes by building, as the Census does. A duplex plus a 4-plex on one lot counts as 6 homes here. A single 5- or 6-unit building falls in the Census's 5+ group, so it shows only in the 'Adding 5 and 6 unit buildings' line.";

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
  // the all-building-sizes line is left off the Summary (owner, 2026-11-11 20:41); it stays on How sure
  await expect(page.locator('[data-testid="summary-legend"] [data-side="all"]')).toHaveCount(0);
  await expect(page.locator("main")).not.toContainText("All building sizes");
  await expect(page.locator("main")).not.toContainText("7,888");
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

// Owner, 2026-11-11 20:41: current law on the Summary is homes in 2–4 unit buildings (baseline_2_4_by_year), not all
// homes; the range band sits on top of it; the legend uses the owner's labels; the all-building-sizes line is gone.
test("middle Summary: current law is homes in 2–4 unit buildings, with the owner's legend labels", async ({ page }) => {
  const s = await statewide(page);
  const B = s.baseline_2_4_by_year as { central: number[]; low: number[]; high: number[] };
  const sum = (xs: number[]) => xs.reduce((a, b) => a + b, 0);
  // the bundle's numbers: 1,709.3 a year central, 8,546.5 over 5 years (shown 8,547), range 3,894 to 15,085
  expect(num(B.central[0])).toBe("1,709");
  expect(sum(B.central)).toBeCloseTo(8546.5, 1);
  expect([num(sum(B.low)), num(sum(B.high))]).toEqual(["3,894", "15,085"]);
  expect(sum(B.central)).not.toBe(sum(s.baseline_by_year.central));
  const side = (id: string) => (s.side_lines as { id: string; value: number }[]).find((l) => l.id === id)!.value;
  await page.goto("#/middle/summary?show=totals");
  await expect(page.getByTestId("summary-legend").locator("li")).toHaveText([
    "Current law (homes in 2–4 unit buildings without the reform; its range shaded grey)",
    `With the law: 90% range, ${num(s.range90.low)} to ${num(s.range90.high)} extra homes in 2–4 unit buildings (on top of current law)`,
    `Four-state measured result: ${num(side("four_state"))}`,
    `All 1–4 unit buildings: ${num(side("1_4"))} (adds 1-unit homes such as split-lot homes and townhouses. Too noisy to include in predicted range because Census mixes them with ordinary single-family homes.)`,
    `Adding 5 and 6 unit buildings: ${num(side("1_6"))} (the 1–4 unit figure plus our estimate for 5 and 6 unit buildings. Too noisy to include in predicted range because Census mixes 5 and 6 unit projects with all 5+ unit projects.)`,
  ]);
  expect([num(s.range90.low), num(s.range90.high), num(side("four_state")), num(side("1_4")), num(side("1_6"))]).toEqual(["−482", "4,515", "1,570", "3,905", "4,226"]);
  // the table: current law per year and in all, and the band on top of it
  await page.getByTestId("summary-table-toggle").click();
  const rows = page.getByTestId("summary-table").locator("tbody tr");
  for (let i = 0; i < 5; i++) await expect(rows.nth(i).locator("td").first()).toHaveText(num(B.central[i]));
  await expect(rows.nth(5).locator("td").first()).toHaveText(num(sum(B.central)));
  await expect(page.getByTestId("table-total-low")).toHaveText(num(sum(B.central) + s.range90.low));
  await expect(page.getByTestId("table-total-high")).toHaveText(num(sum(B.central) + s.range90.high));
  // the year popup: current law, and the band's ends on top of it
  const y = s.range90.years[2];
  await page.locator(`#sum-chart rect.sum-hit-year[data-year="${y.year}"]`).dispatchEvent("pointerover");
  await expect(page.getByTestId("pop-current-law")).toHaveText(num(B.central[2]));
  await expect(page.getByTestId("pop-low")).toHaveText(num(B.central[2] + Math.min(y.low, y.high)));
  await expect(page.getByTestId("pop-high")).toHaveText(num(B.central[2] + Math.max(y.low, y.high)));
  // the chart: the current-law band spans the 2–4 unit baseline's low and high, far below all homes (24,800 a year)
  const svg = page.locator("#sum-chart svg");
  await expect(svg.locator('path[data-band="current-law"]')).toHaveCount(1);
  await expect(svg.locator("desc")).not.toContainText("24,800");
  // per 1,000 Wisconsin homes: the same baseline ÷ 2,778.572
  await page.getByTestId("toggle-per").getByLabel("Per 1,000 Wisconsin homes").check();
  const k = 2778.572;
  const d2 = (v: number) => (Math.round(v * 100) / 100).toLocaleString("en-US", { minimumFractionDigits: 2, maximumFractionDigits: 2 });
  await page.locator(`#sum-chart rect.sum-hit-year[data-year="${y.year}"]`).dispatchEvent("pointerover");
  await expect(page.getByTestId("pop-current-law")).toHaveText(d2(B.central[2] / k));
  // extra homes only (the default): current law is the zero line, the side lines have the same labels
  await page.goto("#/middle/summary");
  await expect(page.getByTestId("summary-legend").locator("li").first()).toHaveText("Current law: the zero line");
  await expect(page.locator('[data-testid="summary-legend"] [data-side="all"]')).toHaveCount(0);
  await expect(page.locator('[data-testid="summary-legend"] [data-side="1_4"]')).toContainText("Too noisy to include in predicted range");
  // the building-count note lives on How sure, not under the chart key (owner 2026-11-11 23:33)
  await expect(page.getByTestId("summary-legend-note")).toHaveCount(0);
  await page.goto("#/middle/how-sure");
  await expect(page.getByTestId("building-count-note")).toHaveText(MIDDLE_LEGEND_NOTE);
  await page.goto("#/middle/summary?show=totals");
  // How sure still lists the all-building-sizes line
  await page.goto("#/middle/how-sure");
  await expect(page.locator('[data-testid="side-lines"] [data-side="all"]')).toContainText(num(side("all")));
});

test("middle Why: In and out of the model lists 7 in and 7 out from evidence_scope, and the Summary links to it", async ({ page }) => {
  const s = await statewide(page);
  const sc = s.evidence_scope as { in: { name: string; kind: string; role: string }[]; out: { name: string; reason: string }[]; source: string };
  expect(sc.in).toHaveLength(7);
  expect(sc.out).toHaveLength(7);
  expect(sc.in.filter((x) => x.role === "test only")).toHaveLength(1);
  await page.goto("#/middle/summary");
  await page.getByTestId("summary-scope-link").locator("a").click();
  await expect(page).toHaveURL(/#\/middle\/why\?section=middle-in-out$/);
  const box = page.locator("#middle-in-out");
  await expect(box).toBeInViewport();
  await expect(box.getByRole("heading", { level: 2 })).toHaveText("In and out of the model");
  await expect(box.getByTestId("in-col").locator("li")).toHaveCount(7);
  await expect(box.getByTestId("out-places").locator("li")).toHaveCount(7);
  await expect(box.getByTestId("in-states").locator("li")).toHaveCount(4);
  for (const n of ["Oregon", "California", "Maine", "Vermont"]) await expect(box.getByTestId("in-states")).toContainText(`${n}:`);
  await expect(box.getByTestId("in-test").locator("li")).toHaveCount(1);
  await expect(box.getByTestId("in-test")).toContainText("test only");
  for (const o of sc.out) await expect(box.getByTestId("out-places")).toContainText(o.name);
  await expect(box.getByTestId("in-out-source")).toHaveText(`Source: ${sc.source}`);
  await expect(page.locator("main")).not.toContainText(/85 of 100/);
});
