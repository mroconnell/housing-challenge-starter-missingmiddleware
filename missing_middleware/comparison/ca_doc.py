"""Generate the number-bearing parts of docs/gate2/CA_COMPARISON_DATA.md from the build outputs.

Every table and figure in the doc that comes from data sits between
``<!-- generated:NAME -->`` and ``<!-- /generated:NAME -->`` markers and is rewritten from
``data/processed/comparison_ca`` (and the committed ``reference/ca_*.csv`` files) by
``update_doc``. ``update_doc(check=True)`` only reports which blocks would change, so a test
or ``scripts/build_ca_comparison_data.py --check-doc`` can confirm the doc matches the outputs.
Prose outside the markers carries no figures computed from data.

Figures that could feed the Gate 3 model are shown for non-holdout jurisdictions, with the
all-jurisdiction figure beside them. Descriptive data-quality tables use all jurisdictions.
"""
from __future__ import annotations

import re
from pathlib import Path

import numpy as np
import pandas as pd

from missing_middleware.paths import REFERENCE, ROOT

DOC = ROOT / "docs" / "gate2" / "CA_COMPARISON_DATA.md"
LA, SF, SD = "0644000", "0667000", "0666000"


# ---------------------------------------------------------------------------
# formatting
# ---------------------------------------------------------------------------

def n0(x) -> str:
    return "—" if x is None or (isinstance(x, float) and not np.isfinite(x)) else f"{x:,.0f}"


def r2(x) -> str:
    return "—" if x is None or not np.isfinite(float(x)) else f"{float(x):.2f}"


def pct(x, d=1) -> str:
    return "—" if x is None or not np.isfinite(float(x)) else f"{100 * float(x):.{d}f}%"


def rng(a, b, f=r2) -> str:
    return f"{f(a)} to {f(b)}"


def table(header: list[str], rows: list[list[str]], align: list[str] | None = None) -> str:
    align = align or ["---"] + ["---:"] * (len(header) - 1)
    out = ["| " + " | ".join(header) + " |", "|" + "|".join(align) + "|"]
    out += ["| " + " | ".join(str(c) for c in r) + " |" for r in rows]
    return "\n".join(out)


def _name(s: str) -> str:
    return s.title().replace(" Of ", " of ").replace("Unincorporated", "unincorporated")


# ---------------------------------------------------------------------------
# loading
# ---------------------------------------------------------------------------

class Outputs:
    def __init__(self, out: Path):
        self.out = Path(out)
        self.s0 = self.out / "step0"
        self._c: dict[str, pd.DataFrame] = {}

    def __call__(self, name: str) -> pd.DataFrame:
        if name not in self._c:
            if name.startswith("ref:"):
                p = REFERENCE / f"{name[4:]}.csv"
            elif (self.s0 / f"{name}.csv").exists():
                p = self.s0 / f"{name}.csv"
            else:
                p = self.out / f"{name}.parquet"
            self._c[name] = (pd.read_parquet(p) if p.suffix == ".parquet"
                             else pd.read_csv(p, dtype={"census_geoid": str, "county_fips": str}))
        return self._c[name]


def available(out: Path) -> bool:
    return (Path(out) / "step0" / "b_adu_share_sensitivity.csv").exists()


# ---------------------------------------------------------------------------
# blocks
# ---------------------------------------------------------------------------

def blk_apr_measures(o: Outputs) -> str:
    agg, dq, dd = o("hcd_apr_a2_juris_year_unitcat"), o("apr_permit_date_quality"), o("hcd_apr_a2_issue_year_dedup")
    rows_total = agg["project_rows"].sum()
    rep = dq["bp_units_reported"].sum()
    earlier = dq["earlier_repeat_units"].sum() + dq["earlier_first_report_units"].sum()
    la = agg[agg["juris_name"] == "LOS ANGELES"]["bp_units_date_earlier"].sum()
    flags = dd.groupby("issue_year_flag")["bp_units_issue_year_dedup"].sum()
    after = dd[dd["issue_year_flag"] == "after_first_report_year"]
    after_in = after[after["issue_year"].between(2018, 2025)]["bp_units_issue_year_dedup"].sum()
    api = o("apr_csv_vs_api_crosscheck")
    t = table(["Figure (Table A2, 2018–2025 reports, all jurisdictions)", "Value"], [
        ["Rows in Table A2", n0(rows_total)],
        ["Permitted units as reported (`NO_BUILDING_PERMITS`)", n0(rep)],
        ["Units whose permit date is before the report year", f"{n0(earlier)} ({pct(earlier / rep, 0)} of reported)"],
        ["… of which the same permit is also listed in another report year (repeats)", n0(dq["earlier_repeat_units"].sum())],
        ["… of which first reported late (kept by the dedup measure, dropped by the primary)", n0(dq["earlier_first_report_units"].sum())],
        ["… of which City of Los Angeles", n0(la)],
        ["Units with no permit date (kept in the primary measure)", n0(dq["date_missing"].sum())],
        ["Units dated after the report year (dropped by the primary measure)", n0(dq["date_later"].sum() + dq["date_later_repeat"].sum())],
        ["Dedup table: units with an issue year after the year first reported", n0(flags.get("after_first_report_year", 0))],
        ["… of which dated 2018–2025 (kept, flagged)", n0(after_in)],
        ["Dedup table: units with an issue year before 2000 (ignored: outside 2018–2025)", n0(flags.get("before_2000", 0))],
        ["Dedup table: issue-year range as entered", f"{int(dd['issue_year'].min())}–{int(dd['issue_year'].max())}"],
        ["CSV vs datastore API, year × UNIT_CAT cells matching", f"{int(api['match'].sum())} of {len(api)}"],
    ], ["---", "---:"])
    return t


def blk_apr_statewide(o: Outputs) -> str:
    agg, dd = o("hcd_apr_a2_juris_year_unitcat"), o("hcd_apr_a2_issue_year_dedup")
    pr = agg.pivot_table(index="year", columns="unit_cat", values="bp_units_primary", aggfunc="sum")
    rp = agg[agg["unit_cat"] == "ADU"].groupby("year")["bp_units_reported"].sum()
    de = dd[dd["unit_cat"] == "ADU"].groupby("issue_year")["bp_units_issue_year_dedup"].sum()
    rows = [[int(y), n0(pr.loc[y, "SFD"]), n0(pr.loc[y, "SFA"]), n0(pr.loc[y, "2 to 4"]), n0(pr.loc[y, "5+"]),
             n0(pr.loc[y, "ADU"]), n0(rp.get(y)), n0(de.get(y)), n0(pr.loc[y, "MH"])] for y in pr.index]
    return table(["Year", "SFD", "SFA", "2–4", "5+", "ADU", "ADU as reported", "ADU, issue-year dedup", "MH"], rows)


def blk_outputs_rows(o: Outputs) -> str:
    f = [("hcd_apr_a2_juris_year_unitcat", "HCD jurisdiction × report year × UNIT_CAT"),
         ("hcd_apr_a2_issue_year_dedup", "jurisdiction × permit issue year × UNIT_CAT × `issue_year_flag`"),
         ("hcd_apr_filing_status", "jurisdiction × year 2018–2025"),
         ("adu_compilation_2012_2019", "jurisdiction × year"),
         ("ca_denominators_acs2024", "incorporated places + county remainders"),
         ("ca_jurisdiction_crosswalk", "HCD or compilation name"),
         ("step0_juris_year_panel", "census_geoid × year 2018–2025")]
    return table(["File", "Grain", "Rows"], [[f"`{a}`", b, n0(len(o(a)))] for a, b in f], ["---", "---", "---:"])


def blk_crosswalk(o: Outputs) -> str:
    x = o("ca_jurisdiction_crosswalk")
    def row(lbl, s):
        return [lbl, n0(len(s)), f"{n0(s['matched_census'].sum())} ({pct(s['matched_census'].mean())})",
                f"{n0(s['matched_bps'].sum())} ({pct(s['matched_bps'].mean())})"]
    t = table(["", "Names", "Matched to Census", "Matched to BPS place ids"],
              [row("HCD APR Table A2 jurisdictions", x[x["in_hcd_apr"]]),
               row("Compilation rows", x[x["in_compilation"]]), row("Union of the two", x)])
    mm = x["match_method"].value_counts()
    miss = x[x["juris_type"].eq("city") & ~x["matched_bps"]].sort_values("juris_name")
    only = x[~x["in_hcd_apr"] & x["in_compilation"]]
    return (t + "\n\n" + f"- Methods: {n0(mm.get('exact name', 0))} exact normalized names, {n0(mm.get('county name', 0))} "
            f"counties by name, {n0(mm.get('consolidated city-county', 0))} consolidated city-county (San Francisco), and "
            f"{n0(mm.get('alias', 0))} hand-checked aliases.\n"
            f"- {len(miss)} cities never appear in any BPS place file from 2010 to 2025 "
            f"({len(miss[miss['in_hcd_apr']])} with HCD Table A2 rows, {len(miss[~miss['in_hcd_apr']])} compilation only): "
            + ", ".join(_name(n) for n in miss["juris_name"]) + ".\n"
            f"- {len(x[x['in_hcd_apr'] & ~x['in_compilation']])} Table A2 names are missing from the compilation; "
            f"{len(only)} compilation names have no A2 rows: " + ", ".join(_name(n) for n in only["juris_name"]) + ".")


def blk_holdout(o: Outputs) -> str:
    h = o("ref:ca_holdout_jurisdictions")
    hh = h[h["holdout"].astype(str) == "True"]
    tf = lambda s: s.astype(str) == "True"
    no_a2 = hh[~tf(hh["has_hcd_a2_data"])]
    return table(["Holdout", "Count"], [
        ["Universe (Census geography, sorted by `census_geoid`)", n0(int(h["universe_size"].iloc[0]))],
        ["Drawn (seed " + str(int(h["seed"].iloc[0])) + ")", n0(len(hh))],
        ["… cities (incl. San Francisco)", n0((hh["juris_type"] != "county_unincorporated").sum())],
        ["… county remainders", n0((hh["juris_type"] == "county_unincorporated").sum())],
        ["… with any HCD or compilation data (effective holdout)", n0(tf(hh["has_hcd_or_compilation_data"]).sum())],
        ["… with HCD Table A2 rows", n0(tf(hh["has_hcd_a2_data"]).sum())],
        ["Held out with no Table A2 rows", ", ".join(f"{r['name']}" + ("" if r["has_hcd_or_compilation_data"] in (True, "True")
                                                              else " (no data at all)") for _, r in no_a2.iterrows())],
    ], ["---", "---:"])


def blk_statewide_bps(o: Outputs) -> str:
    s = o("ref:ca_wi_statewide_bps_per_1000")
    yrs = [2010, 2014, 2016, 2018, 2020, 2021, 2022, 2023, 2024, 2025]
    rows = []
    for st, ab in (("California", "CA"), ("Wisconsin", "WI")):
        d = s[s["state"] == st].set_index("year")
        rows.append([f"{ab} units / 1,000 homes"] + [r2(d.loc[y, "units_per_1000_homes"]) for y in yrs])
        rows.append([f"{ab} index"] + [n0(d.loc[y, "index_2014_2016_eq_100"]) for y in yrs])
    return table(["Year"] + [str(y) for y in yrs], rows)


def blk_full_reporting(o: Outputs) -> str:
    a = o("a_nonadu_by_year")
    f = a[a["subset"] == "both_full_reporting"]
    rows = []
    for samp, lbl in (("non_holdout", "Non-holdout (used for any model-facing figure)"), ("all", "All jurisdictions")):
        g = f[f["jurisdiction_sample"] == samp]
        rows.append([lbl, f"{n0(g['jurisdictions'].min())}–{n0(g['jurisdictions'].max())}", n0(g["jurisdictions"].sum())])
    return table(["Sample", "Fully reported jurisdictions a year", "Jurisdiction-years 2018–2025"], rows)


def blk_table_a(o: Outputs) -> str:
    a = o("a_nonadu_by_year")
    f = a[a["subset"] == "both_full_reporting"]
    nh, al = f[f["jurisdiction_sample"] == "non_holdout"].set_index("year"), f[f["jurisdiction_sample"] == "all"].set_index("year")
    rows = [[int(y), n0(r["jurisdictions"]), n0(r["hcd_nonadu_primary"]), n0(r["hcd_nonadu_reported"]),
             n0(r["hcd_nonadu_issue_year_dedup"]), n0(r["bps_units_total"]), r2(r["ratio_hcd_primary_to_bps"]),
             r2(r["ratio_hcd_reported_to_bps"]), r2(r["ratio_hcd_dedup_to_bps"]), r2(r["ratio_hcd_primary_plus_mh_to_bps"]),
             r2(al.loc[y, "ratio_hcd_primary_to_bps"]), r2(al.loc[y, "ratio_hcd_dedup_to_bps"])] for y, r in nh.iterrows()]
    t = table(["Year", "Jurisdictions", "HCD primary", "HCD as reported", "HCD dedup", "BPS total", "Primary / BPS",
               "Reported / BPS", "Dedup / BPS", "(Primary+MH) / BPS", "Primary / BPS, all juris.", "Dedup / BPS, all juris."], rows)
    allj = a[(a["subset"] == "all")]
    def span(samp, col):
        g = allj[allj["jurisdiction_sample"] == samp][col]
        return rng(g.min(), g.max())
    return (t + "\n\nNon-holdout, fully reported in both sources. Using every jurisdiction-year with BPS imputation, "
            f"primary / BPS is {span('non_holdout', 'ratio_hcd_primary_to_bps')} (non-holdout) and "
            f"{span('all', 'ratio_hcd_primary_to_bps')} (all jurisdictions) (`a_nonadu_by_year.csv`).")


def blk_table_a_top50(o: Outputs) -> str:
    t = o("a_nonadu_top50")
    nh = t[~t["in_holdout"].astype(bool)]
    def band(d):
        r = d["ratio_primary_pooled"]
        return f"median {r2(r.median())}; {int(r.between(0.8, 1.25).sum())} of {len(d)} within 0.80–1.25"
    g = t.set_index("census_geoid")
    named = ["0666000", "0668000", "0667000", "0627000", "0636770", "0653000"]
    s = ", ".join(f"{_name(g.loc[i, 'juris_name'])} {r2(g.loc[i, 'ratio_primary_pooled'])}" for i in named if i in g.index
                  and not g.loc[i, "in_holdout"])
    low = nh[nh["ratio_primary_pooled"] < 0.7].sort_values("ratio_primary_pooled")
    hold_names = ", ".join(_name(n) for n in t[t["in_holdout"].astype(bool)]["juris_name"])
    return (f"- **Top 50 jurisdictions by housing units** (`a_nonadu_top50.csv`, pooled over full-reporting years), "
            f"primary / BPS: non-holdout {band(nh)}; all 50 {band(t)}.\n"
            f"- City of Los Angeles: {r2(g.loc[LA, 'ratio_primary_pooled'])} under the primary measure, "
            f"{r2(g.loc[LA, 'ratio_reported_pooled'])} as reported. Other large non-holdout jurisdictions: {s}.\n"
            f"- Non-holdout top-50 jurisdictions where HCD runs well below BPS (below 0.70): "
            + ", ".join(f"{_name(r['juris_name'])} {r2(r['ratio_primary_pooled'])}" for _, r in low.iterrows()) + ".\n"
            f"- Holdout jurisdictions in the top 50 (flagged `in_holdout` in the CSV; their ratios are not summarised here): "
            f"{len(t) - len(nh)} ({hold_names}).")


def blk_table_a_county(o: Outputs) -> str:
    c = o("a_nonadu_by_county").set_index("county_fips")
    pick = ["037", "065", "073", "059", "085", "075"]
    s = ", ".join(f"{c.loc[k, 'county_name'].replace(' County', '')} {r2(c.loc[k, 'ratio_hcd_primary_to_bps'])}" for k in pick)
    m = c.loc["045"]
    fs = c[c["fold_supported"].astype(bool)]
    fl = ", ".join(f"{r['county_name'].replace(' County', '')} {r2(r['ratio_hcd_primary_to_bps'])} → "
                   f"{r2(r['ratio_hcd_primary_to_bps_folded'])}" for _, r in fs.iterrows())
    return (f"- County sums of full-reporting jurisdiction-years, primary / BPS (`a_nonadu_by_county.csv`; descriptive, "
            f"includes holdout jurisdictions): {s}. Los Angeles County as reported: "
            f"{r2(c.loc['037', 'ratio_hcd_reported_to_bps'])}.\n"
            f"- Mendocino's {r2(m['ratio_hcd_primary_to_bps'])} reflects BPS reporting only {n0(m['bps_units_total'])} units "
            f"in its full-reporting jurisdiction-years.\n"
            f"- With the HCD units of BPS-missing cities folded into the county where the fold test supports it "
            f"(`ratio_hcd_primary_to_bps_folded`): {fl}.")


def blk_table_a_mismatches(o: Outputs) -> str:
    m = o("a_nonadu_largest_mismatches").head(8)
    return "\n".join(f"- {_name(r['juris_name'])}{' (holdout)' if str(r['in_holdout']) == 'True' else ''} {int(r['year'])}: "
                     f"HCD {n0(r['hcd_nonadu'])} ({n0(r['hcd_nonadu_reported'])} as reported) vs BPS {n0(r['bps_units_total'])}."
                     for _, r in m.iterrows())


def blk_table_b(o: Outputs) -> str:
    b = o("b_one_unit_by_year")
    nh, al = b[b["jurisdiction_sample"] == "non_holdout"].set_index("year"), b[b["jurisdiction_sample"] == "all"].set_index("year")
    rows = [[int(y), n0(r["bps_1unit"]), n0(r["hcd_sfd"] + r["hcd_sfa"]), n0(r["hcd_adu"]), r2(r["ratio_bps1_to_hcd_sf"]),
             r2(r["ratio_bps1_to_hcd_sf_plus_adu"]), r2(r["ratio_bps2_4_to_hcd_2_4"]),
             r2(al.loc[y, "ratio_bps1_to_hcd_sf"]), r2(al.loc[y, "ratio_bps1_to_hcd_sf_plus_adu"])] for y, r in nh.iterrows()]
    return table(["Year", "BPS 1-unit", "HCD SFD+SFA", "HCD ADU", "BPS1 / SF", "BPS1 / (SF+ADU)", "BPS 2–4 / HCD 2–4",
                  "BPS1 / SF, all juris.", "BPS1 / (SF+ADU), all juris."], rows) + "\n\nNon-holdout, fully reported in both sources."


def _sens(o: Outputs):
    s = o("b_adu_share_sensitivity")
    return s, s[s["jurisdiction_sample"] == "non_holdout"], s[s["jurisdiction_sample"] == "all"]


def blk_b_sensitivity(o: Outputs) -> str:
    s, nh, al = _sens(o)
    def get(d, analysis, variant=None, measure="primary"):
        q = d[(d["analysis"] == analysis) & (d["measure"] == measure)]
        if variant is not None:
            q = q[q["variant"] == variant]
        return q.iloc[0]
    rows = []
    for m, lbl in (("primary", "primary"), ("issue_year_dedup", "issue-year dedup"), ("as_reported", "as reported")):
        a, b = get(nh, "baseline_adjusted", "all jurisdictions", m), get(al, "baseline_adjusted", "all jurisdictions", m)
        rows.append([f"Baseline-adjusted, {lbl} measure", r2(a["estimate"]), f"{n0(a['n_baseline_juris_years'])}, {r2(a['baseline_ratio'])}",
                     r2(b["estimate"])])
    for m, lbl in (("primary", "primary"), ("issue_year_dedup", "issue-year dedup"), ("as_reported", "as reported")):
        a, b = get(nh, "bootstrap_jurisdiction_cluster", None, m), get(al, "bootstrap_jurisdiction_cluster", None, m)
        rows.append([f"Jurisdiction-cluster bootstrap, {lbl}: median [95% interval]",
                     f"{r2(a['estimate'])} [{rng(a['ci_low'], a['ci_high'])}]", "",
                     f"{r2(b['estimate'])} [{rng(b['ci_low'], b['ci_high'])}]"])
    for m, lbl in (("primary", "primary"), ("issue_year_dedup", "issue-year dedup"), ("as_reported", "as reported")):
        a, b = get(nh, "baseline_adjusted", "excl. City of Los Angeles", m), get(al, "baseline_adjusted", "excl. City of Los Angeles", m)
        rows.append([f"Excluding City of Los Angeles, {lbl}", r2(a["estimate"]), "", r2(b["estimate"])])
    for k in ("5,000", "10,000", "20,000"):
        v = f"baseline from places with >= {k} one-unit detached homes"
        a, b = get(nh, "baseline_min_size", v), get(al, "baseline_min_size", v)
        rows.append([f"Baseline only from places with ≥ {k} one-unit detached homes", r2(a["estimate"]),
                     f"{n0(a['n_baseline_juris_years'])}, {r2(a['baseline_ratio'])}", r2(b["estimate"])])
    a = get(nh, "baseline_min_size", "median one-unit detached homes in baseline places")
    b = get(al, "baseline_min_size", "median one-unit detached homes in baseline places")
    rows.append(["(Median one-unit detached homes in the zero-ADU baseline places)", n0(a["estimate"]), "", n0(b["estimate"])])
    yn, ya = nh[nh["analysis"] == "by_year"], al[al["analysis"] == "by_year"]
    for (_, a), (_, b) in zip(yn.iterrows(), ya.iterrows()):
        rows.append([f"Baseline and share for {a['variant']} only", r2(a["estimate"]),
                     f"{n0(a['n_baseline_juris_years'])}, {r2(a['baseline_ratio'])}", r2(b["estimate"])])
    rn, ra = nh[nh["analysis"] == "regression_adu_coefficient"], al[al["analysis"] == "regression_adu_coefficient"]
    for (_, a), (_, b) in zip(rn.iterrows(), ra.iterrows()):
        kind, samp = a["variant"].split("; ")
        kind = {"pooled": "pooled, no intercept", "within_jurisdiction": "within-jurisdiction",
                "jurisdiction_and_year_fe": "jurisdiction + year FE"}[kind]
        rows.append([f"Regression ADU coefficient, {kind}; {samp} ({a['note'].split(';')[0]})",
                     f"{r2(a['estimate'])} [{rng(a['ci_low'], a['ci_high'])}]", "",
                     f"{r2(b['estimate'])} [{rng(b['ci_low'], b['ci_high'])}]"])
    t = table(["Specification (share of HCD ADUs inside BPS 1-unit)", "Non-holdout", "Baseline jurisdiction-years, baseline ratio",
               "All jurisdictions"], rows, ["---", "---:", "---:", "---:"])
    pts = nh[nh["analysis"].isin(["baseline_adjusted", "baseline_min_size", "regression_adu_coefficient"])
             & ~nh["variant"].str.startswith("median")]
    return (t + "\n\n" + f"Across these non-holdout specifications the central values run from {r2(pts['estimate'].min())} to "
            f"{r2(pts['estimate'].max())}; year-by-year values run from {r2(yn['estimate'].min())} to {r2(yn['estimate'].max())}, "
            f"with {n0(yn['n_baseline_juris_years'].min())}–{n0(yn['n_baseline_juris_years'].max())} baseline jurisdiction-years a year. "
            "Regression intervals use classical standard errors and are too narrow for clustered data; the bootstrap "
            "interval is the honest one.")


def blk_b_place_pattern(o: Outputs) -> str:
    t = o("b_one_unit_top50")
    t = t.assign(in_holdout=t["in_holdout"].astype(str) == "True")
    g = t.set_index("census_geoid")
    def desc(i):
        r = g.loc[i]
        return (f"{_name(r['juris_name'])} (BPS1 / SF {r2(r['ratio_bps1_to_sf'])}, BPS1 / (SF+ADU) "
                f"{r2(r['ratio_bps1_to_sf_plus_adu'])}, BPS total / HCD non-ADU {r2(r['ratio_bps_total_to_hcd_nonadu'])})")
    nh = t[~t["in_holdout"]]
    band = nh["ratio_bps_total_to_hcd_nonadu"].between(0.8, 1.25)
    inc = nh[(nh["ratio_bps1_to_sf"] >= 2.5) & band].sort_values("ratio_bps1_to_sf")
    gap = nh[(nh["ratio_bps1_to_sf"] >= 2.5) & ~band].sort_values("ratio_bps1_to_sf")
    hin = t[t["in_holdout"] & (t["ratio_bps1_to_sf"] >= 2.5)]
    cl = nh["closer_level_match"].value_counts()
    corr = nh.dropna(subset=["corr_bps1_sf", "corr_bps1_sf_plus_adu"])
    better = int((corr["corr_bps1_sf_plus_adu"] > corr["corr_bps1_sf"]).sum())
    la_share = t.loc[t["census_geoid"] == LA, "hcd_adu"].sum() / o("b_one_unit_baseline_adjusted").query(
        "jurisdiction_sample == 'all' and sample == 'all'")["hcd_adu"].iloc[0]
    return (f"- **Appear to exclude ADUs from BPS 1-unit:** {desc(LA)}; {desc(SD)}; {desc(SF)}. BPS1 / (SF+ADU) is far below 1, "
            f"and BPS totals are near HCD non-ADU units alone. Los Angeles holds {pct(la_share, 0)} of HCD ADUs in the full-reporting sample.\n"
            f"- **Appear to include ADUs in BPS 1-unit** (non-holdout top 50, BPS1 / SF ≥ 2.5 while BPS total / HCD non-ADU is "
            f"within 0.80–1.25): " + "; ".join(desc(i) for i in inc["census_geoid"]) + ".\n"
            f"- **BPS1 / SF ≥ 2.5 but more likely an HCD reporting gap** (BPS total also runs far above HCD non-ADU): "
            + "; ".join(desc(i) for i in gap["census_geoid"]) + ". Torrance in particular reports far fewer non-ADU units to "
            "HCD than BPS shows, so its high BPS1 / SF says little about ADUs.\n"
            f"- {len(hin)} holdout jurisdictions in the top 50 also have BPS1 / SF ≥ 2.5; they stay in `b_one_unit_top50.csv` "
            "(flagged) and are not used.\n"
            f"- Among the {len(nh)} non-holdout top-50 jurisdictions, BPS 1-unit is closer in level to SF+ADU in "
            f"{int(cl.get('sf_plus_adu', 0))} and to SF alone in {int(cl.get('sf_only', 0))}; over time it correlates better "
            f"with SF+ADU in {better} of {len(corr)}.")


def blk_fold(o: Outputs) -> str:
    f = o("c_bps_missing_cities_fold")
    rows = []
    for _, r in f.iterrows():
        rows.append([r["county_name"] + (" (holdout)" if str(r["remainder_in_holdout"]) == "True" else ""),
                     ", ".join(_name(c) for c in str(r["bps_missing_cities"]).split(";")),
                     n0(r["remainder_full_years"]), n0(r["cities_hcd_nonadu"]),
                     f"{r2(r['ratio_hcd_to_bps_before'])} → {r2(r['ratio_hcd_to_bps_folded'])}",
                     f"{r2(r['ratio_hcd_to_bps_before_all_years'])} → {r2(r['ratio_hcd_to_bps_folded_all_years'])}",
                     f"{r2(r['ratio_hcd_sf_to_bps1_before'])} → {r2(r['ratio_hcd_sf_to_bps1_folded'])}",
                     r2(r["corr_bps_excess_with_city_hcd_over_years"]),
                     "yes" if str(r["fold_supported"]) == "True" else "no"])
    return table(["County remainder", "BPS-missing cities", "Full years", "Cities' HCD non-ADU units",
                  "HCD / BPS total, full years", "Same, all years with both", "HCD SF / BPS 1-unit, full years",
                  "Corr. of BPS excess with cities' HCD", "Fold supported"], rows,
                 ["---", "---", "---:", "---:", "---:", "---:", "---:", "---:", "---"])


def blk_table_c(o: Outputs) -> str:
    cov = o("c_coverage_by_year").query("jurisdiction_sample == 'all'").set_index("year")
    fil = o("c_apr_filing_by_year").query("jurisdiction_sample == 'all'").set_index("year")
    imp = o("c_bps_imputation_by_year").set_index("year")
    rows = [[int(y), n0(cov.loc[y, "both"]), n0(cov.loc[y, "hcd_only"]), n0(cov.loc[y, "bps_only"]), n0(fil.loc[y, "a2_rows"]),
             n0(fil.loc[y, "filed_no_a2_rows"]), n0(fil.loc[y, "no_record"]),
             f"{n0(imp.loc[y, 'places_12_months'])} / {n0(imp.loc[y, 'places_0_months'])} / {n0(imp.loc[y, 'places_partial'])}",
             pct(imp.loc[y, "imputed_share"])] for y in cov.index]
    one = o("c_one_source_only")
    h, b = one[one["coverage"] == "hcd_only"], one[one["coverage"] == "bps_only"]
    ys = imp.loc[2018:2025, "imputed_share"]
    return (table(["Year", "Both sources", "HCD only (BPS absent or 0 months)", "BPS only (no HCD A2 rows)", "HCD: A2 rows",
                   "HCD: filed, no A2 rows", "HCD: no record", "BPS places with 12 / 0 / partial months",
                   "BPS imputed share of units"], rows)
            + f"\n\nAll jurisdictions (descriptive). HCD-only jurisdiction-years hold {n0(h['hcd_nonadu'].sum())} non-ADU and "
            f"{n0(h['adu'].sum())} ADU permits; BPS-only years hold {n0(b['bps_units_total'].sum())} BPS units. Imputed BPS "
            f"units are {pct(ys.min())}–{pct(ys.max())} of the state total in 2018–2025.")


def blk_table_d(o: Outputs) -> str:
    d = o("d_compilation_vs_apr_summary")
    rows = []
    for samp, lbl in (("all", "all"), ("non_holdout", "non-holdout")):
        for _, r in d[d["jurisdiction_sample"] == samp].iterrows():
            rows.append([f"{int(r['year'])} ({lbl})", n0(r["compilation_rows"]), n0(r["compilation_total"]),
                         n0(r["apr_reported_same_jurisdictions"]), n0(r["apr_primary_total_all"]),
                         f"{n0(r['exact_equal_reported'])} / {n0(r['compilation_rows'])}", n0(r["within_10pct_or_2_reported"]),
                         f"{r['corr_reported']:.3f}", n0(r["apr_positive_compilation_zero"])])
    al = d[d["jurisdiction_sample"] == "all"].set_index("year")
    brk = "; ".join(f"{y}: {pct(al.loc[y, 'compilation_total'] / al.loc[y, 'apr_reported_same_jurisdictions'] - 1)} against "
                    f"as-reported, {pct(al.loc[y, 'compilation_total'] / al.loc[y, 'apr_primary_total_all'] - 1)} against primary"
                    for y in al.index)
    return (table(["Year (sample)", "Compilation rows", "Compilation total", "APR ADU as reported, same jurisdictions",
                   "APR ADU, primary", "Rows exactly equal to APR as reported", "Within ±10% or ±2", "Correlation",
                   "Compilation 0 where APR > 0"], rows)
            + f"\n\nCompilation relative to APR (all jurisdictions): {brk}.")


BLOCKS = {
    "apr_measures": blk_apr_measures, "apr_statewide": blk_apr_statewide, "outputs_rows": blk_outputs_rows,
    "crosswalk": blk_crosswalk, "holdout": blk_holdout, "statewide_bps": blk_statewide_bps,
    "full_reporting": blk_full_reporting, "table_a": blk_table_a, "table_a_top50": blk_table_a_top50,
    "table_a_county": blk_table_a_county, "table_a_mismatches": blk_table_a_mismatches, "table_b": blk_table_b,
    "b_sensitivity": blk_b_sensitivity, "b_place_pattern": blk_b_place_pattern, "fold": blk_fold,
    "table_c": blk_table_c, "table_d": blk_table_d,
}

_RE = re.compile(r"(<!-- generated:(?P<name>[a-z0-9_]+) -->\n)(?P<body>.*?)(\n?<!-- /generated:(?P=name) -->)", re.S)


def render(out: Path) -> dict[str, str]:
    o = Outputs(out)
    return {k: f(o) for k, f in BLOCKS.items()}


def update_doc(out: Path, check: bool = False, doc: Path = DOC) -> list[str]:
    """Rewrite generated blocks in the doc. Returns names of blocks that changed (or would
    change, with check=True). Raises if a block's markers are missing from the doc."""
    text = doc.read_text()
    blocks = render(out)
    missing = [k for k in blocks if f"<!-- generated:{k} -->" not in text]
    if missing:
        raise ValueError(f"{doc} lacks generated blocks: {missing}")
    changed, seen = [], []

    def sub(m):
        new = blocks[m.group("name")]
        seen.append(m.group("name"))
        if m.group("body") != new or m.group(4) != f"\n<!-- /generated:{m.group('name')} -->":
            changed.append(m.group("name"))
        return m.group(1) + new + f"\n<!-- /generated:{m.group('name')} -->"

    new_text = _RE.sub(sub, text)
    unmatched = sorted(set(blocks) - set(seen))
    if unmatched:
        raise ValueError(f"{doc}: generated blocks not parsed (check their end markers): {unmatched}")
    if not check and new_text != text:
        doc.write_text(new_text)
    return changed


def doc_facing_numbers(out: Path) -> str:
    """Short print-out of the headline figures the doc quotes, read from the outputs."""
    o = Outputs(out)
    s, nh, al = _sens(o)
    b = nh[(nh["analysis"] == "bootstrap_jurisdiction_cluster") & (nh["measure"] == "primary")].iloc[0]
    pts = nh[nh["analysis"].isin(["baseline_adjusted", "baseline_min_size", "regression_adu_coefficient"])
             & ~nh["variant"].str.startswith("median")]
    ba = o("b_one_unit_baseline_adjusted")
    pick = lambda samp: ba[(ba["jurisdiction_sample"] == samp) & (ba["sample"] == "all")]["implied_adu_share_in_bps1"].iloc[0]
    h = o("ref:ca_holdout_jurisdictions")
    hh = h[h["holdout"].astype(str) == "True"]
    lines = ["Doc-facing figures (from outputs):",
             f"  holdout drawn {len(hh)}; effective (any data) {int((hh['has_hcd_or_compilation_data'].astype(str) == 'True').sum())}",
             f"  ADU share in BPS1, baseline-adjusted primary: non-holdout {r2(pick('non_holdout'))}, all {r2(pick('all'))}",
             f"  bootstrap (non-holdout, primary): {r2(b['estimate'])} [{rng(b['ci_low'], b['ci_high'])}]",
             f"  central values across specifications (non-holdout): {rng(pts['estimate'].min(), pts['estimate'].max())}",
             f"  fold supported: {', '.join(o('c_bps_missing_cities_fold').query('fold_supported')['county_name'])}"]
    return "\n".join(lines)
