"""Pleasant Prairie, WI (village) adapter: SmartGov public "Permits Issued-Detail Report".

Acquisition is plain HTTP (stdlib urllib), no browser:

1. GET the SmartGov public Reports page (ASP.NET form state).
2. POST "View report" for `VOPP_Permit_Issued_Detail_Report`. SmartGov answers
   with a redirect into an Exago WebReports session on
   reports-new.smartgovcommunity.com (cookie + settings blob).
3. Exago's own JSON endpoints (`wrajax/<Method>.ashx`) load the report,
   start an execution with the "Date Issued between" filter set, report
   status, and the finished file is fetched from `ExecuteExport.aspx`.

CSV/Excel export is disabled for this report; RTF is used because it is a
cell table (`\\cell`/`\\row`) that parses without layout guessing. Each raw
year file is stored gzip-compressed.

The raw report carries owner names, owner mailing addresses and contractor
addresses. They stay in data/raw only: `load_raw_permits` (the single entry
point for every later stage) keeps none of them.
"""
from __future__ import annotations

import gzip
import html
import json
import random
import re
import string
import time
import urllib.parse
import uuid
from datetime import date
from pathlib import Path

import pandas as pd

from . import fetch_util as fu
from .base import STANDARD_COLUMNS, CityAdapter

SOURCE_ID = "pleasant_prairie_permits"
PARCEL_SOURCE_ID = "wi_v12_parcels_kenosha_pp"
JURISDICTION_ID = "5505963300"  # county subdivision GEOID 55-059-63300 (Pleasant Prairie village)
JURISDICTION_NAME = "Pleasant Prairie village, WI"
BPS_ID = "686000"

PORTAL = "https://vlg-pleasantprairie-wi.smartgovcommunity.com"
REPORTS_URL = PORTAL + "/Public/ReportsView"
REPORT_ID = "361fe732-f57f-4e4c-827c-72b67cc09ca6"  # VOPP_Permit_Issued_Detail_Report
VIEW_URL = PORTAL + f"/Public/ReportsView/ViewReport?reportId={REPORT_ID}&reportType=Exago"
DATE_FILTER = "Permits.Date Issued"

# ---------------------------------------------------------------- permit types
NEW_DWELLING_UNITS = {  # permit type -> dwelling units added (calculated from type)
    "NEW SINGLE FAMILY DWELLING": 1,
    "NEW TWO FAMILY DWELLING": 2,
    "NEW MANUFACTURED HOME": 1,
}
MULTI_FAMILY_TYPES = ("NEW MULTI-FAMILY BUILDING",)
RAZE_TYPES = ("RAZING PERMIT",)
# work on an existing dwelling: evidence that a dwelling stood on the parcel
EXISTING_DWELLING_TYPE_RE = re.compile(
    r"^(?:SINGLE[- ]FAMILY|TWO[- ]FAMILY)\s+(?:ROOFING|ELECTRICAL|PLUMBING|HVAC|ADDITION|DECK|INGROUND|ABOVE GROUND|"
    r"SOLAR|ALTERATION|REMODEL|WINDOW|FIREPLACE|BASEMENT|GENERATOR|HOT TUB|RESIDENTIAL HANSEN)", re.I)


# ---------------------------------------------------------------- download
def _verification_token() -> str:
    """SmartGov's client-side form token: random letters around a ms timestamp."""
    c = lambda: random.choice(string.ascii_lowercase)  # noqa: E731
    val = c() + str(int(time.time()) * 1000) + c()
    pos = random.randint(0, 9)
    return val[:pos] + c() + c() + c() + val[pos:]


class _ExagoSession:
    def __init__(self, log=print):
        self.op = fu.opener(cookies=True)
        page = fu.get(REPORTS_URL, op=self.op, timeout=120).decode("utf-8", "replace")
        vs = re.search(r'id="__VIEWSTATE" value="([^"]*)"', page).group(1)
        vsg = re.search(r'id="__VIEWSTATEGENERATOR" value="([^"]*)"', page).group(1)
        bnd = "----mm" + uuid.uuid4().hex
        fields = {"__VIEWSTATE": vs, "__VIEWSTATEGENERATOR": vsg,
                  "__submitFormValidator__": _verification_token(), "_fields": ""}
        body = "".join(f'--{bnd}\r\nContent-Disposition: form-data; name="{k}"\r\n\r\n{v}\r\n'
                       for k, v in fields.items()) + f"--{bnd}--\r\n"
        import urllib.request

        req = urllib.request.Request(VIEW_URL, data=body.encode(),
                                     headers={"Content-Type": "multipart/form-data; boundary=" + bnd})
        with self.op.open(req, timeout=120) as r:
            ex, url = r.read().decode("utf-8", "replace"), r.geturl()
        m = re.search(r'name="WebReportsCtrl\$wrSettings"[^>]*value="([^"]*)"', ex)
        if not m:
            raise RuntimeError("SmartGov did not hand over an Exago session")
        self.settings = json.loads(html.unescape(m.group(1)))
        self.base = url.split("ExagoHome.aspx")[0]
        s = self.settings
        self.ajax_settings = {"Language": s["Language"], "SessionNum": s["SessionNum"],
                              "ShowErrorDetail": s["ShowErrorDetail"], "IsAdmin": s["IsAdmin"],
                              "DevicePixelRatio": 1, "IsExceptionServerEvent": s["IsExceptionServerEvent"],
                              "BrowserType": "Chrome"}

    def ajax(self, method: str, *args):
        import urllib.request

        a = []
        for x in args:
            if isinstance(x, tuple):  # (className, value): a typed argument
                a.append({"className": x[0], "value": json.dumps(x[1]), "isArray": False})
            else:
                a.append({"className": "", "value": x, "isArray": False})
        a.append({"className": "Settings", "value": json.dumps(self.ajax_settings), "isArray": False})
        url = (self.base + "wrajax/" + method + ".ashx?t="
               + urllib.parse.quote(self.settings["TempPath"], safe=""))
        req = urllib.request.Request(url, data=json.dumps({"args": a}).encode(),
                                     headers={"Content-Type": "text/plain; charset=utf-8"})
        with self.op.open(req, timeout=600) as r:
            return json.loads(r.read())["value"]

    def run(self, start: date, end: date, export: str = "rtf", log=print) -> bytes:
        none = None
        d = self.ajax("Client.BaseExecuteCtrl.LoadCallback", self.settings["ApiReportId"], "pdf", True, True,
                      none, ("Client.ClientJsApiPromptingFilterValueList", none),
                      ("Client.ClientJsApiExecuteReportFiltersList", none),
                      ("Client.ClientJsApiExecuteReportParameterList", none))["Data"]
        filt = d["Filters"]
        hit = [f for f in filt["Values"] if f["Name"] == DATE_FILTER]
        if len(hit) != 1:
            raise RuntimeError(f"report filter {DATE_FILTER!r} not found")
        # the server misreads ISO dates; it expects MM/DD/YYYY
        hit[0]["Values"] = [start.strftime("%m/%d/%Y"), end.strftime("%m/%d/%Y")]
        ep = self.ajax("Callbacks.Execute.StartExecuteSimple", d["ReportData"], ("Client.ClientFilterValueList", filt),
                       ("Client.ClientParameterValueList", d["Parameters"]), export, True,
                       ("Client.ClientReportAdjustments", none), ("Client.ClientJsApiExecuteReportFiltersList", none),
                       ("Client.ClientJsApiPromptingFilterValueList", none),
                       ("Client.ClientJsApiExecuteReportParameterList", none))
        eid = ep["ExecutionId"]
        t0 = time.time()
        while True:
            st = self.ajax("Callbacks.Execute.GetStatus", self.settings["EncryptedTempPath"], eid, False)
            phase = st.get("phase")
            if phase == 4:
                break
            if phase == 5:  # nothing qualified
                return b""
            if phase not in (-1, 0, 1, 2, 3, 8):
                raise RuntimeError(f"report execution failed (phase {phase}): {str(st.get('msg'))[:300]}")
            if time.time() - t0 > 1800:
                raise RuntimeError("report execution timed out")
            time.sleep(3)
        url = (self.base + f"ExecuteExport.aspx?eid={eid}&bt=Chrome&l="
               + urllib.parse.quote(self.settings["Language"]) + f"&sn={self.settings['SessionNum']}")
        return fu.get(url, op=self.op, timeout=1800, tries=2)


def fetch_permits(raw_dir: Path, years: list[int], today: date | None = None, refresh: bool = False,
                  log=print) -> dict:
    """One gzip RTF per issue year (Jan 1 .. Dec 31, or today) plus manifest.json."""
    today = today or date.today()
    raw_dir.mkdir(parents=True, exist_ok=True)
    man_path = raw_dir / "manifest.json"
    entries = {e["year"]: e for e in fu.read_manifest(man_path).get("files", [])}
    for year in years:
        path = raw_dir / f"permits_issued_{year}.rtf.gz"
        if path.exists() and not refresh and year != today.year and year in entries:
            log(f"{year}: cached ({entries[year]['permits']} permits)")
            continue
        end = min(date(year, 12, 31), today)
        log(f"{year}: requesting {date(year, 1, 1)}..{end}")
        t0 = time.time()
        data = _ExagoSession(log=log).run(date(year, 1, 1), end, "rtf", log=log)
        path.write_bytes(gzip.compress(data, mtime=0))
        n = len(parse_rtf_records(data.decode("cp1252", "replace"))) if data else 0
        entries[year] = {
            "year": year, "file": path.name,
            "request": {"report": "VOPP_Permit_Issued_Detail_Report", "report_id": REPORT_ID,
                        "date_issued_from": f"{year}-01-01", "date_issued_to": end.isoformat(), "export": "rtf"},
            "accessed": fu.now_iso(), "seconds": round(time.time() - t0, 1),
            "bytes_uncompressed": len(data), "sha256_uncompressed": __import__("hashlib").sha256(data).hexdigest(),
            "bytes_stored": path.stat().st_size, "sha256_stored": fu.sha256_file(path), "permits": n,
        }
        log(f"{year}: {n} permits, {len(data):,} bytes, {entries[year]['seconds']} s")
    fu.write_manifest(man_path, [entries[y] for y in sorted(entries)], {
        "source_id": SOURCE_ID, "url": REPORTS_URL, "report_view_url": VIEW_URL,
        "publisher": "Village of Pleasant Prairie (SmartGov public report, Exago WebReports)",
        "license": "No open-data license stated; public report on the Village's SmartGov portal. "
                   "Raw files include owner names and mailing addresses: keep local, never redistribute.",
        "method": "scripts/build_comparison_permits.py --fetch --city pleasant_prairie "
                  "(HTTP: form post -> Exago wrajax LoadCallback, StartExecuteSimple, GetStatus -> ExecuteExport)",
        "report_filters": "Fee code not one of (impact/sewer/erosion deposit codes) [fixed by the report]; "
                          "Date Issued between <year start> and <year end>; Permit Status <> VOID",
    })
    return fu.read_manifest(man_path)


# ---------------------------------------------------------------- RTF parsing
_TOK = re.compile(r"\\([a-zA-Z]+)(-?\d+)? ?|\\'([0-9a-f]{2})|\\([\\{}])|([{}])|([^\\{}]+)", re.S)


def rtf_rows(text: str) -> list[list[str]]:
    """Table rows of an iText RTF as lists of cell strings (control words dropped)."""
    out: list[list[str]] = []
    cur: list[str] = []
    buf: list[str] = []
    for m in _TOK.finditer(text):
        w, _num, hx, esc, _br, txt = m.groups()
        if w:
            if w == "cell":
                cur.append("".join(buf).strip())
                buf = []
            elif w == "row":
                out.append(cur)
                cur = []
            elif w in ("par", "line"):
                buf.append("\n")
            elif w == "tab":
                buf.append(" ")
        elif hx:
            buf.append(bytes([int(hx, 16)]).decode("cp1252", "replace"))
        elif esc:
            buf.append(esc)
        elif txt:
            buf.append(txt.replace("\r", "").replace("\n", ""))
    return out


def _after(row: list[str], label: str) -> str | None:
    for i, c in enumerate(row):
        if c == label and i + 1 < len(row):
            return row[i + 1]
    return None


def parse_rtf_records(text: str) -> list[dict]:
    """One dict per permit with every published field (owner fields included: raw only).

    Record layout (rows): [Owner <name>, Type: <type>] / [<mailing>, Permit Fees:, <fees>,
    Permit:, <number>] / [Cost:, <cost>, Issued Date:, <date>] / [Site Address: <addr>,
    Parcel:, <parcel>] / [Project Description: <text>] / [Contractor: <name>, <address>].
    """
    recs: list[dict] = []
    cur: dict | None = None
    for row in rtf_rows(text):
        cells = [c for c in row if c != ""]
        if not cells:
            continue
        first = cells[0]
        if first.startswith("Owner") and any(c.startswith("Type:") for c in cells):
            cur = {"owner_name": first[5:].strip(), "permit_type": None, "owner_mailing": None, "fees": None,
                   "permit_id": None, "est_cost": None, "issue_date": None, "site_address": None,
                   "parcel": None, "description": None, "contractor": None, "contractor_address": None}
            cur["permit_type"] = " ".join(next(c for c in cells if c.startswith("Type:"))[5:].split())
            recs.append(cur)
            continue
        if cur is None:
            continue
        if "Permit:" in cells:
            cur["permit_id"] = _after(cells, "Permit:")
            cur["fees"] = _after(cells, "Permit Fees:")
            if cells[0] not in ("Permit Fees:", "Permit:"):
                cur["owner_mailing"] = cells[0]
        elif "Issued Date:" in cells:
            cur["issue_date"] = _after(cells, "Issued Date:")
            cur["est_cost"] = _after(cells, "Cost:")
        elif first.startswith("Site Address:") or "Parcel:" in cells:
            if first.startswith("Site Address:"):
                cur["site_address"] = " ".join(first[len("Site Address:"):].split())
            cur["parcel"] = _after(cells, "Parcel:")
        elif first.startswith("Project Description:"):
            cur["description"] = " ".join(first[len("Project Description:"):].split())
        elif first.startswith("Contractor:"):
            cur["contractor"] = first[len("Contractor:"):].strip()
            cur["contractor_address"] = cells[1] if len(cells) > 1 else None
    return recs


# 2015-2024 descriptions start with the owner's surname and the contractor in parentheses,
# e.g. "SMITH (ACME BUILDERS) NSFR-2968 SF". The prefix is personal data: removed at ingestion.
NAME_PREFIX_RE = re.compile(r"^\s*[A-Za-z][A-Za-z'.&/,\- ]{0,40}?\s*(?:\([^)]*\)\s*)+(?=\S)")


WORK_VERB_RE = re.compile(r"^\s*(?:install|replace|new|add|remove|repair|build|construct|run|extend|upgrade|"
                          r"convert|finish|demo|raze|wire|move|relocate|erect|pour|tear|re-?roof)"
                          r"(?:s|es|ed|d|ing|ment|al)?\b", re.I)


PREFIX_WORK_WORDS_RE = re.compile(
    r"\b(?:of|to|for|with|and|install\w*|construct\w*|sign\w*|plumb\w*|electric\w*|directional|garage|deck|"
    r"roof\w*|provide|low|voltage|rewire|backflow|repair|replace\w*|new|addition|remodel|demo\w*|fence|"
    r"driveway|pool|shed|porch|window|door|bath\w*|kitchen|basement|hvac|furnace|water|sewer|gas)\b", re.I)


def strip_name_prefix(desc: str) -> tuple[str, bool]:
    """Remove a leading "OWNER (CONTRACTOR)" prefix (owner surname is personal data)."""
    d = desc or ""
    m = NAME_PREFIX_RE.match(d)
    if not m or WORK_VERB_RE.match(d):
        return d, False
    prefix = d[:m.end()].split("(")[0]
    inner = re.findall(r"\(([^)]*)\)", d[:m.end()])
    if (len(prefix.split()) > 4 or PREFIX_WORK_WORDS_RE.search(prefix)
            or any(re.fullmatch(r"\s*\d+\s*", x) or len(x) > 45 for x in inner)):
        return d, False
    return d[m.end():].strip(), True


PERSONAL_FIELDS = ("owner_name", "owner_mailing", "contractor", "contractor_address", "fees")
SITE_TAIL_RE = re.compile(
    r"^(?P<street>.*?)\s+(?:(?P<lot>\d{1,4})\s+)?(?P<city>PLEASANT\s+PRAIRIE|KENOSHA|BRISTOL|SOMERS|SALEM|"
    r"PADDOCK\s+LAKE|WINTHROP\s+HARBOR)\s*,?\s*(?:WI|WISCONSIN|IL)?(?:\s+\d{5}(?:-\d{4})?)?\s*$", re.I)


def split_site_address(site: str | None) -> tuple[str, str]:
    """'100 EXAMPLE CT  PLEASANT PRAIRIE WI 53158' -> ('100 EXAMPLE CT', '').

    Mobile-home lots print the lot number between street and city
    ('400 102ND AVE 73 PLEASANT PRAIRIE WI', a made-up address); it is returned as the unit.
    """
    s = " ".join((site or "").split())
    m = SITE_TAIL_RE.match(" " + s)
    if not m:
        return s, ""
    street, lot = m.group("street").strip(), m.group("lot") or ""
    street = re.sub(r"\s+(?:UNIT|APT|LOT|#)$", "", street, flags=re.I)
    return street, lot


RAZE_DWELLING_RE = re.compile(r"house|home|dwelling|residence|single[- ]family|duplex|two[- ]family|mobile|"
                              r"manufactured|princip\w*|primary", re.I)
RAZE_ACCESSORY_ONLY_RE = re.compile(r"garage|shed|barn|accessory|pool|deck|concession|silo|carport|gazebo", re.I)
RAZE_TEXT_RE = re.compile(r"\braz(?:e|ed|ing)\b|\bdemoli\w*|\bdemo\s+(?:of\s+)?(?:the\s+)?existing\s+(?:house|home)", re.I)
TEMP_SECOND_PRINCIPAL_TYPES = ("NEW HOME- TWO PRINCIPAL STRUCTURES",)

UNITS_IN_TEXT_RE = re.compile(r"\b(\d{1,3})\s*[- ]?\s*(?:unit|apartment|dwelling unit)s?\b", re.I)
CONVERSION_TO_2_RE = re.compile(
    r"conver\w*\s+(?:\w+\s+){0,5}?(?:in)?to\s+(?:an?\s+)?(?:duplex|two[- ]family|2[- ]family|two[- ]unit|2[- ]unit)"
    r"|\b(?:add|create|adding|creating)\w*\s+(?:an?\s+)?(?:second|2nd|additional)\s+(?:dwelling\s+|living\s+)?unit"
    r"|\bin[- ]law\b"
    r"|accessory\s+dwelling|\bADU\b", re.I)


def units_from_record(permit_type: str, description: str) -> tuple[float, str]:
    """Calculated dwelling units added (the report has no units field) and the basis."""
    t = (permit_type or "").upper()
    d = description or ""
    if t in NEW_DWELLING_UNITS:
        return float(NEW_DWELLING_UNITS[t]), "type"
    if t in MULTI_FAMILY_TYPES:
        m = UNITS_IN_TEXT_RE.search(d)
        return (float(m.group(1)), "type+text_units") if m else (float("nan"), "multi_family_units_unknown")
    if t in RAZE_TYPES:
        if RAZE_DWELLING_RE.search(d):
            return -1.0, "raze_dwelling_text"
        if RAZE_ACCESSORY_ONLY_RE.search(d) or re.search(r"\bportion\b|\bpartial\b", d, re.I):
            return 0.0, "raze_accessory_or_partial"
        return -1.0, "raze_unspecified_building"  # "Razing", "demolition", legacy rows: assume a principal building
    if CONVERSION_TO_2_RE.search(d) and not re.search(r"\bto\s+(?:a\s+)?single", d, re.I):
        return 1.0, "conversion_text"
    return 0.0, "none"


def load_raw_permits(raw_dir: Path) -> pd.DataFrame:
    """All cached years as the standard frame. Owner/contractor fields and fees are dropped here."""
    frames = []
    for path in sorted(raw_dir.glob("permits_issued_*.rtf.gz")):
        text = gzip.decompress(path.read_bytes()).decode("cp1252", "replace")
        recs = parse_rtf_records(text)
        for r in recs:
            for k in PERSONAL_FIELDS:
                r.pop(k, None)
        df = pd.DataFrame(recs, columns=["permit_type", "permit_id", "est_cost", "issue_date", "site_address",
                                         "parcel", "description"])
        df["source_file"] = path.name
        df["source_row"] = range(len(df))
        frames.append(df)
    if not frames:
        raise FileNotFoundError(f"no permits_issued_*.rtf.gz in {raw_dir}; run with --fetch")
    df = pd.concat(frames, ignore_index=True)
    for c in ("permit_id", "permit_type", "site_address", "parcel", "description"):
        df[c] = df[c].fillna("").astype(str).str.strip()
    df["issue_date"] = pd.to_datetime(df["issue_date"], format="%m/%d/%Y", errors="coerce")
    # the "OWNER (CONTRACTOR) work" convention is used mostly 2015-2024, sometimes later
    stripped = [strip_name_prefix(d) for d in df["description"]]
    df["description"] = [x[0] for x in stripped]
    df["description_prefix_removed"] = [x[1] for x in stripped]
    parts = df["site_address"].map(split_site_address)
    df["address_raw"] = [p[0] for p in parts]
    df["address_unit"] = [p[1] for p in parts]
    df["est_cost"] = pd.to_numeric(df["est_cost"].astype(str).str.replace(r"[$,\s]", "", regex=True),
                                   errors="coerce")
    u = [units_from_record(t, d) for t, d in zip(df["permit_type"], df["description"])]
    df["units_raw"] = [x[0] for x in u]
    df["units_basis"] = [x[1] for x in u]
    df["use_class"] = df["permit_type"]
    df["bldg_sqft"] = float("nan")
    df["parcel_raw"] = df["parcel"]
    df["parcel_key"] = df["parcel"].str.replace(r"\s+", "", regex=True).where(df["parcel"].ne(""))
    df["jurisdiction_id"] = JURISDICTION_ID
    df["source_id"] = SOURCE_ID
    df = df[df["permit_id"].ne("")]
    return df[list(STANDARD_COLUMNS) + ["source_file", "source_row", "parcel_raw", "parcel_key", "address_unit",
                                        "units_basis", "description_prefix_removed"]].reset_index(drop=True)


class PleasantPrairieAdapter(CityAdapter):
    source_id = SOURCE_ID
    parcel_source_id = PARCEL_SOURCE_ID
    jurisdiction_id = JURISDICTION_ID
    jurisdiction_name = JURISDICTION_NAME
    state_fips = "55"
    county_fips = ("059",)
    new_residential_types = tuple(NEW_DWELLING_UNITS) + MULTI_FAMILY_TYPES
    raze_types = RAZE_TYPES
    v12_placename = "VILLAGE OF PLEASANT PRAIRIE"
    v12_coname = "KENOSHA"
    bps_id = BPS_ID
    first_year = 2003
    existing_dwelling_type_re = EXISTING_DWELLING_TYPE_RE
    stage = "issued"
    # AQ-032 headline: parcel-rule hits the audit judged likely false are excluded, the same rule as
    # Madison applies to its judged exclusions (review S3); they stay in the unconfirmed upper bound
    second_home_judgments = None  # set below the class (SECOND_HOME_JUDGMENTS)

    def load_permits(self, raw_dir: Path) -> pd.DataFrame:
        return load_raw_permits(raw_dir)

    def is_new_dwelling(self, df: pd.DataFrame) -> pd.Series:
        return df["permit_type"].str.upper().isin(list(NEW_DWELLING_UNITS))

    def is_manufactured(self, df: pd.DataFrame) -> pd.Series:
        return df["permit_type"].str.upper().eq("NEW MANUFACTURED HOME")

    def is_existing_dwelling_work(self, df: pd.DataFrame) -> pd.Series:
        return df["permit_type"].str.match(EXISTING_DWELLING_TYPE_RE)

    def is_teardown_signal(self, df: pd.DataFrame) -> pd.Series:
        """Raze of a (principal) dwelling, raze-related work on another permit (e.g. sewer capping
        for a raze), or a temporary 'two principal structures' permit while a replacement is built."""
        d = df["description"].fillna("")
        raze_dw = df["permit_type"].isin(RAZE_TYPES) & (df["units_raw"] < 0)
        raze_text = (~df["permit_type"].isin(RAZE_TYPES) & d.str.contains(RAZE_TEXT_RE)
                     & ~d.str.contains(r"interior|garage|shed|barn|accessory|deck|pool", case=False, regex=True))
        temp = df["permit_type"].isin(TEMP_SECOND_PRINCIPAL_TYPES)
        return raze_dw | raze_text | temp


_LIKELY_FALSE = ("Parcel-rule second dwelling that the Gate 2 audit judged uncertain_likely_false "
                 "(data/processed/permits_pleasant_prairie/audit_judgments.csv): {why}. Excluded from the "
                 "headline as in Madison; kept in the unconfirmed upper bound.")
SECOND_HOME_JUDGMENTS: dict[str, dict] = {
    "SF1710-020": {"counts": False, "units": 0, "component": None, "upper_bound": True,
                   "judgment": "parcel_rule_likely_false",
                   "evidence": _LIKELY_FALSE.format(why="only prior evidence is one 2014 legacy permit with no "
                                                    "text, and a new gas service followed the house permit, "
                                                    "which fits a first house on the lot")},
    "SF2110-077": {"counts": False, "units": 0, "component": None, "upper_bound": True,
                   "judgment": "parcel_rule_likely_false",
                   "evidence": _LIKELY_FALSE.format(why="a 10,256 sq ft new house whose only prior evidence is a "
                                                    "2012 legacy alteration: likely a replacement of an older "
                                                    "house without a raze permit, i.e. a teardown under AQ-032")},
    "SF2203-055": {"counts": False, "units": 0, "component": None, "upper_bound": True,
                   "judgment": "parcel_rule_likely_false",
                   "evidence": _LIKELY_FALSE.format(why="an earlier new-dwelling permit on the same parcel 4.5 "
                                                    "years before and no raze: most likely the earlier permit "
                                                    "was not built and the lot was re-permitted")},
}
PleasantPrairieAdapter.second_home_judgments = SECOND_HOME_JUDGMENTS
