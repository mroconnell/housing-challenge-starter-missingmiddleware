"""Kaukauna, WI (city, Outagamie/Calumet) adapter: monthly Building Inspection Reports in Common
Council packets.

kaukauna.gov sits behind a Cloudflare JavaScript challenge (HTTP 403 to plain clients), but the
council's agendas are published on Municode Meetings (kaukauna-wi.municodemeetings.com). Each
meeting page is a plain GET; its accessible-HTML agenda (meetings.municode.com/adaHtmlDocument)
links every agenda item's attachment on a public Azure blob. The "Building Inspection Report"
item (on the second council meeting of most months) is a short PDF listing the permits issued in
the previous month. Only those attachments are downloaded.

The report is an export from the city's permit software and its layout changed many times:
- Jul 2021 - Mar 2022: "Monthly Building Permit Summary" (project type, address, project
  number such as ELEC - 21 - 0978, issued date, business, fees, cost);
- Apr 2022 - Dec 2022: same title from a newer system (template name, permit number 22-000123,
  address, contacts, issued date, fees, cost);
- Jan 2023 onward: Wisconsin-style permit list (permit number KU-2023-123, municipal address,
  category, work type, work target, applicant, owner, issued date ...), sometimes printed with
  the columns spread across successive pages, sometimes as a scanned image (OCR with
  tesseract), and in a few months as "Submitted applications" instead of issued permits.

There is no free-text description. The only unit signal is the work target (e.g. "Single-family
dwelling", "Additional dwelling unit") from 2023 on, and the template ("New Home Permit",
"New Duplex Permit") before. Records are cut at permit-number anchors (or address lines in the
2023 address-led layouts); fields are taken from a closed vocabulary, so applicant and owner names
never enter the output. Counts of records per month are approximate where the layout wraps.
"""
from __future__ import annotations

import html
import json
import re
import subprocess
import tempfile
import urllib.request
from collections import Counter
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
from pathlib import Path

import numpy as np
import pandas as pd

from . import classify
from . import fetch_util as fu

META = {
    "slug": "kaukauna",
    "place": "Kaukauna city",
    "geoids": ["5508738800", "5501538800"],
    "source_url": "https://kaukauna-wi.municodemeetings.com/",
    "source_desc": "monthly Building Inspection Report attachments to Common Council agendas (Municode Meetings)",
    "stage": "issued",
    "license": "public record (no stated licence)",
    "method": ("No descriptions: work target 'Additional dwelling unit' (2023+) is the second-home "
               "signal; new-dwelling records at an address with an earlier dwelling are candidates; "
               "every candidate hand-reviewed in JUDGMENTS."),
}

PORTAL = "https://kaukauna-wi.municodemeetings.com/bc-commoncouncil/page/"
ADA = "https://meetings.municode.com/adaHtmlDocument/index?cc=KAUKAUNAWI&me={mid}&ip=True"
SERIES = {"common-council": 130, "amended-common-council": 60, "common-council-meeting": 30,
          "amended-common-council-meeting": 30}
FIRST, LAST = datetime(2021, 12, 15), datetime(2026, 3, 1)  # meetings carrying Dec 2021 .. Jan 2026 reports


# ------------------------------------------------------------------ fetch
def _get_text(url: str) -> str | None:
    req = urllib.request.Request(url, headers={"User-Agent": fu.USER_AGENT})
    try:
        with urllib.request.urlopen(req, timeout=90) as r:
            return r.read().decode("utf8", "replace")
    except Exception:
        return None


def _meeting(slug: str) -> dict | None:
    h = _get_text(PORTAL + slug)
    if not h:
        return None
    t = re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", h))
    m = re.search(r"(?:Monday|Tuesday|Wednesday|Thursday|Friday|Saturday|Sunday), (\w+ \d+, \d{4})", t)
    pk = re.search(r"MEET-Packet-(\w+)\.pdf", h)
    if not (m and pk):
        return None
    return {"slug": slug, "date": datetime.strptime(m.group(1), "%B %d, %Y").date().isoformat(),
            "meeting_id": pk.group(1), "page": PORTAL + slug}


def _bi_attachments(mid: str) -> list[tuple[str, str]]:
    h = _get_text(ADA.format(mid=mid)) or ""
    t = re.sub(r"<(?!a |/a)[^>]+>", " ", h)
    out = []
    for m in re.finditer(r'([^<>]{0,200})<a [^>]*href="([^"]+ITEM-Attachment[^"]+)"[^>]*>([^<]*)', t):
        ctx = html.unescape(re.sub(r"\s+", " ", m.group(1)))
        if re.search(r"Building Inspection Report", ctx, re.I):
            out.append((m.group(2), html.unescape(m.group(3)).strip()))
    return out


def fetch(raw_dir: Path, log=print) -> dict:
    raw_dir = Path(raw_dir)
    raw_dir.mkdir(parents=True, exist_ok=True)
    man_path = raw_dir / "manifest.json"
    manifest = fu.read_manifest(man_path)
    if manifest.get("files") and all((raw_dir / e["file"]).exists() for e in manifest["files"]):
        return manifest
    slugs = []
    for base, n in SERIES.items():
        slugs += [base] + [f"{base}-{i}" for i in range(n)]
    with ThreadPoolExecutor(8) as ex:
        meetings = [m for m in ex.map(_meeting, slugs) if m]
    meetings = [m for m in meetings
                if FIRST.date().isoformat() <= m["date"] <= LAST.date().isoformat()]
    meetings = list({m["meeting_id"]: m for m in meetings}.values())
    log(f"kaukauna: {len(meetings)} council meetings in window")
    entries = []
    for m in sorted(meetings, key=lambda m: m["date"]):
        for k, (url, name) in enumerate(_bi_attachments(m["meeting_id"])):
            fname = f"{m['date']}_{m['slug']}_{k}.pdf"
            dest = raw_dir / fname
            if not dest.exists():
                dest.write_bytes(fu.get(url))
            entries.append({"file": fname, "url": url, "attachment_name": name, "meeting_date": m["date"],
                            "meeting_page": m["page"], "accessed": fu.now_iso(),
                            "sha256": fu.sha256_file(dest)})
    (raw_dir / "meetings.json").write_text(json.dumps(meetings, indent=1))
    meta = {k: META[k] for k in ("place", "source_url", "license")}
    meta["note"] = "kaukauna.gov returns a Cloudflare challenge; packets read from Municode Meetings"
    fu.write_manifest(man_path, entries, meta)
    return fu.read_manifest(man_path)


# ------------------------------------------------------------------ text
def _pages_text(pdf: Path) -> list[str]:
    n = int(re.search(r"Pages:\s+(\d+)", subprocess.run(["pdfinfo", str(pdf)], capture_output=True,
                                                        text=True).stdout).group(1))
    pages = [subprocess.run(["pdftotext", "-layout", "-f", str(p), "-l", str(p), str(pdf), "-"],
                            capture_output=True, text=True).stdout for p in range(1, n + 1)]
    if sum(len(p.strip()) for p in pages) > 200:
        return [p.replace("‐", "-").replace("‑", "-") for p in pages]
    return _ocr_pages(pdf, n)


def _ocr_score(txt: str) -> int:
    """Readable orientation: permit numbers, dates and common report words."""
    return (100 * len(re.findall(r"KU-\d{4}-\d+", txt)) + 10 * len(re.findall(r"\b2[1-6]-\d{2}-\d{2}\b", txt))
            + len(re.findall(r"\b(?:New|Remodel|Repair|Replacement|Other|Service|Fence|Plumbing|Electrical|HVAC"
                             r"|Brett|Jensen|Permit|issued|dwelling|Single-family)\b", txt)))


def _ocr_pages(pdf: Path, n: int) -> list[str]:
    """Scanned report: OCR each page at the rotation that yields the most permit numbers."""
    cache = pdf.with_suffix(".ocr.json")
    if cache.exists():
        return json.loads(cache.read_text())
    out = []
    with tempfile.TemporaryDirectory() as td:
        subprocess.run(["pdftoppm", "-r", "250", "-png", str(pdf), f"{td}/p"], check=True)
        for img in sorted(Path(td).glob("p-*.png")):
            best = ""
            for rot in (0, 90, 270):
                src = img
                if rot:
                    src = Path(td) / f"r{rot}_{img.name}"
                    src.write_bytes(img.read_bytes())
                    subprocess.run(["sips", "-r", str(rot), str(src)], capture_output=True)
                txt = subprocess.run(["tesseract", str(src), "-", "--psm", "6"], capture_output=True,
                                     text=True).stdout
                if _ocr_score(txt) > _ocr_score(best):
                    best = txt
            out.append(best)
    cache.write_text(json.dumps(out))
    return out


# ------------------------------------------------------------------ vocabulary
CATEGORY_RE = re.compile(
    r"Residential\s*building|Residential\b|Commercial\s*building|Accessory\s*structures|Other\s*structures"
    r"|Storm\s*Sewer|Plumbing|Electrical|HVAC|Signs|Pools|Driveway/?\s*Culvert|Demolition|Erosion\s*control", re.I)
TEMPLATE_RE = re.compile(
    r"New\s+Home|New\s+Duplex|New\s+Multi[- ]?Family|Residential\s+Add-?\s*On|Commercial\s+Add-?\s*On"
    r"|New\s+Commercial|Accessory\s+(?:Structure|Building)|Electrical|Plumbing|Mechanical|Lateral|Fence"
    r"|Sign|Demolition|Driveway|Pool|Siding|Roof|Deck|Chicken|Fire|Window|Sidewalk", re.I)
WORKTYPE_RE = re.compile(r"\b(New|Remodel|Repair|Replacement|Addition|Additional|Finished\s+Basement"
                         r"|Alteration|Conversion|Change\s+of\s+use|Demolition)\b", re.I)
TARGET_RE = re.compile(
    r"\b(?:Additional\s+dwelling(?:\s+unit)?|Single[- ]family\s+dw\w*|Two[- ]family\s+dw\w*|Multi[- ]family\s*\w*"
    r"|Recreational\s+dwelling|Manufactured\s+home|Duplex|Apartment|Townhouse|Condominium|Garage"
    r"|Deck|Porch|Shed|Fence|Gazebo|Pool|Office\s+Building|Retail|Warehouse)\b", re.I)
DWELLING_TARGET_RE = re.compile(r"dwelling|duplex|apartment|manufactured|townhouse|multi[- ]family|New\s+Home", re.I)
ID_RES = [
    re.compile(r"KU-\s?\d{4}-\s?\d+"),
    re.compile(r"\b[A-Z]{3,5}\s*-\s*\d{2}\s*-\s*\d{3,5}\b"),  # 2021-22 project numbers
    re.compile(r"\b2[1-6]-\d{6}\b"),
]
DATE_RES = [(re.compile(r"\b(\d{2}/\d{2}/\d{4})\b"), "%m/%d/%Y"),
            (re.compile(r"\b(\d{1,2}/\d{1,2}/\d{2})\b"), "%m/%d/%y"),
            (re.compile(r"\b(2[1-6]-\d{2}-\d{2})\b"), "%y-%m-%d")]
ADDR_RE = re.compile(r"^(\d{1,5}(?:-\d{1,5})?[A-Z]?)\s+((?:[NSEW]\.?\s+)?[A-Z0-9][A-Za-z0-9.']*(?:\s[A-Za-z0-9.']+){0,3})")
STREET_SUFFIX = re.compile(r"\b(ST|AV|AVE|RD|DR|LA|LN|CT|PL|WAY|TR|TRL|CI|CIR|BLVD|PKWY|HWY|LANE|DRIVE|STREET|ROAD|AVENUE|COURT)\b\.?", re.I)


def _find_date(s: str):
    for rx, fmt in DATE_RES:
        m = rx.search(s)
        if m:
            try:
                return datetime.strptime(m.group(1), fmt)
            except ValueError:
                continue
    return None


def _clean_street(s: str | None) -> str | None:
    if not s:
        return None
    s = re.sub(r"\s+", " ", s).strip().upper().rstrip(".,")
    m = STREET_SUFFIX.search(s)
    # no street suffix: return nothing rather than risk a person's name
    return s[: m.end()].rstrip(".") if m else None


def _anchor_lines(lines: list[str]) -> list[tuple[int, str | None]]:
    """(line index, permit id or None). Address-led layouts have no permit number."""
    out = []
    for i, line in enumerate(lines):
        for rx in ID_RES:
            m = rx.search(line)
            if m:
                out.append((i, re.sub(r"\s+", "", m.group(0))))
                break
    if out:
        # 2022 layout wraps "22-" / "000666" across two lines
        return out
    wrapped = []
    for i, line in enumerate(lines[:-1]):
        m = re.search(r"\b(2[1-6])-\s*$|\b(2[1-6])-\s{2,}", line)
        if m:
            col = m.start()
            nxt = lines[i + 1][max(0, col - 2): col + 10]
            m2 = re.search(r"\d{6}", nxt)
            if m2:
                wrapped.append((i, f"{m.group(1) or m.group(2)}-{m2.group(0)}"))
    if wrapped:
        return wrapped
    for i, line in enumerate(lines):
        if ADDR_RE.match(line) and not re.match(r"^\d{1,2}/", line):
            out.append((i, None))
    return out


def _address_columns(lines: list[str]) -> tuple[int, int] | None:
    """Character span of the address column in the 2021-22 layouts (from the header line)."""
    for l in lines[:15]:
        m = re.search(r"Short Address", l)
        if m:
            n = l.find("Project Number")
            return (max(0, m.start() - 2), n - 1 if n > 0 else m.end() + 12)
        m = re.search(r"NUMBER\s+ADDRESS", l)
        if m:
            a = l.find("ADDRESS", m.start())
            c = l.find("PROJECT CONTACTS")
            return (max(0, a - 1), c - 1 if c > 0 else a + 18)
    return None


HEADER_WORDS_RE = re.compile(r"^\s*(?:Permit number|Municipal|Work type|Work target|Applicant|Issued|Owner|Status"
                             r"|Category|Legal address|Completion|Cost|Valuation)\b", re.I)


def _cont_fields(line: str) -> dict:
    wt = WORKTYPE_RE.match(line.strip())
    tm = TARGET_RE.search(line)
    return {"work_type": wt.group(1) if wt else None, "target": tm.group(0) if tm else None,
            "date": _find_date(line)}


def _parse_report(pdf: Path) -> list[dict]:
    pages = _pages_text(pdf)
    recs, page_recs, cont_pages = [], [], []
    addr_cols_prev = None
    for pno, page in enumerate(pages):
        lines = [l for l in page.splitlines() if l.strip()]
        lines = [l for l in lines if not re.search(r"Item \d+\.[a-z]\.|^\s*\d{1,3}\s*$", l)]
        anchors = _anchor_lines(lines)
        addr_cols = _address_columns(lines) or addr_cols_prev
        addr_cols_prev = addr_cols
        if not anchors:
            # continuation page of a report printed column-group by column-group
            cont_pages.append(lines[1:] if lines and HEADER_WORDS_RE.match(lines[0]) else lines)
            continue
        this = []
        for k, (i, pid) in enumerate(anchors):
            end = anchors[k + 1][0] if k + 1 < len(anchors) else len(lines)
            start = i
            # address-led layouts put part of a record on the lines above the anchor
            if pid is None:
                # the record is the anchor line plus up to 3 lines above it; lines below
                # already belong to the next record
                prev_end = anchors[k - 1][0] + 1 if k else 0
                start = max(prev_end, i - 3)
                end = i + 1
            block = lines[start:end]
            text = " ".join(block)
            line = lines[i]
            addr_src = line
            if pid:
                pos = re.search(re.escape(pid[:3]), line)
                addr_src = line[pos.start():] if pos else line
                addr_src = re.sub(r"^\S+(?:\s*-\s*\S+){0,2}\s+", "", addr_src.strip())
                if pid[:2].isdigit() or re.match(r"[A-Z]{3,5}-", pid):
                    # 2021-22 layouts: the address has its own column (often wrapped); cut by position
                    addr_src = ""
                    if addr_cols:
                        a0, a1 = addr_cols
                        lo = max(0, i - 1) if re.match(r"[A-Z]{3,5}-", pid) else i
                        parts = [l[a0:a1].strip() for l in lines[lo:min(end, i + 4)]]
                        addr_src = " ".join(p for p in parts if p)
                        m = re.search(r"\d{1,5}(?:-\d{1,5})?\s+\S.*", addr_src)
                        addr_src = m.group(0) if m else ""
            ma = ADDR_RE.match(addr_src.strip()) or re.match(r"(\d{1,5}(?:-\d{1,5})?)\s+(.*)", addr_src.strip())
            house, street = (ma.group(1), _clean_street(ma.group(2))) if ma else (None, None)
            cat = CATEGORY_RE.search(text)
            tmpl = TEMPLATE_RE.search(text) if not (pid or "").startswith("KU") and not cat else None
            wt = WORKTYPE_RE.search(re.sub(r"Additional\s+dwelling", "", text, flags=re.I))
            tg = TARGET_RE.search(text)
            rec = {
                "permit_id": pid, "house_nbr": house, "street": street,
                "category": cat.group(0) if cat else (tmpl.group(0) if tmpl else None),
                "work_type": wt.group(1) if wt else None,
                "target": tg.group(0) if tg else None,
                "date": _find_date(text), "page": pno + 1,
            }
            recs.append(rec)
            this.append(rec)
        page_recs.append(this)
    # Column-group pages follow the anchor pages in the same page order: continuation page q
    # holds further columns of anchor page (q mod n), one line per record.
    n = len(page_recs)
    for q, cl in enumerate(cont_pages):
        if not n:
            break
        target_recs = page_recs[q % n]
        rows = cl
        if len(rows) != len(target_recs):
            # wrapped cells: keep only lines that start with a work type or carry a date
            rows = [l for l in cl if WORKTYPE_RE.match(l.strip()) or _find_date(l)]
        if len(rows) != len(target_recs):
            rows = [l for l in cl if WORKTYPE_RE.search(l) or _find_date(l) or re.match(r"\s*\d{9}\b", l)]
        if len(rows) == len(target_recs):
            for r, l in zip(target_recs, rows):
                for k, v in _cont_fields(l).items():
                    if v is not None and r.get(k) is None:
                        r[k] = v
        else:
            for l in cl:  # cannot align: keep dwelling targets as unaligned rows for review
                f = _cont_fields(l)
                if f["target"] and DWELLING_TARGET_RE.search(f["target"]):
                    recs.append({"permit_id": None, "house_nbr": None, "street": None, "category": None,
                                 **f, "page": None})
    for k, r in enumerate(recs):
        r["seq"] = k
    return recs


def load(raw_dir: Path) -> pd.DataFrame:
    raw_dir = Path(raw_dir)
    man = fu.read_manifest(raw_dir / "manifest.json")
    rows = []
    for e in man.get("files", []):
        pdf = raw_dir / e["file"]
        if not pdf.exists():
            continue
        recs = _parse_report(pdf)
        mdate = datetime.fromisoformat(e["meeting_date"])
        dates = [r["date"] for r in recs if r["date"] and abs((mdate - r["date"]).days) < 200]
        if dates:
            ym = Counter((d.year, d.month) for d in dates).most_common(1)[0][0]
        else:
            prev = (mdate.replace(day=1) - pd.Timedelta(days=1))
            ym = (prev.year, prev.month)
        stage = "application" if re.search(r"submitted", e.get("attachment_name", ""), re.I) else "issued"
        for r in recs:
            d = r["date"] if r["date"] and abs((mdate - r["date"]).days) < 200 else None
            rows.append({**r, "date": d, "report_year": ym[0], "report_month": ym[1],
                         "report_file": e["file"], "report_stage": stage})
    df = pd.DataFrame(rows)
    df["date"] = pd.to_datetime(df["date"])
    # undated rows take the report month
    fill = pd.to_datetime(dict(year=df.report_year, month=df.report_month, day=1))
    df["date"] = df["date"].fillna(fill)
    df["permit_id"] = [p if isinstance(p, str) else f"{f[:-4]}#{q}"
                       for p, f, q in zip(df.permit_id, df.report_file, df.seq)]
    df = df.drop_duplicates("permit_id", keep="first")
    df["year"] = df["report_year"].astype(int)  # the report month is the issue month
    df["permit_type"] = df["category"]
    df["description"] = df[["work_type", "target"]].fillna("").agg(" ".join, axis=1).str.strip()
    df["units_raw"] = np.nan
    df["parcel_id"] = None
    cols = ["permit_id", "date", "year", "permit_type", "description", "units_raw", "parcel_id", "street",
            "house_nbr", "work_type", "target", "report_year", "report_month", "report_file", "report_stage"]
    return df[cols].reset_index(drop=True)


# ------------------------------------------------------------------ coverage
def coverage(df: pd.DataFrame) -> pd.DataFrame:
    out = []
    for y in range(2022, 2026):
        d = df[df.report_year == y]
        months = sorted(set(d.report_month))
        missing = [m for m in range(1, 13) if m not in months]
        app = sorted(set(d[d.report_stage == "application"].report_month))
        note = []
        if missing:
            note.append("missing months " + ",".join(map(str, missing)))
        if app:
            note.append("months listed as submitted applications, not issued: " + ",".join(map(str, app)))
        if y >= 2023:
            no_tgt = sorted(mm for mm, g in d.groupby("report_month") if g.target.notna().sum() == 0)
            if no_tgt:
                note.append("months whose report prints no work target (ADUs undetectable): "
                            + ",".join(map(str, no_tgt)))
        else:
            note.append("2022 reports give only template names (New Home/New Duplex/Add-On Remodel): "
                        "interior or attached units are undetectable")
        note.append("no free-text descriptions")
        out.append({"year": y, "months_with_records": len(months), "records": int(len(d)),
                    "complete": not missing, "note": "; ".join(note)})
    return pd.DataFrame(out)


# ------------------------------------------------------------------ classify
_ADU = "work target 'Additional dwelling unit' (Residential building)"
JUDGMENTS: dict[str, dict] = {
    # counted: the permit system's own 'Additional dwelling unit' work target on an existing home
    "2023-05-16_amended-common-council-1_0#0": {
        "counts": True, "component": "adu_attached", "units": 1,
        "why": f"Apr 2023, xxx Fern St: {_ADU}, work type Addition; earlier 2023 permits at the address"},
    "KU-2024-910": {"counts": True, "component": "adu_conversion", "units": 1,
                    "why": f"Sep 2024, xxx Fieldcrest Dr: {_ADU}, work type Remodel"},
    "KU-2025-770": {"counts": True, "component": "adu_attached", "units": 1,
                    "why": f"Aug 2025, xxx Travis La: {_ADU}, work type Addition"},
    "KU-2025-795": {"counts": True, "component": "adu_conversion", "units": 1,
                    "why": f"Aug 2025, xxx Bear Paw Tr: {_ADU}, work type Finished Basement; house "
                           "permitted Jul 2024 (KU-2024-593)"},
    "KU-2025-898": {"counts": True, "component": "adu_conversion", "units": 1,
                    "why": f"Sep 2025, xxx White Dove La: {_ADU}, work type Finished Basement; house "
                           "permitted Nov 2023 (KU-2023-1019)"},
    "KU-2025-1027": {"counts": True, "component": "adu_conversion", "units": 1,
                     "why": f"Dec 2025, xxx Bluebird Ct: {_ADU}; work type not printed (subtype assumed "
                            "interior), ductwork permit same day"},
    "KU-2025-1049": {"counts": True, "component": "adu_conversion", "units": 1,
                     "why": f"Dec 2025, xxx W Henry St: {_ADU}; Aug 2025 egress-window permit on the "
                            "single-family dwelling (KU-2025-807) suggests a basement unit"},
    # unconfirmed (upper bound)
    "KU-2024-502": {"counts": False, "component": None, "units": 0, "unconfirmed": True,
                    "why": "May 2024 (submitted application), xxx Crooks Av: target 'Duplex dwelling', work type "
                           "not printed; could be a conversion or work on an existing duplex - unconfirmed"},
    # excluded
    "KU-2023-4": {"counts": False, "component": None, "units": 0,
                  "why": "Jan 2023: Remodel of an existing 'Recreational dwelling'"},
    "KU-2023-28": {"counts": False, "component": None, "units": 0,
                   "why": "Jan 2023: New 'Duplex dwelling' (xxx & xxx Tarragon Dr), new two-unit building"},
    "KU-2024-790": {"counts": False, "component": None, "units": 0,
                    "why": "Sep 2024: New 'Duplex dwelling' (xxx-xxx Ridgecrest La), new two-unit building"},
    "KU-2024-874": {"counts": False, "component": None, "units": 0,
                    "why": "Sep 2024: New 'Duplex dwelling' (xxx-xxx Ridgecrest La), new two-unit building"},
    "2023-07-18_common-council-31_0#42": {"counts": False, "component": None, "units": 0,
                                          "why": "Jun 2023: Repair of an existing apartment building"},
    "2023-07-18_common-council-31_0#75": {"counts": False, "component": None, "units": 0,
                                          "why": "Jun 2023: Repair of an existing duplex dwelling"},
    "2023-08-15_common-council-34_0#8": {"counts": False, "component": None, "units": 0,
                                         "why": "Jul 2023: New apartment building (xxx E Wisconsin Av), multifamily"},
    "2023-08-15_common-council-34_0#10": {"counts": False, "component": None, "units": 0,
                                          "why": "Jul 2023: New apartment building (xxx E Wisconsin Av), multifamily"},
    "2023-08-15_common-council-34_0#42": {"counts": False, "component": None, "units": 0,
                                          "why": "Jul 2023: Remodel of an existing duplex dwelling"},
}
for _pid in ("22-000262", "22-000263", "22-000264", "22-000265", "22-000602"):
    JUDGMENTS[_pid] = {"counts": False, "component": None, "units": 0,
                       "why": "2022 'New Duplex Permit' for a new two-unit building in a new subdivision"}


def classify_records(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    comp, units, reason, cand = [], [], [], []
    addr_key = df.house_nbr.fillna("") + " " + df.street.fillna("")
    dwelling_new = (df.work_type.fillna("").str.match("New", case=False)
                    & df.target.fillna("").str.contains("single|two|dwelling|duplex", case=False)) \
        | df.permit_type.fillna("").str.contains(r"New\s+Home|New\s+Duplex", case=False)
    for idx, r in df.iterrows():
        c, u, why, is_c = None, 0, "", False
        tgt = r.target if isinstance(r.target, str) else ""
        d = r.description if isinstance(r.description, str) else ""
        ptype = r.permit_type if isinstance(r.permit_type, str) else ""
        wtype = r.work_type if isinstance(r.work_type, str) else ""
        if re.search(r"Additional\s+dwelling", tgt, re.I):
            c, u, is_c = "adu_conversion" if re.search("basement|remodel|conversion", d, re.I) else "adu_attached", 1, True
            why = "work target 'Additional dwelling unit'"
        elif re.search(r"two[- ]family", tgt, re.I) and not re.match("New", wtype, re.I):
            is_c, why = True, "two-family target on non-new work: possible conversion (unconfirmed)"
        elif classify.SF_TO_TWO_RE.search(d):
            c, u, why, is_c = "sf_to_duplex", 1, "text rule: single-family to two-family", True
        elif re.search(r"recreational\s+dwelling|duplex|apartment|multi", d + " " + ptype, re.I):
            is_c, why = True, "dwelling-type wording; reviewed"
        if dwelling_new[idx] and isinstance(r.house_nbr, str):
            same = df[(addr_key == addr_key[idx]) & (df.date < r.date) & dwelling_new]
            if len(same):
                is_c = True
                why = why or "new dwelling at an address with an earlier new-dwelling permit: unconfirmed"
        j = JUDGMENTS.get(str(r.permit_id))
        if j:
            is_c = True
            c, u = (j["component"], int(j.get("units", 1))) if j["counts"] else (None, 0)
            why = ("unconfirmed: " if j.get("unconfirmed") else "judgment: ") + j["why"]
        comp.append(c)
        units.append(u)
        reason.append(why)
        cand.append(is_c)
    df["component"] = comp
    df["units"] = units
    df["reason"] = reason
    df["candidate"] = cand
    return df
