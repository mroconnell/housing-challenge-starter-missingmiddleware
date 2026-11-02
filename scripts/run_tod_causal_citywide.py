"""Causal framework, Test 1 (T1): citywide check for the 11 D-11 places (docs/tod/CAUSAL_FRAMEWORK_PLAN.md, locked
2026-11-02 before any count).

1A: station-area extra homes from the lot tables (functions of run_tod_citywide_per1000.py), all bands to 1 mile and
    1/4 mile only, per 100 lot acres, per 1,000 city homes, district share of the city's new homes, carry-through.
1B: whole-city difference-in-differences on the Census permit survey vs matched non-reform cities, placebo reform
    3 years early (pre-trend rule), and R = citywide net homes / station-area 1/4-mile extra homes.

    OMP_NUM_THREADS=1 .venv/bin/python scripts/run_tod_causal_citywide.py

Writes reference/tod_causal_citywide_11.csv (summaries only).
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))
from missing_middleware import geom_extra_station as X  # noqa: E402
from missing_middleware.paths import RAW, REFERENCE  # noqa: E402
from missing_middleware.tod import control_cities as cc  # noqa: E402
import run_tod_station_model as M  # noqa: E402
import run_tod_citywide_per1000 as P  # noqa: E402

OUT = M.OUT
SEED_PAIR = 20261104


def places() -> dict[str, list[str]]:
    lots = sorted(p.stem.removeprefix("lots_") for p in OUT.glob("lots_*.parquet"))
    return {"New York": [c for c in lots if c.startswith("nyc_")], "Philadelphia": [c for c in lots if c.startswith("phl_")],
            "Austin 2009": ["austin_2009"], "Charlotte 2019": ["charlotte_2019"], "Chicago 2015": ["chicago_2015"],
            "Denver 2018": ["denver_2018"], "Portland 2020": ["portland_2020"],
            "Seattle Mount Baker 2014": ["seattle_mount_baker_2014"], "Seattle Othello 2012": ["seattle_othello_2012"],
            "Salt Lake City 2010": ["slc_2010"], "Saint Paul 2011": ["stpaul_2011"]}


# 2010 Census place GEOID, BPS lookup (state, names), Census region
CITY = {"New York": ("3651000", "36", ["Bronx borough", "Brooklyn borough", "Manhattan borough", "Queens borough", "Staten Island borough"]),
        "Philadelphia": ("4260000", "42", ["Philadelphia"]), "Austin 2009": ("4805000", "48", ["Austin"]),
        "Charlotte 2019": ("3712000", "37", ["Mecklenburg County"]), "Chicago 2015": ("1714000", "17", ["Chicago"]),
        "Denver 2018": ("0820000", "08", ["Denver"]), "Portland 2020": ("4159000", "41", ["Portland"]),
        "Seattle Mount Baker 2014": ("5363000", "53", ["Seattle"]), "Seattle Othello 2012": ("5363000", "53", ["Seattle"]),
        "Salt Lake City 2010": ("4967000", "49", ["Salt Lake City"]), "Saint Paul 2011": ("2758000", "27", ["St. Paul"])}
REGION = {**{s: "NE" for s in ("09", "23", "25", "33", "44", "50", "34", "36", "42")},
          **{s: "MW" for s in ("17", "18", "26", "39", "55", "19", "20", "27", "29", "31", "38", "46")},
          **{s: "S" for s in ("10", "11", "12", "13", "24", "37", "45", "51", "54", "01", "21", "28", "47", "05", "22", "40", "48")},
          **{s: "W" for s in ("04", "08", "16", "30", "32", "35", "49", "56", "02", "06", "15", "41", "53")}}


def cfg(case):
    import build_tod_station_lot_table as B
    return {**B.CASES, **{k: v for k, (_, v) in B.adapter_cases().items()}}[case]


# ------------------------------------------------------------------ city homes (1A)

def stocks() -> dict[str, tuple[float, str]]:
    oct27 = pd.read_csv(REFERENCE / "tod_net_effect_by_case.csv").set_index("case")
    o = {"New York": "nyc_pooled_2003_2013", "Philadelphia": "philadelphia_2012_remapping", "Charlotte 2019": "charlotte_tod_2019",
         "Saint Paul 2011": "stpaul_green_line_2011", "Seattle Mount Baker 2014": "seattle_all_cases",
         "Seattle Othello 2012": "seattle_all_cases", "Chicago 2015": "chicago_tod_2013_2015"}
    out = {k: (float(oct27.loc[v, "city_housing_stock"]), f"{oct27.loc[v, 'city_housing_stock_source']} (as the 2026-10-27 table)")
           for k, v in o.items()}
    out["Portland 2020"] = (P.homes_2010("41", RAW / "tod_census_cases" / "tl_2020_41_place.zip", "GEOID", "4159000"),
                            "2010 Census blocks in the 2020 place boundary (as run_tod_citywide_per1000.py)")
    out["Austin 2009"] = (P.homes_2010("48", RAW / "tod_census_cases" / "tl_2020_48_place.zip", "GEOID", "4805000"),
                          "2010 Census blocks in the 2020 place boundary (2000 count not on disk; flagged)")
    out["Salt Lake City 2010"] = (P.homes_2010("49", RAW / "tod_census_cases" / "tl_2020_49_place.zip", "GEOID", "4967000"),
                                  "2010 Census blocks in the 2020 place boundary (2000 count not on disk; flagged)")
    p = X.read_vector(RAW / "census_cb_2024" / "cb_2024_us_place_500k.zip", columns=["NAME", "STATEFP"])
    poly = p[(p.NAME == "Denver") & (p.STATEFP == "08")].geometry.iloc[0]
    b = X.read_vector(RAW / "census_tiger_2020_tabblock" / "tl_2020_08_tabblock20.zip", columns=["HOUSING20", "INTPTLON20", "INTPTLAT20"], geometry=False)
    x, y = b.INTPTLON20.astype(float).to_numpy(), b.INTPTLAT20.astype(float).to_numpy()
    ins = X.first_within(x, y, [poly]) >= 0
    out["Denver 2018"] = (float(pd.to_numeric(b.HOUSING20, errors="coerce").fillna(0).to_numpy()[ins].sum()),
                          "2020 Census blocks in the 2024 place boundary (no 2010 Colorado blocks on disk; flagged, overstates 2017)")
    return out


# ------------------------------------------------------------------ BPS

def bps_tables():
    D = RAW / "tod_control_cities"
    bps = cc.read_bps(D / "bps", years=range(2000, 2026))
    gaz = cc.read_gazetteer(D / "Gaz_places_national.zip")
    panel, pl = cc.link(bps, gaz, cc.read_county_hu(D / "Gaz_counties_national.zip"))
    inv = cc.inventory_geoids(pd.read_csv(REFERENCE / "tod_cases.csv"), gaz)
    return bps, panel, pl, inv


def bps_city_per_year(bps, place, years) -> float:
    _, st, names = CITY[place]
    s = bps[(bps.state == st) & bps.name.isin(names)].groupby("year").units.sum().reindex(years)
    return float(s.mean()) if s.notna().all() else np.nan


# ------------------------------------------------------------------ 1A extras

def acres_and_district(cases: list[str], kc) -> dict:
    """Reform-group land acres by band, in-area (district) acres by band (reform group), and in-area after-window
    homes a year per case (all groups), with the 1/k weights."""
    ac = np.zeros(3); dac = np.zeros(3); dist = []
    kin = None
    if len(cases) > 1:   # 1/k over cases for in-area lots of any group
        ks = []
        for c in cases:
            L = pd.read_parquet(OUT / f"lots_{c}.parquet", columns=["in_reform_area", "x", "y"])
            L = L[L.in_reform_area.fillna(False).astype(bool)]
            ks.append(pd.Series(1, index=pd.MultiIndex.from_arrays([L.x.round(1), L.y.round(1)])).groupby(level=[0, 1]).size().clip(upper=1))
        kin = pd.concat(ks).groupby(level=[0, 1]).sum()
    for c in cases:
        D = P.load(c)
        D = D.assign(acres_land=pd.read_parquet(OUT / f"lots_{c}.parquet", columns=["acres_land"]).acres_land.reindex(D.index))
        yb, ya = M.windows(c)
        r = D.group == "reform"
        w = np.ones(len(D))
        if kc is not None and len(kc) and kc.max() > 1:
            k = kc.reindex(pd.MultiIndex.from_arrays([D.x[r].round(1), D.y[r].round(1)])).fillna(1).to_numpy()
            w[r.to_numpy()] = 1 / k
        ina = D.in_reform_area.fillna(False).astype(bool).to_numpy()
        for j, b in enumerate(M.BANDS):
            m = r.to_numpy() & (D.band == b).to_numpy()
            ac[j] += np.nansum(D.acres_land.to_numpy()[m] * w[m])
            dac[j] += np.nansum(D.acres_land.to_numpy()[m & ina] * w[m & ina])
        wi = np.ones(ina.sum())
        if kin is not None:
            wi = 1 / kin.reindex(pd.MultiIndex.from_arrays([D.x[ina].round(1), D.y[ina].round(1)])).fillna(1).to_numpy()
        a = cfg(c)["after"]
        dist.append({"case": c, "district_after_per_year": float((D.homes_after_win.to_numpy()[ina] * wi).sum() / ya),
                     "after": (a[0], min(a[1], 2025))})
    return {"acres": ac, "district_acres": dac, "district": dist}


# ------------------------------------------------------------------ 1B

def did_place(place, case, R, panel, pl, inv, col="units"):
    geoid = CITY[place][0]
    c = cfg(case)
    eff = c["before"][1] + 1
    before = (eff - 5, eff - 1)
    after = (c["after"][0], min(c["after"][1], 2025))
    Rt = cc.rates(panel, pl, col)
    st = pl.set_index("geoid")

    def pool_for(bef, aft):
        yrs = cc.years(bef) + cc.years(aft)
        ok = Rt.reindex(columns=yrs).notna().all(axis=1)
        cand = st.loc[st.index.intersection(Rt.index[ok])]
        t = st.loc[geoid]
        reform_ids = {CITY[p][0] for p in CITY} | {r.geoid for r in cc.REFORMS}
        keep = ~cand.index.isin(reform_ids | inv)
        keep &= cand.state.map(lambda s: REGION.get(s) == REGION[t.state]).to_numpy()
        keep &= ~cand.state.map(lambda s: cc.STATE_LAW_YEAR.get(s, 9999) <= aft[1]).to_numpy()
        keep &= ~((cand.cbsa == t.cbsa) & (t.cbsa not in ("99999", "", None))).to_numpy()
        cand = cand[keep]
        lo, hi = t.hu10 / 2, t.hu10 * 2
        while ((cand.hu10 >= lo) & (cand.hu10 <= hi)).sum() < 3 and (lo > 1 or hi < 1e8):
            lo, hi = lo / 1.5, hi * 1.5
        return list(cand[(cand.hu10 >= lo) & (cand.hu10 <= hi)].index), lo / t.hu10, hi / t.hu10

    out = {}
    for lab, bef, aft in (("main", before, after), ("placebo_3yr_early", (eff - 8, eff - 4), (eff - 3, eff - 1))):
        pool, flo, fhi = pool_for(bef, aft)
        k = min(10, len(pool))
        ctl = cc.nearest(Rt, geoid, pool, bef, k)
        est = cc.did(Rt, geoid, ctl, bef, aft)
        fakes = cc.placebos(Rt, pool, pl, bef, aft, "matched", k=min(10, len(pool) - 1))
        out[lab] = {"est": est, "fakes": fakes.to_numpy(), "pool": len(pool), "k": k, "size_band": f"x{flo:.2f}-x{fhi:.2f}",
                    "controls": ";".join(st.loc[ctl, "place_name"].astype(str)), "before": bef, "after": aft}
    office_hu, hu10 = float(st.loc[geoid, "office_hu10"]), float(st.loc[geoid, "hu10"])
    out["office_hu"], out["hu10"] = office_hu, hu10
    return out


def interval(est, fakes):
    q5, q95 = np.percentile(fakes, [5, 95])
    return est - q95, est - q5


def main() -> None:
    PL = places()
    stock = stocks()
    print({k: round(v[0]) for k, v in stock.items()})
    bps, panel, pl, inv = bps_tables()
    rows, idx, keep_draws = [], 0, {}
    rng = np.random.default_rng(SEED_PAIR)
    for place, cases in PL.items():
        kc = P.reform_key_counts(cases) if len(cases) > 1 else None
        res = []
        for c in cases:
            res.append(P.case_numbers(c, idx, kc)); idx += 1
        used = [r for r in res if "skip" not in r]
        AD = acres_and_district(cases, kc)
        # district share of city new homes (sum over cases of each case's share)
        share, bps_py = 0.0, []
        for d in AD["district"]:
            yrs = list(range(d["after"][0], d["after"][1] + 1))
            cpy = bps_city_per_year(bps, place, yrs)
            bps_py.append(cpy)
            share += d["district_after_per_year"] / cpy if cpy else np.nan
        st, src = stock[place]
        base = {"place": place, "cases": ";".join(cases) if len(cases) <= 2 else f"{len(cases)} rezonings",
                "cases_used": len(used), "city_existing_homes": st, "city_existing_homes_source": src}
        draws = {}
        for scope, sel in (("all bands, 0-1 mile", slice(None)), ("0-1/4 mile only", slice(0, 1))):
            s = P.place_summary(res, scope)
            dr = np.nansum(np.stack([np.where(np.isnan(np.asarray(c["draws_by_band"])[..., sel]).all(axis=-1), np.nan,
                                              np.nansum(np.asarray(c["draws_by_band"])[..., sel], axis=-1)) for c in used]), axis=0)
            draws[scope] = dr
            ac, dac = AD["acres"][sel].sum(), AD["district_acres"][sel].sum()
            v, lo, hi = s["extra_homes_per_year"], s["extra_low"], s["extra_high"]
            r = {**base, "measure": "1A lot tables", "scope": scope,
                 "per_100_lot_acres_per_year": 100 * v / ac, "per_100_lot_acres_low": 100 * lo / ac, "per_100_lot_acres_high": 100 * hi / ac,
                 "per_100_district_acres_per_year": 100 * v / dac if dac > 0 else np.nan,
                 "extra_homes_per_year": v, "extra_low": lo, "extra_high": hi,
                 "per_1000_per_year": 1000 * v / st, "per_1000_per_year_low": 1000 * lo / st, "per_1000_per_year_high": 1000 * hi / st,
                 "per_1000_5yr": 5000 * v / st, "per_1000_5yr_low": 5000 * lo / st, "per_1000_5yr_high": 5000 * hi / st,
                 "reform_band_lot_acres": ac, "district_lot_acres": dac,
                 "district_share_of_city_new_homes_after": share,
                 "district_new_homes_per_year_after": sum(d["district_after_per_year"] for d in AD["district"]),
                 "city_bps_new_homes_per_year_after": float(np.nanmean(bps_py)),
                 "district_share_note": "lot tables / BPS place total; " + ("Mecklenburg County office total (lower bound)" if place.startswith("Charlotte") else "NYC = 5 boroughs" if place == "New York" else "") + ("; summed over rezonings" if len(cases) > 1 else ""),
                 "reform_stops": s["reform_stops"], "comparison_stops": s["comparison_stops"],
                 "before_years": s["before_years"], "after_years": s["after_years"]}
            rows.append(r)
        q = draws["0-1/4 mile only"]
        a = draws["all bands, 0-1 mile"]
        ct = rows[-2]["extra_homes_per_year"] / rows[-1]["extra_homes_per_year"] if rows[-1]["extra_homes_per_year"] else np.nan
        with np.errstate(divide="ignore", invalid="ignore"):
            ctd = a / q
        for rr in rows[-2:]:
            rr["carry_through_1mile_over_quarter"] = ct
            rr["carry_through_low"], rr["carry_through_high"] = np.nanpercentile(ctd[q > 0], [5, 95]) if (q > 0).sum() > 50 else (np.nan, np.nan)
        keep_draws[place] = {"q": q, "a": a, "st": st}
        # ---- 1B
        b = {**base, "measure": "1B BPS whole-city DiD", "scope": "whole city"}
        if place in ("New York", "Philadelphia"):
            b["status"] = "not estimable (rule: stacked rezoning dates, no single before/after; NYC no peer size)"
            rows.append(b); print(place, "1A done; 1B left out"); continue
        for col, lab in (("units", ""), ("units5", "_5plus")):
            D = did_place(place, cases[0], None, panel, pl, inv, col)
            m, pb = D["main"], D["placebo_3yr_early"]
            conv = D["office_hu"] / D["hu10"]          # Charlotte: county office -> city homes
            lo, hi = interval(m["est"], m["fakes"])
            plo, phi = interval(pb["est"], pb["fakes"])
            b[f"per_1000_per_year{lab}"] = m["est"] * conv
            b[f"per_1000_per_year{lab}_low"], b[f"per_1000_per_year{lab}_high"] = lo * conv, hi * conv
            b[f"per_1000_5yr{lab}"] = 5 * m["est"] * conv
            b[f"placebo_3yr_early{lab}"] = pb["est"] * conv
            b[f"placebo_3yr_early{lab}_low"], b[f"placebo_3yr_early{lab}_high"] = plo * conv, phi * conv
            if lab == "":
                b["pretrend_pass"] = bool(plo <= 0 <= phi)
                keep_draws[place]["B"] = (m["est"] - rng.choice(m["fakes"], 2000)) * conv
                b["controls"], b["eligible_pool"], b["controls_used"], b["size_band"] = m["controls"], m["pool"], m["k"], m["size_band"]
                b["before_years"] = f"{m['before'][0]}-{m['before'][1]}"; b["after_years"] = f"{m['after'][0]}-{m['after'][1]}"
                b["city_hu10"] = D["hu10"]
                net = m["est"] * D["office_hu"] / 1000             # citywide net extra homes a year
                b["citywide_net_extra_homes_per_year"] = net
                b["citywide_net_low"], b["citywide_net_high"] = lo * D["office_hu"] / 1000, hi * D["office_hu"] / 1000
                sa = rows[-1]["extra_homes_per_year"]           # 1A, 1/4 mile only (b not yet appended)
                b["station_area_quarter_extra_homes_per_year"] = sa
                b["station_area_quarter_per_1000_per_year"] = 1000 * sa / st
                if sa > 0:
                    nd = (m["est"] - rng.choice(m["fakes"], 2000)) * D["office_hu"] / 1000
                    sd = rng.choice(q[np.isfinite(q)], 2000)
                    rd = nd / sd
                    b["R_citywide_over_station_area"] = net / sa
                    b["R_low"], b["R_high"] = np.percentile(rd, [5, 95])
                    keep_draws[place]["R"] = rd
                else:
                    b["R_citywide_over_station_area"] = np.nan
                    b["R_note"] = "not defined: station-area 1/4-mile extra <= 0"
        rows.append(b)
        print(place, "done", round(b.get("per_1000_per_year", np.nan), 2), b.get("pretrend_pass"))
    T = pd.DataFrame(rows)
    # ---- pooled rows
    pr = []
    A = T[T.measure == "1A lot tables"]
    for scope in ("all bands, 0-1 mile", "0-1/4 mile only"):
        a = A[A.scope == scope].set_index("place")
        key = "a" if scope.startswith("all") else "q"
        pd_ = np.mean([1000 * keep_draws[p][key] / keep_draws[p]["st"] for p in a.index], axis=0)
        v = a.per_1000_per_year
        loo = [v.drop(p).mean() for p in v.index]
        v100 = a.per_100_lot_acres_per_year
        pr.append({"place": "POOLED (equal weight, 11 places)", "measure": "1A lot tables", "scope": scope,
                   "per_1000_per_year": v.mean(), "per_1000_per_year_low": np.nanpercentile(pd_, 5), "per_1000_per_year_high": np.nanpercentile(pd_, 95),
                   "per_1000_5yr": 5 * v.mean(), "per_1000_5yr_low": 5 * np.nanpercentile(pd_, 5), "per_1000_5yr_high": 5 * np.nanpercentile(pd_, 95),
                   "per_1000_loo_low": min(loo), "per_1000_loo_high": max(loo),
                   "per_100_lot_acres_per_year": v100.mean(),
                   "per_100_lot_acres_loo_low": min(v100.drop(p).mean() for p in v100.index), "per_100_lot_acres_loo_high": max(v100.drop(p).mean() for p in v100.index),
                   "district_share_of_city_new_homes_after": a.district_share_of_city_new_homes_after.mean(),
                   "carry_through_1mile_over_quarter": np.nan})
        if scope.startswith("all"):
            lo5 = np.nanpercentile(pd_, 5)
            pr[-1]["reading_rule"] = "consistent" if v.mean() > 0 and lo5 > 0 else "not contradicted" if v.mean() > 0 else "contradicts"
    B = T[(T.measure == "1B BPS whole-city DiD") & T.per_1000_per_year.notna()].set_index("place")
    ok = B[B.pretrend_pass == True]  # noqa: E712
    if len(ok):
        v = ok.per_1000_per_year
        pr.append({"place": f"POOLED 1B (passing places: {len(ok)} of {len(B)})", "measure": "1B BPS whole-city DiD", "scope": "whole city",
                   "per_1000_per_year": v.mean(),
                   "per_1000_per_year_low": np.percentile(np.mean([keep_draws[p]["B"] for p in v.index], axis=0), 5),
                   "per_1000_per_year_high": np.percentile(np.mean([keep_draws[p]["B"] for p in v.index], axis=0), 95),
                   "per_1000_loo_low": min(v.drop(p).mean() for p in v.index) if len(v) > 1 else np.nan,
                   "per_1000_loo_high": max(v.drop(p).mean() for p in v.index) if len(v) > 1 else np.nan, "per_1000_5yr": 5 * v.mean()})
        rp = [p for p in ok.index if "R" in keep_draws[p]]
        if rp:
            Rv = ok.loc[rp, "R_citywide_over_station_area"]
            md = np.median(np.stack([keep_draws[p]["R"] for p in rp]), axis=0)
            lo, hi = np.percentile(md, [5, 95])
            med = float(Rv.median())
            down = min(med, 1.0)
            label = "median R capped at 1"
            if lo <= 1 <= hi:
                down, label = min(lo, 1.0), "lower end of median-R interval (not detectable at citywide scale)"
            pr.append({"place": f"DOWNSIDE FACTOR (median R, {len(rp)} places: {', '.join(rp)})", "measure": "1B BPS whole-city DiD",
                       "scope": "R", "R_citywide_over_station_area": med, "R_low": lo, "R_high": hi,
                       "downside_factor": down, "downside_label": label,
                       "R_loo_low": min(Rv.drop(p).median() for p in Rv.index) if len(Rv) > 1 else np.nan,
                       "R_loo_high": max(Rv.drop(p).median() for p in Rv.index) if len(Rv) > 1 else np.nan})
    T = pd.concat([T, pd.DataFrame(pr)], ignore_index=True)
    T.to_csv(REFERENCE / "tod_causal_citywide_11.csv", index=False, float_format="%.4f")
    pd.set_option("display.width", 250); pd.set_option("display.max_columns", 30)
    print(T[["place", "measure", "scope", "per_100_lot_acres_per_year", "per_1000_per_year", "per_1000_per_year_low", "per_1000_per_year_high",
             "district_share_of_city_new_homes_after", "carry_through_1mile_over_quarter"]].round(3).to_string(index=False))
    cols = [c for c in ["place", "per_1000_per_year", "per_1000_per_year_low", "per_1000_per_year_high", "placebo_3yr_early", "placebo_3yr_early_low",
                        "placebo_3yr_early_high", "pretrend_pass", "per_1000_per_year_5plus", "citywide_net_extra_homes_per_year",
                        "station_area_quarter_extra_homes_per_year", "R_citywide_over_station_area", "R_low", "R_high", "downside_factor", "size_band", "controls_used"] if c in T]
    print(T[T.measure == "1B BPS whole-city DiD"][cols].round(3).to_string(index=False))


if __name__ == "__main__":
    main()
