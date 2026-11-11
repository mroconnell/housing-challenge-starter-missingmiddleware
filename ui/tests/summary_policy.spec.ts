// The Summary tab's policy box, full-width chart and "Enlarge chart" overlay (owner, 2026-11-11), for all four reforms.
// The benchmark quotes are the handbook's words (Participant Handbook, "Benchmark Policy Scenarios", page 3), typed
// here as read from the PDF so a change to ui/src/benchmarks.ts fails this test; tests/test_handbook_benchmarks.py
// checks the same strings against the PDF text itself. "What we modeled" is read from where each reform states it.
import { readFileSync } from "node:fs";
import { expect, test, type Page } from "@playwright/test";

const HANDBOOK: Record<string, string> = {
  adu: "Model the effect of allowing one ADU on parcels with existing single-family buildings. Assume detached and semi-detached ADUs of at least 600 square feet are allowed, and no additional parking is required.",
  middle: "Model the effect of allowing 2–6 dwelling units on parcels currently restricted to single-family use, with building heights up to three stories. … Teams may assume that setback and lot coverage requirements do not constrain the development of 2–6 units on a parcel currently restricted to single-family use.",
  tod: "Model the effect of increasing allowable residential density near major transit stops through higher building heights and/or increased floor area ratios. Teams should define major transit stops and justify their transit proximity threshold. Teams may assume that parking requirements are reduced or eliminated.",
  parking: "Model the effects of reducing or eliminating minimum parking requirements for new residential development. Specify assumptions about developer-provided parking in the absence of mandates.",
};
const PRE: Record<string, string> = { adu: "", middle: "/middle", tod: "/tod", parking: "/parking" };

const src = (p: string) => readFileSync(new URL(`../src/${p}`, import.meta.url), "utf8");
const constString = (file: string, name: string) => {
  const m = src(file).match(new RegExp(`export const ${name} = "([^"]+)";`));
  if (!m) throw new Error(`${name} not found in ${file}`);
  return m[1];
};

async function json(page: Page, root: string, file: string) {
  const { run_id } = await (await page.request.get(`${root}latest.json`)).json();
  return (await page.request.get(`${root}${run_id}/${file}`)).json();
}

/** The "What we modeled" text each reform should show, from the same sources the screens use. */
async function modeled(page: Page, id: string): Promise<string[]> {
  if (id === "adu") return [constString("app.ts", "LAW_TEXT")];
  if (id === "middle") return [constString("scenarios/middle/index.ts", "MIDDLE_LAW_TEXT")];
  if (id === "tod") {
    const s = await json(page, "scenarios/tod/runs/", "statewide.json");
    return [s.district.text, `A major transit stop here is a rail or rapid-bus stop, and the proximity threshold is ${s.district.radius}`];
  }
  const m = await json(page, "scenarios/parking/runs/", "manifest.json");
  const w = await json(page, "scenarios/parking/runs/", "why.json");
  const ss = (w.developer_parking as string).split(/(?<=\.)\s+(?=[A-Z])/);
  return [`${m.dates.effective}: it removes minimum parking requirements for all housing.`, ss[0], ss[ss.length - 1]];
}

for (const id of ["adu", "middle", "tod", "parking"]) {
  test(`${id} Summary: "The policy" shows the handbook's benchmark and what we modeled`, async ({ page }) => {
    await page.goto(`#${PRE[id]}/summary`);
    const box = page.getByTestId("summary-policy");
    await expect(box.getByRole("heading", { name: "The policy" })).toBeVisible();
    const bench = box.getByTestId("policy-benchmark");
    await expect(bench.getByRole("heading", { name: "The challenge's benchmark" })).toBeVisible();
    await expect(bench.getByTestId("policy-quote")).toHaveText(`“${HANDBOOK[id]}”`);
    await expect(bench.getByTestId("policy-source")).toContainText("Participant Handbook");
    await expect(bench.getByTestId("policy-source")).toContainText("Benchmark Policy Scenarios");
    const mod = box.getByTestId("policy-modeled");
    await expect(mod.getByRole("heading", { name: "What we modeled" })).toBeVisible();
    for (const t of await modeled(page, id)) await expect(mod).toContainText(t);
    if (id === "tod") await expect(mod).toContainText("The Hop");
    // near the top: before the 90% range card
    const order = await page.locator("[data-testid=summary-policy], [data-testid=summary-range]").evaluateAll((els) => els.map((e) => e.getAttribute("data-testid")));
    expect(order).toEqual(["summary-policy", "summary-range"]);
  });

  test(`${id} Summary: the chart spans the main container, prose stays at a reading measure`, async ({ page, isMobile }) => {
    await page.goto(`#${PRE[id]}/summary`);
    await expect(page.locator("#sum-chart svg")).toBeVisible();
    const w = await page.evaluate(() => {
      const wrap = document.querySelector("main .wrap, main") as HTMLElement;
      const cs = getComputedStyle(wrap);
      const inner = wrap.clientWidth - parseFloat(cs.paddingLeft) - parseFloat(cs.paddingRight);
      return {
        inner,
        card: document.querySelector(".summary-chart-card")!.getBoundingClientRect().width,
        svg: Number(document.querySelector("#sum-chart svg")!.getAttribute("width")),
        prose: document.querySelector("[data-testid=summary-range]")!.getBoundingClientRect().width,
        overflow: document.documentElement.scrollWidth - document.documentElement.clientWidth,
      };
    });
    expect(w.overflow, "no sideways page scroll").toBeLessThanOrEqual(0);
    expect(Math.abs(w.card - w.inner), "chart card fills the main container").toBeLessThanOrEqual(2);
    if (!isMobile) {
      expect(w.card).toBeGreaterThan(1100);
      expect(w.svg).toBeGreaterThan(1000);
      expect(w.prose, "prose card keeps a reading measure").toBeLessThan(900);
    }
  });
}

test("Enlarge chart: a full-window dialog with the same chart, toggles and popups; Escape closes and focus returns", async ({ page, isMobile }) => {
  const errors: string[] = [];
  page.on("pageerror", (e) => errors.push(String(e)));
  const tod = await json(page, "scenarios/tod/runs/", "statewide.json");
  const lines = (tod.side_lines as { id: string; label: string; value?: number; note: string; where: string }[]).filter((s) => s.where === "chart" && s.value !== undefined);
  await page.goto("#/tod/summary?show=extra");
  const btn = page.getByTestId("summary-enlarge");
  const dlg = page.getByTestId("summary-dialog");
  await expect(dlg).toBeHidden();
  await btn.click();
  await expect(dlg).toBeVisible();
  // focus moves into the dialog
  await expect(page.getByTestId("summary-dialog-close")).toBeFocused();
  // the same toggles: extra homes only, so no current-law band
  await expect(page.getByTestId("summary-dialog-state")).toContainText("Chart shows: extra homes only");
  const big = page.locator("#sum-chart-big svg");
  await expect(big).toBeVisible();
  await expect(big.locator('path[data-band="range90"]')).toHaveCount(1);
  await expect(big.locator('path[data-band="current-law"]')).toHaveCount(0);
  await expect(page.getByTestId("summary-legend-big")).toContainText("Current law: the zero line");
  // larger than the page chart, and fits the window
  const sz = await page.evaluate(() => ({
    big: [Number(document.querySelector("#sum-chart-big svg")!.getAttribute("width")), Number(document.querySelector("#sum-chart-big svg")!.getAttribute("height"))],
    small: [Number(document.querySelector("#sum-chart svg")!.getAttribute("width")), Number(document.querySelector("#sum-chart svg")!.getAttribute("height"))],
    vw: window.innerWidth,
  }));
  expect(sz.big[0]).toBeGreaterThanOrEqual(sz.small[0]);
  expect(sz.big[1]).toBeGreaterThan(sz.small[1]);
  expect(sz.big[0]).toBeLessThan(sz.vw);
  // popups work in the dialog: a year and a side line
  const pop = page.getByTestId("summary-popup-big");
  await big.locator('rect.sum-hit-year[data-year="2029"]').dispatchEvent("pointerover");
  await expect(pop).toBeVisible();
  await expect(pop).toHaveAttribute("data-year", "2029");
  await expect(page.getByTestId("summary-crosshair-big")).toHaveAttribute("visibility", "visible");
  await expect(pop.getByTestId("pop-current-law")).toHaveText("0");
  const s = lines[0];
  await big.locator(`circle.sum-hit-side[data-side="${s.id}"][data-year="2031"]`).dispatchEvent("pointerover");
  await expect(pop.getByTestId("pop-side-note")).toHaveText(s.note);
  if (!isMobile) {
    // a real mouse over the enlarged chart
    const rect = big.locator('rect.sum-hit-year[data-year="2030"]');
    const box = (await rect.boundingBox())!;
    await page.mouse.move(box.x + box.width / 2, box.y + 4);
    await expect(pop).toHaveAttribute("data-year", "2030");
    // keyboard: the dialog's year buttons
    await page.getByTestId("summary-years-big").locator('.sum-year[data-year="2027"]').focus();
    await expect(pop).toHaveAttribute("data-year", "2027");
  }
  // Escape closes; focus returns to the button
  await page.keyboard.press("Escape");
  await expect(dlg).toBeHidden();
  await expect(btn).toBeFocused();
  await expect(page.locator("#sum-chart-big")).toHaveCount(0);
  // the Close button also closes it
  await btn.click();
  await expect(dlg).toBeVisible();
  await page.getByTestId("summary-dialog-close").click();
  await expect(dlg).toBeHidden();
  await expect(btn).toBeFocused();
  expect(errors).toEqual([]);
});

for (const id of ["adu", "middle", "parking"]) {
  test(`${id} Enlarge chart opens and closes with Escape`, async ({ page }) => {
    await page.goto(`#${PRE[id]}/summary?per=1000`);
    await page.getByTestId("summary-enlarge").click();
    await expect(page.getByTestId("summary-dialog")).toBeVisible();
    await expect(page.getByTestId("summary-dialog-state")).toContainText("per 1,000 Wisconsin homes");
    await expect(page.locator("#sum-chart-big svg")).toBeVisible();
    await page.keyboard.press("Escape");
    await expect(page.getByTestId("summary-dialog")).toBeHidden();
    await expect(page.getByTestId("summary-enlarge")).toBeFocused();
  });
}

// ---- owner, 2026-11-11 19:41: range lead-in, chart headings, side-lines toggle, ADU legend labels ------------------
const HEADING: Record<string, string> = {
  adu: "ADU permits each year, 2027–2031",
  middle: "Homes in 2–4 unit buildings each year, 2027–2031",
  tod: "Homes permitted near major transit stops each year, 2027–2031",
  parking: "Homes permitted each year, 2027–2031",
};

for (const id of ["adu", "middle", "tod", "parking"]) {
  test(`${id} Summary: "Our estimate is between:", the chart heading, and side lines show / hide`, async ({ page }) => {
    await page.goto(`#${PRE[id]}/summary`);
    const card = page.getByTestId("summary-range");
    await expect(card.getByRole("heading")).toHaveCount(0);
    await expect(page.locator("main")).not.toContainText("The 90% range, 2027–2031");
    await expect(card.locator(".range-lead")).toHaveText("Our estimate is between:");
    await expect(card).toContainText("Low end");
    await expect(card).toContainText("High end");
    await expect(card.getByTestId("range-unit")).toContainText("(90% range)");
    await expect(page.locator("#sum-chart-h")).toHaveText(HEADING[id]);
    // side lines: shown by default, hidden with lines=off; the band, current law and their legend entries stay
    const svg = page.locator("#sum-chart svg");
    const lines = page.getByTestId("toggle-lines");
    await expect(lines.getByLabel("Show")).toBeChecked();
    expect(await svg.locator('path[data-series^="side-"]').count()).toBeGreaterThan(0);
    await lines.getByLabel("Hide").check();
    await expect(page).toHaveURL(/lines=off/);
    await expect(svg.locator('path[data-series^="side-"]')).toHaveCount(0);
    await expect(svg.locator(".sum-hit-side")).toHaveCount(0);
    await expect(svg.locator('path[data-band="range90"]')).toHaveCount(1);
    await expect(svg.locator('path[data-band="current-law"]')).toHaveCount(1);
    await expect(svg.locator('path[data-series="current-law"]')).toHaveCount(1);
    const legend = page.getByTestId("summary-legend");
    await expect(legend.locator("li")).toHaveCount(2);
    await expect(legend).toContainText("Current law");
    await expect(legend).toContainText("With the law: 90% range");
    await page.reload();
    await expect(page.getByTestId("toggle-lines").getByLabel("Hide")).toBeChecked();
    await page.getByTestId("toggle-lines").getByLabel("Show").check();
    await expect(page).not.toHaveURL(/lines=off/);
    expect(await page.locator('#sum-chart svg path[data-series^="side-"]').count()).toBeGreaterThan(0);
  });
}

test("ADU Summary legend: the owner's labels, numbers from the bundle, no Typical adoption line", async ({ page }) => {
  const st = await json(page, "runs/", "state.json");
  const v = (id: string) => (st.side_lines as { id: string; value: number }[]).find((s) => s.id === id)!.value;
  const n = (x: number) => Math.round(x).toLocaleString("en-US");
  await page.goto("#/summary");
  const items = page.getByTestId("summary-legend").locator("li");
  await expect(items).toHaveText([
    "Current law (ADU permits without statewide reform)",
    `With the law: 90% range, ${n(st.range90.low)} to ${n(st.range90.high)} extra ADU permits (on top of current law)`,
    `Median path of the 8 statewide-law states: ${n(v("median8"))}`,
    `Two slowest statewide-law states (Rhode Island and Oregon, averaged): ${n(v("slow2"))}`,
    `Like California (the fastest statewide-law state): ${n(v("like_california"))}`,
  ]);
  expect([n(st.range90.low), n(st.range90.high), n(v("median8")), n(v("slow2")), n(v("like_california"))]).toEqual(["8,055", "13,666", "10,038", "6,321", "19,790"]);
  await expect(page.locator('#sum-chart svg path[data-series="side-typical"]')).toHaveCount(0);
  // the popups keep the bundle's notes
  const slow = (st.side_lines as { id: string; note: string }[]).find((s) => s.id === "slow2")!;
  await page.locator('#sum-chart circle.sum-hit-side[data-side="slow2"][data-year="2031"]').dispatchEvent("pointerover");
  await expect(page.getByTestId("summary-popup").getByTestId("pop-side-note")).toHaveText(slow.note);
  // Typical adoption stays listed on How sure → Details, with the bundle's own label
  const typ = (st.side_lines as { id: string; label: string }[]).find((s) => s.id === "typical")!;
  await page.goto("#/how-sure");
  await expect(page.getByTestId("summary-hidden-lines")).toContainText(`${typ.label}: ${n(v("typical"))}`);
  await expect(page.getByTestId("summary-hidden-lines")).toContainText("The 90% range is built around typical adoption.");
});
