"""Sun Prairie, WI (city) adapter: public Power BI "All Submitted Permits Report".

The report is published to the web (Power BI US Government cloud) and linked
from https://cityofsunprairie.com/974/Construction-Reports. Its anonymous
`querydata` API answers semantic queries against the report's model; one
query per submission year returns every row (2016 onward; Munis records to
mid-2021, OpenGov after).

Only non-personal columns are requested: the model's `Owner Name` and
`Contractor` columns are never downloaded. Fields: record number, record type
(Munis code or OpenGov type), project description, Dane County 12-digit
parcel number, record status, street number and name, subdivision, date
submitted. There is no issue date and no dwelling-unit field: the permit stage
is `application` (submission), and units are calculated from type and text.
"""
from __future__ import annotations

import gzip
import json
import re
import time
import urllib.request
import uuid
from datetime import date, datetime, timezone
from pathlib import Path

import pandas as pd

from . import fetch_util as fu
from .base import STANDARD_COLUMNS, CityAdapter

SOURCE_ID = "sun_prairie_permits"
PARCEL_SOURCE_ID = "wi_v12_parcels_dane_sp"
JURISDICTION_ID = "5502578600"  # county subdivision GEOID 55-025-78600 (Sun Prairie city)
JURISDICTION_NAME = "Sun Prairie city, WI"
BPS_ID = "853000"

PAGE_URL = "https://cityofsunprairie.com/974/Construction-Reports"
RESOURCE_KEY = "fb5e5c09-4069-4ebf-a40e-b0aa51f5e741"
TENANT = "bb6c3b6e-9ea1-4cd1-b811-787fb6e43914"
VIEW_URL = ("https://app.powerbigov.us/view?r=eyJrIjoiZmI1ZTVjMDktNDA2OS00ZWJmLWE0MGUtYjBhYTUxZjVlNzQxIiwidCI6"
            "ImJiNmMzYjZlLTllYTEtNGNkMS1iODExLTc4N2ZiNmU0MzkxNCJ9&pageName=ReportSection")
# the "-redirect" host named in the embed page resets connections; the "-api" host answers
API_HOST = "https://wabi-us-gov-iowa-api.analysis.usgovcloudapi.net"
ENTITY = "PermitList"
COLUMNS = ["Record", "Record Type", "Project Description", "Parcel", "Record Status", "Street No",
           "Street Name", "Subdivision", "Date Submitted", "Year"]
NOT_REQUESTED = ("Owner Name", "Contractor")


# ---------------------------------------------------------------- download
def _post(path: str, body=None, timeout: int = 300):
    req = urllib.request.Request(
        API_HOST + path, data=json.dumps(body).encode() if body is not None else None,
        headers={"X-PowerBI-ResourceKey": RESOURCE_KEY, "ActivityId": str(uuid.uuid4()),
                 "RequestId": str(uuid.uuid4()), "Content-Type": "application/json;charset=UTF-8",
                 "Accept": "application/json", "Accept-Encoding": "gzip", "User-Agent": fu.USER_AGENT,
                 "Origin": "https://app.powerbigov.us", "Referer": "https://app.powerbigov.us/"})
    last = None
    for attempt in range(4):
        try:
            with urllib.request.urlopen(req, timeout=timeout) as r:
                b = r.read()
            if b[:2] == b"\x1f\x8b":
                b = gzip.decompress(b)
            return json.loads(b)
        except Exception as exc:  # network errors are retried, then re-raised
            last = exc
            time.sleep(3 * (attempt + 1))
    raise RuntimeError(f"Power BI request failed: {path}: {last}")


def model_info() -> dict:
    mae = _post(f"/public/reports/{RESOURCE_KEY}/modelsAndExploration?preferReadOnlySession=true")
    m = mae["models"][0]
    return {"model_id": m["id"], "db_name": m["dbName"], "display_name": m.get("displayName"),
            "last_refresh": m.get("lastRefreshTime"), "report_id": mae["exploration"].get("objectId", "")}


def _query_body(info: dict, year: int, restart=None, count: int = 30000) -> dict:
    src = {"SourceRef": {"Source": "p"}}
    sel = [{"Column": {"Expression": src, "Property": c}, "Name": f"{ENTITY}.{c}"} for c in COLUMNS]
    sel.append({"Aggregation": {"Expression": {"Column": {"Expression": src, "Property": "Record Ct"}}, "Function": 0},
                "Name": f"Sum({ENTITY}.Record Ct)"})
    where = [{"Condition": {"In": {"Expressions": [{"Column": {"Expression": src, "Property": "Year"}}],
                                   "Values": [[{"Literal": {"Value": f"{year}L"}}]]}}}]
    win = {"Count": count}
    if restart:
        win["RestartTokens"] = restart
    q = {"Version": 2, "From": [{"Name": "p", "Entity": ENTITY, "Type": 0}], "Select": sel, "Where": where}
    return {"version": "1.0.0", "queries": [{"Query": {"Commands": [{"SemanticQueryDataShapeCommand": {
        "Query": q, "Binding": {"Primary": {"Groupings": [{"Projections": list(range(len(sel)))}]},
                                "DataReduction": {"DataVolume": 3, "Primary": {"Window": win}}, "Version": 1},
        "ExecutionMetricsKind": 1}}]}, "QueryId": "",
        "ApplicationContext": {"DatasetId": info["db_name"], "Sources": [{"ReportId": info["report_id"], "VisualId": ""}]}}],
        "cancelQueries": [], "modelId": info["model_id"]}


def decode_dsr(ds: dict) -> list[list]:
    """Rows of a Power BI DSR data set (value dictionaries, repeat and null bitmasks)."""
    vd = ds.get("ValueDicts", {})
    rows = ds["PH"][0].get("DM0", [])
    if not rows:
        return []
    schema = rows[0]["S"]
    out, prev = [], [None] * len(schema)
    for row in rows:
        rep, nul = row.get("R", 0), row.get("Ø", 0)
        vals = iter(row.get("C", []))
        cur = []
        for i, s in enumerate(schema):
            if rep >> i & 1:
                v = prev[i]
            elif nul >> i & 1:
                v = None
            else:
                v = next(vals)
                if "DN" in s and isinstance(v, int):
                    v = vd[s["DN"]][v]
            cur.append(v)
        out.append(cur)
        prev = cur
    return out


def fetch_year(info: dict, year: int) -> tuple[list[list], list[dict]]:
    rows, responses, restart = [], [], None
    while True:
        r = _post("/public/reports/querydata?synchronous=true", _query_body(info, year, restart))
        responses.append(r)
        ds = r["results"][0]["result"]["data"]["dsr"]["DS"][0]
        rows.extend(decode_dsr(ds))
        restart = ds.get("RT")
        if not restart:
            break
    return rows, responses


def fetch_permits(raw_dir: Path, years: list[int], today: date | None = None, refresh: bool = False,
                  log=print) -> dict:
    """One gzip JSON of raw querydata responses per submission year, plus manifest.json."""
    today = today or date.today()
    raw_dir.mkdir(parents=True, exist_ok=True)
    man_path = raw_dir / "manifest.json"
    entries = {e["year"]: e for e in fu.read_manifest(man_path).get("files", [])}
    info = model_info()
    for year in years:
        path = raw_dir / f"permits_submitted_{year}.json.gz"
        if path.exists() and not refresh and year != today.year and year in entries:
            log(f"{year}: cached ({entries[year]['rows']} rows)")
            continue
        t0 = time.time()
        rows, responses = fetch_year(info, year)
        raw = json.dumps({"year": year, "columns": COLUMNS + ["Record Ct"], "responses": responses}).encode()
        path.write_bytes(gzip.compress(raw, mtime=0))
        entries[year] = {"year": year, "file": path.name, "accessed": fu.now_iso(),
                         "seconds": round(time.time() - t0, 1), "rows": len(rows),
                         "bytes_uncompressed": len(raw), "sha256_stored": fu.sha256_file(path)}
        log(f"{year}: {len(rows)} rows")
    lr = info.get("last_refresh") or ""
    m = re.search(r"\d+", lr)
    fu.write_manifest(man_path, [entries[y] for y in sorted(entries)], {
        "source_id": SOURCE_ID, "url": VIEW_URL, "linked_from": PAGE_URL, "api_host": API_HOST,
        "resource_key": RESOURCE_KEY, "model_display_name": info.get("display_name"),
        "model_last_refresh_utc": (datetime.fromtimestamp(int(m.group(0)) / 1000, tz=timezone.utc).isoformat()
                                   if m else None),
        "publisher": "City of Sun Prairie (Power BI publish-to-web report 'All Submitted Permits Report')",
        "license": "No open-data license stated; report published to the web by the City.",
        "columns_requested": COLUMNS + ["Sum(Record Ct)"], "columns_not_requested": list(NOT_REQUESTED),
        "method": "scripts/build_comparison_permits.py --fetch --city sun_prairie "
                  "(anonymous Power BI querydata, one query per PermitList.Year)",
    })
    return fu.read_manifest(man_path)


# ---------------------------------------------------------------- classification of record types
# Munis (2016 - mid 2021) residential codes seen in the data: R001-R150 new one-family homes (one code
# per subdivision/builder), R160 duplex, R180/R190 multi-unit; Z900 demolition/raze.
MUNIS_NEW_SF_RE = re.compile(r"^R(?:0\d\d|1[0-5]\d)$")
MUNIS_DUPLEX = ("R160",)
MUNIS_MULTI = ("R170", "R180", "R190")
MUNIS_RAZE = ("Z900",)
# Munis codes for work on an existing home (alterations, re-roof, HVAC, plumbing, electrical, decks...)
MUNIS_EXISTING_RE = re.compile(r"^R(?:2\d\d|3\d\d|4\d\d|5\d\d|9\d\d)$")

NEW_SF_TEXT_RE = re.compile(r"(?:single[- ]family|\bSFR?\b|one[- ]family)\s*(?:home|house|dwelling|residence)?"
                            r"|\bnew\s+(?:\w+\s+){0,3}(?:home|house|residence|dwelling)\b", re.I)
DUPLEX_TEXT_RE = re.compile(r"duplex|two[- ]family|2[- ]family|twin\s*home|zero[- ]lot", re.I)
MULTI_TEXT_RE = re.compile(r"\b(\d{1,3})\s*[- ]?\s*(?:unit|apartment)s?\b", re.I)
CONVERSION_TO_2_RE = re.compile(
    r"chang\w*\s+(?:\w+\s+){0,4}?into\s+(?:an?\s+)?(?:duplex|two[- ]family|2[- ]family)|conver\w*\s+(?:\w+\s+){0,5}?(?:in)?to\s+(?:an?\s+)?(?:duplex|two[- ]family|2[- ]family|two[- ]unit|2[- ]unit)"
    r"|\b(?:add|create|adding|creating)\w*\s+(?:an?\s+)?(?:second|2nd|additional)\s+(?:dwelling\s+|living\s+)?unit"
    r"|\bin[- ]law\b|accessory\s+dwelling|\bADU\b", re.I)
RAZE_TEXT_RE = re.compile(r"\braz(?:e|ing)\b|\bdemoli", re.I)
DWELLING_WORD_RE = re.compile(r"house|home|dwelling|residence|single[- ]family|duplex|two[- ]family", re.I)
# Munis one-letter statuses: A active, C closed, W withdrawn, X void, D denied, H hold, E expired.
# OpenGov: Active, Complete, Stopped (workflow stopped = abandoned).
WITHDRAWN_STATUS_RE = re.compile(r"^(?:W|X|D)$|void|withdr|cancel|denied|reject|stopped", re.I)


DWELLING_NOUN = r"(?:home|house|residence|dwelling|duplex|twin\w*|2[- ]flat|two[- ]flat|ranch|condo\w*)"
NEW_START_RE = re.compile(
    r"^\W*(?:construct(?:ion)?\s+(?:of\s+)?(?:an?\s+)?|build\s+(?:an?\s+)?|proposed\s+)?new\s+"
    r"(?!deck|porch|addition|landing|stair|garage|shed|fence|pool|patio|window|roof|siding|furnace|water|kitchen|"
    r"bath|basement|egress|electric|service|ac\b|a/c|hvac|door|driveway|sidewalk)", re.I)
NEW_CONSTRUCTION_RE = re.compile(r"\bnew\s+(?:home\s+)?construction\b", re.I)
NOT_NEW_DWELLING_RE = re.compile(
    r"\b(?:deck|porch|addition|landing|stairs?|remodel\w*|basement|egress|sunroom|three[- ]season|garage\s+addition)\b",
    re.I)
SHORT_DWELLING_RE = re.compile(
    r"^\W*(?:(?:one|two|1|2)[- ]story,?\s+)?(?:single[- ]family|two[- ]family|twin|duplex)\s*"
    r"(?:home|house|residence|dwelling|condo)?\W*$", re.I)


DWELLING_PHRASE_RE = re.compile(
    r"(?:single[- ]?family|two[- ]family|one[- ]family|twin|duplex|2[- ]flat|two[- ]flat)[\s,/-]+(?:[\w/.-]+\s+){0,3}?"
    r"(?:home|house|residence|residential|dwelling|condo\w*|unit)s?\b"
    r"|\bnew\s+(?:[\w/.,'-]+\s+){0,6}?(?:home|house|residence|dwelling|duplex|twin\s*home)s?\b"
    r"|^\W*(?:single[- ]family|duplex|twin\s*home)\W*$"
    r"|^\W*(?:\w+\W+){0,4}?new,?\s+(?:[\w/.,'-]+\s+){0,6}?(?:single|two|one)[- ]?family\b"
    r"|\bnew\s+construction\W+SFR\b"
    r"|(?:single|two)[- ]?family\s*[-,]?\s*(?:new\s+construction|domain|build\b)"
    r"|^\W*single\s+home\W*$", re.I)
WORK_ON_EXISTING_RE = re.compile(
    r"\b(?:deck|porch|addition|landing|stairs?|remodel\w*|renovat\w*|basement|egress|sunroom|repair\w*|replac\w*|"
    r"convert\w*|bath\w*|kitchen|interior|framing|vanity|existing|our|my|to\s+the|of\s+the|alteration|finish\w*|"
    r"garage|shed|fence|pool|roof\w*|siding|window|furnace|electric\w*|plumb\w*)\b", re.I)


INSIDE_PHRASE_RE = re.compile(r"\b(?:deck|porch|addition|landing|stairs?|remodel\w*|renovat\w*|existing|our|my|"
                              r"shed|fence|pool|roof\w*|basement|furnace|window|lights?|to|on|of|in)\b", re.I)


def is_new_dwelling_text(d: str) -> bool:
    """Description's subject is a new house/duplex (not a deck, addition or remodel of one).

    Rule: find the first dwelling phrase ("single family home", "twin home", "new ... house");
    the words before it must not name work on an existing building (deck, addition,
    remodel, basement, existing, our, ...). "New construction" with a dwelling word also counts.
    """
    d = d or ""
    m = DWELLING_PHRASE_RE.search(d)
    if not m:
        return False
    if not WORK_ON_EXISTING_RE.search(d[:m.start()]) and not INSIDE_PHRASE_RE.search(m.group(0)):
        return True
    return bool(re.match(r"^\W*(?:\w+\W+){0,3}new\s+(?:home\s+)?construction\b", d, re.I))


def classify_record(rtype: str, desc: str) -> tuple[str, float, str]:
    """(kind, units_raw, basis). kind: new_sf, new_duplex, new_multi, raze, conversion, existing_work, other."""
    t = (rtype or "").strip()
    tu = t.upper()
    d = desc or ""
    # ----- Munis codes
    if re.match(r"^[RCZ]\d{3}$", tu):
        if MUNIS_NEW_SF_RE.match(tu):
            if DUPLEX_TEXT_RE.search(d):
                return "new_duplex", 2.0, "munis_code+text"
            return "new_sf", 1.0, "munis_code"
        if tu in MUNIS_DUPLEX:
            return "new_duplex", 2.0, "munis_code"
        if tu in MUNIS_MULTI:
            m = MULTI_TEXT_RE.search(d)
            return "new_multi", (float(m.group(1)) if m else float("nan")), "munis_code+text_units"
        if tu in MUNIS_RAZE or RAZE_TEXT_RE.search(d):
            return "raze", (-1.0 if DWELLING_WORD_RE.search(d) else 0.0), "munis_code"
        if CONVERSION_TO_2_RE.search(d) and not re.search(r"\bto\s+(?:a\s+)?single", d, re.I):
            return "conversion", 1.0, "conversion_text"
        if MUNIS_EXISTING_RE.match(tu):
            return "existing_work", 0.0, "munis_code"
        return "other", 0.0, "munis_code"
    # ----- OpenGov record types (text)
    if re.search(r"raz|demoli", tu, re.I) or (RAZE_TEXT_RE.search(d) and not re.search(r"interior\s+demo", d, re.I)):
        if re.search(r"raz|demoli", tu, re.I) or re.search(r"(?:raze|demolish)\w*\s+(?:the\s+|an?\s+)?(?:existing\s+)?"
                                                      r"(?:house|home|dwelling|residence|single)", d, re.I):
            return "raze", (-1.0 if DWELLING_WORD_RE.search(d) else 0.0), "type_or_text"
    one_two = re.search(r"1\s*(?:&|and|-|/)\s*2\s*family|one\s*(?:&|and)\s*two|1-2 family|OTFD", tu, re.I)
    # only the OpenGov "new construction, additions, alterations" type can carry a new home;
    # MWOT/MWMC are minor-work permits on existing buildings
    new_capable = bool(re.match(r"^OTFD\b", tu)) or bool(re.search(r"new\s+construction", tu, re.I))
    if new_capable and is_new_dwelling_text(d):
        if DUPLEX_TEXT_RE.search(d) or re.search(r"2[- ]flat|two[- ]flat", d, re.I):
            return "new_duplex", 2.0, "type+text"
        m = MULTI_TEXT_RE.search(d)
        if m and int(m.group(1)) >= 3:
            return "new_multi", float(m.group(1)), "type+text_units"
        return "new_sf", 1.0, "type+text"
    if (re.search(r"multi|commercial", tu, re.I) and re.search(r"\bnew\b", tu + " " + d, re.I)
            and not re.search(r"renovat|remodel|alteration", d, re.I)):
        m = MULTI_TEXT_RE.search(d)
        if m and int(m.group(1)) >= 3 and re.search(r"apartment|unit|residential|townhome|condo", d, re.I):
            return "new_multi", float(m.group(1)), "type+text_units"
    if CONVERSION_TO_2_RE.search(d) and not re.search(r"\bto\s+(?:a\s+)?single", d, re.I):
        return "conversion", 1.0, "conversion_text"
    if one_two or re.search(r"residential|deck|roof|hvac|mechanical|plumbing|electrical|alteration|remodel", tu, re.I):
        return "existing_work", 0.0, "type"
    return "other", 0.0, "type"


def scrub_builder_name(d: str) -> str:
    """Remove the builder/owner name segment of a Munis new-home description.

    "TWO STORY, SINGLE FAMILY HOME - <NAME> LOT 9 <PLAT>" -> "... - [name removed] LOT 9 <PLAT>";
    without a LOT, the last " - <NAME>" segment is removed.
    """
    d = d or ""
    if re.search(r"\bLOT\b", d):
        return re.sub(r"\s+-\s+[^-]*?(?=\s+LOT\b)", " - [name removed]", d, count=1)
    parts = re.split(r"\s+-\s+", d)
    if len(parts) >= 2 and re.search(DWELLING_NOUN + r"|single|family|duplex", " ".join(parts[:-1]), re.I):
        return " - ".join(parts[:-1]) + " - [name removed]"
    return d


def read_raw_year(path: Path) -> pd.DataFrame:
    d = json.loads(gzip.decompress(path.read_bytes()))
    rows = []
    for r in d["responses"]:
        rows.extend(decode_dsr(r["results"][0]["result"]["data"]["dsr"]["DS"][0]))
    return pd.DataFrame(rows, columns=d["columns"])


def load_raw_permits(raw_dir: Path) -> pd.DataFrame:
    """All cached years as the standard frame. Owner and contractor were never downloaded."""
    frames = []
    for path in sorted(raw_dir.glob("permits_submitted_*.json.gz")):
        df = read_raw_year(path)
        df["source_file"] = path.name
        df["source_row"] = range(len(df))
        frames.append(df)
    if not frames:
        raise FileNotFoundError(f"no permits_submitted_*.json.gz in {raw_dir}; run with --fetch")
    df = pd.concat(frames, ignore_index=True)
    out = pd.DataFrame({
        "permit_id": df["Record"].astype(str).str.strip(),
        "permit_type": df["Record Type"].fillna("").astype(str).str.strip(),
        "description": df["Project Description"].fillna("").astype(str).str.strip(),
        "record_status": df["Record Status"].fillna("").astype(str).str.strip(),
        "parcel_raw": df["Parcel"].fillna("").astype(str).str.strip(),
        "subdivision": df["Subdivision"].fillna("").astype(str).str.strip(),
        "issue_date": pd.to_datetime(pd.to_numeric(df["Date Submitted"], errors="coerce"), unit="ms"),
        "record_ct": pd.to_numeric(df["Record Ct"], errors="coerce"),
        "source_file": df["source_file"], "source_row": df["source_row"],
    })
    # Munis new-home descriptions name the builder/owner-builder after " - " (e.g.
    # "TWO STORY, SINGLE FAMILY HOME - <BUILDER> LOT 9 <PLAT>"); the name is removed at ingestion
    munis_new = out["permit_type"].str.match(r"^R(?:0\d\d|1[0-9]\d)$")
    out.loc[munis_new, "description"] = out.loc[munis_new, "description"].map(scrub_builder_name)
    no = pd.to_numeric(df["Street No"], errors="coerce")
    out["address_raw"] = [(f"{int(n)} " if pd.notna(n) else "") + (s or "")
                          for n, s in zip(no, df["Street Name"].fillna("").astype(str).str.strip())]
    out["address_raw"] = out["address_raw"].str.strip()
    k = [classify_record(t, d) for t, d in zip(out["permit_type"], out["description"])]
    out["record_kind"] = [x[0] for x in k]
    out["units_raw"] = [x[1] for x in k]
    out["units_basis"] = [x[2] for x in k]
    out["withdrawn"] = out["record_status"].str.contains(WITHDRAWN_STATUS_RE)
    # a submission that was withdrawn/voided/denied authorizes nothing
    out.loc[out["withdrawn"] & (out["units_raw"] > 0), "units_raw"] = 0.0
    out["use_class"] = out["record_kind"]
    out["est_cost"] = float("nan")
    out["bldg_sqft"] = float("nan")
    digits = out["parcel_raw"].str.replace(r"\D", "", regex=True)
    out["parcel_key"] = digits.where(digits.str.len() == 12)
    out["address_unit"] = ""
    out["jurisdiction_id"] = JURISDICTION_ID
    out["source_id"] = SOURCE_ID
    out = out[out["permit_id"].ne("") & out["permit_id"].ne("None")]
    return out[list(STANDARD_COLUMNS) + ["source_file", "source_row", "parcel_raw", "parcel_key", "address_unit",
                                         "units_basis", "record_kind", "record_status", "withdrawn",
                                         "subdivision", "record_ct"]].reset_index(drop=True)


class SunPrairieAdapter(CityAdapter):
    source_id = SOURCE_ID
    parcel_source_id = PARCEL_SOURCE_ID
    jurisdiction_id = JURISDICTION_ID
    jurisdiction_name = JURISDICTION_NAME
    state_fips = "55"
    county_fips = ("025",)
    new_residential_types = ()
    raze_types = ("__raze__",)  # razes are identified by record_kind (see load_raw_permits)
    v12_placename = "CITY OF SUN PRAIRIE"
    v12_coname = "DANE"
    bps_id = BPS_ID
    first_year = 2016
    restrictive_last_year = 2025  # last whole restrictive year
    restrictive_end = "2026-05-05"  # Ord. 984 (adopted 2026-05-05) allows ADUs by special use; records
    # submitted before this date are in the restrictive period (review N6: 2026 is split, Jan 1-May 4)
    stage = "application"

    def load_permits(self, raw_dir: Path) -> pd.DataFrame:
        df = load_raw_permits(raw_dir)
        df["source_record_type"] = df["permit_type"]
        df.loc[df["record_kind"].eq("raze"), "permit_type"] = "__raze__"
        return df

    def is_new_dwelling(self, df: pd.DataFrame) -> pd.Series:
        return df["record_kind"].isin(["new_sf", "new_duplex"])

    def is_manufactured(self, df: pd.DataFrame) -> pd.Series:
        return df["description"].str.contains(r"manufactured|mobile\s+home", case=False, regex=True)

    def is_existing_dwelling_work(self, df: pd.DataFrame) -> pd.Series:
        return df["record_kind"].eq("existing_work")

    def is_teardown_signal(self, df: pd.DataFrame) -> pd.Series:
        return df["record_kind"].eq("raze") & (df["units_raw"] < 0)
