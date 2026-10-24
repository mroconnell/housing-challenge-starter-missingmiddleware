"""More measured Wisconsin places, and do the coded local rules predict activity? (Gate 3)

Owner question (2026-10-24): can the coded local ADU rules (reference/wi_rights_exposure.csv and
wi_adu_rules.csv) predict whether a place is active, middle or restrictive under the state-relative
grouping rule v1 / v1.1 (`comparison.ca_regression.state_relative_groups`)?

Pieces:
* `place_years`: one row per place and calendar year 2022-2025 with second-home units (AQ-032:
  ADUs plus single-family-to-duplex conversions plus second dwellings on lots that already had a
  home), the unconfirmed upper bound, coverage (months of records) and stage. Sources:
    - the four earlier pilots from their reference tables (Madison, Pleasant Prairie, Sun Prairie,
      Fitchburg), unchanged;
    - Milwaukee from the open permit data with the Gate 3 candidate rule
      (`model.baseline.milwaukee_candidates`, central = counted, upper = upper bound);
    - one `wimc_<slug>` adapter module per newly measured place (fetch / load / coverage /
      classify_records, see each module's docstring). Every counted record and near-hit is judged
      in the module (`JUDGMENTS`); records judged "unconfirmed" form the upper bound (1 unit each).
* `measured_table`: place-level permits, years observed, homes (ACS 2020-2024 one-unit detached,
  summed over county pieces), rate per 1,000 homes per year, stage, quality.
* `coded_rules`: ordinance status, rights class, restriction flags and tiers per coded place, both
  as currently coded and as in force for most of 2022-2025 (`WINDOW_RULES`, from the dated rows of
  wi_adu_rules.csv). Places outside the 37 coded ones carry provisional rules (`PROVISIONAL_RULES`,
  source leads gathered while measuring) used only in a labelled sensitivity.
* `groups`, `crosstabs`, `rank_correlations`: rule v1 and v1.1 groups and the rules-vs-activity
  tests. Every number carries its unit, numerator and denominator in the output tables.
"""
from __future__ import annotations

import importlib
from pathlib import Path

import numpy as np
import pandas as pd

from ..contracts import POISON_PILL_FLAGS, SECONDARY_FLAGS

YEARS = (2022, 2023, 2024, 2025)
ADAPTERS = ("howard", "de_pere", "neenah", "green_bay", "kaukauna", "verona", "watertown", "waunakee")

# Quality grades (A: descriptions + type/units + lot check; B: descriptions or type, no lot check;
# C: flags only / sparse text / structural gaps). Per place, from the adapter reviews.
QUALITY = {
    "madison": ("A", "assessor parcel rule + text rule + judgments (Gate 2 pipeline)"),
    "pleasant_prairie": ("A", "parcel-history rule + text rule + judgments (Gate 2 pipeline)"),
    "sun_prairie": ("A", "parcel-history rule + text rule + judgments (Gate 2 pipeline); applications"),
    "fitchburg": ("B", "description text rule only; no lot check, duplex conversions without ADU wording missed"),
    "milwaukee": ("C", "open data has no description or unit count: 'Dwelling units impact = Added' residential "
                       "permits matched to MPROP (central rule); unverified candidates"),
    "howard": ("A", "descriptions + trade types + parcel and address history; Oct 2024 read by OCR"),
    "de_pere": ("C", "fixed permit-type names and census codes only, no free text; ADUs filed as remodel or "
                     "addition are invisible (likely undercount since ADUs became legal 2023-01-01)"),
    "neenah": ("A", "descriptions + template + parcel lot checks (2024-2025); 2022-2023 months missing"),
    "green_bay": ("A", "descriptions + type codes + parcel IDs with a 2019 tax-roll lot check; Internet Archive "
                       "copies of the city's reports (live site blocks plain HTTP)"),
    "kaukauna": ("C", "permit system work target 'Additional dwelling unit' only; no free text; some months print "
                      "no work target; 2022 Jan-Feb missing"),
    "verona": ("B", "descriptions + units + parcel in 2022 and 2025; 2023 no parcel; 2024 type/cost only (grade C)"),
    "watertown": ("A", "descriptions + census code + parcel checks; both 2025 ADUs confirmed by CUP staff reports; "
                       "2022 not record-level"),
    "waunakee": ("C", "new-dwelling permits only (no alterations or conversions): attached, conversion and "
                      "duplex-conversion units are structurally invisible"),
}

PILOT_GEOIDS = {
    "madison": ("Madison city", "5502548000", "issued"),
    "pleasant_prairie": ("Pleasant Prairie village", "5505963300", "issued"),
    "sun_prairie": ("Sun Prairie city", "5502578600", "application"),
    "fitchburg": ("Fitchburg city", "5502525950", "issued"),
    "milwaukee": ("Milwaukee city", "5507953000", "issued"),
}

# Holdout places (reference/wi_holdout_coded_places.csv). Never used for fitting; here they enter
# only descriptive cross-tabs, and every test is repeated without them.
def holdout_ids(ref_dir: Path) -> set[str]:
    h = pd.read_csv(ref_dir / "wi_holdout_coded_places.csv", dtype={"jurisdiction_id": str})
    return set(h.loc[h["holdout"].astype(bool), "jurisdiction_id"])


# --------------------------------------------------------------------------- per place-year counts
def _pilot_rows(ref_dir: Path) -> list[dict]:
    rows = []
    mad = pd.read_csv(ref_dir / "madison_adu_permits_by_year.csv")
    for y in YEARS:
        g = mad[mad["year"] == y].set_index("category")["units"]
        rows.append({"slug": "madison", "year": y, "units": int(g.get("second_home_sf_lot", 0)),
                     "upper_units": int(g.get("second_home_sf_lot_upper_bound", g.get("second_home_sf_lot", 0))),
                     "months": 12, "complete": True, "note": "madison_adu_permits_by_year.csv"})
    for slug, f in (("pleasant_prairie", "pleasant_prairie_adu_equivalent_by_year.csv"),
                    ("sun_prairie", "sun_prairie_adu_equivalent_by_year.csv")):
        d = pd.read_csv(ref_dir / f)
        for y in YEARS:
            g = d[d["year"] == y].set_index("series")["units"]
            rows.append({"slug": slug, "year": y, "units": int(g.get("second_home_sf_lot", 0)),
                         "upper_units": int(g.get("second_home_sf_lot_upper_bound", g.get("second_home_sf_lot", 0))),
                         "months": 12, "complete": True, "note": f})
    obs = pd.read_csv(ref_dir / "wi_baseline_observed.csv").set_index("key")
    fb_zero = "fitchburg_2022_2026jul" in obs.index and obs.loc["fitchburg_2022_2026jul", "units"] == 0
    for y in YEARS:
        rows.append({"slug": "fitchburg", "year": y, "units": 0 if fb_zero else np.nan,
                     "upper_units": 0 if fb_zero else np.nan, "months": 12, "complete": bool(fb_zero),
                     "note": "wi_baseline_observed.csv: zero ADU-text hits 2022-01 to 2026-07"})
    return rows


def milwaukee_rows(raw_root: Path) -> list[dict]:
    """Milwaukee 2022-2025 from the open permits + MPROP (same rule as the Gate 3 baseline)."""
    from ..model import baseline as bl

    p = raw_root / "milwaukee_permits" / "buildingpermits.csv"
    if not p.exists():
        return []
    raw = pd.read_csv(p, low_memory=False)
    permits = pd.DataFrame({
        "record_id": raw["Record ID"], "issued": pd.to_datetime(raw["Date Issued"], errors="coerce"),
        "permit_type": raw["Permit Type"].astype(str), "use": raw["Use of Building"],
        "units_impact": raw["Dwelling units impact"], "address": raw["Address"]})
    cols = ["HOUSE_NR_LO", "HOUSE_NR_HI", "SDIR", "STREET", "NR_UNITS", "YR_BUILT"]
    mp = pd.read_csv(raw_root / "milwaukee_mprop" / "mprop.csv", usecols=cols, dtype=str)
    mp.columns = ["house_lo", "house_hi", "sdir", "street", "nr_units", "yr_built"]
    cand = bl.milwaukee_candidates(permits, mp)
    yr = cand["issued"].dt.year
    months = permits.groupby(permits["issued"].dt.year)["issued"].apply(lambda s: s.dt.month.nunique())
    return [{"slug": "milwaukee", "year": y, "units": int(cand.loc[yr == y, "central"].sum()),
             "upper_units": int(cand.loc[yr == y, "upper"].sum()), "months": int(months.get(y, 0)),
             "complete": int(months.get(y, 0)) == 12,
             "note": "open permits (data to 2026-06-15) x MPROP; candidate rule, central/upper"} for y in YEARS]


def adapter_rows(slug: str, raw_root: Path, fetch: bool = False, log=print) -> tuple[list[dict], dict, pd.DataFrame]:
    m = importlib.import_module(f"missing_middleware.permits.wimc_{slug}")
    raw = raw_root / f"wimc_{slug}"
    if fetch:
        m.fetch(raw, log=log)
    df = m.load(raw)
    cov = m.coverage(df).set_index("year")
    c = m.classify_records(df)
    c = c[c["year"].between(YEARS[0], YEARS[-1])]
    counted = c[c["component"].notna()]
    unconf = c[c["candidate"].astype(bool) & c["component"].isna()
               & c["reason"].fillna("").str.contains("unconfirm", case=False)]
    rows = []
    for y in YEARS:
        u = int(counted.loc[counted["year"] == y, "units"].sum())
        rows.append({"slug": slug, "year": y, "units": u,
                     "upper_units": u + int((unconf["year"] == y).sum()),
                     "months": int(cov.loc[y, "months_with_records"]) if y in cov.index else 0,
                     "complete": bool(cov.loc[y, "complete"]) if y in cov.index else False,
                     "note": str(cov.loc[y, "note"]) if y in cov.index else "no records"})
    review = pd.concat([counted.assign(decision="counted"), unconf.assign(decision="unconfirmed_upper_bound")])
    review = review[["year", "permit_type", "component", "units", "reason", "decision"]].assign(slug=slug)
    return rows, m.META, review


def place_years(ref_dir: Path, raw_root: Path, adapters=ADAPTERS, fetch: bool = False,
                log=print) -> tuple[pd.DataFrame, dict, pd.DataFrame]:
    rows = _pilot_rows(ref_dir) + milwaukee_rows(raw_root)
    metas = {s: {"place": p, "geoids": [g], "stage": st} for s, (p, g, st) in PILOT_GEOIDS.items()}
    reviews = []
    for s in adapters:
        if not (raw_root / f"wimc_{s}").exists() and not fetch:
            log(f"  {s}: no raw data (run with --fetch)")
            continue
        r, meta, rev = adapter_rows(s, raw_root, fetch=fetch, log=log)
        rows += r
        metas[s] = meta
        reviews.append(rev)
    py = pd.DataFrame(rows)
    py["place"] = py["slug"].map(lambda s: metas[s]["place"])
    py["stage"] = py["slug"].map(lambda s: metas[s]["stage"])
    rev = pd.concat(reviews, ignore_index=True) if reviews else pd.DataFrame()
    return py, metas, rev


# --------------------------------------------------------------------------- homes and market
def homes_by_place(ref_dir: Path, metas: dict) -> pd.DataFrame:
    """ACS 2020-2024 one-unit detached homes summed over the place's county-subdivision pieces;
    the place key (GEOID) is its largest piece."""
    mun = pd.read_csv(ref_dir / "wi_baseline_by_municipality.csv", dtype={"geoid": str})
    h = mun.set_index("geoid")["homes"]
    out = []
    for s, m in metas.items():
        g = [x for x in m["geoids"] if x in h.index]
        if m["place"].startswith("Milwaukee"):  # Milwaukee pieces in other counties
            g = mun.loc[mun["name"].str.startswith("Milwaukee city"), "geoid"].tolist()
        key = max(g, key=lambda x: h[x]) if g else m["geoids"][0]
        out.append({"slug": s, "geoid": key, "pieces": ";".join(sorted(g)), "homes": float(h[g].sum()) if g else np.nan})
    return pd.DataFrame(out)


def market_values(geoids: pd.Series, raw_root: Path) -> pd.DataFrame:
    """ACS 2020-2024 median home value (B25077) and household income (B19013) per county subdivision."""
    from ..comparison import ca_regression as cr

    folder = raw_root / "census_acs5_2024_tbsf_market"
    paths = {t: folder / f"acsdt5y2024-{t}.dat" for t in ("b25077", "b19013", "b25064", "b25003")}
    if not all(p.exists() for p in paths.values()):
        return pd.DataFrame({"geoid": geoids, "value": np.nan, "income": np.nan})
    mk = cr.read_market(paths, "55", ("060",)).set_index("geoid")
    return pd.DataFrame({"geoid": geoids.values, "value": geoids.map(mk["value"]).values,
                         "income": geoids.map(mk["income"]).values})


# --------------------------------------------------------------------------- measured table
def measured_table(py: pd.DataFrame, homes: pd.DataFrame, quality=QUALITY) -> pd.DataFrame:
    rows = []
    for s, g in py.groupby("slug", sort=False):
        full = g[g["complete"].astype(bool) & g["units"].notna()]
        part = g[~g["complete"].astype(bool) & g["months"].gt(0)]
        rows.append({
            "slug": s, "place": g["place"].iloc[0], "stage": g["stage"].iloc[0],
            "permits": float(full["units"].sum()), "permits_upper": float(full["upper_units"].sum()),
            "years_observed": float(len(full)),
            "complete_years": ";".join(str(y) for y in full["year"]),
            "partial_months_not_used": ";".join(f"{y}:{m}" for y, m in zip(part["year"], part["months"])),
            "quality": quality.get(s, ("?", ""))[0], "quality_note": quality.get(s, ("?", ""))[1]})
    t = pd.DataFrame(rows).merge(homes, on="slug", how="left")
    t["measured_full_window"] = t["years_observed"].eq(len(YEARS))
    hy = t["years_observed"] * t["homes"] / 1000
    t["thousand_home_years"] = hy
    t["rate_per_1000_homes_yr"] = np.where(hy > 0, t["permits"] / hy, np.nan)
    t["rate_upper_per_1000_homes_yr"] = np.where(hy > 0, t["permits_upper"] / hy, np.nan)
    lo, hi = zip(*[poisson_ci(k) for k in t["permits"].fillna(0)])
    t["rate_poisson95_lo"] = np.where(hy > 0, np.array(lo) / hy, np.nan)
    t["rate_poisson95_hi"] = np.where(hy > 0, np.array(hi) / hy, np.nan)
    return t


def poisson_ci(k: float, z: float = 1.959964) -> tuple[float, float]:
    """Exact (Garwood) 95% interval for a Poisson count via the chi-square/gamma link,
    computed with a bisection on the regularized gamma (no scipy)."""
    from math import exp, lgamma, log

    def gammainc_upper_q(a: float, x: float) -> float:  # P(X >= k) for Poisson mean x equals P(a=k, x)
        # regularized lower gamma P(a, x) by series
        if x <= 0:
            return 0.0
        s, term, n = 1.0 / a, 1.0 / a, 0
        while n < 10000:
            n += 1
            term *= x / (a + n)
            s += term
            if term < s * 1e-14:
                break
        return exp(-x + a * log(x) - lgamma(a)) * s

    def solve(f, target):
        lo_, hi_ = 0.0, max(10.0, 10 * (k + 10))
        for _ in range(200):
            mid = (lo_ + hi_) / 2
            if f(mid) < target:
                lo_ = mid
            else:
                hi_ = mid
        return (lo_ + hi_) / 2

    k = int(round(k))
    lower = 0.0 if k == 0 else solve(lambda mu: gammainc_upper_q(k, mu), 0.025)
    upper = solve(lambda mu: gammainc_upper_q(k + 1, mu), 0.975)
    return lower, upper


# --------------------------------------------------------------------------- coded rules
# Rules in force for most of 2022-2025 where they differ from the current coding (dated rows of
# reference/wi_adu_rules.csv). Flags are judged against the AQ-026 benchmark like the current coding.
WINDOW_RULES = {
    "Madison city": ("restricted", "owner_occupancy",
                     "ongoing owner occupancy to 2024-04-25 (28 of 48 months); benchmark after (rule wi5502548000 owner_occupancy rows)"),
    "Milwaukee city": ("prohibited_implicit", "",
                       "ADUs not a defined use and second principal buildings barred in RS until 2025-08-01 (43 of 48 months); "
                       "RT districts allowed a second unit as a two-family dwelling"),
    "Sun Prairie city": ("prohibited_implicit", "", "no ADU text, accessory uses barred as residences until Ord. 984 (2026-05-08)"),
    "Fitchburg city": ("restricted", "form_limited;discretionary_review;owner_occupancy",
                       "attached owner-occupied dependency unit by conditional use until 2025-09-09 (44 of 48 months)"),
    "De Pere city": ("restricted", "owner_occupancy;size_below_benchmark",
                     "ADUs allowed from 2023-01-01 (36 of 48 months); prohibited in 2022"),
    "Green Bay city": ("restricted", "discretionary_review",
                       "detached ADU by conditional use before 2025-12-02 (rule wi5500931000 detached_allowed_1)"),
}
# Places outside the 37 coded ones: provisional rules from the measuring workers' source leads
# (not in wi_adu_rules.csv; sensitivity only). (ordinance_status, current_class, flags, window_class, window_flags, note)
PROVISIONAL_RULES = {
    "Verona city": ("mentioned_allowed", "restricted", "owner_occupancy;extra_parking;size_below_benchmark",
                    "restricted", "owner_occupancy;extra_parking;size_below_benchmark",
                    "by right since 2021 (Ord. 21-980), owner occupancy, one extra parking space, cap 900 sq ft or 50% of house; "
                    "source lead veronawi.gov AgendaCenter Item 129 fileID 2990"),
    "Watertown city": ("mentioned_allowed", "restricted", "discretionary_review;owner_occupancy",
                       "restricted", "discretionary_review;owner_occupancy",
                       "conditional use in SR-4 (s.550-24C(2)(b), s.550-56AA), owner occupancy; source lead (Plan Commission attachment)"),
    "Waunakee village": ("mentioned_allowed", "restricted", "size_below_benchmark;district_limited",
                         "prohibited_implicit", "",
                         "prohibited until the 2024-05-06 amendment (28 of 48 months); by right after, cap 900 sq ft, HOA/joint-planning "
                         "areas excluded (about 29% of single-family lots eligible); source lead (news report)"),
    "Kaukauna city": ("unmentioned", "prohibited_implicit", "", "prohibited_implicit", "",
                      "no ADU provision in Ch. 17 per Gate 2 search, but the city issued 7 'Additional dwelling unit' permits 2023-2025: "
                      "rules coding needs re-checking"),
}

PROHIBITED = ("prohibited_explicit", "prohibited_implicit")


def strictness(cls: str, flags: str) -> int:
    """Ordinal rule strictness: 0 benchmark; 1 restricted by tier-2 limits only; 2 restricted with a tier-1
    flag; 3 prohibited (explicit or implicit). Unknown -> NaN."""
    f = [x for x in str(flags or "").split(";") if x]
    if cls == "scenario_benchmark":
        return 0
    if cls == "restricted":
        return 2 if any(x in POISON_PILL_FLAGS for x in f) else 1
    if cls in PROHIBITED:
        return 3
    return np.nan


def _flag_counts(flags: str) -> tuple[int, int, int]:
    f = [x for x in str(flags or "").split(";") if x and x != "nan"]
    return len(f), sum(x in POISON_PILL_FLAGS for x in f), sum(x in SECONDARY_FLAGS for x in f)


def coded_rules(ref_dir: Path) -> pd.DataFrame:
    rx = pd.read_csv(ref_dir / "wi_rights_exposure.csv", dtype={"jurisdiction_id": str})
    rx = rx[(rx["scenario_id"] == "adu_full") & ~rx["jurisdiction_name"].str.contains(r"\(part", regex=True)]
    rules = pd.read_csv(ref_dir / "wi_adu_rules.csv", dtype={"jurisdiction_id": str})
    st = rules[rules["provision"] == "ordinance_status"].set_index("jurisdiction_id")["value"]
    out = rx[["jurisdiction_id", "jurisdiction_name", "current_class", "class_basis", "restrictions"]].copy()
    out["restrictions"] = out["restrictions"].fillna("")
    out["ordinance_status"] = out["jurisdiction_id"].map(st)
    out["rules_source"] = "coded (wi_rights_exposure.csv adu_full; wi_adu_rules.csv)"
    w = out["jurisdiction_name"].map(WINDOW_RULES)
    out["window_class"] = [x[0] if isinstance(x, tuple) else c for x, c in zip(w, out["current_class"])]
    out["window_flags"] = [x[1] if isinstance(x, tuple) else f for x, f in zip(w, out["restrictions"])]
    out["window_note"] = [x[2] if isinstance(x, tuple) else "same as current coding" for x in w]
    prov = pd.DataFrame([{"jurisdiction_id": "", "jurisdiction_name": k, "ordinance_status": v[0], "current_class": v[1],
                          "restrictions": v[2], "window_class": v[3], "window_flags": v[4], "window_note": v[5],
                          "class_basis": "provisional_source_lead", "rules_source": "provisional (not in wi_adu_rules.csv)"}
                         for k, v in PROVISIONAL_RULES.items()])
    out = pd.concat([out, prov], ignore_index=True)
    for pre, cls, fl in (("", "current_class", "restrictions"), ("window_", "window_class", "window_flags")):
        cnt = out[fl].map(_flag_counts)
        out[f"{pre}n_flags"] = [c[0] for c in cnt]
        out[f"{pre}n_tier1"] = [c[1] for c in cnt]
        out[f"{pre}n_tier2"] = [c[2] for c in cnt]
        out[f"{pre}strictness"] = [strictness(c, f) for c, f in zip(out[cls], out[fl])]
        out[f"{pre}rights_group"] = out[cls].map(lambda c: "prohibited" if c in PROHIBITED else c)
        out[f"{pre}tier"] = [("none (prohibited)" if c in PROHIBITED else "none (benchmark)" if c == "scenario_benchmark"
                              else "tier-1 flag" if t1 else "tier-2 only") for c, t1 in zip(out[cls], out[f"{pre}n_tier1"])]
    return out


# --------------------------------------------------------------------------- groups and tests
def groups(meas: pd.DataFrame, measured_col: str = "measured_full_window") -> pd.DataFrame:
    from ..comparison.ca_regression import state_relative_groups

    o = meas.rename(columns={"years_observed": "years"}).assign(
        jurisdiction=meas["geoid"], measured=meas[measured_col]).copy()
    o["years"] = o["years"].where(o["years"] > 0, np.nan)
    v1 = state_relative_groups(o[["jurisdiction", "permits", "years", "homes", "measured"]].fillna({"permits": 0}))
    v11 = state_relative_groups(o[["jurisdiction", "permits", "years", "homes", "measured"]].fillna({"permits": 0}),
                                min_measured=20)
    out = meas.copy()
    out["group_v1"], out["cutoff_v1"] = v1["group"].values, v1["cutoff"].values
    out["group_v1_1"] = v11["group"].values
    out["n_measured_for_rule"] = int(o["measured"].astype(bool).sum())
    return out


def spearman(x: pd.Series, y: pd.Series, n_perm: int = 20000, seed: int = 20261024) -> dict:
    """Spearman rank correlation (average ranks for ties) with a two-sided permutation p-value."""
    d = pd.DataFrame({"x": x, "y": y}).dropna()
    n = len(d)
    if n < 3 or d["x"].nunique() < 2 or d["y"].nunique() < 2:
        return {"n": n, "rho": np.nan, "p_perm": np.nan}
    rx, ry = d["x"].rank().to_numpy(), d["y"].rank().to_numpy()
    rho = float(np.corrcoef(rx, ry)[0, 1])
    rng = np.random.default_rng(seed)
    perm = np.array([np.corrcoef(rx, rng.permutation(ry))[0, 1] for _ in range(n_perm)])
    p = float((np.abs(perm) >= abs(rho) - 1e-12).mean())
    return {"n": n, "rho": rho, "p_perm": p}


def crosstab_long(df: pd.DataFrame, rule_col: str, group_col: str, sample: str) -> pd.DataFrame:
    t = pd.crosstab(df[rule_col].fillna("missing"), df[group_col])
    rows = []
    for r in t.index:
        for g in t.columns:
            rows.append({"sample": sample, "rule_variable": rule_col, "rule_value": r, "grouping": group_col,
                         "group": g, "places": int(t.loc[r, g]), "places_with_rule_value": int(t.loc[r].sum()),
                         "unit": "count of measured places (numerator) out of places with this rule value (denominator)"})
    return pd.DataFrame(rows)


def rate_by_rule(df: pd.DataFrame, rule_col: str, sample: str) -> pd.DataFrame:
    """Pooled rate per rule value: sum of permits / sum of thousand home-years."""
    rows = []
    for v, g in df.groupby(df[rule_col].fillna("missing")):
        k, hy = g["permits"].sum(), g["thousand_home_years"].sum()
        lo, hi = poisson_ci(k)
        rows.append({"sample": sample, "rule_variable": rule_col, "rule_value": v, "places": len(g),
                     "places_list": "; ".join(g["place"]), "permits": k, "thousand_home_years": round(hy, 3),
                     "pooled_rate_per_1000_homes_yr": k / hy if hy else np.nan,
                     "pooled_rate_poisson95_lo": lo / hy if hy else np.nan,
                     "pooled_rate_poisson95_hi": hi / hy if hy else np.nan,
                     "unit": "second-home permits (numerator) per 1,000 one-unit detached homes per year "
                             "(denominator: sum over places of homes x complete years / 1,000)"})
    return pd.DataFrame(rows)
