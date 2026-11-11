// The transit-oriented density (TOD) reform: six screens over the bundle written by scripts/build_tod_bundle.py.
// The browser only selects, sorts, sums and formats bundle values; it never computes a forecast.
import "./tod.css";
import type { MountedReform, ReformEntry, ReformModule, Route, ShellEnv } from "../types";
import { esc } from "../../format";
import type { TodBundle } from "./types";
import { brief, howSure, pilot, todSummaryInput, where, why } from "./screens";
import { loadWiHomes, renderSummary, type WiHomes } from "../../summary";

async function load(entry: ReformEntry): Promise<TodBundle & { homes: WiHomes }> {
  const root = `${import.meta.env.BASE_URL}${entry.bundle_root}`;
  const get = async (p: string) => { const r = await fetch(p); if (!r.ok) throw new Error(`${p}: ${r.status}`); return r.json(); };
  const { run_id } = await get(`${root}latest.json`);
  const dir = `${root}${run_id}/`;
  const [[manifest, statewide, areas, map, howsure, why_, pilots, today_], homes] = await Promise.all([Promise.all(
    ["manifest", "statewide", "areas", "map", "howsure", "why", "pilots", "today"].map((f) => get(`${dir}${f}.json`))), loadWiHomes()]);
  return { manifest, statewide, areas, map, howsure, why: why_, pilots, today: today_, homes };
}

// The same tabs, in the same order, for every reform (owner, 2026-11-11). The former "Wisconsin today" content is on
// the shared Wisconsin today page; the former Statewide comparison is Summary plus How sure's Details.
const ROUTES: Route[] = [
  { path: "/summary", label: "Summary", n: 1 },
  { path: "/where", label: "Where", n: 2 },
  { path: "/how-sure", label: "How sure", n: 3 },
  { path: "/why", label: "Why", n: 4 },
  { path: "/pilot/milwaukee-connect-1", label: "Pilots", n: 5, match: "/pilot" },
  { path: "/brief", label: "Brief", n: 6 },
];

function mount(env: ShellEnv, data: unknown): MountedReform {
  const b = data as TodBundle & { homes: WiHomes };
  const m = b.manifest;
  return {
    routes: ROUTES,
    defaultPath: "/summary",
    titleSuffix: "Wisconsin transit-oriented density law",
    statusStrip: `<span><strong>Adopted model</strong> (27 October 2026)</span><span>Run <code data-testid="run-id">${esc(m.run_id)}</code></span><span>Last observed year ${m.dates.last_observed_year}</span><span>Forecast 2027–2031</span><span>Law in effect 1 Jan 2027 (stylized)</span>`,
    footer: `<p><strong>Outcome:</strong> <span data-testid="outcome">${esc(m.outcome.short)}</span></p>
      <p class="pill-key"><span class="pill pill-observed">Observed</span> counted in a published source. <span class="pill pill-calculated">Calculated</span> computed from observed inputs and stated rules. <span class="pill pill-assumed">Assumed</span> a judgment where no data decide it. A dash (—) means missing, never zero.</p>
      <p class="muted">Run <code>${esc(m.run_id)}</code> · Validation: ${m.validation.passed} checks passed, ${m.validation.failed} failed · <a href="${esc(m.repo_url)}" target="_blank" rel="noopener">Source code and documentation<span class="sr-only"> (opens GitHub in a new tab)</span> ↗</a> · Apache-2.0</p>`,
    extra: "",
    bind() { /* nothing to bind */ },
    render(path: string, params: URLSearchParams, main: HTMLElement) {
      if (path.startsWith("/where")) where(b, env, params, main);
      else if (path.startsWith("/how-sure")) howSure(b, env, main);
      else if (path.startsWith("/why")) why(b, main);
      else if (path.startsWith("/pilot")) pilot(b, env, path.split("/")[2] ?? "", main);
      else if (path.startsWith("/brief")) brief(b, main);
      else renderSummary(main, todSummaryInput(b, b.homes), env, params);
    },
  };
}

export const todReform: ReformModule = { load, mount };
