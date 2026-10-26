"""Parking scenario for Wisconsin under option A (AQ-046, AQ-048).

For each municipality piece a and forecast year t (2027-2031):

    central   A[a,t] = 0                       (no measurable change in US repeal places)
    upper     A[a,t] = H[a] * u / 1000         (u = high end of the likely range, per 1,000 homes per year)

H is the area's existing homes (ACS 2020-2024 housing units). Places already at the benchmark
get 0 (a statewide law adds nothing there). A repeal never subtracts, so no case is below zero.
Years 4-5 hold the years 1-3 level (G2-2, an assumption). The baseline is the shared
all-housing baseline. Pure functions; scripts/run_parking_model.py does the I/O.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

FORECAST_YEARS = (2027, 2028, 2029, 2030, 2031)


def eligible_homes(areas: pd.DataFrame, at_benchmark: set, zero_types: tuple = ()) -> pd.Series:
    """Existing homes per area that a statewide repeal would reach. areas: area_id, homes,
    muni_type. at_benchmark: area_ids already at the benchmark (0). zero_types: muni types set
    to 0 in a sensitivity case (e.g. ("town",))."""
    h = areas.set_index("area_id")["homes"].astype(float).copy()
    h[h.index.isin(at_benchmark)] = 0.0
    if zero_types:
        h[areas.set_index("area_id")["muni_type"].isin(zero_types).values] = 0.0
    return h


def additions(homes: pd.Series, rate_per_1000: float | pd.Series, years=FORECAST_YEARS) -> pd.DataFrame:
    """Additional permits per area and year at a flat rate (permits per 1,000 homes per year),
    floored at zero. rate may be one number or a Series by area."""
    r = rate_per_1000 if isinstance(rate_per_1000, pd.Series) else pd.Series(rate_per_1000, index=homes.index)
    per_year = (homes * r.reindex(homes.index).fillna(0.0).clip(lower=0.0) / 1000.0)
    out = pd.DataFrame({y: per_year for y in years})
    out.index.name = "area_id"
    return out


def size_metro_rate(population: pd.Series, metro: pd.Series, beta) -> pd.Series:
    """Per-area effect from the size-and-metro model (intercept, log10 population, metro),
    floored at zero (sensitivity case for G2-3)."""
    b0, b1, b2 = beta
    lp = np.log10(np.maximum(population.astype(float), 1.0))
    return (b0 + b1 * lp + b2 * metro.astype(float)).clip(lower=0.0)
