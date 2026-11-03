"""Feasibility sample: project-level parking records for Madison and Milwaukee, Wisconsin (records discovery only).

    uv run python scripts/fetch_parking_wi_project_parking.py [--per-city 16] [--refresh]

Lists Legistar matters through the public Legistar Web API (webapi.legistar.com), then follows each sampled
matter's public Legistar page (gateway.aspx -> LegislationDetail.aspx) to download a few attachments:
  Madison:   Conditional Use files -> "Staff Comments", "Application", "Letter of Intent"
  Milwaukee: zoning-change / planned-development files -> "CPC Staff Report", "Exhibit A", "City Plan Commission Letter"
Text is extracted with poppler's pdftotext (not a Python dependency). No ratios are computed here.

Raw (git-ignored): data/raw/parking_wi_project_parking/ with _sources.json (URL, licence, access time).
Honest user agent only; a refused site is recorded and skipped, never worked around.
"""
from __future__ import annotations

import argparse
import datetime as dt
import html
import json
import re
import subprocess
import sys
import time
import urllib.parse
import urllib.request
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from missing_middleware.paths import RAW  # noqa: E402

D = RAW / "parking_wi_project_parking"
UA = "missing-middleware-research/1.0 (public data)"
API = "https://webapi.legistar.com/v1/{client}/matters"
LICENCE = ("Public records of the City of {city}, published through Granicus Legistar; no open-data licence stated. "
           "Wisconsin public-records law (Wis. Stat. 19.31-19.39) makes them public; use for research with citation.")
CITY = {"madison": "Madison", "milwaukee": "Milwaukee"}
UNITS = re.compile(r"(\d[\d,]*)[- ](?:unit|dwelling|apartment|residential unit|home)", re.I)
WANT = {"madison": ("staff comments", "application", "letter of intent", "staff report"),
        "milwaukee": ("cpc staff report", "exhibit a", "city plan commission letter")}


def get(url: str) -> tuple[int, bytes, str]:
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    try:
        with urllib.request.urlopen(req, timeout=120) as r:
            return r.status, r.read(), r.geturl()
    except urllib.error.HTTPError as e:
        return e.code, b"", url


class Sources:
    def __init__(self) -> None:
        self.path = D / "_sources.json"
        self.rows = json.loads(self.path.read_text()) if self.path.exists() else []

    def add(self, file: str, url: str, city: str, status: int) -> None:
        self.rows = [r for r in self.rows if r["file"] != file]
        self.rows.append({"file": file, "url": url, "licence": LICENCE.format(city=CITY[city]), "http_status": status,
                          "accessed_utc": dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds"),
                          "user_agent": UA})

    def save(self) -> None:
        self.path.write_text(json.dumps(self.rows, indent=1))


def matters(client: str, flt: str) -> list[dict]:
    out, skip = [], 0
    while True:
        q = urllib.parse.urlencode({"$filter": flt, "$top": 1000, "$skip": skip})
        st, body, _ = get(f"{API.format(client=client)}?{q}")
        if st != 200:
            raise SystemExit(f"Legistar API refused {client}: HTTP {st}")
        page = json.loads(body)
        out += page
        if len(page) < 1000:
            return out
        skip += 1000


def units(title: str) -> int | None:
    n = [int(x.replace(",", "")) for x in UNITS.findall(title or "")]
    return max(n) if n else None


def universe(client: str) -> list[dict]:
    if client == "madison":
        flt = ("MatterIntroDate ge datetime'2015-01-01' and MatterIntroDate lt datetime'2026-01-01' "
               "and MatterTypeName eq 'Conditional Use'")
        rows = matters(client, flt)
        keep = [m for m in rows if re.search(r"dwelling|apartment|multi-family|residential building", m["MatterTitle"] or "", re.I)]
    else:
        flt = ("MatterIntroDate ge datetime'2015-01-01' and MatterIntroDate lt datetime'2026-01-01' and "
               "(substringof('Planned Development',MatterTitle) or substringof('change in zoning',MatterTitle))")
        rows = matters(client, flt)
        keep = [m for m in rows if re.search(r"multi-family|multifamily|residential|apartment|dwelling", m["MatterTitle"] or "", re.I)
                and not re.search(r"minor modification", m["MatterTitle"] or "", re.I)]
    return [{"matter_id": m["MatterId"], "file": m["MatterFile"], "intro": m["MatterIntroDate"][:10],
             "type": m["MatterTypeName"], "status": m["MatterStatusName"], "units_in_title": units(m["MatterTitle"]),
             "title": m["MatterTitle"]} for m in keep]


def attachments(client: str, matter_id: int) -> tuple[str, list[tuple[str, str]]]:
    url = f"https://{client}.legistar.com/gateway.aspx?M=L&ID={matter_id}"
    st, body, final = get(url)
    if st != 200:
        return final, []
    links = re.findall(r'href="(View\.ashx\?M=F&(?:amp;)?ID=\d+&(?:amp;)?GUID=[A-F0-9-]+)"[^>]*>([^<]+)<', body.decode("utf-8", "ignore"))
    return final, [(f"https://{client}.legistar.com/{html.unescape(h)}", html.unescape(n).strip()) for h, n in links]


def pick(client: str, links: list[tuple[str, str]]) -> list[tuple[str, str]]:
    got = []
    for key in WANT[client]:
        for url, name in links:
            low = re.sub(r"[_&]+", " ", name.lower())
            if low.startswith(key) and "continued" not in low:
                got.append((url, name))
                break
    return got


def main(argv=None) -> None:
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--per-city", type=int, default=16)
    ap.add_argument("--since", default="2023-01-01", help="sample intro dates from (universe is always 2015-2025)")
    ap.add_argument("--until", default="2026-01-01")
    ap.add_argument("--cities", default="madison,milwaukee")
    ap.add_argument("--refresh", action="store_true")
    a = ap.parse_args(argv)
    D.mkdir(parents=True, exist_ok=True)
    src = Sources()
    for client in a.cities.split(","):
        uni = universe(client)
        (D / f"{client}_matters_2015_2025.json").write_text(json.dumps(uni, indent=1))
        src.add(f"{client}_matters_2015_2025.json", API.format(client=client), client, 200)
        if client == "madison":
            five = [m for m in uni if (m["units_in_title"] or 0) >= 5]
        else:  # Milwaukee titles rarely give unit counts; keep multi-family / apartment wording instead
            five = [m for m in uni if re.search(r"multi-?family|apartment|mixed-use|dwelling units", m["title"] or "", re.I)]
        recent = [m for m in five if a.since <= m["intro"] < a.until]
        # Evenly spaced sample across the chosen intro dates, not the first N.
        step = max(1, len(recent) // a.per_city)
        sample = recent[::step][: a.per_city]
        print(client, "universe", len(uni), "titles with 5+ units", len(five), f"{a.since}..{a.until}", len(recent), "sample", len(sample))
        for m in sample:
            out = D / client / str(m["matter_id"])
            out.mkdir(parents=True, exist_ok=True)
            page, links = attachments(client, m["matter_id"])
            (out / "attachments.json").write_text(json.dumps({"page": page, "links": links, "matter": m}, indent=1))
            src.add(f"{client}/{m['matter_id']}/attachments.json", page, client, 200 if links else 0)
            for url, name in pick(client, links):
                stem = re.sub(r"[^A-Za-z0-9]+", "_", name).strip("_")[:60]
                f = out / f"{stem}.pdf"
                if a.refresh or not f.exists():
                    st, body, _ = get(url)
                    src.add(f"{client}/{m['matter_id']}/{f.name}", url, client, st)
                    if st != 200 or not body.startswith(b"%PDF"):
                        print("  refused/not pdf", st, url)
                        continue
                    f.write_bytes(body)
                    time.sleep(1)
                subprocess.run(["pdftotext", "-layout", str(f), str(f.with_suffix(".txt"))], check=False)
            src.save()
    src.save()


if __name__ == "__main__":
    main()
