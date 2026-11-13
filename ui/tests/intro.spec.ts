// The Introduction (landing page at the root route): the approved copy is on the page (owner changes of 2026-11-12:
// no ranges table, five short steps, four new "What you'll see" bullets), the baseline equals its sources (shared
// reference CSVs), and the links open the right screens (the shared Wisconsin today page and each reform's Summary).
// The ranges moved to each reform's Brief tab: ui/tests/brief_estimate.spec.ts.
import { readFileSync } from "node:fs";
import { expect, test, type Page } from "@playwright/test";

const REF = new URL("../../reference/", import.meta.url);
const csv = (name: string) => {
  const [head, ...lines] = readFileSync(new URL(name, REF), "utf8").trim().split(/\r?\n/);
  const cols = head.split(",");
  return lines.map((l) => Object.fromEntries(cols.map((c, i) => [c, l.split(",")[i]])));
};
const fmt = (v: number) => Math.round(v).toLocaleString("en-US");

async function bundle(page: Page, root: string, file: string) {
  const { run_id } = await (await page.request.get(`${root}latest.json`)).json();
  return (await page.request.get(`${root}${run_id}/${file}`)).json();
}

// The approved copy, word for word (rev 180, as changed by the owner on 2026-11-12).
const COPY = [
  "What would housing reforms mean for new home permits in Wisconsin?",
  "Missing Middleware estimates how different housing reforms would change the number of homes Wisconsin permits. We study real places that already adopted each reform and compare them to places that didn’t. We use what we learn to build a model and apply it to Wisconsin. The result is a range of extra home permits over the first five years after each reform, assuming the law takes effect on January 1, 2027.",
  "What you'll see",
  "How we got there",
];
const STEPS = [
  "Pick a state. Wisconsin",
  "Set a baseline in Wisconsin. We estimate what the state would permit under current law. For Wisconsin that is about 124,000 homes over 2027–2031 (projected range, 90%: 56,500 to 218,865). Wisconsin Today",
  "Define the proposed policies. ADU reform: the modelled law and what it adds Middle housing reform: what the modelled law adds TOD reform: the modelled law and the homes near transit today",
  "Look at cities and states outside Wisconsin to measure the effect of each proposed policy. Compare places where the reforms passed, and places that did not reform.",
  "Carry the effect to Wisconsin. We apply each measured effect to Wisconsin, producing a range of new permits we expect to see from each policy.",
];
const SEE = [
  "How many permits we expect from each reform, with a low and high end.",
  "Comparison scenarios plotted across the timeline, in addition to our projected range.",
  "A map showing where the extra homes might go across Wisconsin.",
  "Sensitivity charts that show the biggest factors in our projected range, and charts that show how other ways of estimating compare.",
];
const LINKS: [string, string, RegExp][] = [
  ["intro-link-adu", "ADU reform: the modelled law and what it adds", /#\/summary$/],
  ["intro-link-middle", "Middle housing reform: what the modelled law adds", /#\/middle\/summary$/],
  ["intro-link-tod", "TOD reform: the modelled law and the homes near transit today", /#\/tod\/summary$/],
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
  // exactly five steps and four bullets, word for word; the carousel stays under the list
  const norm = (xs: string[]) => xs.map((x) => x.replace(/\s+/g, " ").trim());
  expect(norm(await page.locator(".intro-steps > li").allTextContents())).toEqual(STEPS);
  expect(norm(await page.locator(".intro-see > li").allTextContents())).toEqual(SEE);
  // the old table and the dropped steps are gone
  await expect(page.getByTestId("intro-range-table")).toHaveCount(0);
  await expect(page.getByTestId("intro").locator("table")).toHaveCount(0);
  for (const gone of ["Wisconsin, extra permits 2027–2031, 90% range", "Measure the effect where it really happened", "Test the method", "How we count", "Side lines"]) expect(text).not.toContain(gone);
  // step 1 shows Wisconsin as plain text, no state picker
  await expect(page.getByTestId("intro-step-1").locator("select, input, [role=combobox], [role=listbox]")).toHaveCount(0);
  await expect(page.getByTestId("intro-state")).toHaveText("Wisconsin");
});

test("the baseline equals its sources (no reform ranges on the Introduction)", async ({ page }) => {
  await page.goto("#/");
  const tod = await bundle(page, "scenarios/tod/runs/", "statewide.json");
  const central = csv("housing_baseline_statewide_by_year.csv")
    .filter((r) => r.structure_type === "all" && r.kind === "projected" && Number(r.year) >= 2027 && Number(r.year) <= 2031)
    .reduce((a, r) => a + Number(r.central), 0);
  const band = csv("housing_baseline_band.csv").find((r) => r.structure_type === "1unit")!;
  await expect(page.getByTestId("intro-baseline")).toHaveText(fmt(central));
  await expect(page.getByTestId("intro-baseline-range")).toHaveText(`${fmt(central * Number(band.low))} to ${fmt(central * Number(band.high))}`);
  expect([Math.round(central), Math.round(central * Number(band.low)), Math.round(central * Number(band.high))]).toEqual([124000, 56500, 218865]);
  expect(Math.round(central)).toBe(Math.round(tod.state_baseline_total));
  for (const id of ["adu", "middle", "tod", "parking"]) await expect(page.getByTestId(`intro-${id}-low`)).toHaveCount(0);
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

test("step 3's links, in order, word for word, each open that reform's Summary describing the law", async ({ page }) => {
  await page.goto("#/");
  const step3 = page.getByTestId("intro-step-3");
  expect((await step3.locator("a").allTextContents()).map((t) => t.trim())).toEqual(LINKS.map((l) => l[1]));
  const cases: Record<string, [string, string]> = {
    "intro-link-adu": ["Accessory dwelling units", "Allowing one ADU (detached or semi-detached) on parcels with existing single-family buildings."],
    "intro-link-middle": ["Missing middle housing", "Allowing 2–6 homes, up to three stories, on parcels now limited to one single-family home."],
    "intro-link-tod": ["Transit-oriented density", "for apartments by right"],
  };
  for (const [id, name, url] of LINKS) {
    await page.goto("#/");
    await expect(page.getByTestId(id)).toHaveText(name);
    await page.getByTestId(id).click();
    await expect(page).toHaveURL(url);
    await expect(page.getByTestId("summary")).toBeVisible();
    await expect(page.locator("h1")).toHaveText(cases[id][0]);
    await expect(page.locator("main")).toContainText(cases[id][1]);
  }
});

test("reforms appear in the fixed order: ADUs, Middle housing, TOD (parking is off the tool)", async ({ page }) => {
  await page.goto("#/");
  await expect(page.getByTestId("reform-picker").locator("a[data-reform]")).toHaveCount(3);
  expect(await page.getByTestId("reform-picker").locator("a[data-reform]").evaluateAll((as) => as.map((a) => a.getAttribute("data-reform"))))
    .toEqual(["adu", "middle", "tod"]);
  // the three pills stay on one row at desktop width
  const tops = await page.getByTestId("reform-picker").locator("a[data-reform]").evaluateAll((as) => as.map((a) => Math.round(a.getBoundingClientRect().top)));
  expect(new Set(tops).size).toBe(1);
  expect(await page.locator(".intro-reform-links a").evaluateAll((as) => as.map((a) => a.getAttribute("data-testid"))))
    .toEqual(["intro-link-adu", "intro-link-middle", "intro-link-tod"]);
  await expect(page.getByTestId("intro-link-middle")).toHaveText(/^Middle housing reform/);
  await expect(page.getByTestId("intro")).not.toContainText("in development");
});

// Parking reform is off the tool (owner, 2026-11-12; last state with it: git tag parking-ui-before-removal-2026-11-12).
test("no parking or combined pill, tab or link anywhere in the nav or the Introduction", async ({ page }) => {
  const noParking = async () => {
    await expect(page.locator('a[data-reform="parking"], a[data-reform="combined"]')).toHaveCount(0);
    await expect(page.locator('a[href*="parking"], a[href*="combined"]')).toHaveCount(0);
    await expect(page.getByTestId("intro-link-parking")).toHaveCount(0);
    expect((await page.locator("header").textContent()) ?? "").not.toMatch(/parking/i);
  };
  await page.goto("#/");
  await expect(page.getByTestId("intro")).toBeVisible();
  await noParking();
  expect((await page.getByTestId("intro").textContent()) ?? "").not.toMatch(/parking/i);
  for (const url of ["#/summary", "#/middle/summary", "#/tod/summary"]) {
    await page.goto(url);
    await expect(page.getByTestId("summary")).toBeVisible();
    await noParking();
  }
});

test("old parking and combined addresses open the Introduction", async ({ page }) => {
  for (const url of ["#/parking", "#/parking/", "#/parking/summary?per=1000", "#/parking/how-sure", "#/combined/compare", "#/combined/where?p=upper"]) {
    await page.goto(url);
    await expect(page.getByTestId("intro")).toBeVisible();
    await expect(page).toHaveURL(/#\/$/);
    await expect(page).toHaveTitle("Introduction · Missing Middleware");
  }
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
  expect(dom.lists[0]).toBe(1);                     // the five steps
  expect(dom.lists[1]).toBeGreaterThanOrEqual(2);   // reform links, what you'll see
  expect(dom.tables).toBe(0);                       // the ranges table moved to each Brief
  for (const t of dom.links) expect(t.length).toBeGreaterThan(3);
  expect(dom.overflow).toBeLessThanOrEqual(0);
  expect(dom.emoji).toBe(false);
});

test("the Introduction fits a 375 px phone with no sideways page scroll", async ({ page }) => {
  await page.setViewportSize({ width: 375, height: 812 });
  await page.goto("#/");
  await expect(page.getByTestId("intro-step-5")).toBeVisible();
  expect(await page.evaluate(() => document.documentElement.scrollWidth - document.documentElement.clientWidth)).toBeLessThanOrEqual(0);
});

test("header pills: three in one even row on any screen, full names as accessible names", async ({ page }) => {
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
  await expect(nav.getByRole("link")).toHaveCount(3);
  const g = await geo();
  expect(g.overflow).toBeLessThanOrEqual(0);
  expect(g.share).toBeGreaterThan(0.97);
  expect(g.share).toBeLessThanOrEqual(1);
  const tops = new Set(g.boxes.map((b) => b[0])), widths = g.boxes.map((b) => b[1]);
  expect(Math.max(...widths) - Math.min(...widths)).toBeLessThanOrEqual(1);   // even shares
  expect(tops.size).toBe(1);   // three pills, one row, on a phone too (parking off the tool, 2026-11-12)
});

test("the run status strip sits below the sticky header and scrolls away", async ({ page }) => {
  await page.goto("#/middle/summary");
  const strip = page.locator(".status-strip");
  await expect(strip).toBeVisible();
  expect(await strip.evaluate((el) => !el.closest("header") && getComputedStyle(el).position === "static")).toBe(true);
  await expect(strip).not.toContainText(/in development|preview/i);
  await expect(page.getByTestId("preview-flag")).toHaveCount(0);
});
