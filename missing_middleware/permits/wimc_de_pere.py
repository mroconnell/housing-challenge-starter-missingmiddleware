"""De Pere city (Brown County, WI): monthly Building Report PDFs (Building Inspection Division).

Source: the "Building Reports" topic page links one Document Center item per year
(2012-2025), each listing twelve monthly items; each monthly item redirects (HTTP 302)
to a PDF under /egov/documents/. Plain HTTP GET with a normal browser User-Agent (the
site answers scripted user agents poorly). No forms.

Each PDF has a summary page and a "PROJECT VALUATION AND FEE REPORT" listing every
project APPLIED for in the month (header "APPLIED DATES: m/01 THRU m/31"). Fixed-width
rows, two lines per project:
  project #, issue date, NAME (owner/applicant - dropped), LOCATION, contractor (dropped),
  project description (the permit-type text), PROJ TYPE
  segment code, segment date, segment description, BUILDING CODE (census use code, e.g.
  "102 - SINGLE FAMILY DETACHED", "103 - TWO-FAMILY RESIDENCE"), contractor, valuation, fee
A project can have several segment lines. There is no free-text job description; ADUs
show up through the project type / description text (e.g. "ACCESSORY DWELLING UNIT").

Records are grouped by APPLICATION month (year = report year); `date` is the issue date
printed on the row (may be blank for unissued projects).
"""
from __future__ import annotations

import re
import subprocess
from pathlib import Path

import pandas as pd

from . import classify
from . import fetch_util as fu

META = {
    "slug": "de_pere",
    "place": "De Pere city",
    "geoids": ["5500919775"],
    "source_url": "https://www.deperewi.gov/topic/index.php?topicid=476&structureid=126",
    "source_desc": "monthly Building Report PDFs (project valuation and fee report) from the city Document Center",
    "stage": "application",
    "license": "public record (no stated licence)",
    "method": ("project type/description text (classify.text_class, ADU/two-family/conversion words) plus the "
               "census building code on segment lines (102 SF -> 103 two-family); every candidate judged by hand."),
}

BASE = "https://www.deperewi.gov"
TOPIC_URL = META["source_url"]
ITEM_URL = BASE + "/egov/apps/document/center.egov?view=item&id={id}"
UA = ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) "
      "Chrome/124.0 Safari/537.36")
YEARS = (2022, 2023, 2024, 2025)
HISTORY_YEARS = (2020, 2021)  # downloaded only as prior-dwelling evidence for address checks
MONTHS = ["January", "February", "March", "April", "May", "June", "July", "August", "September",
          "October", "November", "December"]


def _op():
    op = fu.opener(cookies=True)
    op.addheaders = [("User-Agent", UA)]
    return op


def _links(html: str) -> list[tuple[int, str]]:
    return [(int(i), t) for i, t in re.findall(r'center\.egov\?view=item(?:&amp;|&|;)id=(\d+)"\s+title="([^"]*)"', html)]


def fetch(raw_dir: Path, log=print) -> dict:
    raw_dir = Path(raw_dir)
    raw_dir.mkdir(parents=True, exist_ok=True)
    man_path = raw_dir / "manifest.json"
    old = {e["file"]: e for e in fu.read_manifest(man_path).get("files", [])}
    want = {f"{y}{m:02d}" for y in HISTORY_YEARS + YEARS for m in range(1, 13)}
    have = {p.name[:6] for p in raw_dir.glob("*.pdf")}
    op = _op()
    items: dict[str, int] = {e["file"][:6]: e["item_id"] for e in old.values()}
    if not want <= have:
        topic = fu.get(TOPIC_URL, op=op).decode("latin-1")
        year_ids = {int(m.group(2)): i for i, t in _links(topic)
                    if (m := re.match(r"((\d{4}) Building Reports)", t))}
        for y in HISTORY_YEARS + YEARS:
            html = fu.get(ITEM_URL.format(id=year_ids[y]), op=op).decode("latin-1")
            for i, t in _links(html):
                m = re.match(r"(\w+) (\d{4}) Building Report", t)
                if m and int(m.group(2)) == y and m.group(1) in MONTHS:
                    items.setdefault(f"{y}{MONTHS.index(m.group(1)) + 1:02d}", i)
    entries = []
    for ym in sorted(want):
        if ym not in items:
            log(f"de_pere: no report link for {ym}")
            continue
        item = items[ym]
        name = f"{ym}_{item}.pdf"
        path = raw_dir / name
        url = ITEM_URL.format(id=item)
        if not path.exists():
            log(f"de_pere: GET {url}")
            with op.open(url, timeout=300) as resp:
                data, final = resp.read(), resp.geturl()
            if not data.startswith(b"%PDF"):
                raise RuntimeError(f"not a PDF: {url}")
            path.write_bytes(data)
            accessed = fu.now_iso()
        else:
            final = old.get(name, {}).get("pdf_url")
            accessed = old.get(name, {}).get("accessed") or fu.now_iso()
        entries.append({"file": name, "item_id": item, "url": url, "pdf_url": final, "accessed": accessed,
                        "sha256": old.get(name, {}).get("sha256") or fu.sha256_file(path)})
    fu.write_manifest(man_path, entries, {"source": TOPIC_URL, "license": META["license"],
                                          "note": "raw PDFs carry owner/applicant and contractor names; never leave data/raw"})
    return fu.read_manifest(man_path)


# ---------------------------------------------------------------- parse
PROJ_RE = re.compile(r"^(\d{6})\s+(\d{1,2}/\d{2}/\d{4}|\s{4,})?")
SEG_RE = re.compile(r"^ (\S+(?: \S+)?)\s+(\d{1,2}/\d{2}/\d{4})\s")


CHAR_W = 4.79983  # the report is a monospaced print: one character = 4.8 pt


def _pdftext(path: Path) -> str:
    """Rebuild exact fixed-width lines from word boxes (`pdftotext -bbox`); `-layout` drifts by a
    few characters, which breaks the fixed-width columns."""
    import html as _html
    xml = subprocess.run(["pdftotext", "-bbox", str(path), "-"], check=True, capture_output=True,
                         text=True).stdout
    pages = []
    for page in xml.split("<page ")[1:]:
        rows: dict[float, list[tuple[int, str]]] = {}
        for x, y, w in re.findall(r'<word xMin="([\d.]+)" yMin="([\d.]+)"[^>]*>(.*?)</word>', page):
            rows.setdefault(round(float(y), 1), []).append((round(float(x) / CHAR_W), _html.unescape(w)))
        lines = []
        for y in sorted(rows):
            buf = ""
            for col, w in sorted(rows[y]):
                if len(buf) < col:
                    buf += " " * (col - len(buf))
                elif buf:
                    buf += " "
                buf += w
            lines.append(buf)
        pages.append("\n".join(lines))
    return "\f".join(pages)


def _cols(header: str) -> dict:
    return {k: header.index(k) for k in ("ISSUE DATE", "NAME", "LOCATION", "CONTRACTOR", "PROJ TYPE")}


def _snap(ln: str, pos: int, tol: int = 5) -> int:
    """Start of the token nearest to header column `pos` (the layout drifts a few characters)."""
    best = None
    for i in range(max(1, pos - tol), min(len(ln), pos + tol + 1)):
        if ln[i] != " " and ln[i - 1] == " " and (best is None or abs(i - pos) < abs(best - pos)):
            best = i
    return best if best is not None else pos


SEG_CODE_RE = re.compile(r"\s(\d{3}|MANU|VIOLATION) - [A-Z<]")
PTYPE_RE = re.compile(r"\s((?:BLD-COM A[LDP]|D/T ACCESS|BLD-FIRE A|HVAC - A/C)|\S+)$")


def _parse_file(path: Path) -> list[dict]:
    text = _pdftext(path)
    applied = re.search(r"APPLIED DATES:\s*(\d{1,2})/\d{2}/(\d{4})", text)
    ym = f"{applied.group(2)}{int(applied.group(1)):02d}" if applied else path.name[:6]
    recs, cur, cols = [], None, None
    for ln in text.splitlines():
        if ln.startswith("PROJECT") and "ISSUE DATE" in ln:
            cols = _cols(ln)
            header_desc = ln.index("DESCRIPTION", cols["CONTRACTOR"])
            continue
        if cols is None:
            continue
        m = PROJ_RE.match(ln)
        if m:
            c_loc, c_con = cols["LOCATION"], cols["CONTRACTOR"]
            loc = ln[c_loc:c_con].strip()
            # the description can overflow into the project-type column: take the type from the end
            tail = ln[header_desc:].rstrip()
            pm = PTYPE_RE.search(tail)
            ptype = pm.group(1) if pm else ""
            desc = tail[:pm.start()].strip() if pm else tail.strip()
            # the NAME field can overflow into LOCATION: keep from the house number on
            lm = re.search(r"(?:^|\s)(\d+[A-Z]?(?:-\d+[A-Z]?)?\s+\S.*)$", loc)
            if lm and lm.start(1) <= 8:
                loc = lm.group(1)
            elif ln[c_loc - 1] != " ":
                loc = ""  # cannot separate the name from the location safely
            cur = {"permit_id": m.group(1), "date_s": (m.group(2) or "").strip(), "location": loc,
                   "proj_desc": desc, "proj_type": ptype, "segments": [], "codes": [], "valuation": 0.0,
                   "report_month": ym, "source_file": path.name}
            recs.append(cur)
            continue
        s = SEG_RE.match(ln)
        if s and cur is not None:
            body = ln[s.end():]
            k = SEG_CODE_RE.search(" " + body)
            seg_desc = (body[:k.start()] if k else body[:30]).strip()
            nums = re.findall(r"-?[\d,]+\.\d\d", body)
            cur["segments"].append(f"{s.group(1)}: {seg_desc}")
            if k:
                cur["codes"].append(k.group(1))
            if nums:
                cur["valuation"] += float(nums[0].replace(",", ""))
    return recs


STREET_RE = re.compile(r"\b(\d+[A-Z]?(?:-\d+[A-Z]?)?) ((?:[A-Z0-9'.]+ ){0,4}?(?:ST|AV|AVE|DR|LN|CI|CT|RD|WAY|TRL|PL|BL|BLVD|"
                       r"PKWY|SPDWY|HWY|CIR|TER|PASS|RUN|PATH|LOOP|SQ|PT|XING)\b(?: [NSEW]\b)?)")
OCR_SEG_RE = re.compile(r"^\s?([A-Z][A-Z0-9_~/.-]+(?: [A-Z]+)?) (\d{1,2}/\d{2}/\d{4}) (.*?) (\d{3}|MANU) - ")


def _ocr_file(path: Path) -> list[dict]:
    """Scanned month (Dec 2022): OCR the image pages with tesseract when installed.

    Project lines run NAME, LOCATION, contractor and description together, so only the
    project #, issue date, a street address matched by STREET_RE (house number + street
    suffix; names never match) and the trailing project-type code are kept. The work
    description comes from the segment lines (segment code, date, description, building
    code), which carry no person names before the building code."""
    import shutil
    import tempfile
    if not (shutil.which("tesseract") and shutil.which("pdftoppm")):
        return []
    info = subprocess.run(["pdfinfo", str(path)], capture_output=True, text=True).stdout
    pages = int(re.search(r"Pages:\s+(\d+)", info).group(1)) if "Pages:" in info else 1
    if pages < 2:
        return []
    with tempfile.TemporaryDirectory() as td:
        subprocess.run(["pdftoppm", "-r", "300", "-gray", "-f", "2", str(path), f"{td}/p"], check=True)
        text = "\n".join(subprocess.run(["tesseract", str(img), "-", "--psm", "6"], capture_output=True,
                                        text=True).stdout for img in sorted(Path(td).glob("p-*")))
    ym = path.name[:6]
    recs, cur = [], None
    for ln in text.splitlines():
        m = re.match(r"^(\d{6}) (\d{1,2}/\d{2}/\d{4})?\s*(.*)$", ln)
        if m and m.group(1)[:2] == ym[2:4]:
            body = m.group(3)
            sm = STREET_RE.search(body)
            pt = re.search(r"(\S+)\W*$", body)
            cur = {"permit_id": m.group(1), "date_s": m.group(2) or "",
                   "location": f"{sm.group(1)} {sm.group(2)}" if sm else "",
                   "proj_desc": "", "proj_type": pt.group(1).replace("~", "-") if pt else "", "segments": [],
                   "codes": [], "valuation": 0.0, "report_month": ym, "source_file": path.name}
            recs.append(cur)
            continue
        sg = OCR_SEG_RE.match(ln)
        if sg and cur is not None:
            cur["segments"].append(f"{sg.group(1).replace('~', '-')}: {sg.group(3).strip()}")
            cur["codes"].append(sg.group(4))
            nums = re.findall(r"-?[\d,]+\.\d\d", ln[sg.end():])
            if nums:
                cur["valuation"] += float(nums[0].replace(",", ""))
    for r in recs:  # project description from the first segment description
        r["proj_desc"] = r["segments"][0].split(": ", 1)[1] if r["segments"] else ""
    return recs


def _split_addr(addr: str) -> tuple[str, str]:
    m = re.match(r"^\s*(\d+[A-Z]?(?:-\d+[A-Z]?)?(?:\s+\d/\d)?)\s+(.*)$", addr or "")
    return (m.group(1), m.group(2).strip()) if m else ("", (addr or "").strip())


def load(raw_dir: Path) -> pd.DataFrame:
    recs = []
    for p in sorted(Path(raw_dir).glob("*.pdf")):
        r = _parse_file(p)
        recs.extend(r if r else _ocr_file(p))
    df = pd.DataFrame(recs)
    df["date"] = pd.to_datetime(df["date_s"].replace("", None), format="%m/%d/%Y", errors="coerce")
    df["year"] = df["report_month"].str[:4].astype(int)
    df["permit_type"] = df["proj_type"]
    df["building_code"] = df["codes"].map(lambda c: "; ".join(dict.fromkeys(c)))
    df["description"] = (df["proj_desc"] + " | " + df["segments"].map("; ".join)).str.strip(" |")
    hs = df["location"].map(_split_addr)
    df["house_nbr"] = [h for h, _ in hs]
    df["street"] = [s for _, s in hs]
    df["units_raw"] = float("nan")
    df["parcel_id"] = pd.NA
    df["month_file"] = df["report_month"]
    cols = ["permit_id", "date", "year", "permit_type", "description", "units_raw", "parcel_id", "street",
            "house_nbr", "building_code", "valuation", "month_file"]
    return df[cols].drop_duplicates("permit_id").reset_index(drop=True)


def coverage(df: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for y in YEARS:
        months = sorted({m for m in df["month_file"] if m.startswith(str(y))})
        miss = [f"{y}{mm:02d}" for mm in range(1, 13) if f"{y}{mm:02d}" not in months]
        note = ("all 12 monthly reports (projects by application month)" if not miss
                else "missing " + ",".join(miss))
        if y == 2022 and "202212" in months:
            note += ("; 202212 detail pages are a scan, read by OCR (segment descriptions and building "
                     "codes; street matched by pattern)")
        rows.append({"year": y, "months_with_records": len(months), "records": int((df["year"] == y).sum()),
                     "complete": not miss, "note": note})
    return pd.DataFrame(rows)


# ---------------------------------------------------------------- classify
# "ONE & TWO FAMILY DWELLING" is the generic new-dwelling permit text, so "two family" is not a
# conversion signal here. There is no free-text job description in this source.
UNIT_WORD_RE = re.compile(r"accessory\s+dwell|\bADU\b|duplex|dwelling\s+unit|apartment|in-?law|conver"
                          r"|living\s+(?:quarters|unit)|second\s+unit", re.I)
NEW_DWELLING_TYPE = "BLD-RES"
# work that also accompanies new construction (not evidence of an existing house)
NEW_CONSTRUCTION_RE = re.compile(r"ONE & TWO FAMILY DWELLING|SOIL EROSION|EARLY START|SEWER|DRIVEWAY|"
                                 r"RESIDENTIAL (?:ELECTRICAL|HVAC)|PLUMBING - RESIDENTIAL|RIPRAP|STABILIZ|"
                                 r"ELECTRICAL SERVICE CHANGE|DECK|FENCE|POOL")
WRECK_RE = re.compile(r"WRECK", re.I)


def classify_records(df: pd.DataFrame) -> pd.DataFrame:
    """Text rules first (they never fire on this source's fixed permit-type texts in 2022-2025),
    then the structured rule: a new 1-2 family dwelling permit (BLD-RES) at an address with
    earlier existing-house work (remodel, HVAC replacement, windows, ...; 2020+ reports) and no
    wrecking permit is a candidate "unconfirmed" second dwelling; low-valuation BLD-RES
    (< $150k) is flagged too. Hand judgments (JUDGMENTS) then decide."""
    out = df.copy()
    out["component"] = None
    out["units"] = 0
    out["reason"] = ""
    out["candidate"] = False
    akey = out["house_nbr"].fillna("") + " " + out["street"].fillna("")
    for idx, r in out.iterrows():
        d = r.description or ""
        cat, note = classify.text_class(d)
        if cat == "adu_legalization":
            out.loc[idx, ["candidate", "reason"]] = [True, "ADU legalization (excluded)"]
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
        if UNIT_WORD_RE.search(d) and r.permit_type != "BLD-APT":
            out.loc[idx, ["candidate", "reason"]] = [True, "unit words; reviewed"]
        if r.permit_type == NEW_DWELLING_TYPE and r.house_nbr:
            same = out[(akey == akey.at[idx]) & (out.index != idx)]
            prior = same[same["permit_id"] < r.permit_id]
            exist = prior[~prior["description"].fillna("").str.contains(NEW_CONSTRUCTION_RE)]
            wreck = same["description"].fillna("").str.contains(WRECK_RE).any()
            if len(exist) and not wreck:
                out.loc[idx, ["candidate", "reason"]] = [
                    True, f"new dwelling permit at an address with {len(exist)} earlier existing-house permit(s); "
                          "unconfirmed"]
            elif r.valuation and r.valuation < 150000:
                out.loc[idx, ["candidate", "reason"]] = [True, "low-valuation new dwelling permit; reviewed"]
    for pid, j in JUDGMENTS.items():
        m = out["permit_id"] == pid
        if not m.any():
            continue
        out.loc[m, "candidate"] = True
        out.loc[m, "component"] = j["component"] if j["counts"] else None
        out.loc[m, "units"] = j.get("units", 1) if j["counts"] else 0
        out.loc[m, "reason"] = "judged: " + j["why"]
    out["units"] = out["units"].astype(int)
    return out


TALLY = ("not in the city's own monthly 'Single Family Dwellings' tally (summary page count and cost "
         "reconcile without it)")
JUDGMENTS: dict[str, dict] = {
    # --- upper-bound (unconfirmed) second dwellings: new-dwelling permit on a lot with a house
    "231655": {"counts": False, "component": "adu_conversion", "why": "unconfirmed (probable ADU): BLD-RES 'one & "
               "two family dwelling' $48k at xxx MENEAU DR filed with a $38k remodel of the existing building, no "
               "sewer or erosion permit (no new foundation); " + TALLY},
    "251103": {"counts": False, "component": "adu_detached", "why": "unconfirmed: BLD-RES $203k at xxx MERRILL ST, "
               "house remodeled there in 2024, new sewer + erosion permits, no wrecking permit seen; " + TALLY +
               "; could be a detached ADU or an unrecorded teardown"},
    "250900": {"counts": False, "component": "adu_attached", "why": "unconfirmed: BLD-RES project whose segment is "
               "'residential addition' $204k (code 434) at xxx RED MAPLE RD with new-dwelling trade permits "
               "(PLB-/ELE-/HVAC-RES) plus a $60k remodel; " + TALLY + "; attached ADU or a large addition"},
    "231205": {"counts": False, "component": "adu_attached", "why": "unconfirmed: BLD-RES $720k at xxx RANDALL AVE "
               "where a $150k remodel was filed 5 months earlier; later only remodel trade permits, no erosion/"
               "sewer for new construction until 2024-25; " + TALLY + "; more likely a large rebuild/addition"},
    "220204": {"counts": False, "component": "adu_detached", "why": "unconfirmed: 2022 (before ADUs were allowed "
               "on 2023-01-01) BLD-RES $18k at xxx COOK ST filed with an $18k detached accessory building >200 sq "
               "ft, remodel, sewer; renewed yearly 2023-25; " + TALLY + "; likely a garage or accessory building "
               "filed under the dwelling type"},
    # --- reviewed and excluded
    "231551": {"counts": False, "why": "BLD-RES at xxx STELLITA CI N with $4,251 valuation but a full new-house "
               "permit set (erosion, sewer, RES trades) and no earlier permits: first house, valuation typo"},
    "250564": {"counts": False, "why": "BLD-RES $35k at xxx BEASLE CT with full new-house permit set, no earlier "
               "permits: first house on the lot"},
    "251364": {"counts": False, "why": "BLD-RES $130k at xxx LAWRENCE DR with full new-house permit set, no "
               "earlier permits: first house on the lot"},
    "220615": {"counts": False, "why": "BLD-RES $110k at a numbered lot in a manufactured-home park (xxx TERRY LN "
               "lot #): replacement/placement of one home"},
    "230797": {"counts": False, "why": "BLD-RES at xxx WILLIE MAYS CI; only earlier permit is an electrical service "
               "(temporary service on a new lot)"},
    "231379": {"counts": False, "why": "BLD-RES at xxx FOXVIEW AVE; only earlier permit is river-bank riprap: "
               "first house"},
    "241178": {"counts": False, "why": "BLD-RES at xxx LOST DAUPHIN RD with a wrecking permit (>600 sq ft) days "
               "later: teardown and rebuild"},
    "240286": {"counts": False, "why": "BLD-RES at xxx BROADWAY ST N after a 2023 wrecking permit: teardown and "
               "rebuild"},
    "241499": {"counts": False, "why": "BLD-RES at xxx GOOD HOPE RD N (unit-numbered address) with early-start, "
               "erosion, sewer and RES trades: new house; the one earlier plumbing permit is coded 3-4 family"},
    "250944": {"counts": False, "why": "BLD-RES at xxx STELLITA CI N; the deck permit a day earlier is part of "
               "the new build"},
    "231639": {"counts": False, "why": "BLD-RES at xxx EVERETT DR; earlier permits are grading/erosion/sewer only "
               "(new lot)"},
    "231786": {"counts": False, "why": "BLD-RES at xxx HONEYSUCKLE CI N; earlier permits are grading only (new lot)"},
    "240700": {"counts": False, "why": "BLD-RES at xxx HONEYSUCKLE CI N; earlier permits are grading only (new lot)"},
}

# component and units for the upper bound (records judged "unconfirmed" above)
UNCONFIRMED = {k: 1 for k, v in JUDGMENTS.items() if v["why"].startswith("unconfirmed")}
