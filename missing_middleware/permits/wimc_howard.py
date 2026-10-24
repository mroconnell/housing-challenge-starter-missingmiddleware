"""Howard village (Brown/Outagamie counties, WI): monthly "Permit Activity Report" PDFs.

Source: the village Archive Center (AMID=41), one PDF per month from Jan 2012. Each file
has a summary page (counts, costs, dwelling units by building type) followed by a
"PERMIT LOG" table: permit #, date issued, job address, parcel #, job description,
owner's name, applicant's name, permits issued (BLDG/ELEC/PLBG/HVAC/OTHER), project cost,
fees. Plain HTTP GET only.

Text is extracted with poppler's `pdftotext -layout` (system binary). Table columns
are left-aligned per page, so each page's column starts are measured from the rows
that split cleanly on runs of 2+ spaces, then every row is cut at those columns.
Owner and applicant names are never returned by `load()`.

Howard does not allow ADUs (accessory buildings may not be living space), so the
expected count is zero; the classifier still looks for ADU words, duplex/two-family
conversions, apartments/living quarters, and new single-family dwellings on parcels
with earlier permits (evidence of a house already on the lot).
"""
from __future__ import annotations

import re
import subprocess
from pathlib import Path

import pandas as pd

from . import classify
from . import fetch_util as fu

META = {
    "slug": "howard",
    "place": "Howard village",
    "geoids": ["5500935950", "5508735950"],
    "source_url": "https://www.villageofhoward.com/Archive.aspx?AMID=41",
    "source_desc": "monthly Permit Activity Report PDFs (permit log) from the village Archive Center",
    "stage": "issued",
    "license": "public record (no stated licence)",
    "method": ("text rule (classify.text_class / SF_TO_TWO_RE / apartment, living-quarters words) on the "
               "job description, plus parcel history: a New Single Family Dwelling or duplex on a parcel "
               "with earlier permits is a candidate; every candidate judged by hand."),
}

BASE = "https://www.villageofhoward.com"
INDEX_URL = BASE + "/Archive.aspx?AMID=41"
FILE_URL = BASE + "/ArchiveCenter/ViewFile/Item/{adid}"
FIRST_YM, LAST_YM = "201201", "202512"  # earlier years are kept as prior-dwelling evidence
YEARS = (2022, 2023, 2024, 2025)

ROW_RE = re.compile(r"^\s*(\d{4}-\d{1,4}[A-Za-z]?)\s+(\d{1,2}/\d{1,2}/\d{2,4})\s+(.*)$")
GAP_RE = re.compile(r"\S(?:.*?\S)?(?=\s{2,}|$)")
MONEY_RE = re.compile(r"\$?-?[\d,]+(?:\.\d\d)?\s*$")


# ---------------------------------------------------------------- download
def _index(log=print) -> list[tuple[str, int]]:
    html = fu.get(INDEX_URL).decode("utf-8", "replace")
    out = []
    for m in re.finditer(r'ADID=(\d+)"[^>]*>(.*?)</a>', html, re.S):
        title = re.sub(r"<[^>]+>", "", m.group(2)).strip()
        ym = re.match(r"(\d{6})\s", title)
        if ym and FIRST_YM <= ym.group(1) <= LAST_YM:
            out.append((ym.group(1), int(m.group(1))))
    return sorted(out)


def fetch(raw_dir: Path, log=print) -> dict:
    raw_dir = Path(raw_dir)
    raw_dir.mkdir(parents=True, exist_ok=True)
    man_path = raw_dir / "manifest.json"
    old = {e["file"]: e for e in fu.read_manifest(man_path).get("files", [])}
    pdfs = sorted(raw_dir.glob("*.pdf"))
    need_index = not pdfs or not any(p.name.startswith(LAST_YM) for p in pdfs)
    items = _index(log) if need_index else [(e["file"][:6], e["adid"]) for e in old.values()]
    entries = []
    for ym, adid in items:
        name = f"{ym}_{adid}.pdf"
        path = raw_dir / name
        url = FILE_URL.format(adid=adid)
        if not path.exists():
            log(f"howard: GET {url}")
            data = fu.get(url)
            if not data.startswith(b"%PDF"):
                raise RuntimeError(f"not a PDF: {url}")
            path.write_bytes(data)
            accessed = fu.now_iso()
        else:
            accessed = old.get(name, {}).get("accessed") or fu.now_iso()
        entries.append({"file": name, "adid": adid, "url": url, "accessed": accessed,
                        "sha256": old.get(name, {}).get("sha256") or fu.sha256_file(path)})
    fu.write_manifest(man_path, entries, {"source": META["source_url"], "license": META["license"],
                                          "note": "raw PDFs contain owner/applicant names; never leave data/raw"})
    return fu.read_manifest(man_path)


# ---------------------------------------------------------------- parse
def _pdftext(path: Path) -> str:
    try:
        return subprocess.run(["pdftotext", "-layout", str(path), "-"], check=True,
                              capture_output=True, text=True).stdout
    except FileNotFoundError as exc:  # pragma: no cover
        raise RuntimeError("poppler `pdftotext` is required to read the Howard PDFs") from exc


def _fields(line: str) -> list[tuple[int, str]]:
    return [(m.start(), m.group(0)) for m in GAP_RE.finditer(line)]


def _cut_left(ln: str, a: int, b: int) -> str:
    """Text in [a, b); if b falls inside a word (owner name abutting a truncated description
    with one space), back off to the previous space so no name fragment is kept."""
    while b > a and ln[b - 1] != " " and b < len(ln) and ln[b] != " ":
        b -= 1
    return ln[a:b].strip()


def _parse_page(lines: list[str]) -> list[dict]:
    rows = [ln for ln in lines if ROW_RE.match(ln)]
    if not rows:
        return []
    # clean rows: num, date, addr, parcel, desc, owner, applicant, permits, cost, fees
    starts = [[], [], [], [], []]  # addr, parcel, desc, owner, permits
    for ln in rows:
        f = _fields(ln)
        if len(f) == 10:
            for k, i in enumerate((2, 3, 4, 5, 7)):
                starts[k].append(f[i][0])
    if not starts[2]:
        return []
    med = lambda v: int(pd.Series(v).median())  # noqa: E731
    c_addr, c_parcel, c_desc, c_permits = med(starts[0]), med(starts[1]), med(starts[2]), med(starts[4])
    # owner column: smallest start seen in clean rows (left-aligned column), but after desc
    c_owner = min(s for s in starts[3] if s > c_desc)
    out = []
    for ln in rows:
        m = ROW_RE.match(ln)
        ln = ln.ljust(c_permits + 40)
        tail = ln[c_permits:].strip()
        money = re.findall(r"\$\s?-?[\d,]+(?:\.\d\d)?", tail)
        permits = re.split(r"\s{2,}|\s\$", tail)[0].strip() if tail else ""
        if permits.startswith("$"):
            permits = ""
        out.append({
            "permit_id": m.group(1),
            "date_s": m.group(2),
            "address": ln[c_addr:c_parcel].strip(),
            "parcel_id": ln[c_parcel:c_desc].strip(),
            "description": _cut_left(ln, c_desc, c_owner),
            "permit_type": permits,
            "cost": money[0] if money else None,
        })
    return out


def _parse_file(path: Path) -> list[dict]:
    text = _pdftext(path)
    recs = []
    for page in text.split("\f"):
        if "PERMIT LOG" not in page:
            continue
        for r in _parse_page(page.splitlines()):
            r["source_file"] = path.name
            recs.append(r)
    return recs


def _split_addr(addr: str) -> tuple[str, str]:
    m = re.match(r"^\s*(\d+(?:-\d+)?(?:\s*[A-Z])?)\s+(.*)$", addr or "")
    if not m:
        return "", (addr or "").strip()
    street = re.sub(r"\s*#\s*\S+$", "", m.group(2)).strip()
    return m.group(1).strip(), street


OCR_DATE_RE = re.compile(r"(?:(\d{4}-\d{1,4})\D{1,6})?\b(\d{1,2}/\d{1,2}/20\d\d)\b[\s\-—|]*(.*)$")


def _ocr_file(path: Path, vocab: list[str]) -> list[dict]:
    """Image-only month (Oct 2024 is a scanned print): OCR with tesseract when installed.

    OCR text loses the column layout, so the description is kept only when it matches a
    description string seen in the text-layer months (`vocab`, longest first); otherwise
    it is set to "UNREADABLE (OCR)". This keeps owner/applicant names (which follow the
    description) out of the output. Rows whose permit number the OCR missed get a
    synthetic id `<year>-ocr<NN>`.
    """
    import shutil
    import tempfile
    if not (shutil.which("tesseract") and shutil.which("pdftoppm")):
        return []
    recs = []
    with tempfile.TemporaryDirectory() as td:
        subprocess.run(["pdftoppm", "-r", "300", "-gray", str(path), f"{td}/p"], check=True)
        text = ""
        for img in sorted(Path(td).glob("p-*")):
            text += subprocess.run(["tesseract", str(img), "-", "--psm", "6"], capture_output=True,
                                   text=True).stdout + "\n"
    n = 0
    for ln in text.splitlines():
        m = OCR_DATE_RE.search(ln)
        if not m or "PERMIT LOG" in ln:
            continue
        rest = m.group(3)
        desc, pos = None, -1
        for v in vocab:
            pos = rest.lower().find(v.lower())
            if pos > 0:
                desc = v
                break
        pre = rest[:pos].split() if desc else rest.split()[:4]
        parcel = pre[-1] if desc and pre else ""
        addr = " ".join(pre[:-1]) if desc else ""
        n += 1
        pid = m.group(1) or f"{m.group(2)[-4:]}-ocr{n:02d}"
        recs.append({"permit_id": pid, "date_s": m.group(2), "address": addr, "parcel_id": parcel,
                     "description": desc or "UNREADABLE (OCR)", "permit_type": "", "cost": None,
                     "source_file": path.name})
    return recs


def load(raw_dir: Path) -> pd.DataFrame:
    raw_dir = Path(raw_dir)
    recs, image_only = [], []
    for p in sorted(raw_dir.glob("*.pdf")):
        r = _parse_file(p)
        if not r and len(_pdftext(p).strip()) < 50:
            image_only.append(p)
        recs.extend(r)
    if image_only:
        vc = pd.Series([r["description"] for r in recs]).value_counts()
        vocab = sorted([d for d, k in vc.items() if k >= 3 and len(d) >= 5], key=len, reverse=True)
        for p in image_only:
            recs.extend(_ocr_file(p, vocab))
    df = pd.DataFrame(recs)
    df["date"] = pd.to_datetime(df["date_s"], format="mixed", errors="coerce")
    # permit numbers carry the year; fix obvious date typos by that year
    py = df["permit_id"].str[:4].astype(int)
    df["year"] = df["date"].dt.year.where(df["date"].dt.year == py, py).astype(int)
    df["month_file"] = df["source_file"].str[:6]
    hs = df["address"].map(_split_addr)
    df["house_nbr"] = [h for h, _ in hs]
    df["street"] = [s for _, s in hs]
    df["units_raw"] = float("nan")
    df["parcel_id"] = df["parcel_id"].replace("", pd.NA)
    df = df.drop_duplicates(["permit_id", "description", "parcel_id"])
    cols = ["permit_id", "date", "year", "permit_type", "description", "units_raw", "parcel_id",
            "street", "house_nbr", "month_file", "cost"]
    return df[cols].reset_index(drop=True)


def coverage(df: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for y in YEARS:
        months = sorted({m for m in df["month_file"] if m.startswith(str(y))})
        n = int((df["year"] == y).sum())
        miss = [f"{y}{mm:02d}" for mm in range(1, 13) if f"{y}{mm:02d}" not in months]
        note = "all 12 monthly permit logs" if not miss else "missing " + ",".join(miss)
        ocr = sorted({m for m in df.loc[df["permit_id"].str.contains("ocr") | df["description"].eq("UNREADABLE (OCR)")
                                        | df["permit_type"].eq(""), "month_file"] if m.startswith(str(y))})
        if f"{y}10" in ocr and y == 2024:
            note += ("; 202410 is an image-only scan, read by OCR (descriptions kept only when they match "
                     "the known description list) and hand-reviewed: no unit/ADU/duplex wording")
        rows.append({"year": y, "months_with_records": len(months), "records": n,
                     "complete": len(months) == 12, "note": note})
    return pd.DataFrame(rows)


# ---------------------------------------------------------------- classify
APT_RE = re.compile(r"apartment|\bapt\b|living\s+(?:quarters|space|unit)|in-?law|second\s+(?:dwelling|unit|kitchen)"
                    r"|\bkitchen(?:ette)?\b.*(?:basement|garage|accessory)|two[- ]?family|duplex|\btwin\b"
                    r"|\bunit\s+(?:added|addition)|add\w*\s+(?:a\s+)?unit|convert", re.I)
NEW_SFD_RE = re.compile(r"new\s+single\s+family|new\s+(?:sfd|home|house|dwelling)|new\s+duplex|new\s+two", re.I)
# work on an existing house: evidence that the parcel already had a dwelling
EXISTING_WORK_RE = re.compile(r"furnace|water\s+heater|\bac\b|re-?roof|roof|window|siding|basement|bath|kitchen"
                              r"|deck|remodel|electrical\s+service|generator|addition|alteration", re.I)


def classify_records(df: pd.DataFrame) -> pd.DataFrame:
    out = df.copy()
    out["component"] = None
    out["units"] = 0
    out["reason"] = ""
    out["candidate"] = False
    desc = out["description"].fillna("")
    # parcel history (all years 2012+)
    by_parcel = {k: g for k, g in out[out["parcel_id"].notna()].groupby("parcel_id")}
    for idx, r in out.iterrows():
        d = desc.at[idx]
        cat, note = classify.text_class(d)
        if cat == "adu_legalization":
            out.at[idx, "candidate"] = True
            out.at[idx, "reason"] = "ADU legalization (excluded)"
            continue
        if cat:
            out.loc[idx, ["component", "units", "candidate", "reason"]] = [cat, 1, True, "ADU text rule"]
            continue
        if note:
            out.loc[idx, ["candidate", "reason"]] = [True, f"ADU word excluded ({note})"]
        if classify.SF_TO_TWO_RE.search(d):
            out.loc[idx, ["component", "units", "candidate", "reason"]] = ["sf_to_duplex", 1, True,
                                                                          "single-family to two-unit text"]
            continue
        if APT_RE.search(d):
            out.loc[idx, ["candidate", "reason"]] = [True, "unit-related words; not a new unit on review"]
        if NEW_SFD_RE.search(d) and pd.notna(r.parcel_id):
            g = by_parcel.get(r.parcel_id)
            prior = g[(g["date"] < r.date) & (g.index != idx)] if g is not None else g
            if prior is not None and len(prior):
                ex = prior[prior["description"].fillna("").str.contains(EXISTING_WORK_RE)
                           & ~prior["description"].fillna("").str.contains(NEW_SFD_RE)]
                earlier_new = prior[prior["description"].fillna("").str.contains(NEW_SFD_RE)]
                out.at[idx, "candidate"] = True
                out.at[idx, "reason"] = (f"new dwelling on parcel with {len(prior)} earlier permit(s) "
                                         f"({len(ex)} existing-house work, {len(earlier_new)} new-dwelling); "
                                         "unconfirmed")
    for pid, j in JUDGMENTS.items():
        m = out["permit_id"] == pid
        if not m.any():
            continue
        out.loc[m, "candidate"] = True
        if j["counts"]:
            out.loc[m, "component"] = j["component"]
            out.loc[m, "units"] = j.get("units", 1)
        else:
            out.loc[m, "component"] = None
            out.loc[m, "units"] = 0
        out.loc[m, "reason"] = "judged: " + j["why"]
    out["units"] = out["units"].astype(int)
    return out


JUDGMENTS: dict[str, dict] = {
    # parcel number shared with an earlier new house at a DIFFERENT address: new-subdivision lots
    # (parcel # typo or a parent parcel number before the plat split); each is a first house on its lot
    "2022-109": {"counts": False, "why": "new SFD at xxx Crescent Hill; the earlier permit on this parcel # is a different address (subdivision lot), no house on this lot before"},
    "2022-110": {"counts": False, "why": "new SFD at xxx Crescent Hill; the earlier permit on this parcel # is a different address (subdivision lot), no house on this lot before"},
    "2023-017": {"counts": False, "why": "new SFD at xxx Paul Court; the earlier permit on this parcel # is a different address (subdivision lot), no house on this lot before"},
    "2023-028": {"counts": False, "why": "new SFD at xxx Hidden Creek Trail; the earlier permit on this parcel # is a different address (subdivision lot), no house on this lot before"},
    "2023-076": {"counts": False, "why": "new SFD at xxx Hidden Creek Trail; the earlier permit on this parcel # is a different address (subdivision lot), no house on this lot before"},
    "2023-458": {"counts": False, "why": "new SFD at xxx Brussels Way; the earlier permit on this parcel # is a different address (subdivision lot), no house on this lot before"},
    "2024-014": {"counts": False, "why": "new SFD at xxx Rainbow Court; the earlier permit on this parcel # is a different address (subdivision lot), no house on this lot before"},
    "2024-165": {"counts": False, "why": "new SFD at xxx Antwerp Avenue; the earlier permit on this parcel # is a different address (subdivision lot), no house on this lot before"},
    "2024-194": {"counts": False, "why": "new SFD at xxx Antwerp Ave; the earlier permit on this parcel # is a different address (subdivision lot), no house on this lot before"},
    "2025-195": {"counts": False, "why": "new SFD at xxx Antwerp Avenue; the earlier permit on this parcel # is a different address (subdivision lot), no house on this lot before"},
    "2025-469": {"counts": False, "why": "new SFD at xxx Glendale Avenue; the earlier permit on this parcel # is a different address (subdivision lot), no house on this lot before"},
    "2022-067": {"counts": False, "why": "new SFD at xxx Coral Reef Lane; only earlier permit is a $700 cable/electrical service (2018) on the vacant lot; first house"},
    "2023-050": {"counts": False, "why": "new SFD at xxx Woodland Ridge; only earlier permit is erosion control (vacant lot)"},
    "2025-541": {"counts": False, "why": "new SFD at xxx Shawano Avenue; only earlier permit is erosion control (vacant lot)"},
    "2023-210": {"counts": False, "why": "new SFD at xxx Lone Grove Avenue; prior house demolished/moved off in 2012: rebuild, not a second dwelling"},
    "2024-114": {"counts": False, "why": "new SFD at xxx Shawano Avenue; prior home demolished 2020 (permit 2020-425): teardown-and-rebuild"},
    "2024-126": {"counts": False, "why": "new SFD at xxx Lincoln Ridge; a 2020 SFD permit on the lot was evidently never built (erosion control re-permitted Jan 2024, new owner): replacement permit, one house"},
    "2025-528": {"counts": False, "why": "new SFD at xxx Pinecrest Road; same owner/applicant re-permitted a larger house ($400k 2023 -> $833k 2025) with no work in between: re-permit, one house"},
    "2022-648": {"counts": False, "why": "unconfirmed: second New SFD permit at the same address xxx Stone Ridge Dr (2019 $189k by a builder; 2022 $114.5k, lower fee, new owner); no intermediate permits; could be a re-permit or a second building - upper bound only"},
    "2025-044": {"counts": False, "why": "'New Duplex' at xxx Tony Lane is a PLBG-only $12.9k permit; the Dec 2025 summary shows 0 new duplexes and 0 two-family units in 2025: plumbing work at an existing duplex, not a new unit"},
    "2022-114": {"counts": False, "why": "relocated (moved-in) single-family house onto xxx Linden Hills; no earlier permit on the lot; one house"},
}

# record left as the upper bound (not counted): permit_id -> units
UNCONFIRMED = {"2022-648": 1}
