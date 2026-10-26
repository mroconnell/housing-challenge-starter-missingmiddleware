// The ADU reform: status strip, footer, vintages dialog and a router over its seven screens.
// The screens themselves live in ui/src/screens/ (owned by the ADU conductor).
import { type Ctx, type UIState } from "../../app";
import { loadBundle, type Bundle, type PathId, type UnknownId } from "../../data";
import { esc, int } from "../../format";
import { renderBrief } from "../../screens/brief";
import { renderCompare } from "../../screens/compare";
import { renderHowSure } from "../../screens/howsure";
import { renderPilot } from "../../screens/pilot";
import { renderToday } from "../../screens/today";
import { leaveWhere, renderWhere } from "../../screens/where";
import { renderWhy } from "../../screens/why";
import type { MountedReform, ReformModule, Route, ShellEnv } from "../types";

const ROUTES: Route[] = [
  { path: "/today", label: "Wisconsin today", n: 1 },
  { path: "/compare", label: "Statewide comparison", n: 2 },
  { path: "/where", label: "Where", n: 3 },
  { path: "/how-sure", label: "How sure", n: 4 },
  { path: "/why", label: "Why", n: 5 },
  { path: "/pilot/madison", label: "Pilot examples", n: 6, match: "/pilot" },
  { path: "/brief", label: "Brief", n: 7 },
];

const UNKNOWN_IDS: UnknownId[] = ["like_restricted", "like_prohibited", "like_benchmark"];

function mount(env: ShellEnv, data: unknown): MountedReform {
  const b = data as Bundle;
  const m = b.manifest;
  const ui: UIState = { scenario: "central", year: 2031, unknown: "like_restricted" };
  const ctx: Ctx = {
    b, ui,
    setScenario(p: PathId) {
      ui.scenario = p;
      writeUrl();
      env.refresh();
      const sc = ctx.scen(p);
      ctx.announce(`${sc.label} scenario: ${int(sc.additional_total)} permits added by the law over 2027 to 2031, ${int(sc.with_law_total)} in total with the law.`);
    },
    setUnknown(u: UnknownId) {
      ui.unknown = u;
      writeUrl();
      env.refresh();
      const v = b.unknown.variants.find((x) => x.id === u)!;
      ctx.announce(`Places with uncoded rules treated ${v.label.toLowerCase()}. Over 2027 to 2031, central scenario: baseline ${int(v.baseline_total)}, added by the law ${int(v.additional_total.central)}, total with the law ${int(v.with_law_total.central)} permits.`);
    },
    scen(p?: PathId) { return b.state.scenarios.find((s) => s.id === (p ?? ui.scenario))!; },
    link: (path: string) => env.link(path),
    announce: (msg: string) => env.announce(msg),
  };
  // keep the scenario and the unknown-rules choice in the URL so a copied link opens the same view
  function writeUrl(): void {
    const q = new URLSearchParams();
    if (ui.scenario !== "central") q.set("s", ui.scenario);
    if (ui.unknown !== "like_restricted") q.set("u", ui.unknown);
    env.replaceQuery(q);
  }
  return {
    routes: ROUTES,
    defaultPath: "/today",
    titleSuffix: "Wisconsin ADU law",
    statusStrip: `
        <span><strong>Adopted model</strong> (25 October 2026)</span>
        <span>Run <code data-testid="run-id">${esc(m.run_id)}</code></span>
        <span>Last observed year ${m.dates.last_observed_year}</span>
        <span>Forecast ${m.dates.forecast_years[0]}–${m.dates.forecast_years[m.dates.forecast_years.length - 1]}</span>
        <span>Law in effect 1 Jan 2027 (stylized)</span>
        <button type="button" class="linkish" id="vint-btn" aria-haspopup="dialog">Data vintages</button>`,
    footer: `
      <p><strong>Outcome:</strong> ${esc(m.outcome.short)}</p>
      <p class="pill-key"><span class="pill pill-observed">Observed</span> ${esc(m.status_pills.observed.split(": ")[1])} <span class="pill pill-calculated">Calculated</span> ${esc(m.status_pills.calculated.split(": ")[1])} <span class="pill pill-assumed">Assumed</span> ${esc(m.status_pills.assumed.split(": ")[1])} A dash (—) means missing, with the reason; it never means zero.</p>
      <p class="muted">Run <code>${esc(m.run_id)}</code> · ${esc(m.model_status)} · Validation: ${m.validation.passed} checks passed · <a href="${esc(m.repo_url)}" target="_blank" rel="noopener">Source code and documentation<span class="sr-only"> (opens GitHub in a new tab)</span> ↗</a> · Apache-2.0</p>`,
    extra: `
  <dialog id="vint" aria-labelledby="vint-h">
    <h2 id="vint-h">Data vintages and run</h2>
    <table class="data"><caption class="sr-only">Data vintages</caption><tbody>${m.vintages.map((v) => `<tr><th scope="row">${esc(v.what)}</th><td>${esc(v.vintage)}</td></tr>`).join("")}</tbody></table>
    <p><strong>Run</strong> <code>${esc(m.run_id)}</code>: a hash of the ${m.inputs.length} input files listed in <code>manifest.json</code>. ${esc(m.dates.effective)}.</p>
    <h3>Validation of this run</h3>
    <ul class="small">${m.validation.checks.map((c) => `<li>${c.passed ? "✓" : "✗"} ${esc(c.check)}: ${esc(c.detail)}</li>`).join("")}</ul>
    <form method="dialog"><button class="button" autofocus>Close</button></form>
  </dialog>`,
    bind() {
      const dlg = document.getElementById("vint") as HTMLDialogElement;
      document.getElementById("vint-btn")!.addEventListener("click", () => dlg.showModal());
    },
    render(path: string, params: URLSearchParams, main: HTMLElement) {
      const s = params.get("s");
      if (s === "lower" || s === "central" || s === "upper") ui.scenario = s;
      const u = params.get("u") as UnknownId | null;
      if (u && UNKNOWN_IDS.includes(u)) ui.unknown = u;
      if (!path.startsWith("/where")) leaveWhere();
      if (path.startsWith("/compare")) renderCompare(ctx, main);
      else if (path.startsWith("/where")) renderWhere(ctx, main);
      else if (path.startsWith("/how-sure")) renderHowSure(ctx, main);
      else if (path.startsWith("/why")) renderWhy(ctx, main);
      else if (path.startsWith("/pilot")) renderPilot(ctx, main, path.split("/")[2] ?? "madison");
      else if (path.startsWith("/brief")) renderBrief(ctx, main);
      else renderToday(ctx, main);
    },
    leave: () => leaveWhere(),
  };
}

export const aduReform: ReformModule = { load: () => loadBundle(), mount };
