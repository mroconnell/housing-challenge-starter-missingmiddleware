"""Permit-to-parcel address matching (city-agnostic).

Inputs: a permit frame with `address_raw`, a reference table of addresses
(`house_nbr`, `street_key`, `unit`, `parcel_id`, `address_full`, `x`, `y`)
built by the adapter from the city's address points and parcels, and a set
of known parcel ids.

Tolerances (fixed before evaluation; documented in MADISON_PERMITS.md):

* address_exact / confirmed: cleaned permit address string equals a cleaned
  reference address string (with or without the word UNIT) and all hits
  resolve to one parcel.
* address_normalized / confirmed: parsed house number + full street key
  (direction, name, type) equals a reference key; one parcel (directly, or
  after narrowing by the permit's unit suffix).
* address_normalized / probable: one relaxation needed to reach one parcel:
  (a) other number of a hyphenated range, (b) street type ignored when the
  name+direction identify a single street with that house number, or
  (c) direction ignored likewise.
* ambiguous: the best key resolves to 2+ parcels and the unit does not narrow
  it. No parcel is assigned; the area is assigned only if every candidate
  parcel lies in the same block group.
* geocode / probable: no key match, but the same street key has a reference
  address with the same parity within +/-10 house numbers; the nearest such
  address point locates the permit for area attachment only (no parcel).
* unmatched / none: everything else.
"""
from __future__ import annotations

from collections import defaultdict

import pandas as pd

from .address import clean, parse

GEOCODE_MAX_NUMBER_GAP = 10


class AddressIndex:
    def __init__(self, ref: pd.DataFrame):
        ref = ref.dropna(subset=["house_nbr", "street_key", "parcel_id"]).copy()
        ref["house_nbr"] = ref["house_nbr"].astype(int)
        self.ref = ref
        self.street_keys = set(ref["street_key"])
        self.by_key: dict[tuple[int, str], set[str]] = defaultdict(set)
        self.by_key_unit: dict[tuple[int, str, str], set[str]] = defaultdict(set)
        self.by_exact: dict[str, set[str]] = defaultdict(set)
        self.by_name: dict[tuple[int, str], set[str]] = defaultdict(set)      # no type
        self.by_nodir: dict[tuple[int, str], set[str]] = defaultdict(set)     # no direction
        self.numbers: dict[str, list[tuple[int, float, float]]] = defaultdict(list)
        for r in ref.itertuples(index=False):
            k = (r.house_nbr, r.street_key)
            self.by_key[k].add(r.parcel_id)
            unit = clean(r.unit or "")
            if unit:
                self.by_key_unit[(r.house_nbr, r.street_key, unit)].add(r.parcel_id)
            full = clean(r.address_full or "")
            if full:
                self.by_exact[full].add(r.parcel_id)
                self.by_exact[full.replace(" UNIT ", " ")].add(r.parcel_id)
            p = parse(f"{r.house_nbr} {r.street_key}", self.street_keys)
            self.by_name[(r.house_nbr, " ".join(x for x in (p.pre_dir, p.street) if x))].add(r.street_key)
            self.by_nodir[(r.house_nbr, " ".join(x for x in (p.street, p.street_type) if x))].add(r.street_key)
            self.numbers[r.street_key].append((r.house_nbr, r.x, r.y))

    def match_one(self, raw: str) -> dict:
        p = parse(raw, self.street_keys)
        base = {"addr_house_nbr": p.house_nbr, "addr_street_key": p.street_key, "addr_unit": p.unit,
                "addr_flags": ",".join(p.flags), "parcel_id": None, "candidate_parcels": None,
                "match_method": "unmatched", "match_quality": "none", "match_rule": "no_match",
                "geo_x": None, "geo_y": None}
        exact = self.by_exact.get(clean(raw))
        if exact and len(exact) == 1:
            return {**base, "parcel_id": next(iter(exact)), "match_method": "address_exact",
                    "match_quality": "confirmed", "match_rule": "exact_string"}
        if p.house_nbr is None:
            return {**base, "match_rule": "no_house_number"}

        def resolve(cands: set[str], method: str, quality: str, rule: str, key=None) -> dict | None:
            if not cands:
                return None
            if len(cands) > 1 and key and p.unit:
                narrowed = self.by_key_unit.get((key[0], key[1], clean(p.unit)))
                if narrowed and len(narrowed) == 1:
                    return {**base, "parcel_id": next(iter(narrowed)), "match_method": method,
                            "match_quality": quality, "match_rule": rule + "+unit"}
            if len(cands) == 1:
                return {**base, "parcel_id": next(iter(cands)), "match_method": method,
                        "match_quality": quality, "match_rule": rule}
            return {**base, "candidate_parcels": ";".join(sorted(cands)), "match_method": method,
                    "match_quality": "ambiguous", "match_rule": rule + ":multi"}

        key = (p.house_nbr, p.street_key)
        res = resolve(self.by_key.get(key, set()), "address_normalized", "confirmed", "key", key)
        if res:
            if exact and res["match_quality"] == "confirmed":
                res["match_method"] = "address_exact"
            return res
        for alt in p.house_alt[1:]:  # (a) range alternates
            res = resolve(self.by_key.get((alt, p.street_key), set()), "address_normalized", "probable",
                          "range_alt", (alt, p.street_key))
            if res:
                return res
        name_key = " ".join(x for x in (p.pre_dir, p.street) if x)
        streets = self.by_name.get((p.house_nbr, name_key), set())  # (b) type ignored
        if len(streets) == 1:
            sk = next(iter(streets))
            res = resolve(self.by_key[(p.house_nbr, sk)], "address_normalized", "probable", "type_ignored",
                          (p.house_nbr, sk))
            if res:
                return res
        nodir_key = " ".join(x for x in (p.street, p.street_type) if x)
        streets = self.by_nodir.get((p.house_nbr, nodir_key), set())  # (c) direction ignored
        if len(streets) == 1:
            sk = next(iter(streets))
            res = resolve(self.by_key[(p.house_nbr, sk)], "address_normalized", "probable", "dir_ignored",
                          (p.house_nbr, sk))
            if res:
                return res
        nums = self.numbers.get(p.street_key)
        if nums:
            same = [(abs(n - p.house_nbr), n, x, y) for n, x, y in nums
                    if n % 2 == p.house_nbr % 2 and abs(n - p.house_nbr) <= GEOCODE_MAX_NUMBER_GAP]
            if same:
                gap, n, x, y = min(same)
                return {**base, "match_method": "geocode", "match_quality": "probable",
                        "match_rule": f"nearest_number_gap_{gap}", "geo_x": x, "geo_y": y}
        return {**base, "match_rule": "street_unknown" if "street_unknown" in p.flags else "number_not_found"}


def match_addresses(permits: pd.DataFrame, index: AddressIndex) -> pd.DataFrame:
    cache: dict[str, dict] = {}
    rows = []
    for raw in permits["address_raw"]:
        if raw not in cache:
            cache[raw] = index.match_one(raw)
        rows.append(cache[raw])
    return pd.DataFrame(rows, index=permits.index)
