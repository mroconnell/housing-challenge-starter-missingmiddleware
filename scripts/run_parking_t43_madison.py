"""Test 43: do Madison's parking minimums bind? Bunching in project records, 2015-2022.

Locked in docs/parking/CAUSAL_FRAMEWORK_PLAN.md ("Test 43", "test 43 additions", "test 43 audit additions").

    uv run python scripts/run_parking_t43_madison.py code      # fetch + parse files in random order until 30+ qualify
    uv run python scripts/run_parking_t43_madison.py draw      # draw the 50 hand-check projects (seed 20261104)
    uv run python scripts/run_parking_t43_madison.py check     # writes reference/parking_t43_parser_check.csv
    uv run python scripts/run_parking_t43_madison.py shares    # only after the check file exists

The first-pass parse and its 50-project draw are kept as coded_projects_firstpass.csv / handcheck_draw_firstpass.csv.
Hand-read PDF values live in hand_values_all.csv (raw folder; titles not copied). When the draw fails, every project up
to the stop point must have hand values, and the stop point is set by the hand-checked count.

Stage order is enforced: `shares` refuses to run until the hand-check file exists, and if fewer than 45 of 50
checked projects are correct it requires every coded project to be hand-checked (reference rows for all).

Raw (git-ignored): data/raw/parking_wi_project_parking/madison_t43/. Committed outputs carry a Legistar file number
as the project id, never an address.
"""
from __future__ import annotations

import argparse
import json
import random
import re
import subprocess
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from scripts.fetch_parking_wi_project_parking import D, Sources, attachments, get, matters  # noqa: E402

REF = Path(__file__).resolve().parent.parent / "reference"
T = D / "madison_t43"
SEED = 20261104
START, END = "2015-01-01", "2023-01-01"
TARGET = 30
CENTRAL_DISTRICTS = {"DC", "UOR", "UMX", "DR1", "DR2"}  # wholly inside the Central Area; others are read from the cell
RESID = re.compile(r"apartment|dwelling|multi-?family|residential unit|townhome|townhouse|two-family|three-family|"
                   r"four-family|residential building|residential development|residential complex|\bunits?\b", re.I)
NONRES = re.compile(r"signage|street graphics|sign variance|lighting plan|outdoor eating|daycare|day care|restaurant|"
                    r"tavern|garage door|accessory building|telecommunication|comprehensive design review|informational presentation|water treatment|unit well", re.I)
UNITS = re.compile(r"(\d[\d,]*)[- ](?:unit|dwelling|apartment|residential unit|home|townhome)", re.I)
WORDNUM = {"two": 2, "three": 3, "four": 4, "five": 5, "six": 6, "seven": 7, "eight": 8, "nine": 9, "ten": 10,
           "eleven": 11, "twelve": 12}
APPROVED = re.compile(r"approved|passed|adopted|accepted|granted", re.I)
ROW = re.compile(r"^\s{0,20}(?:Number (?:of )?Parking Stalls|(?:Number of )?Auto(?:mobile)? Parking(?: Stalls)?|"
                 r"Vehicle Parking(?: Stalls)?|Off-?street Parking|Parking Stalls)\b", re.I)
NEXTROW = re.compile(r"^\s{0,24}(?:Electric Vehicle|EV |Accessible|Loading|Number Bike|Bike|Bicycle|Other Critical|"
                     r"Building Forms|Landscaping|Lighting|Maximum|Minimum|Usable|Lot |Site Design|Zoning)", re.I)


# ---------------------------------------------------------------- universe
def universe() -> list[dict]:
    d = f"MatterIntroDate ge datetime'{START}' and MatterIntroDate lt datetime'{END}'"
    cu = matters("madison", f"{d} and MatterTypeName eq 'Conditional Use'")
    pd_ = [m for m in matters("madison", f"{d} and MatterTypeName eq 'Ordinance' and substringof('28.022',MatterTitle)")
           if re.search(r"PD\s*\(|Planned Development", m["MatterTitle"] or "")]
    sp = matters("madison", f"{d} and MatterTypeName eq 'Miscellaneous' and (MatterBodyName eq 'URBAN DESIGN COMMISSION' "
                            f"or MatterBodyName eq 'PLAN COMMISSION')")
    out = []
    for kind, rows in (("conditional use", cu), ("planned development", pd_), ("site plan", sp)):
        for m in rows:
            t = m["MatterTitle"] or ""
            if kind == "planned development":  # rezoning titles rarely name the use; homes come from the staff PDF
                if NONRES.search(t):
                    continue
            elif not RESID.search(t) or NONRES.search(t):
                continue
            if re.search(r"single-family|single family", t, re.I) and not re.search(r"multi|apartment|two-family", t, re.I):
                continue
            n = [int(x.replace(",", "")) for x in UNITS.findall(t)]
            n += [WORDNUM[w.lower()] for w in re.findall(r"\b(" + "|".join(WORDNUM) + r")[- ](?:unit|dwelling)", t, re.I)]
            if not n and re.search(r"two-family|two family|duplex", t, re.I):
                n = [2]
            homes_title = max(n) if n else None
            if homes_title is not None and homes_title < 2:
                continue
            if homes_title is None and kind != "planned development" and not re.search(r"apartment|multi-?family|dwelling units|townhome|two-family|"
                                                     r"residential units|mixed-use", t, re.I):
                continue
            out.append({"matter_id": m["MatterId"], "file": m["MatterFile"], "intro": m["MatterIntroDate"][:10],
                        "kind": kind, "status": m["MatterStatusName"] or "", "homes_title": homes_title,
                        "district_title": district(t), "site_key": site_key(t), "title": t})
    return out


def district(t: str) -> str | None:
    m = re.search(r"\(([A-Z]{1,4}(?:-[A-Z0-9]{1,4})?\d?)\)\s*(?:zoning\s*)?District", t)
    if m:
        return m.group(1)
    m = re.search(r"\bin the ([A-Z]{2,4}(?:-[A-Z0-9]{1,3})?) District", t)
    return m.group(1) if m else None


def site_key(t: str) -> str:
    """Internal grouping key (house number + first street word); never written to reference/."""
    s = re.sub(r"^(?:\W*(?:SUBSTITUTE|AMENDED|ALTERNATE|REVISED|2nd SUBSTITUTE)\W*)+", "", t.strip(), flags=re.I)
    num = r"(\d{2,6})(?:[\s,/&\-]|\d|\(formerly [^)]*\)|and\s)*?\s*(?:[NSEW]\.?\s+|North |South |East |West )?([A-Za-z']{3,})"
    m = re.search(r"(?:located at|addressed as|address(?:ed)? at|located east of|at)\s+" + num, s)
    if not m or s.lower().startswith(("consideration", "creating")) is False:
        m = re.match(r"\s*" + num, s) or m
    if not m:
        return "nokey:" + re.sub(r"\W+", "", s.lower())[:40]
    return f"{m.group(1)}-{m.group(2).lower()}"


def dedupe(files: list[dict]) -> list[dict]:
    """One record per project: the latest approved file per site (latest file of any status if none approved)."""
    by = {}
    for f in files:
        by.setdefault(f["site_key"], []).append(f)
    out = []
    for k, fs in by.items():
        ok = [f for f in fs if APPROVED.search(f["status"])] or fs
        keep = max(ok, key=lambda f: (f["intro"], f["matter_id"]))
        keep = dict(keep, n_files=len(fs), homes_title=keep["homes_title"] or max([f["homes_title"] or 0 for f in fs]) or None,
                    district_title=keep["district_title"] or next((f["district_title"] for f in fs if f["district_title"]), None))
        out.append(keep)
    return out


# ---------------------------------------------------------------- fetching
def fetch_staff(p: dict, src: Sources) -> list[Path]:
    out = T / str(p["matter_id"])
    out.mkdir(parents=True, exist_ok=True)
    meta = out / "attachments.json"
    if meta.exists():
        page, links = (lambda j: (j["page"], [tuple(x) for x in j["links"]]))(json.loads(meta.read_text()))
    else:
        page, links = attachments("madison", p["matter_id"])
        meta.write_text(json.dumps({"page": page, "links": links}, indent=1))
        src.add(f"madison_t43/{p['matter_id']}/attachments.json", page, "madison", 200 if links else 0)
        time.sleep(0.5)
    got = []
    for url, name in links:
        low = re.sub(r"[_&]+", " ", name.lower())
        if not re.search(r"staff|zoning comments", low):
            continue
        f = out / (re.sub(r"[^A-Za-z0-9]+", "_", name).strip("_")[:60] + ".pdf")
        if not f.exists():
            st, body, _ = get(url)
            src.add(f"madison_t43/{p['matter_id']}/{f.name}", url, "madison", st)
            if st != 200 or not body.startswith(b"%PDF"):
                continue
            f.write_bytes(body)
            time.sleep(1)
        txt = f.with_suffix(".txt")
        if not txt.exists():
            subprocess.run(["pdftotext", "-layout", str(f), str(txt)], check=False, capture_output=True)
        if txt.exists():
            got.append(txt)
    return got


# ---------------------------------------------------------------- parsing
def cells(line: str) -> list[tuple[int, str]]:
    return [(m.start(), m.group(0)) for m in re.finditer(r"\S(?:.*?\S)?(?=\s{3,}|\s*$)", line)]


def table_row(text: str) -> tuple[str, str, str] | None:
    """Returns (required text, proposed text, raw block) from the Zoning 'Required | Proposed' table.

    Cells are split on runs of 3+ spaces; wrapped lines are assigned to the nearer column. A label printed alone
    (vertically centred) takes its cells from the unlabelled lines just above and below it."""
    lines = text.splitlines()
    for i, ln in enumerate(lines):
        m = ROW.search(ln)
        if not m or re.search(r"\bbike|bicycle", ln, re.I) or (i and re.search(r"\bbike\b", lines[i - 1], re.I)
                                                               and ln.lstrip().lower().startswith("parking")):
            continue
        hdr = next((lines[j] for j in range(i - 1, max(-1, i - 60), -1)
                    if re.search(r"\bRequired\b", lines[j]) and re.search(r"\bProposed\b", lines[j])), None)
        if hdr is None:
            continue
        lab_end = m.end()
        main = [c for c in cells(ln) if c[0] >= lab_end - 1]
        def unlabelled(x: str) -> bool:
            return bool(x.strip()) and not x[: max(lab_end - 4, 1)].strip() and not ROW.search(x) and not NEXTROW.search(x)
        above, below = [], []
        if not main:
            for k in (i - 1, i - 2):
                if k >= 0 and unlabelled(lines[k]):
                    above.insert(0, lines[k])
                else:
                    break
        for k in range(i + 1, min(len(lines), i + 5)):
            if unlabelled(lines[k]):
                below.append(lines[k])
            else:
                break
        block = above + [ln] + below
        ref = next((c for c in [main] + [cells(x) for x in above + below] if len(c) >= 2), None)
        if ref:
            rq_x, pr_x = ref[0][0], ref[1][0]
        else:
            rq_x, pr_x = hdr.index("Required"), hdr.index("Proposed")
            mid = (rq_x + pr_x) / 2
            only = main or (cells(block[0]) if block else [])
            if only and only[0][0] > mid:
                rq_x = -999  # a single cell to the right of the midpoint is the proposed cell
        req, prop = [], []
        for x in block:
            for c in cells(x):
                if c[0] < lab_end - 1 and x is ln:
                    continue
                (req if abs(c[0] - rq_x) <= abs(c[0] - pr_x) else prop).append(c[1])
        return " ".join(req).strip(), " ".join(prop).strip(), "\n".join(block)
    return None


def code_rule(req: str, dist: str | None, homes: int | None) -> dict:
    """Rule in force, from the Required cell and the district only (the proposed cell is not read here)."""
    r = req.lower()
    out = {"rule": None, "code_min": None, "ratio": None, "cell_number": None, "reduction_in_cell": False,
           "maximum": None, "mixed_use": False}
    mx = re.search(r"(\d[\d,]*)\s*(?:stalls?\s*)?max(?:imum)?\b|max(?:imum)?[:\s]+(\d[\d,]*)", r)
    if mx:
        out["maximum"] = int((mx.group(1) or mx.group(2)).replace(",", ""))
    out["mixed_use"] = bool(re.search(r"commercial|retail|office|restaurant|per \d+ ?sq|sq\.? ?f|gfa|\+|plus", r))
    if "central area" in r or (dist in CENTRAL_DISTRICTS and re.search(r"no minimum|none|not required", r)):
        out["rule"] = "central area: none"
        return out
    if re.search(r"per approved plan|as approved|per plan|pd\b|planned development|per gdp|per sip", r) or (dist and dist.startswith("PD")):
        out["rule"] = "planned development: no code minimum"
        return out
    if re.search(r"no minimum|not required|^none\b|^n/?a\b|^0\b", r):
        out["rule"] = "no minimum (district)"
        return out
    ratio = re.search(r"(\d*\.?\d+|one|1)\s*(?:stalls?|spaces?)?\s*per\s*(?:dwelling|unit|du\b|d\.u\.|apartment)", r)
    nums = [int(x.replace(",", "")) for x in re.findall(r"\((\d[\d,]*)\)", r)] or \
           [int(x.replace(",", "")) for x in re.findall(r"(?<![\d.])(\d[\d,]*)(?![\d.]*\s*(?:per|%|sq|max))", r)]
    if ratio:
        v = 1.0 if ratio.group(1) in ("one", "1") else float(ratio.group(1))
        out["ratio"] = v
        if homes:
            out["code_min"] = round(v * homes, 2)
    if nums:
        cand = [n for n in nums if n != out["maximum"]]
        if cand:
            out["cell_number"] = cand[0]
            if out["code_min"] is None:
                out["code_min"] = cand[0]
    if re.search(r"reduc|reduced|variance|waive", r) or (out["cell_number"] and out["code_min"] and out["ratio"]
                                                          and out["cell_number"] < 0.95 * out["code_min"]):
        out["reduction_in_cell"] = True
    out["rule"] = "positive code minimum" if out["code_min"] else "unclear"
    return out


def parse_proposed(prop: str) -> int | None:
    t = re.search(r"(\d[\d,]*)\s*total|total[:\s]*(\d[\d,]*)", prop, re.I)
    if t:
        return int((t.group(1) or t.group(2)).replace(",", ""))
    p = re.sub(r"\([^)]*\)", " ", prop)  # condition / comment references
    p = re.sub(r"see (?:comment|condition)s?\s*#?\s*\d+", " ", p, flags=re.I)
    if re.search(r"^\s*(none|0)\b", p, re.I):
        return 0
    nums = [int(x.replace(",", "")) for x in re.findall(r"(?<![\d.#])(\d[\d,]*)(?![\d.]*\s*(?:%|per|sq|ft|'))", p)]
    if not nums:
        return None
    tagged = re.findall(r"(\d[\d,]*)\s*(?:stalls?\s*)?(?:surface|underground|garage|enclosed|structured|covered|"
                        r"under-?building|below|lower|indoor|outdoor|ug|surf)", p, re.I)
    if re.search(r"total", p, re.I):
        t = re.search(r"(\d[\d,]*)\s*total|total[:\s]*(\d[\d,]*)", p, re.I)
        if t:
            return int((t.group(1) or t.group(2)).replace(",", ""))
    if len(tagged) >= 2:
        return sum(int(x.replace(",", "")) for x in tagged)
    return nums[0]


def homes_from_text(text: str) -> int | None:
    n = [int(x.replace(",", "")) for x in re.findall(r"(\d[\d,]*)[- ](?:dwelling units|residential units|apartment units|units)", text[:6000], re.I)]
    n = [x for x in n if x < 3000]
    return max(n) if n else None


def variance_granted(text: str) -> bool:
    return bool(re.search(r"(parking|stall)[^.]{0,80}(reduction|variance)|(reduction|variance)[^.]{0,80}(parking|stall)", text, re.I))


def code_project(p: dict, src: Sources) -> dict:
    txts = fetch_staff(p, src)
    rec = dict(p, n_staff_pdfs=len(txts), required_text=None, proposed_text=None)
    text = "\n".join(t.read_text(errors="ignore") for t in txts)
    rec["homes"] = p["homes_title"] or homes_from_text(text)
    if not (rec["homes"] and rec["homes"] >= 2):
        rec.update({"rule": "not multifamily (no 2+ homes found)", "code_min": None, "proposed": None,
                    "parking_reduction_or_variance_mentioned": None, "qualifies": False})
        return rec
    row = table_row(text) if text else None
    if row:
        req, prop, _ = row
        rec["required_text"] = req
        rec.update(code_rule(req, p["district_title"], rec["homes"]))       # rule coded first ...
        rec["proposed_text"] = prop
        rec["proposed"] = parse_proposed(prop)                              # ... proposed read after
    else:
        rec.update({"rule": "no table" if text else "no staff pdf", "code_min": None, "proposed": None})
    rec["parking_reduction_or_variance_mentioned"] = variance_granted(text) if text else None
    rec["qualifies"] = bool(rec.get("rule") == "positive code minimum" and rec.get("code_min") and rec.get("proposed") is not None
                            and rec.get("homes") and rec["homes"] >= 2)
    return rec


# ---------------------------------------------------------------- stages
def stage_code(all_files: bool = False) -> None:
    T.mkdir(parents=True, exist_ok=True)
    src = Sources()
    files = universe()
    (T / "files.json").write_text(json.dumps(files, indent=1))
    projects = dedupe(files)
    random.Random(SEED).shuffle(projects)
    print(f"files {len(files)} (by kind: {pd.Series([f['kind'] for f in files]).value_counts().to_dict()}); projects {len(projects)}")
    coded, q = [], 0
    for p in projects:
        rec = code_project(p, src)
        coded.append(rec)
        q += rec["qualifies"]
        src.save()
        if q >= TARGET and not all_files:
            break
    df = pd.DataFrame(coded)
    df["coding_order"] = range(1, len(df) + 1)
    df.to_csv(T / "coded_projects.csv", index=False)   # raw (has titles with addresses): git-ignored
    print(f"coded {len(df)} projects (of {len(projects)}) before stopping; qualifying {q}")
    print(df["rule"].value_counts().to_string())


def stage_draw() -> None:
    df = pd.read_csv(T / "coded_projects.csv")
    pool = df[df["required_text"].notna()]
    pick = pool.sample(n=min(50, len(pool)), random_state=SEED)
    pick[["file", "matter_id", "homes", "rule", "code_min", "proposed", "required_text", "proposed_text"]].to_csv(
        T / "handcheck_draw.csv", index=False)
    print(f"drew {len(pick)} of {len(pool)} coded projects with a table")


def boot_share(flags: np.ndarray, rng: np.random.Generator, B: int = 2000) -> tuple[float, float]:
    """90% interval on a share from B project resamples (with replacement)."""
    n = len(flags)
    s = np.array([flags[rng.integers(0, n, n)].mean() for _ in range(B)])
    return float(np.percentile(s, 5)), float(np.percentile(s, 95))


def num(x):
    return pd.to_numeric(x, errors="coerce")


def stage_check() -> None:
    """Writes reference/parking_t43_parser_check.csv from the first-pass parse and the hand-read PDF values.

    The 50 drawn projects (seed 20261104, first-pass parse) set the pass/fail. Every other coded project is also
    listed when the draw fails (fewer than 45 of 50 correct), since the lock then requires a full hand-check."""
    first = pd.read_csv(T / "coded_projects_firstpass.csv").set_index("file")
    draw = set(pd.read_csv(T / "handcheck_draw_firstpass.csv")["file"])
    hand = pd.read_csv(T / "hand_values_all.csv").set_index("file")
    cur = pd.read_csv(T / "coded_projects.csv").set_index("file")
    rows = []
    for f, h in hand.iterrows():
        src = first.loc[f] if f in first.index else cur.loc[f]
        parsed = {"homes": src.get("homes"), "rule": src.get("rule"), "required": src.get("code_min"),
                  "proposed": src.get("proposed")}
        if str(parsed["rule"]) != "positive code minimum" and pd.isna(parsed["required"]):
            parsed["required"] = 0 if str(parsed["rule"]).startswith(("central", "no minimum")) else np.nan
        for fld in ("homes", "rule", "required", "proposed"):
            pv, hv = parsed[fld], h[fld]
            if fld == "rule":
                ok = str(pv) == str(hv)
            else:
                ok = (pd.isna(num(pv)) and pd.isna(num(hv))) or (not pd.isna(num(pv)) and not pd.isna(num(hv))
                                                                 and abs(float(num(pv)) - float(num(hv))) < 0.5)
            rows.append({"project_id": f"LEG-{f}", "field": fld, "parsed_value": pv, "pdf_value": hv, "ok": bool(ok),
                         "in_draw_of_50": f in draw, "parse_pass": "first" if f in first.index else "second"})
    chk = pd.DataFrame(rows)
    chk.to_csv(REF / "parking_t43_parser_check.csv", index=False)
    d = chk[chk["in_draw_of_50"] & chk["field"].isin(["required", "proposed"])].groupby("project_id")["ok"].all()
    print(f"draw: {int(d.sum())} of {len(d)} projects correct (required and proposed); rows {len(chk)}")


def stage_shares() -> None:
    chk_path = REF / "parking_t43_parser_check.csv"
    if not chk_path.exists():
        raise SystemExit("hand-check file missing: run `check` before any share is computed")
    chk = pd.read_csv(chk_path)
    d = chk[chk["in_draw_of_50"] & chk["field"].isin(["required", "proposed"])].groupby("project_id")["ok"].all()
    n_ok, n_chk = int(d.sum()), len(d)
    coded = pd.read_csv(T / "coded_projects.csv")
    hand = pd.read_csv(T / "hand_values_all.csv")
    passed = n_ok >= 45 * n_chk / 50
    if not passed and not set(coded["file"]).issubset(set(hand["file"])) and len(hand) < len(coded):
        # every project up to the stop point must be hand-checked; that is enforced below
        pass
    df = coded[["file", "intro", "kind", "district_title", "n_files", "coding_order",
                "parking_reduction_or_variance_mentioned"]].merge(hand, on="file", how="left")
    df = df.sort_values("coding_order").reset_index(drop=True)
    for c in ("homes", "required", "required_total", "proposed", "maximum"):
        df[c] = num(df[c])
    df["mixed_use"] = df["mixed_use"].fillna(False).astype(str).str.lower().eq("true")
    df["reduction"] = df["reduction"].fillna(False).astype(str).str.lower().eq("true")
    df["qualifies"] = (df["rule"].eq("positive code minimum") & df["required"].gt(0) & df["proposed"].notna()
                       & df["homes"].ge(2))
    # Stop rule: in random coding order, stop at the project that brings the hand-checked count to 30.
    cum = df["qualifies"].cumsum()
    stop = int(cum.searchsorted(TARGET) + 1) if cum.iloc[-1] >= TARGET else len(df)
    unchecked = df.iloc[:stop]["rule"].isna().sum()
    if not passed and unchecked:
        raise SystemExit(f"parser check {n_ok}/{n_chk} below 45/50 and {unchecked} projects before the stop are not hand-checked")
    df = df.iloc[:stop].copy()
    df["project_id"] = "LEG-" + df["file"].astype(str)
    df["year"] = df["intro"].str[:4].astype(int)
    # Mixed-use: proposed stalls serve all uses, so they are compared with the combined requirement when the table
    # gives it; otherwise with the residential code minimum (flagged as combined_total_unknown).
    df["combined_total_unknown"] = df["mixed_use"] & df["required_total"].isna()
    df["required_compared"] = np.where(df["mixed_use"] & df["required_total"].notna(), df["required_total"], df["required"])
    df["required_per_home"] = df["required_compared"] / df["homes"]
    df["proposed_per_home"] = df["proposed"] / df["homes"]
    df["gap_per_home"] = (df["proposed_per_home"] - df["required_per_home"]).round(6)  # 168/160 sits exactly at 0.05
    df["max_within_025_of_min"] = (df["maximum"] / df["homes"] - df["required_per_home"]).le(0.25)
    proj = df[["project_id", "year", "kind", "district_title", "rule", "homes", "required", "required_total",
               "required_compared", "combined_total_unknown", "proposed", "maximum",
               "max_within_025_of_min", "mixed_use", "reduction", "parking_reduction_or_variance_mentioned",
               "required_per_home", "proposed_per_home", "gap_per_home", "n_files", "coding_order", "qualifies"]]
    proj = proj.rename(columns={"district_title": "district", "reduction": "reduction_or_variance_in_table",
                                "parking_reduction_or_variance_mentioned": "reduction_or_variance_in_text"})
    proj.to_csv(REF / "parking_t43_projects.csv", index=False)

    rng = np.random.default_rng(SEED)
    unit = "share of projects (count / projects with a positive code minimum and both numbers)"
    rows = []
    for label, sub in (("all qualifying", df[df["qualifies"]]),
                       ("qualifying, mixed-use excluded", df[df["qualifies"] & ~df["mixed_use"]])):
        n = len(sub)
        g = sub["gap_per_home"].to_numpy()
        groups = {"at the minimum (|gap| <= 0.05 spaces per home)": np.abs(g) <= 0.05,
                  "0.05 to 0.10 spaces per home above (band comparison)": (g > 0.05) & (g <= 0.10),
                  "above the minimum (gap > 0.05)": g > 0.05,
                  "below the minimum (gap < -0.05; reduction or variance)": g < -0.05}
        rows.append({"group": label, "measure": "projects", "count": n, "of": n, "value": n, "p05": None, "p95": None,
                     "unit": "projects"})
        for k, flag in groups.items():
            lo, hi = boot_share(flag.astype(float), rng) if n else (np.nan, np.nan)
            rows.append({"group": label, "measure": k, "count": int(flag.sum()), "of": n,
                         "value": flag.mean() if n else np.nan, "p05": lo, "p95": hi, "unit": unit})
        pph = sub["proposed_per_home"]
        rows.append({"group": label, "measure": "proposed spaces per home (median)", "count": None, "of": n,
                     "value": float(pph.median()), "p05": float(pph.quantile(0.05)), "p95": float(pph.quantile(0.95)),
                     "unit": "proposed stalls / homes; p05 and p95 are the 5th and 95th percentiles across projects"})
        for k, col in (("maximum within 0.25 spaces per home of the minimum", "max_within_025_of_min"),
                       ("reduction or variance shown in the table", "reduction")):
            rows.append({"group": label, "measure": k, "count": int(sub[col].sum()), "of": n,
                         "value": sub[col].mean() if n else np.nan, "p05": None, "p95": None, "unit": unit})
    for label, mask in (("central area (no minimum)", df["rule"].eq("central area: none")),
                        ("other no-minimum districts", df["rule"].eq("no minimum (district)"))):
        ca = df[mask & df["proposed"].notna() & df["homes"].ge(2)]
        pph = ca["proposed"] / ca["homes"]
        rows.append({"group": label, "measure": "proposed spaces per home (median)", "count": None, "of": len(ca),
                     "value": float(pph.median()) if len(ca) else np.nan,
                     "p05": float(pph.quantile(0.05)) if len(ca) else np.nan,
                     "p95": float(pph.quantile(0.95)) if len(ca) else np.nan,
                     "unit": "proposed stalls / homes; p05 and p95 are the 5th and 95th percentiles across projects"})
    n_q = int(df["qualifies"].sum())
    rows.append({"group": "feasibility", "measure": "at least 30 projects with a positive minimum and both numbers",
                 "count": n_q, "of": len(df), "value": n_q >= TARGET, "p05": None, "p95": None,
                 "unit": f"projects; stopped after coding {len(df)} projects in random order (seed {SEED}); "
                         f"parser check {n_ok} of {n_chk} correct, so every project was hand-checked"})
    out = pd.DataFrame(rows)
    out.insert(0, "test", 43)
    out["interval"] = np.where(out["p05"].notna() & out["unit"].eq(unit),
                               "90% from 2,000 project resamples, seed 20261104", "")
    out.to_csv(REF / "parking_t43_madison.csv", index=False)
    print(out.drop(columns=["interval"]).to_string())


def main(argv=None) -> None:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("stage", choices=["code", "draw", "check", "shares"])
    ap.add_argument("--all", action="store_true",
                    help="code: keep fetching past the parser's 30th qualifier (the hand-checked count sets the stop)")
    a = ap.parse_args(argv)
    if a.stage == "code":
        stage_code(a.all)
    else:
        {"draw": stage_draw, "check": stage_check, "shares": stage_shares}[a.stage]()


if __name__ == "__main__":
    main()
