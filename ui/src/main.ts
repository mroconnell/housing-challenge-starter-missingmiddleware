// Multi-reform shell: header with the reform picker, status strip, screens navigation, footer, and a hash
// router. Each reform (ADU, transit-oriented density, parking) fills the strip, tabs, footer and screens through
// the contract in ui/src/scenarios/types.ts (docs/shared/SCENARIO_CONTRACT.md).
//
// URLs: the default reform has no prefix ("#/today"), so existing ADU links keep working; other reforms are
// prefixed with their id ("#/tod/about"). The query part ("?s=upper") belongs to the reform.
import "./style.css";
import "./scenarios/shell.css";
import { labelScrollers } from "./app";
import { esc } from "./format";
import { aduReform } from "./scenarios/adu";
import { placeholderReform } from "./scenarios/placeholder";
import { REGISTRY, reformEntry, type MountedReform, type ReformEntry, type ReformModule, type ShellEnv } from "./scenarios/types";

/** Code for each reform id; a reform without its own module (or not yet "ready") gets the holding page. */
const MODULES: Record<string, ReformModule> = { adu: aduReform };

function moduleFor(e: ReformEntry): ReformModule {
  return e.status === "ready" && MODULES[e.id] ? MODULES[e.id] : placeholderReform;
}

const prefixOf = (id: string) => (id === REGISTRY.default ? "" : `/${id}`);

/** Split the hash into the reform id, the reform-relative path and the query. */
function parse(): { reform: string; path: string; params: URLSearchParams } {
  const raw = location.hash.replace(/^#/, "") || "/";
  const [full, q] = raw.split("?");
  const seg = (full || "/").split("/")[1] ?? "";
  const named = reformEntry(seg);
  const reform = named ? named.id : REGISTRY.default;
  const path = named ? (full.slice(seg.length + 1) || "/") : (full || "/");
  return { reform, path, params: new URLSearchParams(q ?? "") };
}

interface Active { entry: ReformEntry; m: MountedReform }
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

function picker(current: ReformEntry): string {
  return `<nav class="reform-nav" aria-label="Policy reform" data-testid="reform-picker"><span class="reform-nav-label" aria-hidden="true">Policy reform:</span><ul>${REGISTRY.reforms.map((r) => `
    <li><a href="#${prefixOf(r.id)}/" data-reform="${esc(r.id)}" ${r.id === current.id ? 'aria-current="page"' : ""}>${esc(r.label)}${r.status === "ready" ? "" : ' <span class="reform-dev">(in development)</span>'}</a></li>`).join("")}</ul></nav>`;
}

function shell(e: ReformEntry, m: MountedReform): void {
  const pre = prefixOf(e.id);
  document.body.innerHTML = `
  <a class="skip" href="#main">Skip to main content</a>
  <header class="site-head no-print">
    <div class="wrap head-row">
      <a class="brand" href="#${pre}${m.defaultPath}"><span class="brand-mark" aria-hidden="true">⌂</span> Missing Middleware</a>
      <p class="head-sub">${esc(e.subtitle)}</p>
    </div>
    <div class="wrap">${picker(e)}</div>
    <div class="status-strip" role="note" aria-label="Model run status">
      <div class="wrap">${m.statusStrip}</div>
    </div>
    <nav class="tabs" aria-label="Screens"><div class="wrap"><ol>${m.routes.map((r) => `<li><a href="#${pre}${r.path}" data-route="${r.match ?? r.path}"><span class="tab-n" aria-hidden="true">${r.n}</span> ${esc(r.label)}</a></li>`).join("")}</ol></div></nav>
  </header>
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

async function activate(id: string): Promise<Active> {
  const entry = reformEntry(id)!;
  const mod = moduleFor(entry);
  if (!cache.has(id)) cache.set(id, await mod.load(entry));
  const pre = prefixOf(id);
  const env: ShellEnv = {
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
  active?.m.leave?.();
  const m = mod.mount(env, cache.get(id));
  shell(entry, m);
  return { entry, m };
}

async function route(keepFocus = false): Promise<void> {
  const { reform, path: rawPath, params } = parse();
  let switched = false;
  if (!active || active.entry.id !== reform) {
    active = await activate(reform);
    switched = true;
  }
  const { entry, m } = active;
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
  } else if (key !== lastKey) {
    window.scrollTo(0, 0);
    if (lastKey) main.focus({ preventScroll: true });
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
