"""Parking improvement loop, round 1 (docs/parking/IMPROVE_R1_PLAN.md).

    uv run --all-extras python scripts/run_parking_improve_r1.py

Reruns the 76-place comparison under data-fix variants. Outputs: reference/parking_improve_r1_places.csv,
reference/parking_improve_r1_summary.csv, reference/parking_improve_r1_checks.csv
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
sys.path.insert(0, str(Path(__file__).resolve().parent))

import run_parking_comparison as rpc  # noqa: E402
import run_parking_expanded as rpe  # noqa: E402
from missing_middleware.parking import checks  # noqa: E402
from missing_middleware.parking import comparison as cmp  # noqa: E402
from missing_middleware.paths import RAW, REFERENCE  # noqa: E402


def panel_with(bps: pd.DataFrame, reported, ) -> pd.DataFrame:
    b = bps.copy()
    if reported == "scaled":  # reported months scaled to 12; the Census estimate where none reported (audit R1)
        m = pd.to_numeric(b["months_reported"], errors="coerce")
        for g in ("1unit", "2units", "3_4units", "5plus"):
            b[f"{g}_units"] = np.where(m > 0, b[f"{g}_units_rep"] * 12 / m.clip(lower=1), b[f"{g}_units"])
        b["units_total"] = b[[f"{g}_units" for g in ("1unit", "2units", "3_4units", "5plus")]].sum(axis=1)
    elif reported:
        for g in ("1unit", "2units", "3_4units", "5plus"):
            b[f"{g}_units"] = b[f"{g}_units_rep"]
        b["units_total"] = b["units_total_rep"]
    return cmp.panel(b)


_orig_controls = cmp.controls


def controls_nation(p, key, event_year, excluded, homes, population=None):
    """As cmp.controls, then the whole country at 1/2-2x when fewer than MIN_CONTROLS (plan change, 2026-10-31)."""
    c, label = _orig_controls(p, key, event_year, excluded, homes, population)
    if len(c) >= cmp.MIN_CONTROLS:
        return c, label
    pre, post = cmp.windows(event_year)
    last = p[(p["year"] == event_year - 1)].set_index("key")
    base = population.reindex(last.index) if population is not None else last["pop"]
    pop0 = base.get(key, np.nan)
    ok = cmp.complete(p, pre + post) & set(homes.dropna().index)
    c = [k for k, v in base.items() if k != key and k not in excluded and k in ok and 0.5 * pop0 <= v <= 2 * pop0]
    return c, "nation 0.50-2.00"


def main() -> None:
    bps = rpc.read_bps_us()
    p_est, p_rep, p_scl = panel_with(bps, False), panel_with(bps, True), panel_with(bps, "scaled")
    months = bps.assign(key=bps["state_fips"].astype(str).str.strip() + "|" + bps["bps_id"].astype(str).str.strip()) \
        .drop_duplicates(["key", "year"]).set_index(["key", "year"])["months_reported"]
    homes_geo = rpc.acs_table(RAW / "census_acs5_2024_tbsf" / "acsdt5y2024-b25002.dat", "B25002_E001")
    pop_geo = rpc.acs_table(RAW / "census_acs5_2024_tbsf" / "acsdt5y2024-b01003.dat", "B01003_E001")
    geo = p_est.drop_duplicates("key", keep="last").set_index("key")
    homes = geo["acs_geoid"].map(homes_geo)
    homes = homes[homes > 0]
    popn = geo["acs_geoid"].map(pop_geo)
    real = pd.read_csv(REFERENCE / "parking_expanded_effects.csv")
    real = real[(real["status"] == "included") & (real["outcome"] == "all")].copy()
    tax = pd.read_csv(REFERENCE / "parking_reform_taxonomy.csv")
    def keys_for(t):
        return {k for r in t.drop_duplicates("prn_key").itertuples()
                if (k := cmp.match_place(p_est, rpc.STATE_FIPS.get(r.state, "??"), r.place, r.population))}
    base_ex = keys_for(tax[(tax["policy"] == "rm_min") & tax["benchmark_rating"].isin(["at", "near"]) & (tax["place_type"] == "city")])
    base_ex |= set(real["key"].dropna())
    any_ex = base_ex | keys_for(tax[tax["land_use"].fillna("").str.contains("resid|all uses") & (tax["place_type"] == "city")])
    housing = tax[tax["land_use"].fillna("").str.contains("resid|all uses") & (tax["place_type"] == "city")]
    reform_year = {}
    for r in housing.itertuples():
        k = cmp.match_place(p_est, rpc.STATE_FIPS.get(r.state, "??"), r.place, r.population)
        if k:
            y = r.adopted_year if pd.notna(r.adopted_year) else -1  # undated: treat as already reformed
            reform_year[k] = min(reform_year.get(k, 9999), y if y >= 0 else -1)
    # homes and population for the year before each repeal: ACS 2020-24 homes minus permits issued since
    permits_by = p_est.pivot_table(index="key", columns="year", values="units_total", aggfunc="sum").fillna(0)

    def pre_series(ey: int):
        since = permits_by[[y for y in permits_by.columns if ey <= y <= 2024]].sum(axis=1)
        h = (homes - since.reindex(homes.index).fillna(0)).clip(lower=homes * 0.5)
        return h, popn * (h / homes).reindex(popn.index).fillna(1.0)

    variants = {
        "V0 current": dict(p=p_est, ex=base_ex, pre=False, drop_est=False),
        "V1 reported months only": dict(p=p_rep, ex=base_ex, pre=False, drop_est=False),
        "V2 drop places with estimated years": dict(p=p_est, ex=base_ex, pre=False, drop_est=True),
        "V3 clean comparison pools": dict(p=p_est, ex=any_ex, pre=False, drop_est=False, nation=True),
        "V4 pre-repeal traits": dict(p=p_est, ex=base_ex, pre=True, drop_est=False),
        "V5 all fixes (V1+V3+V4)": dict(p=p_rep, ex=any_ex, pre=True, drop_est=False, nation=True),
        "V3a clean pools, no national fallback (first run)": dict(p=p_est, ex=any_ex, pre=False, drop_est=False),
        "V1b reported months scaled to 12": dict(p=p_scl, ex=base_ex, pre=False, drop_est=False),
        "V3b date-aware clean pools": dict(p=p_est, ex=base_ex, pre=False, drop_est=False, nation=True, date_aware=True),
        "V6 all fixes (V1b+V3b+V4)": dict(p=p_scl, ex=base_ex, pre=True, drop_est=False, nation=True, date_aware=True),
    }
    rows = []
    for name, v in variants.items():
        for r in real.itertuples():
            pre, post = cmp.windows(int(r.event_year))
            post = post[: int(r.n_post)]
            est_years = sum(1 for y in pre + post if months.get((r.key, y), 0) < 12)
            if v["drop_est"] and est_years:
                continue
            h, pp = pre_series(int(r.event_year)) if v["pre"] else (homes, popn)
            ex = v["ex"]
            if v.get("date_aware"):
                end = (pre + post)[-1]
                ex = base_ex | {k for k, y in reform_year.items() if y <= end}
            cmp.controls = controls_nation if v.get("nation") else _orig_controls
            e = cmp.effects(v["p"], pd.DataFrame([{"key": r.key, "event_year": int(r.event_year)}]), ex - {r.key}, h, pp, min_post=1)
            if "outcome" not in e:
                continue
            e = e[(e["status"] == "included") & (e["outcome"] == "all")]
            if e.empty:
                continue
            x = e.iloc[0]
            rows.append(dict(variant=name, place=r.place, state=r.state, key=r.key, event_year=int(r.event_year), n_post=int(x["n_post"]),
                             homes=float(x["homes"]), n_controls=int(x["n_controls"]), effect=float(x["effect"]), estimated_years=est_years))
    P = pd.DataFrame(rows)
    P["weight"] = P["homes"] * P["n_post"]
    P.round(4).to_csv(REFERENCE / "parking_improve_r1_places.csv", index=False)
    S = []
    for name, g in P.dropna(subset=["effect"]).groupby("variant", sort=False):
        g = g.reset_index(drop=True)
        m, lo, hi = rpe.boot_mean(g["effect"].values, g["weight"].values)
        S.append(dict(variant=name, places=len(g), weighted=m, p05=lo, p95=hi, equal_weight=g["effect"].mean(), median=g["effect"].median()))
        S[-1].update(controls_median=float(g["n_controls"].median()), controls_under_5=int((g["n_controls"] < 5).sum()))
    top4 = {"San Francisco", "Austin", "San Jose", "Raleigh"}
    for name in ("V0 current", "V6 all fixes (V1b+V3b+V4)"):
        g0 = P[(P["variant"] == name)].dropna(subset=["effect"])
        for lab, g in ((" | without the 4 heaviest places", g0[~g0["place"].isin(top4)]), (" | 3 after-years only", g0[g0["n_post"] == 3])):
            g = g.reset_index(drop=True)
            m, lo, hi = rpe.boot_mean(g["effect"].values, g["weight"].values)
            S.append(dict(variant=name + lab, places=len(g), weighted=m, p05=lo, p95=hi, equal_weight=g["effect"].mean(), median=g["effect"].median(),
                          controls_median=float(g["n_controls"].median()), controls_under_5=int((g["n_controls"] < 5).sum())))
    S = pd.DataFrame(S).rename(columns={"p05": "resampling_p05", "p95": "resampling_p95"})
    S.round(3).to_csv(REFERENCE / "parking_improve_r1_summary.csv", index=False)
    # flags
    v5 = P[P["variant"].str.startswith("V6")].set_index("key")
    v0 = P[P["variant"].str.startswith("V0")].set_index("key")
    d = (v5["effect"] - v0["effect"].reindex(v5.index)).dropna()
    flags = checks.definition(P, "place-variants with fewer than 5 comparison places", P["n_controls"] < 5)
    flags += checks.definition(P, "place-variants with no effect (empty comparison pool)", P["effect"].isna())
    flags += checks.unit_ranges(P.rename(columns={}), {"effect": ("permits per 1,000 existing homes per year", -100.0, 100.0)})
    if len(d):
        k = d.abs().idxmax()
        flags.append(dict(check="largest move V0 -> V6 (trace it)", where=v5.loc[k, "place"], column="effect", value=float(d[k]),
                          note=f"V0 {v0.loc[k, 'effect']:.2f}, V6 {v5.loc[k, 'effect']:.2f}, estimated years {int(v5.loc[k, 'estimated_years'])}"))
    checks.report(flags, REFERENCE / "parking_improve_r1_checks.csv")
    pd.set_option("display.width", 220)
    print(S.round(2).to_string(index=False))


if __name__ == "__main__":
    main()
