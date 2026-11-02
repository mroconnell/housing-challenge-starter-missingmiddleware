// A simple, dependency-free SVG map of station areas: municipality outlines, the ½-mile and ¼-mile circles around
// qualifying stops (drawn in one translucent group so overlaps read as one area), and the stops. No basemap and no
// lots: nothing on it can be read as a prediction for a parcel. The table beside it carries the same numbers.
import { esc } from "../../format";
import type { MapData } from "./types";

export interface MapOpts {
  view: string;
  /** Names of places to label (by outline name). */
  labels: string[];
  /** Show 20-minute bus stops (the wider definition) as well as main-case stops. */
  showWide?: boolean;
  /** Draw the bus station areas paler, so the rail and rapid corridor stands out. */
  emphasizeRapid?: boolean;
  /** Rail and rapid stations only: ½-mile and ¼-mile circles, no bus stops, and no tint for places the model gives homes. */
  rapidOnly?: boolean;
  title: string;
  desc: string;
}

const C = { rapid: "#7b3fb0", bus: "#17644f", wide: "#8a5a00", land: "#f3f3f1", tod: "#e3ece8", line: "#9aa29e" };

export function stationMap(d: MapData, o: MapOpts): string {
  const v = d.views.find((x) => x.id === o.view) ?? d.views[0];
  // rail-and-rapid map: fit the view to its rail and rapid stops (the view's bounds cover every bus stop too)
  const rs = d.stops.filter((s) => s[2] === "r" && v.agencies.includes(s[3]));
  const pad = 0.012;
  const [x0, y0, x1, y1] = o.rapidOnly && rs.length
    ? [Math.min(...rs.map((s) => s[0])) - pad * 1.4, Math.min(...rs.map((s) => s[1])) - pad, Math.max(...rs.map((s) => s[0])) + pad * 1.4, Math.max(...rs.map((s) => s[1])) + pad]
    : v.bounds;
  const k = Math.cos((((y0 + y1) / 2) * Math.PI) / 180);
  const W = 800;
  const sc = W / ((x1 - x0) * k);
  const H = Math.round((y1 - y0) * sc);
  const X = (lon: number) => ((lon - x0) * k * sc).toFixed(1);
  const Y = (lat: number) => ((y1 - lat) * sc).toFixed(1);
  const R = (mi: number) => ((mi / 69.05) * sc).toFixed(1);
  const inView = (p: [number, number]) => p[0] >= x0 && p[0] <= x1 && p[1] >= y0 && p[1] <= y1;
  const outlines = d.outlines.filter((f) => f.views.includes(v.id));
  const paths = outlines.map((f) => `<path d="${f.rings.map((rg) => rg.map((p, i) => `${i ? "L" : "M"}${X(p[0])},${Y(p[1])}`).join("") + "Z").join("")}" fill="${f.tod && !o.rapidOnly ? C.tod : C.land}" stroke="${C.line}" stroke-width="0.8"/>`).join("");
  const stops = d.stops.filter((s) => v.agencies.includes(s[3]) && inView([s[0], s[1]]));
  const circles = (kind: "r" | "b" | "c", mi = d.radius_mi[kind]) => stops.filter((s) => s[2] === kind).map((s) => `<circle cx="${X(s[0])}" cy="${Y(s[1])}" r="${R(mi)}"/>`).join("");
  const dots = (kind: "r" | "b" | "c", r: number, fill: string) => stops.filter((s) => s[2] === kind).map((s) => `<circle cx="${X(s[0])}" cy="${Y(s[1])}" r="${r}" fill="${fill}"/>`).join("");
  // labels at the centre of each named place's largest ring (inside the view)
  const lab: string[] = [];
  const seen = new Set<string>();
  for (const f of outlines) {
    if (!f.name || !o.labels.includes(f.name) || seen.has(f.name)) continue;
    const ring = [...f.rings].sort((a, b) => b.length - a.length)[0];
    const xs = ring.map((p) => p[0]), ys = ring.map((p) => p[1]);
    const cx = Math.min(Math.max((Math.min(...xs) + Math.max(...xs)) / 2, x0 + (x1 - x0) * 0.13), x1 - (x1 - x0) * 0.13);
    const my = o.rapidOnly ? 0.14 : 0; // the rail-and-rapid map is short: keep labels clear of the top and the scale bar
    const cy = Math.min(Math.max((Math.min(...ys) + Math.max(...ys)) / 2, y0 + (y1 - y0) * (0.07 + my)), y1 - (y1 - y0) * (0.05 + my));
    seen.add(f.name);
    lab.push(`<text x="${X(cx)}" y="${Y(cy)}" text-anchor="middle" class="tod-map-label">${esc(f.name.replace(/ (city|village|town)$/, ""))}</text>`);
  }
  const mile = Number(R(1));
  const sb = `<g transform="translate(20 ${H - 20})"><rect x="-6" y="-22" width="${mile + 80}" height="34" fill="#fff" opacity="0.85" rx="3"/><line x1="0" x2="${mile}" y1="0" y2="0" stroke="#1d2623" stroke-width="3"/><line x1="0" x2="0" y1="-4" y2="4" stroke="#1d2623"/><line x1="${mile}" x2="${mile}" y1="-4" y2="4" stroke="#1d2623"/><text x="${mile + 6}" y="6" class="tod-map-scale">1 mile</text></g>`;
  const id = `tod-map-${v.id}`;
  return `<figure class="tod-map"><svg viewBox="0 0 ${W} ${H}" role="img" aria-labelledby="${id}-t ${id}-d" preserveAspectRatio="xMidYMid meet">
    <title id="${id}-t">${esc(o.title)}</title><desc id="${id}-d">${esc(o.desc)}</desc>
    <rect width="${W}" height="${H}" fill="#dce8ef"/>
    ${paths}
    ${o.rapidOnly ? `<g fill="${C.rapid}" opacity="0.2">${circles("r")}</g><g fill="${C.rapid}" opacity="0.3">${circles("r", 0.25)}</g>${dots("r", 2.6, C.rapid)}` : `
    ${o.showWide ? `<g fill="${C.wide}" opacity="0.22">${circles("c")}</g>` : ""}
    <g fill="${C.bus}" opacity="${o.emphasizeRapid ? 0.12 : 0.28}">${circles("b")}</g>
    <g fill="${C.rapid}" opacity="0.3">${circles("r")}</g>
    ${o.showWide ? dots("c", 2.4, C.wide) : ""}${dots("b", 1.3, C.bus)}${dots("r", 2.6, C.rapid)}`}
    ${lab.join("")}${sb}
  </svg></figure>`;
}

/** Key for the rail-and-rapid-only map (stationMap with rapidOnly). */
export function rapidMapKey(): string {
  const sw = (op: number) => `<svg width="18" height="14" aria-hidden="true" focusable="false"><rect width="18" height="14" rx="3" fill="${C.rapid}" opacity="${op}"/></svg>`;
  return `<ul class="legend" aria-label="Map key">
    <li><svg width="14" height="14" aria-hidden="true" focusable="false"><circle cx="7" cy="7" r="4" fill="${C.rapid}"/></svg> Rail or rapid transit stop</li>
    <li>${sw(0.5)} Within ¼ mile</li>
    <li>${sw(0.25)} ¼ to ½ mile</li></ul>`;
}

export function mapKey(showWide = false): string {
  const sw = (c: string, op: number) => `<svg width="18" height="14" aria-hidden="true" focusable="false"><rect width="18" height="14" rx="3" fill="${c}" opacity="${op}"/></svg>`;
  return `<ul class="legend" aria-label="Map key">
    <li>${sw(C.rapid, 0.45)} Within ½ mile of a rail or rapid transit station</li>
    <li>${sw(C.bus, 0.4)} Within ¼ mile of a stop on a bus route every 15 minutes</li>
    ${showWide ? `<li>${sw(C.wide, 0.35)} Within ¼ mile of a stop on a bus route every 20 minutes (wider definition only)</li>` : ""}
    <li>${sw(C.tod, 1)} Places the model gives extra homes</li></ul>`;
}
