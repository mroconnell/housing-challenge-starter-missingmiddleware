"""Download the inputs for the batch-2 TOD comparison cases (docs/tod/CASE_ANALYSIS_PLAN.md, section 7, entry of
2026-10-27 "more cities for the trait test") into data/raw/tod_cases/<city>/.

    uv run --all-extras python scripts/fetch_tod_cases_batch2.py [--city toronto ottawa minneapolis] [--refresh]

Raw (git-ignored): data/raw/tod_cases/<city>/...  and  data/raw/tod_cases/<city>/manifest.json
(URL, access time, bytes, SHA-256, licence, feature counts). Existing files are kept unless --refresh.
Helpers (Manifest, ArcGIS paging) are reused from scripts/fetch_tod_cases.py.

Every file comes from the publishing government's own service:
- Toronto (Eglinton Connects, By-law 1030-2014): City of Toronto Open Data (CKAN) building permits (cleared
  2000-2016, cleared since 2017, active), Zoning By-law 569-2013 zone areas and height overlay (current), address
  points, property boundaries, TTC GTFS (stations), and the by-law PDF itself (its exception numbers 2621-2648
  identify the by-law's lands in the zoning layer). Licence: Open Government Licence - Toronto
  (https://open.toronto.ca/open-data-license/; the CKAN records say "License not specified", the portal's terms
  page governs all of its datasets).
- Ottawa (TD zone, By-law 2012-406): City of Ottawa construction permit monthly workbooks (July 2011 on; Open Ottawa
  hub items), Zoning By-law 2008-250 TD zone polygons (current, with amending by-law numbers and history), O-Train
  Stage 1 stations. Licence: Open Government Licence - City of Ottawa, version 2.0.
- Minneapolis (Hiawatha station areas 2008-2012): City of Minneapolis yearly building permit layers 2000-2014 (no
  unit counts), new non-single-family permits with units 2010-2015, 2017 primary zoning snapshot, transit stations,
  2017 assessor parcels near the Hiawatha stations. Licence: CC0 1.0 (City of Minneapolis open data).
"""
from __future__ import annotations

import argparse
import importlib.util
import sys
import time
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from missing_middleware.paths import RAW  # noqa: E402

_spec = importlib.util.spec_from_file_location("fetch_tod_cases", ROOT / "scripts" / "fetch_tod_cases.py")
F = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(F)  # Manifest, http_get, save_layer, arcgis_query, UA

D = RAW / "tod_cases"

# --------------------------------------------------------------------------- Toronto

TOR_LICENCE = "Open Government Licence - Toronto (https://open.toronto.ca/open-data-license/)"
TOR_CKAN = "https://ckan0.cf.opendata.inter.prod-toronto.ca"
TOR_FILES = {
    # name: (url, note)
    "permits_cleared_2000_2016.csv": (f"{TOR_CKAN}/dataset/9e42a85b-180f-4dc5-b0d7-d46661a6c0ec/resource/"
                                      "c647bdae-0127-425e-86e6-2d88ff0e2adf/download/export_202507081211.csv",
                                      "Building Permits - Cleared Permits, 2000 to 2016"),
    "permits_cleared_since_2017.csv": (f"{TOR_CKAN}/dataset/9e42a85b-180f-4dc5-b0d7-d46661a6c0ec/resource/"
                                       "b41c3e9e-4d2d-4b09-a789-9569d8da407c/download/cleared-building-permits-since-2017.csv",
                                       "Building Permits - Cleared Permits since 2017"),
    "permits_active.csv": (f"{TOR_CKAN}/datastore/dump/6d0229af-bc54-46de-9c2b-26759b01dd05", "Building Permits - Active Permits"),
    "zoning_area.gpkg": (f"{TOR_CKAN}/dataset/34927e44-fc11-4336-a8aa-a0dfb27658b7/resource/"
                         "f9b16f51-e957-4a2a-88e6-4b9679668e11/download/zoning-area-4326.gpkg",
                         "Zoning By-law 569-2013 zone areas, current consolidation"),
    "zoning_height_overlay.geojson": (f"{TOR_CKAN}/dataset/34927e44-fc11-4336-a8aa-a0dfb27658b7/resource/"
                                      "eec27e60-7c2d-4c46-8fa1-b64f441bcc39/download/zoning-height-overlay-4326.geojson",
                                      "Zoning By-law 569-2013 height overlay, current"),
    "address_points.gpkg": (f"{TOR_CKAN}/dataset/abedd8bc-e3dd-4d45-8e69-79165a76e4fa/resource/"
                            "9a7495b3-055c-4c9c-b3b3-e164c3cc6b03/download/address-points-2952.gpkg",
                            "Address Points (Municipal), EPSG:2952"),
    "property_boundaries.gpkg": (f"{TOR_CKAN}/dataset/1acaa8b0-f235-4df6-8305-02025ccdeb07/resource/"
                                 "146daed7-a226-4a0d-817e-7ec772a6bbc6/download/property-boundaries-2952.gpkg",
                                 "Property Boundaries, EPSG:2952"),
    "bylaw_1030_2014.pdf": ("https://www.toronto.ca/legdocs/bylaws/2014/law1030.pdf",
                            "By-law 1030-2014 (Eglinton Connects); exceptions 2621-2648 identify its lands"),
}
TOR_GTFS_PACKAGE = "merged-gtfs-ttc-routes-and-schedules"  # the older "ttc-routes-and-schedules" zip is empty (22 bytes)


def big_download(url: str, dest: Path, retries: int = 6, timeout: int = 1800) -> bytes:
    """Stream a large file to disk with retries (the Toronto portal returns 502/504 intermittently)."""
    last = None
    for attempt in range(retries):
        try:
            req = urllib.request.Request(url, headers=F.UA)
            with urllib.request.urlopen(req, timeout=timeout) as r, open(dest.with_suffix(dest.suffix + ".part"), "wb") as fh:
                while True:
                    b = r.read(1 << 20)
                    if not b:
                        break
                    fh.write(b)
            data = dest.with_suffix(dest.suffix + ".part").read_bytes()
            if data[:200].lstrip().lower().startswith((b"<html", b"<!doctype")):
                raise RuntimeError(f"HTML error page from {url}")
            dest.with_suffix(dest.suffix + ".part").unlink()
            return data
        except Exception as e:  # noqa: BLE001
            last = e
            print(f"    retry {attempt + 1}/{retries}: {type(e).__name__}: {e}")
            time.sleep(20 * (attempt + 1))
    raise RuntimeError(f"{url}: {last}")


def tor_get(man, name: str, url: str, refresh: bool, licence: str, **extra) -> None:
    if man.have(name, refresh):
        print(f"  {name}: kept")
        return
    data = big_download(url, man.folder / name)
    man.record(name, data, url, licence=licence, **extra)


def fetch_toronto(refresh: bool) -> None:
    import json
    man = F.Manifest(D / "toronto", "tod_cases_toronto", "City of Toronto (Open Data portal; City Clerk for by-laws)")
    for name, (url, note) in TOR_FILES.items():
        tor_get(man, name, url, refresh, TOR_LICENCE, note=note)
    # TTC GTFS: the current resource URL is read from the CKAN package record
    if not man.have("ttc_gtfs.zip", refresh) or man.m["files"].get("ttc_gtfs.zip", {}).get("bytes", 0) < 1000:
        pk = json.loads(F.http_get(f"{TOR_CKAN}/api/3/action/package_show", {"id": TOR_GTFS_PACKAGE}))["result"]
        res = [r for r in pk["resources"] if r["url"].endswith(".zip")]
        tor_get(man, "ttc_gtfs.zip", res[0]["url"], True, TOR_LICENCE,
                note="TTC merged GTFS (Complete GTFS), current; only rail and rapid-transit stops are used")


# --------------------------------------------------------------------------- Ottawa

OTT_LICENCE = "Open Government Licence - City of Ottawa, version 2.0 (https://ottawa.ca/en/city-hall/get-know-your-city/open-data#open-data-licence-version-2-0)"
OTT_PERMIT_ITEMS = {  # Open Ottawa hub items: construction, demolition and pool enclosure permits, monthly
    "2011h2": "89846cecb39749b7b7db7ba74fb9d31d", "2012": "aba9890bf3334eeb8e31501e92f2f83c",
    "2013": "9e821ceff81d468aa68111ae9d624b87", "2014": "60c0f061232749e1ae7ea5263b61f25f",
    "2015": "a2b214f0d407491793359af4af32e7ba", "2016": "273b520c126f40cfbf24a7689902fb85",
    "2017": "8dcbb960cc9f452e852494fb181ea91a", "2018": "c42cca39b76d456e9c22e8343a55b802",
    "2019": "a457ac00a07647e0a913a28052df4d85", "2020": "54afabbba45a4607a420c6f9d7b88842",
    "2021": "dc3eecea58054e0e90ed25d8988495e1", "2022": "6b99841340444f83ba2595190e4e143b",
    "2023": "0c19879709c14d008d078f2ae3007e07", "2024_2025": "05046d836248455d92cbc0543ce4c022",
}
OTT_ZONING = "https://maps.ottawa.ca/arcgis/rest/services/Zoning_Bylaw_2008_250/MapServer/3"
OTT_STATIONS = "https://maps.ottawa.ca/arcgis/rest/services/Rail_Implementation_Office/MapServer/11"


def fetch_ottawa(refresh: bool) -> None:
    man = F.Manifest(D / "ottawa", "tod_cases_ottawa", "City of Ottawa (Open Ottawa; maps.ottawa.ca)")
    for label, item in OTT_PERMIT_ITEMS.items():
        # some yearly workbooks are old-format Excel (OLE) despite the hub's .xlsx name: saved with the true extension
        if any(man.have(f"permits/permits_{label}.{e}", refresh) for e in ("xlsx", "xls")):
            print(f"  permits_{label}: kept")
            continue
        url = f"https://www.arcgis.com/sharing/rest/content/items/{item}/data"
        data = F.http_get(url, timeout=600)
        ext = "xls" if data[:4] == b"\xd0\xcf\x11\xe0" else "xlsx"
        man.record(f"permits/permits_{label}.{ext}", data, url, licence=OTT_LICENCE, hub_item=item)
    F.save_layer(man, "td_zones.geojson", OTT_ZONING, refresh, OTT_LICENCE, where="ZONE_MAIN LIKE 'TD%'",
                 out_fields="ZONE_CODE,ZONE_MAIN,BYLAW_NUM,CONS_DATE,HISTORY,HEIGHT,HEIGHTINFO", page=1000)
    F.save_layer(man, "otrain_stage1_stations.geojson", OTT_STATIONS, refresh, OTT_LICENCE, page=1000)


# --------------------------------------------------------------------------- Minneapolis

MPLS = "https://services.arcgis.com/afSMGVsC7QlRK1kZ/arcgis/rest/services"
MPLS_LICENCE = "CC0 1.0 (City of Minneapolis open data)"
MPLS_STATIONS = ("Franklin Avenue", "Lake Street", "38th Street", "46th Street IB", "46th Street OB",
                 "50th Street/Minnehaha Park IB", "50th Street/Minnehaha Park OB", "Cedar-Riverside")


def fetch_minneapolis(refresh: bool) -> None:
    man = F.Manifest(D / "minneapolis", "tod_cases_minneapolis", "City of Minneapolis (open data ArcGIS services)")
    for y in range(2000, 2015):
        F.save_layer(man, f"permits/permits_{y}.geojson", f"{MPLS}/Minneapolis_Building_Permits_{y}/FeatureServer/0",
                     refresh, MPLS_LICENCE, out_fields="APN,Permit_Type,Permit_Number,Date,Address,Year,Use_Code", page=2000)
    F.save_layer(man, "permits_non_sfd_units_2010_2015.geojson", f"{MPLS}/New_Non_SFD_Building_Permits_2010_2015/FeatureServer/0",
                 refresh, MPLS_LICENCE, out_fields="APN,Permit_Type,Permit_Number,Permit_Issue_Date,Address,Use_,Use_Code,Referenced_Dwelling_Units",
                 page=2000)
    F.save_layer(man, "transit_stations.geojson", f"{MPLS}/Transit_Stations/FeatureServer/0", refresh, MPLS_LICENCE, page=1000)
    F.save_layer(man, "zoning_2017_01.geojson", f"{MPLS}/msvcCPED_PrimaryZoning_20170126/FeatureServer/0", refresh,
                 MPLS_LICENCE, out_fields="ZONE_CODE", page=2000)


FETCHERS = {"toronto": fetch_toronto, "ottawa": fetch_ottawa, "minneapolis": fetch_minneapolis}


def main(argv=None) -> None:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--city", nargs="*", choices=list(FETCHERS), help="default: all")
    ap.add_argument("--refresh", action="store_true", help="re-download files that already exist")
    a = ap.parse_args(argv)
    for c in a.city or list(FETCHERS):
        print(f"== {c}")
        FETCHERS[c](a.refresh)


if __name__ == "__main__":
    main()
