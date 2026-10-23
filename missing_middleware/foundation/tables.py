"""Inventory and state_conditions tables, plus the additivity check.

Pure functions over parsed source frames (see parsers.py), so they can be
tested on small fixtures.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

ACS_SOURCE_ID = "census_acs5_2024_tbsf"
ACS_VINTAGE = "ACS 2020-2024 5-year"
ACS_YEAR = 2024  # end year of the 5-year period, used as `year` in state_conditions
PEP_SOURCE_ID = "census_pep_v2025_hu"
PEP_VINTAGE = "PEP Vintage 2025"
BPS_VINTAGE = "BPS annual {year} (final)"

LEVELS_INVENTORY = ("state", "county", "municipality", "tract", "block_group")
LEVELS_CONDITIONS = ("state", "county", "municipality")


def area_id_for(level: str, geoid: str) -> str:
    return f"muni:{geoid}" if level == "municipality" else geoid


def rss(*moes) -> pd.Series:
    """Root-sum-of-squares MOE for a sum of estimates (Census approximation)."""
    return np.sqrt(sum(pd.Series(m, dtype=float) ** 2 for m in moes))


def proportion_moe(num, num_moe, den, den_moe) -> pd.Series:
    """Census formula for the MOE of a proportion; falls back to the ratio formula
    when the term under the root is negative."""
    num, num_moe, den, den_moe = (pd.Series(x, dtype=float) for x in (num, num_moe, den, den_moe))
    p = num / den
    under = num_moe**2 - p**2 * den_moe**2
    ratio = num_moe**2 + p**2 * den_moe**2
    return np.sqrt(under.where(under >= 0, ratio)) / den


# ---------------------------------------------------------------------------
# inventory
# ---------------------------------------------------------------------------

def build_inventory(b25024: pd.DataFrame) -> pd.DataFrame:
    d = b25024[b25024["level"].isin(LEVELS_INVENTORY)].copy()
    out = pd.DataFrame({
        "area_id": [area_id_for(lv, g) for lv, g in zip(d["level"], d["geoid"])],
        "geoid": d["geoid"].values,
        "level": d["level"].values,
        "homes_1unit_detached": d["B25024_E002"].values,
        "homes_1unit_detached_moe": d["B25024_M002"].values,
        "homes_1unit_attached": d["B25024_E003"].values,
        "homes_1unit_attached_moe": d["B25024_M003"].values,
        "total_housing_units": d["B25024_E001"].values,
        "total_housing_units_moe": d["B25024_M001"].values,
    })
    out["total_housing_units_source"] = "ACS 2020-2024 5-year B25024_001 (all units in structure)"
    out["parcel_proxy_count"] = pd.array([pd.NA] * len(out), dtype="Int64")
    out["parcel_to_acs_ratio"] = np.nan
    out["cv_1unit_detached"] = out["homes_1unit_detached_moe"] / 1.645 / out["homes_1unit_detached"].where(out["homes_1unit_detached"] > 0)
    out["method_note"] = (
        "Published ACS B25024_002 estimate for this geography (control total). "
        "Parcel-proxy allocation not yet applied (set at Gate 2 against assessor data)."
    )
    out["missing_reason"] = np.where(out["homes_1unit_detached"].isna(), "not_reported", None)
    out["status"] = "observed"
    out["source_id"] = ACS_SOURCE_ID
    out["source_vintage"] = ACS_VINTAGE
    return out.reset_index(drop=True)


def check_additivity(inv: pd.DataFrame, cols=("homes_1unit_detached", "homes_1unit_attached", "total_housing_units")) -> pd.DataFrame:
    """Compare sums of child geographies to their parent's published estimate.

    Children are grouped by GEOID prefix: block group -> tract (11), tract ->
    county (5), municipality -> county (5), county -> state (2).
    Returns one row per (check, parent, column) with child_sum, parent_value, diff.
    """
    pairs = [("block_group", "tract", 11), ("tract", "county", 5), ("municipality", "county", 5), ("county", "state", 2)]
    frames = []
    for child, parent, n in pairs:
        c = inv[inv["level"] == child].assign(parent_geoid=lambda x: x["geoid"].str[:n])
        sums = c.groupby("parent_geoid")[list(cols)].sum(min_count=1)
        p = inv[inv["level"] == parent].set_index("geoid")[list(cols)]
        for col in cols:
            j = pd.DataFrame({"child_sum": sums[col], "parent_value": p[col]})
            j["check"] = f"{child}->{parent}"
            j["column"] = col
            j["diff"] = j["child_sum"] - j["parent_value"]
            frames.append(j.reset_index(names="parent_geoid"))
    return pd.concat(frames, ignore_index=True)[["check", "column", "parent_geoid", "child_sum", "parent_value", "diff"]]


# ---------------------------------------------------------------------------
# state_conditions
# ---------------------------------------------------------------------------

def _rows(area_ids, year, indicator, value, moe, period_type, status, source_id, vintage, **extra) -> pd.DataFrame:
    df = pd.DataFrame({
        "area_id": list(area_ids),
        "year": year,
        "indicator": indicator,
        "value": pd.Series(value, dtype=float).values,
        "moe": pd.Series(moe, dtype=float).values if moe is not None else np.nan,
        "period_type": period_type,
        "status": status,
        "source_id": source_id,
        "source_vintage": vintage,
    })
    for k, v in extra.items():
        df[k] = v.values if isinstance(v, pd.Series) else v
    return df


def acs_conditions(b25024: pd.DataFrame, b25002: pd.DataFrame, b25034: pd.DataFrame | None = None) -> pd.DataFrame:
    frames = []
    keep = lambda d: d[d["level"].isin(LEVELS_CONDITIONS)].reset_index(drop=True)
    u, o = keep(b25024), keep(b25002)
    ids = lambda d: [area_id_for(lv, g) for lv, g in zip(d["level"], d["geoid"])]
    args = dict(year=ACS_YEAR, period_type="acs_5yr", source_id=ACS_SOURCE_ID, vintage=ACS_VINTAGE)
    observed = {
        "total_housing_units_acs": ("B25024", "001"),
        "units_1_detached": ("B25024", "002"),
        "units_1_attached": ("B25024", "003"),
        "mobile_home": ("B25024", "010"),
    }
    for ind, (_, line) in observed.items():
        frames.append(_rows(ids(u), indicator=ind, value=u[f"B25024_E{line}"], moe=u[f"B25024_M{line}"], status="observed", **args))
    frames.append(_rows(ids(u), indicator="units_2_4", value=u["B25024_E004"] + u["B25024_E005"],
                        moe=rss(u["B25024_M004"], u["B25024_M005"]), status="calculated", **args))
    five = [f"{i:03d}" for i in range(6, 10)]
    frames.append(_rows(ids(u), indicator="units_5_plus", value=sum(u[f"B25024_E{x}"] for x in five),
                        moe=rss(*[u[f"B25024_M{x}"] for x in five]), status="calculated", **args))
    frames.append(_rows(ids(o), indicator="occupied_units", value=o["B25002_E002"], moe=o["B25002_M002"], status="observed", **args))
    frames.append(_rows(ids(o), indicator="vacant_units", value=o["B25002_E003"], moe=o["B25002_M003"], status="observed", **args))
    tot = o["B25002_E001"].where(o["B25002_E001"] > 0)
    frames.append(_rows(ids(o), indicator="vacancy_rate", value=o["B25002_E003"] / tot,
                        moe=proportion_moe(o["B25002_E003"], o["B25002_M003"], tot, o["B25002_M001"]),
                        status="calculated", **args))
    if b25034 is not None:
        y = keep(b25034)
        bands = {
            "built_2020_or_later": "002", "built_2010_2019": "003", "built_2000_2009": "004",
            "built_1990_1999": "005", "built_1980_1989": "006", "built_1970_1979": "007",
            "built_1960_1969": "008", "built_1950_1959": "009", "built_1940_1949": "010",
            "built_1939_or_earlier": "011",
        }
        for ind, line in bands.items():
            frames.append(_rows(ids(y), indicator=ind, value=y[f"B25034_E{line}"], moe=y[f"B25034_M{line}"], status="observed", **args))
    out = pd.concat(frames, ignore_index=True)
    out["reporting_coverage"] = np.nan
    return out


def pep_conditions(pep: pd.DataFrame, county_name_to_geoid: dict[str, str]) -> tuple[pd.DataFrame, list[str]]:
    """PEP housing units (July 1 estimates) for state and counties."""
    def to_id(name: str):
        if name == "Wisconsin":
            return "55"
        return county_name_to_geoid.get(name.replace(", Wisconsin", "").strip())
    p = pep.copy()
    p["area_id"] = p["name"].map(to_id)
    unmatched = sorted(p.loc[p["area_id"].isna(), "name"].unique())
    p = p.dropna(subset=["area_id"])
    out = pd.DataFrame({
        "area_id": p["area_id"], "year": p["year"].astype(int), "indicator": "housing_units",
        "value": p["housing_units"].astype(float), "moe": np.nan, "period_type": "point_in_time",
        "status": "observed", "source_id": PEP_SOURCE_ID, "source_vintage": PEP_VINTAGE,
        "reporting_coverage": np.nan,
    })
    return out.reset_index(drop=True), unmatched


BPS_INDICATORS = {
    "permitted_units_total": "units_total",
    "permitted_units_1unit": "1unit_units",
    "permitted_units_2_4": "units_2_4",
    "permitted_units_5plus": "5plus_units",
}


def bps_conditions(bps: pd.DataFrame, area_ids: pd.Series, source_id: str, coverage: pd.Series,
                   coverage_basis: str, geography_note: pd.Series | str | None = None) -> pd.DataFrame:
    """Long-form BPS indicator rows. `bps` rows align with `area_ids` and `coverage`."""
    frames = []
    for ind, col in BPS_INDICATORS.items():
        df = pd.DataFrame({
            "area_id": area_ids.values, "year": bps["year"].astype(int).values, "indicator": ind,
            "value": bps[col].astype(float).values, "moe": np.nan, "period_type": "annual",
            "status": "observed", "source_id": source_id,
            "source_vintage": [BPS_VINTAGE.format(year=y) for y in bps["year"]],
            "reporting_coverage": coverage.values, "coverage_basis": coverage_basis,
        })
        if geography_note is not None:
            df["geography_note"] = geography_note.values if isinstance(geography_note, pd.Series) else geography_note
        frames.append(df)
    return pd.concat(frames, ignore_index=True)


def units_reported_share(bps: pd.DataFrame) -> pd.Series:
    """Share of authorized units that came from reported (not imputed) months/places."""
    return (bps["units_total_rep"] / bps["units_total"].where(bps["units_total"] > 0)).clip(upper=1.0)
