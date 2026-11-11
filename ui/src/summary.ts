// The Summary tab: one shared component with the same layout for all four reforms (owner, 2026-11-11). It follows
// docs/UNIFORM_DISPLAY_SPEC.md: one 90% range with its low and high ends labelled, no centre line, labelled side
// lines, a unit on every number. Every number comes from the reform's bundle; the browser only scales and formats.
//
// Layout: one plain sentence; "The policy" (the challenge's benchmark, quoted from the handbook, and what we modeled,
// from the reform's own law text); the 90% range; the "How we count" line (the same source as the Introduction's table,
// ui/src/howwecount.ts); the range chart with hover/tap popups, keyboard-reachable year and side-line details and a
// "Show as a table" toggle; three toggles written to the URL; one row of links. The chart card spans the main
// container; prose keeps a readable measure. "Enlarge chart" redraws the same chart, with the same toggles and popups,
// in a full-window native <dialog>.
//
// URL parameters: per=1000 (per 1,000 Wisconsin homes), show=extra (extra homes only), timing=flat (the five-year
// total spread evenly; middle housing uses its own flat version), lines=off (side lines hidden; the band, current law
// and their legend entries stay).
import type { ChartGeom } from "./charts";
import { dec, esc, int } from "./format";
import { HANDBOOK_BENCHMARK, HANDBOOK_SOURCE } from "./benchmarks";
import { HOW_WE_COUNT, type ReformKey } from "./howwecount";
import { BAND_COLOR, CURRENT_LAW_COLOR, drawRangeChart, num, sideStyle, yearShares, type Range90, type SideLine } from "./range";
import type { ShellEnv } from "./scenarios/types";

export interface WiHomes { value: number; vintage: string }

let homesP: Promise<WiHomes> | null = null;
/** All Wisconsin homes (housing units, ACS 2020–2024), the one base for "per 1,000 Wisconsin homes" in every reform.
 *  Read from where the tool stores it: the ADU bundle's state.json, acs_total_units. */
export function loadWiHomes(): Promise<WiHomes> {
  homesP ??= (async () => {
    const root = `${import.meta.env.BASE_URL}runs/`;
    const r = await fetch(`${root}latest.json`);
    if (!r.ok) throw new Error(`${root}latest.json: ${r.status}`);
    const { run_id } = await r.json();
    const s = await fetch(`${root}${run_id}/state.json`);
    if (!s.ok) throw new Error(`${root}${run_id}/state.json: ${s.status}`);
    const st = await s.json();
    return { value: st.acs_total_units.value, vintage: st.acs_total_units.vintage };
  })();
  homesP.catch(() => { homesP = null; });
  return homesP;
}

/** "ACS 2020-2024 5-year" → "ACS 2020–2024". */
const acsLabel = (v: string) => v.replace(/ACS (\d{4})-(\d{4}).*/, "ACS $1–$2");

/** The five-year range spread evenly over the years: each year one fifth of each end. */
export function flatRange(R: Range90): Range90 {
  return { ...R, years: R.years.map((y) => ({ year: y.year, low: R.low / 5, high: R.high / 5 })), years_method: "Flat: the five-year total spread evenly, one fifth in each year." };
}

export interface SummaryInput {
  id: ReformKey;
  /** The page's h1: the reform's name. */
  title: string;
  /** The law, for the plain sentence: "allows one ADU on every lot with a single-family home". */
  law: string;
  /** "What we modeled" in the policy box: the reform's own law text, reused from where the tool already states it
   *  (one plain-text paragraph each). */
  modeled: string[];
  /** What is counted, plural: "ADU permits", "homes near major transit stops". */
  unit: string;
  /** The measured-timing 90% range. */
  range: Range90;
  /** The flat-timing range, or "none" when the reform has no measured ramp (the timing toggle is then disabled). */
  rangeFlat: Range90 | "none";
  /** Side lines drawn on the chart (each a five-year value). */
  sideLines: SideLine[];
  /** One line on side lines listed elsewhere but not drawn. */
  notDrawn?: string;
  /** Current law, 2027–2031, in the same unit. */
  base: { central: number[]; low: number[]; high: number[] };
  /** The chart's heading, before "each year, 2027–2031": "ADU permits", "Homes permitted near major transit stops". */
  chartName: string;
  /** The current-law legend entry, when the reform words it its own way (default "Current law (baseName; its range
   *  shaded grey)"). */
  currentLawLabel?: string;
  /** What current law counts, for the chart and popups: "ADU permits under current law". */
  baseName: string;
  homes: WiHomes;
}

const YEARS = [2027, 2028, 2029, 2030, 2031];
const sumOf = (xs: number[]) => xs.reduce((a, b) => a + b, 0);

/** A signed number with two decimals and a true minus sign (rates per 1,000 homes). */
function dec2(v: number): string {
  const r = Math.round(v * 100) / 100;
  return r < 0 ? `−${dec(-r, 2)}` : dec(r === 0 ? 0 : r, 2);
}

export function renderSummary(main: HTMLElement, o: SummaryInput, env: ShellEnv, params: URLSearchParams): void {
  const per = params.get("per") === "1000";
  const extra = params.get("show") === "extra";
  const hasRamp = o.rangeFlat !== "none";
  const flat = hasRamp && params.get("timing") === "flat";
  const R = flat ? (o.rangeFlat as Range90) : o.range;
  const k = o.homes.value / 1000;          // thousands of Wisconsin homes
  const f = (v: number) => (per ? v / k : v);
  const fmt = (v: number) => (per ? dec2(v / k) : num(v));
  const homesTxt = `${int(o.homes.value)} homes, ${acsLabel(o.homes.vintage)}`;
  const unitLine = per
    ? `extra ${o.unit} per 1,000 Wisconsin homes, 2027–2031 (90% range)`
    : `extra ${o.unit}, Wisconsin, 2027–2031 (90% range)`;
  const unitShort = per ? `extra ${o.unit} per 1,000 Wisconsin homes` : `extra ${o.unit}`;
  const yearUnit = per ? `${o.unit} per 1,000 Wisconsin homes in the year` : `${o.unit} in the year`;
  const signTxt = o.range.low > 0
    ? "the whole range is above zero, so the evidence points to added homes"
    : o.range.high < 0 ? "the whole range is below zero, so the evidence points to fewer homes"
    : "the range includes zero, so the evidence can't tell yet whether the law adds homes";
  // per-year values of everything drawn, in the chart's units (current law added in the totals view)
  const sh = yearShares(R);
  const add = (i: number) => (extra ? 0 : o.base.central[i]);
  const lo = (i: number) => add(i) + Math.min(R.years[i].low, R.years[i].high);
  const hi = (i: number) => add(i) + Math.max(R.years[i].low, R.years[i].high);
  const sideAt = (s: SideLine, i: number) => add(i) + s.value! * sh[i];
  const linesOn = params.get("lines") !== "off";
  const drawn = linesOn ? o.sideLines.filter((s) => s.value !== undefined) : [];
  const q = (k2: string, v: string | null) => {
    const n = new URLSearchParams(params);
    if (v === null) n.delete(k2); else n.set(k2, v);
    return n;
  };
  const radio = (name: string, value: string, label: string, on: boolean, disabled = false) =>
    `<label><input type="radio" name="${name}" value="${value}" ${on ? "checked" : ""} ${disabled ? "disabled" : ""}> ${esc(label)}</label>`;
  const chartHeading = `${o.chartName} each year, 2027–2031`;
  const chartTitle = extra
    ? `Extra ${o.unit} from the law each year, Wisconsin, 2027–2031${per ? ", per 1,000 Wisconsin homes" : ""}`
    : `${o.unit[0].toUpperCase()}${o.unit.slice(1)} each year, Wisconsin, 2027–2031: current law and with the law${per ? ", per 1,000 Wisconsin homes" : ""}`;
  /** The chart, its popup, its key (side lines as buttons) and the year buttons: on the page, or (big) in the dialog. */
  const chartBlock = (big: boolean) => {
    const sfx = big ? "-big" : "", popId = `sum-pop${sfx}`;
    return `<div class="sum-chart-wrap" id="sum-chart-wrap${sfx}">
      <div class="chart-box" id="sum-chart${sfx}" data-testid="summary-chart${sfx}"></div>
      <div class="sum-pop" id="${popId}" role="tooltip" data-testid="summary-popup${sfx}" hidden></div>
    </div>
    <ul class="legend sum-legend" aria-label="Chart key" data-testid="summary-legend${sfx}">
      <li><svg width="28" height="14" aria-hidden="true" focusable="false"><line x1="0" x2="28" y1="7" y2="7" stroke="${CURRENT_LAW_COLOR}" stroke-width="2" stroke-dasharray="7 5"/></svg>${esc(extra ? "Current law: the zero line" : o.currentLawLabel ?? `Current law (${o.baseName}; its range shaded grey)`)}</li>
      <li><svg width="28" height="14" aria-hidden="true" focusable="false"><rect x="0" y="2" width="28" height="10" fill="${BAND_COLOR}" opacity="0.28"/></svg>With the law: 90% range, ${esc(fmt(R.low))} to ${esc(fmt(R.high))} ${esc(unitShort)}${extra ? "" : " (on top of current law)"}</li>
      ${drawn.map((s, i) => { const st = sideStyle(i); return `<li><button type="button" class="sum-side" data-side="${esc(s.id)}" aria-describedby="${popId}"><svg width="28" height="14" aria-hidden="true" focusable="false"><line x1="0" x2="28" y1="7" y2="7" stroke="${st.color}" stroke-width="2" ${st.dash ? `stroke-dasharray="${st.dash}"` : ""}/></svg>${esc(s.label)}: ${esc(fmt(s.value!))}</button></li>`; }).join("")}
    </ul>
    <div class="sum-years" role="group" aria-label="Details for one year" data-testid="summary-years${sfx}"><span class="small muted" aria-hidden="true">Year details:</span>${YEARS.map((y) => `<button type="button" class="sum-year" data-year="${y}" aria-describedby="${popId}">${y}</button>`).join("")}</div>`;
  };

  main.innerHTML = `
  <article class="summary-page" data-testid="summary" data-reform="${esc(o.id)}">
  <h1>${esc(o.title)}</h1>
  <p class="lede summary-sentence" data-testid="summary-sentence">If Wisconsin ${esc(o.law)} from 1 January 2027, the range below is our estimate of the extra ${esc(o.unit)} it would permit over the first five years; ${esc(signTxt)}.</p>

  <section class="card summary-policy" aria-labelledby="sum-policy-h" data-testid="summary-policy">
    <h2 id="sum-policy-h">The policy</h2>
    <div class="policy-part" data-testid="policy-benchmark">
      <h3>The challenge's benchmark</h3>
      <blockquote class="policy-quote"><p data-testid="policy-quote">“${esc(HANDBOOK_BENCHMARK[o.id])}”</p></blockquote>
      <p class="small muted policy-source" data-testid="policy-source">Source: ${esc(HANDBOOK_SOURCE)}</p>
    </div>
    <div class="policy-part" data-testid="policy-modeled">
      <h3>What we modeled</h3>
      ${o.modeled.map((t) => `<p>${esc(t)}</p>`).join("")}
    </div>
  </section>

  <section class="card range-card summary-range" aria-labelledby="sum-range-h" data-testid="summary-range">
    <p class="range-lead" id="sum-range-h">Our estimate is between:</p>
    <p class="range-ends"><span class="range-end"><span class="range-end-label">Low end</span><span class="range-end-num" data-testid="range-low">${fmt(R.low)}</span></span>
      <span class="range-to" aria-hidden="true">to</span>
      <span class="range-end"><span class="range-end-label">High end</span><span class="range-end-num" data-testid="range-high">${fmt(R.high)}</span></span></p>
    <p class="range-unit" data-testid="range-unit">${esc(unitLine)}</p>
    ${per ? `<p class="small muted" data-testid="per-base">Per 1,000 Wisconsin homes: each number ÷ ${dec(k, 3)} thousand homes (all ${esc(homesTxt)}). The same base for every reform.</p>` : ""}
    <p class="small summary-how" data-testid="summary-how"><strong>How we count.</strong> ${esc(HOW_WE_COUNT[o.id])}</p>
  </section>

  <section class="card summary-chart-card" aria-labelledby="sum-chart-h">
    <div class="sum-chart-head"><h2 id="sum-chart-h">${esc(chartHeading)}</h2>
      <button type="button" class="sum-enlarge" id="sum-enlarge" aria-haspopup="dialog" aria-controls="sum-dialog" data-testid="summary-enlarge">Enlarge chart</button></div>
    <div class="summary-toggles">
      <fieldset class="seg" data-testid="toggle-per"><legend>Numbers</legend>${radio("sum-per", "total", "Total", !per)}${radio("sum-per", "1000", "Per 1,000 Wisconsin homes", per)}</fieldset>
      <fieldset class="seg" data-testid="toggle-show"><legend>Chart shows</legend>${radio("sum-show", "totals", "Totals with current law", !extra)}${radio("sum-show", "extra", "Extra homes only", extra)}</fieldset>
      <fieldset class="seg" data-testid="toggle-timing" ${hasRamp ? "" : 'disabled aria-describedby="sum-noramp"'}><legend>Timing</legend>${radio("sum-timing", "measured", "Measured", !flat, !hasRamp)}${radio("sum-timing", "flat", "Flat", flat, !hasRamp)}
        ${hasRamp ? "" : `<p class="small muted sum-noramp" id="sum-noramp" data-testid="no-ramp">This reform has no measured ramp.</p>`}</fieldset>
      ${o.sideLines.some((s) => s.value !== undefined) ? `<fieldset class="seg" data-testid="toggle-lines"><legend>Side lines</legend>${radio("sum-lines", "on", "Show", linesOn)}${radio("sum-lines", "off", "Hide", !linesOn)}</fieldset>` : ""}
    </div>
    ${chartBlock(false)}
    <p><button type="button" class="linkish" id="sum-table-btn" aria-expanded="false" aria-controls="sum-table-wrap" data-testid="summary-table-toggle">Show as a table</button></p>
    <div id="sum-table-wrap" hidden>
      <div class="table-wrap"><table class="data" data-testid="summary-table"><caption>${esc(extra ? `Extra ${o.unit} each year with the law` : `${o.unit} each year: current law, and with the law`)}${per ? ", per 1,000 Wisconsin homes" : ""}, 2027–2031</caption>
        <thead><tr><th scope="col">Year</th>${extra ? "" : `<th scope="col" class="num">Current law</th>`}<th scope="col" class="num">${extra ? "Low end" : "With the law: low end"}</th><th scope="col" class="num">${extra ? "High end" : "With the law: high end"}</th>${drawn.map((s) => `<th scope="col" class="num">${esc(s.label)}</th>`).join("")}</tr></thead>
        <tbody>${YEARS.map((y, i) => `<tr><th scope="row">${y}</th>${extra ? "" : `<td class="num">${fmt(o.base.central[i])}</td>`}<td class="num">${fmt(lo(i))}</td><td class="num">${fmt(hi(i))}</td>${drawn.map((s) => `<td class="num">${fmt(sideAt(s, i))}</td>`).join("")}</tr>`).join("")}
        <tr><th scope="row">2027–2031</th>${extra ? "" : `<td class="num">${fmt(sumOf(o.base.central))}</td>`}<td class="num" data-testid="table-total-low">${fmt((extra ? 0 : sumOf(o.base.central)) + R.low)}</td><td class="num" data-testid="table-total-high">${fmt((extra ? 0 : sumOf(o.base.central)) + R.high)}</td>${drawn.map((s) => `<td class="num">${fmt((extra ? 0 : sumOf(o.base.central)) + s.value!)}</td>`).join("")}</tr></tbody></table></div>
      <p class="small muted">${extra ? "" : "The totals add current law to each end; current law's own range is shaded on the chart and is not added. "}Rows may not add exactly because of rounding.</p>
    </div>
    <p class="small muted" data-testid="summary-timing-note">${esc(R.years_method ?? "")}${o.notDrawn ? ` ${esc(o.notDrawn)}` : ""} No centre line is drawn: the range has no single best guess.</p>
  </section>

  <dialog class="sum-dialog" id="sum-dialog" aria-labelledby="sum-dialog-h" data-testid="summary-dialog">
    <div class="sum-dialog-head"><h2 id="sum-dialog-h">${esc(chartHeading)}</h2>
      <button type="button" class="sum-dialog-close" id="sum-dialog-close" data-testid="summary-dialog-close">Close</button></div>
    <p class="small muted" data-testid="summary-dialog-state">${esc(`Numbers: ${per ? "per 1,000 Wisconsin homes" : "total"}. Chart shows: ${extra ? "extra homes only" : "totals with current law"}. Timing: ${flat ? "flat" : "measured"}. Side lines: ${linesOn ? "shown" : "hidden"}.`)}</p>
    <div class="sum-dialog-body" id="sum-dialog-body"></div>
  </dialog>

  <p class="summary-links" data-testid="summary-links"><a href="${env.link("/where")}">Where homes would go →</a><a href="${env.link("/how-sure")}">How sure we are →</a><a href="${env.link("/why")}">Why →</a></p>
  </article>`;

  // toggles: each is written to the URL, then the screen re-renders
  const bindRadio = (name: string, key: string, def: string, say: (v: string) => string) =>
    main.querySelectorAll<HTMLInputElement>(`input[name="${name}"]`).forEach((inp) => inp.addEventListener("change", () => {
      if (!inp.checked) return;
      env.replaceQuery(q(key, inp.value === def ? null : inp.value));
      env.refresh();
      env.announce(say(inp.value));
    }));
  bindRadio("sum-per", "per", "total", (v) => (v === "1000" ? "Numbers per 1,000 Wisconsin homes." : "Numbers as totals."));
  bindRadio("sum-show", "show", "totals", (v) => (v === "extra" ? "Chart shows only the extra homes from the law. Current law is the zero line." : "Chart shows totals with current law."));
  bindRadio("sum-lines", "lines", "on", (v) => (v === "off" ? "Side lines hidden. The range and current law stay." : "Side lines shown."));
  bindRadio("sum-timing", "timing", "measured", (v) => (v === "flat" ? "Timing: flat, the five-year total spread evenly." : "Timing: measured."));

  const tbtn = main.querySelector<HTMLButtonElement>("#sum-table-btn")!;
  const twrap = main.querySelector<HTMLElement>("#sum-table-wrap")!;
  tbtn.addEventListener("click", () => {
    const open = twrap.hidden;
    twrap.hidden = !open;
    tbtn.setAttribute("aria-expanded", String(open));
    tbtn.textContent = open ? "Hide the table" : "Show as a table";
  });

  // ---- the chart, with its hover and tap layer -------------------------------------------------
  // Drawn twice at most: on the page, and (while open) in the "Enlarge chart" dialog. Each copy has its own popup,
  // crosshair, legend buttons and year buttons, bound to its own scales.
  const yLabel = per ? (extra ? "Extra per 1,000 Wisconsin homes per year" : "Per 1,000 Wisconsin homes per year") : (extra ? `Extra ${o.unit} per year` : `${o.unit[0].toUpperCase()}${o.unit.slice(1)} per year`);

  function mountChart(root: HTMLElement, big: boolean, height?: number): void {
    const sfx = big ? "-big" : "";
    const wrap = root.querySelector<HTMLElement>(".sum-chart-wrap")!;
    const pop = root.querySelector<HTMLElement>(".sum-pop")!;
    let geom: ChartGeom | null = null;
    drawRangeChart(root.querySelector<HTMLElement>(".chart-box")!, {
      mode: extra ? "extra" : "totals", range: R, sideLines: drawn, f, noun: o.unit,
      base: { years: YEARS, central: o.base.central, low: o.base.low, high: o.base.high },
      title: chartTitle, yLabel, yFormat: per ? (y: number) => dec(y, 2) : undefined, height,
      onDraw: (g) => { geom = g; addHitLayer(g); hide(); },
    });

    function addHitLayer(g: ChartGeom): void {
      const NS = "http://www.w3.org/2000/svg";
      const mk = (tag: string, attrs: Record<string, string | number>) => {
        const e = document.createElementNS(NS, tag);
        for (const [a, v] of Object.entries(attrs)) e.setAttribute(a, String(v));
        return e;
      };
      const layer = mk("g", { class: "sum-hit-layer", "data-testid": `summary-hit-layer${sfx}` });
      const step = g.X(2028) - g.X(2027);
      YEARS.forEach((y) => layer.appendChild(mk("rect", { class: "sum-hit-year", "data-year": y, x: g.X(y) - step / 2, y: g.m.t, width: step, height: g.H - g.m.t - g.m.b, fill: "transparent" })));
      layer.appendChild(mk("line", { class: "sum-cross", "data-testid": `summary-crosshair${sfx}`, x1: 0, x2: 0, y1: g.m.t, y2: g.H - g.m.b, visibility: "hidden" }));
      drawn.forEach((s) => {
        const vis = g.svg.querySelector(`path[data-series="side-${CSS.escape(s.id)}"]`);
        if (vis) layer.appendChild(mk("path", { class: "sum-hit-side", "data-side": s.id, d: vis.getAttribute("d") ?? "", fill: "none", stroke: "transparent", "stroke-width": 14 }));
        YEARS.forEach((y, i) => layer.appendChild(mk("circle", { class: "sum-hit-side", "data-side": s.id, "data-year": y, cx: g.X(y), cy: g.Y(f(sideAt(s, i))), r: 8, fill: "transparent" })));
      });
      g.svg.appendChild(layer);
      g.svg.addEventListener("pointerover", onPointer);
      g.svg.addEventListener("pointermove", onPointer);
      g.svg.addEventListener("pointerdown", onPointer);
      g.svg.addEventListener("pointerleave", () => hide());
    }

    function onPointer(ev: Event): void {
      const t = ev.target as Element;
      const side = t.closest?.(".sum-hit-side") as Element | null;
      if (side) { showSide(side.getAttribute("data-side")!, Number(side.getAttribute("data-year")) || 2031); return; }
      const yr = t.closest?.("[data-year]") as Element | null;
      if (yr) showYear(Number(yr.getAttribute("data-year")));
    }

    function place(x: number, y: number): void {
      pop.hidden = false;
      const W = wrap.clientWidth;
      const w = pop.offsetWidth;
      let left = x + 14;
      if (left + w > W - 4) left = Math.max(4, x - w - 14);
      pop.style.left = `${left}px`;
      pop.style.top = `${Math.max(0, y - 10)}px`;
    }

    function cross(year: number | null): void {
      const c = geom?.svg.querySelector<SVGLineElement>(".sum-cross");
      if (!c || !geom) return;
      if (year === null) { c.setAttribute("visibility", "hidden"); return; }
      c.setAttribute("x1", String(geom.X(year)));
      c.setAttribute("x2", String(geom.X(year)));
      c.setAttribute("visibility", "visible");
    }

    function showYear(year: number): void {
      const i = YEARS.indexOf(year);
      if (i < 0 || !geom) return;
      pop.dataset.kind = "year";
      pop.dataset.year = String(year);
      delete pop.dataset.side;
      pop.innerHTML = `<p class="sum-pop-h"><strong>${year}</strong></p><ul class="plain">
        <li><span class="sw sw-band" aria-hidden="true"></span>With the law, 90% range: <strong data-testid="pop-low">${fmt(lo(i))}</strong> to <strong data-testid="pop-high">${fmt(hi(i))}</strong></li>
        <li><span class="sw sw-law" aria-hidden="true"></span>Current law: <strong data-testid="pop-current-law">${fmt(extra ? 0 : o.base.central[i])}</strong>${extra ? " (the zero line)" : ""}</li>
        ${drawn.map((s, j) => `<li data-side="${esc(s.id)}"><span class="sw" style="background:${sideStyle(j).color}" aria-hidden="true"></span>${esc(s.label)}: <strong>${fmt(sideAt(s, i))}</strong></li>`).join("")}
      </ul><p class="small muted">${esc(extra ? `Extra ${yearUnit}` : yearUnit[0].toUpperCase() + yearUnit.slice(1))}.</p>`;
      cross(year);
      place(geom.X(year), geom.m.t);
    }

    function showSide(id: string, year = 2031): void {
      const j = drawn.findIndex((s) => s.id === id);
      if (j < 0 || !geom) return;
      const s = drawn[j];
      pop.dataset.kind = "side";
      pop.dataset.side = id;
      delete pop.dataset.year;
      pop.innerHTML = `<p class="sum-pop-h"><span class="sw" style="background:${sideStyle(j).color}" aria-hidden="true"></span><strong>${esc(s.label)}</strong></p>
        <p><strong data-testid="pop-side-value">${fmt(s.value!)}</strong> ${esc(unitShort)}, 2027–2031</p>
        <p class="small" data-testid="pop-side-note">${esc(s.note)}</p>`;
      cross(null);
      const yi = Math.max(0, YEARS.indexOf(year));
      place(geom.X(YEARS[yi]), geom.Y(f(sideAt(s, yi))));
    }

    function hide(): void {
      pop.hidden = true;
      delete pop.dataset.kind;
      cross(null);
    }

    root.querySelectorAll<HTMLButtonElement>(".sum-year").forEach((b) => {
      const y = Number(b.dataset.year);
      b.addEventListener("focus", () => showYear(y));
      b.addEventListener("mouseenter", () => showYear(y));
      b.addEventListener("click", () => showYear(y));
      b.addEventListener("blur", () => hide());
    });
    root.querySelectorAll<HTMLButtonElement>(".sum-side").forEach((b) => {
      const id = b.dataset.side!;
      b.addEventListener("focus", () => showSide(id));
      b.addEventListener("mouseenter", () => showSide(id));
      b.addEventListener("click", () => showSide(id));
      b.addEventListener("blur", () => hide());
    });
    // Escape hides the page popup; in the dialog, Escape closes the dialog itself (native behaviour)
    if (!big) root.addEventListener("keydown", (e) => { if (e.key === "Escape" && !pop.hidden) hide(); });
  }

  mountChart(main.querySelector<HTMLElement>(".summary-chart-card")!, false, main.querySelector<HTMLElement>("#sum-chart")!.clientWidth >= 900 ? 380 : undefined);

  // ---- "Enlarge chart": the same chart in a full-window native dialog ----------------------------
  const dlg = main.querySelector<HTMLDialogElement>("#sum-dialog")!;
  const dbody = main.querySelector<HTMLElement>("#sum-dialog-body")!;
  const enlarge = main.querySelector<HTMLButtonElement>("#sum-enlarge")!;
  const closeBtn = main.querySelector<HTMLButtonElement>("#sum-dialog-close")!;
  enlarge.addEventListener("click", () => {
    dbody.innerHTML = chartBlock(true);
    dlg.showModal();
    closeBtn.focus();
    // as tall as the window allows, leaving room for the heading, the key and the year buttons
    const room = dlg.clientHeight - (dbody.offsetTop + (dbody.querySelector<HTMLElement>(".sum-legend")?.offsetHeight ?? 0) + (dbody.querySelector<HTMLElement>(".sum-years")?.offsetHeight ?? 0) + 72);
    mountChart(dbody, true, Math.max(300, Math.round(room)));
  });
  closeBtn.addEventListener("click", () => dlg.close());
  dlg.addEventListener("close", () => { dbody.innerHTML = ""; enlarge.focus(); });
}
