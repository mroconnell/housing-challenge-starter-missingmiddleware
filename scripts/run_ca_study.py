"""Run the pre-registered California comparison study (docs/gate3/CA_COMPARISON_PLAN.md).

Run:  uv run python scripts/run_ca_study.py              # full run (reads raw APR A2 once, then cached)
      uv run python scripts/run_ca_study.py --rebuild-outcome   # re-read raw Table A2 text rules
      uv run python scripts/run_ca_study.py --doc-only    # rewrite generated doc blocks from outputs
      uv run python scripts/run_ca_study.py --check-doc   # fail if the doc differs from outputs
Needs: outputs of scripts/build_ca_comparison_data.py (data/processed/comparison_ca/) and
       data/raw/hcd_apr_a2/tablea2.csv.
Outputs: data/processed/comparison_ca/study/*.csv|parquet (jurisdiction level, git-ignored),
         reference/ca_study_*.csv (group aggregates), docs/gate3/CA_STUDY_RESULTS.md generated blocks.
Order: holdout test results are written before anything else that uses holdout data, and no
all-data refit is performed.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import pandas as pd

from missing_middleware.comparison import ca_inputs as I
from missing_middleware.comparison import ca_step0 as Z
from missing_middleware.comparison import ca_study as S

from missing_middleware.paths import REFERENCE, processed_dir, raw_dir

CA = processed_dir("comparison_ca")


def outcome(rebuild: bool) -> tuple[pd.DataFrame, pd.DataFrame]:
    out = processed_dir("comparison_ca/study")
    f, fx = out / "hcd_adu_outcome.parquet", out / "hcd_adu_text_exclusions.csv"
    if f.exists() and fx.exists() and not rebuild:
        return pd.read_parquet(f), pd.read_csv(fx)
    path = raw_dir("hcd_apr_a2") / "tablea2.csv"
    rows = I.classify_permit_rows(I.read_apr_a2(path))
    # free text read in memory only, aligned by row position; never written out
    txt = pd.read_csv(path, usecols=["NOTES", "PROJECT_NAME"], dtype=str, low_memory=False)
    assert len(txt) == len(rows)
    flag = S.classify_adu_text(txt["NOTES"].fillna("") + " | " + txt["PROJECT_NAME"].fillna(""))
    flag.index = rows.index
    del txt
    o, exc = S.hcd_adu_outcome(rows, flag)
    o.to_parquet(f, index=False)
    exc.to_csv(fx, index=False)
    return o, exc


def main(argv: list[str]) -> None:
    out = processed_dir("comparison_ca/study")
    if "--doc-only" in argv or "--check-doc" in argv:
        changed = S.update_doc(check="--check-doc" in argv)
        if "--check-doc" in argv and changed:
            raise SystemExit(f"{S.DOC_PATH} differs from outputs: {', '.join(changed)}")
        return
    o, exc = outcome("--rebuild-outcome" in argv)
    comp = pd.read_parquet(CA / "adu_compilation_2012_2019.parquet")
    filing = pd.read_parquet(CA / "hcd_apr_filing_status.parquet")
    xw = pd.read_parquet(CA / "ca_jurisdiction_crosswalk.parquet")
    den = pd.read_parquet(CA / "ca_denominators_acs2024.parquet")
    panel = S.build_panel(o, comp, filing, xw, den)
    panel.to_parquet(out / "study_panel.parquet", index=False)

    # ---- main specification, then the holdout test, published before anything else ----
    results = {sp.name: S.run_spec(panel, sp) for sp in S.SPECS}
    main = results["main"]
    glev, jlev, mets, hgroups = S.holdout_test(panel, main)
    glev.to_csv(REFERENCE / "ca_study_holdout_group.csv", index=False)
    mets.to_csv(REFERENCE / "ca_study_holdout_metrics.csv", index=False)
    jlev.to_csv(out / "holdout_jurisdictions.csv", index=False)
    (out / "holdout_groups.json").write_text(json.dumps(hgroups, indent=1))
    print("holdout test written")

    # ---- non-holdout study tables ----
    boots = {name: S.bootstrap(r) for name, r in results.items()}
    ev = pd.concat([r["event"].assign(spec=name) for name, r in results.items()], ignore_index=True)
    ev.to_csv(REFERENCE / "ca_study_event_study.csv", index=False)
    counts = pd.concat([S.group_counts(r) for r in results.values()], ignore_index=True)
    counts.to_csv(REFERENCE / "ca_study_groups.csv", index=False)
    stats = []
    for name, r in results.items():
        for w in S.WAVES:
            for k, v in r["stats"][w.wave].items():
                lo, hi = S.interval(boots[name][w.wave], k)
                stats.append({"spec": name, "wave": w.wave, "statistic": k, "estimate": v, "ci95_lo": lo, "ci95_hi": hi})
    stats = pd.DataFrame(stats)
    stats.to_csv(REFERENCE / "ca_study_wave_stats.csv", index=False)
    exc.to_csv(REFERENCE / "ca_study_text_exclusions.csv", index=False)
    # jurisdiction-level groups (non-holdout), for audit
    gj = []
    for name, r in results.items():
        for w in S.WAVES:
            pre = r["pre"][w.wave].assign(group=r["groups"][w.wave], spec=name, wave=w.wave)
            gj.append(pre.reset_index())
    pd.concat(gj).to_csv(out / "groups_by_jurisdiction.csv", index=False)

    # ---- ADU-share model ----
    bps_place = pd.read_parquet(CA / "bps_ca_place_annual.parquet")
    bps = S.bps_by_jurisdiction(Z.bps_to_jurisdiction(bps_place, xw))
    share = pd.concat([S.share_model(panel, bps, xw, m) for m in ("adu_main", "adu_issue")], ignore_index=True)
    share.to_csv(REFERENCE / "ca_study_share_model.csv", index=False)
    sb = pd.concat([S.share_bootstrap(panel, bps, xw, m) for m in ("adu_main", "adu_issue")], ignore_index=True)
    sb.to_csv(REFERENCE / "ca_study_share_bootstrap.csv", index=False)
    wi = pd.read_csv(REFERENCE / "ca_wi_statewide_bps_per_1000.csv")
    wi = wi[wi["state"].eq("Wisconsin")]
    inv = pd.read_parquet(processed_dir("foundation") / "inventory.parquet")
    wi_homes = float(inv.loc[inv["level"].eq("state"), "homes_1unit_detached"].iloc[0])
    wi_bps = float(wi[wi["year"].isin(S.PLATEAU_YEARS)]["units_total"].mean())
    vol = []
    for m in ("adu_main", "adu_issue"):
        for per in ("wave3_plateau_2023_2025", "pre_2014_2016"):
            row = share[(share["measure"] == m) & (share["period"] == per)].iloc[0]
            v = S.wi_share_volume(row, wi_bps, wi_homes)
            vol.append(v.assign(measure=m, ca_period=per, wi_bps_years="2023-2025 mean", wi_homes=wi_homes))
    pd.concat(vol).to_csv(REFERENCE / "ca_study_wi_share_volume.csv", index=False)
    # Madison comparison point (context only; the Madison floor is another work package)
    mad = pd.read_csv(REFERENCE / "madison_adu_permits_by_year.csv")
    comps = [f"second_home_sf_lot:{c}" for c in ("adu_detached", "adu_attached", "adu_conversion", "adu_two_unit")]
    m_units = mad[mad["year"].between(2022, 2025) & mad["category"].isin(comps)]["units"].sum() / 4
    m_homes = float(inv.loc[inv["area_id"].eq("muni:5502548000"), "homes_1unit_detached"].iloc[0])
    pd.DataFrame([
        {"item": "madison_adu_type_per_year", "value": m_units, "note": "2022-2025 mean, ADU-type components"},
        {"item": "madison_homes", "value": m_homes, "note": "ACS 2020-2024 one-unit detached"},
        {"item": "madison_rate", "value": m_units / m_homes * 1000, "note": "per 1,000 homes per year"},
        {"item": "madison_rate_div_0_8", "value": m_units / m_homes * 1000 / 0.8, "note": "AQ-030 scaling"},
        {"item": "wi_bps_total_2023_2025", "value": wi_bps, "note": "Census BPS state total, mean"},
        {"item": "wi_homes_1unit_detached", "value": wi_homes, "note": "ACS 2020-2024"},
    ]).to_csv(REFERENCE / "ca_study_wi_context.csv", index=False)
    S.update_doc()
    print("done")


if __name__ == "__main__":
    main(sys.argv[1:])
