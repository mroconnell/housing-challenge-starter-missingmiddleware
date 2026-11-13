// The ADU reform: status strip, footer, vintages dialog and a router over its seven screens.
// The screens themselves live in ui/src/screens/ (owned by the ADU conductor).
import { type Ctx, type Spread, type UIState } from "../../app";
import { loadBundle, type Bundle, type PathId, type UnknownId } from "../../data";
import { esc, int } from "../../format";
import { renderBrief } from "../../screens/brief";
import { aduSummaryInput } from "../../screens/compare";
import { renderHowSure } from "../../screens/howsure";
import { renderPilot } from "../../screens/pilot";
import { leaveWhere, renderWhere } from "../../screens/where";
import { renderWhy } from "../../screens/why";
import { loadWiHomes, renderSummary, type WiHomes } from "../../summary";
import type { MountedReform, ReformModule, Route, ShellEnv } from "../types";

// The same tabs, in the same order, for every reform (owner, 2026-11-11): Summary · Where · How sure · Why · Pilots · Brief.
const ROUTES: Route[] = [
  { path: "/summary", label: "Summary", n: 1 },
  { path: "/where", label: "Where", n: 2 },
  { path: "/how-sure", label: "How sure", n: 3 },
  { path: "/why", label: "Why", n: 4 },
  { path: "/pilot/madison", label: "Pilots", n: 5, match: "/pilot" },
  { path: "/brief", label: "Brief", n: 6 },
];

const UNKNOWN_IDS: UnknownId[] = ["like_restricted", "like_prohibited", "like_benchmark"];

interface AduData { b: Bundle; homes: WiHomes }

function mount(env: ShellEnv, data: unknown): MountedReform {
  const { b, homes } = data as AduData;
  const m = b.manifest;
  const ui: UIState = { scenario: "central", year: 2031, unknown: "like_restricted", spread: "model" };
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
      // Uniform display: the addition as a 90% range (typical adoption, the former central, times the statewide
      // range's low and high multipliers), as on the How sure tiles.
      const R = b.state.range90, typ = ctx.scen("central").additional_total, lo = R.low / typ, hi = R.high / typ;
      const add = v.additional_total.central;
      ctx.announce(`Places with uncoded rules treated ${v.label.toLowerCase()}. Over 2027 to 2031: ${int(v.baseline_total)} permits without the law; the law adds ${int(add * lo)} to ${int(add * hi)} permits (projected range); ${int(v.baseline_total + add * lo)} to ${int(v.baseline_total + add * hi)} permits in total with the law.`);
    },
    setSpread(s: Spread) {
      ui.spread = s;
      writeUrl();
      env.refresh();
      ctx.announce(s === "forest" ? `The law's addition spread by the causal forest pattern. ${b.forest.note}` : "The law's addition spread by our model.");
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
    if (ui.spread === "forest") q.set("w", "forest");   // "w" = where-spread; "s" is the scenario
    env.replaceQuery(q);
  }
  return {
    routes: ROUTES,
    defaultPath: "/summary",
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
    <ul class="small">${m.validation.checks.map((c) => `<li>${c.passed ? "Passed:" : "Failed:"} ${esc(c.check)}: ${esc(c.detail)}</li>`).join("")}</ul>
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
      // like s= and u=, an absent w= keeps the current choice (tab links carry no query)
      const w = params.get("w");
      if (w === "forest" || w === "model") ui.spread = w;
      if (!path.startsWith("/where")) leaveWhere();
      if (path.startsWith("/where")) renderWhere(ctx, main);
      else if (path.startsWith("/how-sure")) renderHowSure(ctx, main);
      else if (path.startsWith("/why")) renderWhy(ctx, main);
      else if (path.startsWith("/pilot")) renderPilot(ctx, main, path.split("/")[2] ?? "madison");
      else if (path.startsWith("/brief")) renderBrief(ctx, main);
      else renderSummary(main, aduSummaryInput(ctx, homes), env, params);
    },
    leave: () => leaveWhere(),
  };
}

async function load(): Promise<AduData> {
  const [b, homes] = await Promise.all([loadBundle(), loadWiHomes()]);
  return { b, homes };
}

export const aduReform: ReformModule = { load, mount };
