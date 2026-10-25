// County and municipality choropleth with MapLibre GL JS (BSD-3-Clause). No basemap: area fills only,
// no point symbols, so nothing on the map can be read as a prediction for a lot.
import * as maplibregl from "maplibre-gl";
import "maplibre-gl/dist/maplibre-gl.css";
import workerUrl from "maplibre-gl/dist/maplibre-gl-worker.mjs?url";

maplibregl.setWorkerUrl(workerUrl);

export const RAMP = ["#fde725", "#7ad151", "#22a884", "#2a788e", "#414487"]; // viridis, colour-blind safe
export const WI_BOUNDS: [number, number, number, number] = [-92.9, 42.45, -86.75, 47.15];
export const WATER = "#dce8ef"; // background: lakes and outside Wisconsin (the outlines are shoreline-clipped)
const PAD = { top: 12, right: 44, bottom: 12, left: 12 }; // right: room for the zoom buttons

export interface MapHandle {
  setData(values: Map<string, number | null>, breaks: number[]): void;
  setGeography(kind: "counties" | "munis"): void;
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

export function createMap(el: HTMLElement, geo: { counties: unknown; munis: unknown }, onPick: (id: string) => void,
  onHover: (id: string | null, x: number, y: number) => void): MapHandle {
  const map = new maplibregl.Map({
    container: el,
    style: { version: 8, sources: {}, layers: [{ id: "bg", type: "background", paint: { "background-color": WATER } }] },
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
  let kind: "counties" | "munis" = "counties";
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
    for (const k of ["counties", "munis"] as const) {
      map.addSource(k, { type: "geojson", data: geo[k] as GeoJSON.FeatureCollection, promoteId: "id" });
      map.addLayer({ id: `${k}-missing`, type: "fill", source: k, paint: { "fill-pattern": "hatch" }, layout: { visibility: k === kind ? "visible" : "none" } });
      map.addLayer({ id: `${k}-fill`, type: "fill", source: k, paint: { "fill-color": "rgba(0,0,0,0)", "fill-opacity": 1 }, layout: { visibility: k === kind ? "visible" : "none" } });
      map.addLayer({ id: `${k}-line`, type: "line", source: k, paint: { "line-color": "#ffffff", "line-width": k === "counties" ? 0.9 : 0.25, "line-opacity": 0.9 }, layout: { visibility: k === kind ? "visible" : "none" } });
    }
    map.addLayer({ id: "county-outline", type: "line", source: "counties", paint: { "line-color": "#2b2f2d", "line-width": 0.7, "line-opacity": 0.55 } });
    for (const k of ["counties", "munis"] as const)
      map.addLayer({ id: `${k}-sel`, type: "line", source: k, filter: ["==", ["get", "id"], "__none__"], paint: { "line-color": "#d1361a", "line-width": 3 }, layout: { visibility: k === kind ? "visible" : "none" } });
    for (const k of ["counties", "munis"] as const) {
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

  return {
    setData(values, breaks) {
      when(() => {
        for (const [id, v] of values) map.setFeatureState({ source: kind, id }, { v });
        map.setPaintProperty(`${kind}-fill`, "fill-color", fillColor(breaks));
      });
    },
    setGeography(k) {
      kind = k;
      when(() => {
        for (const g of ["counties", "munis"]) for (const suffix of ["missing", "fill", "line", "sel"])
          map.setLayoutProperty(`${g}-${suffix}`, "visibility", g === k ? "visible" : "none");
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
