// County, municipality and legislative-district choropleth with MapLibre GL JS (BSD-3-Clause). No basemap: area fills only,
// no point markers, so nothing on the map can be read as a prediction for a lot. Optional overlays (county
// name labels now; transit-stop labels and buffers later) sit above the fills; see OverlaySpec.
import * as maplibregl from "maplibre-gl";
import "maplibre-gl/dist/maplibre-gl.css";
import workerUrl from "maplibre-gl/dist/maplibre-gl-worker.mjs?url";

maplibregl.setWorkerUrl(workerUrl);

export const RAMP = ["#fde725", "#7ad151", "#22a884", "#2a788e", "#414487"]; // viridis, colour-blind safe
export const WI_BOUNDS: [number, number, number, number] = [-92.9, 42.45, -86.75, 47.15];
export const WATER = "#dce8ef"; // background: lakes and outside Wisconsin (the outlines are shoreline-clipped)
const PAD = { top: 12, right: 44, bottom: 12, left: 12 }; // right: room for the zoom buttons

/** An optional layer drawn above the area fills: text labels now, and later e.g. buffers around transit stops.
 *  Each overlay has its own GeoJSON source; `kind` picks the drawing. Add new kinds in `overlayLayers`. */
export interface OverlaySpec {
  id: string;                          // e.g. "county-labels", later "transit-stops", "transit-buffers"
  kind: "labels" | "buffer";           // labels: point features with a "name"; buffer: polygon features (outline + light fill)
  data: GeoJSON.FeatureCollection;
  visible: boolean;
  color?: string;
  minzoom?: number;
}

/** Self-hosted glyphs (ui/public/fonts, Open Sans Semibold, Apache-2.0) for map text. */
export const LABEL_FONT = "open-sans-semibold";
function glyphsUrl(): string {
  // MapLibre needs an absolute URL; keep {fontstack} and {range} unencoded
  return new URL("./", location.href).href + "fonts/{fontstack}/{range}.pbf";
}

function overlayLayers(o: OverlaySpec): maplibregl.LayerSpecification[] {
  const vis = o.visible ? "visible" : "none";
  if (o.kind === "labels") return [{
    id: `${o.id}-text`, type: "symbol", source: o.id, minzoom: o.minzoom ?? 0,
    layout: { visibility: vis, "text-field": ["get", "name"], "text-font": [LABEL_FONT], "text-size": ["interpolate", ["linear"], ["zoom"], 5, 10, 8, 14],
      "text-allow-overlap": false, "text-padding": 2, "text-max-width": 8 },
    paint: { "text-color": "#1d2623", "text-halo-color": "rgba(255,255,255,0.9)", "text-halo-width": 1.4 },
  }];
  return [
    { id: `${o.id}-fill`, type: "fill", source: o.id, minzoom: o.minzoom ?? 0, layout: { visibility: vis }, paint: { "fill-color": o.color ?? "#c2410c", "fill-opacity": 0.12 } },
    { id: `${o.id}-line`, type: "line", source: o.id, minzoom: o.minzoom ?? 0, layout: { visibility: vis }, paint: { "line-color": o.color ?? "#c2410c", "line-width": 1.5 } },
  ];
}

export type GeoKind = "counties" | "munis" | "assembly" | "senate";
const GEOS: GeoKind[] = ["counties", "munis", "assembly", "senate"];

export interface MapHandle {
  setData(values: Map<string, number | null>, breaks: number[]): void;
  addOverlay(o: OverlaySpec): void;
  setOverlayVisible(id: string, visible: boolean): void;
  setGeography(kind: GeoKind): void;
  select(id: string | null): void;
  resize(): void;
  destroy(): void;
}

function hatchImage(): ImageData {
  const s = 8, c = document.createElement("canvas");
  c.width = c.height = s;
  const g = c.getContext("2d")!;
  g.fillStyle = "#f3f3f1"; g.fillRect(0, 0, s, s);
  g.strokeStyle = "#8a8f8c"; g.lineWidth = 1.2;
  g.beginPath(); g.moveTo(0, s); g.lineTo(s, 0); g.stroke();
  return g.getImageData(0, 0, s, s);
}

export function createMap(el: HTMLElement, geo: Record<GeoKind, unknown>, onPick: (id: string) => void,
  onHover: (id: string | null, x: number, y: number) => void): MapHandle {
  const map = new maplibregl.Map({
    container: el,
    style: { version: 8, glyphs: glyphsUrl(), sources: {}, layers: [{ id: "bg", type: "background", paint: { "background-color": WATER } }] },
    bounds: WI_BOUNDS,
    fitBoundsOptions: { padding: PAD },
    attributionControl: false,
    dragRotate: false,
    pitchWithRotate: false,
    touchPitch: false,
    maxBounds: [-95.5, 41.2, -84.2, 48.4],
  });
  map.addControl(new maplibregl.NavigationControl({ showCompass: false }), "top-right");
  // No tiles, so no attribution is required on the canvas; the boundary source is credited under the map instead,
  // which keeps the south-east corner (Kenosha) clear.
  map.touchZoomRotate.disableRotation();
  // Fit the whole state whenever the container settles at a new size, until the reader pans or zooms.
  let userMoved = false;
  map.on("dragstart", () => { userMoved = true; });
  map.on("zoomstart", (e) => { if ((e as { originalEvent?: Event }).originalEvent) userMoved = true; });
  const fit = () => { map.resize(); if (!userMoved) map.fitBounds(WI_BOUNDS, { padding: PAD, animate: false }); };
  let lastSize = "";
  const ro = new ResizeObserver(() => {
    const size = `${el.clientWidth}x${el.clientHeight}`;
    if (size !== lastSize) { lastSize = size; fit(); }
  });
  ro.observe(el);
  let kind: GeoKind = "counties";
  let pending: (() => void)[] = [];
  let ready = false;
  let selected: string | null = null;

  const fillColor = (breaks: number[]): maplibregl.ExpressionSpecification => [
    "case", ["==", ["feature-state", "v"], null], "rgba(0,0,0,0)",
    ["step", ["feature-state", "v"], RAMP[0], breaks[0], RAMP[1], breaks[1], RAMP[2], breaks[2], RAMP[3], breaks[3], RAMP[4]],
  ] as unknown as maplibregl.ExpressionSpecification;

  map.on("load", () => {
    fit();
    map.addImage("hatch", hatchImage(), { pixelRatio: 1 });
    for (const k of GEOS) {
      map.addSource(k, { type: "geojson", data: geo[k] as GeoJSON.FeatureCollection, promoteId: "id" });
      map.addLayer({ id: `${k}-missing`, type: "fill", source: k, paint: { "fill-pattern": "hatch" }, layout: { visibility: k === kind ? "visible" : "none" } });
      map.addLayer({ id: `${k}-fill`, type: "fill", source: k, paint: { "fill-color": "rgba(0,0,0,0)", "fill-opacity": 1 }, layout: { visibility: k === kind ? "visible" : "none" } });
      map.addLayer({ id: `${k}-line`, type: "line", source: k, paint: { "line-color": "#ffffff", "line-width": k === "munis" ? 0.25 : 0.9, "line-opacity": 0.9 }, layout: { visibility: k === kind ? "visible" : "none" } });
    }
    // county outlines over counties and municipalities only; district views show district outlines alone
    map.addLayer({ id: "county-outline", type: "line", source: "counties", paint: { "line-color": "#2b2f2d", "line-width": 0.7, "line-opacity": 0.55 }, layout: { visibility: kind === "counties" || kind === "munis" ? "visible" : "none" } });
    for (const k of GEOS)
      map.addLayer({ id: `${k}-sel`, type: "line", source: k, filter: ["==", ["get", "id"], "__none__"], paint: { "line-color": "#d1361a", "line-width": 3 }, layout: { visibility: k === kind ? "visible" : "none" } });
    for (const k of GEOS) {
      map.on("click", `${k}-fill`, (e: maplibregl.MapLayerMouseEvent) => { const f = e.features?.[0]; if (f) onPick(String(f.properties!.id)); });
      map.on("mousemove", `${k}-fill`, (e: maplibregl.MapLayerMouseEvent) => {
        const f = e.features?.[0];
        map.getCanvas().style.cursor = f ? "pointer" : "";
        onHover(f ? String(f.properties!.id) : null, e.point.x, e.point.y);
      });
      map.on("mouseleave", `${k}-fill`, () => { map.getCanvas().style.cursor = ""; onHover(null, 0, 0); });
    }
    ready = true;
    pending.forEach((f) => f());
    pending = [];
  });
  const when = (f: () => void) => (ready ? f() : pending.push(f));

  const overlays = new Map<string, OverlaySpec>();
  return {
    addOverlay(o) {
      overlays.set(o.id, o);
      when(() => {
        if (map.getSource(o.id)) return;
        map.addSource(o.id, { type: "geojson", data: o.data });
        for (const l of overlayLayers(o)) map.addLayer(l);   // added last, so above fills, outlines and selection
      });
    },
    setOverlayVisible(id, visible) {
      const o = overlays.get(id);
      if (!o) return;
      o.visible = visible;
      when(() => { for (const l of overlayLayers(o)) if (map.getLayer(l.id)) map.setLayoutProperty(l.id, "visibility", visible ? "visible" : "none"); });
    },
    setData(values, breaks) {
      when(() => {
        for (const [id, v] of values) map.setFeatureState({ source: kind, id }, { v });
        map.setPaintProperty(`${kind}-fill`, "fill-color", fillColor(breaks));
      });
    },
    setGeography(k) {
      kind = k;
      when(() => {
        for (const g of GEOS) for (const suffix of ["missing", "fill", "line", "sel"])
          map.setLayoutProperty(`${g}-${suffix}`, "visibility", g === k ? "visible" : "none");
        map.setLayoutProperty("county-outline", "visibility", k === "counties" || k === "munis" ? "visible" : "none");
      });
    },
    select(id) {
      selected = id;
      when(() => map.setFilter(`${kind}-sel`, ["==", ["get", "id"], selected ?? "__none__"]));
    },
    resize() { map.resize(); },
    destroy() { ro.disconnect(); map.remove(); },
  };
}
