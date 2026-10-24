"""Build a local HTML map for the Gate 2 owner review.

Layers (area-level only; no permit points or lot-level marks):
- Pilot tracts in Madison, Pleasant Prairie, and Sun Prairie, shaded by observed
  ADU and ADU-equivalent permits 2014-2025, with one-unit detached homes (ACS).
- Municipalities statewide, colored by coded current-law ADU rights class
  (37 coded places) or "not coded (MVP default: no ADU rights)".

Basemap: OpenStreetMap raster tiles (for local review only; attribution shown).
Output: data/processed/review/gate2_map.html (git-ignored).
Run: uv run python scripts/build_gate2_review_map.py
"""
from __future__ import annotations

import json

import geopandas as gpd
import pandas as pd

from missing_middleware.paths import PROCESSED, REFERENCE

ADU_CATS = {"adu_detached", "adu_attached", "adu_conversion", "adu_equivalent"}
CITIES = {
    "permits": "Madison",
    "permits_pleasant_prairie": "Pleasant Prairie",
    "permits_sun_prairie": "Sun Prairie",
}


def pilot_tracts() -> gpd.GeoDataFrame:
    geo = gpd.read_parquet(PROCESSED / "foundation/geo/areas_display.parquet")
    inv = pd.read_parquet(PROCESSED / "foundation/inventory.parquet")[["area_id", "homes_1unit_detached"]]
    frames = []
    for folder, city in CITIES.items():
        d = pd.read_parquet(PROCESSED / folder / "permits_by_area_year.parquet")
        d = d[(d.level == "tract") & d.year.between(2014, 2025)]
        adu = d[d.unit_category.isin(ADU_CATS)].groupby("area_id").units.sum()
        tracts = d.area_id.unique()
        f = pd.DataFrame({"area_id": tracts})
        f["city"] = city
        f["adu_permits_2014_2025"] = f.area_id.map(adu).fillna(0).astype(int)
        frames.append(f)
    t = pd.concat(frames).drop_duplicates("area_id")
    t = t.merge(inv, on="area_id", how="left")
    return geo.merge(t, on="area_id", how="inner")[
        ["area_id", "city", "adu_permits_2014_2025", "homes_1unit_detached", "geometry"]
    ]


def rights_munis() -> gpd.GeoDataFrame:
    geo = gpd.read_parquet(PROCESSED / "foundation/geo/areas_display.parquet")
    geo = geo[geo.level == "municipality"]
    r = pd.read_csv(REFERENCE / "wi_rights_exposure.csv", dtype=str)
    r = r[r.scenario_id == "adu_full"]
    r["area_id"] = "muni:" + r.jurisdiction_id
    g = geo.merge(r[["area_id", "jurisdiction_name", "current_class", "class_basis", "rules_as_of"]], on="area_id", how="left")
    g["current_class"] = g.current_class.fillna("not coded (default: no ADU rights)")
    g["jurisdiction_name"] = g.jurisdiction_name.fillna("")
    g["geometry"] = g.geometry.simplify(0.002)
    return g[["area_id", "jurisdiction_name", "current_class", "class_basis", "rules_as_of", "geometry"]]


HTML = """<!doctype html><html><head><meta charset="utf-8"><title>Gate 2 review map</title>
<meta name="viewport" content="width=device-width,initial-scale=1">
<link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css">
<script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
<style>body{margin:0;font:14px system-ui,sans-serif}#map{height:100vh}
.legend{background:#fff;padding:8px 10px;border-radius:4px;line-height:1.5}
.legend i{display:inline-block;width:14px;height:14px;margin-right:6px;vertical-align:-2px}</style></head>
<body><div id="map"></div><script>
const tracts=__TRACTS__, munis=__MUNIS__;
const map=L.map('map').setView([43.07,-89.4],11);
L.tileLayer('https://tile.openstreetmap.org/{z}/{x}/{y}.png',{maxZoom:18,
 attribution:'&copy; OpenStreetMap contributors'}).addTo(map);
const cls={'compliant':'#1b9e77','restricted':'#d95f02','prohibited':'#7570b3',
 'not coded (default: no ADU rights)':'#bbbbbb'};
const rights=L.geoJSON(munis,{style:f=>({color:'#555',weight:0.5,fillColor:cls[f.properties.current_class]||'#bbb',fillOpacity:f.properties.jurisdiction_name?0.8:0.15}),
 onEachFeature:(f,l)=>l.bindPopup(`<b>${f.properties.jurisdiction_name||f.properties.area_id}</b><br>Current law: ${f.properties.current_class}`+
 (f.properties.rules_as_of?`<br>Rules as of ${f.properties.rules_as_of} (${f.properties.class_basis})`:'') )});
function shade(n){return n>=10?'#08519c':n>=5?'#3182bd':n>=2?'#6baed6':n>=1?'#bdd7e7':'#f7fbff'}
const pilot=L.geoJSON(tracts,{style:f=>({color:'#222',weight:1,fillColor:shade(f.properties.adu_permits_2014_2025),fillOpacity:0.6}),
 onEachFeature:(f,l)=>l.bindPopup(`<b>${f.properties.city}</b> tract ${f.properties.area_id}<br>`+
 `Observed ADU + ADU-equivalent permits 2014-2025: ${f.properties.adu_permits_2014_2025}<br>`+
 `One-unit detached homes (ACS 2020-24): ${f.properties.homes_1unit_detached??'n/a'}`)}).addTo(map);
L.control.layers(null,{'Pilot tracts: observed ADU permits':pilot,'Statewide: coded current-law ADU rights':rights},{collapsed:false}).addTo(map);
const lg=L.control({position:'bottomright'});lg.onAdd=()=>{const d=L.DomUtil.create('div','legend');
d.innerHTML='<b>Observed ADU permits 2014-25 (tract)</b><br>'+[[10,'10+'],[5,'5-9'],[2,'2-4'],[1,'1'],[0,'0']].map(([n,t])=>`<i style="background:${shade(n)}"></i>${t}`).join('<br>')+
'<br><b>Current-law rights</b><br>'+Object.entries(cls).map(([k,v])=>`<i style="background:${v}"></i>${k}`).join('<br>')+
'<br><small>Pale green on the basemap is national forest, not a rights class.<br>Area totals only; no lot-level marks.<br>Jump: <a href="#" onclick="map.setView([43.07,-89.4],11)">Madison</a> | '+
'<a href="#" onclick="map.setView([42.54,-87.9],12)">Pleasant Prairie</a> | <a href="#" onclick="map.setView([43.18,-89.21],12)">Sun Prairie</a> | '+
'<a href="#" onclick="map.setView([44.6,-89.8],7)">Wisconsin</a></small>';return d};lg.addTo(map);
</script></body></html>"""


def main() -> None:
    out = PROCESSED / "review"
    out.mkdir(parents=True, exist_ok=True)
    t = pilot_tracts()
    m = rights_munis()
    html = HTML.replace("__TRACTS__", t.to_json()).replace("__MUNIS__", m.to_json())
    (out / "gate2_map.html").write_text(html)
    summary = t.groupby("city").agg(tracts=("area_id", "size"), adu_permits=("adu_permits_2014_2025", "sum"),
                                     homes=("homes_1unit_detached", "sum"))
    print(summary.to_string())
    print(m.current_class.value_counts().to_string())
    print("wrote", out / "gate2_map.html")


if __name__ == "__main__":
    main()
