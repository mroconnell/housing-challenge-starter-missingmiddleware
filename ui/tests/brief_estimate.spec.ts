// Each reform's Brief tab carries the estimate card moved from the Introduction's ranges table (owner, 2026-11-12):
// "The estimate, 2027–2031 (90% range)", the low and high ends with the unit (read from the reform's own bundle), and the
// "How we count" line from ui/src/howwecount.ts, the same line as the reform's Summary.
import { readFileSync } from "node:fs";
import { expect, test, type Page } from "@playwright/test";

const fmt = (v: number) => Math.round(v).toLocaleString("en-US");
const signed = (v: number) => (Math.round(v) < 0 ? `−${fmt(-v)}` : `+${fmt(v)}`);

/** The How we count lines, parsed from the one source module. */
const HWC: Record<string, string> = Object.fromEntries(
  [...readFileSync(new URL("../src/howwecount.ts", import.meta.url), "utf8").matchAll(/\n  (adu|middle|tod|parking): "((?:[^"\\]|\\.)*)"/g)].map((m) => [m[1], m[2]]));

async function bundle(page: Page, root: string, file: string) {
  const { run_id } = await (await page.request.get(`${root}latest.json`)).json();
  return (await page.request.get(`${root}${run_id}/${file}`)).json();
}

const CASES: { id: string; pre: string; root: string; file: string; unit: string; ends: (b: any) => [number, number] }[] = [
  { id: "adu", pre: "", root: "runs/", file: "state.json", unit: "extra ADU permits", ends: (b) => [b.range90.low, b.range90.high] },
  { id: "middle", pre: "/middle", root: "scenarios/middle/runs/", file: "statewide.json", unit: "extra homes in 2–4 unit buildings", ends: (b) => [b.core.lower, b.core.upper] },
  { id: "tod", pre: "/tod", root: "scenarios/tod/runs/", file: "statewide.json", unit: "extra homes permitted near transit", ends: (b) => [b.range90.low, b.range90.high] },
];
// the owner-approved numbers the cards must show (five-year totals, 2027–2031)
const EXPECTED: Record<string, [string, string]> = {
  adu: ["8,055", "13,666"], middle: ["−482", "+4,515"], tod: ["3,922", "16,335"],
};

// Parking is off the tool (owner, 2026-11-12; git tag parking-ui-before-removal-2026-11-12): its line stays in the
// source only so the unrouted parking module compiles.
test("the How we count source has the three lines plus parking's kept line", () => {
  expect(Object.keys(HWC)).toEqual(["adu", "middle", "tod", "parking"]);
});

for (const c of CASES) {
  test(`${c.id} Brief: the estimate card with the bundle's ends, the unit and the How we count line`, async ({ page }) => {
    await page.goto(`#${c.pre}/brief`);
    const card = page.getByTestId("brief-estimate");
    await expect(card).toHaveCount(1);
    await expect(card).toHaveAttribute("data-reform", c.id);
    await expect(card.getByRole("heading", { name: "Projected range, 2027–2031 (90%)", exact: true })).toBeVisible();
    const b = await bundle(page, c.root, c.file);
    const [lo, hi] = c.ends(b);
    const f = lo < 0 ? signed : fmt;
    await expect(card.getByTestId("estimate-low")).toHaveText(f(lo));
    await expect(card.getByTestId("estimate-high")).toHaveText(f(hi));
    expect([f(lo), f(hi)]).toEqual(EXPECTED[c.id]);
    await expect(card.locator(".estimate-end").first()).toHaveText(new RegExp(`^\\s*Low end\\s+${f(lo).replace("+", "\\+")}\\s+${c.unit}\\s*$`));
    await expect(card.locator(".estimate-end").nth(1)).toHaveText(new RegExp(`^\\s*High end\\s+${f(hi).replace("+", "\\+")}\\s+${c.unit}\\s*$`));
    await expect(card.getByTestId("estimate-how")).toHaveText(`How we count. ${HWC[c.id]}`);
    // the same line as the reform's Summary
    await page.goto(`#${c.pre}/summary`);
    await expect(page.getByTestId("summary-how")).toHaveText(`How we count. ${HWC[c.id]}`);
  });
}

test("the middle housing Brief tab is reachable from its tabs", async ({ page }) => {
  await page.goto("#/middle/summary");
  await page.locator("nav.tabs a", { hasText: "Brief" }).click();
  await expect(page).toHaveURL(/#\/middle\/brief$/);
  await expect(page.getByTestId("brief-estimate")).toBeVisible();
  await expect(page.locator("h1")).toHaveCount(1);
});

test("the estimate card fits a 375 px phone", async ({ page }) => {
  await page.setViewportSize({ width: 375, height: 812 });
  for (const c of CASES) {
    await page.goto(`#${c.pre}/brief`);
    await expect(page.getByTestId("brief-estimate")).toBeVisible();
    expect(await page.evaluate(() => document.documentElement.scrollWidth - document.documentElement.clientWidth), c.id).toBeLessThanOrEqual(0);
  }
});
