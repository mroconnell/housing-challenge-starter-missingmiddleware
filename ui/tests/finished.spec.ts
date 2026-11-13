// Unfinished pages (owner, 2026-11-12 22:01; the list is ui/src/finished.ts). Clickable: the Introduction, each reform's
// Summary and How sure, and the ADU and TOD Where tabs. Greyed: Middle housing Where, every Why, Pilots and Brief tab,
// and the shared Wisconsin today page. Greyed tabs stay in the row, dimmed with "coming soon", and are not links; a
// direct address shows "This page is coming soon" with links to the Summary and the Introduction; nothing links to them.
// This spec runs without the reviewer override the other specs use (playwright.config.ts).
import { expect, test, type Page } from "@playwright/test";

test.use({ storageState: { cookies: [], origins: [] } });

const REFORMS = [
  { id: "adu", pre: "", done: ["Summary", "Where", "How sure"], soon: ["Why", "Pilots", "Brief"] },
  { id: "middle", pre: "/middle", done: ["Summary", "How sure"], soon: ["Where", "Why", "Brief"] },
  { id: "tod", pre: "/tod", done: ["Summary", "Where", "How sure"], soon: ["Why", "Pilots", "Brief"] },
];
const ACTIVE = ["#/", "#/summary", "#/where", "#/how-sure", "#/middle/summary", "#/middle/how-sure", "#/tod/summary", "#/tod/where", "#/tod/how-sure"];
const GREYED = ["#/why", "#/pilot/madison", "#/pilot/sun-prairie", "#/brief", "#/adu/why", "#/middle/where", "#/middle/why", "#/middle/brief",
  "#/tod/why", "#/tod/pilot/milwaukee-connect-1", "#/tod/brief", "#/wisconsin-today", "#/wisconsin-today?section=tod"];

/** True when an in-page address opens a finished page (mirrors the owner's list above). */
function allowed(href: string): boolean {
  const full = (href.replace(/^#/, "") || "/").split("?")[0];
  if (full === "/" || full === "") return true;
  if (/^\/wisconsin-today\/?$/.test(full) || /^\/(adu|middle|tod)?\/?today/.test(full) || /^\/today/.test(full)) return false;
  const m = full.match(/^\/(middle|tod|adu)(\/.*)?$/);
  const id = m ? m[1] : "adu", path = m ? (m[2] || "/") : full;
  if (path === "/" || /^\/(summary|how-sure|compare)(\/|$)/.test(path)) return true;
  if (/^\/where(\/|$)/.test(path)) return id !== "middle";
  if (/^\/(why|pilot|brief)(\/|$)/.test(path)) return false;
  return true;   // an unknown screen falls back to the Summary
}

/** A fresh load of `url` (a hash-only change would leave the previous page's h1 in place while the next one loads). */
async function open(page: Page, url: string) {
  await page.goto("about:blank");
  await page.goto(url);
  await expect(page.locator("main h1").first(), url).toBeVisible();
}

async function hrefs(page: Page): Promise<string[]> {
  return page.locator('a[href^="#"]').evaluateAll((as) => as.map((a) => a.getAttribute("href")!));
}

for (const r of REFORMS) {
  test(`${r.id}: greyed tabs show "coming soon", are not links and can be reached by keyboard`, async ({ page }) => {
    await page.goto(`#${r.pre || "/adu"}/summary`);
    await expect(page.getByTestId("summary")).toBeVisible();
    const tabs = page.locator("nav.tabs a");
    const label = (t: string) => t.replace(/^\s*\d+\s*/, "").replace(/\s*coming soon\s*$/, "").trim();
    for (const t of await tabs.all()) {
      const name = label((await t.textContent()) ?? "");
      if (r.soon.includes(name)) {
        await expect(t, name).not.toHaveAttribute("href");
        await expect(t, name).toHaveAttribute("aria-disabled", "true");
        await expect(t, name).toHaveAttribute("tabindex", "0");
        await expect(t, name).toContainText("coming soon");
        await expect(t, name).toHaveAccessibleName(`${name} coming soon`);
        await t.focus();
        await expect(t).toBeFocused();
        const before = page.url();
        await t.click({ force: true });   // aria-disabled: Playwright would wait for it to be enabled
        expect(page.url()).toBe(before);
      } else {
        expect(r.done, name).toContain(name);
        await expect(t, name).toHaveAttribute("href", /^#/);
        await expect(t, name).not.toContainText("coming soon");
      }
    }
    expect((await tabs.allTextContents()).map(label).filter((x) => r.soon.includes(x)).sort()).toEqual([...r.soon].sort());
  });
}

test("the header's Wisconsin today is greyed, and the Introduction's step 2 link is plain text", async ({ page }) => {
  await page.goto("#/");
  const head = page.getByTestId("head-today");
  await expect(head).toContainText("coming soon");
  await expect(head).not.toHaveAttribute("href");
  await expect(head).toHaveAttribute("aria-disabled", "true");
  const step2 = page.getByTestId("intro-step-2");
  await expect(step2).toContainText("Wisconsin Today");
  await expect(step2.locator("a")).toHaveCount(0);
});

test("direct addresses of greyed pages show the coming-soon note with links to the Summary and the Introduction", async ({ page }) => {
  for (const url of GREYED) {
    await page.goto("about:blank");
    await page.goto(url);
    const note = page.getByTestId("coming-soon");
    await expect(note, url).toBeVisible();
    await expect(page.locator("h1"), url).toHaveText("This page is coming soon");
    await expect(page, url).toHaveTitle(/^Coming soon · /);
    await expect(note.getByTestId("coming-soon-intro")).toHaveAttribute("href", "#/");
    await expect(note.getByTestId("coming-soon-summary")).toHaveAttribute("href", /\/summary$/);
  }
  await page.goto("#/tod/brief");
  // a hash change keeps the previous greyed page on screen until the router redraws: wait for the TOD link before clicking
  await expect(page.getByTestId("coming-soon-summary")).toHaveAttribute("href", "#/tod/summary");
  await page.getByTestId("coming-soon-summary").click();
  await expect(page).toHaveURL(/#\/tod\/summary$/);
  await expect(page.getByTestId("summary")).toHaveAttribute("data-reform", "tod");
  await page.goto("#/middle/where");
  await page.getByTestId("coming-soon-intro").click();
  await expect(page.getByTestId("intro")).toBeVisible();
  // an old "/today" address lands on the Wisconsin today note
  await page.goto("#/tod/today");
  await expect(page.getByTestId("coming-soon")).toBeVisible();
});

test("finished pages open normally, with no coming-soon note", async ({ page }) => {
  const errors: string[] = [];
  page.on("pageerror", (e) => errors.push(String(e)));
  for (const url of ACTIVE) {
    await open(page, url);
    await expect(page.getByTestId("coming-soon"), url).toHaveCount(0);
  }
  await open(page, "#/where");
  await expect(page.locator("#map canvas")).toBeAttached({ timeout: 20_000 });
  // the carousel's links stay active (Summary, Where and How sure are all finished)
  await page.goto("#/");
  for (const id of ["range", "map", "sens"]) await expect(page.getByTestId(`intro-slide-link-${id}`)).toHaveAttribute("href", /^#\//);
  expect(errors).toEqual([]);
});

test("no link anywhere points at a greyed page", async ({ page }) => {
  for (const url of ACTIVE) {
    await open(page, url);
    await page.waitForTimeout(300);
    const bad = (await hrefs(page)).filter((h) => !allowed(h));
    expect(bad, url).toEqual([]);
  }
  // the Summary's "Why →" style links are plain text now, words kept
  await page.goto("#/tod/summary");
  await expect(page.getByTestId("summary")).toBeVisible();
  expect((await hrefs(page)).filter((h) => /\/why/.test(h))).toEqual([]);
  // on Where, the picker sends Middle housing (whose Where is greyed) to its Summary
  await page.goto("#/where");
  await expect(page.locator('.reform-nav a[data-reform="middle"]')).toHaveAttribute("href", "#/middle/summary");
  await expect(page.locator('.reform-nav a[data-reform="tod"]')).toHaveAttribute("href", "#/tod/where");
});
