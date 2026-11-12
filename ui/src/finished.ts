// Which pages are finished (owner, 2026-11-12 22:01). Unfinished pages stay in the tab bar, dimmed and labelled
// "coming soon"; they are not links, a direct address shows a short "This page is coming soon" note, and any link to
// one becomes plain text. To switch a page back on, add its path to its reform's list here (one line).
//
// Paths are the reform's tab paths ("/pilot" covers every pilot page). The Introduction ("#/") is always finished.
import { esc } from "./format";
import { reformEntry, REGISTRY } from "./scenarios/types";

export const FINISHED: Record<string, string[]> = {
  adu: ["/summary", "/where", "/how-sure"],
  middle: ["/summary", "/how-sure"],
  tod: ["/summary", "/where", "/how-sure"],
};

/** The shared Wisconsin today page ("#/wisconsin-today"), with the header link and the Introduction's step 2 link. */
const WISCONSIN_TODAY_FINISHED = false;

/** Reviewer override: with localStorage "mm-show-unfinished" = "1" every page is shown as finished, so unfinished
 *  pages can still be reviewed and tested (ui/playwright.config.ts sets it for the content tests; finished.spec.ts
 *  runs without it). Visitors never see it unless they set it themselves. */
const SHOW_ALL = (() => { try { return localStorage.getItem("mm-show-unfinished") === "1"; } catch { return false; } })();

export function wisconsinTodayFinished(): boolean { return SHOW_ALL || WISCONSIN_TODAY_FINISHED; }

export const COMING_SOON = "coming soon";

/** True when this reform's page is finished. `path` is reform-relative ("/why", "/pilot/madison", "/"). */
export function isFinished(reform: string, path: string): boolean {
  if (SHOW_ALL) return true;
  const p = path.split("?")[0];
  if (p === "/" || p === "") return true;   // a reform's bare address opens its Summary
  // old addresses: "/compare" opens the Summary, "/today" opens Wisconsin today
  if (p.startsWith("/compare")) return isFinished(reform, "/summary");
  if (p.startsWith("/today")) return wisconsinTodayFinished();
  return (FINISHED[reform] ?? []).some((f) => p === f || p.startsWith(`${f}/`));
}

/** True when an in-page address ("#/tod/why?x=1", "#/wisconsin-today") points at a finished page (or the Introduction). */
export function hrefFinished(href: string): boolean {
  if (!href.startsWith("#")) return true;
  const full = (href.slice(1) || "/").split("?")[0];
  if (full === "/" || full === "") return true;
  if (full.replace(/\/$/, "") === "/wisconsin-today") return wisconsinTodayFinished();
  const seg = full.split("/")[1] ?? "";
  const named = reformEntry(seg);
  if (named) return isFinished(named.id, full.slice(seg.length + 1) || "/");
  // no reform prefix: the default reform's screen (an unknown path falls back to its Summary, which is finished)
  const known = ["/summary", "/where", "/how-sure", "/why", "/pilot", "/brief", "/compare", "/today"].some((p) => full === p || full.startsWith(`${p}/`));
  return known ? isFinished(REGISTRY.default, full) : true;
}

/** Turn every in-page link to an unfinished page inside `root` into plain text (same words, no link). */
export function unlinkUnfinished(root: ParentNode): void {
  if (SHOW_ALL) return;
  root.querySelectorAll<HTMLAnchorElement>('a[href^="#"]').forEach((a) => {
    if (hrefFinished(a.getAttribute("href")!)) return;
    const s = document.createElement("span");
    s.className = `${a.className ? `${a.className} ` : ""}unlinked`.replace(/\bbutton\b/, "").trim();
    s.dataset.unlinked = a.getAttribute("href")!;
    for (const k of ["data-testid", "id"]) { const v = a.getAttribute(k); if (v) s.setAttribute(k, v); }
    while (a.firstChild) s.appendChild(a.firstChild);
    a.replaceWith(s);
  });
}

/** Keep the page free of links to unfinished pages, including content drawn later (popups, re-renders). */
export function watchUnfinishedLinks(): void {
  unlinkUnfinished(document.body);
  new MutationObserver((ms) => {
    for (const m of ms) for (const n of m.addedNodes) {
      if (n instanceof HTMLAnchorElement && n.parentNode) unlinkUnfinished(n.parentNode);
      else if (n instanceof Element) unlinkUnfinished(n);
    }
  }).observe(document.body, { childList: true, subtree: true });
}

/** The note shown at a direct address of an unfinished page, with links to the Summary and the Introduction. */
export function comingSoonHTML(summaryHref: string, what: string): string {
  return `<section class="coming-soon" data-testid="coming-soon" aria-labelledby="coming-soon-h">
    <h1 id="coming-soon-h">This page is coming soon</h1>
    <p>We are still finishing ${esc(what)}.</p>
    <p><a href="${summaryHref}" data-testid="coming-soon-summary">Go to the Summary</a> · <a href="#/" data-testid="coming-soon-intro">Go to the Introduction</a></p>
  </section>`;
}
