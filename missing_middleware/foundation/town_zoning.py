"""General-zoning status of every Wisconsin town (AQ-026 `no_zoning` class).

A town is zoned when (a) its county adopted general (comprehensive) zoning under
Wis. Stat. 59.69 and the town board approved it, or (b) the town adopted its own
general zoning under village powers (60.62 / 62.23(7), incl. 60.61). Shoreland,
floodplain, airport and farmland-only ordinances are not general zoning. Towns with
neither are `unzoned`. Anything the sources leave unclear is `unknown`, never guessed.

Base source: WI DOA "Comp Plan and Land Regs Inventory" spreadsheet (one row per
county, city, village and town; field "General Zoning" = county / municipal / no).
Spot-check corrections and verification upgrades are listed in OVERRIDES and
VERIFIED below, each with its own dated source.
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

import pandas as pd

from .parsers import read_xlsx_first_sheet

STATUSES = ("county_general", "town_own", "unzoned", "unknown")
VERIFICATION = ("verified", "source_lead", "unknown")

DOA_URL = "https://doa.wi.gov/DIR/Comp-Plan-and-Land-Regs-Inventory.xlsx"
DOA_WAYBACK_URL = "https://web.archive.org/web/20250215161415id_/" + DOA_URL
DOA_DATE = "2025-01-30"  # workbook dcterms:modified; Wayback capture 2025-02-15
DOA_CODE_TO_STATUS = {"county": "county_general", "municipal": "town_own", "no": "unzoned"}

COLS = ["fips5", "gov_type", "place_name", "county", "rpc", "plan_date",
        "general_zoning", "subdivision", "ordinance_url"]


def norm_fips(v) -> str | None:
    """DOA FIPS cells are mostly zero-padded strings; a few are floats (8350.0 -> '08350')."""
    if v is None or (isinstance(v, float) and pd.isna(v)):
        return None
    if isinstance(v, float):
        return f"{int(v):05d}"
    s = str(v).strip()
    return s.zfill(5) if s.isdigit() else s


def read_doa_inventory(path: str | Path) -> pd.DataFrame:
    """Parse the DOA workbook (first sheet 'Inventory') into normalized columns."""
    rows = read_xlsx_first_sheet(path)
    header = rows[0]
    if not str(header[0]).startswith("5-Digit FIPS") or "General Zoning" not in header:
        raise ValueError(f"unexpected DOA inventory header: {header}")
    body = [(list(r) + [None] * len(COLS))[: len(COLS)] for r in rows[1:]]
    df = pd.DataFrame(body, columns=COLS)
    return normalize_inventory(df)


def normalize_inventory(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df["fips5"] = df["fips5"].map(norm_fips)
    for c in ("gov_type", "place_name", "county", "general_zoning"):
        df[c] = df[c].map(lambda v: None if v is None or (isinstance(v, float) and pd.isna(v)) else str(v).strip())
    df["general_zoning"] = df["general_zoning"].str.lower()
    return df[df["gov_type"].notna()].reset_index(drop=True)


def county_status(inv: pd.DataFrame) -> pd.DataFrame:
    """County rows: county name and whether DOA records a county general zoning ordinance."""
    c = inv[inv["gov_type"] == "County"][["fips5", "place_name", "general_zoning"]]
    return c.rename(columns={"fips5": "county_geoid", "place_name": "county",
                             "general_zoning": "county_general_zoning"}).reset_index(drop=True)


@dataclass(frozen=True)
class Override:
    county: str
    town: str
    status: str
    verification: str
    source_url: str
    source_date: str
    note: str


_WOOD_URL = "https://woodcountywi.gov/Departments/PZ/Zoning.aspx"
_WOOD_NOTE_AMBIG = (
    "Ambiguous: Wood County's 1934 zoning ordinance (Ord. 700, adopted under 59.69 and approved by "
    "town boards) is still in effect in all towns, but has only a Forestry & Recreation district "
    "(dwellings barred) and an Unrestricted district (any lawful use); DOA does not count it as "
    "general zoning. District map not obtained. Town has no own zoning per county page.")
_TAYLOR_GUIDE = "https://taylor.extension.wisc.edu/files/2013/03/Rural-Living-Guide-Taylor-County-rev-2013-CM.pdf"

OVERRIDES: tuple[Override, ...] = (
    Override("Crawford", "Eastman", "unzoned", "source_lead",
             "https://www.crawfordcountywi.gov/zoningforms", "undated (read 2026-10-24)",
             "DOA codes 'county', but Crawford County states it 'is not comprehensively zoned' (shoreland and "
             "floodplain only); county clerk directory leaves Eastman's ZONED cell blank; town ordinance list "
             "(townofeastman.com/ordinances) has no zoning ordinance."),
    Override("Grant", "Platteville", "unknown", "unknown",
             "https://gcinternetwebsite.co.grant.wi.gov/conservation-sanitation-and-zoning/ordinances-applies-to-the-following-towns/",
             "2026-07-21",
             "DOA codes 'county', but the county's list of towns under its comprehensive zoning omits Platteville; "
             "no town zoning ordinance found; part of the town is under City of Platteville extraterritorial "
             "zoning (city Ch. 25). Not resolved."),
    Override("Monroe", "Angelo", "town_own", "verified",
             "https://angelowi.gov/wp-content/uploads/2026/07/Ordinance-Interim-Zoning.pdf", "2026-06-30",
             "DOA (2025) codes 'no'. Town Ordinance 063026 'Establishing Interim Zoning' under 60.62 / "
             "62.23(7)(da), effective 2026-07-01, up to 2 years pending a comprehensive town ordinance."),
    Override("Taylor", "Little Black", "town_own", "source_lead",
             "https://energyzoning.org/sites/default/files/PDF/5511944900_Taylor_Little%20Black%20Town_20230202.pdf",
             "2017-02-15 (copy collected 2023-02-02)",
             "DOA codes 'no'. Town zoning code with Residential, A-1, A-2 and Commercial/Industrial districts "
             "under 60.61/62.23, adopted 2017, amended 2018."),
    Override("Taylor", "Chelsea", "unknown", "unknown", _TAYLOR_GUIDE, "2013",
             "Conflict: DOA codes 'no'; 2013 UW-Extension Taylor County guide says the town has its own "
             "planning/zoning. Not resolved."),
    Override("Taylor", "Hammel", "unknown", "unknown", _TAYLOR_GUIDE, "2013",
             "Conflict: DOA codes 'no'; 2013 UW-Extension guide says own planning/zoning; town comp plan "
             "2020-2030 describes town setback and lot rules. Not resolved."),
    Override("Taylor", "Molitor", "unknown", "unknown", _TAYLOR_GUIDE, "2013",
             "Conflict: DOA codes 'no'; 2013 UW-Extension guide says own planning/zoning. Not resolved."),
    Override("Wood", "Cameron", "town_own", "verified", _WOOD_URL, "undated (read 2026-10-24)",
             "DOA codes 'no'; Wood County lists Cameron among 12 towns with their own zoning (approved 2007-09-05)."),
    Override("Wood", "Marshfield", "town_own", "verified", _WOOD_URL, "undated (read 2026-10-24)",
             "DOA codes 'no'; Wood County lists Marshfield among 12 towns with their own zoning (approved 2022-12-20)."),
) + tuple(
    Override("Wood", t, "unknown", "unknown", _WOOD_URL, "undated (read 2026-10-24)", _WOOD_NOTE_AMBIG)
    for t in ("Arpin", "Cary", "Cranmoor", "Hansen", "Hiles", "Milladore", "Remington", "Richfield",
              "Sherry", "Wood")
)

# Rows where a dated county or town source names the town with the same status DOA gives.
# (county, tuple of towns) -> (source_url, source_date)
VERIFIED: tuple[tuple[str, tuple[str, ...], str, str], ...] = (
    ("Chippewa", ("Anson", "Eagle Point", "Hallie", "Lafayette", "Wheaton", "Woodmohr"),
     "https://www.chippewacountywi.gov/401", "undated; Ch. 70 amended through 2026-08-11"),
    ("Chippewa", ("Bloomer",), "https://townofbloomer.com/zoning-information", "undated (read 2026-10-24)"),
    ("Rusk", ("Atlanta", "Flambeau", "Grant", "Grow", "Marshall", "Stubbs", "Thornapple", "Washington", "Wilson"),
     "https://ruskcounty.org/index.asp?SEC=6C5C3289-D463-4C0F-8C16-3773BF9C3BB6&DE=64D1B37C-BD85-4775-94C5-721FFB923011",
     "undated (read 2026-10-24)"),
    ("Rusk", ("Willard",), "https://www.willardwi.gov/ordinances/", "2021-10-11"),
    ("Monroe", ("La Grange",), "https://townoflagrangemcwi.gov/government/zoning", "undated (read 2026-10-24)"),
    ("Monroe", ("Little Falls",), "https://townoflittlefalls.wi.gov/zoning", "undated (read 2026-10-24)"),
    ("Grant", ("Boscobel", "Clifton", "Ellenboro", "Fennimore", "Harrison", "Hickory Grove", "Jamestown", "Liberty",
               "Lima", "Millville", "Mount Hope", "Mount Ida", "Muscoda", "Paris", "Potosi", "South Lancaster",
               "Watterstown", "Wingville"),
     "https://gcinternetwebsite.co.grant.wi.gov/conservation-sanitation-and-zoning/ordinances-applies-to-the-following-towns/",
     "2026-07-21"),
    ("Barron", ("Almena", "Barron", "Cedar Lake", "Clinton", "Crystal Lake", "Cumberland", "Dallas", "Doyle",
                "Maple Grove", "Maple Plain", "Oak Grove", "Prairie Lake", "Rice Lake", "Stanfold", "Stanley",
                "Sumner", "Turtle Lake", "Arland", "Bear Lake", "Chetek", "Dovre", "Lakeland", "Prairie Farm",
                "Sioux Creek", "Vance Creek"),
     "https://www.co.barron.wi.us/misc%20docs/maps/zoned_unzoned.pdf",
     "undated map; ordinance 17.10(1)(a) town table; county statement 2026-10-20"),
    ("Crawford", ("Bridgeport", "Freeman", "Haney", "Prairie Du Chien", "Utica", "Clayton", "Scott", "Seneca"),
     "https://www.crawfordcountywi.gov/media/departments/LC_Planning_Zoning/Zoning/Clerks_UDC.pdf", "2026-09-16"),
    ("Wood", ("Auburndale", "Dexter", "Grand Rapids", "Lincoln", "Port Edwards", "Rock", "Rudolph", "Saratoga",
              "Seneca", "Sigel"), _WOOD_URL, "undated (read 2026-10-24)"),
    ("Juneau", ("Germantown",), "https://www.co.juneau.wi.gov/departments/sanitation_zoning/index.php",
     "town ordinance 1989, amended 2021-07"),
)

# Notes attached to towns that keep the DOA status but carry a known caveat.
COUNTY_NOTES = {
    "Vernon": ("Vernon County has no general zoning but is drafting its first countywide ordinance "
               "(towns would opt in; Vernon Reporter 2026-06-15), and about nine unzoned towns planned "
               "interim moratoria; status may change in 2026-27."),
    "Clark": ("Clark County's 1934 zoning survives only as 'Zoning of County-Owned Land' (Code Ch. 22 Art. X); "
              "not general zoning of private land."),
    "Pepin": "Pepin County bluffland and Great River Road codes are overlays, not general zoning.",
    "Juneau": "Juneau County has no county general zoning (county sanitation & zoning page).",
    "Taylor": "Taylor County has no county general zoning (comp plan ch. 8, 2007; zoning dept page).",
}
TOWN_NOTES = {
    ("Rusk", "Big Bend"): "Reported 2026 data-center moratorium (Wisconsin Watch); ordinance type not verified.",
    ("Juneau", "Kildare"): "Town building-permit ordinance with 5-acre minimum lot and setbacks, no zoning districts.",
}


def _key(county: str, town: str) -> tuple[str, str]:
    return (county.strip().lower(), town.strip().lower())


def classify_towns(inv: pd.DataFrame, towns: pd.DataFrame, strict: bool = True) -> pd.DataFrame:
    """One row per town in `towns` (columns area_id, geoid, name, cousubfp, parent_county_id).

    Joins the DOA inventory on the 5-digit county-subdivision FIPS (unique statewide),
    then applies OVERRIDES and VERIFIED. With strict=True every listed town must match exactly
    one row; strict=False skips listed towns that are absent (test fixtures).
    """
    t_inv = inv[inv["gov_type"] == "Town"].copy()
    # A town whose FIPS appears in the inventory only under another type (DOA lists Rib Falls,
    # Marathon Co., as a "Village") is still matched on FIPS, and the mismatch is noted.
    other = inv[(inv["gov_type"].isin(["City", "Village"])) & inv["fips5"].isin(towns["cousubfp"])
                & ~inv["fips5"].isin(t_inv["fips5"])].copy()
    other["type_note"] = "DOA lists this FIPS as a " + other["gov_type"].str.lower() + " (TIGER 2024: town)"
    t_inv = pd.concat([t_inv.assign(type_note=""), other], ignore_index=True)
    if t_inv["fips5"].duplicated().any():
        raise ValueError("duplicate town FIPS in DOA inventory")
    cty = county_status(inv)
    df = towns[["area_id", "geoid", "name", "cousubfp", "parent_county_id"]].merge(
        t_inv[["fips5", "place_name", "county", "general_zoning", "type_note"]],
        left_on="cousubfp", right_on="fips5", how="left")
    df = df.merge(cty[["county_geoid", "county", "county_general_zoning"]].rename(columns={"county": "county_name"}),
                  left_on="parent_county_id", right_on="county_geoid", how="left")
    df["doa_code"] = df["general_zoning"]
    df["zoning_status"] = df["doa_code"].map(DOA_CODE_TO_STATUS).fillna("unknown")
    df["verification"] = df["zoning_status"].map(lambda s: "unknown" if s == "unknown" else "source_lead")
    df["source_url"] = DOA_URL
    df["source_date"] = DOA_DATE
    df["notes"] = df["doa_code"].map(
        lambda c: f"DOA inventory General Zoning = '{c}'" if isinstance(c, str) else "not in DOA inventory")
    df.loc[df["type_note"].fillna("") != "", "notes"] += "; " + df["type_note"]
    df.loc[df["doa_code"].isna(), "source_url"] = ""
    df.loc[df["doa_code"].isna(), "source_date"] = ""

    # county name fallback when the DOA town row is missing
    df["county"] = df["county"].fillna(df["county_name"])
    keys = [_key(c or "", n or "") for c, n in zip(df["county"], df["place_name"].fillna(""))]
    pos = {}
    for i, k in enumerate(keys):
        pos.setdefault(k, []).append(i)

    def _one(county, town):
        hits = pos.get(_key(county, town), [])
        if len(hits) == 0 and not strict:
            return None
        if len(hits) != 1:
            raise KeyError(f"{town} ({county}) matched {len(hits)} towns")
        return df.index[hits[0]]

    for county, names, url, date in VERIFIED:
        for n in names:
            i = _one(county, n)
            if i is None:
                continue
            df.at[i, "verification"] = "verified"
            df.at[i, "notes"] += f"; confirmed by {url} ({date})"
    for o in OVERRIDES:
        i = _one(o.county, o.town)
        if i is None:
            continue
        df.at[i, "zoning_status"] = o.status
        df.at[i, "verification"] = o.verification
        df.at[i, "source_url"] = o.source_url
        df.at[i, "source_date"] = o.source_date
        df.at[i, "notes"] = f"{o.note} (DOA {DOA_DATE} code: '{df.at[i, 'doa_code']}')"
    for i in df.index:
        c = df.at[i, "county"]
        if c in COUNTY_NOTES and df.at[i, "zoning_status"] in ("unzoned", "unknown"):
            df.at[i, "notes"] += "; " + COUNTY_NOTES[c]
        tn = TOWN_NOTES.get((c, df.at[i, "place_name"]))
        if tn:
            df.at[i, "notes"] += "; " + tn
    if df.loc[df["zoning_status"] == "county_general", "county_general_zoning"].ne("county").any():
        bad = df[(df["zoning_status"] == "county_general") & (df["county_general_zoning"] != "county")]
        raise ValueError(f"county_general town in county without general zoning: {bad['name'].tolist()}")

    out = df[["area_id", "geoid", "name", "county", "zoning_status", "source_url", "source_date",
              "verification", "notes"]].rename(columns={"county": "county_name"})
    assert out["zoning_status"].isin(STATUSES).all() and out["verification"].isin(VERIFICATION).all()
    return out.sort_values("geoid").reset_index(drop=True)


def summarize(status: pd.DataFrame, inventory: pd.DataFrame) -> pd.DataFrame:
    """Towns and ACS one-unit detached homes by zoning_status."""
    h = status.merge(inventory[["area_id", "homes_1unit_detached"]], on="area_id", how="left")
    g = h.groupby("zoning_status").agg(towns=("area_id", "size"),
                                       homes_1unit_detached=("homes_1unit_detached", "sum"),
                                       verified=("verification", lambda s: int((s == "verified").sum())))
    g = g.reindex(STATUSES).fillna(0).astype(int)
    g.loc["total"] = g.sum()
    return g.reset_index()
