"""Whole-city comparison of TOD reform cities with matched cities that made no such reform.

Plan: docs/tod/CONTROL_CITIES_PLAN.md (written before running). Outcome: homes permitted (Census
Building Permits Survey, all structure sizes) per 1,000 homes in 2010, per year.
"""
from __future__ import annotations

import io
import re
import zipfile
from dataclasses import dataclass
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.optimize import nnls

SEED = 20261028
DRAWS = 2000

# Reform cities (plan section 3). GEOID = 2010 Census place (state FIPS + place FIPS).
@dataclass(frozen=True)
class Reform:
    test: str
    city: str
    geoid: str
    year: int
    before: tuple[int, int]
    after: tuple[int, int]
    net_case: str          # row in reference/tod_net_effect_by_case.csv to compare with
    pooled_city: str       # city name used when averaging tests into one per city


REFORMS = [
    Reform("charlotte_2019", "Charlotte", "3712000", 2019, (2013, 2018), (2020, 2024), "charlotte_tod_2019", "Charlotte"),
    Reform("stpaul_2011", "Saint Paul", "2758000", 2011, (2005, 2010), (2012, 2016), "stpaul_green_line_2011", "Saint Paul"),
    Reform("los_angeles_2013", "Los Angeles", "0644000", 2013, (2007, 2012), (2014, 2018), "los_angeles_all_cases", "Los Angeles"),
    Reform("seattle_2012", "Seattle", "5363000", 2012, (2006, 2011), (2013, 2017), "seattle_nbh_othello_2012", "Seattle"),
    Reform("seattle_2014", "Seattle", "5363000", 2014, (2008, 2013), (2015, 2019), "seattle_mount_baker_2014", "Seattle"),
    Reform("chicago_2015", "Chicago", "1714000", 2015, (2009, 2014), (2016, 2020), "chicago_tod_2013_2015", "Chicago"),
    Reform("madison_2023", "Madison", "5548000", 2023, (2017, 2022), (2023, 2025), "madison_tod_overlay_2023", "Madison"),
]
# Pooled per-upzoned-home basis uses the city row (Seattle: both cases together).
POOLED_NET_CASE = {"Seattle": "seattle_all_cases"}

# Statewide transit-area density laws in force from this year (plan section 4).
STATE_LAW_YEAR = {"25": 2021, "41": 2022, "49": 2022, "24": 2024, "08": 2024, "53": 2025, "06": 2026, "09": 2026}
STATE_FIPS = {
    "Alabama": "01", "Alaska": "02", "Arizona": "04", "Arkansas": "05", "California": "06", "Colorado": "08",
    "Connecticut": "09", "Delaware": "10", "District of Columbia": "11", "Florida": "12", "Georgia": "13", "Hawaii": "15",
    "Idaho": "16", "Illinois": "17", "Indiana": "18", "Iowa": "19", "Kansas": "20", "Kentucky": "21", "Louisiana": "22",
    "Maine": "23", "Maryland": "24", "Massachusetts": "25", "Michigan": "26", "Minnesota": "27", "Mississippi": "28",
    "Missouri": "29", "Montana": "30", "Nebraska": "31", "Nevada": "32", "New Hampshire": "33", "New Jersey": "34",
    "New Mexico": "35", "New York": "36", "North Carolina": "37", "North Dakota": "38", "Ohio": "39", "Oklahoma": "40",
    "Oregon": "41", "Pennsylvania": "42", "Rhode Island": "44", "South Carolina": "45", "South Dakota": "46",
    "Tennessee": "47", "Texas": "48", "Utah": "49", "Vermont": "50", "Virginia": "51", "Washington": "53",
    "West Virginia": "54", "Wisconsin": "55", "Wyoming": "56",
}


# ---------------------------------------------------------------- reading
def read_bps_file(path: Path) -> pd.DataFrame:
    """One annual place file -> year, state, id6, name, months, units, units5 (columns located by header)."""
    lines = path.read_text(errors="replace").splitlines()
    h1, h2 = [c.strip() for c in lines[0].split(",")], [c.strip() for c in lines[1].split(",")]
    ni, mi = h2.index("Name"), h2.index("Months Rep")
    fips = h1.index("FIPS Place") if "FIPS Place" in h1 else None
    cbsa = h1.index("CBSA") if "CBSA" in h1 else None
    rows = []
    for line in lines[2:]:
        c = line.split(",")
        if len(c) < ni + 12 or not c[0].strip().isdigit():
            continue
        u = [int(float(c[ni + k] or 0)) for k in (2, 5, 8, 11)]
        rows.append({"year": int(c[0]), "state": c[1].strip().zfill(2), "id6": c[2].strip(), "name": c[ni].strip(),
                     "months": int(float(c[mi] or 0)), "units": sum(u), "units5": u[3],
                     "fips_place": c[fips].strip() if fips is not None else None,
                     "cbsa": c[cbsa].strip() if cbsa is not None else None})
    return pd.DataFrame(rows)


def read_bps(folder: Path, years=range(2000, 2026)) -> pd.DataFrame:
    return pd.concat([read_bps_file(folder / f"{r}{y}a.txt") for y in years for r in ("mw", "ne", "so", "we")],
                     ignore_index=True)


def read_gazetteer(zip_path: Path) -> pd.DataFrame:
    with zipfile.ZipFile(zip_path) as z:
        name = [n for n in z.namelist() if n.endswith(".txt")][0]
        g = pd.read_csv(io.BytesIO(z.read(name)), sep="\t", dtype={"GEOID": str}, encoding="latin-1")
    g.columns = [c.strip() for c in g.columns]
    return g[["USPS", "GEOID", "NAME", "HU10"]].rename(columns={"GEOID": "geoid", "NAME": "place_name", "HU10": "hu10"})


# Charlotte's permits are issued and reported by one county-wide office (Mecklenburg County, BPS id 379000),
# so Charlotte is measured as that office, per 1,000 county homes (plan section 9, item 1).
COUNTY_OFFICES = {"3712000": ("37", "379000", "37119")}


def read_county_hu(zip_path: Path) -> dict[str, int]:
    with zipfile.ZipFile(zip_path) as z:
        name = [n for n in z.namelist() if n.endswith(".txt")][0]
        g = pd.read_csv(io.BytesIO(z.read(name)), sep="\t", dtype={"GEOID": str}, encoding="latin-1")
    g.columns = [c.strip() for c in g.columns]
    return dict(zip(g["GEOID"], g["HU10"]))


def link(bps: pd.DataFrame, gaz: pd.DataFrame, county_hu: dict[str, int] | None = None) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Permit place id -> 2010 Census place, via FIPS place codes in the 2012+ files (latest year wins)."""
    recent = bps[(bps["year"] >= 2012) & bps["fips_place"].notna()].sort_values("year")
    recent = recent[recent["fips_place"].str.fullmatch(r"\d{5}") & ~recent["fips_place"].isin(["00000", "99990", "99999"])]
    ids = recent.groupby(["state", "id6"]).last()[["fips_place", "cbsa"]].reset_index()
    ids["geoid"] = ids["state"] + ids["fips_place"]
    ids = ids.merge(gaz[["geoid", "hu10", "place_name"]], on="geoid", how="inner")
    # A row with 0 months reported and 0 homes is a non-report, not a Census imputation: treat as missing.
    bps = bps[~((bps["months"] == 0) & (bps["units"] == 0))]
    panel = bps.merge(ids[["state", "id6", "geoid"]], on=["state", "id6"], how="inner")
    panel = panel.groupby(["geoid", "year"], as_index=False)[["units", "units5"]].sum()
    places = ids.groupby("geoid").agg(state=("state", "first"), cbsa=("cbsa", "last"), hu10=("hu10", "first"),
                                      place_name=("place_name", "first")).reset_index()
    places["office_hu10"] = places["hu10"]
    for geoid, (st, id6, county) in COUNTY_OFFICES.items():
        if county_hu is None:
            continue
        rows = bps[(bps["state"] == st) & (bps["id6"] == id6)]
        add = rows.groupby("year", as_index=False)[["units", "units5"]].sum().assign(geoid=geoid)
        panel = pd.concat([panel[panel["geoid"] != geoid], add], ignore_index=True)
        g = gaz.set_index("geoid").loc[geoid]
        cbsa = rows.sort_values("year")["cbsa"].dropna().iloc[-1]
        places = pd.concat([places[places["geoid"] != geoid], pd.DataFrame([{
            "geoid": geoid, "state": st, "cbsa": cbsa, "hu10": g["hu10"], "place_name": g["place_name"],
            "office_hu10": county_hu[county]}])], ignore_index=True)
    places = places[places["hu10"] > 0]
    return panel, places


def inventory_geoids(inv: pd.DataFrame, gaz: pd.DataFrame) -> set[str]:
    """US cities in the TOD case inventory -> 2010 Census place GEOIDs (by state and name)."""
    out = set()
    g = gaz.copy()
    g["base"] = g["place_name"].str.replace(r"\s*\(balance\)", "", regex=True).str.replace(
        r"\s+(city|town|village|borough|municipality|CDP|city and borough)$", "", regex=True).str.strip()
    g["base"] = g["base"].str.replace(r"^(.*)/.*$", r"\1", regex=True).str.replace(r"\s+(metropolitan government|unified government).*$", "", regex=True)
    for _, r in inv[inv["country"] == "US"].iterrows():
        st = STATE_FIPS.get(str(r["state_or_province"]).strip())
        city = re.sub(r"\s*\(.*\)", "", str(r["city"])).strip().replace("Saint ", "St. ")
        names = [n.strip() for n in re.split(r",| and ", city.replace("and smaller towns", "")) if n.strip()]
        for n in names:
            hit = g[(g["geoid"].str[:2] == st) & (g["base"].str.lower() == n.lower())]
            out.update(hit["geoid"])
    return out


# ---------------------------------------------------------------- estimates
def years(a: tuple[int, int]) -> list[int]:
    return list(range(a[0], a[1] + 1))


def rates(panel: pd.DataFrame, places: pd.DataFrame, col: str = "units") -> pd.DataFrame:
    """Wide table: rows geoid, columns year, value = permits per 1,000 2010 homes."""
    w = panel.pivot(index="geoid", columns="year", values=col)
    hu = places.set_index("geoid")["office_hu10"].reindex(w.index)
    return w.div(hu, axis=0) * 1000


def eligible(rf: Reform, R: pd.DataFrame, places: pd.DataFrame, inv: set[str], same_metro: bool = False,
             before=None, after=None) -> pd.DataFrame:
    """Plan section 4. Returns the eligible places table (with hu10, cbsa)."""
    before, after = before or rf.before, after or rf.after
    yrs = years(before) + years(after)
    p = places.set_index("geoid")
    ok = R.reindex(columns=yrs).notna().all(axis=1)
    cand = p.loc[p.index.intersection(R.index[ok])]
    t = p.loc[rf.geoid]
    reform_ids = {r.geoid for r in REFORMS}
    last = after[1]
    keep = ~cand.index.isin(reform_ids | inv)
    keep &= ~cand["state"].map(lambda s: STATE_LAW_YEAR.get(s, 9999) <= last).to_numpy()
    if not same_metro:
        keep &= ~((cand["cbsa"] == t["cbsa"]) & (t["cbsa"] not in ("99999", "", None))).to_numpy()
    cand = cand[keep]
    lo, hi = t["hu10"] / 4, t["hu10"] * 4
    while ((cand["hu10"] >= lo) & (cand["hu10"] <= hi)).sum() < 10 and (lo > 1 or hi < 1e8):
        lo, hi = lo / 1.5, hi * 1.5
    return cand[(cand["hu10"] >= lo) & (cand["hu10"] <= hi)]


def features(R: pd.DataFrame, ids, before) -> pd.DataFrame:
    by = years(before)
    X = R.loc[ids, by]
    x = np.array(by, dtype=float) - np.mean(by)
    slope = (X.to_numpy() - X.to_numpy().mean(axis=1, keepdims=True)) @ x / (x @ x)
    return pd.DataFrame({"mean": X.mean(axis=1).to_numpy(), "slope": slope}, index=ids)


def nearest(R: pd.DataFrame, target: str, pool: list[str], before, k: int) -> list[str]:
    F = features(R, [target, *pool], before)
    sd = F.loc[pool].std(ddof=0).replace(0, 1)
    d = (((F.loc[pool] - F.loc[target]) / sd) ** 2).sum(axis=1) ** 0.5
    return list(d.sort_values(kind="mergesort").index[:k])


def did(R: pd.DataFrame, target: str, controls: list[str], before, after) -> float:
    b, a = years(before), years(after)
    tgt = R.loc[target, a].mean() - R.loc[target, b].mean()
    ctl = (R.loc[controls, a].mean(axis=1) - R.loc[controls, b].mean(axis=1)).mean()
    return float(tgt - ctl)


def synth(R: pd.DataFrame, target: str, pool: list[str], before, after, k: int = 50) -> tuple[float, dict]:
    donors = nearest(R, target, pool, before, min(k, len(pool)))
    b, a = years(before), years(after)
    A = R.loc[donors, b].to_numpy().T
    y = R.loc[target, b].to_numpy()
    big = 1e3 * max(1.0, float(np.abs(A).max()))
    w, _ = nnls(np.vstack([A, big * np.ones(len(donors))]), np.append(y, big))
    w = w / w.sum() if w.sum() > 0 else np.full(len(donors), 1 / len(donors))
    gap_b = y - A @ w
    gap_a = R.loc[target, a].to_numpy() - R.loc[donors, a].to_numpy().T @ w
    return float(gap_a.mean() - gap_b.mean()), dict(zip(donors, w))


def estimate(R, target, pool, before, after, method: str, k: int = 10) -> float:
    if method == "matched":
        return did(R, target, nearest(R, target, pool, before, k), before, after)
    return synth(R, target, pool, before, after)[0]


def placebos(R, pool: list[str], places: pd.DataFrame, before, after, method: str, k: int = 10,
             same_metro: bool = False) -> pd.Series:
    """Fake reform in each eligible place; its controls come from the other eligible places (plan section 6)."""
    cb = places.set_index("geoid")["cbsa"]
    out = {}
    for p in pool:
        others = [q for q in pool if q != p and (same_metro or cb.get(q) != cb.get(p) or cb.get(p) == "99999")]
        out[p] = estimate(R, p, others, before, after, method, k)
    return pd.Series(out)


def to_5yr_share(effect_per_1000_per_year: float, office_hu: float = 1.0, city_hu: float = 1.0) -> float:
    """Per 1,000 permit-office homes per year -> % of the city's homes over five years."""
    return effect_per_1000_per_year * 5 / 10 * office_hu / city_hu
