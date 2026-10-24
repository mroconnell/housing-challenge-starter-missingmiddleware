#!/usr/bin/env python3
"""Write docs/data-sources/ from scripts/source_catalog.py and data/sample/.

Run after scripts/fetch_samples.py:
  python3 scripts/build_data_dictionaries.py
"""
from __future__ import annotations

import csv
import re
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from source_catalog import CATALOG, HANDBOOK  # noqa: E402

SAMPLES = ROOT / "data" / "sample"
DOCS = ROOT / "docs" / "data-sources"
SHOW_ROWS = 3
CELL = 60

STATUS = {
    "ok": "Fetched",
    "no_rows": "Reached, no rows",
    "restricted": "Restricted (not fetched)",
    "request_form": "Manual request only (not fetched)",
    "error": "Could not reach",
    None: "Not run yet",
}
GROUPS = {
    "national": "National sources named in the handbook",
    "added": "Added by the team",
    "state": "State open data portals (from data/DATA_SOURCES.md)",
    "wisconsin": "Wisconsin pilot sources (used by the pipeline)",
}


def esc(v, n=CELL):
    s = "" if v is None else str(v)
    s = s.replace("|", "\\|").replace("\n", " ").strip()
    return s if len(s) <= n else s[: n - 1] + "…"


def load(sid):
    meta_p, csv_p = SAMPLES / f"{sid}.meta.json", SAMPLES / f"{sid}.csv"
    meta = json.loads(meta_p.read_text()) if meta_p.exists() else {}
    rows = list(csv.DictReader(csv_p.open(encoding="utf-8"))) if csv_p.exists() else []
    return meta, rows


def access_url(meta):
    for k in ("api_url", "service_url", "page_url", "master_url", "index_url", "sample_file", "wms_url", "search_url"):
        if meta.get(k):
            return meta[k]
    for v in meta.values():
        if isinstance(v, dict) and v.get("url"):
            return v["url"]
    return ""


HCD_INCOME = {
    "ACUTELY_LOW": "acutely low income",
    "EXTREMELY_LOW": "extremely low income",
    "VLOW": "very low income",
    "LOW": "low income",
    "MOD": "moderate income",
    "ABOVE_MOD": "above moderate income",
}


def hcd_meaning(name):
    """Spell out APR Table A2 unit-count columns from their naming pattern."""
    m = re.match(r"^(BP_|CO_)?(ACUTELY_LOW|EXTREMELY_LOW|VLOW|LOW|MOD|ABOVE_MOD)_INCOME(_DR|_NDR)?$", name)
    if not m:
        return ""
    stage = {"BP_": "Units issued building permits", "CO_": "Units completed (certificate of occupancy)"}.get(m.group(1) or "", "Units entitled")
    dr = {"_DR": ", deed restricted", "_NDR": ", not deed restricted"}.get(m.group(3) or "", "")
    return f"{stage}: {HCD_INCOME[m.group(2)]}{dr}."


def pattern_meaning(sid, name):
    """Meanings for columns that follow a naming pattern."""
    if sid == "hcd_apr":
        return hcd_meaning(name)
    if sid == "bls_qcew":
        if name.startswith("lq_"):
            return f"Location quotient for {name[3:]}: local share of this industry divided by the national share (1.0 = same as nation)."
        if name.startswith("oty_"):
            kind = "percent change" if name.endswith("_pct_chg") else "change"
            return f"Over-the-year {kind} in {re.sub(r'_(pct_)?chg$', '', name[4:])} from the prior year."
    if sid == "census_bps":
        m = re.match(r"^(1-unit|2-units|3-4 units|5\+ ?units)( rep)? (Bldgs|Units|Value)$", name)
        if m:
            what = {"Bldgs": "Buildings", "Units": "Housing units", "Value": "Construction value in thousands of dollars"}[m.group(3)]
            size = m.group(1).replace("5+units", "5+ units")
            rep = " Reported only (no imputation for non-reporting places)." if m.group(2) else " Includes Census imputation for non-reporting places."
            return f"{what} permitted in {size} buildings.{rep}"
    return ""


def field_rows(sid, info, meta, rows):
    notes = info.get("fields", {})
    fields = meta.get("fields") or []
    if sid == "hcd_apr" and meta.get("sample_table"):
        fields = meta["tables"][meta["sample_table"]]["fields"]

    if sid == "nasa_modis_lc" or not fields:
        fields = [{"name": c} for c in (rows[0].keys() if rows else notes.keys())]
    out = []
    for f in fields:
        name = f.get("name")
        meaning = notes.get(name) or pattern_meaning(sid, name) or f.get("description") or f.get("alias") or ""
        if meaning == name:
            meaning = ""
        extra = f.get("concept")
        if extra and extra not in meaning:
            meaning = f"{meaning} ({extra})" if meaning else extra
        out.append((name, f.get("type") or "", meaning))
    return out


def sample_table(rows, limit=SHOW_ROWS):
    if not rows:
        return "_No sample rows._\n"
    rows = rows[:limit]
    head = "| Field | " + " | ".join(f"Row {i + 1}" for i in range(len(rows))) + " |\n"
    head += "|---|" + "---|" * len(rows) + "\n"
    keys = [k for k in rows[0].keys() if any(str(r.get(k) or "").strip() for r in rows)]
    body = "".join(
        f"| `{esc(k, 40)}` | " + " | ".join(esc(r.get(k)) for r in rows) + " |\n" for k in keys
    )
    return head + body


def extras(sid, meta):
    """Source-specific sections."""
    md = ""
    if sid == "hcd_apr" and meta.get("tables"):
        md += "## Tables in this dataset\n\n| Table | Records | Fields |\n|---|---|---|\n"
        for name, t in meta["tables"].items():
            fl = ", ".join(f"`{f['name']}`" for f in t.get("fields", []) if f["name"] != "_id")
            md += f"| {name} | {t.get('record_count', '')} | {esc(fl, 400)} |\n"
        md += "\nHCD publishes a data dictionary (DOCX) for each table on the dataset page.\n\n"
    if sid == "ntd" and meta.get("stations_dataset"):
        st = meta["stations_dataset"]
        md += f"## Related NTD table: {st.get('name')}\n\n"
        md += f"Station and facility counts by agency and mode, useful for the transit scenario. API: `{st.get('api_url')}`.\n\n"
        md += "| Field | Type | Meaning |\n|---|---|---|\n"
        for f in st.get("fields", []):
            md += f"| `{f['name']}` | {f.get('type') or ''} | {esc(f.get('description') or f.get('alias'), 160)} |\n"
        md += "\n"
    if sid == "census_bps":
        for geo, m in meta.items():
            if isinstance(m, dict) and m.get("url"):
                md += f"- {geo} file: `{m['url']}`\n"
        md += "\nThe raw file has two header rows. Our script joins them into one name, for example `1-unit` + `Units` = `1-unit Units`.\n\n"
    if sid == "fhfa_hpi" and meta.get("all_download_links_found"):
        md += "## Other FHFA HPI files found on the datasets page\n\n"
        md += "".join(f"- {u}\n" for u in meta["all_download_links_found"][:30]) + "\n"
    if sid == "acs" and meta.get("pipeline_tables"):
        md += "## Other ACS tables the pipeline reads\n\n| Table | Line | Meaning | Wisconsin estimate |\n|---|---|---|---|\n"
        from fetch_samples import ACS_TABLE_LINES
        for t, m in meta["pipeline_tables"].items():
            if m.get("error"):
                md += f"| {t} | | could not read: {esc(m['error'], 100)} | |\n"
                continue
            wi = m.get("wisconsin_row") or {}
            for line, label in ACS_TABLE_LINES.get(t, {}).items():
                md += f"| {t} | `{t}_E{line}` | {label} | {wi.get(f'{t}_E{line}', '')} |\n"
        md += "\nEach estimate column `_E###` has a margin of error column `_M###`.\n\n"
    if sid == "buildinganadu_ca_adu" and meta.get("statewide_sums"):
        md += f"## Statewide sums\n\nSum of {meta.get('jurisdiction_rows')} jurisdiction rows, by year. Compare with the table in docs/ASSUMPTIONS_AND_QUESTIONS.md (AQ-017).\n\n"
        md += "| Year | ADU permits |\n|---|---|\n" + "".join(f"| {y} | {v:,} |\n" for y, v in meta["statewide_sums"].items()) + "\n"
    if sid == "pa_pasda_parcels" and meta.get("counties"):
        md += "## Field comparison across counties\n\n"
        md += "| County | Layer | Parcels | Fields | Parcel id | Address | Land use | Value | Area |\n|---|---|---|---|---|---|---|---|---|\n"
        concepts = {
            "Parcel id": r"pin|parcel_?(id|num)|propid|upi|apn|map_?(no|num)|^pid|tax_?id|account",
            "Address": r"addr|situs|site|street|location",
            "Land use": r"use|luc|class|zon",
            "Value": r"val|assess|apr|mkt|market",
            "Area": r"acre|sqft|area",
        }
        for c, m in meta["counties"].items():
            if "field_names" not in m:
                md += f"| {c} | not sampled: {esc(m.get('error'), 120)} | | | | | | | |\n"
                continue
            names = [n for n in m["field_names"] if not re.match(r"(?i)shape|objectid|fid$", n)]
            cells = [esc(", ".join(f"`{n}`" for n in names if re.search(rx, n, re.I)), 160) or "none" for rx in concepts.values()]
            md += f"| {c} | {esc(m.get('layer_name'), 40)} | {m.get('record_count') or ''} | {len(m['field_names'])} | " + " | ".join(cells) + " |\n"
        md += "\nThe concept columns are a name match only. They show which fields probably hold that idea, not a checked crosswalk.\n\n"
    if meta.get("page_excerpt"):
        md += f"## What the source page says\n\n> {esc(meta['page_excerpt'], 1200)}\n\n"
    return md


def crs_label(c):
    if isinstance(c, dict):
        w = c.get("latestWkid") or c.get("wkid")
        if w and c.get("wkid") and c.get("wkid") != w:
            return f"EPSG:{w} (Esri {c['wkid']})"
        return f"EPSG:{w}" if w else "not stated"
    return str(c) if c else "not stated"


def geometry_section(sid, meta):
    g = meta.get("geometry_sample")
    if not g:
        if meta.get("geometry_sample_error"):
            return f"## Geometry sample\n\nCould not get geometry: {esc(meta['geometry_sample_error'], 300)}\n\n"
        return ""
    v = g.get("vertices_per_feature") or []
    md = "## Geometry sample\n\n"
    md += f"[`{g['file']}`](../../{g['file']}) has {g['features']} complete features (geometry and all attributes, owner fields redacted). "
    md += "Coordinates are converted to WGS84 longitude/latitude for GeoJSON. Open it in QGIS or geojson.io.\n\n"
    md += "| | |\n|---|---|\n"
    md += f"| Geometry type | {g.get('geometry_type')} |\n"
    md += f"| Source coordinate system | {crs_label(g.get('native_crs'))} |\n"
    md += f"| Vertices per feature in the sample | {', '.join(str(x) for x in v)} |\n"
    if g.get("max_record_count"):
        md += f"| Max features per request | {g['max_record_count']} |\n"
    if g.get("supports_pagination") is not None:
        md += f"| Paging supported | {'yes' if g['supports_pagination'] else 'no'} |\n"
    md += "\n"
    return md


def shape_table():
    """One row per source with a geometry sample."""
    out = []
    for sid, info in CATALOG.items():
        meta, _ = load(sid)
        g = meta.get("geometry_sample")
        if not g:
            continue
        v = g.get("vertices_per_feature") or [0]
        total = meta.get("record_count")
        if sid == "pa_pasda_parcels":
            total = sum((m.get("record_count") or 0) for m in meta.get("counties", {}).values()) or None
        paging = {True: "yes", False: "no"}.get(g.get("supports_pagination"), "")
        out.append(
            f"| [{info['title']}]({sid}.md) | {g.get('geometry_type')} | {esc(crs_label(g.get('native_crs')), 40)} | "
            f"{total if total is not None else ''} | {g.get('max_record_count') or ''} | {paging} | {round(sum(v) / len(v))} | "
            f"[geojson](../../{g['file']}) |"
        )
    if not out:
        return ""
    md = "## Data shape by source\n\n"
    md += "Each source below also has a small GeoJSON file with a few complete features, so you can see the real geometry before picking a state.\n\n"
    md += "| Source | Geometry | Source CRS | Records | Max per request | Paging | Avg vertices | Sample |\n|---|---|---|---|---|---|---|---|\n"
    return md + "\n".join(out) + "\n\n"


def write_source(sid, info, meta, rows):
    status = STATUS.get(meta.get("status"), meta.get("status"))
    url = access_url(meta)
    md = f"# {info['title']}\n\n"
    md += f"**Status:** {status}"
    if meta.get("fetched_at"):
        md += f" (last fetch {meta['fetched_at'][:10]})"
    md += f"  \n**Source id:** `{sid}`  \n"
    if info.get("handbook_item"):
        md += f"**Handbook listing:** {info['handbook_item']}\n"
    md += "\n"
    if meta.get("error"):
        md += f"> **Fetch error:** {esc(meta['error'], 600)}\n\n"
    md += "## Summary\n\n| | |\n|---|---|\n"
    for label, key in (
        ("Publisher", "publisher"),
        ("What it is", "what"),
        ("Geography", "geography"),
        ("Time coverage and update frequency", "time"),
        ("Units", "units"),
        ("Access method", "access"),
        ("License", "license"),
        ("Use in our model", "uses"),
        ("Caveats", "caveats"),
    ):
        if info.get(key):
            md += f"| {label} | {esc(info[key], 2000)} |\n"
    facts = []
    if url:
        facts.append(f"Endpoint used for the sample: `{url}`")
    for k, label in (("vintage", "Vintage"), ("name", "Dataset"), ("layer_name", "Layer"), ("layer", "Layer"), ("sample_table", "Sample table"), ("record_count", "Total records at fetch time"), ("last_edit_date", "Last edited"), ("rows_updated_at", "Rows last updated"), ("latest_date", "Latest date"), ("window", "Sample window"), ("records_in_window", "Permits in the window"), ("jurisdiction_rows", "Jurisdiction rows"), ("county_rows", "County rows"), ("title", "Table title"), ("projection", "Projection (.prj)")):
        if meta.get(k) not in (None, ""):
            facts.append(f"{label}: {meta[k]}")
    item = meta.get("item") or meta.get("chosen_search_hit")
    if item:
        facts.append(f"Item: {item.get('title')} (owner `{item.get('owner')}`, id `{item.get('id')}`)")
    if meta.get("sample_tile"):
        t = meta["sample_tile"]
        facts.append(f"Sample tile: quadkey {t.get('QuadKey')} ({t.get('Location')}), `{t.get('Url')}`")
    if meta.get("geometry_type"):
        facts.append(f"Geometry: {meta['geometry_type']}")
    if meta.get("note"):
        facts.append(meta["note"])
    if facts:
        md += "\n## Access details\n\n" + "".join(f"- {esc(f, 400)}\n" for f in facts) + "\n"
    fr = field_rows(sid, info, meta, rows)
    if fr:
        md += f"## Fields ({len(fr)})\n\n| Field | Type | Meaning |\n|---|---|---|\n"
        md += "".join(f"| `{n}` | {t} | {esc(m, 300)} |\n" for n, t, m in fr) + "\n"
        if any(not m for _, _, m in fr):
            md += "Blank meanings: the publisher gives no description. Check the source's own metadata page before relying on that field.\n\n"
    names = {n for n, _, _ in fr}
    patterns = {k: v for k, v in info.get("fields", {}).items() if k not in names and any(c in k for c in "*/.")}
    if patterns:
        md += "## Field groups\n\n| Fields | Meaning |\n|---|---|\n"
        md += "".join(f"| `{esc(k, 80)}` | {esc(v, 300)} |\n" for k, v in patterns.items()) + "\n"
    md += extras(sid, meta)
    md += geometry_section(sid, meta)
    if rows and sid == "pa_pasda_parcels":
        md += f"## Sample rows\n\nOne row from each county, out of {len(rows)} rows in [`data/sample/{sid}.csv`](../../data/sample/{sid}.csv). Fields that are blank in every shown row are hidden. Owner names and mailing addresses are replaced with `[redacted]`.\n\n"
    elif rows:
        md += f"## Sample rows\n\nFirst {min(len(rows), SHOW_ROWS)} of {len(rows)} rows in [`data/sample/{sid}.csv`](../../data/sample/{sid}.csv). Long values are cut short. Owner names and mailing addresses are replaced with `[redacted]`.\n\n"
    else:
        md += f"## Sample rows\n\nNone. See the status above. What we did find is in [`data/sample/{sid}.meta.json`](../../data/sample/{sid}.meta.json).\n\n"
    shown = rows
    if sid == "pa_pasda_parcels":
        # One row from each county, so the table shows how they differ.
        seen, shown = set(), []
        for r in rows:
            if r.get("pasda_county") not in seen:
                seen.add(r.get("pasda_county"))
                shown.append(r)
    md += sample_table(shown, limit=len(shown)) if rows else ""
    md += f"\n## Refresh\n\n```sh\npython3 scripts/fetch_samples.py {sid}\npython3 scripts/build_data_dictionaries.py\n```\n"
    (DOCS / f"{sid}.md").write_text(md)
    return status, url


def main():
    DOCS.mkdir(parents=True, exist_ok=True)
    lines = {g: [] for g in GROUPS}
    for sid, info in CATALOG.items():
        meta, rows = load(sid)
        status, _ = write_source(sid, info, meta, rows)
        done = "x" if meta.get("status") == "ok" else " "
        note = re.split(r"(?<!U\.S)\. ", info.get("caveats", ""))[0]
        lines[info["group"]].append(
            f"| [{done}] | [{info['title']}]({sid}.md) | {status} | {len(rows)} | {esc(info.get('geography'), 70)} | {esc(note, 110)} |"
        )
    md = "# Data source checklist\n\n"
    md += (
        f"This folder has one data dictionary per source. The sources come from the \"Data and Resources\" section of the [Challenge Handbook]({HANDBOOK}) "
        "and the state portal list in [data/DATA_SOURCES.md](../../data/DATA_SOURCES.md). "
        "Each page lists the fields, units, geography, update frequency, how to access the data, and a few sample rows.\n\n"
        "Sample rows live in [data/sample/](../../data/sample/). They are small on purpose. The handbook says not to commit large source data, "
        "so the full datasets must be downloaded by our pipeline.\n\n"
        "## What the samples leave out\n\n"
        "The samples are for learning the fields. They are not inputs for spatial work.\n\n"
        "- The CSVs hold attributes only, and every cell is cut to 200 characters. Building footprint polygons in the CSVs are incomplete.\n"
        "- For sources with geometry, a few complete features are saved separately in `data/sample/geo/` as GeoJSON. See the table below.\n"
        "- Each sample has a few rows, not the full layer. Full layers need paging (ArcGIS `resultOffset`, up to the layer's max record count).\n\n"
        "The modeling pipeline needs its own download step that keeps full geometry, gets every record, records the coordinate system, and checks joins. "
        "Asking for geometry does not add information a layer lacks: parcel points stay points, and building outlines do not give dwelling counts or zoning.\n\n"
        "## How to refresh\n\n"
        "```sh\npython3 scripts/fetch_samples.py          # all sources (standard library only)\n"
        "python3 scripts/build_data_dictionaries.py  # rewrite these pages\n```\n\n"
        "The **Fetch data samples** GitHub Actions workflow runs the same script and commits the results. "
        "Facts we wrote by hand (publisher, units, caveats) are in `scripts/source_catalog.py`.\n\n"
    )
    md += shape_table()
    for g, title in GROUPS.items():
        md += f"## {title}\n\n| Done | Source | Status | Sample rows | Geography | Main caveat |\n|---|---|---|---|---|---|\n"
        md += "\n".join(lines[g]) + "\n\n"
    (DOCS / "README.md").write_text(md)
    print(f"wrote {len(CATALOG)} source pages and README to {DOCS}")


if __name__ == "__main__":
    main()
