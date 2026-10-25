// App shell: header, status strip, tab navigation, footer and a hash router over the seven screens.
import "./style.css";
import type { Ctx, UIState } from "./app";
import { loadBundle, type Bundle, type PathId } from "./data";
import { esc } from "./format";
import { renderBrief } from "./screens/brief";
import { renderCompare } from "./screens/compare";
import { renderHowSure } from "./screens/howsure";
import { renderPilot } from "./screens/pilot";
import { renderToday } from "./screens/today";
import { leaveWhere, renderWhere } from "./screens/where";
import { renderWhy } from "./screens/why";

const ROUTES = [
  { path: "/today", label: "Wisconsin today", n: 1 },
  { path: "/compare", label: "Statewide comparison", n: 2 },
  { path: "/where", label: "Where", n: 3 },
  { path: "/how-sure", label: "How sure", n: 4 },
  { path: "/why", label: "Why", n: 5 },
  { path: "/pilot/madison", label: "Pilot examples", n: 6, match: "/pilot" },
  { path: "/brief", label: "Brief", n: 7 },
];

const ui: UIState = { scenario: "central", year: 2031 };

function parse(): { path: string; params: URLSearchParams } {
  const raw = location.hash.replace(/^#/, "") || "/today";
  const [path, q] = raw.split("?");
  return { path: path || "/today", params: new URLSearchParams(q ?? "") };
}

function shell(b: Bundle): void {
  const m = b.manifest;
  document.title = `${m.title} · Missing Middleware`;
  document.body.innerHTML = `
  <a class="skip" href="#main">Skip to main content</a>
  <header class="site-head no-print">
    <div class="wrap head-row">
      <a class="brand" href="#/today"><span class="brand-mark" aria-hidden="true">⌂</span> Missing Middleware</a>
      <p class="head-sub">Wisconsin ADU law · statewide estimates</p>
    </div>
    <div class="status-strip" role="note" aria-label="Model run status">
      <div class="wrap">
        <span><strong>Adopted model</strong> (Gate 3, AQ-042)</span>
        <span>Run <code data-testid="run-id">${esc(m.run_id)}</code></span>
        <span>Last observed year ${m.dates.last_observed_year}</span>
        <span>Forecast ${m.dates.forecast_years[0]}–${m.dates.forecast_years[m.dates.forecast_years.length - 1]}</span>
        <span>Law in effect 1 Jan 2027 (stylized)</span>
        <button type="button" class="linkish" id="vint-btn" aria-haspopup="dialog">Data vintages</button>
      </div>
    </div>
    <nav class="tabs" aria-label="Screens"><div class="wrap"><ol>${ROUTES.map((r) => `<li><a href="#${r.path}" data-route="${r.match ?? r.path}"><span class="tab-n" aria-hidden="true">${r.n}</span> ${esc(r.label)}</a></li>`).join("")}</ol></div></nav>
  </header>
  <main id="main" class="wrap" tabindex="-1"></main>
  <footer class="site-foot">
    <div class="wrap">
      <p><strong>Outcome:</strong> ${esc(m.outcome.short)}</p>
      <p class="pill-key"><span class="pill pill-observed">Observed</span> ${esc(m.status_pills.observed.split(": ")[1])} <span class="pill pill-calculated">Calculated</span> ${esc(m.status_pills.calculated.split(": ")[1])} <span class="pill pill-assumed">Assumed</span> ${esc(m.status_pills.assumed.split(": ")[1])} A dash (—) means missing, with the reason; it never means zero.</p>
      <p class="muted">Run <code>${esc(m.run_id)}</code> · ${esc(m.model_status)} · Validation: ${m.validation.passed} checks passed · <a href="${esc(m.repo_url)}" target="_blank" rel="noopener">Source code and documentation<span class="sr-only"> (opens GitHub in a new tab)</span> ↗</a> · Apache-2.0</p>
    </div>
  </footer>
  <dialog id="vint" aria-labelledby="vint-h">
    <h2 id="vint-h">Data vintages and run</h2>
    <table class="data"><caption class="sr-only">Data vintages</caption><tbody>${m.vintages.map((v) => `<tr><th scope="row">${esc(v.what)}</th><td>${esc(v.vintage)}</td></tr>`).join("")}</tbody></table>
    <p><strong>Run</strong> <code>${esc(m.run_id)}</code>: a hash of the ${m.inputs.length} input files listed in <code>manifest.json</code>. ${esc(m.dates.effective)}.</p>
    <h3>Validation of this run</h3>
    <ul class="small">${m.validation.checks.map((c) => `<li>${c.passed ? "✓" : "✗"} ${esc(c.check)}: ${esc(c.detail)}</li>`).join("")}</ul>
    <form method="dialog"><button class="button" autofocus>Close</button></form>
  </dialog>`;
  document.querySelector<HTMLAnchorElement>(".skip")!.addEventListener("click", (e) => {
    e.preventDefault();
    document.getElementById("main")!.focus();
  });
  const dlg = document.getElementById("vint") as HTMLDialogElement;
  document.getElementById("vint-btn")!.addEventListener("click", () => dlg.showModal());
}

function start(b: Bundle): void {
  shell(b);
  const main = document.getElementById("main")!;
  let lastPath = "";
  const ctx: Ctx = {
    b, ui,
    setScenario(p: PathId) { ui.scenario = p; route(true); },
    scen(p?: PathId) { return b.state.scenarios.find((s) => s.id === (p ?? ui.scenario))!; },
    link(path: string) { return `#${path}`; },
  };
  function route(keepFocus = false): void {
    const { path, params } = parse();
    const s = params.get("s");
    if (s === "lower" || s === "central" || s === "upper") ui.scenario = s;
    const active = document.activeElement as HTMLElement | null;
    const activeSel = active && main.contains(active) ? selectorFor(active) : null;
    const y = window.scrollY;
    if (!path.startsWith("/where")) leaveWhere();
    if (path.startsWith("/compare")) renderCompare(ctx, main);
    else if (path.startsWith("/where")) renderWhere(ctx, main);
    else if (path.startsWith("/how-sure")) renderHowSure(ctx, main);
    else if (path.startsWith("/why")) renderWhy(ctx, main);
    else if (path.startsWith("/pilot")) renderPilot(ctx, main, path.split("/")[2] ?? "madison");
    else if (path.startsWith("/brief")) renderBrief(ctx, main);
    else renderToday(ctx, main);
    document.querySelectorAll<HTMLAnchorElement>("nav.tabs a").forEach((a) => {
      if (path.startsWith(a.dataset.route!)) a.setAttribute("aria-current", "page"); else a.removeAttribute("aria-current");
    });
    const label = ROUTES.find((r) => path.startsWith(r.match ?? r.path))?.label ?? "Wisconsin today";
    document.title = `${label} · Wisconsin ADU law · Missing Middleware`;
    if (keepFocus) {
      window.scrollTo(0, y);
      if (activeSel) (main.querySelector(activeSel) as HTMLElement | null)?.focus();
    } else if (path !== lastPath) {
      window.scrollTo(0, 0);
      if (lastPath) main.focus({ preventScroll: true });
    }
    lastPath = path;
  }
  window.addEventListener("hashchange", () => route());
  route();
}

function selectorFor(el: HTMLElement): string | null {
  if (el.id) return `#${CSS.escape(el.id)}`;
  const inp = el as HTMLInputElement;
  if (inp.name && inp.value) return `input[name="${CSS.escape(inp.name)}"][value="${CSS.escape(inp.value)}"]`;
  return null;
}

loadBundle().then(start).catch((e: Error) => {
  document.body.innerHTML = `<main class="wrap"><h1>The tool could not load its data</h1><p>${esc(e.message)}</p><p>Run <code>bash scripts/run_tool.sh</code> from the repository root.</p></main>`;
});
