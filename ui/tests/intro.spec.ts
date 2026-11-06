// The Introduction (landing page at the root route): the approved copy is on the page, the three 90% ranges and the
// baseline equal their sources (bundles and shared reference CSVs), the links open the right screens, and the old
// "Wisconsin today" screen is still reachable at its old address.
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
  "How would housing reform change the number of new homes?",
  "Missing Middleware studies how real reforms worked in places that adopted them. It compares them with places or years without the reform. Then it carries what it learned to one state, and gives a range of extra home permits for the five years after a law, 2027 to 2031.",
  "Wisconsin, extra permits 2027–2031, 90% range",
  "Statewide ADU reform: 8,055 to 13,666 ADU permits. This range covers only how far off the model was in other states. It leaves out uncertainty in Wisconsin's own current ADU rates.",
  "Statewide TOD reform: 3,922 to 16,335 extra homes near transit",
  "Statewide parking reform: −46,268 to +19,649 homes. A range that includes zero means the data can't tell whether repealing parking minimums alone adds or removes homes. The evidence comes from city repeals, since no state has repealed them statewide. This range is the spread of fake-repeal results, placed around the measured average.",
  "How we got there",
  "Pick a state. Wisconsin",
  "Set a baseline. We estimate what the state would permit under current law. For Wisconsin that is about 124,000 homes over 2027–2031 (90% range 56,500 to 218,865). Wisconsin Today",
  "Define each reform.",
  "Measure the effect where it really happened. We measure what happened where a reform passed, against places or years without it. The difference is our estimate of the reform's effect.",
  "Test the method.",
  "We hide data from some places and try to predict them, then check how close we got.",
  "We run placebo tests in places that never reformed by pretending they reformed in a given year. The method should find no effect there.",
  "A 90% range should hold the true answer about 9 times in 10. Where a test showed it held less often, we widened the range or say so on the page.",
  "Carry the effect to the state. We apply each measured effect to the state's own places and homes. ADU's rate adjusts for home values and incomes. TOD and parking use one average rate, because no local trait predicted the effect better than a plain average.",
  "What you'll see",
  "A range for each reform, with its low and high ends. We show no single best guess, because the evidence supports a range, not a point.",
  "Side lines across each range. They give a plain reason to believe the range. Some are real cases, like the median of 8 states that passed ADU laws. Others are our earlier scenario estimates.",
  "A map of where homes might land. It shows how ADU reform spreads homes differently from TOD reform. It is an illustration, not a prediction of which lots will build.",
  "Sensitivities. Other choices that could push a range up or down. Some did not pass tests set in advance. Others are reasonable alternative assumptions. Neither changes the range.",
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

test("the three ranges and the baseline equal their sources", async ({ page }) => {
  await page.goto("#/");
  const state = await bundle(page, "runs/", "state.json");
  const tod = await bundle(page, "scenarios/tod/runs/", "statewide.json");
  const pkState = await bundle(page, "scenarios/parking/runs/", "statewide.json");
  await expect(page.getByTestId("intro-adu-range")).toHaveText(`${fmt(state.range90.low)} to ${fmt(state.range90.high)} ADU permits`);
  await expect(page.getByTestId("intro-tod-range")).toHaveText(`${fmt(tod.range90.low)} to ${fmt(tod.range90.high)} extra homes near transit`);
  const lo = pkState.range90.low, hi = pkState.range90.high;
  await expect(page.getByTestId("intro-parking-range")).toHaveText(`${signed(lo)} to ${signed(hi)} homes`);
  // the copy's numbers, and the parking bundle's high end of the evidence
  expect([Math.round(lo), Math.round(hi)]).toEqual([-46268, 19649]);
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

test("the Wisconsin Today link opens the old Wisconsin today screen", async ({ page }) => {
  await page.goto("#/");
  await page.getByRole("link", { name: "Wisconsin Today" }).click();
  await expect(page).toHaveURL(/#\/today$/);
  await expect(page.locator("h1")).toHaveText("Wisconsin housing today");
  await expect(page.getByTestId("today-central")).toBeVisible();
  await expect(page).toHaveTitle("Wisconsin today · Wisconsin ADU law · Missing Middleware");
  // and the brand link brings the reader back to the Introduction
  await page.locator("a.brand").click();
  await expect(page.getByTestId("intro")).toBeVisible();
});

test("the reform links open each reform's page that describes the law", async ({ page }) => {
  const cases: [string, RegExp, string, string][] = [
    ["intro-link-adu", /#\/compare$/, "A statewide ADU law: what it adds", "The law."],
    ["intro-link-tod", /#\/tod\/today$/, "Homes near major transit stops in Wisconsin today", "What the modelled law does"],
    ["intro-link-parking", /#\/parking\/compare$/, "A statewide parking law: what it adds", "removed minimum parking requirements"],
  ];
  for (const [id, url, h1, lawText] of cases) {
    await page.goto("#/");
    await page.getByTestId(id).click();
    await expect(page).toHaveURL(url);
    await expect(page.locator("h1")).toHaveText(h1);
    await expect(page.locator("main")).toContainText(lawText);
  }
});

test("the Introduction is accessible and fits a phone", async ({ page }) => {
  await page.goto("#/");
  await expect(page.getByTestId("intro")).toBeVisible();
  const dom = await page.evaluate(() => ({
    hs: [...document.querySelectorAll("h1,h2,h3,h4,h5,h6")].map((h) => Number(h.tagName[1])),
    lists: [document.querySelectorAll("[data-testid=intro] ol").length, document.querySelectorAll("[data-testid=intro] ul").length],
    links: [...document.querySelectorAll("main a")].map((a) => (a.textContent ?? "").trim()),
    overflow: document.documentElement.scrollWidth - document.documentElement.clientWidth,
    emoji: /\p{Extended_Pictographic}/u.test(document.querySelector("main")!.textContent ?? ""),
  }));
  expect(dom.hs[0]).toBe(1);
  expect(dom.hs.filter((l) => l === 1)).toHaveLength(1);
  dom.hs.forEach((l, i) => { if (i) expect(l).toBeLessThanOrEqual(dom.hs[i - 1] + 1); });
  expect(dom.lists[0]).toBeGreaterThanOrEqual(2);   // the steps and the sub-steps of step 5
  expect(dom.lists[1]).toBeGreaterThanOrEqual(3);   // ranges, reform links, what you'll see
  for (const t of dom.links) expect(t.length).toBeGreaterThan(3);
  expect(dom.overflow).toBeLessThanOrEqual(0);
  expect(dom.emoji).toBe(false);
});
