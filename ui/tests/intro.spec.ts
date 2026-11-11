// The Introduction (landing page at the root route): the approved copy is on the page, the four 90% ranges (a table) and the
// baseline equal their sources (bundles and shared reference CSVs), the links open the right screens (the shared
// Wisconsin today page and each reform's Summary), and the Summary's "How we count" line is the intro's own.
import { readFileSync } from "node:fs";
import { expect, test, type Page } from "@playwright/test";

const REF = new URL("../../reference/", import.meta.url);
const csv = (name: string) => {
  const [head, ...lines] = readFileSync(new URL(name, REF), "utf8").trim().split(/\r?\n/);
  const cols = head.split(",");
  return lines.map((l) => Object.fromEntries(cols.map((c, i) => [c, l.split(",")[i]])));
};
const fmt = (v: number) => Math.round(v).toLocaleString("en-US");
const signed = (v: number) => (Math.round(v) < 0 ? `−${fmt(-v)}` : `+${fmt(v)}`);

async function bundle(page: Page, root: string, file: string) {
  const { run_id } = await (await page.request.get(`${root}latest.json`)).json();
  return (await page.request.get(`${root}${run_id}/${file}`)).json();
}

// The approved copy, sentence by sentence (owner-approved rev 180 with the approved parking-line change).
const COPY = [
  "Let's build some housing!",
  "If Wisconsin adopts new housing bills, how many more homes would it permit?",
  "Missing Middleware estimates how many extra homes different housing reforms could add. We study real places that already adopted each reform and compare them with places that didn’t. We test how well that comparison holds up. Then we carry what we learned to Wisconsin, and give a range of extra home permits for the first five years, assuming a law takes effect on 1 January 2027.",
  "Wisconsin, extra permits 2027–2031, 90% range",
  "ADU permits. We learned the ADU rate once a statewide law is in force from 8 states (plus 5 cities), adjusting for home values and incomes. We hid 7 of the states one at a time and predicted each from the rest: predictions ran from 12% too low to 21% too high. The range is set from the size of those misses.",
  "Homes in 2–4 unit buildings. We measured how these homes changed in the 4 states with statewide middle housing laws, each against similar places in its own region, and did the same for 10,000 groups of 4 states without a law. The reform states beat 85 of every 100 groups, short of the 95 needed to call it clear. So Wisconsin's range still includes zero: the evidence can't tell yet whether the law changes the number of these homes.",
  "Extra homes permitted near transit. We compared permits within ¼ mile of rail and rapid-bus stops in 11 places that adopted upzoning near transit. In each place, we found some stops with an upzoned apartment district nearby, and other similar stops in the same transit network that weren't rezoned. We looked at permits before and after the reforms, across both kinds of stops. The whole range is above zero, so the evidence points to extra homes permitted.",
  "Homes. We studied 74 places that repealed parking minimums for housing, each compared with similar cities that kept them, and ran fake repeals in 9,185 cities that never repealed. A range that includes zero means the data can't tell whether repealing parking minimums alone adds or removes homes.",
  "How we got there",
  "Pick a state. Wisconsin",
  "Set a baseline. We estimate what the state would permit under current law. For Wisconsin that is about 124,000 homes over 2027–2031 (90% range 56,500 to 218,865). Wisconsin Today",
  "Define each reform.",
  "Measure the effect where it really happened. We measure what happened where a reform passed, against places or years without it. The difference is our estimate of the reform's effect.",
  "Test the method.",
  "We hide data from some places and try to predict them, then check how close we got.",
  "We run placebo tests in places that never reformed by pretending they reformed in a given year. The method should find no effect there.",
  "A 90% range should hold the true answer about 9 times in 10. Where a test showed it held less often, we widened the range or say so on the page.",
  "Carry the effect to Wisconsin. We apply each measured effect to Wisconsin's own places and homes. ADU's rate adjusts for home values and incomes. Middle housing applies the same rate to every single-family home, measured in the 4 states that passed laws against similar places without them. The first year starts weak: in the 3 states with a separate first year, it averaged slightly below zero, too noisy to tell its sign. TOD and parking use one average rate, because no local trait predicted the effect better than a plain average. TOD's extra homes land only within ¼ mile of rail and rapid-bus stops.",
  "What you'll see",
  "A range for each reform, with its low and high ends. We show no single best guess, because the evidence supports a range, not a point.",
  "Side lines across each range. They give a plain reason to believe the range. Some are real cases, like the median of 8 states that passed ADU laws. Others are our earlier scenario estimates.",
  "A map of where homes might land. It shows how ADU reform spreads homes differently from TOD reform. It is an illustration, not a prediction of which lots will build.",
  "Sensitivities. Other choices that could push a range up or down. Some are reasonable alternative assumptions. Others show other ways to look at the reform that failed to pass our rigorous test design standards.",
];

test("the root address opens the Introduction with the approved copy", async ({ page }) => {
  for (const url of ["", "#", "#/"]) {
    await page.goto(url);
    await expect(page.getByTestId("intro")).toBeVisible();
  }
  await expect(page).toHaveTitle("Introduction · Missing Middleware");
  await expect(page.locator("h1")).toHaveText(COPY[0]);
  // visible text only: screen-reader suffixes on the reform links are not part of the copy
  const text = (await page.getByTestId("intro").evaluate((el) => {
    const c = el.cloneNode(true) as HTMLElement;
    c.querySelectorAll(".sr-only").forEach((s) => s.remove());
    return c.textContent ?? "";
  })).replace(/\s+/g, " ");
  for (const s of COPY) expect(text).toContain(s);
  expect(text).not.toContain("84%");
  // step 1 shows Wisconsin as plain text, no state picker
  await expect(page.getByTestId("intro-step-1").locator("select, input, [role=combobox], [role=listbox]")).toHaveCount(0);
  await expect(page.getByTestId("intro-state")).toHaveText("Wisconsin");
});

test("the ranges table: caption, headers, row order and names", async ({ page }) => {
  await page.goto("#/");
  const t = page.getByTestId("intro-range-table");
  await expect(t.locator("caption")).toHaveText("Wisconsin, extra permits 2027–2031, 90% range");
  await expect(t.locator("thead th")).toHaveText(["Reform", "Low end", "High end", "How we count"]);
  await expect(t.locator("thead th[scope=col]")).toHaveCount(4);
  await expect(t.locator("tbody th[scope=row]")).toHaveText(["ADUs by right", "Missing Middle", "TOD Upzoning", "Parking Minimum Repeal"]);
  await expect(t.locator("tbody tr")).toHaveCount(4);
  // number columns right-aligned on a wide screen (a phone stacks the rows instead)
  if ((page.viewportSize()?.width ?? 1280) > 640) for (const c of await t.locator("tbody td.num").all()) expect(await c.evaluate((el) => getComputedStyle(el).textAlign)).toBe("right");
  // no stronger-reform line
  await expect(t).not.toContainText(/stronger/i);
});

test("the four ranges and the baseline equal their sources", async ({ page }) => {
  await page.goto("#/");
  const state = await bundle(page, "runs/", "state.json");
  const tod = await bundle(page, "scenarios/tod/runs/", "statewide.json");
  const pkState = await bundle(page, "scenarios/parking/runs/", "statewide.json");
  const mid = await bundle(page, "scenarios/middle/runs/", "statewide.json");
  const ends = async (id: string) => [await page.getByTestId(`intro-${id}-low`).textContent(), await page.getByTestId(`intro-${id}-high`).textContent()];
  expect(await ends("adu")).toEqual([fmt(state.range90.low), fmt(state.range90.high)]);
  expect(await ends("tod")).toEqual([fmt(tod.range90.low), fmt(tod.range90.high)]);
  const lo = pkState.range90.low, hi = pkState.range90.high;
  expect(await ends("parking")).toEqual([signed(lo), signed(hi)]);
  expect(await ends("middle")).toEqual([signed(mid.core.lower), signed(mid.core.upper)]);
  // the copy's numbers
  expect([Math.round(state.range90.low), Math.round(state.range90.high)]).toEqual([8055, 13666]);
  expect([Math.round(tod.range90.low), Math.round(tod.range90.high)]).toEqual([3922, 16335]);
  expect([Math.round(lo), Math.round(hi)]).toEqual([-46268, 19649]);
  expect([Math.round(mid.core.lower), Math.round(mid.core.upper)]).toEqual([-482, 4515]);
  expect(mid.core.label).toBe("Homes in 2–4 unit buildings (predicted range)");
  await expect(page.getByTestId("intro-middle")).toContainText("Homes in 2–4 unit buildings.");
  // the parking bundle's high end of the evidence
  expect(pkState.scenarios.find((s: { id: string }) => s.id === "upper").additional_total).toBe(Math.round(hi));
  const central = csv("housing_baseline_statewide_by_year.csv")
    .filter((r) => r.structure_type === "all" && r.kind === "projected" && Number(r.year) >= 2027 && Number(r.year) <= 2031)
    .reduce((a, r) => a + Number(r.central), 0);
  const band = csv("housing_baseline_band.csv").find((r) => r.structure_type === "1unit")!;
  await expect(page.getByTestId("intro-baseline")).toHaveText(fmt(central));
  await expect(page.getByTestId("intro-baseline-range")).toHaveText(`${fmt(central * Number(band.low))} to ${fmt(central * Number(band.high))}`);
  expect(Math.round(central)).toBe(Math.round(tod.state_baseline_total));
  expect(Math.round(central)).toBe(Math.round(pkState.baseline_total));
});

test("the Wisconsin Today link opens the shared Wisconsin today page", async ({ page }) => {
  await page.goto("#/");
  await page.getByRole("link", { name: "Wisconsin Today", exact: true }).click();
  await expect(page).toHaveURL(/#\/wisconsin-today$/);
  await expect(page.locator("h1")).toHaveText("Wisconsin today");
  await expect(page.getByTestId("wt-baseline-total")).toBeVisible();
  await expect(page).toHaveTitle("Wisconsin today · Missing Middleware");
  // and the brand link brings the reader back to the Introduction
  await page.locator("a.brand").click();
  await expect(page.getByTestId("intro")).toBeVisible();
});

test("the reform links open each reform's page that describes the law", async ({ page }) => {
  const cases: [string, RegExp, string, string][] = [
    ["intro-link-adu", /#\/summary$/, "Accessory dwelling units", "Allowing one 600+ sq. ft. ADU (detached or semi-detached) on parcels with existing single-family buildings."],
    ["intro-link-middle", /#\/middle\/summary$/, "Missing middle housing", "Allowing 2–6 homes, up to three stories, on parcels now limited to one single-family home."],
    ["intro-link-tod", /#\/tod\/summary$/, "Transit-oriented density", "for apartments by right"],
    ["intro-link-parking", /#\/parking\/summary$/, "Parking requirement reduction", "Removing minimum parking requirements for all new housing, statewide."],
  ];
  for (const [id, url, h1, lawText] of cases) {
    await page.goto("#/");
    await page.getByTestId(id).click();
    await expect(page).toHaveURL(url);
    await expect(page.locator("h1")).toHaveText(h1);
    await expect(page.locator("main")).toContainText(lawText);
  }
});

test("reforms appear in the fixed order: ADUs, Middle housing, TOD, parking (combined is out of the picker)", async ({ page }) => {
  await page.goto("#/");
  await expect(page.getByTestId("reform-picker").locator("a[data-reform]")).toHaveCount(4);
  expect(await page.getByTestId("reform-picker").locator("a[data-reform]").evaluateAll((as) => as.map((a) => a.getAttribute("data-reform"))))
    .toEqual(["adu", "middle", "tod", "parking"]);
  expect(await page.locator(".intro-reform-links a").evaluateAll((as) => as.map((a) => a.getAttribute("data-testid"))))
    .toEqual(["intro-link-adu", "intro-link-middle", "intro-link-tod", "intro-link-parking"]);
  await expect(page.getByTestId("intro-link-middle")).toHaveText(/^Middle housing reform/);
  await expect(page.getByTestId("intro")).not.toContainText("in development");
  // the combined view's routes still work for old links
  await page.goto("#/combined/compare");
  await expect(page.locator("main h1")).toBeVisible();
});

test("the Introduction is accessible and fits a phone", async ({ page }) => {
  await page.goto("#/");
  await expect(page.getByTestId("intro")).toBeVisible();
  const dom = await page.evaluate(() => ({
    hs: [...document.querySelectorAll("h1,h2,h3,h4,h5,h6")].map((h) => Number(h.tagName[1])),
    lists: [document.querySelectorAll("[data-testid=intro] ol").length, document.querySelectorAll("[data-testid=intro] ul").length],
    tables: document.querySelectorAll("[data-testid=intro] table caption").length,
    links: [...document.querySelectorAll("main a")].map((a) => (a.textContent ?? "").trim()),
    overflow: document.documentElement.scrollWidth - document.documentElement.clientWidth,
    emoji: /\p{Extended_Pictographic}/u.test(document.querySelector("main")!.textContent ?? ""),
  }));
  expect(dom.hs[0]).toBe(1);
  expect(dom.hs.filter((l) => l === 1)).toHaveLength(1);
  dom.hs.forEach((l, i) => { if (i) expect(l).toBeLessThanOrEqual(dom.hs[i - 1] + 1); });
  expect(dom.lists[0]).toBeGreaterThanOrEqual(2);   // the steps and the sub-steps of step 5
  expect(dom.lists[1]).toBeGreaterThanOrEqual(2);   // reform links, what you'll see
  expect(dom.tables).toBe(1);                       // the ranges table, with its caption
  for (const t of dom.links) expect(t.length).toBeGreaterThan(3);
  expect(dom.overflow).toBeLessThanOrEqual(0);
  expect(dom.emoji).toBe(false);
});

test("the ranges table fits a 375 px phone with no sideways page scroll", async ({ page }) => {
  await page.setViewportSize({ width: 375, height: 812 });
  await page.goto("#/");
  await expect(page.getByTestId("intro-range-table")).toBeVisible();
  const m = await page.evaluate(() => {
    const t = document.querySelector("[data-testid=intro-range-table]")!;
    const card = t.closest(".card")!;
    return {
      page: document.documentElement.scrollWidth - document.documentElement.clientWidth,
      table: t.getBoundingClientRect().right - card.getBoundingClientRect().right,
      wrap: (t.parentElement!.scrollWidth - t.parentElement!.clientWidth),
    };
  });
  expect(m.page).toBeLessThanOrEqual(0);
  expect(m.table).toBeLessThanOrEqual(0);
  expect(m.wrap).toBeLessThanOrEqual(0);
  // each stacked cell keeps its column name
  await expect(page.getByTestId("intro-parking-low")).toHaveAttribute("data-label", "Low end");
});

test("header pills: one even row on a wide screen, a 2×2 grid on a phone, full names as accessible names", async ({ page }) => {
  await page.goto("#/");
  const nav = page.getByTestId("reform-picker");
  const geo = () => nav.evaluate((n) => {
    const ul = n.querySelector("ul")!, wrap = n.parentElement!;
    const cs = getComputedStyle(wrap), inner = wrap.clientWidth - parseFloat(cs.paddingLeft) - parseFloat(cs.paddingRight);
    return { share: ul.getBoundingClientRect().width / inner, boxes: [...ul.querySelectorAll("a")].map((a) => { const r = a.getBoundingClientRect(); return [Math.round(r.top), Math.round(r.width)]; }),
      overflow: document.documentElement.scrollWidth - document.documentElement.clientWidth };
  });
  await expect(nav.getByRole("link", { name: "Accessory dwelling units" })).toBeVisible();
  await expect(nav.getByRole("link", { name: "Missing middle housing" })).toBeVisible();
  await expect(nav.getByRole("link", { name: "Transit-oriented density" })).toBeVisible();
  await expect(nav.getByRole("link", { name: "Parking requirement reduction" })).toBeVisible();
  const g = await geo();
  expect(g.overflow).toBeLessThanOrEqual(0);
  expect(g.share).toBeGreaterThan(0.97);
  expect(g.share).toBeLessThanOrEqual(1);
  const tops = new Set(g.boxes.map((b) => b[0])), widths = g.boxes.map((b) => b[1]);
  expect(Math.max(...widths) - Math.min(...widths)).toBeLessThanOrEqual(1);   // even shares
  expect(tops.size).toBe((page.viewportSize()?.width ?? 1280) > 640 ? 1 : 2);  // one row, or a 2×2 grid on a phone
});

test("the run status strip sits below the sticky header and scrolls away", async ({ page }) => {
  await page.goto("#/middle/summary");
  const strip = page.locator(".status-strip");
  await expect(strip).toBeVisible();
  expect(await strip.evaluate((el) => !el.closest("header") && getComputedStyle(el).position === "static")).toBe(true);
  await expect(strip).not.toContainText(/in development|preview/i);
  await expect(page.getByTestId("preview-flag")).toHaveCount(0);
});

test("each reform's Summary shows the same How we count line as the Introduction's table", async ({ page }) => {
  await page.goto("#/");
  const lines: Record<string, string> = {};
  for (const id of ["adu", "middle", "tod", "parking"]) lines[id] = ((await page.getByTestId(`intro-${id}`).locator("td.intro-how").textContent()) ?? "").trim();
  for (const [id, pre] of [["adu", ""], ["middle", "/middle"], ["tod", "/tod"], ["parking", "/parking"]]) {
    await page.goto(`#${pre}/summary`);
    await expect(page.getByTestId("summary-how")).toHaveText(`How we count. ${lines[id]}`);
  }
});
