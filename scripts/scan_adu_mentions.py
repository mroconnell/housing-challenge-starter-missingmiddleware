"""First-pass scan: does a municipality's current code text mention ADUs at all?

For each target (municipality, code host, URL of a fetchable code text) the
script downloads the page or PDF, extracts text, and searches for ADU terms.
A hit means the code *mentions* ADUs (`mentions_adu`), not that it allows
them (New Berlin mentions and prohibits). Hosts that refuse automated
access (Municode, ecode360, several city sites behind Cloudflare) are
recorded as `could_not_access`; those are then read by hand.

Usage:
  uv run python scripts/scan_adu_mentions.py [--out data/processed/adu_mention_scan/scan.csv] [--only NAME ...]

Network is needed for the scan itself; the matcher (`find_terms`) is pure and tested offline.
Downloaded texts are treated as data only; they are never executed.
"""
from __future__ import annotations

import argparse
import csv
import datetime as dt
import hashlib
import html
import re
import subprocess
import sys
import tempfile
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

TERMS = {
    "accessory dwelling": r"accessory\s+dwelling",
    "ADU": r"\bADUs?\b",
    "in-law": r"\bin[\s-]law\s+(?:unit|suite|apartment|quarters)|mother[\s-]in[\s-]law",
    "granny flat": r"granny\s+flat",
    "coach house": r"coach\s+house",
    "carriage house": r"carriage[\s-]house",
    "secondary dwelling unit": r"secondary\s+(?:dwelling\s+unit|suite)",
    "accessory living quarters": r"accessory\s+living\s+(?:quarters|unit)",
    # New Berlin's defined term; case-sensitive and must start a sentence/heading so that
    # "single-family dwelling unit", "one (1) family dwelling unit", "four family ..." do not match.
    "family dwelling unit": r"(?-i:(?:^|[.;:\n\"“()]\s*|\d\.\s*|[A-Z]\.\s*)Family\s+dwelling\s+unit)",
    "backyard cottage": r"backyard\s+cottage",
}
_SECTION = re.compile(r"(§\s?[\d.\-]+[A-Za-z0-9().\-]*|Sec(?:tion)?\.?\s+[\d.\-]+[A-Za-z0-9().\-]*)")

# (name, wi_muni_id, host, url). URLs are the most direct current code text we know of.
TARGETS = [
    ("Milwaukee city", "5507953000", "city site (Clerk PDF)", "https://city.milwaukee.gov/ImageLibrary/Groups/ccClerk/Ordinances/Volume-2/CH295-sub5.pdf"),
    ("Madison city", "5502548000", "municode", "https://library.municode.com/wi/madison/codes/code_of_ordinances?nodeId=COORMAWIVOIICH20--31_CH28ZOCOOR_SUBCHAPTER_28JSUUSRE_28.151ACUSSURE"),
    ("Green Bay city", "5500931000", "municode (ordinance PDF)", "https://mcclibraryfunctions.azurewebsites.us/api/ordinanceDownload/15619/1400450/pdf"),
    ("Kenosha city", "5505939225", "municode", "https://library.municode.com/wi/kenosha/codes/zoning_ordinance"),
    ("Racine city", "5510166000", "municode", "https://library.municode.com/wi/racine/codes/code_of_ordinances?nodeId=PTIIMUCO_CH114ZO_ARTVDIRE_DIV2REDI"),
    ("Appleton city", "5508702375", "city site", "https://www.appleton.org/government/municipal-code"),
    ("Waukesha city", "5513384250", "Legistar (adopted Ch. 22.03)", "https://legistar2.granicus.com/waukesha/attachments/c852c290-1ccf-4801-9967-8d87347537fd.pdf"),
    ("Eau Claire city", "5503522300", "city site (LDO PDF)", "https://www.eauclairewi.gov/DocumentCenter/View/1033/Land-Development-Ordinance-PDF"),
    ("Oshkosh city", "5513960500", "Wayback copy of city Laserfiche", "https://web.archive.org/web/20251214231347/https://www.oshkoshwi.gov/WebLink/DocView.aspx?id=1183289&dbid=0&repo=Laserfiche"),
    ("Janesville city", "5510537825", "municode", "https://library.municode.com/wi/janesville/codes/code_of_ordinances"),
    ("West Allis city", "5507985300", "Legistar (O-2022-0024)", "https://westalliswi.legistar1.com/westalliswi/attachments/df2ec2d7-5409-4759-a080-5366789281e4.pdf"),
    ("La Crosse city", "5506340775", "Legistar (Ord. 5280)", "https://legistar.granicus.com/CityofLaCrosse/attachments/239dbc28-943b-4645-9f22-e87475d777da.docx"),
    ("Sheboygan city", "5511772975", "city meetings blob (Ch. 105 compiled 2023)", "https://mccmeetingspublic.blob.core.usgovcloudapi.net/sheboygnwi-meet-1ab88e5a89ad4af6836be2c56109cdb0/ITEM-Attachment-001-015d62d52b424fc985217ee1b0ae1f13.pdf"),
    ("Wauwatosa city", "5507984675", "Legistar (O-25-25)", "https://wauwatosacitywi.legistar1.com/wauwatosacitywi/attachments/f54c270b-576f-4e05-a954-36755d2e4f9c.pdf"),
    ("Fond du Lac city", "5503926275", "Zoneomics mirror of ecode360 Ch. 720 (art. IV)", "https://www.zoneomics.com/code/fond-du-lac-WI/chapter_4"),
    ("New Berlin city", "5513356375", "municode", "https://library.municode.com/wi/new_berlin/codes/municipal_code?nodeId=PTIIGELE_CH275ZO_ARTVIIIGEDERE"),
    ("Wausau city", "5507384475", "municode", "https://library.municode.com/wi/wausau/codes/code_of_ordinances?nodeId=TIT23ZO_ARTIIILAUSRE"),
    ("Brookfield city", "5513310025", "codepublishing", "https://www.codepublishing.com/WI/Brookfield/html/Brookfield17/Brookfield1728.html"),
    ("Beloit city", "5510506500", "municode", "https://library.municode.com/wi/beloit/codes/code_of_ordinances"),
    ("Greenfield city", "5507931175", "municode", "https://library.municode.com/wi/greenfield/codes/code_of_ordinances"),
    ("Franklin city", "5507927300", "city site (UDO PDF)", "https://www.franklinwi.gov/Files/Planning/UDO-Rewrite-2025/2025-UDO-Rewrite-Text.pdf"),
    ("Oak Creek city", "5507958800", "ecode360 print (parkingreform.org copy)", "https://assets.parkingreform.org/assets/7d1088f1-4f0b-4f6a-a368-d7a3b6c4d398/oak-creek-wisconsin-united-states-attachment.pdf"),
    ("Manitowoc city", "5507148500", "codepublishing", "https://www.codepublishing.com/WI/Manitowoc/html/Manitowoc15/Manitowoc15110.html"),
    ("West Bend city", "5513185350", "city site (Ch. 17 PDF, 2022)", "https://cms9files.revize.com/westbend/17%20Chapter%20Municipal%20Code-%201.pdf"),
    ("Sun Prairie city", "5502578600", "municode (Ord. 984 PDF)", "https://mcclibraryfunctions.azurewebsites.us/api/ordinanceDownload/13968/1423544/pdf"),
    ("Superior city", "5503178650", "municode", "https://library.municode.com/wi/superior/codes/code_of_ordinances?nodeId=PTIICOOR_CH122ZO"),
    ("Stevens Point city", "5509777200", "city site (Ch. 23 PDF)", "https://www.stevenspoint.com/DocumentCenter/View/769/Chapter-23---Zoning--Floodplain"),
    ("Neenah city", "5513955750", "municode", "https://library.municode.com/wi/neenah/codes/code_of_ordinances"),
    ("Fitchburg city", "5502525950", "city site (Ord. 2025-O-17)", "https://fitchburgwi.gov/DocumentCenter/View/29094/2025-O-17"),
    ("Muskego city", "5513355275", "ecode360", "https://ecode360.com/29722805"),
    ("Mount Pleasant village", "5510154875", "ecode360", "https://ecode360.com/36325067"),
    ("Caledonia village", "5510111950", "zoninghub (staff report)", "https://data.zoninghub.com/viewfile.aspx?fileid=110664"),
    ("Mequon city", "5508951150", "municode", "https://library.municode.com/wi/mequon/codes/code_of_ordinances"),
    ("De Pere city", "5500919775", "city site (Ch. 14 PDF)", "https://www.deperewi.gov/egov/documents/1703171468_81245.pdf"),
    ("Pleasant Prairie village", "5505963300", "ecode360", "https://ecode360.com/36640696"),
    ("Menomonee Falls village", "5513351000", "municode", "https://library.municode.com/wi/menomonee_falls/codes/code_of_ordinances"),
    ("Howard village", "5500935950", "municode", "https://library.municode.com/wi/howard/codes/code_of_ordinances"),
]


def find_terms(text: str) -> tuple[list[str], str, str]:
    """Return (matched term names, first-hit context, nearest preceding section citation)."""
    found, first = [], None
    for name, pat in TERMS.items():
        for m in re.finditer(pat, text, flags=re.IGNORECASE):
            found.append(name)
            if first is None or m.start() < first.start():
                first = m
            break
    if first is None:
        return [], "", ""
    ctx = re.sub(r"\s+", " ", text[max(0, first.start() - 80): first.end() + 80]).strip()
    secs = list(_SECTION.finditer(text[max(0, first.start() - 4000): first.start()]))
    return found, ctx, (secs[-1].group(0).strip() if secs else "")


def _to_text(data: bytes, ctype: str, url: str) -> str:
    if data[:4] == b"%PDF":
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / "f.pdf"
            p.write_bytes(data)
            out = subprocess.run(["pdftotext", "-layout", str(p), "-"], capture_output=True, timeout=120)
            return out.stdout.decode("utf-8", "ignore")
    if data[:2] == b"PK" and url.endswith(".docx"):
        import io, zipfile
        xml = zipfile.ZipFile(io.BytesIO(data)).read("word/document.xml").decode("utf-8", "ignore")
        return html.unescape(re.sub(r"<[^>]+>", " ", xml))
    t = data.decode("utf-8", "ignore")
    t = re.sub(r"(?is)<(script|style).*?</\1>", " ", t)
    return html.unescape(re.sub(r"<[^>]+>", " ", t))


def scan(target, timeout=60) -> dict:
    name, jid, host, url = target
    row = dict(jurisdiction_name=name, jurisdiction_id=jid, code_host=host, url_searched=url,
               scan_date=dt.date.today().isoformat(), search_method="http_get_text_regex",
               result="", http_status="", matched_terms="", first_hit_section="", first_hit_context="",
               text_chars="", sha256="")
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 (research; missing-middleware ADU scan)"})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            data, ctype, row["http_status"] = r.read(), r.headers.get("Content-Type", ""), str(r.status)
    except Exception as e:  # noqa: BLE001 - record any access failure
        row["result"], row["http_status"] = "could_not_access", getattr(e, "code", type(e).__name__)
        return row
    row["sha256"] = hashlib.sha256(data).hexdigest()
    text = _to_text(data, ctype, url)
    row["text_chars"] = str(len(text))
    if len(text.strip()) < 2000 or re.search(r"(?i)just a moment|enable javascript|access denied|captcha", text[:3000]):
        row["result"] = "could_not_access"
        row["search_method"] += " (page shell or bot check; no code text)"
        return row
    terms, ctx, sec = find_terms(text)
    row.update(result="mentions_adu" if terms else "no_mention", matched_terms=";".join(terms),
               first_hit_section=sec, first_hit_context=ctx[:240])
    return row


def main(argv=None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=str(ROOT / "data" / "processed" / "adu_mention_scan" / "scan.csv"))
    ap.add_argument("--only", nargs="*", default=None)
    a = ap.parse_args(argv)
    out = Path(a.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    rows = []
    for t in TARGETS:
        if a.only and t[0] not in a.only:
            continue
        r = scan(t)
        rows.append(r)
        print(f"{r['result']:17} {r['http_status']:>6}  {t[0]}  {r['matched_terms']}", flush=True)
        with out.open("w", newline="") as fh:  # rewrite after each target so partial runs are saved
            w = csv.DictWriter(fh, fieldnames=list(rows[0]), lineterminator="\n")
            w.writeheader(); w.writerows(rows)
    print(f"wrote {out} ({len(rows)} rows)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
