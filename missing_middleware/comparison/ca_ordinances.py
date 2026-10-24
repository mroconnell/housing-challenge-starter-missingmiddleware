"""California local ADU rules as they stood before 2020, and whether they predict ADU activity.

Owner idea (2026-10-24): test whether coded local ADU rules predict ADU activity in California,
where many places have measured permits, so that rule codings might assign activity groups to
unmeasured Wisconsin places.

Three existing pre-2020 coded sources are read (all public, plain HTTP):

* **Terner California Residential Land Use Survey (TCRLUS)**, Mawhorter and Reid (2018). Planner
  self-reports, August 2017 to October 2018, 271 jurisdictions. ADU fields: ordinance status, minimum
  lot size, maximum unit size, off-street parking spaces, total fees.
* **CCI ADU Scorecard, interim report (2020-02-01)**, Chapple et al., UC Berkeley Center for Community
  Innovation. Letter grades for the ordinances received by HCD by 2019-09-06 (pre-2020 rules), from a
  16-criterion rubric. Only the composite grade is public; per-criterion scores are not.
* **HCD "ADU ordinances received by HCD" list**, current as of 2019-05-01 (Wayback capture 2019-08-31):
  whether each jurisdiction had filed a post-2017 ADU ordinance with HCD, and its date.

A fourth source is the team's own AQ-026 coding of a sample of jurisdictions from archived 2017-2019
ordinance text (``reference/ca_ordinances_2019.csv``), each row with its source URL and date.

Everything here is a pure function of data frames or text so the tests run offline. Results are
associations across California places; they are not causal effects of rules.
"""
from __future__ import annotations

import re
import xml.etree.ElementTree as ET
import zipfile
from pathlib import Path

import numpy as np
import pandas as pd

BENCHMARK_SQFT = 600          # AQ-026: a size cap below 600 sq ft is a restriction
HIGH_FEE_USD = 10_000         # TCRLUS "total fees for a typical ADU" at or above this = fee flag (stated cut)
TIER1 = ("owner_occupancy", "related_occupant", "extra_parking", "discretionary_review", "form_limited")
TIER2 = ("size_below_benchmark", "siting", "lot_minimum", "district_limited", "fees")
FLAGS = TIER1 + TIER2
GRADE_POINTS = {"A": 12, "A-": 11, "B+": 10, "B": 9, "B-": 8, "C+": 7, "C": 6, "C-": 5, "D+": 4, "D": 3,
                "D-": 2, "F": 1}
# TCRLUS missing codes (codebook): -99 seen not answered, -98 varies, -97 N/A/blank/zero, -96 inconsistent.
TCRLUS_MISSING = {-99: "not_answered", -98: "varies", -97: "na_blank_or_zero", -96: "inconsistent"}

# ---------------------------------------------------------------------------
# Names
# ---------------------------------------------------------------------------

NAME_ALIASES = {"SAN BUENAVENTURA": "VENTURA", "RANCHO ST MARGARITA": "RANCHO SANTA MARGARITA"}


def norm_name(name: str) -> str:
    """Normalize a jurisdiction name to the HCD/crosswalk style (upper case, 'X COUNTY' for
    unincorporated areas, 'update' suffixes and punctuation removed)."""
    s = str(name).upper().strip()
    s = re.sub(r"\s+UNINCORPORATED$", "", s)
    s = re.sub(r"\(.*?\)", " ", s)
    s = re.sub(r"\s+-.*$", "", s)
    s = re.sub(r"\s+(UPDATE|UPDATED|AMENDED|AMENDMENT|ADU|JADU|EXCEPTIONS|FEES|TAX EXEMPT)\b.*$", "", s)
    s = re.sub(r",\s*CITY$", "", s)
    s = re.sub(r"^CITY OF\s+", "", s)
    s = s.replace(".", "").replace("’", "'")
    s = re.sub(r"\s+CO$", " COUNTY", s.strip())
    s = re.sub(r"\s+", " ", s).strip()
    return NAME_ALIASES.get(s, s)


def attach_geoid(df: pd.DataFrame, crosswalk: pd.DataFrame, name_col: str = "juris_name") -> pd.DataFrame:
    """Add census_geoid by exact normalized name against the HCD crosswalk (juris_name)."""
    xw = crosswalk[["juris_name", "census_geoid"]].copy()
    xw["_key"] = xw["juris_name"].map(norm_name)
    out = df.copy()
    out["_key"] = out[name_col].map(norm_name)
    out = out.merge(xw[["_key", "census_geoid"]].drop_duplicates("_key"), on="_key", how="left")
    return out.drop(columns="_key")

# ---------------------------------------------------------------------------
# Source 1: CCI ADU Scorecard (interim report, 2020-02-01), Appendix C
# ---------------------------------------------------------------------------


def parse_scorecard_table(text: str) -> pd.DataFrame:
    """Parse Appendix C ('Table 3. Grades') of the interim report from its markdown text.

    Rows look like ``| ALAMEDA | B | 0 | 2018 | http://...pdf |``. '--' grade = no ordinance received
    (not graded); '-' = missing. Returns juris_name, grade, grade_points, adus_2018, year_adopted, link.
    """
    start = text.find("Appendix C")
    body = text[start:] if start >= 0 else text
    rows = []
    for line in body.splitlines():
        if not line.startswith("| ") or line.startswith("| Jurisdiction") or line.startswith("| ---"):
            continue
        cells = [c.strip() for c in line.strip().strip("|").split("|")]
        if len(cells) != 5:
            continue
        name, grade, adus, year, link = cells
        g = grade if grade in GRADE_POINTS else None
        rows.append({
            "juris_name": name,
            "cci_grade": g,
            "cci_graded": g is not None,
            "cci_grade_points": GRADE_POINTS.get(grade, np.nan),
            "cci_adus_2018": pd.to_numeric(adus, errors="coerce"),
            "cci_year_adopted": pd.to_numeric(year, errors="coerce"),
            "cci_ordinance_link": link if link.startswith("http") else None,
        })
    return pd.DataFrame(rows).drop_duplicates("juris_name")

# ---------------------------------------------------------------------------
# Source 2: HCD list of ADU ordinances received (xlsx), read with the standard library
# ---------------------------------------------------------------------------

_NS = {"m": "http://schemas.openxmlformats.org/spreadsheetml/2006/main"}


def read_xlsx_rows(path: Path) -> list[list[str]]:
    """Read the first worksheet of an .xlsx file into a list of string rows (stdlib only)."""
    z = zipfile.ZipFile(path)
    shared = []
    if "xl/sharedStrings.xml" in z.namelist():
        for si in ET.fromstring(z.read("xl/sharedStrings.xml")).findall("m:si", _NS):
            shared.append("".join(t.text or "" for t in si.iter("{%s}t" % _NS["m"])))
    sheets = sorted(n for n in z.namelist() if re.match(r"xl/worksheets/sheet\d+\.xml$", n))
    root = ET.fromstring(z.read(sheets[0]))
    out = []
    for row in root.iter("{%s}row" % _NS["m"]):
        vals = []
        for c in row.findall("m:c", _NS):
            v = c.find("m:v", _NS)
            if v is None:
                inline = c.find("m:is", _NS)
                vals.append("".join(x.text or "" for x in inline.iter("{%s}t" % _NS["m"])) if inline is not None else "")
            else:
                vals.append(shared[int(v.text)] if c.get("t") == "s" else (v.text or ""))
        out.append(vals)
    return out


def _date_from_link(link: str) -> str | None:
    m = re.search(r"(\d{1,2})-(\d{1,2})-(\d{2,4})", link or "")
    if not m:
        return None
    mo, d, y = (int(x) for x in m.groups())
    y = y + 2000 if y < 100 else y
    if not (1 <= mo <= 12 and 1 <= d <= 31 and 2010 <= y <= 2020):
        return None
    return f"{y:04d}-{mo:02d}-{d:02d}"


def parse_hcd_received(rows: list[list[str]]) -> tuple[pd.DataFrame, str | None]:
    """Parse HCD's 'ADU ordinances received by HCD' list. Returns one row per jurisdiction with
    received (bool), the latest ordinance link and its date (from the file name), plus the
    'current as of' text."""
    as_of = None
    recs = []
    for r in rows:
        if not r:
            continue
        if "current as of" in r[0].lower():
            as_of = r[0].split("as of:")[-1].strip() if "as of:" in r[0] else r[0]
            continue
        if len(r) < 2 or r[0].strip().lower() in ("jurisdiction", "") or "RECEIVED" not in r[1].upper():
            continue
        link = r[2].strip() if len(r) > 2 else ""
        recs.append({"juris_name_raw": r[0].strip(), "juris_name": norm_name(r[0]),
                     "hcd_received": r[1].strip().upper() == "RECEIVED BY HCD",
                     "hcd_link": link or None, "hcd_ordinance_date": _date_from_link(link)})
    df = pd.DataFrame(recs)
    agg = (df.sort_values("hcd_ordinance_date", na_position="first")
             .groupby("juris_name", as_index=False)
             .agg(hcd_received=("hcd_received", "max"), hcd_link=("hcd_link", "last"),
                  hcd_ordinance_date=("hcd_ordinance_date", "last"), hcd_n_filings=("hcd_link", "count")))
    return agg, as_of

# ---------------------------------------------------------------------------
# Source 3: Terner California Residential Land Use Survey (2017-2018)
# ---------------------------------------------------------------------------


def tcrlus_codes(d: pd.DataFrame) -> pd.DataFrame:
    """Map TCRLUS ADU answers to AQ-026 ordinance status and the restriction flags it can see.

    Flags are True / False / NA (missing never becomes False):
    * lot_minimum: minimum lot size for ADUs > 0 sq ft (True); -97 (N/A, blank or zero) -> False.
    * size_below_benchmark: maximum ADU size < 600 sq ft.
    * extra_parking: off-street parking for the ADU > 0 spaces; -97 -> False (zero or blank).
    * fees: total fees for a typical ADU >= $10,000 (stated cut; includes building-permit fees,
      so this is a cost proxy, not the AQ-026 ADU-specific-fee flag).
    Owner occupancy, related occupant, discretionary review and form are not asked.
    """
    out = pd.DataFrame({"juris_name": d["city"].map(norm_name)})
    status = d["adu_ordinance"].map({0: "no_local_ordinance", 1: "in_process", 2: "adopted"})
    out["tcrlus_ordinance"] = status
    out["tcrlus_type"] = d["type"].map({0: "city", 1: "county"})

    def num(col):
        v = pd.to_numeric(d[col], errors="coerce")
        return v

    lot, size, park, fee = num("adu_minlotsize"), num("adu_maxunitsize"), num("adu_offstpark"), num("adu_fees")
    out["tcrlus_minlot_sqft"] = lot.where(lot >= 0)
    out["tcrlus_maxsize_sqft"] = size.where(size >= 0)
    out["tcrlus_parking_spaces"] = park.where(park >= 0)
    out["tcrlus_fees_usd"] = fee.where(fee >= 0)

    def flag(val, cond, zero_code_false=True):
        f = pd.Series(pd.NA, index=val.index, dtype="boolean")
        ok = val >= 0
        f[ok] = cond(val[ok])
        if zero_code_false:
            f[val == -97] = False
        return f

    out["lot_minimum"] = flag(lot, lambda v: v > 0)
    out["size_below_benchmark"] = flag(size, lambda v: v < BENCHMARK_SQFT, zero_code_false=False)
    out["extra_parking"] = flag(park, lambda v: v > 0)
    out["fees"] = flag(fee, lambda v: v >= HIGH_FEE_USD)
    out["tcrlus_apl_adu"] = d.get("apl_adu")
    out["tcrlus_recorded"] = d.get("recordeddate")
    return out

# ---------------------------------------------------------------------------
# Source 4: hand coding (reference/ca_ordinances_2019.csv)
# ---------------------------------------------------------------------------

HAND_COLUMNS = ("census_geoid", "juris_name", "ordinance_status", "rights_class", *FLAGS, "approval_pathway",
                "max_size_sqft", "parking_spaces", "min_lot_sqft", "rules_as_of", "source_type", "source_url",
                "snapshot_date", "evidence", "coder_notes", "confidence")


def read_hand_coding(path: Path) -> pd.DataFrame:
    """Read hand-coded AQ-026 rows; flags as nullable booleans ('' or 'unknown' -> NA)."""
    h = pd.read_csv(path, dtype=str, keep_default_na=False)
    for f in FLAGS:
        h[f] = h[f].str.lower().map({"true": True, "false": False}).astype("boolean")
    return h


def flag_counts(df: pd.DataFrame, flags=FLAGS) -> pd.DataFrame:
    """Count known True flags by tier, and how many flags are unknown."""
    present = [f for f in flags if f in df.columns]
    t1 = [f for f in TIER1 if f in present]
    t2 = [f for f in TIER2 if f in present]
    out = pd.DataFrame(index=df.index)
    out["n_tier1"] = df[t1].fillna(False).astype(int).sum(axis=1) if t1 else np.nan
    out["n_tier2"] = df[t2].fillna(False).astype(int).sum(axis=1) if t2 else np.nan
    out["n_flags"] = out["n_tier1"] + out["n_tier2"]
    out["n_unknown"] = df[present].isna().sum(axis=1)
    return out

# ---------------------------------------------------------------------------
# Analysis helpers
# ---------------------------------------------------------------------------


def spearman(x: pd.Series, y: pd.Series) -> tuple[float, int]:
    """Spearman rank correlation (average ranks for ties) over pairs where both are present."""
    m = x.notna() & y.notna()
    if m.sum() < 3:
        return np.nan, int(m.sum())
    rx = x[m].astype(float).rank()
    ry = y[m].astype(float).rank()
    if rx.std() == 0 or ry.std() == 0:
        return np.nan, int(m.sum())
    return float(np.corrcoef(rx, ry)[0, 1]), int(m.sum())


def spearman_ci(x: pd.Series, y: pd.Series, n_boot: int = 2000, seed: int = 20261024) -> tuple[float, float]:
    """Percentile bootstrap 95% interval for the Spearman correlation (resampling places)."""
    m = x.notna() & y.notna()
    xv, yv = x[m].to_numpy(float), y[m].to_numpy(float)
    n = len(xv)
    if n < 8:
        return np.nan, np.nan
    rng = np.random.default_rng(seed)
    vals = []
    for _ in range(n_boot):
        i = rng.integers(0, n, n)
        r, _ = spearman(pd.Series(xv[i]), pd.Series(yv[i]))
        if not np.isnan(r):
            vals.append(r)
    return float(np.percentile(vals, 2.5)), float(np.percentile(vals, 97.5))


def group_crosstab(df: pd.DataFrame, by: str, group_col: str = "group") -> pd.DataFrame:
    """Counts of places by predictor level x 2017-2019 activity group, with pooled rates.

    Pooled rates are homes-weighted: permits / (homes x years) x 1,000.
    """
    rows = []
    for lvl, g in df.groupby(by, dropna=False):
        r = {"predictor": by, "level": "missing" if pd.isna(lvl) else str(lvl), "n_places": len(g)}
        for grp in ("active", "middle", "restrictive"):
            r[f"n_{grp}"] = int((g[group_col] == grp).sum())
        r["share_active"] = r["n_active"] / len(g) if len(g) else np.nan
        r["share_restrictive"] = r["n_restrictive"] / len(g) if len(g) else np.nan
        r["homes"] = float(g["homes"].sum())
        r["pre_permits"] = float(g["pre_permits"].sum())
        r["pre_home_years"] = float((g["homes"] * 3).sum())
        r["pre_rate_pooled"] = 1000 * r["pre_permits"] / r["pre_home_years"] if r["pre_home_years"] else np.nan
        r["plateau_permits"] = float(g["adu"].sum())
        r["plateau_home_years"] = float((g["homes"] * g["n_years"]).sum())
        r["plateau_rate_pooled"] = 1000 * r["plateau_permits"] / r["plateau_home_years"] if r["plateau_home_years"] else np.nan
        r["pre_rate_median"] = float(g["pre_rate"].median())
        r["plateau_rate_median"] = float(g["rate"].median())
        rows.append(r)
    return pd.DataFrame(rows)


def ordered_logit_free_auc(score: pd.Series, active: pd.Series) -> tuple[float, int, int]:
    """Area under the ROC curve for a score separating active (True) from not-active places.
    Ties count one half. Returns (auc, n_pos, n_neg)."""
    m = score.notna() & active.notna()
    s, a = score[m].astype(float), active[m].astype(bool)
    pos, neg = s[a].to_numpy(), s[~a].to_numpy()
    if len(pos) == 0 or len(neg) == 0:
        return np.nan, len(pos), len(neg)
    gt = (pos[:, None] > neg[None, :]).sum()
    eq = (pos[:, None] == neg[None, :]).sum()
    return float((gt + 0.5 * eq) / (len(pos) * len(neg))), len(pos), len(neg)


def fit_poisson(X: np.ndarray, y: np.ndarray, exposure: np.ndarray, maxit: int = 100, tol: float = 1e-10) -> np.ndarray:
    """Poisson regression with log(exposure) offset by IRLS (same form as ca_regression)."""
    beta = np.zeros(X.shape[1])
    beta[0] = np.log(max(y.sum(), 0.5) / exposure.sum())
    off = np.log(exposure)
    for _ in range(maxit):
        eta = X @ beta + off
        mu = np.exp(eta)
        W = mu
        z = eta - off + (y - mu) / mu
        XtW = X.T * W
        new = np.linalg.solve(XtW @ X + 1e-9 * np.eye(X.shape[1]), XtW @ z)
        if np.max(np.abs(new - beta)) < tol:
            beta = new
            break
        beta = new
    return beta


def poisson_deviance(y: np.ndarray, mu: np.ndarray) -> float:
    with np.errstate(divide="ignore", invalid="ignore"):
        t = np.where(y > 0, y * np.log(y / mu), 0.0)
    return float(2 * np.sum(t - (y - mu)))

# ---------------------------------------------------------------------------
# Assembly and tests of association
# ---------------------------------------------------------------------------

PRE_YEARS = 3                  # 2017-2019, the study's wave-3 pre-period (complete years required)
LA_GEOID = "0644000"
HAND_SAMPLE_SEED = 20261024
# Strata quota for the hand-coded sample (activity group x home-value tercile among non-holdout places).
HAND_QUOTA = {("active", "low"): 7, ("middle", "low"): 10, ("restrictive", "low"): 12,
              ("active", "mid"): 10, ("middle", "mid"): 10, ("restrictive", "mid"): 9,
              ("active", "high"): 6, ("middle", "high"): 5, ("restrictive", "high"): 4}


def study_base(juris: pd.DataFrame, holdout: pd.DataFrame) -> pd.DataFrame:
    """Study jurisdictions with outcomes and market variables.

    `juris` is reference/ca_regression_ca_jurisdictions.csv: wave-3 group (pre-period 2017-2019), pre_rate,
    plateau (2023-2025) permits `adu` over `n_years`, homes (ACS one-unit detached), value, income.
    Pre-period permits are recovered as pre_rate x homes x 3 / 1,000.
    """
    b = juris.copy()
    b = b.merge(holdout[["census_geoid", "holdout"]], on="census_geoid", how="left")
    b["holdout"] = b["holdout"].fillna(False).astype(bool)
    b["pre_permits"] = (b["pre_rate"] * b["homes"] * PRE_YEARS / 1000).round()
    b["active"] = b["group"].eq("active")
    b["restrictive"] = b["group"].eq("restrictive")
    b["log_value"] = np.log(b["value"])
    b["log_income"] = np.log(b["income"])
    return b


def value_terciles(values: pd.Series, ref: pd.Series) -> pd.Series:
    """Tercile labels low / mid / high using cut points from `ref` (the non-holdout places)."""
    q1, q2 = ref.quantile([1 / 3, 2 / 3])
    return pd.cut(values, [-np.inf, q1, q2, np.inf], labels=["low", "mid", "high"], include_lowest=True).astype(str)


def draw_hand_sample(base: pd.DataFrame, quota=HAND_QUOTA, seed: int = HAND_SAMPLE_SEED) -> pd.DataFrame:
    """Reproduce the stratified hand-coding draw: non-holdout places, group x value tercile, fixed seed.
    Cells are drawn in the quota's order with one generator; within a cell places are sorted by geoid."""
    nb = base[~base["holdout"]].copy()
    nb["value_tercile"] = value_terciles(nb["value"], nb["value"])
    rng = np.random.default_rng(seed)
    out = []
    for (grp, vt), q in quota.items():
        cell = nb[(nb["group"] == grp) & (nb["value_tercile"] == vt)].sort_values("census_geoid")
        idx = rng.permutation(len(cell))[:q]
        s = cell.iloc[idx].copy()
        s["draw_order"] = range(1, len(s) + 1)
        out.append(s)
    return pd.concat(out)


def assemble(base: pd.DataFrame, scorecard: pd.DataFrame, hcd: pd.DataFrame, tcrlus: pd.DataFrame,
             hand: pd.DataFrame | None) -> pd.DataFrame:
    """One row per study jurisdiction with every pre-2020 rule source attached (left joins on geoid)."""
    df = base.copy()
    sc = scorecard.drop(columns=["juris_name"]).dropna(subset=["census_geoid"]).drop_duplicates("census_geoid")
    hc = hcd.drop(columns=["juris_name"]).dropna(subset=["census_geoid"]).drop_duplicates("census_geoid")
    tc = tcrlus.drop(columns=["juris_name"]).dropna(subset=["census_geoid"]).drop_duplicates("census_geoid")
    tc = tc.rename(columns={f: f"tcrlus_{f}" for f in ("lot_minimum", "size_below_benchmark", "extra_parking", "fees")})
    df = df.merge(sc, on="census_geoid", how="left").merge(hc, on="census_geoid", how="left")
    df = df.merge(tc, on="census_geoid", how="left")
    df["in_tcrlus"] = df["tcrlus_ordinance"].notna()
    tflags = [f"tcrlus_{f}" for f in ("lot_minimum", "size_below_benchmark", "extra_parking", "fees")]
    df["tcrlus_n_flags"] = df[tflags].fillna(False).astype(int).sum(axis=1).where(df["in_tcrlus"])
    df["tcrlus_n_known"] = df[tflags].notna().sum(axis=1).where(df["in_tcrlus"])
    df["cci_graded"] = df["cci_graded"].fillna(False).astype(bool)
    df["hcd_received"] = df["hcd_received"].fillna(False).astype(bool)
    if hand is not None:
        h = hand.copy()
        keep = ["census_geoid", "ordinance_status", "rights_class", *FLAGS, "approval_pathway", "confidence",
                "source_type", "rules_as_of"]
        h = h[keep].rename(columns={c: f"hand_{c}" for c in keep if c != "census_geoid"})
        df = df.merge(h, on="census_geoid", how="left")
        df["in_hand"] = df["hand_ordinance_status"].notna()
        df["hand_coded"] = df["hand_ordinance_status"].isin(["mentions_allows", "not_mentioned", "prohibits"])
        hf = df[[f"hand_{f}" for f in FLAGS]].copy()
        hf.columns = list(FLAGS)
        fc = flag_counts(hf)
        for c in fc.columns:
            df[f"hand_{c}"] = fc[c].where(df["hand_coded"])
    return df


def logistic_fit(X: np.ndarray, y: np.ndarray, maxit: int = 100, ridge: float = 1e-6) -> np.ndarray:
    """Logistic regression by IRLS with a tiny ridge for stability."""
    beta = np.zeros(X.shape[1])
    for _ in range(maxit):
        p = 1 / (1 + np.exp(-(X @ beta)))
        W = np.clip(p * (1 - p), 1e-9, None)
        z = X @ beta + (y - p) / W
        XtW = X.T * W
        new = np.linalg.solve(XtW @ X + ridge * np.eye(X.shape[1]), XtW @ z)
        if np.max(np.abs(new - beta)) < 1e-10:
            return new
        beta = new
    return beta


def insample_auc(X: np.ndarray, y: np.ndarray) -> float:
    """AUC of a logistic model scored on the places it was fitted to."""
    b = logistic_fit(X, y)
    return ordered_logit_free_auc(pd.Series(X @ b), pd.Series(y.astype(bool)))[0]


def cv_auc(X: np.ndarray, y: np.ndarray, k: int = 5, repeats: int = 20, seed: int = HAND_SAMPLE_SEED) -> float:
    """Cross-validated AUC: stratified k folds, AUC computed within each held-out fold and averaged over
    folds and repeats (per-fold AUC avoids the pooled leave-one-out artifact that pushes uninformative
    predictors below 0.5)."""
    rng = np.random.default_rng(seed)
    pos, neg = np.where(y == 1)[0], np.where(y == 0)[0]
    vals = []
    for _ in range(repeats):
        fold = np.empty(len(y), int)
        fold[rng.permutation(pos)] = np.arange(len(pos)) % k
        fold[rng.permutation(neg)] = np.arange(len(neg)) % k
        for f in range(k):
            te = fold == f
            if y[te].sum() in (0, te.sum()) or y[~te].sum() in (0, (~te).sum()):
                continue
            b = logistic_fit(X[~te], y[~te])
            vals.append(ordered_logit_free_auc(pd.Series(X[te] @ b), pd.Series(y[te].astype(bool)))[0])
    return float(np.mean(vals)) if vals else np.nan


def loo_auc(X: np.ndarray, y: np.ndarray) -> float:
    """Leave-one-out AUC of a logistic model (each place scored by a fit that excluded it)."""
    n = len(y)
    scores = np.empty(n)
    for i in range(n):
        m = np.ones(n, bool)
        m[i] = False
        b = logistic_fit(X[m], y[m])
        scores[i] = X[i] @ b
    auc, _, _ = ordered_logit_free_auc(pd.Series(scores), pd.Series(y.astype(bool)))
    return auc


def poisson_rate_ratio(df: pd.DataFrame, outcome: str, exposure: str, predictor: str, controls: tuple[str, ...],
                       n_boot: int = 1000, seed: int = HAND_SAMPLE_SEED) -> dict:
    """Rate ratio for `predictor` (0/1 or count) in a Poisson model with log exposure offset and controls.

    Intervals: percentile bootstrap over places (over-dispersion makes Poisson SEs useless).
    Also returns the deviance share explained by controls alone and with the predictor.
    """
    cols = [outcome, exposure, predictor, *controls]
    d = df[cols].dropna()
    d = d[d[exposure] > 0]
    y = d[outcome].to_numpy(float)
    e = d[exposure].to_numpy(float)

    def X_of(dd, with_pred=True):
        parts = [np.ones(len(dd))] + [dd[c].to_numpy(float) for c in controls]
        if with_pred:
            parts.append(dd[predictor].astype(float).to_numpy())
        return np.column_stack(parts)

    X1, X0 = X_of(d), X_of(d, False)
    b1, b0 = fit_poisson(X1, y, e), fit_poisson(X0, y, e)
    null = np.full(len(y), y.sum() / e.sum()) * e
    dev_null = poisson_deviance(y, null)
    dev0 = poisson_deviance(y, np.exp(X0 @ b0) * e)
    dev1 = poisson_deviance(y, np.exp(X1 @ b1) * e)
    rng = np.random.default_rng(seed)
    draws = []
    n = len(d)
    for _ in range(n_boot):
        i = rng.integers(0, n, n)
        Xi = X1[i]
        if np.ptp(Xi[:, -1]) == 0:
            continue
        draws.append(fit_poisson(Xi, y[i], e[i])[-1])
    lo, hi = (np.percentile(draws, [2.5, 97.5]) if len(draws) > 50 else (np.nan, np.nan))
    return {"outcome": outcome, "predictor": predictor, "controls": "+".join(controls) or "none", "n_places": n,
            "permits": float(y.sum()), "home_years_thousands": float(e.sum()),
            "rate_ratio": float(np.exp(b1[-1])), "rr_lo95": float(np.exp(lo)), "rr_hi95": float(np.exp(hi)),
            "deviance_explained_controls": 1 - dev0 / dev_null if dev_null else np.nan,
            "deviance_explained_with_predictor": 1 - dev1 / dev_null if dev_null else np.nan,
            "n_boot_used": len(draws)}
