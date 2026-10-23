"""Parsers for the raw Census files used by the foundation build.

All parsers are pure functions of a file path (or file-like text), so the
tests can run them on tiny fixtures without network access.
"""
from __future__ import annotations

import io
import re
import zipfile
from pathlib import Path
from xml.etree import ElementTree as ET

import pandas as pd

# ---------------------------------------------------------------------------
# ACS table-based summary file (pipe-delimited .dat, one national file per table)
# ---------------------------------------------------------------------------

# Census summary levels we keep, keyed by the 3-digit code at the start of GEO_ID.
SUMLEVEL_TO_LEVEL = {
    "040": "state",
    "050": "county",
    "060": "municipality",  # county subdivision (WI city / village / town piece)
    "140": "tract",
    "150": "block_group",
}

# Special values in the table-based summary file. -555555555 in an MOE column
# means the estimate is controlled (no sampling error). Other negative codes
# mean "not available"; they become null.
MOE_CONTROLLED = -555555555


def read_acs_sf(path: str | Path, state_fips: str = "55", sumlevels=tuple(SUMLEVEL_TO_LEVEL)) -> pd.DataFrame:
    """Read one table-based summary file, keeping only rows for one state.

    Returns columns: geo_id, sumlevel, level, geoid, and every <TABLE>_E### /
    <TABLE>_M### column as float. Negative special codes become NaN, except
    controlled MOEs, which become 0 and are flagged in `<col>_controlled`.
    """
    path = Path(path)
    lines = []
    with open(path, encoding="utf-8") as f:
        header = f.readline().rstrip("\n")
        for line in f:
            gid = line.split("|", 1)[0]
            # GEO_ID = 3-digit summary level + "0000" (no geographic component) + "US" + GEOID
            if gid[:3] in sumlevels and gid[3:9] == "0000US" and gid[9:].startswith(state_fips):
                lines.append(line)
    df = pd.read_csv(io.StringIO(header + "\n" + "".join(lines)), sep="|", dtype=str)
    df = df.rename(columns={"GEO_ID": "geo_id"})
    df["sumlevel"] = df["geo_id"].str[:3]
    df["level"] = df["sumlevel"].map(SUMLEVEL_TO_LEVEL)
    df["geoid"] = df["geo_id"].str.split("US", n=1).str[1]
    for col in [c for c in df.columns if re.match(r"^[A-Z]\d{5}[A-Z]?_[EM]\d{3}$", c)]:
        vals = pd.to_numeric(df[col], errors="coerce")
        if "_M" in col:
            controlled = vals == MOE_CONTROLLED
            if controlled.any():
                df[col + "_controlled"] = controlled
            vals = vals.mask(controlled, 0.0)
        df[col] = vals.mask(vals < 0)
    return df


# ---------------------------------------------------------------------------
# Building Permits Survey annual text files
# ---------------------------------------------------------------------------

_SIZE_GROUPS = ("1unit", "2units", "3_4units", "5plus")
_MEASURES = ("bldgs", "units", "value")


def _bps_value_columns() -> list[str]:
    cols = [f"{g}_{m}" for g in _SIZE_GROUPS for m in _MEASURES]
    return cols + [f"{g}_{m}_rep" for g in _SIZE_GROUPS for m in _MEASURES]


BPS_STATE_ID_COLS = ["survey_date", "state_fips", "region", "division", "name"]
BPS_COUNTY_ID_COLS = ["survey_date", "state_fips", "county_fips", "region", "division", "name"]
BPS_PLACE_ID_COLS = [
    "survey_date", "state_fips", "bps_id", "county_fips", "census_place_code", "fips_place",
    "fips_mcd", "pop", "csa", "cbsa", "footnote", "central_city", "zip", "region", "division",
    "months_reported", "name",
]


def read_bps(path: str | Path, kind: str, state_fips: str | None = "55") -> pd.DataFrame:
    """Parse a BPS annual file. kind is 'state', 'county' or 'place'.

    The files have two header rows and a blank third row. Columns ending in
    `_rep` are the reported-only values; the plain columns include Census
    imputation for non-reporting months/places.
    """
    id_cols = {"state": BPS_STATE_ID_COLS, "county": BPS_COUNTY_ID_COLS, "place": BPS_PLACE_ID_COLS}[kind]
    names = id_cols + _bps_value_columns()
    df = pd.read_csv(path, skiprows=3, header=None, names=names, dtype=str, skip_blank_lines=True)
    df = df.dropna(subset=["survey_date"])
    for c in id_cols:
        df[c] = df[c].str.strip()
    if state_fips is not None:
        df = df[df["state_fips"] == state_fips].copy()
    for c in _bps_value_columns():
        df[c] = pd.to_numeric(df[c].str.strip(), errors="coerce")
    df["year"] = df["survey_date"].str[:4].astype(int)
    if kind == "place":
        df["months_reported"] = pd.to_numeric(df["months_reported"], errors="coerce")
        df["pop"] = pd.to_numeric(df["pop"], errors="coerce")
    df["units_total"] = df[[f"{g}_units" for g in _SIZE_GROUPS]].sum(axis=1)
    df["units_total_rep"] = df[[f"{g}_units_rep" for g in _SIZE_GROUPS]].sum(axis=1)
    df["units_2_4"] = df["2units_units"] + df["3_4units_units"]
    df["units_2_4_rep"] = df["2units_units_rep"] + df["3_4units_units_rep"]
    return df.reset_index(drop=True)


# ---------------------------------------------------------------------------
# Minimal .xlsx reader (stdlib only; openpyxl is not a project dependency)
# ---------------------------------------------------------------------------

_NS = {"m": "http://schemas.openxmlformats.org/spreadsheetml/2006/main"}


def _col_index(ref: str) -> int:
    letters = re.match(r"[A-Z]+", ref).group(0)
    n = 0
    for ch in letters:
        n = n * 26 + (ord(ch) - 64)
    return n - 1


def read_xlsx_first_sheet(path: str | Path) -> list[list]:
    """Return the first worksheet as a list of rows (strings or floats)."""
    with zipfile.ZipFile(path) as z:
        shared: list[str] = []
        if "xl/sharedStrings.xml" in z.namelist():
            root = ET.fromstring(z.read("xl/sharedStrings.xml"))
            for si in root.findall("m:si", _NS):
                shared.append("".join(t.text or "" for t in si.iter(f"{{{_NS['m']}}}t")))
        sheet = ET.fromstring(z.read("xl/worksheets/sheet1.xml"))
    rows = []
    for row in sheet.find("m:sheetData", _NS).findall("m:row", _NS):
        cells: dict[int, object] = {}
        for c in row.findall("m:c", _NS):
            v = c.find("m:v", _NS)
            if v is None:
                isel = c.find("m:is", _NS)
                if isel is not None:
                    cells[_col_index(c.get("r"))] = "".join(t.text or "" for t in isel.iter(f"{{{_NS['m']}}}t"))
                continue
            if c.get("t") == "s":
                cells[_col_index(c.get("r"))] = shared[int(v.text)]
            elif c.get("t") in ("str", "inlineStr"):
                cells[_col_index(c.get("r"))] = v.text
            else:
                cells[_col_index(c.get("r"))] = float(v.text)
        width = max(cells) + 1 if cells else 0
        rows.append([cells.get(i) for i in range(width)])
    return rows


def read_pep_housing_units(path: str | Path) -> pd.DataFrame:
    """Parse CO-EST2025-HU-<st>.xlsx into long form: name, year, housing_units.

    Row layout: a header row whose cells C.. are years; then one row per
    geography (state first, then '.County, State'). Column B is the April 1,
    2020 estimates base, which is not a July 1 estimate and is dropped.
    """
    rows = read_xlsx_first_sheet(path)
    year_row = next(r for r in rows if len(r) > 3 and isinstance(r[2], float) and 2000 < r[2] < 2100)
    years = {i: int(v) for i, v in enumerate(year_row) if isinstance(v, float) and 2000 < v < 2100}
    out = []
    started = False
    for r in rows:
        if r is year_row:
            started = True
            continue
        if not started or not r or not isinstance(r[0], str):
            continue
        name = r[0].lstrip(".").strip()
        vals = {years[i]: r[i] for i in years if i < len(r) and isinstance(r[i], float)}
        if not vals:
            continue
        for y, v in vals.items():
            out.append({"name": name, "year": y, "housing_units": v})
    return pd.DataFrame(out)
