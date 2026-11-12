// Multi-reform shell: header with the reform picker, status strip, screens navigation, footer, and a hash
// router. Each reform (ADU, middle housing, transit-oriented density) fills the strip, tabs, footer and screens through
// the contract in ui/src/scenarios/types.ts (docs/shared/SCENARIO_CONTRACT.md).
//
// Parking reform is off the tool for now (owner, 2026-11-12; the last state with it is the git tag
// parking-ui-before-removal-2026-11-12). Its code (ui/src/scenarios/parking/, and the retired "TOD and parking
// together" view in ui/src/scenarios/combined/) and bundles stay on disk, unregistered and unrouted. Old "#/parking"
// and "#/combined" addresses open the Introduction.
//
// URLs: the bare root ("#/", or no hash) is the Introduction, the landing page above every reform; "#/wisconsin-today"
// is the shared Wisconsin today page. The default reform has no prefix ("#/summary"), so existing ADU links keep
// working ("#/adu/" opens its first screen); other reforms are prefixed with their id ("#/tod/summary"). The query
// part ("?per=1000") belongs to the reform.
//
// Every reform has the same tabs in the same order (Summary · Where · How sure · Why · Pilots · Brief; a reform
// without one omits it). Old addresses keep working: a reform's "/compare" (the former Statewide comparison) opens
// its Summary, and its "/today" opens that reform's section of the shared Wisconsin today page.
import "./style.css";
import "./scenarios/shell.css";
import { labelScrollers } from "./app";
import { esc } from "./format";
import { aduReform } from "./scenarios/adu";
import { introLoading, loadIntro, renderIntro } from "./screens/intro";
import { renderWisconsinToday, type TodayData } from "./screens/wisconsin_today";
import { middleReform } from "./scenarios/middle";
import { placeholderReform } from "./scenarios/placeholder";
import { todReform } from "./scenarios/tod/index";
import { REGISTRY, reformEntry, type MountedReform, type ReformEntry, type ReformModule, type ShellEnv } from "./scenarios/types";

/** Code for each reform id; a reform without its own module (or not yet "ready") gets the holding page. */
const MODULES: Record<string, ReformModule> = { adu: aduReform, middle: middleReform, tod: todReform };

/** Preview mode lets the owner review a reform that has screens but is not yet "ready" (a Gate 4 pilot).
 *  Turn it on with `?preview=1` in the URL (off with `?preview=0`); it is remembered for this browser tab only. */
function previewOn(): boolean {
  const q = new URLSearchParams((location.hash.split("?")[1] ?? ""));
  const v = q.get("preview");
  try {
    if (v === "1") sessionStorage.setItem("mm-preview", "1");
    if (v === "0") sessionStorage.removeItem("mm-preview");
    return sessionStorage.getItem("mm-preview") === "1";
  } catch {
    return v === "1";
  }
}

/** True when the reform is shown through its own screens only because preview mode is on. */
function isPreview(e: ReformEntry): boolean {
  return e.status !== "ready" && !!MODULES[e.id] && previewOn();
}

function moduleFor(e: ReformEntry): ReformModule {
  return MODULES[e.id] && (e.status === "ready" || isPreview(e)) ? MODULES[e.id] : placeholderReform;
}

const prefixOf = (id: string) => (id === REGISTRY.default ? "" : `/${id}`);

/** Split the hash into the reform id, the reform-relative path and the query. */
/** True for the Introduction: no reform prefix and no screen path ("", "#", "#/", "#/?x=1"). */
function isHome(): boolean {
  const full = (location.hash.replace(/^#/, "") || "/").split("?")[0];
  return full === "/" || full === "";
}

function parse(): { reform: string; path: string; params: URLSearchParams } {
  const raw = location.hash.replace(/^#/, "") || "/";
  const [full, q] = raw.split("?");
  const seg = (full || "/").split("/")[1] ?? "";
  const named = reformEntry(seg);
  const reform = named ? named.id : REGISTRY.default;
  const path = named ? (full.slice(seg.length + 1) || "/") : (full || "/");
  return { reform, path, params: new URLSearchParams(q ?? "") };
}

interface Active { entry: ReformEntry; m: MountedReform; mod: ReformModule }
let active: Active | null = null;
const cache = new Map<string, unknown>();
let lastKey = "";

function announce(msg: string): void {
  // clear first so the same message is announced again if repeated
  const el = document.getElementById("announce");
  if (!el) return;
  el.textContent = "";
  window.setTimeout(() => { el.textContent = msg; }, 60);
}

/** The reforms shown in the header picker, in registry order (a reform with in_nav: false keeps its routes only). */
const NAV_REFORMS = REGISTRY.reforms.filter((r) => r.in_nav !== false);

/** One pill per reform on one row. A phone shows the short name; the full label is always the accessible name. */
function pickerList(href: (r: ReformEntry) => string, current?: ReformEntry): string {
  return `<nav class="reform-nav" aria-label="Policy reform" data-testid="reform-picker"><ul>${NAV_REFORMS.map((r) => {
    const name = `${r.label}${r.status === "ready" ? "" : " (in development)"}`;
    return `
    <li><a href="${href(r)}" data-reform="${esc(r.id)}" aria-label="${esc(name)}" ${current && r.id === current.id ? 'aria-current="page"' : ""}><span class="rn-full">${esc(r.label)}${r.status === "ready" ? "" : ' <span class="reform-dev">(in development)</span>'}</span><span class="rn-short" aria-hidden="true">${esc(r.short_label ?? r.label)}</span></a></li>`;
  }).join("")}</ul></nav>`;
}

/** The small "Wisconsin today" link in the header (the shared page), marked current on that page. */
function todayLink(current = false): string {
  return `<a class="head-today" href="#/wisconsin-today" data-testid="head-today"${current ? ' aria-current="page"' : ""}>Wisconsin today</a>`;
}

function picker(current: ReformEntry): string {
  return pickerList((r) => `#${prefixOf(r.id)}/`, current);
}

function shell(e: ReformEntry, m: MountedReform): void {
  const pre = prefixOf(e.id);
  document.body.innerHTML = `
  <a class="skip" href="#main">Skip to main content</a>
  <header class="site-head no-print">
    <div class="wrap head-row">
      <a class="brand" href="#/"><span class="brand-mark" aria-hidden="true">⌂</span> Missing Middleware</a>
      <p class="head-sub">${esc(e.subtitle)}</p>
      ${todayLink()}
    </div>
    <div class="wrap">${picker(e)}</div>
    <nav class="tabs" aria-label="Screens"><div class="wrap"><ol>${m.routes.map((r) => `<li><a href="#${pre}${r.path}" data-route="${r.match ?? r.path}"><span class="tab-n" aria-hidden="true">${r.n}</span> ${esc(r.label)}</a></li>`).join("")}</ol></div></nav>
  </header>
  <div class="status-strip no-print" role="note" aria-label="Model run status">
    <div class="wrap">${isPreview(e) ? '<span class="preview-flag" data-testid="preview-flag"><strong>Preview</strong>: not yet reviewed; numbers may change</span>' : ""}${m.statusStrip}</div>
  </div>
  <main id="main" class="wrap" tabindex="-1"></main>
  <div id="announce" class="sr-only" role="status" aria-live="polite" aria-atomic="true" data-testid="announce"></div>
  <footer class="site-foot">
    <div class="wrap">${m.footer}</div>
  </footer>${m.extra}`;
  document.querySelector<HTMLAnchorElement>(".skip")!.addEventListener("click", (ev) => {
    ev.preventDefault();
    document.getElementById("main")!.focus();
  });
  const tabRow = document.querySelector<HTMLElement>("nav.tabs ol");
  tabRow?.addEventListener("scroll", () => tabRow.classList.toggle("at-end", tabRow.scrollLeft + tabRow.clientWidth >= tabRow.scrollWidth - 2), { passive: true });
  m.bind();
}

/** A reform's loaded data, shared by its screens and the Wisconsin today page (loaded once). */
async function dataFor(entry: ReformEntry, mod: ReformModule): Promise<unknown> {
  const key = `${entry.id}:${mod === placeholderReform ? "holding" : "screens"}`;
  if (!cache.has(key)) cache.set(key, await mod.load(entry));
  return cache.get(key);
}

function envFor(entry: ReformEntry): ShellEnv {
  const pre = prefixOf(entry.id);
  return {
    entry,
    link: (path) => `#${pre}${path}`,
    replaceQuery(q) {
      const { path } = parse();
      const qs = q.toString();
      history.replaceState(null, "", `#${pre}${path}${qs ? `?${qs}` : ""}`);
    },
    refresh: () => route(true),
    announce,
  };
}

async function activate(id: string): Promise<Active> {
  const entry = reformEntry(id)!;
  const mod = moduleFor(entry);
  const data = await dataFor(entry, mod);
  const env = envFor(entry);
  active?.m.leave?.();
  const m = mod.mount(env, data);
  shell(entry, m);
  return { entry, m, mod };
}

/** The Introduction's page (and the shared Wisconsin today page): header with the reform picker (no reform current),
 *  no status strip or screen tabs. */
function homeShell(page: "home" | "today" = "home"): void {
  document.body.innerHTML = `
  <a class="skip" href="#main">Skip to main content</a>
  <header class="site-head no-print">
    <div class="wrap head-row">
      <a class="brand" href="#/"${page === "home" ? ' aria-current="page"' : ""}><span class="brand-mark" aria-hidden="true">⌂</span> Missing Middleware</a>
      <p class="head-sub">Wisconsin housing reform · statewide estimates</p>
      ${todayLink(page === "today")}
    </div>
    <div class="wrap">${pickerList((r) => `#/${esc(r.id)}/`)}</div>
  </header>
  <main id="main" class="wrap" tabindex="-1"></main>
  <div id="announce" class="sr-only" role="status" aria-live="polite" aria-atomic="true" data-testid="announce"></div>
  <footer class="site-foot">
    <div class="wrap"><p class="muted"><a href="${esc(REGISTRY.repo_url)}" target="_blank" rel="noopener">Source code and documentation<span class="sr-only"> (opens GitHub in a new tab)</span> ↗</a> · Apache-2.0</p></div>
  </footer>`;
  document.querySelector<HTMLAnchorElement>(".skip")!.addEventListener("click", (ev) => {
    ev.preventDefault();
    document.getElementById("main")!.focus();
  });
}

async function home(): Promise<void> {
  active?.m.leave?.();
  active = null;
  homeShell();
  document.title = "Introduction · Missing Middleware";
  const main = document.getElementById("main")!;
  introLoading(main);
  const n = await loadIntro();
  if (!isHome()) return;   // the reader moved on while the bundles loaded
  renderIntro(main, n);
  window.scrollTo(0, 0);
  if (lastKey) main.focus({ preventScroll: true });
  lastKey = "home";
}

/** True for the shared Wisconsin today page. */
function isWiToday(): boolean {
  return (location.hash.replace(/^#/, "") || "/").split("?")[0].replace(/\/$/, "") === "/wisconsin-today";
}

/** The shared Wisconsin today page: the baseline, all housing, then one section per reform (each from its own bundle). */
async function wisconsinToday(keepFocus: boolean): Promise<void> {
  const params = new URLSearchParams(location.hash.split("?")[1] ?? "");
  const y = window.scrollY;
  const focused = document.activeElement as HTMLElement | null;
  const wasHere = lastKey === "wisconsin-today" && !!document.querySelector('[data-testid="wisconsin-today"]');
  const sel = keepFocus && wasHere && focused && document.getElementById("main")?.contains(focused) ? selectorFor(focused) : null;
  if (!wasHere) {
    active?.m.leave?.();
    active = null;
    homeShell("today");
    document.getElementById("main")!.innerHTML = `<h1>Wisconsin today</h1><p class="muted" data-testid="wt-loading">Loading…</p>`;
  }
  document.title = "Wisconsin today · Missing Middleware";
  const load = async (id: string): Promise<unknown> => {
    const e = reformEntry(id);
    if (!e || e.status !== "ready" || !MODULES[id]) return null;
    try { return await dataFor(e, MODULES[id]); } catch { return null; }
  };
  const [adu, tod] = await Promise.all([load("adu"), load("tod")]);
  if (!isWiToday()) return;   // the reader moved on while the bundles loaded
  const d: TodayData = {
    adu: adu ? (adu as { b: TodayData["adu"] }).b : null,
    tod: tod as TodayData["tod"],
  };
  const main = document.getElementById("main")!;
  const pageEnv = (id: string): ShellEnv => {
    const base = envFor(reformEntry(id)!);
    return { ...base, replaceQuery(q) { const qs = q.toString(); history.replaceState(null, "", `#/wisconsin-today${qs ? `?${qs}` : ""}`); }, refresh: () => route(true) };
  };
  renderWisconsinToday(main, d, pageEnv, params);
  labelScrollers(main);
  if (keepFocus && wasHere) {
    window.scrollTo(0, y);
    if (sel) (main.querySelector(sel) as HTMLElement | null)?.focus();
  } else {
    const sec = params.get("section");
    const target = sec ? document.getElementById(`wt-${sec}`) : null;
    if (target) target.scrollIntoView(); else window.scrollTo(0, 0);
    if (lastKey) main.focus({ preventScroll: true });
  }
  lastKey = "wisconsin-today";
}

/** Reforms taken off the tool (parking, and TOD and parking together): their old addresses open the Introduction. */
const RETIRED = new Set(["parking", "combined"]);

function isRetired(): boolean {
  const seg = (location.hash.replace(/^#/, "") || "/").split("?")[0].split("/")[1] ?? "";
  return RETIRED.has(seg);
}

async function route(keepFocus = false): Promise<void> {
  if (isRetired()) {
    history.replaceState(null, "", "#/");
    return home();
  }
  if (isHome()) return home();
  if (isWiToday()) return wisconsinToday(keepFocus);
  const { reform, path: rawPath, params } = parse();
  let switched = false;
  if (!active || active.entry.id !== reform || moduleFor(active.entry) !== active.mod) {
    active = await activate(reform);
    switched = true;
  }
  const { entry, m } = active;
  // old addresses: "/today" opens this reform's section of Wisconsin today; "/compare" opens the Summary
  const has = (p: string) => m.routes.some((r) => (r.match ?? r.path) === p || r.path === p);
  if (rawPath.startsWith("/today") && !has("/today") && active.mod !== placeholderReform) {
    const q = new URLSearchParams();
    q.set("section", entry.id);
    const v = params.get("view");
    if (v) q.set("view", v);
    history.replaceState(null, "", `#/wisconsin-today?${q.toString()}`);
    return route();
  }
  if (rawPath.startsWith("/compare") && !has("/compare") && has("/summary")) {
    const qs = params.toString();
    history.replaceState(null, "", `#${prefixOf(entry.id)}/summary${qs ? `?${qs}` : ""}`);
    return route();
  }
  const known = m.routes.some((r) => rawPath.startsWith(r.match ?? r.path));
  const path = known ? rawPath : m.defaultPath;
  const main = document.getElementById("main")!;
  const focused = document.activeElement as HTMLElement | null;
  const activeSel = !switched && focused && main.contains(focused) ? selectorFor(focused) : null;
  const y = window.scrollY;
  m.render(path, params, main);
  labelScrollers(main);
  document.querySelectorAll<HTMLAnchorElement>("nav.tabs a").forEach((a) => {
    if (path.startsWith(a.dataset.route!)) a.setAttribute("aria-current", "page"); else a.removeAttribute("aria-current");
  });
  // the picker opens the same screen in another reform when that reform has it (unknown paths fall back to its first screen)
  document.querySelectorAll<HTMLAnchorElement>(".reform-nav a").forEach((a) => { a.href = `#${prefixOf(a.dataset.reform!)}${path}`; });
  // on narrow screens the tab row scrolls sideways: bring the current tab into view (horizontal only)
  const ol = document.querySelector<HTMLElement>("nav.tabs ol");
  const cur = document.querySelector<HTMLElement>('nav.tabs a[aria-current="page"]')?.parentElement;
  if (ol && cur && ol.scrollWidth > ol.clientWidth) ol.scrollLeft = Math.max(0, cur.offsetLeft - (ol.clientWidth - cur.offsetWidth) / 2);
  ol?.classList.toggle("at-end", !!ol && ol.scrollLeft + ol.clientWidth >= ol.scrollWidth - 2);
  const label = m.routes.find((r) => path.startsWith(r.match ?? r.path))?.label ?? m.routes[0].label;
  document.title = `${label} · ${m.titleSuffix} · Missing Middleware`;
  const key = `${entry.id}${path}`;
  if (keepFocus) {
    window.scrollTo(0, y);
    if (activeSel) (main.querySelector(activeSel) as HTMLElement | null)?.focus();
  } else {
    // "?section=<id>" opens the screen at that part of it (e.g. the ADU Why tab's in/out list)
    const sec = params.get("section");
    const target = sec ? main.querySelector<HTMLElement>(`#${CSS.escape(sec)}`) : null;
    if (target) {
      if (target instanceof HTMLDetailsElement) target.open = true;   // a folded list opens when linked to
      const head = document.querySelector<HTMLElement>(".site-head");
      if (head) document.documentElement.style.setProperty("--head-h", `${head.offsetHeight}px`);
      target.scrollIntoView();
      if (lastKey) main.focus({ preventScroll: true });
    } else if (key !== lastKey) {
      window.scrollTo(0, 0);
      if (lastKey) main.focus({ preventScroll: true });
    }
  }
  lastKey = key;
}

function selectorFor(el: HTMLElement): string | null {
  if (el.id) return `#${CSS.escape(el.id)}`;
  const inp = el as HTMLInputElement;
  if (inp.name && inp.value) return `input[name="${CSS.escape(inp.name)}"][value="${CSS.escape(inp.value)}"]`;
  return null;
}

function fail(e: Error): void {
  active = null;
  document.body.innerHTML = `<main class="wrap"><h1>The tool could not load its data</h1><p>${esc(e.message)}</p><p>Run <code>bash scripts/run_tool.sh</code> from the repository root.</p></main>`;
}

window.addEventListener("hashchange", () => { route().catch(fail); });
route().catch(fail);
