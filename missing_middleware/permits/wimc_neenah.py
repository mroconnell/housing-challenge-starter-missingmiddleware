"""Neenah, WI (city, Winnebago Co.) adapter: monthly "Building Permit Activity" PDFs.

The city posts one record-level PDF a month (permit #, template, address with
county parcel number, owner, contractor, issue date, valuation, description).
Older months are no longer linked from the Building Activity Reports page but
remain in the WordPress media library, which is listed through the public
WordPress REST API (GET, JSON). Files are found there, downloaded once, and
parsed with `pdftotext -layout` (poppler) by column positions taken from each
page's header line.

Months held for 2022-2025 (by the "Date From/To" header of each file):
2022: Feb, Jul, Aug, Sep, Oct (Jan, Mar-Jun, Nov, Dec never found);
2023: Apr-Oct, Dec (Jan exists only as a count summary; Feb, Mar, Nov missing);
2024 and 2025: all twelve months.

Owner names and contractor names never leave `load()`. Neenah zoning allows one
dwelling unit per lot in R-1 (ADUs prohibited), so near-zero counts are expected.
"""
from __future__ import annotations

import json
import re
import subprocess
from collections import defaultdict
from datetime import datetime
from pathlib import Path

import numpy as np
import pandas as pd

from . import classify
from . import fetch_util as fu

META = {
    "slug": "neenah",
    "place": "Neenah city",
    "geoids": ["5513955750"],
    "source_url": "https://www.ci.neenah.wi.us/departments/inspections/building-activity-reports/",
    "source_desc": "monthly 'Building Permit Activity' PDFs (record-level), current page plus WordPress media library",
    "stage": "issued",
    "license": "public record (no stated licence)",
    "method": ("Text rule on the permit description (classify.text_class, SF_TO_TWO_RE) plus a "
               "structured rule: WUBPA (new 1&2-family) permits on a parcel that had earlier "
               "residential-building activity or text such as 'second dwelling' are candidates; "
               "every candidate is hand-reviewed in JUDGMENTS."),
}

MEDIA_API = "https://www.ci.neenah.wi.us/wp-json/wp/v2/media"
# Activity reports (not the count-only "Summary" files) uploaded 2022-01..2026-02.
ACTIVITY_RE = re.compile(r"/uploads/(\d{4})/(\d{2})/[^/]*activ[^/]*\.pdf$", re.I)
SKIP_RE = re.compile(r"guide|flyer|crime|booth|pool|weekly|summer", re.I)
UPLOAD_MIN, UPLOAD_MAX = "2022/01", "2026/02"

RECORD_RE = re.compile(r"^\s*(\d{9})\s+(\S.*)$")
DATE_RE = re.compile(r"\b(\d{2}/\d{2}/\d{4})\b")
VAL_RE = re.compile(r"\$[\d,]+(?:\.\d\d)?")
PARCEL_RE = re.compile(r"\((\d{8,12})\s*\)")
PERIOD_RE = re.compile(r"Date From\s+(\S+)\s+and Date To\s+(\S+)")
TEMPLATE_WORDS = {"Accessory", "Commercial", "Building", "Demolition", "Fence", "Foundation", "Repair",
                  "Moving", "Pool", "Residential", "Sign", "Solar", "WUBPA"}
HEADER_COLS = ["Permit #", "Templates", "Permit Address", "Owner Name", "Contractor",
               "Issue Date", "Valuation", "Description"]


# ------------------------------------------------------------------ fetch
def _list_media(log=print) -> list[dict]:
    out, page = [], 1
    while True:
        try:
            raw = fu.get(MEDIA_API, params={"mime_type": "application/pdf", "per_page": 100,
                                            "page": page, "_fields": "id,date,title,source_url"},
                         tries=2)
        except RuntimeError:
            break  # past the last page WordPress answers 400
        rows = json.loads(raw)
        if not rows:
            break
        out.extend(rows)
        page += 1
    log(f"neenah: {len(out)} PDF media items listed")
    return out


def fetch(raw_dir: Path, log=print) -> dict:
    raw_dir = Path(raw_dir)
    raw_dir.mkdir(parents=True, exist_ok=True)
    man_path = raw_dir / "manifest.json"
    manifest = fu.read_manifest(man_path)
    have = {e["file"]: e for e in manifest.get("files", [])}
    if have and all((raw_dir / f).exists() for f in have):
        # idempotent: the archive of past months does not change
        return manifest
    entries = list(have.values())
    for item in _list_media(log):
        url = item["source_url"]
        m = ACTIVITY_RE.search(url)
        if not m or SKIP_RE.search(url):
            continue
        if not (UPLOAD_MIN <= f"{m.group(1)}/{m.group(2)}" <= UPLOAD_MAX):
            continue
        fname = url.split("/uploads/")[1].replace("/", "_")
        dest = raw_dir / fname
        if fname in have and dest.exists():
            continue
        dest.write_bytes(fu.get(url))
        entries.append({"file": fname, "url": url, "accessed": fu.now_iso(),
                        "sha256": fu.sha256_file(dest), "media_title": item["title"]["rendered"]})
        log(f"neenah: got {fname}")
    meta = {k: META[k] for k in ("place", "source_url", "license")}
    meta["media_api"] = MEDIA_API
    fu.write_manifest(man_path, entries, meta)
    return fu.read_manifest(man_path)


# ------------------------------------------------------------------ parse
def _pdftext(path: Path) -> str:
    return subprocess.run(["pdftotext", "-layout", str(path), "-"], capture_output=True,
                          text=True, check=True).stdout


def _tokens(line: str):
    """(start, text) for runs separated by 2+ spaces."""
    for m in re.finditer(r"\S+(?: \S+)*", line):
        yield m.start(), m.group(0)


def _col_for(pos: int, cols: list[tuple[str, int]]) -> str:
    # nearest header start: data columns drift up to ~4 characters from the header
    return min(cols, key=lambda cs: abs(cs[1] - pos))[0]


def _parse_file(path: Path) -> tuple[list[dict], tuple]:
    text = _pdftext(path)
    period = PERIOD_RE.search(text)
    period = (period.group(1), period.group(2)) if period else (None, None)
    recs, cur, cols = [], None, None
    for line in text.splitlines():
        if line.lstrip().startswith("Permit #") and "Templates" in line:
            cols = [(c, line.find(c)) for c in HEADER_COLS if line.find(c) >= 0]
            continue
        if (cols is None or not line.strip() or "Building Permit Activity" in line
                or PERIOD_RE.search(line) or re.match(r"^\s*Page \d+ of \d+", line)
                or re.match(r"^\s*\d{2}/\d{2}/\d{4}\s*$", line)):
            continue
        m = RECORD_RE.match(line)
        if m:
            cur = defaultdict(list)
            cur["_id"] = m.group(1)
            recs.append(cur)
        if cur is None:
            continue
        for pos, tok in _tokens(line):
            if m and tok.startswith(m.group(1)):
                tok = tok[len(m.group(1)):].strip()
                pos += len(m.group(1)) + 1
                if not tok:
                    continue
            col = _col_for(pos, cols)
            # dates and valuations sometimes drift a few characters left or right
            if DATE_RE.fullmatch(tok):
                col = "Issue Date"
            elif VAL_RE.fullmatch(tok):
                col = "Valuation"
            cur[col].append(tok)
    out = []
    for r in recs:
        tmpl = " ".join(r.get("Templates", [])).strip()
        addr = " ".join(r.get("Permit Address", []))
        if re.search(r"\d", tmpl):  # template and address ran together in one token
            words = tmpl.split()
            kind = [w for w in words if w in TEMPLATE_WORDS]
            rest = [w for w in words if w not in TEMPLATE_WORDS]
            tmpl, addr = " ".join(kind), (" ".join(rest) + " " + addr).strip()
        parcel = PARCEL_RE.search(addr)
        # a parcel number can spill into the owner column when the address is long
        if not parcel:
            parcel = PARCEL_RE.search(" ".join(r.get("Owner Name", [])))
        addr = PARCEL_RE.sub("", addr).strip()
        date = next((d for d in r.get("Issue Date", []) if DATE_RE.fullmatch(d)), None)
        val = next((v for v in r.get("Valuation", []) if VAL_RE.fullmatch(v)), None)
        out.append({
            "permit_id": r["_id"],
            "permit_type": tmpl,
            "address": addr,
            "parcel_id": parcel.group(1) if parcel else None,
            "date": date,
            "valuation": float(val.replace("$", "").replace(",", "")) if val else np.nan,
            "description": " ".join(r.get("Description", [])).strip(),
            "source_file": path.name,
        })
    return out, period


def _split_address(addr: str) -> tuple[str | None, str | None]:
    m = re.match(r"^\s*(\d+[A-Z]?(?:-\d+)?)\s+(.*)$", addr or "")
    if m:
        return m.group(1), m.group(2).strip().upper()
    return None, (addr or "").strip().upper() or None


def load(raw_dir: Path) -> pd.DataFrame:
    raw_dir = Path(raw_dir)
    rows, periods = [], {}
    for pdf in sorted(raw_dir.glob("*.pdf")):
        recs, period = _parse_file(pdf)
        periods[pdf.name] = period
        rows.extend(recs)
    df = pd.DataFrame(rows)
    df["date"] = pd.to_datetime(df["date"], format="%m/%d/%Y", errors="coerce")
    df = df.sort_values(["permit_id", "source_file"]).drop_duplicates("permit_id", keep="last")
    hs = df["address"].map(_split_address)
    df["house_nbr"] = [h for h, _ in hs]
    df["street"] = [s for _, s in hs]
    df["year"] = df["date"].dt.year.astype("Int64")
    df["units_raw"] = np.nan
    df["units_raw"] = df["units_raw"].astype(float)
    df.attrs["periods"] = periods
    cols = ["permit_id", "date", "year", "permit_type", "description", "units_raw", "parcel_id",
            "street", "house_nbr", "valuation", "source_file"]
    return df[cols].reset_index(drop=True)


# ------------------------------------------------------------------ coverage
def _months_from_periods(periods: dict) -> dict[int, set]:
    months: dict[int, set] = {}
    for start, end in periods.values():
        if not start:
            continue
        s = pd.to_datetime(start, errors="coerce")
        e = pd.to_datetime(end, errors="coerce")
        if pd.isna(s) or pd.isna(e):
            continue
        # a file "3/31 - 4/30" or "6/30 - 7/31" covers the month of its end date
        months.setdefault(e.year, set()).add(e.month)
    return months


def coverage(df: pd.DataFrame) -> pd.DataFrame:
    periods = df.attrs.get("periods") or {}
    if not periods:  # attrs can be dropped by pandas ops; recompute from the records
        mm = df.dropna(subset=["date"]).groupby("year")["date"].apply(lambda s: set(s.dt.month))
        months = {int(y): set(v) for y, v in mm.items()}
    else:
        months = _months_from_periods(periods)
    notes = {
        2022: "record-level files only for Feb, Jul, Aug, Sep, Oct; Jan, Mar-Jun, Nov, Dec not found "
              "in the media library or by URL guessing",
        2023: "Apr-Oct and Dec present; Jan only as a count summary (2 new 1&2-family permits); "
              "Feb, Mar, Nov not found",
        2024: "all 12 monthly files",
        2025: "all 12 monthly files",
    }
    out = []
    for y in range(2022, 2026):
        n = len(months.get(y, set()))
        out.append({"year": y, "months_with_records": n,
                    "records": int((df["year"] == y).sum()),
                    "complete": n == 12, "note": notes[y]})
    return pd.DataFrame(out)


# ------------------------------------------------------------------ classify
NEW_DWELLING_TEMPLATE = "WUBPA"
DWELLING_TEXT_RE = re.compile(r"\bdwelling\b|\bhome\b|\bhouse\b|duplex|two[- ]family|\b2[- ]family"
                              r"|apartment|living\s+quarters|\bunit\b|kitchen", re.I)
CANDIDATE_RE = re.compile(r"apartment|living\s+quarters|in[- ]law|second\s+(?:dwelling|unit|home|house)"
                          r"|duplex|two[- ]family|\b2[- ]family|upper\s+unit|lower\s+unit|dwelling\s+unit"
                          r"|\bADU\b|accessory\s+dwell|guest\s+(?:house|suite)|efficiency"
                          r"|convert\w*\s+(?:\w+\s+){0,4}(?:to|into)\s+(?:a\s+)?(?:living|dwelling|unit|apartment|duplex)",
                          re.I)

JUDGMENTS: dict[str, dict] = {
    "202401108": {"counts": False, "component": None, "units": 0,
                  "why": "new 2-story home on xxx Bayview Rd; the only earlier permit on the parcel is its own "
                         "footings/foundation permit (202400712), so no prior house"},
    "202500560": {"counts": False, "component": None, "units": 0,
                  "why": "new zero-lot-line duplex on a lot with no earlier permits (new construction, not a "
                         "second home)"},
    "202400991": {"counts": False, "component": None, "units": 0,
                  "why": "modular home moved onto xxx Riverlawn St (with moving permit 202400728); a replacement/"
                         "new single home, no evidence a house remains on the lot"},
    "202400728": {"counts": False, "component": None, "units": 0,
                  "why": "moving permit for the same modular home on xxx Riverlawn St (see 202400991)"},
    "202401380": {"counts": False, "component": None, "units": 0,
                  "why": "3-unit apartment converted back to a single-family home (unit reduction)"},
    "202300467": {"counts": False, "component": None, "units": 0,
                  "why": "renovation of an existing 2nd-floor apartment; no unit added"},
}


def classify_records(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    comp, units, reason, cand = [], [], [], []
    wubpa_parcels = df[df.permit_type.str.startswith(NEW_DWELLING_TEMPLATE, na=False)]
    earlier = df.dropna(subset=["parcel_id"]).groupby("parcel_id")
    for r in df.itertuples():
        d = r.description or ""
        c, u, why, is_c = None, 0, "", False
        tc, note = classify.text_class(d)
        if tc and tc != "adu_legalization":
            c, u, why, is_c = tc, 1, "text rule: ADU wording", True
        elif tc == "adu_legalization":
            why, is_c = "excluded: legalization of an existing unit", True
        elif classify.SF_TO_TWO_RE.search(d):
            c, u, why, is_c = "sf_to_duplex", 1, "text rule: single-family to two-family", True
        elif note.startswith("near_miss") or note == "related_term":
            why, is_c = f"near-miss ({note})", True
        elif CANDIDATE_RE.search(d):
            why, is_c = "candidate wording; not a second home by rule", True
        if (r.permit_type or "").startswith("Moving") or re.search(r"modular\s+home|move\s+\w*\s*home", d, re.I):
            is_c = True
            why = why or "home moved onto a lot: check whether a house remains"
        if (r.permit_type or "").startswith(NEW_DWELLING_TEMPLATE):
            # new 1&2-family dwelling: candidate only when the lot shows an earlier house
            prior = pd.DataFrame()
            if r.parcel_id and r.parcel_id in earlier.groups:
                g = earlier.get_group(r.parcel_id)
                prior = g[(g.permit_id < r.permit_id)
                          & ~g.permit_type.str.startswith(("Demolition", "Fence"), na=False)]
            if re.search(r"second|rear|existing\s+(?:house|home|dwelling)", d, re.I) or len(prior):
                is_c = True
                why = why or ("new dwelling on a parcel with earlier permits: unconfirmed "
                              "(lot may already hold a house)")
            elif re.search(r"duplex|two[- ]family|2[- ]family|twin", d, re.I):
                is_c = True
                why = why or "new duplex/two-family on a lot with no earlier house: excluded"
        j = JUDGMENTS.get(str(r.permit_id))
        if j:
            is_c = True
            if j["counts"]:
                c, u = j["component"], int(j.get("units", 1))
            else:
                c, u = None, 0
            why = "judgment: " + j["why"]
        comp.append(c)
        units.append(u)
        reason.append(why)
        cand.append(is_c)
    df["component"] = comp
    df["units"] = units
    df["reason"] = reason
    df["candidate"] = cand
    return df
