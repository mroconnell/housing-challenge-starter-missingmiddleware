"""Audit: why our upzoned acres differ from each plan's published acres (docs/tod/ASK_WHY_REVIEW_2026-10-28.md).

    uv run --all-extras python scripts/run_tod_audit_acres.py

For each case, the acres of parcels inside the reform are split into: treated (counted), not eligible by class
(industrial, institutional, park, other), eligible but allowed density did not rise, already at the law, and
zoning changed in the window. Writes reference/tod_audit_acres.csv.
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
from missing_middleware.tod import cases as C  # noqa: E402
from scripts.run_tod_net_effect import capture  # noqa: E402

PUBLISHED = {"charlotte_tod_2019": 1782.83, "la_cornfield_arroyo_seco_2013": 650, "la_warner_center_2013": 960,
             "bellevue_belred_2009": 900, "madison_tod_overlay_2023": 6031, "seattle_nbh_othello_2012": 41,
             "seattle_mount_baker_2014": 37}


def split(case: str, args: dict, cls: pd.Series | None) -> dict:
    P = args["parcels"]
    ac = P.geometry.area / C.SQM_PER_ACRE
    inr, rose, el = args["in_reform"].astype(bool), args["rose"].astype(bool), args["eligible"].astype(bool)
    chg = args["changed_outside"].astype(bool)
    base = inr & rose & el
    med = C.weighted_median(args["level_after"][base].replace(np.inf, np.nan).fillna(1e9), ac[base])
    at_law = args["uncapped_before"].astype(bool) & (args["level_before"].fillna(-1) >= med)
    treated = inr & rose & ~at_law & ~chg & el
    r = {"case": case, "published_acres": PUBLISHED.get(case), "in_reform_parcel_acres": ac[inr].sum(),
         "treated_acres": ac[treated].sum()}
    ne = inr & ~el
    if cls is not None:
        c = cls.reindex(P.index).astype(str).str.lower()
        for k, pat in (("industrial", "ind"), ("institutional", "inst"), ("park", "park")):
            m = ne & c.str.startswith(pat)
            r[f"not_eligible_{k}_acres"] = ac[m].sum()
            r[f"not_eligible_{k}_rezoned_up_acres"] = ac[m & rose].sum()
            ne = ne & ~m
    r["not_eligible_other_acres"] = ac[ne].sum()
    r["eligible_density_not_rising_acres"] = ac[inr & el & ~rose].sum()
    r["eligible_already_at_law_acres"] = ac[inr & el & rose & at_law].sum()
    r["eligible_zoning_changed_in_window_acres"] = ac[inr & el & rose & ~at_law & chg].sum()
    return r


def main() -> None:
    rows = []
    from missing_middleware.tod import case_charlotte as K
    with capture() as cap:
        K.build()
    a, _ = cap["uniform"][0]
    rows.append(split("charlotte_tod_2019", a, a["parcels"]["zclass"]))
    from missing_middleware.tod import case_la as LA
    for case in ("la_warner_center_2013", "la_cornfield_arroyo_seco_2013"):
        with capture() as cap:
            LA._areas(case)
        a, _ = cap["uniform"][0]
        rows.append(split(case, a, a["parcels"]["zone_before"].map(LA.zclass)))
    from missing_middleware.tod import case_bellevue as B
    with capture() as cap:
        B.build()
    a, _ = max(cap["uniform"], key=lambda t: int((t[1] == C.TREAT).sum()))
    P = a["parcels"]
    cc = next((c for c in ("zclass", "zoning_class", "use_class") if c in P), None)
    print("Bellevue columns:", [c for c in P.columns][:40], flush=True)
    rows.append(split("bellevue_belred_2009", a, P[cc] if cc else None))
    import importlib.util as ilu
    spec = ilu.spec_from_file_location("run_tod_madison_test", ROOT / "scripts" / "run_tod_madison_test.py")
    M = ilu.module_from_spec(spec)
    spec.loader.exec_module(M)
    from missing_middleware.permits import madison
    from missing_middleware.permits.match import AddressIndex
    from missing_middleware.tod import net_effect as NE
    from missing_middleware.paths import RAW
    Lm = M.lots()
    ptab = madison.parcel_table(madison.load_parcels(RAW / "madison_parcels"))
    index = AddressIndex(madison.address_reference(ptab, madison.load_address_points(RAW / "madison_parcels")))
    Lm["changed"], _ = M.rezoned_lots(Lm, index, M.ref_points(index.ref))
    print("Madison columns:", list(Lm.columns)[:60], flush=True)
    a = NE.bind_uniform_args(Lm, in_reform=Lm.in_overlay, rose=Lm.rose, level_before=Lm.far_base, level_after=Lm.far_ovl,
                             uncapped_before=Lm.uncapped, changed_outside=Lm.changed, eligible=Lm.elig)
    cc = next((c for c in ("zclass", "zoning_class", "use_class", "district_class") if c in Lm), None)
    rows.append(split("madison_tod_overlay_2023", a, Lm[cc] if cc else None))
    R = pd.DataFrame(rows)
    R["treated_share_of_published"] = R["treated_acres"] / R["published_acres"]
    R.round(1).to_csv(REFERENCE / "tod_audit_acres.csv", index=False)
    pd.set_option("display.width", 250)
    print(R.round(1).T.to_string())


if __name__ == "__main__":
    main()
