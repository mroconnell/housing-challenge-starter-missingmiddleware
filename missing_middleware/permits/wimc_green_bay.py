"""Green Bay city: monthly "Detail Summary of Projects Issued" building reports (2022-2025).

The city posts one PDF per month in its Archive Center ("Building Reports", AMID=46,
https://www.greenbaywi.gov/625/Building-Reports). The live site sits behind a Cloudflare
browser challenge, so plain HTTP gets 403; the files are fetched from the Internet Archive's
copies of the same Archive Center URLs (public GETs, original bytes via the `id_` form).
The Archive holds every month from January 2022 to June 2024, August-December 2024 and
February 2025, plus the full-year detail reports for 2022, 2023 and 2024 (same layout, every
project of the year). July 2024 records are taken from the 2024 yearly report (dated 2024-07-01).
January 2025 and March-December 2025 were never captured, so 2025 holds February only.
Lot check: the 2019 tax-roll improvement value of every new-dwelling parcel (statewide parcel
layer V6, Brown County) plus raze permits on the same parcel in the series.

Each project row: project number, address with the parcel number after "..", owner,
applicant, fees, estimated cost, status, then "[<code> - <type>] <description>" and
free-text staff notes. Owner and applicant are dropped in `load()`.
"""
from __future__ import annotations

import json
import re
import subprocess
import urllib.parse
import time
from pathlib import Path

import pandas as pd

from . import classify
from . import fetch_util as fu

META = {
    "slug": "green_bay",
    "place": "Green Bay city",
    "geoids": ["5500931000"],
    "source_url": "https://www.greenbaywi.gov/625/Building-Reports",
    "source_desc": "monthly and yearly 'Detail Summary of Projects Issued' building report PDFs from the "
                   "city Archive Center, fetched from Internet Archive captures (live site blocks non-browser clients)",
    "stage": "issued",
    "license": "public record (no stated licence); copies from web.archive.org",
    "method": "ADU/sf-to-duplex text rules on every issued project, plus manual review of every new "
              "1-2 family dwelling (lot checked against 2019 tax-roll improvements and raze permits) and every "
              "'unit'/'apartment'/'duplex'/'kitchen'/conversion record.",
}

# (month key, Archive Center ADID, Internet Archive timestamp, original URL)
FILES = [
    ("2022-01", 622, "20221218153305", "https://greenbaywi.gov/Archive.aspx?ADID=622"),
    ("2022-02", 624, "20221218153302", "https://greenbaywi.gov/Archive.aspx?ADID=624"),
    ("2022-03", 628, "20221218153259", "https://greenbaywi.gov/Archive.aspx?ADID=628"),
    ("2022-04", 630, "20221218153257", "https://greenbaywi.gov/Archive.aspx?ADID=630"),
    ("2022-05", 636, "20221218153255", "https://greenbaywi.gov/Archive.aspx?ADID=636"),
    ("2022-06", 637, "20221218153252", "https://greenbaywi.gov/Archive.aspx?ADID=637"),
    ("2022-07", 639, "20221218153249", "https://greenbaywi.gov/Archive.aspx?ADID=639"),
    ("2022-08", 642, "20221218153247", "https://greenbaywi.gov/Archive.aspx?ADID=642"),
    ("2022-09", 645, "20221218153244", "https://greenbaywi.gov/Archive.aspx?ADID=645"),
    ("2022-10", 647, "20221218153241", "https://greenbaywi.gov/Archive.aspx?ADID=647"),
    ("2022-11", 650, "20221218153238", "https://greenbaywi.gov/Archive.aspx?ADID=650"),
    ("2022-12", 652, "20240718080650", "https://greenbaywi.gov/Archive.aspx?ADID=652"),
    ("2023-01", 654, "20240718080635", "https://greenbaywi.gov/Archive.aspx?ADID=654"),
    ("2023-02", 656, "20240718080627", "https://greenbaywi.gov/Archive.aspx?ADID=656"),
    ("2023-03", 658, "20240718080611", "https://greenbaywi.gov/Archive.aspx?ADID=658"),
    ("2023-04", 659, "20240718080314", "https://greenbaywi.gov/Archive.aspx?ADID=659"),
    ("2023-05", 661, "20240718080307", "https://greenbaywi.gov/Archive.aspx?ADID=661"),
    ("2023-06", 665, "20240718080255", "https://greenbaywi.gov/Archive.aspx?ADID=665"),
    ("2023-07", 668, "20240718080242", "https://greenbaywi.gov/Archive.aspx?ADID=668"),
    ("2023-08", 670, "20240718080217", "https://greenbaywi.gov/Archive.aspx?ADID=670"),
    ("2023-09", 672, "20240718080202", "https://greenbaywi.gov/Archive.aspx?ADID=672"),
    ("2023-10", 674, "20240718080153", "https://greenbaywi.gov/Archive.aspx?ADID=674"),
    ("2023-11", 676, "20240718080146", "https://greenbaywi.gov/Archive.aspx?ADID=676"),
    ("2023-12", 678, "20240718080136", "https://greenbaywi.gov/Archive.aspx?ADID=678"),
    ("2024-01", 681, "20240718080127", "https://greenbaywi.gov/Archive.aspx?ADID=681"),
    ("2024-02", 685, "20240718080112", "https://greenbaywi.gov/Archive.aspx?ADID=685"),
    ("2024-03", 686, "20240718080105", "https://greenbaywi.gov/Archive.aspx?ADID=686"),
    ("2024-04", 688, "20240718080057", "https://greenbaywi.gov/Archive.aspx?ADID=688"),
    ("2024-05", 691, "20240718080048", "https://greenbaywi.gov/Archive.aspx?ADID=691"),
    ("2024-06", 693, "20240718080025", "https://greenbaywi.gov/Archive.aspx?ADID=693"),
        ("2024-08", 697, "20250317203953", "https://www.greenbaywi.gov/ArchiveCenter/ViewFile/Item/697"),
    ("2024-09", 700, "20250322114844", "https://www.greenbaywi.gov/ArchiveCenter/ViewFile/Item/700"),
    ("2024-10", 702, "20250321111757", "https://www.greenbaywi.gov/ArchiveCenter/ViewFile/Item/702"),
    ("2024-11", 704, "20250318202524", "https://www.greenbaywi.gov/ArchiveCenter/ViewFile/Item/704"),
    ("2024-12", 706, "20250318034152", "https://www.greenbaywi.gov/ArchiveCenter/ViewFile/Item/706"),
    ("2025-02", 711, "20250321111752", "https://www.greenbaywi.gov/ArchiveCenter/ViewFile/Item/711"),
    # yearly summaries (counts only; kept for cross-checks)
    ("2022-yearly", 653, "20240718080642", "https://greenbaywi.gov/Archive.aspx?ADID=653"),
    ("2023-yearly", 682, "20240718080120", "https://greenbaywi.gov/Archive.aspx?ADID=682"),
    ("2024-yearly", 708, "20250324122603", "https://www.greenbaywi.gov/ArchiveCenter/ViewFile/Item/708"),
]
PARCEL_URL = ("https://services.arcgis.com/xOi1kZaI0eWDREZv/arcgis/rest/services/"
              "2020_Brown_County_Assessed_Value/FeatureServer/0/query")
PARCEL_FILE = "parcels_2019roll_new_dwellings.json"
YEARLY_YEARS = (2022, 2023, 2024)  # full-year detail reports fetched
# Months listed on the city's Building Reports page for which no archive copy exists.
MISSING = ["2024-07", "2025-01"] + ["2025-%02d" % m for m in range(3, 13)]


def fetch(raw_dir: Path, log=print) -> dict:
    raw_dir = Path(raw_dir)
    raw_dir.mkdir(parents=True, exist_ok=True)
    old = {e["file"]: e for e in fu.read_manifest(raw_dir / "manifest.json").get("files", [])}
    entries = []
    for key, adid, ts, orig in FILES:
        name = f"gb_building_report_{key}.pdf"
        path = raw_dir / name
        url = f"https://web.archive.org/web/{ts}id_/{orig}"
        if not path.exists():
            log(f"fetch {key} {url}")
            data = b""
            for attempt in range(6):  # the Archive refuses connections when hit quickly
                try:
                    data = fu.get(url, tries=2)
                    break
                except RuntimeError as exc:
                    log(f"  retry after error: {exc}")
                    time.sleep(30 * (attempt + 1))
            if not data.startswith(b"%PDF"):
                raise RuntimeError(f"not a PDF: {url}")
            path.write_bytes(data)
            time.sleep(6)
        e = old.get(name) or {"file": name, "url": url, "original_url": orig, "adid": adid,
                              "accessed": fu.now_iso()}
        e["sha256"] = fu.sha256_file(path)
        entries.append(e)
    # 2019 tax-roll improvement values for every new-dwelling parcel (and the parent of a split lot)
    pfile = raw_dir / PARCEL_FILE
    df = load(raw_dir)
    new = df[df["permit_type"].fillna("").str.contains(NEW_DWELLING_TYPE_RE)]
    ids = set(new["parcel_id"].dropna()) | {_parent(p) for p in new["parcel_id"].dropna() if _parent(p)}
    ids = sorted(ids)
    if not pfile.exists() or not set(ids) <= set(json.loads(pfile.read_text())["queried"]):
        rows = []
        for i in range(0, len(ids), 50):
            where = "PLACENAME='CITY OF GREEN BAY' AND PARCELID IN (%s)" % ",".join("'%s'" % x for x in ids[i:i + 50])
            body = urllib.parse.urlencode({"where": where, "returnGeometry": "false", "f": "json",
                                           "outFields": "PARCELID,IMPVALUE,LNDVALUE,PROPCLASS,TAXROLLYEAR"}).encode()
            res = json.loads(fu.get(PARCEL_URL, data=body))
            rows += [f["attributes"] for f in res.get("features", [])]
        pfile.write_text(json.dumps({"queried": ids, "rows": rows}, indent=1) + "\n")
    entries.append({"file": PARCEL_FILE, "url": PARCEL_URL, "accessed": fu.now_iso(),
                    "note": "Wisconsin statewide parcels V6 (2020 release, 2019 tax roll), Brown County, "
                            "fields PARCELID/IMPVALUE/LNDVALUE/PROPCLASS only",
                    "sha256": fu.sha256_file(pfile)})
    meta = {k: META[k] for k in ("place", "source_url", "license")}
    meta["missing_months"] = MISSING
    fu.write_manifest(raw_dir / "manifest.json", entries, meta)
    return fu.read_manifest(raw_dir / "manifest.json")


# ---------------------------------------------------------------- parsing
REC_RE = re.compile(r"^\s{0,3}(\d{5,7})\s{2,}(\S.*?)\.\.(\S+)\s{2,}(.*?)\s*(\$[\d,]+\.\d\d)\s*(\$[\d,.]+)?\s*([A-Za-z][\w ]*?)?\s*$")
TYPE_RE = re.compile(r"^\s*\[(\d+)-(\d+)\s+-\s+(.*?)\]\s*(.*)$")
FOOTER_RE = re.compile(r"Page \d+ of \d+ - Report Prepared|Detail Summary of Projects Issued|^\s*Proj #|"
                       r"^\s*\d+/\d+/\d{4} to \d+/\d+/\d{4}\s*$")
SUMMARY_START_RE = re.compile(r"^\s*Summary|^\s*Type\s+Description|Totals:", re.I)
# words in staff notes that point at a dwelling unit; only the flag leaves this module
NOTE_FLAG_RE = re.compile(r"accessory\s+dwell|\bADU\b|apartment|\bapt\b|duplex|two[- ]family|2[- ]family|"
                          r"second\s+(?:unit|dwelling|house|home)|in[- ]law|living\s+(?:unit|quarters)|"
                          r"kitchen|efficiency|\bunit\b", re.I)
WRAP_WIDTH = 124
HOUSE_NBR_RE = re.compile(r"^\s*(\d+[A-Z]?(?:-\d+)?(?:\s*1/2)?)\s+(.*)$")


def _parent(pid) -> str | None:
    """Parcel numbers of split lots carry a suffix (14-1356-1 from 14-1356)."""
    if not isinstance(pid, str) or pid.count("-") < 2:
        return None
    return pid.rsplit("-", 1)[0]


def _parcel_values(raw_dir: Path) -> dict:
    f = Path(raw_dir) / PARCEL_FILE
    if not f.exists():
        return {}
    return {r["PARCELID"]: r["IMPVALUE"] for r in json.loads(f.read_text())["rows"]}


def _pdftext(path: Path) -> str:
    return subprocess.run(["pdftotext", "-layout", str(path), "-"], capture_output=True, text=True,
                          check=True).stdout


def _parse(text: str, month: str) -> list[dict]:
    rows, cur, stage, pending = [], None, None, ""
    for line in text.splitlines():
        if FOOTER_RE.search(line) or not line.strip():
            continue
        m = REC_RE.match(line)
        if m:
            if cur:
                rows.append(cur)
            pid, addr, parcel, _people, fees, est, status = m.groups()
            status = status or ""
            est = re.sub(r"(\.\d\d).*$", r"\1", est) if est and "." in est else (est or "")
            cur = {"permit_id": pid, "address": addr.strip(), "parcel_id": parcel.strip(),
                   "fees": fees, "est_cost": est, "status": status.strip(), "month": month,
                   "type_code": None, "permit_type": None, "description": "", "notes": []}
            stage = "head"
            continue
        if cur is None:
            continue
        if re.match(r"^\s*\d{1,2}\s+\S", line) and re.search(r"\$[\d,]+\.\d\d\s*$", line) and stage != "head":
            # per-type summary table at the end of the report
            rows.append(cur)
            cur = None
            break
        if stage == "head" and line.strip().startswith("[") and "]" not in line:
            pending = line.strip()
            stage = "type_cont"
            continue
        if stage == "type_cont":
            line = pending + " " + line.strip()
            stage = "head"
        t = TYPE_RE.match(line)
        if t and stage == "head":
            cur["type_code"] = f"{t.group(1)}-{t.group(2)}"
            cur["permit_type"] = t.group(3).strip()
            cur["description"] = t.group(4).strip()
            # a description that fills the line wraps onto the next one
            stage = "body_wrap" if len(line.rstrip()) >= WRAP_WIDTH else "body"
            continue
        if stage == "body_wrap":
            stage = "body"
            # staff notes (dated, starred) are not part of the description
            if not re.search(r"\d{1,2}/\d{1,2}/\d{2,4}|^\s*\*", line):
                cur["description"] += " " + line.strip()
                continue
        if stage == "body":
            cur["notes"].append(line.strip())
        # stage == "head": continuation of owner/applicant columns -> dropped
    if cur:
        rows.append(cur)
    return rows


def load(raw_dir: Path) -> pd.DataFrame:
    raw_dir = Path(raw_dir)
    recs, yearly = [], []
    for key, *_ in FILES:
        path = raw_dir / f"gb_building_report_{key}.pdf"
        if not path.exists():
            continue
        text = _pdftext(path)
        hdr = re.search(r"(\d+)/1/(\d{4}) to (\d+)/(\d+)/(\d{4})", text)
        if "yearly" in key:
            if not hdr or hdr.group(0) != f"1/1/{key[:4]} to 12/31/{key[:4]}":
                raise RuntimeError(f"{path.name}: not a full-year report: {hdr and hdr.group(0)}")
            # records only in the yearly report (mostly the uncaptured month): month unknown,
            # dated to the year's missing month, or July 1 when no month is missing
            miss = [mm for mm in MISSING if mm.startswith(key[:4])]
            yearly.extend(dict(r, date_source="yearly report") for r in
                          _parse(text, miss[0] if len(miss) == 1 else f"{key[:4]}-07"))
            continue
        if not hdr or f"{int(hdr.group(2)):04d}-{int(hdr.group(1)):02d}" != key:
            raise RuntimeError(f"{path.name}: report period does not match {key}: {hdr and hdr.group(0)}")
        recs.extend(dict(r, date_source="monthly report") for r in _parse(text, key))
    seen = {r["permit_id"] for r in recs}
    recs += [r for r in yearly if r["permit_id"] not in seen]
    df = pd.DataFrame(recs)
    df["date"] = pd.to_datetime(df["month"] + "-01")
    df["year"] = df["date"].dt.year.astype(int)
    hn = df["address"].str.extract(HOUSE_NBR_RE)
    df["house_nbr"] = hn[0]
    df["street"] = hn[1].fillna(df["address"]).str.strip()
    df["units_raw"] = float("nan")
    notes = df["notes"].map(lambda xs: " ".join(xs))
    df["note_flags"] = notes.map(lambda s: ",".join(sorted({m.group(0).lower() for m in NOTE_FLAG_RE.finditer(s)})))
    df["est_cost"] = pd.to_numeric(df["est_cost"].str.replace(r"[$,]", "", regex=True), errors="coerce")
    df = df.drop(columns=["notes", "address", "fees", "month"])
    imp = _parcel_values(raw_dir)
    df["lot_imp_2019"] = df["parcel_id"].map(imp)
    df["parent_imp_2019"] = df["parcel_id"].map(lambda p: imp.get(_parent(p)) if _parent(p) else None)
    df = df.drop_duplicates(["permit_id", "type_code", "description", "date"])
    cols = ["permit_id", "date", "year", "permit_type", "description", "units_raw", "parcel_id", "street",
            "house_nbr", "type_code", "status", "est_cost", "note_flags", "date_source", "lot_imp_2019", "parent_imp_2019"]
    return df[cols].reset_index(drop=True)


def coverage(df: pd.DataFrame) -> pd.DataFrame:
    out = []
    for y in range(2022, 2026):
        d = df[df.year == y]
        months = d["date"].dt.month.nunique()
        has_year = (d["date_source"] == "yearly report").any() or y in YEARLY_YEARS
        miss = [] if (has_year and y in YEARLY_YEARS) else [m for m in MISSING if m.startswith(str(y))]
        if y in YEARLY_YEARS and months == 12:
            out.append({"year": y, "months_with_records": int(months), "records": int(len(d)),
                        "complete": True,
                        "note": "monthly reports plus the full-year detail report"
                                + (" (July records taken from the yearly report)" if y == 2024 else "")})
            continue
        out.append({"year": y, "months_with_records": int(months), "records": int(len(d)),
                    "complete": months == 12 and not miss,
                    "note": ("monthly reports Jan-Dec present" if months == 12 and not miss else
                             f"no archived copy of {', '.join(miss)} (live site blocks plain HTTP)" if miss else
                             f"only {months} monthly files parsed - run fetch()")})
    return pd.DataFrame(out)


# ---------------------------------------------------------------- classification
NEW_DWELLING_TYPE_RE = re.compile(r"Residential - New", re.I)
TWO_FAMILY_TYPE_RE = re.compile(r"2 Family|Two Family|Duplex", re.I)
MULTI_TYPE_RE = re.compile(r"5 or More Family|3 (?:and|&|or) 4 Family|Multi-Family|Rooming", re.I)
TRADE_CODE_RE = re.compile(r"^(?:40|50|60|70)-")
# building permits: any of these words makes the record a candidate
UNIT_WORDS_RE = re.compile(
    r"accessory\s+dwell|\bADU\b|apartment|\bapts?\b|duplex|two[- ]?family|2[- ]?family|\b2\s*unit|two\s+unit|"
    r"second\s+(?:unit|dwelling|house|home|residence)|in[- ]law|living\s+(?:unit|quarters)|"
    r"efficiency|dwelling\s+unit|additional\s+unit|\bnew\s+unit|\bunits?\b|\bconver(?:t|sion)|carriage|coach|granny|"
    r"tiny\s+(?:house|home)|guest\s+(?:house|suite)|\bkitchen(?:ette)?\b.*\b(?:basement|garage|upper|lower|attic)|"
    r"\b(?:basement|garage|upper|lower|attic)\b.*\bkitchen", re.I)
# trade permits (electric/HVAC/plumbing): only explicit unit words
TRADE_UNIT_RE = re.compile(r"accessory\s+dwell|\bADU\b|in[- ]law|(?:new|additional|second|2nd|upper|lower)\s+"
                           r"(?:unit|apartment|apt|dwelling|living)|single\s+family\s+(?:in)?to|1\s+family\s+(?:in)?to|"
                           r"(?:into|to)\s+(?:a\s+)?(?:duplex|2\s+family|two\s+family)", re.I)
NOT_UNIT_RE = re.compile(r"tub\s+to\s+shower|shower\s+conversion|\bconver\w*\s+(?:to|from)\s+(?:gas|electric|LED|natural)", re.I)
RAZE_TYPE_RE = re.compile(r"\bRaze\b|^Demolition\b", re.I)
RAZE_DESC_RE = re.compile(r"\braz(?:e|ing)\b|demo(?:lish)?\w*\s+(?:the\s+|existing\s+)?(?:house|home|dwelling)", re.I)


def classify_records(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    out["component"] = None
    out["units"] = 0
    out["reason"] = ""
    out["candidate"] = False
    desc = out["description"].fillna("")
    ptype = out["permit_type"].fillna("")
    tcode = out["type_code"].fillna("")
    razed = set(out.loc[ptype.str.contains(RAZE_TYPE_RE) & (ptype.str.contains(r"Raze", case=False)
                                                           | desc.str.contains(RAZE_DESC_RE)), "parcel_id"].dropna())
    is_new = ptype.str.contains(NEW_DWELLING_TYPE_RE) & ~ptype.str.contains(MULTI_TYPE_RE)
    # first month each parcel shows up with a non-new-dwelling permit (evidence of an existing building)
    weak = (ptype + " " + desc).str.contains(r"Tempor|Temproary|Erosion|\bSite\b|new\s+(?:home|house|construction)",
                                            case=False, regex=True)
    other = out[~is_new & ~weak & out["parcel_id"].notna()]
    first_other = other.groupby("parcel_id")["date"].min().to_dict()
    for idx, r in out.iterrows():
        d, t = desc.at[idx], ptype.at[idx]
        tc, note = classify.text_class(d)
        comp, why, cand = None, "", False
        if NOT_UNIT_RE.search(d) and not tc:
            pass
        elif tc == "adu_legalization":
            cand, why = True, "ADU text but legalization of an existing unit (excluded)"
        elif tc:
            comp, why, cand = tc, f"ADU text ({note})", True
        elif note.startswith("near_miss"):
            cand, why = True, f"ADU text with exclusion: {note}"
        elif classify.SF_TO_TWO_RE.search(d) and not TRADE_CODE_RE.match(tcode.at[idx]):
            comp, why, cand = "sf_to_duplex", "description: single family to two units", True
        elif is_new.at[idx]:
            cand = True
            kind = "two-family building" if TWO_FAMILY_TYPE_RE.search(t) else "single-family house"
            fo = first_other.get(r.parcel_id)
            lot_imp = r.lot_imp_2019 if pd.notna(r.lot_imp_2019) else None
            if r.parcel_id in razed or RAZE_DESC_RE.search(d):
                why = f"new {kind} on a parcel with a raze permit/raze wording (teardown/rebuild; excluded)"
            elif lot_imp and lot_imp >= 20000:
                why = (f"new {kind}; lot had a building on the 2019 tax roll (improvements ${lot_imp:,.0f}) and no "
                       "raze permit seen 2022-25 - rebuild or second dwelling, unconfirmed (upper bound)")
            elif fo is not None and fo < r.date:
                why = (f"new {kind}; parcel had other permits in earlier months - checked by hand, "
                       "unconfirmed (upper bound)")
            elif pd.notna(r.parent_imp_2019) and r.parent_imp_2019 > 0:
                why = (f"new {kind} on a lot split from a parcel with a house (new lot by land division, "
                       "not a second home on the same lot; excluded)")
            elif lot_imp is not None:
                why = (f"new {kind}; no house on the lot on the 2019 tax roll (improvements "
                       f"${lot_imp or 0:,.0f}; vacant or city-owned lot; excluded)")
            else:
                why = f"new {kind}; lot not on the 2019 tax roll (new subdivision lot; excluded)"
        elif TRADE_CODE_RE.match(tcode.at[idx]):
            if TRADE_UNIT_RE.search(d):
                cand, why = True, "trade permit mentioning a unit; reviewed, no new unit"
        elif MULTI_TYPE_RE.search(t):
            pass  # units in multifamily buildings are out of scope
        elif UNIT_WORDS_RE.search(d) or re.search(r"adu|apartment|duplex|family|second|in.law|living|efficiency",
                                                   r.note_flags or ""):
            cand, why = True, "unit-related wording in a building permit; reviewed, no new unit"
        out.at[idx, "component"] = comp
        out.at[idx, "units"] = 1 if comp else 0
        out.at[idx, "reason"] = why
        out.at[idx, "candidate"] = cand
    for pid, j in JUDGMENTS.items():
        sel = out["permit_id"] == pid
        if not sel.any():
            continue
        out.loc[sel, "candidate"] = True
        out.loc[sel, "reason"] = "judged: " + j["why"]
        if j["counts"]:
            out.loc[sel, "component"] = j["component"]
            out.loc[sel, "units"] = int(j.get("units", 1))
        else:
            out.loc[sel, "component"] = None
            out.loc[sel, "units"] = 0
    out["units"] = out["units"].astype(int)
    return out


JUDGMENTS: dict[str, dict] = {
    # --- possible units that cannot be confirmed (upper bound only)
    "111173": {"counts": False, "component": "adu_detached", "units": 1,
               "why": "unconfirmed (upper bound): 2022-12 furnace permit for a 'mother in law suite behind main house' "
                      "on xxx Reber St; no building permit for the suite 2022-25, so it may predate 2022"},
    "117063": {"counts": False, "component": "adu_conversion", "units": 1,
               "why": "unconfirmed (upper bound): 2024-06 electrical permit wiring a 'new lower suite' with kitchen "
                      "circuits (sink, refrigerator, microwave) on xxx Sitka St; only a fence permit otherwise on the "
                      "parcel 2022-25 (July 2024 report missing); may be a wet bar/kitchenette, not a separate unit"},
    "116327": {"counts": False, "component": "second_dwelling", "units": 1,
               "why": "unconfirmed (upper bound): new house with detached garage on xxx 14th Av; lot had a house "
                      "on the 2019 roll ($38k) that a 2023 note calls condemned - most likely a replacement, "
                      "but no raze permit seen (July 2024 report missing)"},
    # --- near-hits excluded
    "115536": {"counts": False, "component": None,
               "why": "description 'raze old & build new' - teardown/rebuild"},
    "116775": {"counts": False, "component": None,
               "why": "house changed from a duplex to a single-family dwelling (unit removed)"},
    "117465": {"counts": False, "component": None, "why": "convert 4 units to 2 units (units removed)"},
    "110475": {"counts": False, "component": None, "why": "existing duplex re-platted as condo duplex; no new unit"},
    "114375": {"counts": False, "component": None, "why": "existing duplex to zero-lot-line duplex; no new unit"},
    "107998": {"counts": False, "component": None,
               "why": "garage converted into living space of the house; no kitchen or unit mentioned"},
    "112482": {"counts": False, "component": None, "why": "garage attic conversion; no unit mentioned"},
    "114361": {"counts": False, "component": None,
               "why": "basement finish plus new (main) kitchen in a house remodel; no second unit mentioned"},
    "116681": {"counts": False, "component": None,
               "why": "main floor and basement remodel with new kitchen and basement bedrooms; no second unit mentioned"},
    "112542": {"counts": False, "component": None,
               "why": "adding basement bedroom/bath and new kitchen in a house remodel; no second unit mentioned"},
}
