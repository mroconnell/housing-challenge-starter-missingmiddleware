// TOD and parking together: three screens over the bundle written by scripts/build_combined_bundle.py
// (docs/shared/SCENARIO_CONTRACT.md section 9). The browser only selects, sorts, sums and formats bundle values;
// both combining rules are applied by the builder.
import "./combined.css";
import { COLORS, DASH } from "../../app";
import { legendHTML, xyChart } from "../../charts";
import { esc, int, pill, small, YEARS } from "../../format";
import type { MountedReform, ReformEntry, ReformModule, Route, ShellEnv } from "../types";

// ---- bundle types --------------------------------------------------------------------------------
type Role = "lower" | "central" | "upper";
type SeriesKey = "tod" | "parking" | "parking_near" | "parking_elsewhere" | "near_a" | "near_b" | "both_a" | "both_b";
interface RoleRow {
  role: Role; tod_path: string; tod_label: string; parking_path: string; parking_label: string;
  by_year: Record<SeriesKey, number[]>; total: Record<SeriesKey, number>; overlap_counted_twice: number;
}
interface Statewide {
  years: number[]; baseline_total: number; baseline_note: string; roles: RoleRow[];
  rules: Record<"a" | "b", { label: string; info: string }>; rule_c: string; double_count: string; role_labels: Record<Role, string>;
}
type Cols = [number, number, number, number, number]; // tod, parking_near, parking_elsewhere, total_a, total_b
interface AreaRow { id: string; name: string; county: string | null; baseline: number; share_near: number; lower: Cols; central: Cols; upper: Cols }
interface Areas { munis: AreaRow[]; counties: (AreaRow & { places: number })[]; cols: string[]; col_labels: Record<string, string>; sources: { tod: string; parking: string } }
interface Manifest {
  run_id: string; title: string; outcome: { short: string; long: string }; baseline_version: string; sources: { tod: string; parking: string };
  validation: { passed: number; failed: number; checks: { check: string; passed: boolean; detail: string }[] }; repo_url: string;
}
export interface CombinedBundle { manifest: Manifest; statewide: Statewide; areas: Areas }

async function load(entry: ReformEntry): Promise<CombinedBundle> {
  const root = `${import.meta.env.BASE_URL}${entry.bundle_root}`;
  const get = async (p: string) => { const r = await fetch(p); if (!r.ok) throw new Error(`${p}: ${r.status}`); return r.json(); };
  const { run_id } = await get(`${root}latest.json`);
  const dir = `${root}${run_id}/`;
  const [manifest, statewide, areas] = await Promise.all(["manifest", "statewide", "areas"].map((f) => get(`${dir}${f}.json`)));
  return { manifest, statewide, areas };
}

// ---- helpers ---------------------------------------------------------------------------------------
const ROLES: Role[] = ["lower", "central", "upper"];
const C = { tod: COLORS.central, parking: COLORS.lower, a: COLORS.upper, b: COLORS.ref };
const ROUTES: Route[] = [
  { path: "/compare", label: "Statewide comparison", n: 1 },
  { path: "/where", label: "By place", n: 2 },
  { path: "/about", label: "How it is combined", n: 3 },
];
const roleOf = (p: URLSearchParams): Role => (ROLES.includes(p.get("p") as Role) ? (p.get("p") as Role) : "upper");
const row = (s: Statewide, r: Role) => s.roles.find((x) => x.role === r)!;
const pairing = (x: RoleRow) => `TOD ${x.tod_label.toLowerCase()} with parking ${x.parking_label.toLowerCase()}`;

function rolePicker(s: Statewide, current: Role, name: string): string {
  return `<form class="combined-picker"><fieldset class="seg"><legend>Which paths to pair</legend>${ROLES.map((r) => {
    const x = row(s, r);
    return `<label><input type="radio" name="${name}" value="${r}" ${r === current ? "checked" : ""}> ${esc(s.role_labels[r])}: ${esc(pairing(x))}</label>`;
  }).join("")}</fieldset></form>`;
}

function bindRole(main: HTMLElement, env: ShellEnv, params: URLSearchParams, s: Statewide, name: string): void {
  main.querySelectorAll<HTMLInputElement>(`input[name="${name}"]`).forEach((i) => i.addEventListener("change", () => {
    const q = new URLSearchParams(params);
    q.set("p", i.value);
    env.replaceQuery(q); env.refresh();
    const x = row(s, i.value as Role);
    env.announce(`${s.role_labels[x.role]}. Both reforms together, 2027–2031: ${int(x.total.both_a)} under rule (a), ${int(x.total.both_b)} under rule (b).`);
  }));
}

// ---- 1. Statewide comparison -------------------------------------------------------------------
function compare(b: CombinedBundle, env: ShellEnv, params: URLSearchParams, main: HTMLElement): void {
  const s = b.statewide;
  const role = roleOf(params);
  const x = row(s, role);
  const t = x.total;
  const same = Math.round(t.both_a) === Math.round(t.both_b);
  const tile = (id: string, label: string, v: number, note: string, accent = false) => `<section class="tile${accent ? " tile-accent" : ""}"><h2 class="tile-label">${esc(label)}</h2>
      <p class="tile-num" data-testid="${id}">${int(v)}</p><p class="tile-sub">extra homes permitted, 2027–2031 ${pill("calculated")}</p><p class="tile-note">${note}</p></section>`;
  main.innerHTML = `
  <div class="combined-view">
  <h1>Transit-oriented density and parking reform together</h1>
  <p class="lede">How many more homes would Wisconsin permit over 2027–2031 if it passed both laws from 1 January 2027 (an illustrative start date), compared with each law alone? All figures are extra housing units in issued building permits, compared with current law.</p>
  ${rolePicker(s, role, "combined-role")}
  <div class="tiles tiles-4 combined-tiles">
    ${tile("alone-tod", `TOD alone: ${x.tod_label}`, t.tod, "Near major transit stops only.")}
    ${tile("alone-parking", `Parking alone: ${x.parking_label}`, t.parking, `${int(t.parking_near)} near stops and ${int(t.parking_elsewhere)} elsewhere.`)}
    ${tile("both-a", s.rules.a.label, t.both_a, "Adds both near stops: may count some homes twice.", true)}
    ${tile("both-b", s.rules.b.label, t.both_b, "Takes the larger of the two near stops.", true)}
  </div>
  <section class="card combined-double" data-testid="double-count"><h2>Why there are two numbers for both laws</h2>
    <p>${esc(s.double_count)}</p>
    <ul>
      <li><strong>${esc(s.rules.a.label)}.</strong> ${esc(s.rules.a.info)}</li>
      <li><strong>${esc(s.rules.b.label)}.</strong> ${esc(s.rules.b.info)}</li>
    </ul>
    <p data-testid="overlap">${same
      ? `In this pairing the two rules give the same total, because the parking path adds nothing (${esc(x.parking_label.toLowerCase())}).`
      : `In this pairing the two rules differ by <strong>${int(x.overlap_counted_twice)}</strong> homes over five years: the most that could be counted twice. The true combined effect has not been measured: it could lie between the two, or above rule (a) if the reforms reinforce each other.`}</p>
    <p class="small muted">Rule (b) is taken place by place and year, so it can be larger than either law alone statewide.</p>
  </section>
  <section class="card"><h2>Extra homes permitted each year</h2>
    <div class="chart-box" id="combined-chart"></div>
    ${legendHTML([{ name: `TOD alone`, color: C.tod, dash: DASH.central }, { name: `Parking alone`, color: C.parking, dash: DASH.lower }, { name: s.rules.a.label, color: C.a, dash: DASH.upper }, { name: s.rules.b.label, color: C.b, dash: DASH.ref }])}
    <div class="table-wrap"><table class="data" data-testid="combined-years"><caption>Extra homes permitted by year, ${esc(s.role_labels[role].toLowerCase())} (${esc(pairing(x))})</caption>
      <thead><tr><th scope="col">Year</th><th scope="col" class="num">TOD alone</th><th scope="col" class="num">Parking alone</th><th scope="col" class="num">Both, rule (a)</th><th scope="col" class="num">Both, rule (b)</th></tr></thead>
      <tbody>${s.years.map((y, i) => `<tr><th scope="row">${y}</th><td class="num">${int(x.by_year.tod[i])}</td><td class="num">${int(x.by_year.parking[i])}</td><td class="num">${int(x.by_year.both_a[i])}</td><td class="num">${int(x.by_year.both_b[i])}</td></tr>`).join("")}
      <tr class="combined-total"><th scope="row">2027–2031</th><td class="num">${int(t.tod)}</td><td class="num">${int(t.parking)}</td><td class="num">${int(t.both_a)}</td><td class="num">${int(t.both_b)}</td></tr></tbody></table></div>
    <p class="small muted">Current law over the same years: ${int(s.baseline_total)} homes permitted statewide. ${esc(s.baseline_note)} Yearly rows may not add exactly to the totals because of rounding.</p></section>
  <section class="card"><h2>Every pairing, statewide, 2027–2031</h2>
    <div class="table-wrap"><table class="data" data-testid="combined-roles"><caption>Extra homes permitted, 2027–2031, for each pairing of paths</caption>
      <thead><tr><th scope="col">Pairing</th><th scope="col" class="num">TOD alone</th><th scope="col" class="num">Parking alone</th><th scope="col" class="num">Both, rule (a)</th><th scope="col" class="num">Both, rule (b)</th></tr></thead>
      <tbody>${s.roles.map((r) => `<tr><th scope="row">${esc(s.role_labels[r.role])}<br><span class="small muted">${esc(pairing(r))}</span></th><td class="num">${int(r.total.tod)}</td><td class="num">${int(r.total.parking)}</td><td class="num">${int(r.total.both_a)}</td><td class="num">${int(r.total.both_b)}</td></tr>`).join("")}</tbody></table></div>
    <p class="small muted">Paths are paired by meaning: low with low, central with central, high with high. They are never crossed. The parking reform's central path adds nothing, so in the low and central pairings both laws together equal TOD alone.</p></section>
  <section class="card combined-rule-c" data-testid="rule-c"><h2>A third rule, not yet measured</h2><p>${esc(s.rule_c)}</p></section>
  <p><a class="button" href="${env.link(`/where?p=${role}`)}">Next: by place →</a></p>
  </div>`;
  xyChart(document.getElementById("combined-chart")!, {
    title: `Extra homes permitted each year, ${s.role_labels[role].toLowerCase()}`,
    desc: `2027–2031 totals: TOD alone ${int(t.tod)}, parking alone ${int(t.parking)}, both under rule (a) ${int(t.both_a)}, both under rule (b) ${int(t.both_b)}. The table below has the same values by year.`,
    yLabel: "Extra homes per year", xTicks: YEARS,
    series: [
      { name: "TOD alone", values: s.years.map((y, i) => ({ x: y, y: x.by_year.tod[i] })), color: C.tod, dash: DASH.central, marker: "circle" },
      { name: "Parking alone", values: s.years.map((y, i) => ({ x: y, y: x.by_year.parking[i] })), color: C.parking, dash: DASH.lower, marker: "square" },
      { name: s.rules.a.label, values: s.years.map((y, i) => ({ x: y, y: x.by_year.both_a[i] })), color: C.a, dash: DASH.upper, marker: "circle" },
      { name: s.rules.b.label, values: s.years.map((y, i) => ({ x: y, y: x.by_year.both_b[i] })), color: C.b, dash: DASH.ref, marker: "square" },
    ],
  });
  bindRole(main, env, params, s, "combined-role");
}

// ---- 2. By place --------------------------------------------------------------------------------------
type Level = "place" | "county";
const SORTS: [string, string, (r: AreaRow & { places?: number }, role: Role) => number | string][] = [
  ["name", "Place", (r) => r.name],
  ["tod", "TOD alone", (r, ro) => r[ro][0]],
  ["pn", "Parking near stops", (r, ro) => r[ro][1]],
  ["pe", "Parking elsewhere", (r, ro) => r[ro][2]],
  ["a", "Both, rule (a)", (r, ro) => r[ro][3]],
  ["b", "Both, rule (b)", (r, ro) => r[ro][4]],
];

function where(b: CombinedBundle, env: ShellEnv, params: URLSearchParams, main: HTMLElement): void {
  const s = b.statewide;
  const role = roleOf(params);
  const x = row(s, role);
  const level: Level = params.get("level") === "county" ? "county" : "place";
  const sortKey = SORTS.some(([k]) => k === params.get("sort")) ? params.get("sort")! : "a";
  const dir = params.get("dir") === "asc" ? "asc" : "desc";
  const q = (params.get("q") ?? "").trim().toLowerCase();
  const all = level === "county" ? b.areas.counties : b.areas.munis;
  const nonzero = all.filter((r) => r[role][3] > 0);
  const fn = SORTS.find(([k]) => k === sortKey)![2];
  const rows = nonzero.slice().sort((p, r) => {
    const u = fn(p, role), v = fn(r, role);
    const c = typeof u === "string" ? u.localeCompare(v as string) : (u as number) - (v as number);
    return dir === "asc" ? c : -c;
  });
  const head = SORTS.map(([k, label]) => {
    const lab = k === "name" ? (level === "county" ? "County" : "Place") : label;
    const cur = k === sortKey;
    return `<th scope="col" class="${k === "name" ? "" : "num"}" ${cur ? `aria-sort="${dir === "asc" ? "ascending" : "descending"}"` : ""}><button type="button" class="sort combined-sort-btn" data-sort="${k}">${esc(lab)} <span class="combined-sort-ind" aria-hidden="true">${cur ? (dir === "asc" ? "▲" : "▼") : "↕"}</span></button></th>`;
  });
  if (level === "place") head.splice(1, 0, `<th scope="col">County</th>`);
  const matches = (r: AreaRow) => !q || r.name.toLowerCase().includes(q) || (r.county ?? "").toLowerCase().includes(q);
  main.innerHTML = `
  <div class="combined-view">
  <h1>Both laws together, by place</h1>
  <p class="lede">Each municipality's extra homes over 2027–2031 from each law alone and from both together. Near major transit stops the two laws are combined two ways (rule (a) adds them, rule (b) takes the larger); away from stops only the parking law acts, so the two rules agree there.</p>
  ${rolePicker(s, role, "combined-where-role")}
  <section class="card">
    <div class="combined-controls">
      <form id="combined-level"><fieldset class="seg"><legend>Show by</legend><label><input type="radio" name="combined-level" value="place" ${level === "place" ? "checked" : ""}> Cities, villages and towns</label><label><input type="radio" name="combined-level" value="county" ${level === "county" ? "checked" : ""}> Counties</label></fieldset></form>
      <div class="combined-search"><label for="combined-q">Find a ${level === "county" ? "county" : "place or county"}</label><input id="combined-q" type="search" autocomplete="off" value="${esc(params.get("q") ?? "")}"></div>
    </div>
    <p class="small" id="combined-count" data-testid="combined-count">${int(rows.filter(matches).length)} of ${int(nonzero.length)} ${level === "county" ? "counties" : "places"} shown</p>
    <div class="table-wrap"><table class="data combined-table" data-testid="combined-where"><caption>Extra homes, ${esc(s.role_labels[role].toLowerCase())} (${esc(pairing(x))}), by ${level === "county" ? "county" : "municipality"}, 2027–2031. Select a column heading to sort.</caption>
      <thead><tr>${head.join("")}</tr></thead>
      <tbody>${rows.map((r) => `<tr data-name="${esc(`${r.name} ${r.county ?? ""}`.toLowerCase())}" ${matches(r) ? "" : "hidden"}><th scope="row">${esc(r.name)}</th>${level === "place" ? `<td>${esc(r.county ?? "—")}</td>` : ""}${r[role].map((v) => `<td class="num">${small(v)}</td>`).join("")}</tr>`).join("")}</tbody>
      <tfoot><tr class="combined-total"><th scope="row">Wisconsin</th>${level === "place" ? "<td></td>" : ""}<td class="num" data-testid="where-total-tod">${int(x.total.tod)}</td><td class="num">${int(x.total.parking_near)}</td><td class="num">${int(x.total.parking_elsewhere)}</td><td class="num" data-testid="where-total-a">${int(x.total.both_a)}</td><td class="num" data-testid="where-total-b">${int(x.total.both_b)}</td></tr></tfoot></table></div>
    <p class="small muted">Places with no extra homes in this pairing are left out. Parking's extra homes are split between near stops and elsewhere by each place's share of homes near qualifying stops. "under 1" means more than zero but less than half a home. Rows may not add exactly to the Wisconsin total because of rounding.</p>
  </section>
  </div>`;
  const setQ = (k: string, v: string | null, msg?: string) => {
    const nq = new URLSearchParams(params);
    if (v === null || v === "") nq.delete(k); else nq.set(k, v);
    if (k === "level") { nq.delete("sort"); nq.delete("dir"); }
    env.replaceQuery(nq); env.refresh();
    if (msg) env.announce(msg);
  };
  bindRole(main, env, params, s, "combined-where-role");
  main.querySelectorAll<HTMLInputElement>('input[name="combined-level"]').forEach((i) => i.addEventListener("change", () => setQ("level", i.value, `Table: ${i.value === "county" ? "counties" : "cities, villages and towns"}.`)));
  main.querySelectorAll<HTMLButtonElement>("button[data-sort]").forEach((btn) => btn.addEventListener("click", () => {
    const k = btn.dataset.sort!;
    const nd = k === sortKey ? (dir === "asc" ? "desc" : "asc") : k === "name" ? "asc" : "desc";
    const nq = new URLSearchParams(params);
    nq.set("sort", k); nq.set("dir", nd);
    env.replaceQuery(nq); env.refresh();
    env.announce(`Table sorted by ${btn.textContent!.replace(/[▲▼↕]/g, "").trim()}, ${nd === "asc" ? "ascending" : "descending"}.`);
  }));
  // filter in place (no re-render) so typing keeps the caret; the query is kept in the URL
  const input = main.querySelector<HTMLInputElement>("#combined-q")!;
  const count = main.querySelector<HTMLElement>("#combined-count")!;
  input.addEventListener("input", () => {
    const v = input.value.trim().toLowerCase();
    let n = 0;
    main.querySelectorAll<HTMLTableRowElement>(".combined-table tbody tr").forEach((tr) => { const ok = !v || tr.dataset.name!.includes(v); tr.hidden = !ok; if (ok) n++; });
    count.textContent = `${int(n)} of ${int(nonzero.length)} ${level === "county" ? "counties" : "places"} shown`;
    const nq = new URLSearchParams(params);
    if (input.value) nq.set("q", input.value); else nq.delete("q");
    env.replaceQuery(nq);
  });
  input.addEventListener("change", () => env.announce(count.textContent ?? ""));
}

// ---- 3. How it is combined --------------------------------------------------------------------------
function about(b: CombinedBundle, env: ShellEnv, main: HTMLElement): void {
  const s = b.statewide, m = b.manifest;
  main.innerHTML = `
  <div class="combined-view">
  <h1>How the two laws are combined</h1>
  <p class="lede">The combined view is its own result set. It reads each law's published extra homes by place and year and puts them together by fixed rules; neither law's own numbers change.</p>
  <section class="card"><h2>The rules</h2>
    <ol class="combined-steps">
      <li><strong>Same current-law forecast.</strong> Both laws are measured against the same current-law forecast (<span data-testid="baseline-version">${esc(m.baseline_version)}</span>). The builder refuses to combine results built on different forecasts.</li>
      <li><strong>Paths paired by meaning.</strong> ${s.roles.map((r) => `${esc(s.role_labels[r.role])}: ${esc(pairing(r))}`).join("; ")}. Paths are never crossed.</li>
      <li><strong>Away from stops, added.</strong> Only the parking law acts there, so nothing is counted twice.</li>
      <li><strong>Near stops, two rules side by side.</strong> ${esc(s.rules.a.info)} ${esc(s.rules.b.info)}</li>
      <li><strong>A third rule as a sensitivity only.</strong> ${esc(s.rule_c)}</li>
    </ol></section>
  <section class="card"><h2>Where the numbers come from</h2>
    <ul>
      <li>Transit-oriented density: run <code data-testid="source-tod">${esc(m.sources.tod)}</code> (<a href="${esc(env.link("/compare").replace("/combined/", "/tod/"))}">its own screens</a>).</li>
      <li>Parking requirement reduction: run <code data-testid="source-parking">${esc(m.sources.parking)}</code> (<a href="${esc(env.link("/compare").replace("/combined/", "/parking/"))}">its own screens</a>).</li>
    </ul>
    <div class="table-wrap"><table class="data"><caption>Checks run when the combined result was built</caption>
      <thead><tr><th scope="col">Check</th><th scope="col">Detail</th><th scope="col">Result</th></tr></thead>
      <tbody>${m.validation.checks.map((c) => `<tr><th scope="row">${esc(c.check)}</th><td>${esc(c.detail)}</td><td>${c.passed ? "Passed" : "Failed"}</td></tr>`).join("")}</tbody></table></div></section>
  </div>`;
}

function mount(env: ShellEnv, data: unknown): MountedReform {
  const b = data as CombinedBundle;
  const m = b.manifest;
  return {
    routes: ROUTES,
    defaultPath: "/compare",
    titleSuffix: "Transit-oriented density and parking together",
    statusStrip: `<span><strong>In development</strong></span><span>Run <code data-testid="run-id">${esc(m.run_id)}</code></span><span>From TOD <code>${esc(m.sources.tod)}</code> and parking <code>${esc(m.sources.parking)}</code></span><span>Forecast 2027–2031</span>`,
    footer: `<p><strong>Outcome:</strong> <span data-testid="outcome">${esc(m.outcome.short)}</span></p>
      <p class="pill-key"><span class="pill pill-calculated">Calculated</span> computed from observed inputs and stated rules. A dash (—) means missing, never zero.</p>
      <p class="muted">Run <code>${esc(m.run_id)}</code> · Validation: ${m.validation.passed} checks passed, ${m.validation.failed} failed · <a href="${esc(m.repo_url)}" target="_blank" rel="noopener">Source code and documentation<span class="sr-only"> (opens GitHub in a new tab)</span> ↗</a> · Apache-2.0</p>`,
    extra: "",
    bind() { /* nothing to bind */ },
    render(path: string, params: URLSearchParams, main: HTMLElement) {
      if (path.startsWith("/where")) where(b, env, params, main);
      else if (path.startsWith("/about")) about(b, env, main);
      else compare(b, env, params, main);
    },
  };
}

export const combinedReform: ReformModule = { load, mount };
