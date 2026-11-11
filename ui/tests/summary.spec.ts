// The shared Summary tab (ui/src/summary.ts) for all four reforms, and the shared Wisconsin today page. Every expected
// number is read from the bundles and shared reference files, never typed here: the 90% range ends, the side-line
// popups (label, value, unit, note), the year popups and crosshair, keyboard access, the three URL toggles (per 1,000
// Wisconsin homes = total ÷ 2,778.572, totals or extra only, measured or flat timing) and no centre line.
import { readFileSync } from "node:fs";
import { expect, test, type Page } from "@playwright/test";

const fmt = (v: number) => { const r = Math.round(v); return (r === 0 ? 0 : r).toLocaleString("en-US"); };
const num = (v: number) => (Math.round(v) < 0 ? `−${fmt(-v)}` : fmt(v));
const dec2 = (v: number) => { const r = Math.round(v * 100) / 100; return r < 0 ? `−${(-r).toLocaleString("en-US", { minimumFractionDigits: 2, maximumFractionDigits: 2 })}` : (r === 0 ? 0 : r).toLocaleString("en-US", { minimumFractionDigits: 2, maximumFractionDigits: 2 }); };

const ADU_LABELS: Record<string, string> = {
  median8: "Median path of the 8 statewide-law states",
  slow2: "Like OR & RI (lowest statewide adoption)",
  like_california: "Like CA (highest statewide adoption)",
};

interface Side { id: string; label: string; value?: number; note: string; where: string }
interface R90 { low: number; high: number; years: { year: number; low: number; high: number }[] }
interface Reform { id: string; pre: string; R: R90; flat: R90 | null; lines: Side[] }

async function json(page: Page, root: string, file: string) {
  const { run_id } = await (await page.request.get(`${root}latest.json`)).json();
  return (await page.request.get(`${root}${run_id}/${file}`)).json();
}

async function reforms(page: Page): Promise<{ list: Reform[]; homes: number }> {
  const adu = await json(page, "runs/", "state.json");
  const mid = await json(page, "scenarios/middle/runs/", "statewide.json");
  const tod = await json(page, "scenarios/tod/runs/", "statewide.json");
  const pk = await json(page, "scenarios/parking/runs/", "statewide.json");
  const even = (R: R90): R90 => ({ ...R, years: R.years.map((y) => ({ year: y.year, low: R.low / 5, high: R.high / 5 })) });
  const chart = (xs: Side[]) => xs.filter((s) => s.where === "chart" && s.value !== undefined);
  return {
    homes: adu.acs_total_units.value,
    list: [
      // the ADU Summary relabels its lines and leaves "typical" off the chart (owner, 2026-11-11; display only)
      { id: "adu", pre: "", R: adu.range90, flat: even(adu.range90), lines: chart(adu.side_lines).filter((s) => s.id !== "typical").map((s) => ({ ...s, label: ADU_LABELS[s.id] ?? s.label })) },
      { id: "middle", pre: "/middle", R: mid.range90, flat: mid.range90_flat, lines: chart(mid.side_lines).filter((s) => s.id !== "all") },
      { id: "tod", pre: "/tod", R: tod.range90, flat: even(tod.range90), lines: chart(tod.side_lines) },
      { id: "parking", pre: "/parking", R: pk.range90, flat: null, lines: chart(pk.side_lines) },
    ],
  };
}

test("the per-1,000 base is all Wisconsin homes, ACS 2020–2024: 2,778,572, the same for every reform", async ({ page }) => {
  const { homes } = await reforms(page);
  expect(homes).toBe(2778572);
  const tod = await json(page, "scenarios/tod/runs/", "statewide.json");
  expect(tod.acs_homes).toBe(homes);
});

for (const id of ["adu", "middle", "tod", "parking"]) {
  test(`${id} Summary: ends, How we count, side-line and year popups, keyboard, table and no centre line`, async ({ page, isMobile }) => {
    const errors: string[] = [];
    page.on("pageerror", (e) => errors.push(String(e)));
    const { list } = await reforms(page);
    const r = list.find((x) => x.id === id)!;
    await page.goto(`#${r.pre}/summary`);
    await expect(page.locator("h1")).toHaveCount(1);
    await expect(page.getByTestId("summary")).toHaveAttribute("data-reform", id);
    // one plain sentence, the range with both ends labelled and its unit
    await expect(page.getByTestId("summary-sentence")).toContainText("from 1 January 2027");
    const card = page.getByTestId("summary-range");
    await expect(card.getByTestId("range-low")).toHaveText(num(r.R.low));
    await expect(card.getByTestId("range-high")).toHaveText(num(r.R.high));
    await expect(card).toContainText("Low end");
    await expect(card).toContainText("High end");
    await expect(card.getByTestId("range-unit")).toContainText("2027–2031 (90% range)");
    await expect(page.getByTestId("summary-how")).toContainText("How we count.");
    // only one row of links under the chart
    const links = page.getByTestId("summary-links").locator("a");
    await expect(links).toHaveText(["Where homes would go →", "How sure we are →", "Why →"]);
    await expect(links.nth(1)).toHaveAttribute("href", `#${r.pre}/how-sure`);
    // no centre line: only current law and the side lines are drawn as lines
    const svg = page.locator("#sum-chart svg");
    await expect(svg.locator('path[data-band="range90"]')).toHaveCount(1);
    const ids = await svg.locator("path[data-series]").evaluateAll((ps) => ps.map((p) => p.getAttribute("data-series")));
    expect(ids.filter((i) => i !== "current-law" && !i!.startsWith("side-"))).toEqual([]);
    expect(ids.filter((i) => i!.startsWith("side-"))).toHaveLength(r.lines.length);
    await expect(page.locator("main")).not.toContainText(/\bcentral (scenario|line)\b/i);

    // side-line popups: label, value with its unit, and the line's own note (hover or tap on the line)
    const pop = page.getByTestId("summary-popup");
    await expect(pop).toBeHidden();
    for (const s of r.lines) {
      await svg.locator(`circle.sum-hit-side[data-side="${s.id}"][data-year="2031"]`).dispatchEvent("pointerover");
      await expect(pop).toBeVisible();
      await expect(pop).toContainText(s.label);
      await expect(pop.getByTestId("pop-side-value")).toHaveText(num(s.value!));
      await expect(pop).toContainText("2027–2031");
      await expect(pop.getByTestId("pop-side-note")).toHaveText(s.note);
    }
    await svg.dispatchEvent("pointerleave");
    await expect(pop).toBeHidden();

    // year popups in the extra-homes view: the band's low and high and every drawn line, with a crosshair
    await page.getByTestId("toggle-show").getByLabel("Extra homes only").check();
    await expect(page).toHaveURL(/show=extra/);
    const i = 2;   // 2029
    const y = r.R.years[i];
    await svg.locator(`rect.sum-hit-year[data-year="${y.year}"]`).dispatchEvent("pointerover");
    await expect(pop).toBeVisible();
    await expect(pop).toHaveAttribute("data-year", String(y.year));
    await expect(page.getByTestId("summary-crosshair")).toHaveAttribute("visibility", "visible");
    await expect(pop.getByTestId("pop-low")).toHaveText(num(Math.min(y.low, y.high)));
    await expect(pop.getByTestId("pop-high")).toHaveText(num(Math.max(y.low, y.high)));
    await expect(pop.getByTestId("pop-current-law")).toHaveText("0");
    for (const s of r.lines) await expect(pop.locator(`li[data-side="${s.id}"]`)).toContainText(`${s.label}: ${num(s.value! * (y.low / r.R.low))}`);

    // keyboard: the same details from focusable year buttons and side-line legend items
    if (!isMobile) {
      await page.mouse.move(0, 0);   // keep the resting pointer off the chart, which scrolls under it as focus moves
      await page.locator('.sum-year[data-year="2027"]').focus();
      await expect(pop).toHaveAttribute("data-year", "2027");
      await expect(pop).toContainText(num(Math.min(r.R.years[0].low, r.R.years[0].high)));
      await page.keyboard.press("Escape");
      await expect(pop).toBeHidden();
      const first = r.lines[0];
      await page.locator(`.sum-side[data-side="${first.id}"]`).focus();
      await expect(pop.getByTestId("pop-side-note")).toHaveText(first.note);
      await page.keyboard.press("Tab");   // to the next legend item or the year buttons
      await expect(pop).toBeVisible();
    }

    // "Show as a table": the yearly table, with the five-year ends in its last row
    const tbtn = page.getByTestId("summary-table-toggle");
    await expect(tbtn).toHaveAttribute("aria-expanded", "false");
    await expect(page.getByTestId("summary-table")).toBeHidden();
    await tbtn.click();
    await expect(tbtn).toHaveAttribute("aria-expanded", "true");
    await expect(page.getByTestId("summary-table").locator("tbody tr")).toHaveCount(6);
    await expect(page.getByTestId("table-total-low")).toHaveText(num(r.R.low));
    await expect(page.getByTestId("table-total-high")).toHaveText(num(r.R.high));
    expect(errors).toEqual([]);
  });

  test(`${id} Summary toggles: per 1,000 Wisconsin homes, totals or extra only, timing`, async ({ page }) => {
    const { list, homes } = await reforms(page);
    const r = list.find((x) => x.id === id)!;
    const k = homes / 1000;
    await page.goto(`#${r.pre}/summary`);
    // per 1,000 Wisconsin homes: total ÷ 2,778.572, in the range, the popups and the URL
    await page.getByTestId("toggle-per").getByLabel("Per 1,000 Wisconsin homes").check();
    await expect(page).toHaveURL(/per=1000/);
    await expect(page.getByTestId("range-low")).toHaveText(dec2(r.R.low / k));
    await expect(page.getByTestId("range-high")).toHaveText(dec2(r.R.high / k));
    await expect(page.getByTestId("range-unit")).toContainText("per 1,000 Wisconsin homes");
    await expect(page.getByTestId("per-base")).toContainText("2,778,572 homes, ACS 2020–2024");
    const s = r.lines[0];
    await page.locator(`#sum-chart circle.sum-hit-side[data-side="${s.id}"][data-year="2031"]`).dispatchEvent("pointerover");
    await expect(page.getByTestId("pop-side-value")).toHaveText(dec2(s.value! / k));
    await expect(page.getByTestId("summary-popup")).toContainText("per 1,000 Wisconsin homes");
    // the choice survives a reload (it is in the URL)
    await page.reload();
    await expect(page.getByTestId("toggle-per").getByLabel("Per 1,000 Wisconsin homes")).toBeChecked();
    await expect(page.getByTestId("range-low")).toHaveText(dec2(r.R.low / k));
    await page.getByTestId("toggle-per").getByLabel("Total").check();
    await expect(page).not.toHaveURL(/per=1000/);
    await expect(page.getByTestId("range-low")).toHaveText(num(r.R.low));

    // totals with current law (default) or extra homes only: current law drawn, or the zero line
    const svg = page.locator("#sum-chart svg");
    await expect(svg.locator('path[data-band="current-law"]')).toHaveCount(1);
    await page.getByTestId("toggle-show").getByLabel("Extra homes only").check();
    await expect(page).toHaveURL(/show=extra/);
    await expect(svg.locator('path[data-band="current-law"]')).toHaveCount(0);
    await expect(page.getByTestId("summary-legend")).toContainText("Current law: the zero line");

    // timing: measured (default) or flat; parking has no measured ramp, so the toggle is off
    const timing = page.getByTestId("toggle-timing");
    if (!r.flat) {
      for (const x of await timing.getByRole("radio").all()) await expect(x).toBeDisabled();
      await expect(timing).toHaveAttribute("disabled", "");
      await expect(page.getByTestId("no-ramp")).toHaveText("This reform has no measured ramp.");
      return;
    }
    await expect(timing.getByLabel("Measured")).toBeChecked();
    await timing.getByLabel("Flat").check();
    await expect(page).toHaveURL(/timing=flat/);
    await expect(page.getByTestId("range-low")).toHaveText(num(r.flat.low));
    await expect(page.getByTestId("range-high")).toHaveText(num(r.flat.high));
    await page.locator('#sum-chart rect.sum-hit-year[data-year="2027"]').dispatchEvent("pointerover");
    const y0 = r.flat.years[0];
    await expect(page.getByTestId("pop-low")).toHaveText(num(Math.min(y0.low, y0.high)));
    await expect(page.getByTestId("pop-high")).toHaveText(num(Math.max(y0.low, y0.high)));
    if (id !== "middle") expect(Math.round(y0.low)).toBe(Math.round(r.R.low / 5));   // the five-year total spread evenly
  });
}

test("a real mouse over a year shows the crosshair and that year's popup", async ({ page, isMobile }) => {
  test.skip(isMobile, "mouse test runs on desktop");
  await page.goto("#/summary");
  const rect = page.locator('#sum-chart rect.sum-hit-year[data-year="2030"]');
  await page.locator("#sum-chart").scrollIntoViewIfNeeded();
  const box = (await rect.boundingBox())!;
  await page.mouse.move(box.x + box.width / 2, box.y + 4);   // the top of the plot, clear of the lines
  await expect(page.getByTestId("summary-popup")).toHaveAttribute("data-year", "2030");
  await expect(page.getByTestId("summary-crosshair")).toHaveAttribute("visibility", "visible");
  await page.mouse.move(2, 2);
  await expect(page.getByTestId("summary-popup")).toBeHidden();
});

// ---- Wisconsin today -----------------------------------------------------------------------------
const REF = new URL("../../reference/", import.meta.url);
const csv = (name: string) => {
  const [head, ...lines] = readFileSync(new URL(name, REF), "utf8").trim().split(/\r?\n/);
  const cols = head.split(",");
  return lines.map((l) => Object.fromEntries(cols.map((c, i) => [c, l.split(",")[i]])));
};

test("Wisconsin today shows the baseline, then all housing and the four reforms in order", async ({ page }) => {
  const errors: string[] = [];
  page.on("pageerror", (e) => errors.push(String(e)));
  page.on("console", (m) => { if (m.type() === "error") errors.push(m.text()); });
  await page.goto("#/wisconsin-today");
  await expect(page.locator("h1")).toHaveText("Wisconsin today");
  await expect(page).toHaveTitle("Wisconsin today · Missing Middleware");
  // the baseline from the shared reference files (the same as the Introduction): about 124,000, 56,500 to 218,865
  const proj = csv("housing_baseline_statewide_by_year.csv").filter((r) => r.structure_type === "all" && r.kind === "projected" && Number(r.year) >= 2027 && Number(r.year) <= 2031);
  const central = proj.reduce((a, r) => a + Number(r.central), 0);
  const band = csv("housing_baseline_band.csv").find((r) => r.structure_type === "1unit")!;
  await expect(page.getByTestId("wt-baseline-total")).toHaveText(fmt(central));
  await expect(page.getByTestId("wt-baseline-range")).toHaveText(`${fmt(central * Number(band.low))} to ${fmt(central * Number(band.high))}`);
  expect([Math.round(central), Math.round(central * Number(band.low)), Math.round(central * Number(band.high))]).toEqual([124000, 56500, 218865]);
  await expect(page.locator("#wt-base-chart svg")).toBeVisible();
  await expect(page.getByTestId("wt-baseline-table").locator("tbody tr").last()).toContainText(fmt(central));
  // sections in the fixed order, each with its reform's own content
  const order = await page.locator("[data-testid^=wt-section-]").evaluateAll((els) => els.map((e) => e.getAttribute("data-testid")));
  expect(order).toEqual(["wt-section-all", "wt-section-adu", "wt-section-middle", "wt-section-tod", "wt-section-parking"]);
  const adu = await json(page, "runs/", "state.json");
  await expect(page.getByTestId("wt-section-adu").getByTestId("today-baseline")).toHaveText(fmt(adu.baseline.total));
  await expect(page.getByTestId("today-adu-rules").locator("tfoot")).toContainText(fmt(adu.homes.value));
  await expect(page.getByTestId("today-adu-permits")).toContainText("Madison");
  const last = adu.bps[adu.bps.length - 1];
  await expect(page.getByTestId("wt-middle-last")).toHaveText(fmt(last["2_4"]));
  await expect(page.getByTestId("wt-middle-table").locator("tbody tr")).toHaveCount(adu.bps.filter((b: { "2_4": number | null }) => b["2_4"] !== null).length);
  await expect(page.getByTestId("wt-section-tod").getByTestId("density-tiles")).toBeVisible();
  await expect(page.getByTestId("wt-section-parking").getByTestId("parking-checkup")).toBeVisible();
  await expect(page.getByTestId("not-available")).toHaveCount(0);
  // each section links on to that reform's Summary
  for (const [sec, href] of [["adu", "#/summary"], ["middle", "#/middle/summary"], ["tod", "#/tod/summary"], ["parking", "#/parking/summary"]])
    await expect(page.getByTestId(`wt-section-${sec}`).locator(`a[href="${href}"]`)).toHaveCount(1);
  // one h1; each reform's own heading sits under its section heading
  const hs = await page.evaluate(() => [...document.querySelectorAll("main h1, main h2, main h3, main h4, main h5, main h6")].map((h) => Number(h.tagName[1])));
  expect(hs.filter((l) => l === 1)).toHaveLength(1);
  hs.forEach((l, i) => { if (i) expect(l).toBeLessThanOrEqual(hs[i - 1] + 1); });
  const overflow = await page.evaluate(() => document.documentElement.scrollWidth - document.documentElement.clientWidth);
  expect(overflow, "no sideways page scroll").toBeLessThanOrEqual(0);
  expect(errors).toEqual([]);
});
