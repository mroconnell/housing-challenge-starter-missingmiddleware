"""Madison, WI adapter: Building Inspection "Construction Summary" report + City GIS.

Acquisition is plain HTTP (stdlib urllib):

* Permits: the SSRS ReportViewer page is an ASP.NET WebForms page. One GET
  gives the form state (__VIEWSTATE etc.); one POST with Start Date, End Date
  and Permit Type=ALL renders the report server-side and returns an
  ``ExportUrlBase``; a GET of that URL + ``CSV`` returns the report as CSV.
  Each year is a fresh session, so session expiry does not matter.
* Parcels and address points: ArcGIS REST query endpoints, paged.

Owner name / owner mailing address columns exist in the raw permit CSV. They
stay in data/raw only and are dropped by `load_raw_permits`, the single entry
point every later stage uses.
"""
from __future__ import annotations

import csv
import html
import io
import json
import re
import urllib.parse
from datetime import date
from pathlib import Path

import pandas as pd

from . import fetch_util as fu
from .base import CityAdapter, STANDARD_COLUMNS

SOURCE_ID = "madison_permits"
PARCEL_SOURCE_ID = "madison_parcels"
JURISDICTION_ID = "5502548000"  # wi_muni_id: county subdivision GEOID 55-025-48000 (Madison city)
JURISDICTION_NAME = "Madison city, WI"

REPORT_URL = (
    "https://cityreports.cityofmadison.com/CityReports/ReportViewer/ReportViewer/"
    "?ReportPath=/Web%20Access/Building/Permits/Construction%20Summary"
)
PARCELS_URL = "https://maps.cityofmadison.com/arcgis/rest/services/Public/OPEN_DATA2/FeatureServer/0"
ADDRPTS_URL = "https://maps.cityofmadison.com/arcgis/rest/services/Public/OPEN_DATA/MapServer/20"

PERMIT_ID_RE = re.compile(r"^BLD[A-Z]{3}-\d{4}-\d+$")
OWNER_COLUMNS = ("Owner_Full_Name", "Owner_Address_Line")
RAW_COLUMNS = (
    "B1_ALT_ID", "Reportable_Data", "Address_Part_Address_Line", "BLDG_SQFT", "Textbox9",
    "Total_Pay", "Textbox13", "Owner_Full_Name", "Owner_Address_Line", "Detailed_Description",
    "Issuance_Date", "ContractorBusiness", "ContractorAddress_Line",
)
# Columns kept from the raw file after ingestion (owner and contractor fields dropped).
KEEP_RAW = {
    "B1_ALT_ID": "permit_id",
    "Reportable_Data": "use_class",
    "Address_Part_Address_Line": "address_raw",
    "BLDG_SQFT": "bldg_sqft",
    "Textbox9": "est_cost",
    "Textbox13": "units_raw",
    "Detailed_Description": "description",
    "Issuance_Date": "issue_date",
}

PARCEL_FIELDS = (
    "OBJECTID,Parcel,XRefParcel,Address,HouseNbr,StreetDir,StreetName,StreetType,Unit,"
    "PropertyClass,PropertyUse,PropertyUseCode,TotalDwellingUnits,YearBuilt,MaxConstructionYear,"
    "MoreThanOneBuild,ZoningAll,Zoning1,LotSize,DateAdded,ParcelChangeDate,XCoord,YCoord"
)
ADDRPT_FIELDS = "OBJECTID,HouseNbr,StreetDir,StreetName,StreetType,Unit,Address,ZipCode,Parcel,DateAdded"


# --------------------------------------------------------------------------- permits
def _form_fields(page: str) -> dict[str, str]:
    out: dict[str, str] = {}
    for m in re.finditer(r"<input[^>]*>", page):
        tag = m.group(0)
        name = re.search(r'name="([^"]*)"', tag)
        typ = re.search(r'type="([^"]*)"', tag)
        if not name or not typ or typ.group(1) not in ("hidden", "text"):
            continue
        val = re.search(r'value="([^"]*)"', tag)
        out[html.unescape(name.group(1))] = html.unescape(val.group(1)) if val else ""
    return out


def fetch_report_csv(start: date, end: date, permit_type: str = "ALL") -> bytes:
    """Run the Construction Summary report for [start, end] and return the CSV bytes."""
    op = fu.opener(cookies=True)
    page = fu.get(REPORT_URL, op=op, timeout=120).decode("utf-8", "replace")
    form = _form_fields(page)
    p = "ctl00$MainContent$rvSiteMapping$ctl08$"
    form[p + "ctl03$txtValue"] = f"{start.month}/{start.day}/{start.year}"
    form[p + "ctl05$txtValue"] = f"{end.month}/{end.day}/{end.year}"
    form[p + "ctl07$ddValue"] = permit_type
    form[p + "ctl00"] = "View Report"
    form["__EVENTTARGET"] = ""
    form["__EVENTARGUMENT"] = ""
    action = re.search(r'<form method="post" action="([^"]*)"', page).group(1)
    post_url = urllib.parse.urljoin(REPORT_URL, html.unescape(action))
    resp = fu.get(post_url, op=op, data=urllib.parse.urlencode(form).encode(), timeout=900, tries=1)
    resp = resp.decode("utf-8", "replace")
    m = re.search(r'ExportUrlBase":"([^"]*)"', resp)
    if not m:
        raise RuntimeError("report did not render (no ExportUrlBase in response)")
    export = m.group(1).encode().decode("unicode_escape")
    data = fu.get(urllib.parse.urljoin(REPORT_URL, export) + "CSV", op=op, timeout=900, tries=1)
    if not data.lstrip(b"\xef\xbb\xbf").startswith(b"B1_ALT_ID"):
        raise RuntimeError("export did not return the expected CSV header")
    return data


def count_detail_rows(data: bytes) -> int:
    text = data.decode("utf-8-sig", "replace")
    return sum(1 for row in csv.reader(io.StringIO(text)) if row and PERMIT_ID_RE.match(row[0].strip()))


def fetch_permits(raw_dir: Path, years: list[int], today: date | None = None,
                  refresh: bool = False, log=print) -> dict:
    """Download one CSV per issue year into raw_dir and (re)write manifest.json."""
    today = today or date.today()
    raw_dir.mkdir(parents=True, exist_ok=True)
    man_path = raw_dir / "manifest.json"
    manifest = fu.read_manifest(man_path)
    entries = {e["year"]: e for e in manifest.get("files", [])}
    for year in years:
        path = raw_dir / f"construction_summary_{year}.csv"
        current_year = year == today.year
        if path.exists() and not refresh and not current_year and year in entries:
            log(f"{year}: cached ({entries[year]['detail_rows']} rows)")
            continue
        end = min(date(year, 12, 31), today)
        log(f"{year}: requesting {date(year, 1, 1)}..{end}")
        try:
            data = fetch_report_csv(date(year, 1, 1), end)
        except Exception as exc:  # big years: fall back to half-years and concatenate
            log(f"{year}: full-year request failed ({exc}); retrying by half-year")
            parts = []
            for a, b in ((date(year, 1, 1), date(year, 6, 30)), (date(year, 7, 1), end)):
                if a > end:
                    continue
                parts.append(fetch_report_csv(a, min(b, end)))
            data = _concat_csvs(parts)
        path.write_bytes(data)
        entries[year] = {
            "year": year,
            "file": path.name,
            "request": {"start": f"{year}-01-01", "end": end.isoformat(), "permit_type": "ALL"},
            "accessed": fu.now_iso(),
            "bytes": len(data),
            "detail_rows": count_detail_rows(data),
            "sha256": fu.sha256_file(path),
        }
        log(f"{year}: {entries[year]['detail_rows']} detail rows")
    fu.write_manifest(man_path, [entries[y] for y in sorted(entries)], {
        "source_id": SOURCE_ID,
        "url": REPORT_URL,
        "publisher": "City of Madison Building Inspection (SSRS report 'Construction Summary')",
        "license": "No open-data license stated; public-records report on the City website. "
                   "Raw file includes owner names/addresses: keep local, never redistribute.",
        "method": "scripts/build_madison_permits.py --fetch (HTTP GET form, POST View Report, GET export CSV)",
    })
    return fu.read_manifest(man_path)


def _concat_csvs(parts: list[bytes]) -> bytes:
    """Concatenate report CSVs keeping one header and only detail rows."""
    out = io.StringIO()
    w = csv.writer(out, lineterminator="\r\n")
    w.writerow(RAW_COLUMNS)
    for data in parts:
        for row in csv.reader(io.StringIO(data.decode("utf-8-sig", "replace"))):
            if row and PERMIT_ID_RE.match(row[0].strip()):
                w.writerow(row)
    return out.getvalue().encode("utf-8")


def read_report_csv(path: Path) -> pd.DataFrame:
    """Detail rows of one raw report CSV, all raw columns as strings (owner fields included)."""
    text = path.read_text(encoding="utf-8-sig", errors="replace")
    rows = list(csv.reader(io.StringIO(text)))
    header = rows[0]
    if tuple(header[: len(RAW_COLUMNS)]) != RAW_COLUMNS:
        raise ValueError(f"{path.name}: unexpected header {header}")
    detail = [r for r in rows[1:] if r and PERMIT_ID_RE.match(r[0].strip())]
    detail = [r[: len(RAW_COLUMNS)] + [""] * (len(RAW_COLUMNS) - len(r)) for r in detail]
    return pd.DataFrame(detail, columns=list(RAW_COLUMNS))


def _num(s: pd.Series) -> pd.Series:
    return pd.to_numeric(s.str.replace(r"[$,\s]", "", regex=True).replace("", None), errors="coerce")


def load_raw_permits(raw_dir: Path) -> pd.DataFrame:
    """All cached years as the adapter's standard frame. Owner fields are dropped here."""
    frames = []
    for path in sorted(raw_dir.glob("construction_summary_*.csv")):
        df = read_report_csv(path)
        df = df.drop(columns=list(OWNER_COLUMNS) + ["ContractorBusiness", "ContractorAddress_Line", "Total_Pay"])
        df["source_file"] = path.name
        df["source_row"] = range(len(df))
        frames.append(df)
    if not frames:
        raise FileNotFoundError(f"no construction_summary_*.csv in {raw_dir}; run with --fetch")
    df = pd.concat(frames, ignore_index=True).rename(columns=KEEP_RAW)
    for c in ("permit_id", "use_class", "address_raw", "description"):
        df[c] = df[c].fillna("").str.strip()
    df["issue_date"] = pd.to_datetime(df["issue_date"], format="%m/%d/%Y", errors="coerce")
    df["units_raw"] = _num(df["units_raw"])
    df["est_cost"] = _num(df["est_cost"])
    df["bldg_sqft"] = _num(df["bldg_sqft"])
    df["permit_type"] = df["permit_id"].str[:6]
    df["jurisdiction_id"] = JURISDICTION_ID
    df["source_id"] = SOURCE_ID
    return df[list(STANDARD_COLUMNS) + ["source_file", "source_row"]]


# --------------------------------------------------------------------------- GIS layers
def _arcgis_pages(layer_url: str, out_fields: str, page: int = 2000, log=print) -> list[dict]:
    ids = json.loads(fu.get(layer_url + "/query", {"where": "1=1", "returnIdsOnly": "true", "f": "json"}))
    oids = sorted(ids["objectIds"])
    feats: list[dict] = []
    for i in range(0, len(oids), page):
        chunk = oids[i:i + page]
        body = urllib.parse.urlencode({
            "where": f"OBJECTID>={chunk[0]} AND OBJECTID<={chunk[-1]}",
            "outFields": out_fields, "returnGeometry": "true", "outSR": "4326",
            "geometryPrecision": "7", "f": "geojson",
        }).encode()
        data = json.loads(fu.get(layer_url + "/query", data=body, timeout=300))
        feats.extend(data["features"])
        if (i // page) % 10 == 0:
            log(f"  {layer_url.rsplit('/', 3)[-3]}: {len(feats)}/{len(oids)}")
    return feats


def fetch_gis(raw_parcels_dir: Path, log=print) -> dict:
    """Download Tax Parcels (polygons) and Address Points to raw_parcels_dir as GeoJSON."""
    raw_parcels_dir.mkdir(parents=True, exist_ok=True)
    entries = []
    for name, url, fields in (
        ("tax_parcels.geojson", PARCELS_URL, PARCEL_FIELDS),
        ("address_points.geojson", ADDRPTS_URL, ADDRPT_FIELDS),
    ):
        feats = _arcgis_pages(url, fields, log=log)
        path = raw_parcels_dir / name
        path.write_text(json.dumps({"type": "FeatureCollection", "features": feats}))
        entries.append({"file": name, "url": url, "fields": fields, "features": len(feats),
                        "accessed": fu.now_iso(), "sha256": fu.sha256_file(path)})
        log(f"{name}: {len(feats)} features")
    fu.write_manifest(raw_parcels_dir / "manifest.json", entries, {
        "source_id": PARCEL_SOURCE_ID,
        "publisher": "City of Madison (ArcGIS REST, Public/OPEN_DATA2 and OPEN_DATA)",
        "license": "Not stated on the service; public City GIS.",
        "note": "Owner fields not requested. Geometry requested in EPSG:4326. Layer is current (not historical).",
    })
    return fu.read_manifest(raw_parcels_dir / "manifest.json")


def load_parcels(raw_parcels_dir: Path):
    import geopandas as gpd

    gdf = gpd.read_file(raw_parcels_dir / "tax_parcels.geojson")
    return gdf.set_crs(4326, allow_override=True)


def load_address_points(raw_parcels_dir: Path):
    import geopandas as gpd

    gdf = gpd.read_file(raw_parcels_dir / "address_points.geojson")
    return gdf.set_crs(4326, allow_override=True)


class MadisonAdapter(CityAdapter):
    source_id = SOURCE_ID
    parcel_source_id = PARCEL_SOURCE_ID
    jurisdiction_id = JURISDICTION_ID
    jurisdiction_name = JURISDICTION_NAME
    state_fips = "55"
    county_fips = ("025",)
    new_residential_types = ("BLDNRC", "BLDNCC")
    # assessor property uses that can host an ADU-equivalent (one- to three-unit homes)
    host_uses = ("Single family", "2 Unit", "3 Unit")

    def load_permits(self, raw_dir: Path) -> pd.DataFrame:
        return load_raw_permits(raw_dir)


# --------------------------------------------------------------------------- reference tables
def parcel_table(parcels) -> pd.DataFrame:
    """Standard parcel table (PARCEL_COLUMNS) plus representative-point lon/lat."""
    from .address import street_key_from_parts

    g = parcels
    rp = g.geometry.representative_point()
    out = pd.DataFrame({
        "parcel_id": g["Parcel"].astype(str),
        "xref_parcel": g["XRefParcel"].astype(str),
        "parcel_address": g["Address"],
        "house_nbr": pd.to_numeric(g["HouseNbr"], errors="coerce"),
        "street_key": [street_key_from_parts(d, n, t) for d, n, t in
                       zip(g["StreetDir"], g["StreetName"], g["StreetType"])],
        "unit": g["Unit"].fillna(""),
        "dwelling_units": pd.to_numeric(g["TotalDwellingUnits"], errors="coerce"),
        "property_class": g["PropertyClass"],
        "property_use": g["PropertyUse"],
        "zoning": g["ZoningAll"],
        "year_built": pd.to_numeric(g["YearBuilt"], errors="coerce"),
        "more_than_one_building": g["MoreThanOneBuild"],
        "x": rp.x.values, "y": rp.y.values,
    })
    # a parcel id can repeat only if the layer has multipart duplicates; keep first
    return out.drop_duplicates("parcel_id").reset_index(drop=True)


def address_reference(parcels_tbl: pd.DataFrame, addr_points) -> pd.DataFrame:
    """Union of address points (address -> parcel) and parcel situs addresses."""
    from .address import street_key_from_parts

    a = addr_points
    pts = pd.DataFrame({
        "house_nbr": pd.to_numeric(a["HouseNbr"], errors="coerce"),
        "street_key": [street_key_from_parts(d, n, t) for d, n, t in
                       zip(a["StreetDir"], a["StreetName"], a["StreetType"])],
        "unit": a["Unit"].fillna(""),
        "parcel_id": a["Parcel"].astype(str).where(a["Parcel"].notna()),
        "address_full": a["Address"],
        "x": a.geometry.x.values, "y": a.geometry.y.values,
        "ref_source": "address_point",
    })
    known = set(parcels_tbl["parcel_id"])
    # condo unit points may carry a unit parcel that is absent from the tax layer; keep only known parcels
    pts = pts[pts["parcel_id"].isin(known)]
    par = parcels_tbl.rename(columns={"parcel_address": "address_full"})[
        ["house_nbr", "street_key", "unit", "parcel_id", "address_full", "x", "y"]].assign(ref_source="parcel")
    return pd.concat([pts, par], ignore_index=True)
