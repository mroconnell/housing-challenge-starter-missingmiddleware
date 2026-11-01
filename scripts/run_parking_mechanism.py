"""Parking: per-project (mechanism) estimate (docs/parking/MECHANISM_PLAN.md).

    uv run python scripts/run_parking_mechanism.py part_a      # measured project size, 76 repeal places (+ placebo; long)
    uv run python scripts/run_parking_mechanism.py summarise_a # summaries, held-out test, placebo position
    uv run python scripts/run_parking_mechanism.py part_c      # where Wisconsin minimums still bind
    uv run python scripts/run_parking_mechanism.py part_b      # cost chain draws and its held-out checks

Checkpoints: data/interim/parking_mechanism/. Outputs: reference/parking_mechanism_*.csv
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
sys.path.insert(0, str(Path(__file__).resolve().parent))

import run_parking_comparison as rpc  # noqa: E402
from missing_middleware.parking import comparison as cmp  # noqa: E402
from missing_middleware.paths import RAW, REFERENCE  # noqa: E402

SEED = 20261101
CKPT = Path(__file__).resolve().parent.parent / "data" / "interim" / "parking_mechanism"
CKPT.mkdir(parents=True, exist_ok=True)
MAX_PARTNERS = 40
PLACEBO_SETS = 20_000
MIN_BLDGS = 2  # 5+ unit buildings needed in each window, in the place and in its comparison group


# ---------------------------------------------------------------- panel and inputs
def panel_full() -> pd.DataFrame:
    """One row per place-year: units (all, 2-4, 5+) and 5+ buildings. Same place filter as cmp.panel."""
    d = rpc.read_bps_us()
    for c in ("state_fips", "bps_id", "county_fips", "fips_place", "fips_mcd", "name", "division"):
        d[c] = d[c].astype(str).str.strip()
    d = d[d["fips_place"] != "99990"].copy()
    d["key"] = d["state_fips"] + "|" + d["bps_id"]
    d["acs_geoid"] = np.where(d["fips_place"].str.strip("0") != "",
                              "160|" + d["state_fips"] + d["fips_place"].str.zfill(5),
                              "060|" + d["state_fips"] + d["county_fips"].str.zfill(3) + d["fips_mcd"].str.zfill(5))
    d["u5"] = d["5plus_units"]
    d["b5"] = d["5plus_bldgs"]
    d["u24"] = d["2units_units"] + d["3_4units_units"]
    d["units_2plus"] = d["u24"] + d["u5"]
    keep = ["key", "state_fips", "division", "bps_id", "name", "county_fips", "fips_place", "fips_mcd", "acs_geoid",
            "year", "pop", "units_total", "units_2plus", "u24", "u5", "b5"]
    return d[keep].drop_duplicates(["key", "year"]).reset_index(drop=True)


def acs_inputs(p: pd.DataFrame):
    homes_geo = rpc.acs_table(RAW / "census_acs5_2024_tbsf" / "acsdt5y2024-b25002.dat", "B25002_E001")
    pop_geo = rpc.acs_table(RAW / "census_acs5_2024_tbsf" / "acsdt5y2024-b01003.dat", "B01003_E001")
    geo = p.drop_duplicates("key", keep="last").set_index("key")
    homes = geo["acs_geoid"].map(homes_geo)
    homes = homes[homes > 0]
    popn = geo["acs_geoid"].map(pop_geo)
    return homes, popn


def excluded_keys(p: pd.DataFrame, real: pd.DataFrame) -> set:
    """Every place with an apartment-scale repeal (taxonomy at/near city rows) and every real case."""
    tax = pd.read_csv(REFERENCE / "parking_reform_taxonomy.csv")
    ref = tax[(tax["policy"] == "rm_min") & tax["benchmark_rating"].isin(["at", "near"]) & (tax["place_type"] == "city")]
    out = set(real["key"])
    for r in ref.drop_duplicates("prn_key").itertuples():
        k = cmp.match_place(p, rpc.STATE_FIPS.get(r.state, "??"), r.place, r.population)
        if k:
            out.add(k)
    return out


# ---------------------------------------------------------------- outcomes
class Sums:
    """Fast window sums: index (key, year) -> columns."""

    def __init__(self, p: pd.DataFrame):
        self.t = p.set_index(["key", "year"])[["units_total", "u24", "u5", "b5"]].sort_index()

    def total(self, keys, years) -> pd.Series:
        idx = pd.MultiIndex.from_product([list(keys), list(years)], names=["key", "year"])
        return self.t.reindex(idx).sum()


def outcomes(S: Sums, key: str, ctrl: list, pre, post, homes: pd.Series) -> dict:
    tp, ta = S.total([key], pre), S.total([key], post)
    cp, ca = S.total(ctrl, pre), S.total(ctrl, post)
    h, hc = float(homes[key]), float(homes.reindex(ctrl).sum())
    npre, npost = len(pre), len(post)

    def rate(s, col, n, hh):
        return s[col] / n / hh * 1000 if hh else np.nan
    out = dict(homes=h, n_pre=npre, n_post=npost, n_controls=len(ctrl),
               b5_before=float(tp["b5"]), b5_after=float(ta["b5"]), u5_before=float(tp["u5"]), u5_after=float(ta["u5"]),
               cb5_before=float(cp["b5"]), cb5_after=float(ca["b5"]), cu5_before=float(cp["u5"]), cu5_after=float(ca["u5"]))
    ok = min(tp["b5"], ta["b5"]) >= MIN_BLDGS and min(cp["b5"], ca["b5"]) >= MIN_BLDGS
    out["A1_size_before"] = tp["u5"] / tp["b5"] if tp["b5"] else np.nan
    out["A1_size_after"] = ta["u5"] / ta["b5"] if ta["b5"] else np.nan
    out["A1"] = (np.log(ta["u5"] / ta["b5"]) - np.log(tp["u5"] / tp["b5"])
                 - (np.log(ca["u5"] / ca["b5"]) - np.log(cp["u5"] / cp["b5"]))) if ok else np.nan
    out["A1_weight"] = float(tp["b5"] + ta["b5"]) if ok else 0.0
    for col, lab in (("u24", "A2"), ("b5", "A3"), ("units_total", "ALL"), ("u5", "U5")):
        out[lab] = (rate(ta, col, npost, h) - rate(tp, col, npre, h)) - (rate(ca, col, npost, hc) - rate(cp, col, npre, hc))
        out[lab + "_before"] = rate(tp, col, npre, h)
        out[lab + "_ctrl_before"] = rate(cp, col, npre, hc)
    out["AB_weight"] = h * npost
    return out


def case_rows(p, S, cases: pd.DataFrame, excluded, homes, popn, label: str) -> pd.DataFrame:
    rows = []
    complete_cache = {}
    for r in cases.itertuples(index=False):
        ev = int(r.event_year)
        pre, post = cmp.windows(ev)
        base = r._asdict()
        if len(pre) < cmp.PRE_YEARS_MIN or len(post) < 1:
            rows.append({**base, "status": "excluded: too few years"})
            continue
        yrs = tuple(pre + post)
        if yrs not in complete_cache:
            complete_cache[yrs] = cmp.complete(p, list(yrs))
        if r.key not in complete_cache[yrs] or pd.isna(homes.get(r.key)):
            rows.append({**base, "status": "excluded: missing permit years or homes"})
            continue
        ctrl, window = cmp.controls(p, r.key, ev, excluded, homes, popn)
        rows.append({**base, "status": "included", "pop_window": window, "pre_years": f"{pre[0]}-{pre[-1]}",
                     "post_years": f"{post[0]}-{post[-1]}", **outcomes(S, r.key, ctrl, pre, post, homes)})
    return pd.DataFrame(rows).assign(set=label)


def part_a() -> None:
    p = panel_full()
    homes, popn = acs_inputs(p)
    S = Sums(p)
    e = pd.read_csv(REFERENCE / "parking_expanded_effects.csv")
    real = e[(e["status"] == "included") & (e["outcome"] == "all")][["place", "state", "key", "event_year"]].drop_duplicates("key")
    real["event_year"] = real["event_year"].astype(int)
    print("real places:", len(real), flush=True)
    excluded = excluded_keys(p, real)
    f_real = CKPT / "real.csv"
    if not f_real.exists():
        r = case_rows(p, S, real, excluded, homes, popn, "real")
        r.to_csv(f_real, index=False)
        print("real done:", (r["status"] == "included").sum(), "included", flush=True)
    # placebo partners: same division, 0.5-2x population (ACS), never reformed, complete years and homes
    rng = np.random.default_rng(SEED)
    last = p.drop_duplicates("key", keep="last").set_index("key")
    div = last["division"]
    pop = popn.reindex(last.index)
    for r in real.itertuples():
        f = CKPT / f"placebo_{r.key.replace('|', '_')}.csv"
        if f.exists():
            continue
        pre, post = cmp.windows(int(r.event_year))
        ok = cmp.complete(p, pre + post) & set(homes.dropna().index)
        p0 = pop.get(r.key, np.nan)
        cand = [k for k in ok if k not in excluded and div.get(k) == div.get(r.key) and pd.notna(pop.get(k))
                and 0.5 * p0 <= pop[k] <= 2.0 * p0] if pd.notna(p0) else []
        cand = sorted(cand)
        if len(cand) > MAX_PARTNERS:
            cand = list(rng.choice(cand, MAX_PARTNERS, replace=False))
        fake = pd.DataFrame(dict(place=[last.loc[k, "name"] for k in cand], state="", key=cand, event_year=int(r.event_year)))
        out = case_rows(p, S, fake, excluded, homes, popn, "placebo") if len(fake) else pd.DataFrame()
        out = out.assign(real_key=r.key) if len(out) else pd.DataFrame(dict(real_key=[r.key], status=["no partners"]))
        out.to_csv(f, index=False)
        print(f"placebo {r.place}: {len(cand)} partners", flush=True)
    print("part A done", flush=True)


# ---------------------------------------------------------------- summaries
def wavg(y, w):
    y, w = np.asarray(y, float), np.asarray(w, float)
    m = np.isfinite(y) & (w > 0)
    return float(np.average(y[m], weights=w[m])) if m.any() else np.nan


OUT_DEF = {"A1": ("A1", "A1_weight"), "A2": ("A2", "AB_weight"), "A3": ("A3", "AB_weight"),
           "ALL": ("ALL", "AB_weight"), "U5": ("U5", "AB_weight")}


def summarise_a() -> None:
    r = pd.read_csv(CKPT / "real.csv")
    inc = r[r["status"] == "included"].copy()
    pl = pd.concat([pd.read_csv(f) for f in sorted(CKPT.glob("placebo_*.csv"))], ignore_index=True)
    pl = pl[pl["status"] == "included"]
    rng = np.random.default_rng(SEED)
    groups = {k: g for k, g in pl.groupby("real_key")}
    real_keys = [k for k in inc["key"] if k in groups]
    rows, place_rows = [], []
    # placebo sets: one random partner per real place that has partners
    picks = {k: rng.integers(0, len(groups[k]), PLACEBO_SETS) for k in real_keys}
    for o, (col, wcol) in OUT_DEF.items():
        real_avg = wavg(inc[col], inc[wcol])
        n_real = int((np.isfinite(inc[col]) & (inc[wcol] > 0)).sum())
        # bootstrap over places
        d = inc[np.isfinite(inc[col]) & (inc[wcol] > 0)]
        bs = [wavg(d[col].values[i], d[wcol].values[i]) for i in (rng.integers(0, len(d), len(d)) for _ in range(2000))]
        # placebo
        Y = np.column_stack([groups[k][col].values[picks[k]] for k in real_keys])
        W = np.column_stack([groups[k][wcol].values[picks[k]] for k in real_keys])
        W = np.where(np.isfinite(Y) & (W > 0), W, 0.0)
        Y = np.where(np.isfinite(Y), Y, 0.0)
        fake = (Y * W).sum(1) / np.where(W.sum(1) > 0, W.sum(1), np.nan)
        # leave one state out: predict held-out places by other states' average; compare with zero
        err_avg, err_zero, wts = [], [], []
        for st, g in d.groupby("state"):
            rest = d[d["state"] != st]
            m = wavg(rest[col], rest[wcol])
            err_avg += list(np.abs(g[col] - m))
            err_zero += list(np.abs(g[col]))
            wts += list(g[wcol])
        lsso_avg = float(np.average(err_avg, weights=wts))
        lsso_zero = float(np.average(err_zero, weights=wts))
        loo = [wavg(d[col].drop(i), d[wcol].drop(i)) for i in d.index]
        rows.append(dict(outcome=o, places=n_real, average=real_avg, boot_p05=np.percentile(bs, 5), boot_p95=np.percentile(bs, 95),
                         loo_min=min(loo), loo_max=max(loo), loo_p05=np.percentile(loo, 5), loo_p95=np.percentile(loo, 95),
                         median=float(d[col].median()),
                         placebo_mean=np.nanmean(fake), placebo_p05=np.nanpercentile(fake, 5), placebo_p95=np.nanpercentile(fake, 95),
                         placebo_percentile=float(np.nanmean(fake < real_avg) * 100),
                         lsso_error_average=lsso_avg, lsso_error_zero=lsso_zero, average_beats_zero=lsso_avg < lsso_zero,
                         without_sf=wavg(d.loc[d["place"] != "San Francisco", col], d.loc[d["place"] != "San Francisco", wcol])))
    s = pd.DataFrame(rows)
    s.to_csv(REFERENCE / "parking_mechanism_part_a_summary.csv", index=False)
    inc.to_csv(REFERENCE / "parking_mechanism_part_a_places.csv", index=False)
    r[r["status"] != "included"][["place", "state", "key", "event_year", "status"]].to_csv(
        REFERENCE / "parking_mechanism_part_a_excluded.csv", index=False)
    pd.set_option("display.width", 250)
    print(s.round(4).to_string(index=False))
    # noise question: placebo width relative to the before-level, A1 (log points) vs all units (share of before-rate)
    a1 = s.set_index("outcome")
    lvl_all = wavg(inc["ALL_before"], inc["AB_weight"])
    print("placebo width, A1 (log points):", round(a1.loc["A1", "placebo_p95"] - a1.loc["A1", "placebo_p05"], 4))
    print("placebo width, all units (share of before-rate):",
          round((a1.loc["ALL", "placebo_p95"] - a1.loc["ALL", "placebo_p05"]) / lvl_all, 4))
    worst = inc.assign(absA1=inc["A1"].abs() * inc["A1_weight"]).sort_values("absA1", ascending=False)
    print(worst[["place", "state", "event_year", "A1", "A1_weight", "A1_size_before", "A1_size_after"]].head(8).to_string(index=False))


# ---------------------------------------------------------------- Part C: where Wisconsin minimums still bind
EXEMPT_AT = {"Algoma", "Brodhead", "Cottage Grove", "Fitchburg", "Franklin", "Gilman", "La Crosse", "Omro", "West Allis"}
EXEMPT_GUIDANCE = {"Pewaukee", "Roberts"}  # guidance only, no mandates ("Pewaukee (City)" in the taxonomy)
MADISON_DOWNTOWN = {"DC", "UMX", "UOR", "DR1", "DR2"}
V9 = "/vsizip/" + str(RAW / "tod_land_values" / "wi_parcels_v9_2023.zip") + "/V9.0.1_Wisconsin_Parcels_2023_10.3_Uncompressed.gdb"


def base_name(n: str) -> tuple[str, str]:
    n = str(n)
    for t in ("city", "village", "town"):
        if n.endswith(" " + t):
            return n[: -len(t) - 1], t
    return n, ""


def madison_shares() -> dict:
    import geopandas as gpd
    g = gpd.read_file(RAW / "madison_parcels" / "tax_parcels.geojson", columns=["TotalDwellingUnits", "YearBuilt", "ZoningAll"])
    n = g[g["YearBuilt"].between(2015, 2024) & (g["TotalDwellingUnits"] >= 5)].copy()
    n["zone"] = n["ZoningAll"].astype(str).str.split(r"[ ,;/]").str[0]
    tod = gpd.read_file(RAW / "madison_tod" / "tod_boundary.geojson").to_crs(n.crs).geometry.union_all()
    n["in_tod"] = n.geometry.representative_point().within(tod)
    u = n["TotalDwellingUnits"]
    down = n["zone"].isin(MADISON_DOWNTOWN)
    return dict(madison_units=float(u.sum()), madison_buildings=len(n),
                madison_downtown_units=float(u[down].sum()),
                madison_downtown_or_tod_units=float(u[down | n["in_tod"]].sum()))


def milwaukee_shares() -> dict:
    m = pd.read_csv(RAW / "milwaukee_mprop" / "mprop.csv", dtype=str, usecols=["TAXKEY", "NR_UNITS", "YR_BUILT", "ZONING"])
    m["NR_UNITS"] = pd.to_numeric(m["NR_UNITS"], errors="coerce")
    m["YR_BUILT"] = pd.to_numeric(m["YR_BUILT"], errors="coerce")
    n = m[m["YR_BUILT"].between(2015, 2024) & (m["NR_UNITS"] >= 5)].drop_duplicates("TAXKEY")
    c9 = n["ZONING"].fillna("").str.startswith("C9")
    return dict(milwaukee_units=float(n["NR_UNITS"].sum()), milwaukee_buildings=len(n), milwaukee_c9_units=float(n.loc[c9, "NR_UNITS"].sum()))


def land_values() -> pd.DataFrame:
    """Median assessed land value per sq ft of residential (1) and commercial (2) parcels, by municipality and county."""
    f = CKPT / "v9_land.parquet"
    if not f.exists():
        import pyogrio
        pyogrio.read_dataframe(V9, columns=["PLACENAME", "CONAME", "PROPCLASS", "LNDVALUE", "GISACRES", "PARCELFIPS"],
                               read_geometry=False).to_parquet(f)
    d = pd.read_parquet(f)
    d = d[d["PROPCLASS"].isin(["1", "2"]) & d["GISACRES"].between(0.05, 10) & (d["LNDVALUE"] > 0)].copy()
    d["per_sqft"] = d["LNDVALUE"] / (d["GISACRES"] * 43560)
    out = d.groupby(["PLACENAME", "PARCELFIPS"]).agg(land_per_sqft=("per_sqft", "median"), parcels=("per_sqft", "size")).reset_index()
    return out


def part_c() -> None:
    b = pd.read_csv(REFERENCE / "housing_baseline_by_area.csv")
    b = b[b["area_id"] != "unallocated"].copy()
    b["base"], b["mtype"] = zip(*b["name"].map(base_name))
    b["county3"] = b["area_id"].str[7:10]
    sh = {**madison_shares(), **milwaukee_shares()}
    print(json.dumps(sh, indent=1))
    mad_lo = sh["madison_downtown_units"] / sh["madison_units"]
    mad_hi = sh["madison_downtown_or_tod_units"] / sh["madison_units"]
    mke = sh["milwaukee_c9_units"] / sh["milwaukee_units"]
    rows = []
    for r in b.itertuples():
        exempt_lo = exempt_hi = 0.0
        why = "minimums bind"
        if r.base in EXEMPT_AT or (r.base in EXEMPT_GUIDANCE and r.mtype == "city"):
            exempt_lo = exempt_hi = 1.0
            why = "already no minimums (taxonomy)"
        elif r.name == "Madison city" and r.structure_type != "1unit":
            exempt_lo, exempt_hi, why = mad_lo, mad_hi, "Madison: downtown districts (low) or downtown + TOD overlay (high)"
        elif r.name == "Milwaukee city" and r.structure_type != "1unit":
            exempt_lo = exempt_hi = mke
            why = "Milwaukee: downtown C9 districts"
        rows.append(dict(area_id=r.area_id, name=r.name, county3=r.county3, context=r.context, structure_type=r.structure_type,
                         housing_units_acs=r.housing_units_acs, five_year_central=r.five_year_central,
                         exempt_share_low=exempt_lo, exempt_share_high=exempt_hi, reason=why))
    out = pd.DataFrame(rows)
    lv = land_values()
    lv["key"] = lv["PLACENAME"].str.upper().str.strip() + "|" + lv["PARCELFIPS"].astype(str).str.zfill(3)
    names = out["name"].map(lambda n: f"{base_name(n)[1].upper()} OF {base_name(n)[0].upper()}")
    out["land_per_sqft"] = (names + "|" + out["county3"]).map(lv.set_index("key")["land_per_sqft"])
    miss = out["land_per_sqft"].isna()
    # unmatched pieces take their county's median (flagged)
    cty = lv.groupby(lv["PARCELFIPS"].astype(str).str.zfill(3))["land_per_sqft"].median()
    out.loc[miss, "land_per_sqft"] = out.loc[miss, "county3"].map(cty)
    out["land_source"] = np.where(miss, "county median (no municipal match)", "municipal median")
    out.to_csv(REFERENCE / "parking_mechanism_where_binding.csv", index=False)
    pd.DataFrame([dict(sh, madison_exempt_low=mad_lo, madison_exempt_high=mad_hi, milwaukee_exempt=mke)]).to_csv(
        REFERENCE / "parking_mechanism_exempt_shares.csv", index=False)
    apt = out[out["structure_type"] != "1unit"]
    print("land value matched (2+ unit rows with homes):", (apt.loc[apt.five_year_central > 0, "land_source"] == "municipal median").mean())
    for lab, c in (("low", "exempt_share_low"), ("high", "exempt_share_high")):
        print(f"2+ unit baseline still binding ({lab} exemption):", round((apt["five_year_central"] * (1 - apt[c])).sum()),
              "of", round(apt["five_year_central"].sum()))


# ---------------------------------------------------------------- Part B: cost chain
SOURCES_S = {"Buffalo": 1 - 1942 / 2444, "Los Angeles transit program": 1 - 151 / 224.5,
             "Seattle (secondary)": 0.40, "Champaign": 1 - 1833 / 3975}
# Multifamily minimums as listed in Mankato's 2025 staff comparison (Planning Commission packet 2025-08-27,
# "Parking Information - Other Communities"). Spaces per home; bedroom-based rules use a 50/50 mix of
# studio-or-one-bedroom and two-bedroom homes (1.5 bedrooms per home); guest spaces included where listed.
MINIMUMS = {"Madison city": 1.0, "Milwaukee city": 2 / 3, "Green Bay city": 1.25, "Stevens Point city": (1.375 + 1.75) / 2,
            "Superior city": 1.0, "Eau Claire city": 1.5, "Oshkosh city": 2.0, "Janesville city": 1.75,
            "Wauwatosa city": 1.25, "New Berlin city": 2.1, "Wausau city": 1.5, "Menomonee Falls village": 1.5,
            "Greenfield city": (2.0 + 2.25) / 2, "Beloit city": 1.5, "Oak Creek city": 1.0, "Manitowoc city": 2.25}
# La Crosse (1.5) is listed but repealed its minimums in December 2024, so it is exempt.
SQFT_PER_SPACE = 330
DRAWS = 10_000


def wi_value_per_home() -> dict:
    p = rpc.read_bps_us()
    w = p[(p["state_fips"].astype(str).str.strip() == "55") & p["year"].between(2023, 2025)]
    out = {}
    for k, lab in (("5plus", "5plus"), ("3_4units", "3_4units"), ("2units", "2units")):
        out[lab] = float(w[f"{k}_value"].sum() / w[f"{k}_units"].sum())
    return out


def chain_draws(where: pd.DataFrame, vph: dict, rng, hold: str | None = None) -> np.ndarray:
    """Wisconsin extra homes over 2027-2031 per draw (2+ unit buildings). `hold` keeps one piece at its central value."""
    apt = where[(where["structure_type"] != "1unit") & (where["five_year_central"] > 0)].reset_index(drop=True)
    listed = apt["name"].map(MINIMUMS)
    other_vals = np.array([v for n, v in MINIMUMS.items() if n not in ("Madison city", "Milwaukee city")])
    central = dict(s=float(np.median(list(SOURCES_S.values()))), m_other=float(np.median(other_vals)), eps=0.30,
                   hard=0.635, struct=(29_900 + 52_000) / 2, surf=(1_500 + 10_000) / 2, exempt=0.5)
    urban = (apt["context"] == "urban").values
    land = apt["land_per_sqft"].fillna(apt["land_per_sqft"].median()).values * SQFT_PER_SPACE
    base = apt["five_year_central"].values
    vals = apt["structure_type"].map(vph).values
    out = np.empty(DRAWS)
    svals = np.array(list(SOURCES_S.values()))
    for i in range(DRAWS):
        s = central["s"] if hold == "s" else rng.choice(svals)
        mo = central["m_other"] if hold == "m" else rng.choice(other_vals)
        m = np.where(listed.notna(), listed.fillna(0).values, mo)
        eps = central["eps"] if hold == "eps" else rng.triangular(0.11, 0.30, 0.59)
        hard = central["hard"] if hold == "tdc" else rng.uniform(0.60, 0.67)
        cs = central["struct"] if hold == "cost" else rng.uniform(29_900, 52_000)
        cu = central["surf"] if hold == "cost" else rng.uniform(1_500, 10_000)
        cost = np.where(urban, cs, cu + land)
        u = central["exempt"] if hold == "exempt" else rng.uniform()
        ex = apt["exempt_share_low"].values + u * (apt["exempt_share_high"].values - apt["exempt_share_low"].values)
        pct = eps * s * m * cost / (vals / hard)
        out[i] = float((base * (1 - ex) * pct).sum())
    return out


def part_b() -> None:
    where = pd.read_csv(REFERENCE / "parking_mechanism_where_binding.csv")
    vph = wi_value_per_home()
    print("Census permit value per home, Wisconsin 2023-2025:", {k: round(v) for k, v in vph.items()})
    rng = np.random.default_rng(SEED)
    main = chain_draws(where, vph, rng)
    rows = [dict(case="all pieces vary", p05=np.percentile(main, 5), p50=np.percentile(main, 50), p95=np.percentile(main, 95),
                 mean=main.mean())]
    for h in ("s", "m", "eps", "tdc", "cost", "exempt"):
        d = chain_draws(where, vph, np.random.default_rng(SEED), hold=h)
        rows.append(dict(case=f"hold {h} at central", p05=np.percentile(d, 5), p50=np.percentile(d, 50),
                         p95=np.percentile(d, 95), mean=d.mean()))
    # Buffalo-only sensitivity (closest market to Wisconsin)
    keep = dict(SOURCES_S)
    SOURCES_S.clear()
    SOURCES_S["Buffalo"] = keep["Buffalo"]
    d = chain_draws(where, vph, np.random.default_rng(SEED))
    rows.append(dict(case="Buffalo only for s (sensitivity)", p05=np.percentile(d, 5), p50=np.percentile(d, 50),
                     p95=np.percentile(d, 95), mean=d.mean()))
    SOURCES_S.clear()
    SOURCES_S.update(keep)
    # structured parking only in Madison and Milwaukee (sensitivity; plan uses all 'urban' context)
    w2 = where.copy()
    w2.loc[~w2["name"].isin(["Madison city", "Milwaukee city"]) & (w2["context"] == "urban"), "context"] = "urban_surface"
    d = chain_draws(w2, vph, np.random.default_rng(SEED))
    rows.append(dict(case="structured parking only in Madison and Milwaukee (sensitivity)", p05=np.percentile(d, 5),
                     p50=np.percentile(d, 50), p95=np.percentile(d, 95), mean=d.mean()))
    res = pd.DataFrame(rows)
    res.to_csv(REFERENCE / "parking_mechanism_part_b_wi.csv", index=False)
    pd.set_option("display.width", 250)
    print(res.round(0).to_string(index=False))

    # per-project figures at central values, for a typical binding apartment home
    apt = where[(where["structure_type"] == "5plus") & (where["five_year_central"] > 0)]
    s_c = float(np.median(list(SOURCES_S.values())))
    w = apt["five_year_central"] * (1 - (apt["exempt_share_low"] + apt["exempt_share_high"]) / 2)
    other_vals = [v for n, v in MINIMUMS.items() if n not in ("Madison city", "Milwaukee city")]
    m_c = apt["name"].map(MINIMUMS).fillna(float(np.median(other_vals)))
    land = apt["land_per_sqft"].fillna(apt["land_per_sqft"].median()) * SQFT_PER_SPACE
    cost_c = np.where(apt["context"] == "urban", (29_900 + 52_000) / 2, (1_500 + 10_000) / 2 + land)
    tdc = vph["5plus"] / 0.635
    pp = pd.DataFrame([dict(
        old_min_spaces_per_home=float(np.average(m_c, weights=w)),
        spaces_not_built_per_home=float(np.average(s_c * m_c, weights=w)),
        cost_per_space=float(np.average(cost_c, weights=w)),
        dollars_saved_per_home=float(np.average(s_c * m_c * cost_c, weights=w)),
        total_cost_per_home=tdc,
        pct_cost_saved=float(np.average(s_c * m_c * cost_c / tdc, weights=w)) * 100,
        pct_more_homes_central_eps=float(np.average(0.30 * s_c * m_c * cost_c / tdc, weights=w)) * 100)])
    pp.to_csv(REFERENCE / "parking_mechanism_part_b_per_project.csv", index=False)
    print(pp.round(3).T.to_string())

    # B1: leave one study out for s
    b1 = []
    for k, v in SOURCES_S.items():
        rest = [x for kk, x in SOURCES_S.items() if kk != k]
        b1.append(dict(left_out=k, actual=v, predicted=float(np.mean(rest)), miss=v - float(np.mean(rest))))
    b1 = pd.DataFrame(b1)
    b1.to_csv(REFERENCE / "parking_mechanism_b1_loso.csv", index=False)
    print(b1.round(3).to_string(index=False))

    # B2: B's percent change in 2+ unit permits against the measured 2+ effect in the repeal places (Buffalo out)
    pct_central = pp["pct_more_homes_central_eps"].iloc[0] / 100
    pct_draw_lo = pct_central * 0.11 / 0.30
    pct_draw_hi = pct_central * 0.59 / 0.30
    e = pd.read_csv(REFERENCE / "parking_expanded_effects.csv")
    e = e[(e["status"] == "included") & (e["outcome"] == "2plus") & (e["place"] != "Buffalo")].dropna(subset=["effect"])
    wts = e["homes"] * e["n_post"]
    predB = pct_central * e["rate_before"]
    b2 = dict(places=len(e), error_B=float(np.average(np.abs(e["effect"] - predB), weights=wts)),
              error_zero=float(np.average(np.abs(e["effect"]), weights=wts)),
              mean_predicted_B=float(np.average(predB, weights=wts)), mean_measured=float(np.average(e["effect"], weights=wts)),
              B_pct_central=pct_central * 100, B_pct_low_eps=pct_draw_lo * 100, B_pct_high_eps=pct_draw_hi * 100)
    b2["B_beats_zero"] = b2["error_B"] <= b2["error_zero"]
    b2["gain_vs_zero_pct"] = (1 - b2["error_B"] / b2["error_zero"]) * 100
    pd.DataFrame([b2]).to_csv(REFERENCE / "parking_mechanism_b2_vs_repeals.csv", index=False)
    print(json.dumps(b2, indent=1, default=float))


# ---------------------------------------------------------------- unplanned robustness checks on A1 (logged in the plan)
def robust_a() -> None:
    p = pd.read_csv(REFERENCE / "parking_mechanism_part_a_places.csv")
    pl = pd.concat([pd.read_csv(f) for f in sorted(CKPT.glob("placebo_*.csv"))], ignore_index=True)
    pl = pl[pl["status"] == "included"].copy()
    for df in (p, pl):
        df["raw"] = np.log(df["A1_size_after"] / df["A1_size_before"])
    d = p[np.isfinite(p["A1"]) & (p["A1_weight"] > 0)]
    g = {k: x[np.isfinite(x["A1"]) & (x["A1_weight"] > 0)] for k, x in pl.groupby("real_key")}
    rng = np.random.default_rng(1)
    stats = {"weighted by buildings (pre-set)": lambda x: np.average(x["A1"], weights=x["A1_weight"]),
             "unweighted mean": lambda x: x["A1"].mean(), "median": lambda x: x["A1"].median(),
             "own change only, no comparison places (weighted)": lambda x: np.average(x["raw"], weights=x["A1_weight"])}
    rows = []
    for keys_lab, keys in (("all", list(d["key"])), ("without Austin", list(d.loc[d["place"] != "Austin", "key"]))):
        for lab, st in stats.items():
            if keys_lab == "without Austin" and lab != "weighted by buildings (pre-set)":
                continue
            real = st(d[d["key"].isin(keys)])
            ks = [k for k in keys if k in g and len(g[k])]
            fake = np.array([st(pd.concat([g[k].iloc[[rng.integers(len(g[k]))]] for k in ks])) for _ in range(5000)])
            rows.append(dict(places=keys_lab, statistic=lab, value=real, pct_change=(np.exp(real) - 1) * 100,
                             placebo_percentile=float(np.mean(fake < real) * 100),
                             placebo_p05=np.percentile(fake, 5), placebo_p95=np.percentile(fake, 95), n=len(ks)))
    out = pd.DataFrame(rows)
    out.to_csv(REFERENCE / "parking_mechanism_part_a_robustness.csv", index=False)
    print(out.round(3).to_string(index=False))


# ---------------------------------------------------------------- audit fix 1: A3 and 5+ homes on A1's 38 places
def same_places_a() -> None:
    inc = pd.read_csv(REFERENCE / "parking_mechanism_part_a_places.csv")
    d = inc[np.isfinite(inc["A1"]) & (inc["A1_weight"] > 0)]
    pl = pd.concat([pd.read_csv(f) for f in sorted(CKPT.glob("placebo_*.csv"))], ignore_index=True)
    pl = pl[pl["status"] == "included"]
    groups = {k: g for k, g in pl.groupby("real_key")}
    keys = [k for k in d["key"] if k in groups]
    rng = np.random.default_rng(SEED)
    picks = {k: rng.integers(0, len(groups[k]), PLACEBO_SETS) for k in keys}
    rows = []
    for o, (col, wcol) in OUT_DEF.items():
        real = wavg(d[col], d[wcol])
        bs = [wavg(d[col].values[i], d[wcol].values[i]) for i in (rng.integers(0, len(d), len(d)) for _ in range(2000))]
        Y = np.column_stack([groups[k][col].values[picks[k]] for k in keys])
        W = np.column_stack([groups[k][wcol].values[picks[k]] for k in keys])
        W = np.where(np.isfinite(Y) & (W > 0), W, 0.0)
        Y = np.where(np.isfinite(Y), Y, 0.0)
        fake = (Y * W).sum(1) / np.where(W.sum(1) > 0, W.sum(1), np.nan)
        rows.append(dict(outcome=o, places=len(d), average=real, boot_p05=np.percentile(bs, 5), boot_p95=np.percentile(bs, 95),
                         placebo_mean=np.nanmean(fake), placebo_p05=np.nanpercentile(fake, 5),
                         placebo_p95=np.nanpercentile(fake, 95), placebo_percentile=float(np.nanmean(fake < real) * 100)))
    out = pd.DataFrame(rows)
    out.to_csv(REFERENCE / "parking_mechanism_part_a_same38.csv", index=False)
    print(out.round(4).to_string(index=False))


if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else "part_a"
    {"part_a": part_a, "summarise_a": summarise_a, "part_c": part_c, "part_b": part_b, "robust_a": robust_a, "same_places_a": same_places_a}[cmd]()
