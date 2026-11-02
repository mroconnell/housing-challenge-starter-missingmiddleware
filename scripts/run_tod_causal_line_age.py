"""T2 line-age matching (docs/tod/CAUSAL_FRAMEWORK_PLAN.md, "Test 3 (T2)", locked before any count).

Station-area effect within 1/4 mile for the D-11 places, with each reform stop compared only with comparison stops of
the same transit era:
  M3  (main, learning plan v1): opening years within 3 years, or both open 10+ years at the reform year;
  M10 (sensitivity, first brief): opening years within +-10 years.
Unknown comparison years are kept in every matched set (flagged); variant "known" drops them.

Opening year per stop: the stop table's opening_year_best; else the hand-coded agency facts and Wikidata (CC0) matcher of
scripts/build_tod_stop_extra_traits.py (imported, unchanged), run on every station; else the line-level codes in
LINE_CODES below. Nothing in the stop table is rewritten.

    OMP_NUM_THREADS=1 .venv/bin/python scripts/run_tod_causal_line_age.py

Writes reference/tod_causal_line_age.csv (place summaries; no parcel ids, no lot rows).
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))
from missing_middleware.paths import REFERENCE  # noqa: E402

import build_tod_stop_extra_traits as XT  # noqa: E402
import build_tod_station_lot_table as BL  # noqa: E402
import run_tod_station_model as SM  # noqa: E402

OUT = ROOT / "data" / "processed" / "tod_station_area"
SEED, DRAWS = 20261102, 1000
WI_FACTOR = 4874.1 / 100 * 5 * 1.2269   # Wisconsin 1/4-mile lot acres /100 x 5 years x statewide scale
D11_SINGLE = {"austin_2009": "Austin", "charlotte_2019": "Charlotte", "chicago_2015": "Chicago 2015",
              "denver_2018": "Denver", "portland_2020": "Portland 2020", "seattle_mount_baker_2014": "Seattle Mount Baker",
              "seattle_othello_2012": "Seattle Othello", "slc_2010": "Salt Lake City", "stpaul_2011": "Saint Paul"}

# Line-level opening years for stations the stop table and Wikidata leave blank (agency opening dates, coded by hand
# from the agencies' published line histories; not re-fetched in this run, flagged "line code" in the output).
# (city, stop_type_text, set of stop names or None for all) -> year, or "old" = open long before 2000 (age class only).
LINE_CODES = [
    ("Austin", "MetroRail (commuter rail, opened 2010)", None, 2010, "CapMetro MetroRail opened March 2010"),
    ("Charlotte", "CityLYNX Gold Line streetcar", {"CPCC CityLYNX", "CTC/Arena CityLYNX"}, 2015, "CATS Gold Line phase 1, July 2015"),
    ("Charlotte", "CityLYNX Gold Line streetcar", {"Gateway Station CityLYNX"}, 2021, "CATS Gold Line phase 2, August 2021"),
    ("Charlotte", "LYNX Blue Line light rail", {"I-485 Station", "East/ West Station"}, 2007, "CATS LYNX Blue Line, November 2007"),
    ("Charlotte", "LYNX Blue Line light rail", {"Parkwood Station", "25th St Station", "36th St Station", "Sugar Creek Station",
                                               "Old Concord Road Station", "Tom Hunter Station", "University City Blvd Station",
                                               "McCullough Station", "JW Clay Blvd Station"}, 2018, "CATS Blue Line Extension, March 2018"),
    ("Chicago", "CTA rail", None, "old", "CTA Blue (Congress 1958, O'Hare 1984), Red (Dan Ryan 1969), Green (1892), Pink branch (1896) stations"),
    ("Chicago", "Metra", {"35th St. - Lou Jones"}, 2011, "Metra Rock Island 35th St-Lou Jones station, 2011"),
    ("Chicago", "Metra", None, "old", "Metra / predecessor commuter rail stations within Chicago, 19th-20th century"),
    ("Denver", "RTD rail (East Corridor)", None, 2016, "RTD A Line (East Corridor), April 2016"),
    ("New York", "Subway", None, "old", "NYC subway stations of the IRT/BMT/IND (1904-1940s)"),
    ("Philadelphia", "Rail", None, "old", "SEPTA Regional Rail stations (19th-20th century)"),
    ("Philadelphia", "Subway/elevated", None, "old", "SEPTA Market-Frankford / Broad Street stations (1907-1956)"),
    ("Philadelphia", "Trolley", None, "old", "SEPTA trolley routes (streetcar era)"),
    ("Portland", "MAX", {"Gateway North"}, "old", "TriMet MAX Blue Line Gateway, 1986"),
    ("Portland", "MAX", {"PSU South/SW 6th & College"}, 2009, "TriMet MAX on the Portland Mall, 2009"),
    ("Portland", "Street Car", {"SE M L King & Mill", "SE Grand & Hawthorne", "SE Grand & Taylor", "SE M L King & Morrison",
                                "SE Grand & Stark", "SE Grand & Burnside", "NE Oregon & Grand", "NE 7th & Holladay",
                                "NE Grand & Multnomah", "NE 7th & Halsey", "NE Weidler & Grand", "NE Broadway & 2nd",
                                "N Weidler & Ross"}, 2012, "Portland Streetcar Central Loop (east side), September 2012"),
    ("Portland", "Street Car", {"S Lowell & Bond", "S Bond & Lane", "S River & Moody", "S Harrison Street", "SW 3rd & Harrison"},
     2007, "Portland Streetcar RiverPlace / South Waterfront extensions, 2005-2007 (latest year used)"),
    ("Portland", "Street Car", {"PSU Urban Center", "SW 10th & Clay", "Art Museum", "NW 10th & Couch", "NW 11th & Glisan",
                                "NW 10th & Johnson", "NW 9th & Lovejoy", "NW 13th & Lovejoy", "NW 11th & Marshall",
                                "NW 18th & Lovejoy", "NW 14th & Northrup", "NW 21st & Lovejoy", "NW 22nd & Lovejoy",
                                "NW 18th & Northrup", "NW 21st & Northrup", "NW 23rd & Marshall", "NW 22nd & Northrup"},
     2001, "Portland Streetcar NW-PSU line, July 2001"),
]


def place_of(case: str) -> str:
    return "New York" if case.startswith("nyc_") else "Philadelphia" if case.startswith("phl_") else D11_SINGLE.get(case, "")


def opening_years() -> pd.DataFrame:
    """One row per (case, stop_id): opening year (oy), 'old' age-class flag, source kind."""
    T = pd.read_csv(XT.STOPS, low_memory=False)
    U = T.drop_duplicates("stop_key").reset_index(drop=True).copy()
    U["prio"] = True
    U["x"], U["y"] = XT.X.transform(U.lon.values, U.lat.values, 4326, XT.CRS)
    U["names"] = (U.stop_name.fillna("").astype(str) + ";" + U.names_merged.fillna("").astype(str)).str.split(";")
    M = XT.wikidata_match(U, XT.wikidata_items())[["stop_key", "wd_open_min", "wd_incep_min"]]
    H = XT.handcoded(U)
    H = H[["stop_key", "hc_open"]] if len(H) else pd.DataFrame(columns=["stop_key", "hc_open"])
    S = T[["case", "city", "role", "stop_id", "stop_key", "stop_name", "stop_type_text", "opening_year_best", "reform_year"]]
    S = S.merge(M, on="stop_key", how="left").merge(H, on="stop_key", how="left")
    S["oy"], S["src"] = np.nan, ""
    for col, lab in (("opening_year_best", "stop table"), ("hc_open", "agency hand-coded"), ("wd_open_min", "Wikidata P1619"),
                     ("wd_incep_min", "Wikidata P571")):
        m = S.oy.isna() & S[col].notna()
        S.loc[m, "oy"], S.loc[m, "src"] = S.loc[m, col], lab
    S["old"] = False
    for city, stt, names, yr, _ in LINE_CODES:
        m = S.oy.isna() & ~S.old & (S.city == city) & (S.stop_type_text == stt)
        if names is not None:
            m &= S.stop_name.isin(names)
        if yr == "old":
            S.loc[m, "old"], S.loc[m, "src"] = True, "line code (old)"
        else:
            S.loc[m, "oy"], S.loc[m, "src"] = float(yr), "line code"
    S.loc[S.src == "", "src"] = "unknown"
    return S[["case", "stop_id", "role", "stop_name", "oy", "old", "src", "reform_year"]]


def stop_sums(case: str, src: Path = OUT) -> pd.DataFrame:
    """Per stop in the 1/4-mile band: N = sum(after/ya - before/yb) homes a year, A = land acres (as case_effects)."""
    D = pd.read_parquet(src / f"lots_{case}.parquet", columns=["stop_id", "group", "band", "homes_existing", "homes_before_win",
                                                               "homes_after_win", "in_reform_area", "implausible", "acres_land"])
    if (src / f"events_{case}.parquet").exists():
        D = SM.event_windows(case, D, "permit_est", src)
    D = D[~D.implausible.fillna(False) & (D.band == "0-1/4")]
    yb, ya = SM.windows(case)
    D = D.assign(n=D.homes_after_win / ya - D.homes_before_win / yb)
    return D.groupby(["group", "stop_id"]).agg(N=("n", "sum"), A=("acres_land", "sum")).reset_index()


def match_matrix(r: pd.DataFrame, c: pd.DataFrame, ry: float, rule: str, keep_unknown: bool) -> np.ndarray:
    """Boolean (reform stops x comparison stops)."""
    ro, co = r.oy.values[:, None], c.oy.values[None, :]
    r_old = (r.old.values | (ry - r.oy.values >= 10))[:, None]
    c_old = (c.old.values | (ry - c.oy.values >= 10))[None, :]
    r_unk = (np.isnan(r.oy.values) & ~r.old.values)[:, None]
    if rule == "M3":
        c_unk = (np.isnan(c.oy.values) & ~c.old.values)[None, :]
        m = (np.abs(ro - co) <= 3) | (r_old & c_old)
    elif rule == "M10":   # needs exact years: age-class-only stops count as unknown here
        c_unk = np.isnan(c.oy.values)[None, :]
        r_unk = np.isnan(r.oy.values)[:, None]
        m = np.abs(ro - co) <= 10
    else:                 # "all": every comparison stop (reproduces the measured effect)
        return np.ones((len(r), len(c)), bool)
    m = m | r_unk                       # unknown reform stop: compared with all
    if keep_unknown:
        m = m | c_unk
    else:
        m = m & ~c_unk | (r_unk & ~c_unk)
    return m


def effect(r: pd.DataFrame, c: pd.DataFrame, M: np.ndarray, wr=None, wc=None) -> tuple[float, float]:
    wr = np.ones(len(r)) if wr is None else wr
    wc = np.ones(len(c)) if wc is None else wc
    cn, ca = M @ (wc * c.N.values), M @ (wc * c.A.values)
    ok = (ca > 0) & (r.A.values > 0) & (wr > 0)
    if not ok.any():
        return np.nan, 0.0
    dr = r.N.values / np.where(r.A.values > 0, r.A.values, np.nan)
    dm = cn / np.where(ca > 0, ca, np.nan)
    w = wr * r.A.values * ok
    return 100 * np.nansum(w * (dr - dm)) / w.sum(), (r.A.values * ok).sum() / r.A.values.sum()


VERSIONS = [("measured", "all", True), ("M3", "M3", True), ("M3_known", "M3", False), ("M10", "M10", True), ("M10_known", "M10", False)]


def main() -> None:
    rng = np.random.default_rng(SEED)
    OY = opening_years()
    cases = sorted(p.stem.removeprefix("lots_") for p in OUT.glob("lots_*.parquet"))
    cases = [c for c in cases if place_of(c)]
    measured = pd.read_csv(REFERENCE / "tod_station_area_effects_by_city.csv")
    measured = measured[measured.band == "0-1/4"].set_index("city").effect_per_100_acres
    rows, draws, transit = [], {}, []
    for case in cases:
        S = stop_sums(case).merge(OY[OY.case == case], on="stop_id", how="left")
        ry = float(S.reform_year.dropna().iloc[0])
        r = S[S.group == "reform"].reset_index(drop=True)
        c = S[S.group == "comparison"].reset_index(drop=True)
        new_r = (ry - r.oy <= 3).values   # opened after the reform or within 3 years before it
        rec = {"case": case, "place": place_of(case), "reform_year": ry,
               "reform_stops": len(r), "comparison_stops": len(c),
               "reform_acres": r.A.sum(), "reform_acres_new_transit_share": r.A[new_r].sum() / r.A.sum(),
               "reform_stops_unknown_year": int((r.src == "unknown").sum()),
               "comparison_stops_unknown_year": int((c.src == "unknown").sum()),
               "comparison_stops_line_code": int(c.src.str.startswith("line code").sum())}
        bi_r = rng.integers(0, len(r), (DRAWS, len(r)))
        bi_c = rng.integers(0, len(c), (DRAWS, len(c)))
        for lab, rule, keep in VERSIONS:
            M = match_matrix(r, c, ry, rule, keep)
            e, kept = effect(r, c, M)
            rec[f"{lab}"] = e
            rec[f"{lab}_reform_acres_kept"] = kept
            if rule != "all":
                known_c = ~((c.src == "unknown") | (rule == "M10") & c.oy.isna()).values
                used = M[(r.A.values > 0)].any(axis=0) & known_c & (c.A.values > 0)
                rec[f"{lab}_matched_known_comparison_ids"] = ",".join(map(str, sorted(c.stop_id[used])))
            d = np.empty(DRAWS)
            for k in range(DRAWS):
                wr = np.bincount(bi_r[k], minlength=len(r)).astype(float)
                wc = np.bincount(bi_c[k], minlength=len(c)).astype(float)
                d[k] = effect(r, c, M, wr, wc)[0]
            draws[(case, lab)] = d
        # transit-only check: comparison stops opened within 3 years before the reform or in the after window
        cfg = {**BL.CASES, **{k: v for k, (_, v) in BL.adapter_cases().items()}}[case]
        newc = ((c.oy >= ry - 3) & (c.oy <= cfg["after"][1])).values
        oldc = ((ry - c.oy >= 10) | c.old).values
        if newc.any() and oldc.any() and c.A[newc].sum() > 0 and c.A[oldc].sum() > 0:
            dn = 100 * c.N[newc].sum() / c.A[newc].sum()
            do = 100 * c.N[oldc].sum() / c.A[oldc].sum()
            transit.append({"case": case, "place": place_of(case), "new_stops": int(newc.sum()), "new_acres": c.A[newc].sum(),
                            "new_minus_old": dn - do, "new_stop_names": "; ".join(c.stop_name[newc].astype(str))})
        rows.append(rec)
        print(case, {k: round(v, 1) for k, v in rec.items() if k in ("measured", "M3", "M3_known", "M10")}, flush=True)
    C = pd.DataFrame(rows)

    # place level
    P = []
    for place, g in C.groupby("place"):
        p = {"place": place, "cases": len(g), "measured_published": measured.get(
            {"Chicago 2015": "chicago_2015", "Portland 2020": "portland_2020", "Austin": "austin_2009", "Charlotte": "charlotte_2019",
             "Denver": "denver_2018", "Seattle Mount Baker": "seattle_mount_baker_2014", "Seattle Othello": "seattle_othello_2012",
             "Salt Lake City": "slc_2010", "Saint Paul": "stpaul_2011"}.get(place, place), np.nan)}
        w = g.reform_acres
        p["new_transit_share"] = (g.reform_acres_new_transit_share * w).sum() / w.sum()
        p["flag_rezoned_with_new_transit"] = p["new_transit_share"] > 0.5
        p["comparison_stops"] = int(g.comparison_stops.sum())
        p["comparison_stops_unknown_year"] = int(g.comparison_stops_unknown_year.sum())
        for lab, rule, keep in VERSIONS:
            vals = g[lab]
            p[lab] = vals.mean()
            dd = np.nanmean(np.vstack([draws[(cs, lab)] for cs in g.case]), axis=0)
            draws[(place, lab)] = dd
            p[f"{lab}_lo90"], p[f"{lab}_hi90"] = np.nanpercentile(dd, [5, 95])
            p[f"{lab}_cases_estimable"] = int(vals.notna().sum())
            p[f"{lab}_reform_acres_kept"] = (g[f"{lab}_reform_acres_kept"] * w).sum() / w.sum()
            if rule != "all":
                ids = set()
                for cs, s in zip(g.case, g[f"{lab}_matched_known_comparison_ids"]):
                    ids |= {f"{cs}:{i}" if not cs.startswith(("nyc_", "phl_")) else i for i in str(s).split(",") if i}
                # New York / Philadelphia: stop ids repeat across rezonings; count distinct stop ids over the place
                p[f"{lab}_matched_known_comparison_stops"] = len(ids)
        P.append(p)
    P = pd.DataFrame(P)
    passes = int((P.M3_matched_known_comparison_stops >= 3).sum())

    def pooled(lab: str, mask) -> dict:
        v = P.loc[mask, ["place", lab]].dropna()
        dd = np.nanmean(np.vstack([draws[(pl, lab)] for pl in v.place]), axis=0)
        loo = [v[lab].drop(i).mean() for i in v.index]
        return {"value": v[lab].mean(), "lo90": np.nanpercentile(dd, 5), "hi90": np.nanpercentile(dd, 95),
                "loo_low": min(loo), "loo_high": max(loo), "places": len(v)}

    out = P.copy()
    out.insert(0, "row", "place")
    summ = []
    for lab, *_ in VERSIONS:
        for nm, mask in (("all 11", P.place.notna()), ("without flagged", ~P.flag_rezoned_with_new_transit),
                         ("flagged only", P.flag_rezoned_with_new_transit)):
            if mask.sum() == 0:
                continue
            q = pooled(lab, mask)
            summ.append({"row": "pooled", "place": f"{lab} | {nm}", lab: q["value"], f"{lab}_lo90": q["lo90"], f"{lab}_hi90": q["hi90"],
                         "loo_low": q["loo_low"], "loo_high": q["loo_high"], "places_in_pool": q["places"],
                         "wisconsin_central": q["value"] * WI_FACTOR, "wisconsin_lo90": q["lo90"] * WI_FACTOR,
                         "wisconsin_hi90": q["hi90"] * WI_FACTOR})
    S_ = pd.DataFrame(summ)
    TR = pd.DataFrame(transit)
    if len(TR):
        tp = TR.groupby("place").new_minus_old.mean()
        summ_t = {"row": "transit_only_check", "place": f"new-line comparison stops minus old ones, mean over {len(tp)} places",
                  "measured": tp.mean(), "note": "; ".join(f"{k} {v:.1f}" for k, v in tp.items())}
        S_ = pd.concat([S_, pd.DataFrame([summ_t])], ignore_index=True)
    hop = pd.read_csv(REFERENCE / "tod_station_checks_milwaukee_placebo.csv")
    hop = hop[hop.band == "0-1/4"]
    S_ = pd.concat([S_, pd.DataFrame([{"row": "transit_only_check", "place": f"Milwaukee Hop placebo ({v})", "measured": e}
                                      for v, e in zip(hop.version, hop.effect_per_100_acres)])], ignore_index=True)
    S_ = pd.concat([S_, pd.DataFrame([{"row": "pass_rule", "place": f"M3: places with >=3 matched known comparison stops = {passes} of {len(P)}",
                                       "note": "PASS (matched version becomes main T2 estimate)" if passes >= 8 else "FAIL (matched version is a sensitivity)"}])],
                   ignore_index=True)
    res = pd.concat([out.drop(columns=[c for c in out.columns if c.endswith("_ids")], errors="ignore"), S_], ignore_index=True)
    res.round(4).to_csv(REFERENCE / "tod_causal_line_age.csv", index=False)
    pd.set_option("display.width", 250, "display.max_columns", 40)
    print(P[["place", "measured_published", "measured", "M3", "M3_lo90", "M3_hi90", "M3_known", "M10", "M10_known",
             "new_transit_share", "M3_matched_known_comparison_stops", "M3_reform_acres_kept", "comparison_stops_unknown_year"]].round(1).to_string(index=False))
    print(S_.round(1).to_string(index=False))
    if len(TR):
        print(TR.round(1).to_string(index=False))


EXTRA = {"honolulu_2017": "Honolulu", "bellevue_belred_2009": "Bellevue BelRed", "seattle_roosevelt_2012": "Seattle Roosevelt"}
CELLS = [("new", "no"), ("old", "no"), ("old", "up"), ("new", "up")]


def twobytwo() -> None:
    """T2b (CAUSAL_FRAMEWORK_PLAN.md): cells of line age x upzoning, stops within 1/4 mile."""
    OY = opening_years()
    allc = {}
    for p in OUT.glob("lots_*.parquet"):
        c = p.stem.removeprefix("lots_")
        if place_of(c) or c in EXTRA:
            allc[c] = OUT
    allc["seattle_roosevelt_2012"] = OUT / "candidates"
    recs, counts = [], []
    for case, src in sorted(allc.items()):
        S = stop_sums(case, src).merge(OY[OY.case == case], on="stop_id", how="left")
        ry = float(S.reform_year.dropna().iloc[0])
        cfg = {**BL.CASES, **{k: v for k, (_, v) in BL.adapter_cases().items()}}.get(case)
        ae = cfg["after"][1] if cfg else ry + 5
        age = np.where((S.oy >= ry - 3) & (S.oy <= ae), "new", np.where((ry - S.oy >= 10) | S.old, "old", "excluded"))
        S["age"] = age
        S["up"] = np.where(S.group == "reform", "up", "no")
        place = place_of(case) or EXTRA[case]
        for (a, u), g in S.groupby(["age", "up"]):
            counts.append({"case": case, "place": place, "age": a, "up": u, "stops": len(g), "acres": g.A.sum()})
            if a != "excluded" and g.A.sum() > 0:
                recs.append({"case": case, "place": place, "extra": case in EXTRA, "cell": f"{a}/{u}", "d": 100 * g.N.sum() / g.A.sum(), "acres": g.A.sum()})
    # Milwaukee Hop placebo: one place in new/no (all its 1/4-mile lots; recorded acres)
    M = pd.read_parquet(OUT / "checks_milwaukee_placebo_lots.parquet")
    M = M[(M.band == "0-1/4") & ~M.implausible.fillna(False)]
    recs.append({"case": "milwaukee_placebo", "place": "Milwaukee Hop placebo", "extra": False, "cell": "new/no",
                 "d": 100 * (M.a2024.sum() / 5 - M.b.sum() / 5) / M.acres.sum(), "acres": M.acres.sum()})
    counts.append({"case": "milwaukee_placebo", "place": "Milwaukee Hop placebo", "age": "new", "up": "no", "stops": np.nan, "acres": M.acres.sum()})
    R = pd.DataFrame(recs)
    K = pd.DataFrame(counts)
    PC = R.groupby(["place", "extra", "cell"]).d.mean().reset_index()   # place x cell (NY/PHL averaged over rezonings)
    rng = np.random.default_rng(SEED)
    rows = []

    def contrasts(cm: dict) -> dict:
        g = lambda k: cm.get(k, np.nan)  # noqa: E731
        return {"transit_alone": g("new/no") - g("old/no"), "upzoning_alone": g("old/up") - g("old/no"),
                "interaction": g("new/up") - g("new/no") - g("old/up") + g("old/no")}

    def within(T: pd.DataFrame) -> dict:
        W = T.pivot_table(index="place", columns="cell", values="d")
        out = {}
        for nm, need, f in (("transit_alone", ["new/no", "old/no"], lambda w: w["new/no"] - w["old/no"]),
                            ("upzoning_alone", ["old/up", "old/no"], lambda w: w["old/up"] - w["old/no"]),
                            ("interaction", ["new/up", "new/no", "old/up", "old/no"],
                             lambda w: w["new/up"] - w["new/no"] - w["old/up"] + w["old/no"])):
            w = W.dropna(subset=[c for c in need if c in W]) if all(c in W for c in need) else W.iloc[0:0]
            out[nm] = (f(w).mean() if len(w) else np.nan, len(w))
        return out

    for version, mask in (("main: D-11 + Milwaukee", ~PC.extra), ("sensitivity: + Honolulu, BelRed, Roosevelt", PC.extra | ~PC.extra),
                          ("sensitivity: D-11 only", ~PC.extra & (PC.place != "Milwaukee Hop placebo"))):
        T = PC[mask]
        places = T.place.unique()
        cm = T.groupby("cell").d.mean().to_dict()
        est = contrasts(cm)
        bs, dropped = [], 0
        for _ in range(2000):
            pick = rng.choice(places, len(places), replace=True)
            B = pd.concat([T[T.place == p] for p in pick])
            bcm = B.groupby("cell").d.mean().to_dict()
            if any(k not in bcm for k, _ in [(c, 0) for c in ("new/no", "old/no", "old/up", "new/up")]):
                dropped += 1
                continue
            bs.append({**bcm, **contrasts(bcm)})
        BS = pd.DataFrame(bs)
        wi = within(T)
        for cell in ("new/no", "old/no", "old/up", "new/up"):
            t = T[T.cell == cell]
            rows.append({"version": version, "row": "cell", "name": cell, "value": cm.get(cell, np.nan),
                         "lo90": BS[cell].quantile(.05), "hi90": BS[cell].quantile(.95), "places": t.place.nunique(),
                         "place_list": "; ".join(f"{p} {v:.1f}" for p, v in zip(t.place, t.d)),
                         "stops": int(K[K.place.isin(t.place) & (K.age + "/" + K.up == cell)].stops.sum())})
        for nm, v in est.items():
            lo, hi = BS[nm].quantile(.05), BS[nm].quantile(.95)
            rows.append({"version": version, "row": "effect", "name": nm, "value": v, "lo90": lo, "hi90": hi,
                         "wisconsin": v * WI_FACTOR, "wisconsin_lo90": lo * WI_FACTOR, "wisconsin_hi90": hi * WI_FACTOR,
                         "within_place_value": wi[nm][0], "within_place_n": wi[nm][1], "bootstrap_draws_dropped": dropped})
        ia = est["interaction"]
        lo, hi = BS["interaction"].quantile(.05), BS["interaction"].quantile(.95)
        material = (lo > 0 or hi < 0) and abs(ia) > 0.25 * abs(est["upzoning_alone"])
        law = est["upzoning_alone"] + (ia if material and ia > 0 else 0)
        rows.append({"version": version, "row": "rule", "name": "interaction material" if material else "interaction not material",
                     "value": law, "wisconsin": law * WI_FACTOR,
                     "place_list": "law effect near new lines = upzoning alone" + (" + interaction" if material and ia > 0 else "")})
    ex = K[K.age == "excluded"].groupby(["place", "up"]).stops.sum()
    rows.append({"version": "all", "row": "excluded_stops", "name": "4-9 years old, opened after the after window, or unknown",
                 "value": ex.sum(), "place_list": "; ".join(f"{p}/{u} {int(v)}" for (p, u), v in ex.items())})
    O = pd.DataFrame(rows)
    O.round(3).to_csv(REFERENCE / "tod_causal_line_age_2x2.csv", index=False)
    pd.set_option("display.width", 250, "display.max_columns", 20, "display.max_colwidth", 120)
    print(O.round(1).to_string(index=False))


if __name__ == "__main__":
    if "--twobytwo" in sys.argv:
        twobytwo()
    else:
        main()
