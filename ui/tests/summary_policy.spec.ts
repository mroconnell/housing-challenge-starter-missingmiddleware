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

// Owner 2026-11-11 20:05 (ADU) and 20:23 (all four): "The policy" holds only the owner's text; no opening sentence;
// what we modeled and the handbook's benchmark sit in one card under the chart, before the row of links. On wide
// screens "The policy" and the range card share one row (20:21).
const ADU_POLICY = "Allowing one 600+ sq. ft. ADU (detached or semi-detached) on parcels with existing single-family buildings. No additional parking is required. No owner-occupant requirement.";

/** The owner's policy text for each reform; TOD's numbers are read from its bundle's district fields. */
async function policyText(page: Page, id: string): Promise<string> {
  if (id === "adu") return ADU_POLICY;
  if (id === "middle") return constString("scenarios/middle/index.ts", "MIDDLE_POLICY_TEXT");
  if (id === "parking") return constString("scenarios/parking/index.ts", "PARKING_POLICY_TEXT");
  const d = (await json(page, "scenarios/tod/runs/", "statewide.json")).district;
  return `Requiring every Wisconsin city with rail or rapid-bus stops to zone ${Math.round(d.share * 100)}% of the land within ${d.radius} of those stops for apartments by right, at least ${d.min_homes_per_acre} homes per acre.`;
}

for (const id of ["adu", "middle", "tod", "parking"]) {
  test(`${id} Summary: the owner's policy text, then range, chart, what we modeled with the benchmark, links`, async ({ page }) => {
    await page.goto(`#${PRE[id]}/summary`);
    const policy = await policyText(page, id);
    const box = page.getByTestId("summary-policy");
    await expect(box.getByRole("heading")).toHaveText(["The policy"]);
    await expect(box.getByTestId("policy-text")).toHaveText(policy);
    // nothing else in the box
    expect((await box.innerText()).replace(/\s+/g, " ").trim()).toBe(`The policy ${policy}`);
    await expect(box.getByTestId("policy-benchmark")).toHaveCount(0);
    await expect(box.getByTestId("policy-modeled")).toHaveCount(0);
    await expect(page.getByTestId("summary-sentence")).toHaveCount(0);
    await expect(page.locator("main")).not.toContainText("If Wisconsin ");
    // the card under the chart: what we modeled, then the handbook's benchmark
    const card = page.getByTestId("summary-modeled");
    const mod = card.getByTestId("policy-modeled");
    await expect(mod.getByRole("heading", { name: "What we modeled" })).toBeVisible();
    for (const t of await modeled(page, id)) await expect(mod).toContainText(t);
    if (id === "tod") await expect(mod).toContainText("The Hop");
    const bench = card.getByTestId("policy-benchmark");
    await expect(bench.getByRole("heading", { name: "The challenge's benchmark" })).toBeVisible();
    await expect(bench.getByTestId("policy-quote")).toHaveText(`“${HANDBOOK[id]}”`);
    await expect(bench.getByTestId("policy-source")).toContainText("Participant Handbook");
    await expect(bench.getByTestId("policy-source")).toContainText("Benchmark Policy Scenarios");
    const parts = await card.locator("[data-testid^=policy-]").evaluateAll((els) => els.filter((e) => e.classList.contains("policy-part")).map((e) => e.getAttribute("data-testid")));
    expect(parts).toEqual(["policy-modeled", "policy-benchmark"]);
    // order: heading, the policy + estimate row (policy first), chart, what we modeled, links
    const top = page.getByTestId("summary-top");
    expect(await top.locator(":scope > section").evaluateAll((els) => els.map((e) => e.getAttribute("data-testid")))).toEqual(["summary-policy", "summary-range"]);
    const order = await page.locator("article.summary-page > :is(h1, [data-testid=summary-top], .summary-chart-card, [data-testid=summary-modeled], [data-testid=summary-links])")
      .evaluateAll((els) => els.map((e) => e.getAttribute("data-testid") ?? (e.classList.contains("summary-chart-card") ? "chart" : e.tagName.toLowerCase())));
    expect(order).toEqual(["h1", "summary-top", "chart", "summary-modeled", "summary-links"]);
    // nothing else visible below the chart but this card and the links (the dialog is closed)
    const after = await page.locator("article.summary-page > .summary-chart-card ~ *").evaluateAll((els) => els.filter((e) => (e as HTMLElement).offsetParent !== null).map((e) => e.getAttribute("data-testid")));
    expect(after).toEqual(["summary-modeled", "summary-links"]);
    // the link to the list of places: ADU and parking have one on Why; middle housing and TOD do not (yet)
    const scope = card.getByTestId("summary-scope-link");
    if (id === "adu") {
      await expect(scope).toHaveText("For the full list of states and cities included in or excluded from the model, see Why → In and out of the model →");
      await expect(scope.locator("a")).toHaveAttribute("href", "#/why?section=adu-in-out");
    } else if (id === "parking") {
      await expect(scope).toHaveText("For the full list of the 74 places that removed parking minimums and were studied, see Why → All 74 places →");
      await expect(scope.locator("a")).toHaveAttribute("href", "#/parking/why?section=parking-places");
    } else if (id === "tod") {
      await expect(scope).toHaveText("For the 11 places behind the range, and the places left out, see Why → In and out of the model →");
      await expect(scope.locator("a")).toHaveAttribute("href", "#/tod/why?section=tod-in-out");
    } else await expect(scope).toHaveCount(0);
  });

  test(`${id} Summary: policy and estimate side by side at 1280 px, stacked at 375 px with no sideways scroll`, async ({ page }) => {
    const boxes = async () => page.evaluate(() => {
      const r = (t: string) => document.querySelector(`[data-testid=${t}]`)!.getBoundingClientRect();
      const p = r("summary-policy"), e = r("summary-range");
      return { p: { x: p.left, y: p.top, w: p.width, h: p.height, b: p.bottom }, e: { x: e.left, y: e.top, w: e.width, h: e.height }, overflow: document.documentElement.scrollWidth - document.documentElement.clientWidth };
    });
    await page.setViewportSize({ width: 1280, height: 900 });
    await page.goto(`#${PRE[id]}/summary`);
    await expect(page.getByTestId("summary-range")).toBeVisible();
    const wide = await boxes();
    expect(Math.abs(wide.p.y - wide.e.y), "same row").toBeLessThanOrEqual(1);
    expect(wide.e.x, "estimate to the right of the policy").toBeGreaterThan(wide.p.x + wide.p.w);
    expect(wide.p.w, "policy narrower than the estimate").toBeLessThan(wide.e.w);
    expect(Math.abs(wide.p.h - wide.e.h), "equal heights").toBeLessThanOrEqual(1);
    expect(wide.overflow).toBeLessThanOrEqual(0);
    await page.setViewportSize({ width: 375, height: 812 });
    await page.reload();
    await expect(page.getByTestId("summary-range")).toBeVisible();
    const narrow = await boxes();
    expect(narrow.e.y, "estimate below the policy").toBeGreaterThanOrEqual(narrow.p.b);
    expect(Math.abs(narrow.p.x - narrow.e.x)).toBeLessThanOrEqual(1);
    expect(Math.abs(narrow.p.w - narrow.e.w), "both full width").toBeLessThanOrEqual(1);
    expect(narrow.overflow, "no sideways page scroll at 375 px").toBeLessThanOrEqual(0);
  });
}

// ADU Why: the in/out list is the bundle's state.json evidence_scope: 13 in (8 states that set the statewide level,
// 5 cities for the law and local-rules terms only) and 15 out (10 states, then 5 places), each with its reason.
test("ADU Why: In and out of the model lists 13 places in (8 states, 5 cities) and 15 out, from evidence_scope", async ({ page }) => {
  await page.goto("#/why");
  const box = page.locator("#adu-in-out");
  await expect(box).toBeVisible();
  await expect(box.getByRole("heading", { level: 2 })).toHaveText("In and out of the model");
  const sc = (await json(page, "runs/", "state.json")).evidence_scope as { in: { name: string; kind: string; role: string }[]; out: { name: string; kind: string }[]; source: string };
  expect(sc.in).toHaveLength(13);
  expect(sc.out).toHaveLength(15);
  const states = sc.in.filter((x) => x.kind === "state");
  expect(states.map((x) => x.name).sort()).toEqual(["California", "Maine", "Massachusetts", "Oregon", "Rhode Island", "Utah", "Vermont", "Washington"]);
  await expect(box.getByTestId("in-states").locator("li")).toHaveCount(8);
  for (const s of states) await expect(box.getByTestId("in-states")).toContainText(`${s.name}:`);
  for (const s of states) expect(s.role).toBe("sets the statewide level");
  const cities = box.getByTestId("in-cities");
  await expect(cities.locator("li")).toHaveCount(5);
  for (const c of ["Seattle", "Portland", "Austin", "Denver", "Minneapolis"]) await expect(cities).toContainText(c);
  for (const t of await cities.locator("li").allInnerTexts()) expect(t).toContain("law and local-rules terms only");
  const out = box.getByTestId("out-places");
  await expect(out.locator("li")).toHaveCount(15);
  expect(sc.out.slice(0, 10).every((x) => x.kind === "state")).toBe(true);
  for (const s of ["Montana", "Arizona", "Colorado", "Arkansas", "Iowa", "New Hampshire", "Connecticut", "Hawaii", "Maryland", "Nevada", "Tucson", "Spokane", "Honolulu", "Montgomery County", "Bozeman"]) await expect(out).toContainText(s);
  for (const t of await out.locator("li").allInnerTexts()) expect(t).toMatch(/^.+: .+$/);
  await expect(box.getByTestId("in-out-source")).toHaveText(`Source: ${sc.source}`);
  await expect(box.getByTestId("madison-like-check")).toContainText("A check, not used for the rate");
});

test("ADU Summary link opens Why at the in/out list", async ({ page }) => {
  await page.goto("#/summary");
  await page.getByTestId("summary-scope-link").locator("a").click();
  await expect(page).toHaveURL(/#\/why\?section=adu-in-out$/);
  await expect(page.locator("#adu-in-out")).toBeInViewport();
});

// The TOD Why card: the 11 D-11 places (effects average 33.54 extra homes per 100 lot acres a year, the central's
// per-acre effect), the 5 edge-check places, and the places left out with a reason each.
test("TOD Why: In and out of the model lists 11 places averaging 33.54, 5 edge places, and the places left out", async ({ page }) => {
  await page.goto("#/tod/why");
  const box = page.locator("#tod-in-out");
  await expect(box).toBeVisible();
  await expect(box.getByRole("heading", { level: 2 })).toHaveText("In and out of the model");
  const why = await json(page, "scenarios/tod/runs/", "why.json");
  const effects = (why.in_out.places as { effect: number }[]).map((p) => p.effect);
  expect(effects).toHaveLength(11);
  expect((effects.reduce((a, b) => a + b, 0) / 11).toFixed(2)).toBe("33.54");
  await expect(box.getByTestId("tod-in-places").locator("tbody tr")).toHaveCount(11);
  await expect(box.getByTestId("tod-in-mean")).toHaveText("+33.54");
  for (const n of ["New York", "Philadelphia", "Austin 2009", "Charlotte 2019", "Chicago 2015", "Denver 2018", "Portland 2020", "Seattle Mount Baker 2014", "Seattle Othello 2012", "Salt Lake City 2010", "Saint Paul 2011"])
    await expect(box.getByTestId("tod-in-places")).toContainText(n);
  const edge = box.getByTestId("tod-edge-places").locator("li");
  await expect(edge).toHaveCount(5);
  expect((await edge.allInnerTexts()).map((t) => t.split(":")[0])).toEqual(["Philadelphia", "Austin 2009", "Chicago 2015", "Denver 2018", "Saint Paul 2011"]);
  const out = box.getByTestId("tod-out-places");
  for (const n of ["Los Angeles TOC 2017", "San Diego 2021", "Chicago 2022", "Bellevue BelRed 2009", "Honolulu 2017", "Seattle Roosevelt 2012", "Madison", "Toronto", "Ottawa"])
    await expect(out).toContainText(n);
  for (const t of await out.locator("li").allInnerTexts()) expect(t).toMatch(/^.+: .+$/);
});

test("TOD Summary link opens Why at the in/out card", async ({ page }) => {
  await page.goto("#/tod/summary");
  await page.getByTestId("summary-scope-link").locator("a").click();
  await expect(page).toHaveURL(/#\/tod\/why\?section=tod-in-out$/);
  await expect(page.locator("#tod-in-out")).toBeInViewport();
});

test("parking Summary link opens Why with the list of 74 places open", async ({ page }) => {
  await page.goto("#/parking/summary");
  await page.getByTestId("summary-scope-link").locator("a").click();
  await expect(page).toHaveURL(/#\/parking\/why\?section=parking-places$/);
  const list = page.locator("details#parking-places");
  await expect(list).toHaveAttribute("open", "");
  await expect(list.getByTestId("why-places").locator("tbody tr")).toHaveCount(74);
  await expect(list).toBeInViewport();
});

for (const id of ["adu", "middle", "tod", "parking"]) {
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
    `Like OR & RI (lowest statewide adoption): ${n(v("slow2"))}`,
    `Like CA (highest statewide adoption): ${n(v("like_california"))}`,
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

// Summary chart key (owner, 2026-11-11 20:37): one item per row at every width, every swatch the same width, so every
// label starts at the same x; on the page and in the enlarged chart, at 1280 and 375 px.
for (const id of ["adu", "middle", "tod", "parking"]) {
  test(`${id} Summary: chart key has one item per row and its labels line up, page and enlarged, 1280 and 375 px`, async ({ page }) => {
    const measure = (tid: string) => page.evaluate((t) => {
      const items = [...document.querySelectorAll(`[data-testid=${t}] > li`)];
      return items.map((li) => {
        const sw = li.querySelector("svg")!;
        const txt = sw.nextSibling!;
        const r = document.createRange(); r.selectNodeContents(txt);
        const box = li.getBoundingClientRect();
        return { label: r.getClientRects()[0].left, sw: sw.getBoundingClientRect().width, top: box.top, bottom: box.bottom };
      });
    }, tid);
    const check = (rows: { label: number; sw: number; top: number; bottom: number }[]) => {
      expect(rows.length).toBeGreaterThanOrEqual(2);
      for (const r of rows) {
        expect(Math.abs(r.label - rows[0].label), "label left edges equal").toBeLessThanOrEqual(0.5);
        expect(r.sw, "swatch 36 px").toBeCloseTo(36, 0);
      }
      for (let i = 1; i < rows.length; i++) expect(rows[i].top, "one item per row").toBeGreaterThanOrEqual(rows[i - 1].bottom - 0.5);
    };
    for (const width of [1280, 375]) {
      await page.setViewportSize({ width, height: 900 });
      await page.goto(`#${PRE[id]}/summary`);
      await expect(page.getByTestId("summary-legend")).toBeVisible();
      check(await measure("summary-legend"));
      await page.getByTestId("summary-enlarge").click();
      await expect(page.getByTestId("summary-legend-big")).toBeVisible();
      check(await measure("summary-legend-big"));
      await page.keyboard.press("Escape");
    }
  });
}
