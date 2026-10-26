"""First-pass scan: does a municipality's current code text mention ADUs at all?

For each target (municipality, code host, URL of a fetchable code text) the
script downloads the page or PDF, extracts text, and searches for ADU terms.
A hit means the code *mentions* ADUs (`mentions_adu`), not that it allows
them (New Berlin mentions and prohibits). Only dwelling-unit terms count
(an ADU is a dwelling unit with its own kitchen, sanitation and sleeping
facilities for permanent habitation); generic "accessory structure /
building / use" wording never does. Second-dwelling words that are not
dwelling units (guest house, servants' quarters ...) go to `lead_terms`, and
a rule barring dwellings or living quarters in accessory buildings goes to
`accessory_dwelling_ban_*`; neither makes a mention. Hosts that refuse automated
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
import urllib.parse
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

# ADU definition used by the scan (owner decision 2026-10-24): a dwelling unit with its own kitchen,
# sanitation and sleeping facilities for permanent habitation, accessory to a principal dwelling.
# Only DWELLING-UNIT terms count as an ADU mention. Generic "accessory structure / building / use"
# wording never counts (every zoning code has it), and neither does second-dwelling vocabulary that
# does not say the space is a dwelling unit (guest houses, servants' or domestic-help quarters,
# accessory living quarters, dependency living arrangements): those are recorded as LEAD_TERMS for a
# reader to check, but do not make a mention.
TERMS = {
    "accessory dwelling": r"accessory\s+dwelling",
    "ADU": r"\bADUs?\b",
    "in-law": r"\bin[\s-]law\s+(?:unit|suite|apartment)|mother[\s-]in[\s-]law",
    "granny flat": r"granny\s+flat",
    # coach / carriage house only as a dwelling ("carriage-house dwelling", "coach house unit")
    "coach house": r"coach[\s-]house\s+(?:dwelling|unit|apartment|residence)s?\b",
    "carriage house": r"carriage[\s-]house\s+(?:dwelling|unit|apartment|residence)s?\b",
    "secondary dwelling unit": r"secondary\s+(?:dwelling\s+unit|suite)",
    "accessory apartment": r"accessory\s+apartments?\b",
    # New Berlin's defined term; case-sensitive and must start a sentence/heading so that
    # "single-family dwelling unit", "one (1) family dwelling unit", "four family ..." do not match.
    "family dwelling unit": r"(?-i:(?:^|[.;:\n\"“()]\s*|\d\.\s*|[A-Z]\.\s*)Family\s+dwelling\s+unit)",
    "backyard cottage": r"backyard\s+cottage",
}
# Second-dwelling vocabulary that is not, on its face, a dwelling unit (added to the scan 2026-10-24 after
# the Gate 2 review; demoted to leads the same day under the owner's ADU definition). Recorded, not counted.
LEAD_TERMS = {
    "accessory living quarters": r"accessory\s+living\b",
    "guest house": r"\bguest[\s-]?houses?\b",
    "domestic help/servant quarters": r"quarters\s+for\s+(?:domestic\s+(?:help|servants?|employees?)|servants?|employees?)|(?:servant|employee|caretaker|domestic)s?['’]?\s+(?:living\s+)?quarters",
    "dependency living": r"dependency\s+living",
}
# Never an ADU mention on their own (asserted in tests).
NOT_ADU = ("accessory structure", "accessory building", "accessory use")
# A rule that accessory buildings/structures may not be used as dwellings or living quarters. In the
# second pass a place whose code has such a rule and allows no ADU form is `prohibited_explicit`.
_LIVING = r"(?:dwellings?|dwelling\s+units?|dwelling\s+purposes|living\s+(?:quarters|space|purposes)|residences?|residential\s+(?:use|purposes)|human\s+habitation|sleeping\s+quarters|habitable\s+space)"
_ACC = r"accessory\s+(?:buildings?|structures?|uses?)"
_NEG = r"(?:shall\s+not|may\s+not|must\s+not|cannot|can\s+not|will\s+not|not\s+(?:to\s+)?be|never|is\s+not|are\s+not|prohibited|not\s+permitted)"
PROHIBITION = [
    _ACC + r"\b[^.;]{0,160}?\b" + _NEG + r"\b[^.;]{0,80}?\b" + _LIVING,
    r"\b(?:no|in\s+no\s+(?:instance|case|event)\s+shall)\s+(?:portion\s+of\s+)?(?:an?\s+|any\s+)?" + _ACC + r"\b[^.;]{0,120}?\b(?:used|occupied|designed)\b[^.;]{0,60}?\b" + _LIVING,
    _LIVING + r"[^.;]{0,60}?\b(?:not\s+(?:be\s+)?(?:permitted|allowed)|prohibited)\b[^.;]{0,40}?\b(?:in|within)\s+(?:an?\s+|any\s+)?" + _ACC,
]
_SECTION = re.compile(r"(§\s?[\d.\-]+[A-Za-z0-9().\-]*|Sec(?:tion)?\.?\s+[\d.\-]+[A-Za-z0-9().\-]*)")

# (name, wi_muni_id, host, url, document_kind). URLs are the most direct current code text we know of.
# document_kind says what the URL holds, because a hit in an adopting ordinance is guaranteed and a
# stale compilation can miss later amendments: codified_chapter (current codified text), adopted_chapter_text
# (a full chapter as adopted), adopting_ordinance (only the amending ordinance), stale_compilation (an older
# compiled copy), archived_copy (web archive of the official page), codified_print_copy (official print
# re-hosted by a third party), mirror (third-party re-typeset), staff_report, code_index_page (no code text).
TARGETS = [
    ("Milwaukee city", "5507953000", "city site (Clerk PDF)", "https://city.milwaukee.gov/ImageLibrary/Groups/ccClerk/Ordinances/Volume-2/CH295-sub5.pdf", "codified_chapter"),
    ("Madison city", "5502548000", "municode", "https://library.municode.com/wi/madison/codes/code_of_ordinances?nodeId=COORMAWIVOIICH20--31_CH28ZOCOOR_SUBCHAPTER_28JSUUSRE_28.151ACUSSURE", "codified_chapter"),
    ("Green Bay city", "5500931000", "municode (ordinance PDF)", "https://mcclibraryfunctions.azurewebsites.us/api/ordinanceDownload/15619/1400450/pdf", "adopting_ordinance"),
    ("Kenosha city", "5505939225", "municode", "https://library.municode.com/wi/kenosha/codes/zoning_ordinance", "codified_chapter"),
    ("Racine city", "5510166000", "municode", "https://library.municode.com/wi/racine/codes/code_of_ordinances?nodeId=PTIIMUCO_CH114ZO_ARTVDIRE_DIV2REDI", "codified_chapter"),
    ("Appleton city", "5508702375", "city site", "https://www.appleton.org/government/municipal-code", "code_index_page"),
    ("Waukesha city", "5513384250", "Legistar (adopted Ch. 22.03)", "https://legistar2.granicus.com/waukesha/attachments/c852c290-1ccf-4801-9967-8d87347537fd.pdf", "adopted_chapter_text"),
    ("Eau Claire city", "5503522300", "city site (LDO PDF)", "https://www.eauclairewi.gov/DocumentCenter/View/1033/Land-Development-Ordinance-PDF", "codified_chapter"),
    ("Oshkosh city", "5513960500", "Wayback copy of city Laserfiche", "https://web.archive.org/web/20251214231347/https://www.oshkoshwi.gov/WebLink/DocView.aspx?id=1183289&dbid=0&repo=Laserfiche", "archived_copy"),
    ("Janesville city", "5510537825", "municode", "https://library.municode.com/wi/janesville/codes/code_of_ordinances", "codified_chapter"),
    ("West Allis city", "5507985300", "Legistar (O-2022-0024)", "https://westalliswi.legistar1.com/westalliswi/attachments/df2ec2d7-5409-4759-a080-5366789281e4.pdf", "adopting_ordinance"),
    ("La Crosse city", "5506340775", "Legistar (Ord. 5280)", "https://legistar.granicus.com/CityofLaCrosse/attachments/239dbc28-943b-4645-9f22-e87475d777da.docx", "adopting_ordinance"),
    ("Sheboygan city", "5511772975", "city meetings blob (Ch. 105 compiled 2023)", "https://mccmeetingspublic.blob.core.usgovcloudapi.net/sheboygnwi-meet-1ab88e5a89ad4af6836be2c56109cdb0/ITEM-Attachment-001-015d62d52b424fc985217ee1b0ae1f13.pdf", "stale_compilation"),
    ("Wauwatosa city", "5507984675", "Legistar (O-25-25)", "https://wauwatosacitywi.legistar1.com/wauwatosacitywi/attachments/f54c270b-576f-4e05-a954-36755d2e4f9c.pdf", "adopting_ordinance"),
    # The codified ecode360 Ch. 720 (FO3072) is behind a bot check. The Zoneomics mirror read before 2026-10-25
    # is not used: its terms of use bar automated access and reuse (owner decision D4).
    ("Fond du Lac city", "5503926275", "Granicus (council packet with Ord. 3809)", "https://fonddulac.granicus.com/AgendaViewer.php?view_id=1&clip_id=586", "adopting_ordinance"),
    ("New Berlin city", "5513356375", "municode", "https://library.municode.com/wi/new_berlin/codes/municipal_code?nodeId=PTIIGELE_CH275ZO_ARTVIIIGEDERE", "codified_chapter"),
    ("Wausau city", "5507384475", "municode", "https://library.municode.com/wi/wausau/codes/code_of_ordinances?nodeId=TIT23ZO_ARTIIILAUSRE", "codified_chapter"),
    ("Brookfield city", "5513310025", "codepublishing", "https://www.codepublishing.com/WI/Brookfield/html/Brookfield17/Brookfield17.html", "codified_chapter"),
    ("Beloit city", "5510506500", "municode", "https://library.municode.com/wi/beloit/codes/code_of_ordinances", "codified_chapter"),
    ("Greenfield city", "5507931175", "municode", "https://library.municode.com/wi/greenfield/codes/code_of_ordinances", "codified_chapter"),
    ("Franklin city", "5507927300", "city site (UDO PDF)", "https://www.franklinwi.gov/Files/Planning/UDO-Rewrite-2025/2025-UDO-Rewrite-Text.pdf", "codified_chapter"),
    ("Oak Creek city", "5507958800", "ecode360 print (parkingreform.org copy)", "https://assets.parkingreform.org/assets/7d1088f1-4f0b-4f6a-a368-d7a3b6c4d398/oak-creek-wisconsin-united-states-attachment.pdf", "codified_print_copy"),
    ("Manitowoc city", "5507148500", "codepublishing", "https://www.codepublishing.com/WI/Manitowoc/html/Manitowoc15/Manitowoc15.html", "codified_chapter"),
    ("West Bend city", "5513185350", "city site (Ch. 17 PDF, 2022)", "https://cms9files.revize.com/westbend/17%20Chapter%20Municipal%20Code-%201.pdf", "stale_compilation"),
    ("Sun Prairie city", "5502578600", "municode (Ord. 984 PDF)", "https://mcclibraryfunctions.azurewebsites.us/api/ordinanceDownload/13968/1423544/pdf", "adopting_ordinance"),
    ("Superior city", "5503178650", "municode", "https://library.municode.com/wi/superior/codes/code_of_ordinances?nodeId=PTIICOOR_CH122ZO", "codified_chapter"),
    ("Stevens Point city", "5509777200", "city site (Ch. 23 PDF)", "https://www.stevenspoint.com/DocumentCenter/View/769/Chapter-23---Zoning--Floodplain", "codified_chapter"),
    ("Neenah city", "5513955750", "municode", "https://library.municode.com/wi/neenah/codes/code_of_ordinances", "codified_chapter"),
    ("Fitchburg city", "5502525950", "city site (Ord. 2025-O-17)", "https://fitchburgwi.gov/DocumentCenter/View/29094/2025-O-17", "adopting_ordinance"),
    ("Muskego city", "5513355275", "ecode360", "https://ecode360.com/29722805", "codified_chapter"),
    ("Mount Pleasant village", "5510154875", "ecode360", "https://ecode360.com/36325067", "codified_chapter"),
    ("Caledonia village", "5510111950", "zoninghub (staff report)", "https://data.zoninghub.com/viewfile.aspx?fileid=110664", "staff_report"),
    ("Mequon city", "5508951150", "municode", "https://library.municode.com/wi/mequon/codes/code_of_ordinances", "codified_chapter"),
    ("De Pere city", "5500919775", "city site (Ch. 14 PDF)", "https://www.deperewi.gov/egov/documents/1703171468_81245.pdf", "codified_chapter"),
    ("Pleasant Prairie village", "5505963300", "ecode360", "https://ecode360.com/36640696", "codified_chapter"),
    ("Menomonee Falls village", "5513351000", "municode", "https://library.municode.com/wi/menomonee_falls/codes/code_of_ordinances", "codified_chapter"),
    ("Howard village", "5500935950", "municode", "https://library.municode.com/wi/howard/codes/code_of_ordinances", "codified_chapter"),
]


def _first(patterns, text):
    found, first = [], None
    for name, pat in patterns.items():
        for m in re.finditer(pat, text, flags=re.IGNORECASE):
            found.append(name)
            if first is None or m.start() < first.start():
                first = m
            break
    return found, first


def _context(text, m):
    ctx = re.sub(r"\s+", " ", text[max(0, m.start() - 80): m.end() + 80]).strip()
    secs = list(_SECTION.finditer(text[max(0, m.start() - 4000): m.start()]))
    return ctx, (secs[-1].group(0).strip() if secs else "")


def find_terms(text: str) -> tuple[list[str], str, str]:
    """Return (matched dwelling-unit term names, first-hit context, nearest preceding section citation)."""
    found, first = _first(TERMS, text)
    if first is None:
        return [], "", ""
    ctx, sec = _context(text, first)
    return found, ctx, sec


def find_leads(text: str) -> list[str]:
    """Second-dwelling vocabulary that is not, on its face, a dwelling unit (not counted as a mention)."""
    return _first(LEAD_TERMS, text)[0]


def find_prohibition(text: str) -> tuple[str, str]:
    """(context, section) of the first rule barring dwellings/living quarters in accessory buildings, or ("", "")."""
    # Floodplain chapters (Wisconsin model floodplain ordinance) define "accessory structure ... shall not
    # be used for human habitation" for flood-fringe purposes; that is not a zoning ADU ban, so hits with
    # "flood" nearby are skipped.
    hits = [m for pat in PROHIBITION for m in re.finditer(pat, text, flags=re.IGNORECASE)
            if not re.search(r"(?i)flood", text[max(0, m.start() - 1500): m.end() + 500])]
    if not hits:
        return "", ""
    return _context(text, min(hits, key=lambda m: m.start()))


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


UA = "Mozilla/5.0 (research; missing-middleware ADU scan)"


def _curl(url: str, timeout: int) -> bytes | None:
    """Plain GET with curl; returns the body on HTTP 200, else None."""
    try:
        out = subprocess.run(["curl", "-sL", "--max-time", str(timeout), "-A", UA, "-w", "\n%{http_code}", url],
                             capture_output=True, timeout=timeout + 10)
    except (OSError, subprocess.TimeoutExpired):
        return None
    body, _, code = out.stdout.rpartition(b"\n")
    return body if code.strip() == b"200" else None


def _get(url: str, timeout: int) -> bytes | None:
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return r.read()
    except Exception:  # noqa: BLE001
        return _curl(url, timeout)


def scan(target, timeout=60) -> dict:
    name, jid, host, url, kind = target
    row = dict(jurisdiction_name=name, jurisdiction_id=jid, code_host=host, document_kind=kind, url_searched=url,
               scan_date=dt.date.today().isoformat(), search_method="http_get_text_regex",
               result="", http_status="", matched_terms="", first_hit_section="", first_hit_context="",
               lead_terms="", accessory_dwelling_ban_section="", accessory_dwelling_ban_context="",
               text_chars="", sha256="")
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            data, ctype, row["http_status"] = r.read(), r.headers.get("Content-Type", ""), str(r.status)
    except Exception as e:  # noqa: BLE001 - record any access failure
        # Some hosts refuse Python's HTTP client but answer a plain curl GET with the same user agent.
        status = getattr(e, "code", type(e).__name__)
        got = _curl(url, timeout)
        if got is None:
            row["result"], row["http_status"] = "could_not_access", status
            return row
        data, ctype = got, ""
        row["http_status"] = "200"
        row["search_method"] += f" (curl fallback after urllib {status})"
    host = (urllib.parse.urlsplit(url).hostname or "").lower()
    if host == "codepublishing.com" or host.endswith(".codepublishing.com"):
        # A codepublishing title/chapter page is a table of contents: fetch every section page it links
        # in the same folder and scan them together.
        base = url.rsplit("/", 1)[0]
        links = sorted({h.split("#")[0] for h in re.findall(r'href="\.\./' + re.escape(base.rsplit("/", 1)[1]) + r'/([^"#]+\.html)', data.decode("utf-8", "ignore"))})
        parts = [data]
        for h in links:
            got = _get(f"{base}/{h}", timeout)
            if got is not None:
                parts.append(got)
        row["search_method"] += f" (table of contents plus {len(parts) - 1} of {len(links)} linked pages)"
        data = b"\n".join(parts)
    row["sha256"] = hashlib.sha256(data).hexdigest()
    text = _to_text(data, ctype, url)
    row["text_chars"] = str(len(text))
    if len(text.strip()) < 2000 or re.search(r"(?i)just a moment|enable javascript|access denied|captcha", text[:3000]):
        row["result"] = "could_not_access"
        row["search_method"] += " (page shell or bot check; no code text)"
        return row
    terms, ctx, sec = find_terms(text)
    ban_ctx, ban_sec = find_prohibition(text)
    # result counts dwelling-unit terms only; lead terms and an accessory-dwelling ban are recorded beside it
    row.update(result="mentions_adu" if terms else "no_mention", matched_terms=";".join(terms),
               first_hit_section=sec, first_hit_context=ctx[:240], lead_terms=";".join(find_leads(text)),
               accessory_dwelling_ban_section=ban_sec, accessory_dwelling_ban_context=ban_ctx[:240])
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
