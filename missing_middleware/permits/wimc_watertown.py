"""Watertown, WI (city; Jefferson and Dodge Cos.) adapter: monthly building-permit PDFs.

Source: https://www.watertownwi.gov/page/reports-monthly-year-end -> Documents ->
Building Safety & Zoning -> Reports-Monthly & Year End -> Building Permits -> "<year> Building
Permits" folders (2023, 2024, 2025, 2026; there is NO 2022 folder - 2022 exists only as the
summary "2022 Construction Totals" chart, which is not record-level).
The folder listings are read from the Nuxt page data of each folder page (plain GET); files are
served from files-backend.assets.thrillshare.com.

Each monthly PDF (Excel export) lists: permit # (YY-NNN), permit date, parcel # (291-xxxx-xxxx-xxx),
site address, contractor, description, census code (2023: "Key", 3-digit code; 2024-25: code
plus label, e.g. "434 - Residential Additions and Alterations"), estimated cost, fee.
The contractor column is often an owner's or person's name: it is never kept by `load()`.

Parsing uses `pdftotext -bbox`; column left edges are detected per file from the most common
word x-positions (Excel cells are left-aligned) and matched to the (centred) header labels.
"""
from __future__ import annotations

import collections
import json
import re
import subprocess
import urllib.request
from html import unescape
from pathlib import Path

import numpy as np
import pandas as pd

from . import classify
from . import fetch_util as fu

META = {
    "slug": "watertown",
    "place": "Watertown city",
    "geoids": ["5505583975", "5502783975"],
    "source_url": "https://www.watertownwi.gov/page/reports-monthly-year-end",
    "source_desc": "monthly building-permit PDFs (2023-2026) from the city document archive",
    "stage": "issued",
    "license": "public record (no stated licence)",
    "method": ("text rule (classify.text_class, SF_TO_TWO_RE) on the description plus census code "
               "(101/103/104/105 new dwellings, 434 residential alterations); every candidate reviewed "
               "by hand; parcel numbers checked for earlier permits."),
}

FOLDER_BASE = ("https://www.watertownwi.gov/documents/departments/building-safety-%26-zoning-department/"
               "reports-monthly-%26-year-end/building-permits/")
FOLDERS = {2023: "2023-building-permits/22162285", 2024: "2024-building-permits/22162281",
           2025: "2025-building-permits/22162279"}
MONTHS = ["january", "february", "march", "april", "may", "june", "july", "august", "september",
          "october", "november", "december"]
WORD_RE = re.compile(r'<word xMin="([\d.]+)" yMin="([\d.]+)" xMax="([\d.]+)" yMax="([\d.]+)">([^<]*)</word>')
PERMIT_RE = re.compile(r"^\d{2}-\d{3,4}[A-Za-z]?$")
DATE_RE = re.compile(r"^\d{1,2}/\d{1,2}/20\d{0,2}$")  # long dates can wrap ("5/23/202" + "5")


# ---------------------------------------------------------------- download
def _nuxt_listing(url: str) -> list[dict]:
    s = fu.get(url).decode("utf-8", "replace")
    d = json.loads(re.search(r'id="__NUXT_DATA__">(.*?)</script>', s, re.S).group(1))

    def res(i):
        v = d[i]
        if isinstance(v, dict):
            return {k: res(x) for k, x in v.items()}
        if isinstance(v, list):
            if v and v[0] in ("ShallowReactive", "Reactive", "Ref", "ShallowRef"):
                return res(v[1])
            return [res(x) for x in v]
        return v

    data = res(d[1]["data"])
    out = []
    for v in data.values():
        out += [x for x in v.get("foldersAndDocuments", []) if isinstance(x, dict) and x.get("url")]
    return out


def fetch(raw_dir: Path, log=print) -> dict:
    raw_dir = Path(raw_dir)
    raw_dir.mkdir(parents=True, exist_ok=True)
    man_path = raw_dir / "manifest.json"
    old = {e["file"]: e for e in fu.read_manifest(man_path).get("files", [])}
    entries = []
    for year, folder in FOLDERS.items():
        names_needed = [f"{year}_{i + 1:02d}.pdf" for i in range(12)]
        if all((raw_dir / n).exists() and n in old for n in names_needed):
            entries += [old[n] for n in names_needed]
            continue
        log(f"watertown: list {folder}")
        for doc in _nuxt_listing(FOLDER_BASE + folder):
            fname = doc.get("file_name", "").lower()
            mon = next((i for i, m in enumerate(MONTHS) if fname.startswith(m)), None)
            if mon is None or str(year) not in fname:
                continue
            name = f"{year}_{mon + 1:02d}.pdf"
            path = raw_dir / name
            if path.exists() and name in old:
                entries.append(old[name])
                continue
            log(f"watertown: GET {doc['file_name']}")
            data = fu.get(doc["url"])
            if not data.startswith(b"%PDF"):
                raise RuntimeError(f"not a PDF: {doc['url']}")
            path.write_bytes(data)
            entries.append({"file": name, "year": year, "month": mon + 1, "title": doc["file_name"],
                            "url": doc["url"], "accessed": fu.now_iso(), "sha256": fu.sha256_file(path),
                            "bytes": len(data)})
    fu.write_manifest(man_path, entries, {
        "source": META["source_url"], "license": META["license"],
        "note": "City of Watertown monthly building permits; no 2022 folder exists (only a summary chart). "
                "Raw PDFs contain a contractor column with person names: keep in data/raw only."})
    return fu.read_manifest(man_path)


# ---------------------------------------------------------------- parse
def _pages(pdf: Path) -> list[list[tuple]]:
    out = subprocess.run(["pdftotext", "-bbox", str(pdf), "-"], capture_output=True, text=True,
                         check=True).stdout
    return [[(float(a), float(b), float(c), unescape(t)) for a, b, c, _d, t in WORD_RE.findall(p)]
            for p in out.split("<page ")[1:]]


def _lines(words, tol=2.0):
    lines = []
    for w in sorted(words, key=lambda w: (w[1], w[0])):
        if lines and abs(lines[-1][0][1] - w[1]) <= tol:
            lines[-1].append(w)
        else:
            lines.append([w])
    return [sorted(l, key=lambda w: w[0]) for l in lines]


HEADERS = [("permit_id", ("Permit",)), ("date", ("Permit",)), ("parcel_id", ("Parcel",)),
           ("address", ("Site", "Address")), ("contractor", ("Contractor",)),
           ("description", ("Description",)), ("code", ("Census", "Key")), ("cost", ("Estimated",))]


def _columns(page) -> list[tuple[str, float]] | None:
    """Left edges for each column of one page, from header label centres and data x-position peaks
    (column positions differ between pages of the same file). None when the page has no header."""
    head = {}
    for line in _lines(page):
        texts = [w[3] for w in line]
        if "Description" in texts:
            for w in line:
                head.setdefault(w[3], []).append(((w[0] + w[2]) / 2, w[0]))
            break
    centres = []
    for name, labels in HEADERS:
        lab = next((l for l in labels if l in head), None)
        if lab is None:
            return None
        # second "Permit" label is the date column; "Date" is on the next line, use the 2nd Permit
        if name == "permit_id":
            centres.append((name, head["Permit"][0][0], head["Permit"][0][1]))
        elif name == "date":
            p = head["Permit"]
            centres.append((name, p[1][0] if len(p) > 1 else head["Date"][0][0], None))
        else:
            centres.append((name, head[lab][0][0], head[lab][0][1]))
    cnt = collections.Counter(round(w[0]) for w in page)
    edges = [("permit_id", 0.0)]
    for i in range(1, len(centres)):
        name, c, x0 = centres[i]
        if name == "date":  # dates are right-aligned: the column starts after the permit numbers
            ends = [w[2] for w in page if PERMIT_RE.match(w[3])]
            if not ends:
                return None
            edges.append((name, max(ends) + 1))
            continue
        if name == "cost":  # right-aligned numbers: start just left of the header label
            edges.append((name, x0 - 2))
            continue
        lo = centres[i - 1][1]
        cands = [(n, x) for x, n in cnt.items() if lo < x <= c + 2]
        if not cands:
            return None
        edges.append((name, max(cands)[1] - 1.5))
    return edges


def _col(x, cols):
    name = cols[0][0]
    for n, x0 in cols:
        if x >= x0:
            name = n
    return name


def parse_pdf(pdf: Path) -> list[dict]:
    pages = _pages(pdf)
    recs, cur, cols = [], None, None
    for page in pages:
        cols = _columns(page) or cols
        if cols is None:
            raise RuntimeError(f"no column header on first page of {pdf.name}")
        for line in _lines(page):
            texts = [w[3] for w in line]
            if texts[0] in ("Page:", "Permit", "#") or "Building" in texts and "Permits" in texts and len(line) < 8:
                cur = None
                continue
            first = {}
            for w in line:
                first.setdefault(_col(w[0], cols), w[3])
            if PERMIT_RE.match(first.get("permit_id", "")) and DATE_RE.match(first.get("date", "")):
                cur = {}
                recs.append(cur)
            if cur is None:
                continue
            for w in line:
                cur.setdefault(_col(w[0], cols), []).append(w[3])
    rows = []
    for c in recs:
        addr = c.get("address", [])
        hn = addr[0] if addr and re.fullmatch(r"\d+[A-Za-z]?", addr[0]) else None
        code = " ".join(c.get("code", []))
        m = re.match(r"(\d{3}|O/S)", code)
        cost = re.sub(r"[^\d.]", "", (c.get("cost") or ["", ""])[0])
        rows.append({"permit_id": c["permit_id"][0], "date": "".join(c["date"][:2]) if len(c["date"][0]) < 8 or c["date"][0].endswith("/202") else c["date"][0],
                     "parcel_id": "".join(c.get("parcel_id", [])) or None,
                     "house_nbr": hn, "street": " ".join(addr[1:] if hn else addr).upper() or None,
                     "description": " ".join(c.get("description", [])) or None,
                     "permit_type": m.group(1) if m else (code or None), "code_label": code or None,
                     "cost": float(cost) if cost else np.nan})
        # contractor column intentionally dropped (person names)
    return rows


def load(raw_dir: Path) -> pd.DataFrame:
    raw_dir = Path(raw_dir)
    rows = []
    for pdf in sorted(raw_dir.glob("20[0-9][0-9]_[01][0-9].pdf")):
        for r in parse_pdf(pdf):
            r["file_month"] = pdf.stem
            rows.append(r)
    df = pd.DataFrame(rows)
    df["date"] = pd.to_datetime(df["date"], format="%m/%d/%Y", errors="coerce")
    df["year"] = df["file_month"].str[:4].astype(int)
    df["units_raw"] = np.nan
    void = df["description"].fillna("").str.fullmatch(r"(?i)\s*void\s*")
    df = df[~void].drop_duplicates("permit_id", keep="first")
    cols = ["permit_id", "date", "year", "permit_type", "description", "units_raw", "parcel_id", "street",
            "house_nbr", "code_label", "cost", "file_month"]
    return df[cols].reset_index(drop=True)


def coverage(df: pd.DataFrame) -> pd.DataFrame:
    out = []
    for y in range(2022, 2026):
        d = df[df.year == y]
        months = d.file_month.nunique() if len(d) else 0
        note = ("no record-level source (only the summary '2022 Construction Totals' chart)" if y == 2022
                else "monthly PDFs")
        out.append({"year": y, "months_with_records": months, "records": len(d),
                    "complete": bool(months == 12), "note": note})
    return pd.DataFrame(out)


CAND_RE = re.compile(r"kitchen|apartment|\bapt\b|in[- ]?law|living\s+(?:quarters|unit)|efficiency|second\s+"
                     r"(?:unit|dwelling|home|house)|dwelling\s+unit|two[- ]family|2[- ]family|duplex|\bADU\b"
                     r"|accessory|conver|upper\s+unit|lower\s+unit|\bunit\b", re.I)
NEW_DWELLING_CODES = {"101", "102", "103", "104", "105"}

JUDGMENTS: dict[str, dict] = {
    # manual review of every 2023-2025 candidate (house numbers redacted)
    "25-198": {"counts": True, "component": "adu_detached", "units": 1,
               "why": "2025-09 'Accessory Dwelling Unit (ADU)', census code 101 (new detached building), "
                      "xxx N. Second St, $150,000; Plan Commission CUP staff report 2025-09-08: detached ~366 sq ft "
                      "studio with kitchen behind the EXISTING single-family home (SR-4 district)"},
    "25-237": {"counts": True, "component": "adu_attached", "units": 1,
               "why": "2025-12 'Accessory Dwelling Unit Above Garage', code 434, xxx Hickory Ct, $100,000; "
                      "Plan Commission CUP 2025-12-08 for a 2-bed ~800 sq ft ADU above the ATTACHED garage of a "
                      "single-family home (Watertown Daily Times, 2025-12-09)"},
    "25-010": {"counts": False, "component": "adu_conversion", "units": 1,
               "why": "unconfirmed: 2025-01 'Adding Bathroom and Kitchen in Basement', xxx Steeplechase Dr, "
                      "$6,000; second kitchen but no unit wording (ADUs need a conditional use)"},
    "25-215": {"counts": False, "component": "adu_conversion", "units": 1,
               "why": "unconfirmed: 2025-10 basement finish with living room/kitchen and bedroom, xxx Allerman "
                      "Dr, $70,000; no unit wording"},
    "23-230": {"counts": False, "component": "second_dwelling", "units": 1,
               "why": "unconfirmed: 2023-10 'New home' (code 101) on a River Dr parcel that had a shed permit "
                      "in 2023-05; no demolition permit found; probably a vacant lot with a shed"},
    "25-044": {"counts": False, "component": None,
               "why": "new SFD after its own early-start (footing) permit 25-026 on the same parcel: same house"},
    "25-067": {"counts": False, "component": None,
               "why": "new SFD after its own early-start permit 25-027: same house"},
    "25-068": {"counts": False, "component": None,
               "why": "new SFD after its own early-start permit 25-028: same house"},
    "25-049": {"counts": False, "component": None,
               "why": "re-issue: same parcel and address had 'New SFD' 24-299 three months earlier"},
    "25-050": {"counts": False, "component": None,
               "why": "re-issue: same parcel and address had 'New SFD' 24-298 three months earlier"},
    "25-051": {"counts": False, "component": None,
               "why": "re-issue: same parcel had 'New SFD' 24-297 three months earlier"},
    "23-131": {"counts": False, "component": None,
               "why": "2023 '2 apartments' (code 434) on N. Water St (downtown mixed-use): work on apartments "
                      "in an existing multi-unit building, not a second home on a single-family lot"},
    "24-023": {"counts": False, "component": None, "why": "renovation of an existing upstairs apartment"},
    "25-019": {"counts": False, "component": None, "why": "duplex converted to single family (unit loss)"},
    "25-080": {"counts": False, "component": None,
               "why": "2nd story on garage + breezeway to house; no kitchen or unit wording"},
    "24-080": {"counts": False, "component": None, "why": "garage addition and kitchen remodel; no unit"},
}


def classify_records(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    for col in ("description", "permit_type", "parcel_id"):
        df[col] = df[col].astype(object).where(df[col].notna(), None)
    # earlier permits on the same parcel (within the 2023+ window only)
    first_seen = df.dropna(subset=["parcel_id"]).groupby("parcel_id")["date"].min()
    comp, units, reason, cand = [], [], [], []
    for r in df.itertuples():
        d = r.description or ""
        c, note = classify.text_class(d)
        rs, cd = "", False
        if c == "adu_legalization":
            rs, cd, c = "legalization of existing unit (excluded)", True, None
        elif c:
            rs, cd = f"ADU text ({note})", True
        elif classify.SF_TO_TWO_RE.search(d):
            c, rs, cd = "sf_to_duplex", "text: single-family to two-family", True
        else:
            c = None
            if note:
                rs, cd = note, True
            if r.permit_type in NEW_DWELLING_CODES and r.permit_type != "101":
                rs, cd = f"new attached/two-family/multifamily building, code {r.permit_type} (excluded: own lot, not a second home)", True
            elif r.permit_type == "101" and r.parcel_id and first_seen.get(r.parcel_id, r.date) < r.date:
                rs, cd = "unconfirmed: new single-family on a parcel with an earlier permit", True
            elif r.permit_type in ("434", "438", None, "") and (CAND_RE.search(d) or re.search(
                    r"(?i)(?:2nd|second)\s+stor|upstairs|above\s+garage|garage.*(?:suite|living)", d)):
                rs, cd = "unit/kitchen wording in residential alteration (reviewed)", True
        comp.append(c)
        units.append(1 if c else 0)
        reason.append(rs)
        cand.append(cd)
    df["component"], df["units"], df["reason"], df["candidate"] = comp, units, reason, cand
    for pid, j in JUDGMENTS.items():
        m = df.permit_id == pid
        if not m.any():
            continue
        df.loc[m, "candidate"] = True
        df.loc[m, "reason"] = "judgment: " + j["why"]
        df.loc[m, "component"] = j["component"] if j["counts"] else None
        df.loc[m, "units"] = j.get("units", 1) if j["counts"] else 0
    df["units"] = df["units"].astype(int)
    return df
