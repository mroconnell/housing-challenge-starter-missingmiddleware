"""Parking dose-response (docs/parking/DOSE_PLAN.md): per-place effects for the reforms outside the 74, with the batch
pipeline's own code, pools, windows and seeds, plus their placebo stand-ins, event-study leads and placebo-date
(shifted) effects; the 74's own rows are copied from the same working copy so that one set of files feeds the dose fit.

Run by scripts/run_parking_dose.sh on an outcome working copy (MM_REFERENCE_DIR = data/processed/dose/<outcome>_ref,
MM_BPS_OUTCOME set for units_2_4, unset for all homes) AFTER that copy's batch pipeline and Test 56 extras (event,
placebo_dates) have run. Existing scripts are imported, never edited. Refuses to run unless the dose table is frozen
(scripts/parking_dose_common.require_frozen_doses: committed, sha256 equal to the first one in DOSES_BUILT.md).

    uv run --all-extras python scripts/run_parking_dose_effects.py --parts match,effects,standins,event,shift
    uv run --all-extras python scripts/run_parking_dose_effects.py --augment-taxonomy   # drop-from-pools copy only

Which reforms: every dose-table row outside the 74 with event_used = yes (pooled, alone, dose-0 and waiting rows alike;
the dose fit decides who is pooled). BPS key: same state, BPS name equal to the place name once a trailing
city/town/borough/village/township is removed, incorporated place preferred; anything else stops the run.

Main method (as run_parking_expanded.us_effects / run_parking_partial): cmp.effects(min_post=1), ACS 2020-2024 homes and
population, comparison pools excluding the taxonomy's citywide benchmark places and the 74 (the new place itself is
removed from that list for its own call). Central Falls (C8): after-years end in 2024 (cmp.LAST_YEAR set to 2024 for its
calls only).
Method 2, D: run_parking_method2.case_effect(D, case, "D", OPT_MAIN) on the corrected data (Test 56 patch: pools and
pre-event homes on all permits), scale 1, not trimmed.
Stand-ins: run_parking_placebo.py --full logic (never-repealed places at 0.5-2x population, state -> division -> nation
until 20, the real place's event year and after-year count, its key added to the exclusions); stand-in order from
rng(20261027), restarted for the new places in dose-table order (order only maps draws to stand-ins).
Leads: run_parking_t56_extras.event_main / event_d (years -5..+3, reference -1) with the main pool from cmp.controls.
Shifted dates 2 and 4: run_parking_t52_placebos timing logic (cmp.effects with event year - s, pools re-chosen; D on
the shifted standard windows; stand-ins as above at the shifted year).

Outputs (in MM_REFERENCE_DIR): dose_match.csv, dose_places.csv, dose_wi_cells.csv, dose_standins.csv,
dose_event_places.csv, dose_shift{2,4}_places.csv, dose_shift{2,4}_standins.csv.
"""
from __future__ import annotations

import argparse
import contextlib
import os
import re
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))

import parking_dose_common as dc  # noqa: E402
from missing_middleware.parking import comparison as cmp  # noqa: E402

STANDIN_SEED, MIN_STANDINS = 20261027, 20
SUFFIX = re.compile(r"\s+(city and borough|city|town|township|borough|village|municipality|plantation|cdp)$")
KEY_OVERRIDE: dict[str, str] = {}  # reform_id -> BPS key, only if the name rule fails (record the reason in the notes)


def ref() -> Path:
    from missing_middleware.paths import REFERENCE
    return REFERENCE


@contextlib.contextmanager
def last_year(y):
    """Temporarily end the after-window at y (Central Falls, C8); cmp.windows reads cmp.LAST_YEAR at call time."""
    old = cmp.LAST_YEAR
    if y is not None:
        cmp.LAST_YEAR = min(int(y), old)
    try:
        yield
    finally:
        cmp.LAST_YEAR = old


_orig_complete = cmp.complete
_ccache: dict = {}


def fast_complete(p, years):
    k = (id(p), tuple(years))
    if k not in _ccache:
        _ccache[k] = _orig_complete(p, years)
    return _ccache[k]


# ------------------------------------------------------------------ BPS keys (names only) -----------------------------
def bps_names(p: pd.DataFrame) -> pd.DataFrame:
    last = p.sort_values("year").drop_duplicates("key", keep="last")
    last = last[~last["name"].str.lower().str.contains("county|balance")].copy()
    last["norm"] = last["name"].str.lower().str.strip().map(lambda s: SUFFIX.sub("", s))
    last["is_place"] = last["fips_place"].str.strip("0") != ""
    return last[["key", "state_fips", "name", "norm", "is_place", "pop"]]


def find_key(names: pd.DataFrame, state: str, place: str) -> tuple[str | None, str]:
    import run_parking_comparison as rpc
    st = rpc.STATE_FIPS.get(state, "??")
    want = SUFFIX.sub("", dc.norm_place(place))
    c = names[(names["state_fips"] == st) & (names["norm"] == want)]
    if len(c) > 1 and c["is_place"].any():
        c = c[c["is_place"]]
    if len(c) == 1:
        return str(c["key"].iloc[0]), "matched"
    return None, "not found" if c.empty else f"ambiguous: {', '.join(c['name'])}"


def drop_list(universe: Path = dc.UNIVERSE) -> pd.DataFrame:
    """C5 check: every dated partial reform outside the 74 that touches housing leaves all pools (statewide rules, undated
    or non-reform rows, and non-residential-only reforms are not partial housing reforms)."""
    u = pd.read_csv(universe, dtype=str).fillna("")
    u = u[u["in_main_74"].str.lower() != "yes"]
    u = u[pd.to_numeric(u["year"], errors="coerce").notna()]
    cj = u["could_join"].str.lower()
    u = u[~cj.str.startswith(("no: no date", "no: not a reform", "no: no dated housing"))]
    u = u[~u["reform_id"].str.startswith(("oth_california_statewide", "oth_oregon_cfec"))]
    u = u[~u["type"].str.contains("non-residential only")]
    return u


# ------------------------------------------------------------------ setup ---------------------------------------------
class Ctx:
    def __init__(self, need_d: bool = True):
        import parking_t56_common as c56
        import run_parking_comparison as rpc
        import run_parking_method2 as m
        import run_parking_t45_t46 as t46
        from missing_middleware.paths import RAW
        REF = ref()
        self.m, self.rpc = m, rpc
        self.doses = dc.load_doses()
        self.ids74 = set(dc.main74()["reform_id"])
        self.new = self.doses[(self.doses["role"] != "74") & self.doses["event_used_yes"]].reset_index(drop=True)
        m.SUF, m.CORRECTED = "_corrected", True
        c56.patch_method2(m)
        c56.patch_rebuild(t46)
        self.D = m.Data() if need_d else None
        p = cmp.panel(rpc.read_bps_us())
        homes_geo = rpc.acs_table(RAW / "census_acs5_2024_tbsf" / "acsdt5y2024-b25002.dat", "B25002_E001")
        pop_geo = rpc.acs_table(RAW / "census_acs5_2024_tbsf" / "acsdt5y2024-b01003.dat", "B01003_E001")
        geo = p.drop_duplicates("key", keep="last").set_index("key")
        homes = geo["acs_geoid"].map(homes_geo)
        self.homes = homes[homes > 0]
        self.popn = geo["acs_geoid"].map(pop_geo)
        self.p, self.geo = p, geo
        tax = pd.read_csv(REF / "parking_reform_taxonomy.csv")
        reformed = tax[(tax["policy"] == "rm_min") & tax["benchmark_rating"].isin(["at", "near"]) & (tax["place_type"] == "city")]
        exc = {k for r in reformed.drop_duplicates("prn_key").itertuples()
               if (k := cmp.match_place(p, rpc.STATE_FIPS.get(r.state, "??"), r.place, r.population))}
        real = pd.read_csv(REF / "parking_expanded_effects.csv", dtype={"key": str})
        self.real = real[(real["status"] == "included") & (real["outcome"] == "all")].dropna(subset=["effect"]).reset_index(drop=True)
        assert len(self.real) == 74, len(self.real)
        self.real["reform_id"] = dc.match74(self.real)
        self.excluded = exc | set(self.real["key"])
        cmp.complete = fast_complete
        names = bps_names(p)
        self.keys = {}
        rows = []
        for r in self.new.itertuples():
            k, status = (KEY_OVERRIDE[r.reform_id], "override") if r.reform_id in KEY_OVERRIDE else find_key(names, r.state, r.place)
            self.keys[r.reform_id] = k
            rows.append(dict(reform_id=r.reform_id, role=r.role, place=r.place, state=r.state, event_year=r.year_num, key=k,
                             bps_name=names.set_index("key")["name"].get(k, "") if k else "", match=status))
        self.match = pd.DataFrame(rows)
        bad = self.match[(self.match["role"] == "pooled") & self.match["key"].isna()]
        if len(bad):
            raise SystemExit("BPS key not found or ambiguous for pooled places:\n" + bad.to_string(index=False))

    def case(self, r) -> dict:
        k = self.keys[r.reform_id]
        with last_year(dc.POST_END.get(r.reform_id)):
            pre, post = cmp.windows(int(r.year_num))
        return dict(reform_id=r.reform_id, key=k, event_year=int(r.year_num), pre=tuple(pre), post=tuple(post), scale=1.0,
                    pop=float(self.popn.get(k, np.nan)), trimmed=False, place=r.place, state=r.state,
                    homes=float(self.homes.get(k, np.nan)), post_end=dc.POST_END.get(r.reform_id))

    def cases(self) -> list[dict]:
        return [self.case(r) for r in self.new.itertuples() if self.keys.get(r.reform_id)]


# ------------------------------------------------------------------ main effects and stand-ins ------------------------
def main_effect(C: Ctx, c: dict, ey: int | None = None, post_end=None) -> dict:
    ey = c["event_year"] if ey is None else ey
    with last_year(post_end):
        e = cmp.effects(C.p, pd.DataFrame([{"key": c["key"], "event_year": ey}]), C.excluded - {c["key"]}, C.homes, C.popn, min_post=1)
        r = e.iloc[0].to_dict()
        out = dict(main_status=r["status"], main_effect=np.nan, main_n_post=np.nan, rate_before=np.nan, n_controls=np.nan, pool=[])
        if r["status"] == "included":
            a = e[e["outcome"] == "all"].iloc[0]
            pool, _ = cmp.controls(C.p, c["key"], ey, C.excluded - {c["key"]}, C.homes, C.popn)
            out.update(main_effect=float(a["effect"]) / c["scale"], main_n_post=int(a["n_post"]), rate_before=float(a["rate_before"]),
                       n_controls=int(a["n_controls"]), pre_years=a["pre_years"], post_years=a["post_years"], pool=list(pool))
    return out


def standins(C: Ctx, c: dict, ey: int, n_post: int, rng, post_end=None) -> tuple[list[dict], dict]:
    """run_parking_placebo.py --full (and run_parking_t52_placebos.placebo_spread) for one real place."""
    st = c["key"].split("|")[0]
    with last_year(post_end):
        pre, post = cmp.windows(ey)
        post = post[:n_post]
        ok = cmp.complete(C.p, pre + post) & set(C.homes.index)
        pop0 = C.popn.get(c["key"], np.nan)
        if pd.isna(pop0):
            pop0 = c["pop"]
        size_ok = [k for k in ok if k not in C.excluded and 0.5 * pop0 <= C.popn.get(k, np.nan) <= 2 * pop0]
        cand, scope = [k for k in size_ok if k.startswith(st + "|")], "state"
        if len(cand) < MIN_STANDINS:
            div = C.geo["division"].get(c["key"], "")
            cand, scope = [k for k in size_ok if C.geo["division"].get(k, "") == div], "division"
            if len(cand) < MIN_STANDINS:
                cand, scope = size_ok, "nation"
        info = dict(reform_id=c["reform_id"], scope=scope, standins=len(cand))
        if not cand:
            return [], info
        pick = list(rng.choice(sorted(cand), size=len(cand), replace=False))
        eff = cmp.effects(C.p, pd.DataFrame({"key": pick, "event_year": ey}), C.excluded | {c["key"]}, C.homes, C.popn, min_post=1)
    eff = eff[(eff["status"] == "included") & (eff["outcome"] == "all")]
    eff = eff[eff["n_post"] == n_post]
    return [dict(reform_id=c["reform_id"], placebo_key=x.key, event_year=ey, n_post=int(x.n_post), homes=x.homes,
                 effect=x.effect, weight=x.homes * x.n_post) for x in eff.itertuples()], info


def d_effect(C: Ctx, c: dict, ey: int | None = None, shifted: bool = False) -> tuple[float, int]:
    m = C.m
    if not shifted:
        r = m.case_effect(C.D, c, "D", m.OPT_MAIN)
        return float(r["effect"]), len(c["post"])
    pre, post = cmp.windows(ey)
    if len(pre) < cmp.PRE_YEARS_MIN or not post:
        return np.nan, len(post)
    r = m.case_effect(C.D, dict(c, event_year=ey, pre=tuple(pre), post=tuple(post), trimmed=False), "D", m.OPT_MAIN)
    return float(r["effect"]), len(post)


# ------------------------------------------------------------------ parts ---------------------------------------------
def part_match(C: Ctx) -> None:
    C.match.to_csv(ref() / "dose_match.csv", index=False)
    print(C.match.to_string(index=False), flush=True)


def part_effects(C: Ctx) -> dict:
    """dose_places.csv: the 74 (from this copy's batch outputs) and every new reform (computed here)."""
    m, REF, D = C.m, ref(), C.D
    r = C.real
    bp = pd.read_csv(REF / "parking_method2_corrected_places.csv")
    bp = bp[bp["variant"] == "method 2, D"].reset_index(drop=True)
    assert (bp["place"].values == r["place"].values).all(), "method-2 rows out of order"
    rows = [dict(reform_id=x.reform_id, group="74", col=i, key=x.key, place=x.place, state=x.state, event_year=int(x.event_year),
                 homes=float(x.homes), n_post=int(x.n_post), population=float(x.population) if pd.notna(x.population) else np.nan,
                 metro=float(D.metro.get(x.key, 0.0)), main_status="included", main_effect=float(x.effect),
                 main_weight=float(x.homes * x.n_post), d_effect=float(bp.loc[i, "effect"]),
                 rate_before=float(x.rate_before), post_end=np.nan)
            for i, x in enumerate(r.itertuples())]
    pools = {}
    for j, c in enumerate(C.cases()):
        a = main_effect(C, c, post_end=c["post_end"])
        pools[c["reform_id"]] = a.pop("pool")
        de, _ = d_effect(C, c)
        n_post = a["main_n_post"] if np.isfinite(a["main_n_post"]) else len(c["post"])
        rows.append(dict(reform_id=c["reform_id"], group="new", col=74 + j, key=c["key"], place=c["place"], state=c["state"],
                         event_year=c["event_year"], homes=c["homes"], n_post=n_post, population=c["pop"],
                         metro=float(D.metro.get(c["key"], 0.0)), main_weight=c["homes"] * n_post, d_effect=de,
                         post_end=c["post_end"] if c["post_end"] else np.nan, **a))
        print("effects", c["reform_id"], a["main_status"], flush=True)
    P = pd.DataFrame(rows)
    P["d_available"] = np.isfinite(P["d_effect"])
    P.to_csv(REF / "dose_places.csv", index=False)
    wi = m.target_cells(D, "55")
    wi.rename("h").reset_index().to_csv(REF / "dose_wi_cells.csv", index=False)
    return pools


def new_rows(C: Ctx) -> pd.DataFrame:
    P = pd.read_csv(ref() / "dose_places.csv", dtype={"key": str})
    return P[P["group"] == "new"].reset_index(drop=True)


def part_standins(C: Ctx) -> None:
    REF = ref()
    rng = np.random.default_rng(STANDIN_SEED)
    st74 = pd.read_csv(REF / "parking_placebo_full_places.csv")
    out = [st74.assign(col=st74["real_index"], reform_id=st74["real_index"].map(dict(enumerate(C.real["reform_id"]))))
           [["col", "reform_id", "placebo_key", "event_year", "n_post", "homes", "effect", "weight"]]]
    scopes = []
    byid = {c["reform_id"]: c for c in C.cases()}
    for r in new_rows(C).itertuples():
        if r.main_status != "included":
            continue
        s, info = standins(C, byid[r.reform_id], int(r.event_year), int(r.n_post), rng, post_end=byid[r.reform_id]["post_end"])
        scopes.append(info)
        if s:
            out.append(pd.DataFrame(s).assign(col=r.col))
        print("standins", r.reform_id, info["scope"], info["standins"], flush=True)
    pd.concat(out, ignore_index=True).to_csv(REF / "dose_standins.csv", index=False)
    pd.DataFrame(scopes).to_csv(REF / "dose_standin_scopes.csv", index=False)


def part_event(C: Ctx, pools: dict | None = None) -> None:
    import run_parking_t56_extras as ex
    REF = ref()
    e74 = pd.read_csv(REF / "parking_t56_event_places.csv")
    n = len(e74) // 2
    assert n == 74 and (e74["method"].values == ["main"] * 74 + ["D"] * 74).all(), "Test 56 event places: unexpected layout"
    e74 = e74.assign(reform_id=list(C.real["reform_id"]) * 2)
    rows = []
    for c in C.cases():
        pool = pools[c["reform_id"]] if pools and c["reform_id"] in pools else None
        if pool is None:
            with last_year(c["post_end"]):
                pool, _ = cmp.controls(C.p, c["key"], c["event_year"], C.excluded - {c["key"]}, C.homes, C.popn)
        cc = dict(c, pool=list(pool), p=C.p, call_homes=C.homes)
        for meth, e in (("main", ex.event_main(cc)), ("D", ex.event_d(C.D, cc))):
            rows.append(dict(method=meth, place=c["place"], state=c["state"], event_year=c["event_year"], reform_id=c["reform_id"],
                             **{f"k{k}": e[k] for k in ex.KS}))
    E = pd.concat([e74, pd.DataFrame(rows)], ignore_index=True)
    E.to_csv(REF / "dose_event_places.csv", index=False)


def part_shift(C: Ctx) -> None:
    REF = ref()
    byid = {c["reform_id"]: c for c in C.cases()}
    for s in dc.SHIFTS:
        d = REF / f"t56_placebo_shift{s}"
        p74 = pd.read_csv(d / f"parking_t56_placebo_shift{s}_places.csv")
        assert len(p74) == 74 and (p74["i"].values == np.arange(74)).all()
        rows = []
        for x in p74.itertuples():
            rows.append(dict(reform_id=C.real.loc[x.i, "reform_id"], col=int(x.i), shifted_event_year=int(x.event_year),
                             main_status=x.status, main_effect=x.effect if x.status == "included" else np.nan,
                             main_n_post=x.n_post if x.status == "included" else np.nan, d_effect=x.d_effect,
                             d_n_post=len(cmp.windows(int(x.event_year))[1])))
        s74 = pd.read_csv(d / "standins" / "d_timing4_standins.csv")
        sts = [s74.assign(col=s74["real_index"])[["col", "placebo_key", "event_year", "n_post", "homes", "effect", "weight"]]]
        rng = np.random.default_rng(STANDIN_SEED)
        for r in new_rows(C).itertuples():
            c = byid[r.reform_id]
            ey = c["event_year"] - s
            a = main_effect(C, c, ey=ey)
            a.pop("pool")
            de, dn = d_effect(C, c, ey=ey, shifted=True)
            rows.append(dict(reform_id=r.reform_id, col=int(r.col), shifted_event_year=ey, main_status=a["main_status"],
                             main_effect=a["main_effect"], main_n_post=a["main_n_post"], d_effect=de, d_n_post=dn))
            if a["main_status"] == "included":
                st, _ = standins(C, c, ey, int(a["main_n_post"]), rng)
                if st:
                    sts.append(pd.DataFrame(st).assign(col=int(r.col))[["col", "placebo_key", "event_year", "n_post", "homes", "effect", "weight"]])
            print("shift", s, r.reform_id, a["main_status"], flush=True)
        pd.DataFrame(rows).to_csv(REF / f"dose_shift{s}_places.csv", index=False)
        pd.concat(sts, ignore_index=True).to_csv(REF / f"dose_shift{s}_standins.csv", index=False)


def augment_taxonomy() -> None:
    """Drop-from-pools copy (C5 check): append every dated partial housing reform outside the 74 to this copy's
    taxonomy as a citywide benchmark city, under its exact BPS name and population, so that every script's exclusion
    list (main pools, stand-ins, D's main and strict lists) leaves it out. Names only; no permit count is used."""
    import run_parking_comparison as rpc
    REF = ref()
    tax_path = REF / "parking_reform_taxonomy.csv"
    tax = pd.read_csv(tax_path, dtype=str)
    if tax["prn_key"].str.startswith("dose drop-from-pools:").any():
        raise SystemExit("taxonomy already augmented")
    names = bps_names(cmp.panel(rpc.read_bps_us()))
    rows, log = [], []
    for u in drop_list().itertuples():
        k, status = find_key(names, u.state, u.place)
        log.append(dict(reform_id=u.reform_id, place=u.place, state=u.state, key=k, match=status))
        if k is None:
            continue
        n = names.set_index("key").loc[k]
        rows.append(dict(prn_key=f"dose drop-from-pools: {u.reform_id}", place=n["name"], state=u.state, place_type="city",
                         population=n["pop"], policy="rm_min", status="adopted", benchmark_rating="at",
                         rating_reason="dose plan C5 check: partial reform left out of every pool"))
    pd.concat([tax, pd.DataFrame(rows)], ignore_index=True).to_csv(tax_path, index=False)
    pd.DataFrame(log).to_csv(REF / "dose_droppools_list.csv", index=False)
    print(pd.DataFrame(log).to_string(index=False))


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--parts", default="match,effects,standins,event,shift")
    ap.add_argument("--augment-taxonomy", action="store_true")
    a = ap.parse_args()
    wc = os.environ.get("MM_REFERENCE_DIR")
    if not wc or Path(wc).resolve() == (ROOT / "reference").resolve():
        raise SystemExit("run on a dose working copy (scripts/run_parking_dose.sh)")
    dc.require_frozen_doses()  # audit fix 6: no effect before the doses are frozen
    if a.augment_taxonomy:
        augment_taxonomy()
        return
    parts = a.parts.split(",")
    C = Ctx(need_d=bool({"effects", "event", "shift"} & set(parts)))
    if "match" in parts:
        part_match(C)
    pools = part_effects(C) if "effects" in parts else None
    if "standins" in parts:
        part_standins(C)
    if "event" in parts:
        part_event(C, pools)
    if "shift" in parts:
        part_shift(C)


if __name__ == "__main__":
    main()
