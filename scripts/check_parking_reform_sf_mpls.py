"""Audit check: reform-model Wisconsin nets refitted without San Francisco and Minneapolis (both out together).

    uv run --all-extras python scripts/check_parking_reform_sf_mpls.py
Output: reference/parking_reform_models_sf_mpls_out.csv
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.argv = [sys.argv[0], "--round", "2"]
import run_parking_reform_models as RM  # noqa: E402

NR = RM.NR
R, reform_year, *_ = NR.prepare()
ry, o = R["reform_year"].values, R["origin"].values
R["reform"] = ((ry >= o - 1) & (ry <= o + 2) & (ry != 9999) & (ry > 0)).astype(int)
data = R[(R["no_reform"] | (R["reform"] == 1)) & R["actual"].notna() & (R["state_fips"] != NR.WI)].copy()
drop = set(data.loc[(data["reform"] == 1) & data["name"].isin(["San Francisco", "Minneapolis"]), "key"])
wi_all = R[(R["state_fips"] == NR.WI) & (R["origin"] == 2025)]
wi = wi_all[wi_all["key"].map(lambda k: reform_year.get(k, 9999) == 9999)]
scale = RM.CENTRAL / (5 * float(wi_all["units_3y"].sum()))
res = RM.all_models(data[~data["key"].isin(drop)], data.head(1), wi)
out = pd.DataFrame([dict(model=m, wi_net_2027_2031=float(np.sum(w) * 5 * scale), left_out="San Francisco + Minneapolis") for m, (_, _, w) in res.items()])
out.to_csv(RM.REFERENCE / "parking_reform_models_sf_mpls_out.csv", index=False)
print(out.round(0).to_string(index=False))
