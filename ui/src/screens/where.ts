import { bindScenarioPicker, noteBox, scenarioPicker, scenPhrase, scenShort, type Ctx } from "../app";
import type { Area, County, PathId } from "../data";
import { dec, esc, int, missing, permitsText, pill, small, withRange, YEARS } from "../format";
import { createMap, RAMP, WATER, type MapHandle } from "../map";

/** Areas below this many single-family homes get a "small area" flag and are left out of the "Highest" line. */
const SMALL_AREA = 1000;

type Geo = "counties" | "munis";
type Layer = "homes" | "baseline" | "additional";
type Measure = "rate" | "count";
interface WhereState { geo: Geo; layer: Layer; measure: Measure; year: number; selected: string | null; sort: string; dir: 1 | -1; q: string; county: string; showAll: boolean; labels: boolean }

// Defaults (owner review 2026-10-26): counties, permits, central scenario (app default), five years 2027–2031, added by the law.
const ws: WhereState = { geo: "counties", layer: "additional", measure: "count", year: 2031, selected: null, sort: "value", dir: -1, q: "", county: "", showAll: false, labels: true };
let geoCache: { counties: unknown; munis: unknown; labels: unknown } | null = null;
let mapH: MapHandle | null = null;

type Row = { id: string; name: string; county: string; homes: number; base: number[]; add: Record<PathId, number[]>; area?: Area; c?: County };

function rows(ctx: Ctx): Row[] {
  if (ws.geo === "counties") return ctx.b.areas.counties.map((c) => ({ id: c.id, name: c.name, county: c.name, homes: c.homes, base: c.base, add: c.add, c }));
  return ctx.b.areas.munis.map((a) => ({ id: a.id, name: a.name, county: a.county, homes: a.homes, base: a.base, add: a.add, area: a }));
}
const nYears = () => ws.year - 2026;
const thru = (arr: number[]) => arr.slice(0, nYears()).reduce((a, b) => a + b, 0);

function value(ctx: Ctx, r: Row, p: PathId = ctx.ui.scenario): number | null {
  if (r.homes === 0) return null; // water areas and empty slivers have no value in any measure (missing, not 0)
  if (ws.layer === "homes") return r.homes;
  const v = ws.layer === "baseline" ? thru(r.base) : thru(r.add[p]);
  if (ws.measure === "count") return v;
  return r.homes > 0 ? (v / r.homes / nYears()) * 1000 : null;
}

function breaks(vals: number[]): number[] {
  const v = vals.filter((x) => x !== null && Number.isFinite(x)).sort((a, b) => a - b);
  if (!v.length) return [1, 2, 3, 4];
  const q = (f: number) => v[Math.min(v.length - 1, Math.floor(f * v.length))];
  const raw = [q(0.2), q(0.4), q(0.6), q(0.8)];
  const nice = (x: number) => {
    if (x === 0) return 0;
    const p = Math.pow(10, Math.floor(Math.log10(Math.abs(x))) - 1);
    return Math.round(x / p) * p;
  };
  const out = raw.map(nice);
  for (let i = 1; i < 4; i++) if (out[i] <= out[i - 1]) out[i] = out[i - 1] + (out[i - 1] || 0.01) * 0.01;
  return out;
}

function fmtVal(v: number | null): string {
  if (v === null) return "—";
  if (ws.layer === "homes" || ws.measure === "count") return v >= 0.5 || v === 0 ? int(v) : "under 1";
  return dec(v);
}

/** Legend class breaks: one decimal below 1 so the classes never read "under 1 to under 1". */
function fmtBreak(v: number): string {
  if (ws.layer === "homes") return int(v);
  if (ws.measure === "count") return v < 1 ? dec(v, 1) : v < 10 ? (Number.isInteger(v) ? int(v) : dec(v, 1)) : int(v);
  return dec(v);
}

/** Statewide value of the current layer and measure, for context next to the "Highest" line. */
function stateValue(ctx: Ctx): string {
  const st = ctx.b.state;
  const homes = st.homes.value ?? 0;
  if (ws.layer === "homes") return int(homes);
  const v = ws.layer === "baseline" ? thru(st.baseline.by_year) : thru(ctx.scen().additional_by_year);
  return ws.measure === "count" ? int(v) : dec((v / homes / nYears()) * 1000);
}

function layerTitle(ctx: Ctx): string {
  const y = ws.year === 2027 ? "2027" : `2027–${ws.year}`;
  if (ws.layer === "homes") return "Existing single-family homes (ACS 2020–2024)";
  const what = ws.layer === "baseline" ? "Permits without statewide reform (baseline)" : `Permits added by statewide ADU reform (${scenShort(ctx)})`;
  return ws.measure === "rate" ? `${what}, ${y}: per 1,000 single-family homes per year` : `${what}, ${y}`;
}

export function renderWhere(ctx: Ctx, main: HTMLElement): void {
  mapH?.destroy();
  mapH = null;
  main.innerHTML = `
  <h1>Where: counties and municipalities</h1>
  <p class="lede">The statewide result split across Wisconsin's 72 counties and 1,925 cities, villages and towns (census county subdivisions). The map fills whole areas; it never marks a lot or a building. Smaller areas are rough shares of the statewide result, rounded, with the lower and strong adoption scenarios as a range.</p>
  <div class="controls card" role="group" aria-label="Map and table settings">
    <fieldset class="seg"><legend>Areas</legend>
      <label><input type="radio" name="geo" value="counties" ${ws.geo === "counties" ? "checked" : ""}> Counties</label>
      <label><input type="radio" name="geo" value="munis" ${ws.geo === "munis" ? "checked" : ""}> Cities, villages and towns</label></fieldset>
    <fieldset class="seg"><legend>Show</legend>
      <label><input type="radio" name="layer" value="homes" ${ws.layer === "homes" ? "checked" : ""}> Existing homes</label>
      <label><input type="radio" name="layer" value="baseline" ${ws.layer === "baseline" ? "checked" : ""}> Baseline growth</label>
      <label><input type="radio" name="layer" value="additional" ${ws.layer === "additional" ? "checked" : ""}> Additional from the law</label></fieldset>
    <fieldset class="seg" ${ws.layer === "homes" ? "disabled" : ""}><legend>Measure</legend>
      <label><input type="radio" name="measure" value="count" ${ws.measure === "count" ? "checked" : ""}> Permits</label>
      <label><input type="radio" name="measure" value="rate" ${ws.measure === "rate" ? "checked" : ""}> Per 1,000 homes per year</label></fieldset>
    <div class="year-ctl">
      <label for="year">Through year: <output id="year-out" for="year">${ws.year}</output></label>
      <input type="range" id="year" min="2027" max="2031" step="1" value="${ws.year}" aria-valuetext="through ${ws.year}" ${ws.layer === "homes" ? "disabled" : ""}>
      <div class="year-ticks" aria-hidden="true">${YEARS.map((y) => `<span>${y}</span>`).join("")}</div>
    </div>
    <div class="scen-inline">${scenarioPicker(ctx, "scen-where", true)}</div>
    <label class="check"><input type="checkbox" id="lbl" ${ws.labels ? "checked" : ""}> Show county names</label>
  </div>

  <div class="map-layout">
    <section class="card map-card" aria-labelledby="map-title">
      <h2 id="map-title" class="map-title">${esc(layerTitle(ctx))}</h2>
      <div id="map" class="map" role="region" aria-label="Map of ${ws.geo === "counties" ? "counties" : "municipalities"}. The table below has the same values and is keyboard accessible."><div class="map-tip" hidden></div></div>
      <div id="map-legend"></div>
      <p class="muted small" id="map-summary"></p>
      <p class="muted small">Outlines: U.S. Census Bureau cartographic boundary files 2024 (1:500,000, shoreline-clipped); areas and results: TIGER/Line 2024 county subdivisions.</p>
    </section>
    <aside class="card detail" id="detail" aria-live="polite" aria-labelledby="detail-h"></aside>
  </div>

  <section class="card" aria-labelledby="tbl-h">
    <h2 id="tbl-h">Table: ${ws.geo === "counties" ? "all 72 counties" : "cities, villages and towns"}</h2>
    <div class="tbl-tools">
      <label>Search <input type="search" id="q" value="${esc(ws.q)}" placeholder="Name or county"></label>
      ${ws.geo === "munis" ? `<label>County <select id="cf"><option value="">All counties</option>${ctx.b.areas.counties.map((c) => `<option value="${c.name}" ${ws.county === c.name ? "selected" : ""}>${esc(c.name)}</option>`).join("")}</select></label>` : ""}
    </div>
    <div id="reconcile" class="reconcile"></div>
    <div class="table-wrap" id="tbl"></div>
  </section>`;

  const rerender = () => renderWhere(ctx, main);
  main.querySelectorAll<HTMLInputElement>('input[name="geo"]').forEach((i) => i.addEventListener("change", () => { ws.geo = i.value as Geo; ws.selected = null; ws.sort = "value"; ws.dir = -1; ws.showAll = false; rerender(); focusName(main, "geo", i.value); }));
  main.querySelectorAll<HTMLInputElement>('input[name="layer"]').forEach((i) => i.addEventListener("change", () => { ws.layer = i.value as Layer; update(ctx, main); focusName(main, "layer", i.value); }));
  main.querySelectorAll<HTMLInputElement>('input[name="measure"]').forEach((i) => i.addEventListener("change", () => { ws.measure = i.value as Measure; update(ctx, main); }));
  const yr = main.querySelector<HTMLInputElement>("#year")!;
  yr.addEventListener("input", () => { ws.year = Number(yr.value); yr.setAttribute("aria-valuetext", `through ${ws.year}`); main.querySelector("#year-out")!.textContent = String(ws.year); update(ctx, main); });
  bindScenarioPicker(ctx, main, "scen-where");
  main.querySelector<HTMLInputElement>("#q")!.addEventListener("input", (e) => { ws.q = (e.target as HTMLInputElement).value; ws.showAll = false; table(ctx, main); });
  main.querySelector<HTMLInputElement>("#lbl")!.addEventListener("change", (e) => { ws.labels = (e.target as HTMLInputElement).checked; mapH?.setOverlayVisible("county-labels", ws.labels); });
  main.querySelector<HTMLSelectElement>("#cf")?.addEventListener("change", (e) => { ws.county = (e.target as HTMLSelectElement).value; ws.showAll = false; table(ctx, main); });

  const mapEl = main.querySelector<HTMLElement>("#map")!;
  const tip = mapEl.querySelector<HTMLElement>(".map-tip")!;
  const start = (g: { counties: unknown; munis: unknown; labels: unknown }) => {
    if (!mapEl.isConnected) return;
    mapH = createMap(mapEl, g, (id) => select(ctx, main, id, false), (id, x, y) => {
      if (!id) { tip.hidden = true; return; }
      const r = rows(ctx).find((z) => z.id === id);
      if (!r) return;
      tip.hidden = false;
      tip.style.left = `${Math.min(x + 12, mapEl.clientWidth - 200)}px`;
      tip.style.top = `${y + 12}px`;
      tip.textContent = `${r.name}: ${fmtVal(value(ctx, r))}`;
    });
    mapH.setGeography(ws.geo);
    mapH.addOverlay({ id: "county-labels", kind: "labels", data: g.labels as GeoJSON.FeatureCollection, visible: ws.labels });
    update(ctx, main);
  };
  if (geoCache) start(geoCache);
  else Promise.all(["geo_counties.json", "geo_munis.json", "geo_labels.json"].map((f) => fetch(ctx.b.base + f).then((r) => r.json())))
    .then(([counties, munis, labels]) => { geoCache = { counties, munis, labels }; start(geoCache); });
  update(ctx, main);
}

function focusName(main: HTMLElement, name: string, v: string) {
  main.querySelector<HTMLInputElement>(`input[name="${name}"][value="${v}"]`)?.focus();
}

function update(ctx: Ctx, main: HTMLElement): void {
  if (!main.querySelector("#map-title")) return;
  const rs = rows(ctx);
  const vals = new Map<string, number | null>();
  for (const r of rs) vals.set(r.id, value(ctx, r));
  const br = breaks([...vals.values()].filter((v): v is number => v !== null));
  mapH?.setData(vals, br);
  mapH?.select(ws.selected);
  main.querySelector("#map-title")!.textContent = layerTitle(ctx);
  main.querySelectorAll<HTMLFieldSetElement>("fieldset.seg")[2].disabled = ws.layer === "homes";
  main.querySelector<HTMLInputElement>("#year")!.disabled = ws.layer === "homes";
  const lab = (i: number) => (i === 0 ? `under ${fmtBreak(br[0])}` : i === 4 ? `${fmtBreak(br[3])} or more` : `${fmtBreak(br[i - 1])} to under ${fmtBreak(br[i])}`);
  main.querySelector("#map-legend")!.innerHTML = `<ul class="legend map-legend" aria-label="Map legend: five classes with equal numbers of areas">${RAMP.map((c, i) => `<li><span class="lg-sw" style="background:${c}"></span>${esc(lab(i))}</li>`).join("")}<li><span class="lg-sw lg-hatch"></span>no single-family homes (no value)</li><li><span class="lg-sw" style="background:${WATER}"></span>lakes and outside Wisconsin</li></ul>`;
  const rateMode = ws.layer !== "homes" && ws.measure === "rate";
  const eligible = rs.filter((r) => vals.get(r.id) !== null && (!rateMode || r.homes >= SMALL_AREA));
  const top = [...eligible].sort((a, b) => (vals.get(b.id) ?? 0) - (vals.get(a.id) ?? 0)).slice(0, 3);
  const nSmall = rateMode ? rs.filter((r) => r.homes > 0 && r.homes < SMALL_AREA).length : 0;
  main.querySelector("#map-summary")!.textContent = `Wisconsin: ${stateValue(ctx)}. Highest${rateMode ? ` among areas with at least ${int(SMALL_AREA)} single-family homes` : ""}: ${top.map((r) => `${r.name} (${fmtVal(vals.get(r.id) ?? null)})`).join(", ")}.${nSmall ? ` ${int(nSmall)} smaller areas are flagged "small area" in the table: a few homes make their rates swing, and some small, high-value villages reach several times the state rate (being reviewed).` : ""} Classes split the areas into five equal-sized groups.`;
  detail(ctx, main);
  table(ctx, main);
}

function select(ctx: Ctx, main: HTMLElement, id: string, fromTable: boolean): void {
  ws.selected = id;
  mapH?.select(id);
  detail(ctx, main);
  table(ctx, main);
  if (!fromTable) main.querySelector<HTMLElement>("#detail")?.focus();
}

function detail(ctx: Ctx, main: HTMLElement): void {
  const el = main.querySelector<HTMLElement>("#detail")!;
  el.tabIndex = -1;
  const r = rows(ctx).find((x) => x.id === ws.selected);
  const st = ctx.b.state;
  if (!r) {
    el.innerHTML = `<h2 id="detail-h">Pick an area</h2><p>Click an area on the map, or choose <strong>Details</strong> in the table, to see its numbers.</p>
    <p class="muted">Wisconsin through ${ws.year}: ${int(thru(st.baseline.by_year))} baseline permits and ${int(thru(ctx.scen().additional_by_year))} additional permits (${esc(scenPhrase(ctx))}).</p>`;
    return;
  }
  const y = ws.year === 2027 ? "2027" : `2027–${ws.year}`;
  const add = (p: PathId) => thru(r.add[p]);
  const a = r.area;
  const rate = (v: number) => (r.homes > 0 ? dec((v / r.homes / nYears()) * 1000) : "—");
  // Madison's note shows only where Madison's numbers are: its own panel and its county's (Dane)
  const cNote = r.c ? ctx.b.areas.munis.find((m) => m.note && m.county_id === r.id)?.note : undefined;
  const typeText = a ? (a.type === "not_defined" ? "Undefined area" : a.type.charAt(0).toUpperCase() + a.type.slice(1)) : "";
  el.innerHTML = `<h2 id="detail-h">${esc(r.name)}</h2>
    ${a ? `<p class="muted">${esc(typeText)} in ${esc(a.county)}${a.context ? ` · ${esc(a.context.replace("_", " "))}` : ""}</p>` : `<p class="muted">${int(r.c!.n_areas)} cities, villages and towns</p>`}
    ${a?.note ? noteBox(a.note, "detail-madison-note") : ""}
    ${r.c && cNote ? noteBox(cNote, "detail-madison-note") : ""}
    ${r.homes > 0 && r.homes < SMALL_AREA ? `<p class="small-flag"><strong>Small area.</strong> Fewer than ${int(SMALL_AREA)} single-family homes, so its rate can swing widely; read its figures with the range.</p>` : ""}
    <dl class="kv">
      <dt>Single-family homes</dt><dd>${int(r.homes)} ${pill("observed")}</dd>
      <dt>Without statewide reform (baseline), ${y}</dt><dd>${r.homes > 0 ? `${permitsText(thru(r.base))} ${pill("calculated")}` : missing(a?.missing_reason ?? "no homes")}</dd>
      <dt>Added by statewide ADU reform, ${esc(scenShort(ctx))}, ${y}</dt><dd>${r.homes > 0 ? `<strong>${permitsText(add(ctx.ui.scenario))}</strong> ${pill("calculated")}` : missing("no homes")}</dd>
      <dt>All three scenarios (lower / central / strong adoption)</dt><dd>${r.homes > 0 ? `${small(add("lower"))} / ${small(add("central"))} / ${small(add("upper"))}` : "—"}</dd>
      <dt>Rate with the law</dt><dd>${r.homes > 0 ? `${rate(thru(r.base) + add(ctx.ui.scenario))} per 1,000 homes per year (current law ${rate(thru(r.base))})` : "—"}</dd>
      ${a ? `<dt>Local ADU rules</dt><dd>${esc(ctx.b.areas.class_text[a.current_class] ?? a.current_class)} ${pill(a.rights_status === "assumed" ? "assumed" : "observed")}${a.rights_status === "source_lead" ? " <span class=\"muted\">(some provisions from a source lead)</span>" : ""}</dd>
      <dt>Current-law rate (basis)</dt><dd>${r.homes > 0 ? `${dec(a.x_rate)} per 1,000 homes per year ${pill(a.x_status)}: ${esc(a.basis_text)}` : "—"}</dd>
      ${a.rights_added_text ? `<dt>What the law changes</dt><dd>${esc(a.rights_added_text)}</dd>` : ""}` : `<dt>Homes by rate basis</dt><dd>Observed ${int(r.c!.homes_by_status.observed)}, calculated ${int(r.c!.homes_by_status.estimated)}, assumed ${int(r.c!.homes_by_status.assumed)}</dd>`}
    </dl>
    ${a?.pilot ? `<p><a class="button" href="${ctx.link(`/pilot/${a.pilot}`)}">Open the ${esc(a.name)} pilot example →</a></p>` : ""}
    ${r.c ? `<p><button type="button" class="linkish" data-drill="${esc(r.name)}">Show its cities, villages and towns</button></p>` : ""}
    <p class="muted small">An area figure is the area's share of the statewide result. It is not a forecast for any lot.</p>
    ${a ? `<p><button type="button" class="linkish" id="back-to-table">Back to the table</button></p>` : ""}`;
  el.querySelector<HTMLButtonElement>("#back-to-table")?.addEventListener("click", () => {
    const btn = main.querySelector<HTMLButtonElement>(`button[data-sel="${CSS.escape(r.id)}"]`);
    if (btn) btn.focus(); else main.querySelector<HTMLElement>("#q")?.focus();
  });
  el.querySelector<HTMLButtonElement>("[data-drill]")?.addEventListener("click", (e) => {
    ws.geo = "munis"; ws.county = (e.target as HTMLElement).dataset.drill!; ws.selected = null; ws.showAll = true;
    renderWhere(ctx, main);
  });
}

function table(ctx: Ctx, main: HTMLElement): void {
  const all = rows(ctx);
  const q = ws.q.trim().toLowerCase();
  let rs = all.filter((r) => (!q || r.name.toLowerCase().includes(q) || r.county.toLowerCase().includes(q)) && (!ws.county || ws.geo === "counties" || r.county === ws.county));
  const key = (r: Row): number | string => {
    switch (ws.sort) {
      case "name": return r.name;
      case "county": return r.county;
      case "homes": return r.homes;
      case "base": return thru(r.base);
      case "add": return thru(r.add[ctx.ui.scenario]);
      default: return value(ctx, r) ?? -Infinity;
    }
  };
  rs = [...rs].sort((a, b) => { const x = key(a), y = key(b); return (typeof x === "string" ? x.localeCompare(y as string) : (x as number) - (y as number)) * ws.dir; });
  const p = ctx.ui.scenario;
  const totAdd = all.reduce((s, r) => s + thru(r.add[p]), 0);
  const totBase = all.reduce((s, r) => s + thru(r.base), 0);
  const totHomes = all.reduce((s, r) => s + r.homes, 0);
  const st = ctx.b.state;
  const stAdd = thru(ctx.scen().additional_by_year), stBase = thru(st.baseline.by_year);
  const ok = Math.abs(totAdd - stAdd) < 1 && Math.abs(totBase - stBase) < 1;
  const y = ws.year === 2027 ? "2027" : `2027–${ws.year}`;
  main.querySelector("#reconcile")!.innerHTML = `<p data-testid="reconcile" class="${ok ? "ok" : "bad"}">${ok ? "✓" : "✗"} All ${int(all.length)} ${ws.geo === "counties" ? "counties" : "areas"} add up to <strong>${int(totAdd)}</strong> additional and <strong>${int(totBase)}</strong> baseline permits for ${y} (${esc(scenPhrase(ctx))}); the statewide figures are ${int(stAdd)} and ${int(stBase)}. ${int(totHomes)} single-family homes. Each row is rounded to whole permits for display; totals add the unrounded values, so rounded rows can differ from a total by a permit or two.</p>`;
  const limit = ws.showAll || ws.geo === "counties" ? rs.length : 50;
  const shown = rs.slice(0, limit);
  const th = (k: string, label: string, num = true) => `<th scope="col" class="${num ? "num" : ""}" aria-sort="${ws.sort === k ? (ws.dir === 1 ? "ascending" : "descending") : "none"}"><button type="button" class="sort" data-k="${k}">${label}<span aria-hidden="true">${ws.sort === k ? (ws.dir === 1 ? " ▲" : " ▼") : " ↕"}</span></button></th>`;
  const mapCol = ws.layer === "homes" ? "Single-family homes (map)" : ws.measure === "rate" ? "Map value: per 1,000 homes per year" : "Map value: permits";
  main.querySelector("#tbl")!.innerHTML = `<table class="data sortable" data-testid="where-table"><caption>${esc(layerTitle(ctx))}. ${rs.length === all.length ? "" : `Filtered: ${int(rs.length)} of ${int(all.length)} rows.`} Additional permits show ${esc(scenPhrase(ctx))} with the range from the lower to the strong adoption scenario. "Small area": fewer than ${int(SMALL_AREA)} single-family homes.</caption>
    <thead><tr>${th("name", "Name", false)}${ws.geo === "munis" ? th("county", "County", false) : ""}${th("homes", "Single-family homes")}${th("base", `Baseline, ${y}`)}${th("add", `Additional, ${y} (range)`)}${th("value", mapCol)}${ws.geo === "munis" ? `<th scope="col">Current-law rate basis</th>` : ""}<th scope="col"><span class="sr-only">Details</span></th></tr></thead>
    <tbody>${shown.map((r) => `<tr class="${r.id === ws.selected ? "sel" : ""}"><th scope="row">${esc(r.name)}${r.area?.pilot ? ` <a href="${ctx.link(`/pilot/${r.area.pilot}`)}" class="tag">pilot</a>` : ""}</th>${ws.geo === "munis" ? `<td>${esc(r.county)}</td>` : ""}<td class="num">${int(r.homes)}</td><td class="num">${r.homes ? small(thru(r.base)) : missing(noHomes(r))}</td><td class="num">${r.homes ? withRange(thru(r.add[p]), thru(r.add.lower), thru(r.add.upper)) : missing(noHomes(r))}</td><td class="num">${r.homes ? fmtVal(value(ctx, r)) : "—"}${r.homes > 0 && r.homes < SMALL_AREA && ws.layer !== "homes" ? ` <span class="tag" title="Fewer than ${int(SMALL_AREA)} single-family homes: the rate can swing widely">small area</span>` : ""}</td>${ws.geo === "munis" ? `<td>${r.homes ? pill(r.area!.x_status) : `<span class="muted small">${r.area!.water ? "water area" : "no homes"}</span>`}</td>` : ""}<td><button type="button" class="linkish" data-sel="${r.id}" aria-label="Details for ${esc(r.name)}">Details</button></td></tr>`).join("")}</tbody>
    <tfoot><tr><th scope="row">${rs.length === all.length ? "Wisconsin (all rows)" : `Total of ${int(rs.length)} filtered rows`}</th>${ws.geo === "munis" ? "<td></td>" : ""}<td class="num">${int(rs.reduce((s, r) => s + r.homes, 0))}</td><td class="num">${int(rs.reduce((s, r) => s + thru(r.base), 0))}</td><td class="num">${int(rs.reduce((s, r) => s + thru(r.add[p]), 0))}</td><td></td>${ws.geo === "munis" ? "<td></td>" : ""}<td></td></tr></tfoot></table>
    ${rs.length > limit ? `<p><button type="button" class="button" id="show-all">Show all ${int(rs.length)} rows</button></p>` : ""}`;
  main.querySelectorAll<HTMLButtonElement>("button.sort").forEach((b) => b.addEventListener("click", () => {
    const k = b.dataset.k!;
    if (ws.sort === k) ws.dir = ws.dir === 1 ? -1 : 1; else { ws.sort = k; ws.dir = k === "name" || k === "county" ? 1 : -1; }
    table(ctx, main);
    main.querySelector<HTMLButtonElement>(`button.sort[data-k="${k}"]`)?.focus();
  }));
  main.querySelectorAll<HTMLButtonElement>("button[data-sel]").forEach((b) => b.addEventListener("click", () => {
    const id = b.dataset.sel!;
    select(ctx, main, id, true);
    main.querySelector<HTMLElement>("#detail")?.focus();
  }));
  main.querySelector<HTMLButtonElement>("#show-all")?.addEventListener("click", () => { ws.showAll = true; table(ctx, main); });
}

function noHomes(r: Row): string {
  return r.area?.water ? "water area, no homes" : "no homes";
}

/** Called by the router when leaving the Where screen, to free the WebGL context. */
export function leaveWhere(): void { mapH?.destroy(); mapH = null; }
