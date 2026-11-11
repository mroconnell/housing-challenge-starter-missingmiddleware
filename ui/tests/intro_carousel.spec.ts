// The Introduction's "What you'll see" preview carousel (owner 2026-11-11): three thumbnails drawn from the ADU
// bundle by the screens' own functions, each one link to its screen; Pause/Play, no autoplay with reduced motion,
// named buttons, carousel/slide roles, a live region only when the reader moves the slides, keyboard use, a fixed
// height, a phone fit, and a short note (not an error) when the map cannot load.
import { expect, test, type Page } from "@playwright/test";

const current = (page: Page) => page.locator(".ic-slide.is-current");
async function bundle(page: Page, file: string) {
  const { run_id } = await (await page.request.get("runs/latest.json")).json();
  return (await page.request.get(`runs/${run_id}/${file}`)).json();
}
/** Move the mouse off the carousel and focus out of it, so only the reader's Pause/Play choice counts. */
async function leave(page: Page) {
  await page.mouse.move(2, 2);
  await page.evaluate(() => (document.activeElement as HTMLElement | null)?.blur());
}

test("three slides render from the bundle, each one link to its screen", async ({ page }) => {
  await page.goto("#/");
  await page.getByTestId("intro-carousel").scrollIntoViewIfNeeded();   // it sits under the list now
  const car = page.getByTestId("intro-carousel");
  await expect(car).toHaveAttribute("aria-roledescription", "carousel");
  const slides = page.getByTestId("intro-slide");
  await expect(slides).toHaveCount(3);
  for (let i = 0; i < 3; i++) {
    await expect(slides.nth(i)).toHaveAttribute("aria-roledescription", "slide");
    await expect(slides.nth(i)).toHaveAttribute("aria-label", `${i + 1} of 3`);
  }
  // every thumbnail is drawn from real data (no notes)
  for (const id of ["range", "map", "sens"]) await expect(page.locator(`[data-thumb="${id}"]`)).toHaveAttribute("data-ready", "1", { timeout: 20_000 });
  const state = await bundle(page, "state.json");
  const unc = await bundle(page, "uncertainty.json");
  // 1: the Statewide comparison's band chart: the 90% band and one line per chart side line
  await expect(page.locator('[data-thumb="range"] svg path[data-band="range90"]')).toHaveCount(1);
  const chartLines = state.side_lines.filter((s: { where: string; value?: number }) => s.where === "chart" && s.value !== undefined);
  await expect(page.locator('[data-thumb="range"] svg path[data-series^="side-"]')).toHaveCount(chartLines.length);
  // 2: the Where map (MapLibre canvas)
  await expect(page.locator('[data-thumb="map"] canvas')).toHaveCount(1);
  // 3: How sure's what-ifs against the range, one row per case
  const cases = unc.sensitivity_cases.filter((c: { id: string; group: string }) => c.id !== "adopted" && c.group === "addition");
  await expect(page.locator('[data-thumb="sens"] .vs-row')).toHaveCount(cases.length);
  // links and their names
  const links: [string, string, string][] = [
    ["range", "#/compare", "The ADU 90% range, with its side lines — open Statewide comparison"],
    ["map", "#/where", "Where ADUs might go: an illustration — open Where"],
    ["sens", "#/how-sure", "What-ifs against the ADU range — open How sure"],
  ];
  for (const [id, href, name] of links) {
    const a = page.getByTestId(`intro-slide-link-${id}`);
    await expect(a).toHaveAttribute("href", href);
    await expect(a).toHaveAttribute("aria-label", name);
  }
  // the thumbnails are hidden from screen readers and hold nothing focusable
  for (const th of await page.locator(".ic-thumb").all()) {
    await expect(th).toHaveAttribute("aria-hidden", "true");
    await expect(th).toHaveAttribute("inert", "");
  }
  // clicking the visible slide opens its screen
  await page.getByRole("link", { name: links[0][2] }).click();
  await expect(page).toHaveURL(/#\/compare$/);
  await expect(page.locator("h1")).toHaveText("A statewide ADU law: what it adds");
});

test("autoplay advances every 6 seconds, stops on hover and focus, and Pause stops it", async ({ page }) => {
  await page.clock.install();
  await page.goto("#/");
  await page.getByTestId("intro-carousel").scrollIntoViewIfNeeded();   // it sits under the list now
  const car = page.getByTestId("intro-carousel");
  await expect(car).toHaveAttribute("data-running", "1");
  await expect(current(page)).toHaveAttribute("aria-label", "1 of 3");
  await page.clock.runFor(6100);
  await expect(current(page)).toHaveAttribute("aria-label", "2 of 3");
  // autoplay never announces
  await expect(page.locator("#ic-slides")).toHaveAttribute("aria-live", "off");
  // hover pauses
  await car.hover();
  await page.clock.runFor(13_000);
  await expect(current(page)).toHaveAttribute("aria-label", "2 of 3");
  await leave(page);
  await page.clock.runFor(6100);
  await expect(current(page)).toHaveAttribute("aria-label", "3 of 3");
  // focus inside pauses
  await page.getByRole("button", { name: "Next preview" }).focus();
  await page.mouse.move(2, 2);
  await page.clock.runFor(13_000);
  await expect(current(page)).toHaveAttribute("aria-label", "3 of 3");
  await leave(page);
  // Pause: a visible button that stops the rotation until Play
  const btn = page.getByTestId("intro-carousel-pause");
  await expect(btn).toBeVisible();
  await expect(btn).toHaveText("Pause");
  await btn.click();
  await expect(btn).toHaveText("Play");
  await expect(car).toHaveAttribute("data-state", "paused");
  await leave(page);
  const before = await current(page).getAttribute("aria-label");
  await page.clock.runFor(20_000);
  await expect(current(page)).toHaveAttribute("aria-label", before!);
  await btn.click();
  await expect(btn).toHaveText("Pause");
  await leave(page);
  await page.clock.runFor(6100);
  await expect(current(page)).not.toHaveAttribute("aria-label", before!);
});

test("with reduced motion the carousel never plays on its own", async ({ page }) => {
  await page.emulateMedia({ reducedMotion: "reduce" });
  await page.clock.install();
  await page.goto("#/");
  await page.getByTestId("intro-carousel").scrollIntoViewIfNeeded();   // it sits under the list now
  const car = page.getByTestId("intro-carousel");
  await expect(car).toHaveAttribute("data-state", "paused");
  await expect(car).toHaveAttribute("data-running", "0");
  await expect(page.getByTestId("intro-carousel-pause")).toHaveText("Play");
  await page.clock.runFor(30_000);
  await expect(current(page)).toHaveAttribute("aria-label", "1 of 3");
  // the reader can still move the slides
  await page.getByRole("button", { name: "Next preview" }).click();
  await expect(current(page)).toHaveAttribute("aria-label", "2 of 3");
});

test("the buttons have names and work from the keyboard; the live region speaks only when the reader moves", async ({ page }) => {
  await page.emulateMedia({ reducedMotion: "reduce" });
  await page.goto("#/");
  await page.getByTestId("intro-carousel").scrollIntoViewIfNeeded();   // it sits under the list now
  await expect(page.getByRole("button", { name: "Play the previews" })).toBeVisible();
  await expect(page.getByRole("button", { name: "Previous preview" })).toBeVisible();
  await expect(page.getByRole("button", { name: "Next preview" })).toBeVisible();
  await expect(page.getByRole("button", { name: /^Preview \d of 3: / })).toHaveCount(3);
  await expect(page.getByRole("button", { name: "Preview 2 of 3: Where ADUs might go: an illustration" })).toBeVisible();
  await expect(page.locator("#ic-slides")).toHaveAttribute("aria-live", "off");
  const next = page.getByRole("button", { name: "Next preview" });
  await next.focus();
  await page.keyboard.press("Enter");
  await expect(current(page)).toHaveAttribute("aria-label", "2 of 3");
  await expect(page.locator("#ic-slides")).toHaveAttribute("aria-live", "polite");
  await page.keyboard.press("ArrowRight");
  await expect(current(page)).toHaveAttribute("aria-label", "3 of 3");
  await page.keyboard.press("ArrowRight");
  await expect(current(page)).toHaveAttribute("aria-label", "1 of 3");
  await page.keyboard.press("ArrowLeft");
  await expect(current(page)).toHaveAttribute("aria-label", "3 of 3");
  await page.getByRole("button", { name: /^Preview 1 of 3/ }).press("Space");
  await expect(current(page)).toHaveAttribute("aria-label", "1 of 3");
  await expect(page.getByRole("button", { name: /^Preview 1 of 3/ })).toHaveAttribute("aria-current", "true");
  // Tab from the page start reaches the slide link before the controls, and Enter opens the screen
  await page.getByRole("link", { name: /open Statewide comparison/ }).focus();
  await page.keyboard.press("Enter");
  await expect(page).toHaveURL(/#\/compare$/);
});

test("the carousel passes the accessibility checks, keeps a fixed height and fits a 375 px phone", async ({ page }) => {
  await page.setViewportSize({ width: 375, height: 812 });
  await page.emulateMedia({ reducedMotion: "reduce" });
  await page.goto("#/");
  await page.getByTestId("intro-carousel").scrollIntoViewIfNeeded();   // it sits under the list now
  await expect(page.locator('[data-thumb="map"]')).toHaveAttribute("data-ready", /1|note/, { timeout: 20_000 });
  const dom = await page.evaluate(() => {
    const ids: Record<string, number> = {};
    document.querySelectorAll("[id]").forEach((e) => { ids[e.id] = (ids[e.id] ?? 0) + 1; });
    const car = document.querySelector(".intro-carousel")!;
    const focusable = [...car.querySelectorAll(".ic-thumb *")].filter((e) => (e as HTMLElement).tabIndex >= 0 && !(e as HTMLElement).closest("[inert]"));
    return {
      dupIds: Object.entries(ids).filter(([, n]) => n > 1).map(([k]) => k),
      overflow: document.documentElement.scrollWidth - document.documentElement.clientWidth,
      carRight: car.getBoundingClientRect().right - document.documentElement.clientWidth,
      focusableInThumbs: focusable.length,
      hiddenSlides: [...car.querySelectorAll(".ic-slide:not(.is-current)")].map((s) => s.getAttribute("aria-hidden")),
      emoji: /\p{Extended_Pictographic}/u.test(car.textContent ?? ""),
      positiveTabindex: [...car.querySelectorAll("[tabindex]")].filter((e) => Number(e.getAttribute("tabindex")) > 0).length,
    };
  });
  expect(dom.dupIds).toEqual([]);
  expect(dom.overflow).toBeLessThanOrEqual(0);
  expect(dom.carRight).toBeLessThanOrEqual(0);
  expect(dom.focusableInThumbs).toBe(0);
  expect(dom.hiddenSlides).toEqual(["true", "true"]);
  expect(dom.emoji).toBe(false);
  expect(dom.positiveTabindex).toBe(0);
  // every control, link and region in the carousel has a name (browser accessibility tree)
  const snap = await page.getByTestId("intro-carousel").ariaSnapshot();
  const unnamed = snap.split("\n").filter((l) => /^\s*- (button|link|img|region|group)(:|$| \[)/.test(l));
  expect(unnamed).toEqual([]);
  // only the current slide is exposed, and its thumbnail is not
  expect(snap).toContain("open Statewide comparison");
  expect(snap).not.toContain("open Where");
  expect(snap).not.toMatch(/- img/);
  // fixed height: the page does not move between slides
  const h = async () => page.locator("#ic-slides").evaluate((e) => e.getBoundingClientRect().height);
  const listTop = async () => page.locator(".intro-see").evaluate((e) => e.getBoundingClientRect().top + window.scrollY);
  const [h0, t0] = [await h(), await listTop()];
  for (let i = 0; i < 3; i++) {
    await page.getByRole("button", { name: "Next preview" }).click();
    expect(await h()).toBe(h0);
    expect(await listTop()).toBe(t0);
  }
  // the carousel sits under the list, full width (owner 2026-11-11)
  expect(await page.getByTestId("intro-carousel").evaluate((e) => e.getBoundingClientRect().top)).toBeGreaterThanOrEqual(
    await page.locator(".intro-see").evaluate((e) => e.getBoundingClientRect().bottom));
});

test("a map that cannot load leaves a short note, not an error", async ({ page }) => {
  await page.route("**/geo_counties.json", (r) => r.fulfill({ status: 404, body: "" }));
  await page.goto("#/");
  await page.getByTestId("intro-carousel").scrollIntoViewIfNeeded();   // it sits under the list now
  const th = page.locator('[data-thumb="map"]');
  await expect(th).toHaveAttribute("data-ready", "note", { timeout: 20_000 });
  await expect(th).toContainText("Preview not available here");
  await expect(page.locator('[data-thumb="range"]')).toHaveAttribute("data-ready", "1");
  await expect(page.getByTestId("intro-range-table")).toBeVisible();
});

test("the bundle files and the map geometry load only once the carousel is shown", async ({ page }) => {
  const geo: string[] = [];
  page.on("request", (r) => { if (/geo_|areas\.json|uncertainty\.json/.test(r.url())) geo.push(r.url()); });
  await page.setViewportSize({ width: 1280, height: 220 });   // the carousel starts below the fold
  await page.goto("#/");
  await expect(page.getByTestId("intro-range-table")).toBeAttached();
  await page.waitForTimeout(800);
  expect(geo).toEqual([]);
  await page.getByTestId("intro-carousel").scrollIntoViewIfNeeded();
  await expect(page.locator('[data-thumb="map"]')).toHaveAttribute("data-ready", "1", { timeout: 20_000 });
  expect(geo.filter((u) => /geo_/.test(u)).map((u) => u.split("/").pop())).toEqual(["geo_counties.json"]);   // counties only
});
