"""Baseline bake-off, Part 2 inputs: Wisconsin place permit rows 1990-2025 linked to today's municipality pieces.

1990-2006 files have no FIPS codes and use a different column layout; 2007-2025 files have the FIPS MCD code and
the foundation layout (parsers.read_bps). Old rows are read into the same columns, then every row goes through the
foundation crosswalk (missing_middleware/foundation/crosswalk.py): code, then place code, then name in county
(full name, then base name for a changed type), then documented aliases; county "Part Unincorporated Area" rows are
split each year among the county's towns with no own row that year, by today's one-unit detached homes.
"""
from __future__ import annotations

import re
from pathlib import Path

import numpy as np
import pandas as pd

from missing_middleware.foundation import crosswalk as xwmod
from missing_middleware.foundation import parsers

SIZE_GROUPS = ("1unit", "2units", "3_4units", "5plus")
FIPS_LAYOUT_FROM = 2007

# Old names -> today's TIGER 2024 name (county FIPS, lower-case cleaned name). Applied before the crosswalk, because
# its base-name rule would otherwise pick a wrong successor (for example Menasha town -> Menasha city).
OLD_RENAMES = {
    ("139", "menasha town"): "Fox Crossing village",     # town of Menasha incorporated as Fox Crossing, 2016
    ("009", "de pere town"): "Ledgeview town",           # town of De Pere renamed Ledgeview, 1990s
    ("059", "salem town"): "Salem Lakes village",        # Salem town + Silver Lake village merged, 2017
    ("133", "pewaukee town"): "Pewaukee city",           # town of Pewaukee incorporated as a city, 1999
    ("133", "waukesha town"): "Waukesha village",        # town of Waukesha incorporated as a village
    ("073", "brokaw village"): "Maine village",          # Brokaw dissolved into Maine
    ("025", "de forest village"): "DeForest village",    # spelling
    ("011", "buffalo city"): "Buffalo City city",        # 1990-91 files write the city's name with a lower-case type
}


def clean_name(name: str) -> str:
    """'Adrian town@5' -> 'Adrian town'; 'ABINGDON . . .' -> 'ABINGDON'; a name with no type that is not a county
    row is a city (1990-2006 files list cities without a type word)."""
    n = re.sub(r"@\d+|\(N\)|#", " ", str(name))
    n = re.sub(r"(\s*\.)+\s*$", "", n).strip()
    n = re.sub(r"\s+", " ", n)
    if not xwmod.is_county_row(n) and not re.search(r"\s(city|village|town)$", n):   # type words are lower case
        n = f"{n} city"
    return n


def rename_old(df: pd.DataFrame) -> pd.DataFrame:
    """Apply OLD_RENAMES to rows before 2015 (2015-2025 rows come from the foundation build unchanged)."""
    key = list(zip(df["county_fips"], df["name"].str.lower()))
    df = df.copy()
    df["name"] = [OLD_RENAMES.get(k, n) for k, n in zip(key, df["name"])]
    return df


def read_old_place_file(path: Path, year: int, state_fips: str = "55") -> pd.DataFrame:
    """Read a 1990-2006 BPS place file by its own header (columns differ between eras)."""
    lines = path.read_text(errors="ignore").splitlines()
    h2 = [c.strip() for c in lines[1].split(",")]
    i_name, i_months = h2.index("Name"), h2.index("Months Rep")
    rows = []
    for ln in lines[3:]:
        p = [c.strip() for c in ln.split(",")]
        if len(p) < i_name + 25 or p[1] != state_fips:
            continue
        vals = [pd.to_numeric(x, errors="coerce") for x in p[i_name + 1:i_name + 25]]
        r = dict(year=year, bps_id=p[2], county_fips=p[3], fips_mcd="", fips_place="", name=clean_name(p[i_name]),
                 months_reported=pd.to_numeric(p[i_months], errors="coerce"))
        for k, g in enumerate(SIZE_GROUPS):
            r[f"{g}_units"] = vals[3 * k + 1]
            r[f"{g}_units_rep"] = vals[12 + 3 * k + 1]
        rows.append(r)
    return pd.DataFrame(rows)


def read_all_places(old_dir: Path, new_dir_old: Path, foundation_bps: pd.DataFrame) -> pd.DataFrame:
    """1990-2006 from old files, 2007-2014 via parsers.read_bps, 2015-2025 from the foundation build."""
    parts = [read_old_place_file(old_dir / f"mw{y}a.txt", y) for y in range(1990, FIPS_LAYOUT_FROM)]
    for y in range(FIPS_LAYOUT_FROM, 2015):
        d = parsers.read_bps(new_dir_old / f"mw{y}a.txt", "place")
        d["name"] = d["name"].map(lambda s: re.sub(r"\s+", " ", re.sub(r"@\d+|\(N\)|#", " ", str(s))).strip())
        parts.append(d)
    parts = [rename_old(p) for p in parts]
    keep = ["year", "bps_id", "county_fips", "fips_mcd", "fips_place", "name", "months_reported"] + \
        [f"{g}_units" for g in SIZE_GROUPS] + [f"{g}_units_rep" for g in SIZE_GROUPS]
    f = foundation_bps.copy()
    f["name"] = f["name"].map(lambda s: re.sub(r"@\d+", "", str(s)).strip())
    out = pd.concat([p.reindex(columns=keep) for p in parts] + [f.reindex(columns=keep)], ignore_index=True)
    for c in ("fips_mcd", "fips_place"):
        out[c] = out[c].fillna("").astype(str).str.strip()
    out["units_total"] = out[[f"{g}_units" for g in SIZE_GROUPS]].sum(axis=1, min_count=1)
    out["1unit_units"] = out["1unit_units"]
    out["reporting_status"] = np.where(out["months_reported"].fillna(0) > 0, "reported", "not_reported")
    return out


def link(bps_all: pd.DataFrame, munis: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Foundation crosswalk and per-year county-row allocation on the 1990-2025 rows."""
    xw = xwmod.build_crosswalk(bps_all, munis)
    alloc = xwmod.county_unincorporated_allocation(xw, bps_all, munis)
    return xw, alloc


def coverage(bps_all: pd.DataFrame, xw: pd.DataFrame, alloc: pd.DataFrame, state_units: pd.Series) -> pd.DataFrame:
    """Per year: units in rows linked to a piece (matched codes or names, and county rows split to towns), against
    the state file's units (estimate columns, as published). A year passes if linked >= 95% of the state."""
    keys = ["bps_id", "county_fips", "fips_mcd", "fips_place"]
    m = xw[xw["match_type"].isin(xwmod.MATCHED_TYPES)].drop_duplicates(keys[:1] + ["bps_county_fips", "fips_mcd", "fips_place"])
    mk = set(zip(m["bps_id"], m["bps_county_fips"], m["fips_mcd"], m["fips_place"]))
    ck = set(zip(alloc["bps_id"], alloc["bps_county_fips"], alloc["fips_mcd"], alloc["fips_place"], alloc["year"])) if len(alloc) else set()
    b = bps_all.copy()
    b["linked"] = [((i, c, f, p) in mk) or ((i, c, f, p, y) in ck) for i, c, f, p, y in
                   zip(b["bps_id"], b["county_fips"], b["fips_mcd"], b["fips_place"], b["year"])]
    g = b.groupby("year").apply(lambda d: pd.Series(dict(place_rows_units=d["units_total"].sum(),
                                                          linked_units=d.loc[d["linked"], "units_total"].sum())))
    g["state_units"] = state_units.reindex(g.index)
    g["linked_share_of_state"] = g["linked_units"] / g["state_units"]
    g["passes_95"] = g["linked_share_of_state"] >= 0.95
    return g.reset_index()
