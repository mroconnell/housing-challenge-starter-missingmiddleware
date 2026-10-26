"""Download the TOD transit inputs: BTS National Transit Map layers for every Wisconsin agency, and
the official GTFS schedule files whose terms allow our use.

    uv run python scripts/fetch_tod_transit.py [--only ntm|gtfs] [--feed NTD_ID ...]

Raw (git-ignored): data/raw/tod_transit/ntm/{agencies.json,stops.json,routes.geojson}
                   data/raw/tod_transit/gtfs/<ntd_id>_<label>.zip
                   data/raw/tod_transit/manifest.json (URL, access time, bytes, SHA-256, HTTP Last-Modified)

Rules (docs/tod/TRANSIT_PIPELINE.md, AQ-045, AQ-047):
- Madison Metro's own GTFS file is never downloaded (licence question open). Madison frequency comes
  from the route descriptions in the NTM routes layer.
- MCTS: the official URL is tried first; when it fails, the Mobility Database stored copy is used and
  the manifest says so.
- Green Bay has no current feed that scripts can fetch: it is recorded, not downloaded, and treated as
  having no frequent routes.
- Amtrak is excluded (AQ-047 item 10); the Amtrak Stations layer is not fetched.
"""
from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import sys
import time
import urllib.parse
import urllib.request
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from missing_middleware.paths import RAW  # noqa: E402

D = RAW / "tod_transit"
NTM_BASE = "https://services.arcgis.com/xOi1kZaI0eWDREZv/arcgis/rest/services"
NTM_LAYERS = {
    "agencies": "NTAD_National_Transit_Map_Agencies",
    "stops": "NTAD_National_Transit_Map_Stops",
    "routes": "NTAD_National_Transit_Map_Routes",
}
NTM_LICENCE = "CC BY 3.0 US (stops layer statement); agency table lists Wisconsin agencies as Public Domain. Source: U.S. DOT Bureau of Transportation Statistics, National Transit Map (NTAD)"
UA = {"User-Agent": "missing-middleware research (housing policy model)"}

# Official GTFS feeds used for route frequency, keyed by NTD id. Source: docs/tod/research/WI_TRANSIT_DATA.md.
# Madison (50005) is deliberately absent. Each entry: label, url, terms note, optional fallback.
GTFS_FEEDS: dict[str, dict] = {
    "50008": {"label": "mcts", "agency": "Milwaukee County Transit System",
              "url": "https://kamino.mcts.org/gtfs/google_transit.zip",
              "fallback": "https://files.mobilitydatabase.org/mdb-2127/latest.zip",
              "fallback_note": "Mobility Database stored copy (mdb-2127) of the official MCTS feed; agency terms still apply",
              "terms": "MCTS Developer Terms (ridemcts.com/policies/developer-terms): not sponsored by MCTS; show feed last-updated and valid-through dates; no MCTS logos"},
    "55312": {"label": "hop", "agency": "The Hop streetcar (City of Milwaukee)",
              "url": "https://thehopmke.transloc.com/Secure/Admin/Reports/GTFSDownload.aspx", "terms": "None stated (public record, D1)"},
    "50001": {"label": "valley", "agency": "Valley Transit (Appleton)", "url": "https://ridemyvalleytransit.com/gtfs", "terms": "None stated (public record, D1)"},
    "50003": {"label": "kenosha", "agency": "Kenosha Area Transit", "url": "https://kenoshatransit.com/gtfs", "terms": "None stated (public record, D1)"},
    "50006": {"label": "racine", "agency": "RYDE Racine", "url": "https://racine.connexionz.net/rtt/public/utility/gtfs.aspx", "terms": "None stated (public record, D1)"},
    "50096": {"label": "waukesha", "agency": "Waukesha Metro Transit", "url": "https://mywaukeshametro.com/gtfs", "terms": "None stated (public record, D1)"},
    "50004": {"label": "lacrosse", "agency": "La Crosse MTU", "url": "https://ridemtu.com/gtfs", "terms": "None stated (public record, D1)"},
    "50099": {"label": "eauclaire", "agency": "Eau Claire Transit", "url": "https://gtfs.ect.cadavl.com/ECT/GTFS/GTFS_ECT.zip", "terms": "None stated (public record, D1)"},
    "50009": {"label": "oshkosh", "agency": "GO Transit (Oshkosh)", "url": "https://data.trilliumtransit.com/gtfs/oshkosh-wi-us/oshkosh-wi-us.zip", "terms": "None stated by agency"},
    "50088": {"label": "sheboygan", "agency": "Shoreline Metro (Sheboygan)", "url": "https://data.trilliumtransit.com/gtfs/sheboygan-wi-us/sheboygan-wi-us.zip", "terms": "None stated by agency"},
    "50091": {"label": "wausau", "agency": "Metro Ride (Wausau)", "url": "https://data.trilliumtransit.com/gtfs/wausau-wi-us/wausau-wi-us.zip", "terms": "None stated by agency"},
    "50108": {"label": "janesville", "agency": "Janesville Transit System", "url": "https://data.trilliumtransit.com/gtfs/jts-wi-us/jts-wi-us.zip", "terms": "None stated by agency"},
    "50109": {"label": "beloit", "agency": "Beloit Transit System", "url": "https://passio3.com/beloit/passioTransit/gtfs/google_transit.zip", "terms": "None stated (public record, D1)"},
    "50171": {"label": "fonddulac", "agency": "Fond du Lac Area Transit", "url": "http://www.fonddulac.ridesystems.net/Secure/Admin/Reports/GTFSDownload.aspx", "terms": "None stated (public record, D1)"},
    "50359": {"label": "stevenspoint", "agency": "Stevens Point Transit", "url": "https://passio3.com/centraltrans/passioTransit/gtfs/google_transit.zip", "terms": "None stated (public record, D1)"},
    "50442": {"label": "lacrossecounty", "agency": "La Crosse County (SMRT)", "url": "https://rapid.nationalrtap.org/GTFSFileManagement/UserUploadFiles/13162/SMRTfeedfinal2026.zip", "terms": "None stated (public record, D1); National RTAP upload URL changes with each new file"},
}

# Agencies in the NTM whose frequency is not taken from a GTFS file, and why.
NO_GTFS = {
    "50005": "NTM route_desc (Madison Metro's own GTFS file is not used, AQ-045)",
    "50002": "none: Green Bay has no current feed that scripts can fetch (HTTP 403, file name changes); no route counted as frequent",
    "50461": "none: Manitowoc feed gives implausible frequencies (WI_TRANSIT_DATA.md section 4); not used, no route counted as frequent",
}
DEFAULT_NO_GTFS = "none: no official feed used (small system with no frequent service in the research pass)"


def _open(url: str, timeout: int):
    return urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=timeout)


def _record(data: bytes, url: str, extra: dict | None = None) -> dict:
    rec = {"url": url, "accessed_utc": dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
           "bytes": len(data), "sha256": hashlib.sha256(data).hexdigest()}
    rec.update(extra or {})
    return rec


def ntm_query(layer: str, where: str, geojson: bool = False, page: int = 2000, retries: int = 3) -> tuple[list, list[str]]:
    """All features of an NTM layer matching `where` (paged). Returns (features, request URLs)."""
    feats, urls, off = [], [], 0
    while True:
        p = dict(where=where, outFields="*", returnGeometry=str(geojson).lower(), outSR=4326,
                 f="geojson" if geojson else "json", resultOffset=off, resultRecordCount=page, orderByFields="OBJECTID")
        url = f"{NTM_BASE}/{layer}/FeatureServer/0/query?" + urllib.parse.urlencode(p)
        for attempt in range(retries):
            try:
                with _open(url, 180) as r:
                    d = json.load(r)
                break
            except Exception:
                if attempt == retries - 1:
                    raise
                time.sleep(5 * (attempt + 1))
        if "error" in d:
            raise RuntimeError(f"{layer}: {d['error']}")
        f = d.get("features", [])
        feats += f
        urls.append(url)
        more = d.get("exceededTransferLimit") or d.get("properties", {}).get("exceededTransferLimit")
        if len(f) < page and not more:
            break
        off += len(f)
    return feats, urls


def fetch_ntm(manifest: dict) -> None:
    out = D / "ntm"
    out.mkdir(parents=True, exist_ok=True)
    ag, ag_urls = ntm_query(NTM_LAYERS["agencies"], "State='WI'")
    ids = sorted({a["attributes"].get(k) for a in ag for k in ("NTD_ID", "NTAD_NTD_ID") if a["attributes"].get(k)})
    where = "ntd_id IN (" + ",".join(f"'{i}'" for i in ids) + ")"
    stops, st_urls = ntm_query(NTM_LAYERS["stops"], where)
    routes, rt_urls = ntm_query(NTM_LAYERS["routes"], where, geojson=True, page=500)
    files = {
        "agencies.json": (json.dumps([a["attributes"] for a in ag], indent=1).encode(), ag_urls[0]),
        "stops.json": (json.dumps([s["attributes"] for s in stops]).encode(), st_urls[0]),
        "routes.geojson": (json.dumps({"type": "FeatureCollection", "features": routes}).encode(), rt_urls[0]),
    }
    for name, (data, url) in files.items():
        (out / name).write_bytes(data)
        manifest["files"][f"ntm/{name}"] = _record(data, url, {"licence": NTM_LICENCE, "pages": {"agencies.json": len(ag_urls), "stops.json": len(st_urls), "routes.geojson": len(rt_urls)}[name],
                                                               "note": "first page URL shown; later pages add resultOffset"})
    dl = sorted({s["attributes"].get("download_date") for s in stops if s["attributes"].get("download_date")})
    manifest["ntm"] = {"agencies": len(ag), "ntd_ids": ids, "stops": len(stops), "route_shapes": len(routes), "download_dates": dl}
    print(f"NTM: {len(ag)} agencies, {len(stops)} stops, {len(routes)} route shapes (compiled {', '.join(dl)})")


def _download(url: str, retries: int = 2, timeout: int = 90) -> tuple[bytes, str]:
    """GTFS zip bytes and the Last-Modified header; retries once on failure."""
    for attempt in range(retries):
        try:
            with _open(url, timeout) as r:
                data, lm = r.read(), r.headers.get("Last-Modified", "")
            if not data.startswith(b"PK"):
                raise ValueError("response is not a zip file")
            return data, lm
        except Exception:
            if attempt == retries - 1:
                raise
            time.sleep(10)
    raise AssertionError("unreachable")


def fetch_gtfs(manifest: dict, only: set[str] | None = None) -> None:
    out = D / "gtfs"
    out.mkdir(parents=True, exist_ok=True)
    for nid, f in GTFS_FEEDS.items():
        if only and nid not in only:
            continue
        name = f"gtfs/{nid}_{f['label']}.zip"
        rec = None
        tried = []
        for kind, url in (("official", f["url"]), ("fallback", f.get("fallback"))):
            if not url:
                continue
            try:
                data, lm = _download(url)
                rec = _record(data, url, {"ntd_id": nid, "agency": f["agency"], "source_kind": kind, "last_modified": lm,
                                          "terms": f["terms"], "note": f.get("fallback_note", "") if kind == "fallback" else ""})
                (D / name).write_bytes(data)
                break
            except Exception as e:  # noqa: BLE001 - record and try the fallback
                tried.append({"url": url, "error": f"{type(e).__name__}: {e}"[:300]})
        if rec is None:
            print(f"GTFS {nid} {f['label']}: FAILED {tried}")
            manifest["files"].pop(name, None)
            manifest.setdefault("failed", {})[nid] = tried
            continue
        if tried:
            rec["failed_attempts"] = tried
        manifest["files"][name] = rec
        manifest.get("failed", {}).pop(nid, None)
        print(f"GTFS {nid} {f['label']}: {rec['source_kind']} {rec['bytes']:,} bytes")


def main(argv=None) -> None:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--only", choices=["ntm", "gtfs"])
    ap.add_argument("--feed", nargs="*", help="NTD ids of GTFS feeds to (re)fetch")
    a = ap.parse_args(argv)
    D.mkdir(parents=True, exist_ok=True)
    mpath = D / "manifest.json"
    manifest = json.loads(mpath.read_text()) if mpath.exists() else {}
    manifest.update({"source_id": "tod_transit",
                     "publisher": "BTS National Transit Map (NTAD) and Wisconsin transit agencies' official GTFS feeds",
                     "purpose": "TOD major-transit-stop layer and homes near stops (scripts/build_tod_stops.py)",
                     "not_downloaded": {"50005": "Madison Metro GTFS: not used pending the licence question (AQ-045)",
                                        "50002": "Green Bay: no script-fetchable current feed",
                                        "amtrak": "Amtrak excluded (AQ-047 item 10)"}})
    manifest.setdefault("files", {})
    if a.only in (None, "ntm"):
        fetch_ntm(manifest)
    if a.only in (None, "gtfs"):
        fetch_gtfs(manifest, set(a.feed) if a.feed else None)
    if not manifest.get("failed"):
        manifest.pop("failed", None)
    mpath.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n")
    print("wrote", mpath)


if __name__ == "__main__":
    main()
