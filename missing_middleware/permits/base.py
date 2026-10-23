"""City-adapter interface for the permit pipeline.

A city plugs in by subclassing `CityAdapter` and returning, from
`load_permits`, one row per raw source record with `STANDARD_COLUMNS`.
Everything downstream (dedupe, address normalization, classification,
parcel match, area attach, aggregation) works on that frame plus a parcel
table with `PARCEL_COLUMNS` and an address-point table with
`ADDRESS_POINT_COLUMNS`.
"""
from __future__ import annotations

from pathlib import Path

import pandas as pd

STANDARD_COLUMNS = (
    "permit_id",       # source permit number (string, as published)
    "permit_type",     # source permit class/prefix, e.g. BLDNRC
    "use_class",       # source use class text
    "address_raw",     # site address as published (internal only)
    "units_raw",       # dwelling units on the record (float/NaN)
    "description",     # free-text work description
    "issue_date",      # datetime64, permit issuance
    "est_cost",
    "bldg_sqft",
    "jurisdiction_id",
    "source_id",
)

# Parcel table, one row per parcel, built by the adapter from local GIS.
PARCEL_COLUMNS = (
    "parcel_id", "address", "house_nbr", "street_key", "unit", "dwelling_units",
    "property_class", "property_use", "zoning", "year_built", "geometry",
)
ADDRESS_POINT_COLUMNS = ("house_nbr", "street_key", "unit", "parcel_id", "geometry")


class CityAdapter:
    source_id: str = ""
    parcel_source_id: str = ""
    jurisdiction_id: str = ""
    jurisdiction_name: str = ""
    state_fips: str = ""
    county_fips: tuple[str, ...] = ()
    # permit types that can carry new dwelling units (others are repairs/razes)
    new_residential_types: tuple[str, ...] = ()

    def load_permits(self, raw_dir: Path) -> pd.DataFrame:  # pragma: no cover - interface
        raise NotImplementedError
