"""Round 6 audit checks for the parking net Wisconsin and no-reform data (docs/parking/NET_WI_PLAN.md).

    uv run --all-extras python scripts/check_parking_net_wi_r6.py
Output: reference/parking_net_wi_audit_checks_r7.csv
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.argv = [sys.argv[0], "--round", "6"]
import run_parking_no_reform as NR  # noqa: E402
from missing_middleware.paths import REFERENCE  # noqa: E402

R, *_ = NR.prepare()
out = []
# 2. homes varies by origin
nun = R.groupby("key")["homes"].nunique()
out.append(dict(check="homes varies by origin", value=f"{(nun > 1).mean():.3f}", note=f"share of {len(nun)} places with more than one homes value across origins"))
# 3. jump where the census base switches (origin 2021 uses 2010 + permits 2012-2021; origin 2022 uses 2020 + permits 2020-2022)
w = R.pivot_table(index="key", columns="origin", values="homes")
for a, b in ((2019, 2020), (2021, 2022)):
    j = (w[b] / w[a] - 1).dropna()
    big = j[j.abs() > 0.05]
    names = R.drop_duplicates("key").set_index("key")["name"]
    out.append(dict(check=f"homes change > 5% from origin {a} to {b}", value=f"{len(big)} of {len(j)}",
                    note=f"median change {j.median():+.3f}; largest: " + ", ".join(f"{names[k]} {v:+.2f}" for k, v in big.abs().sort_values(ascending=False).head(6).items())))
# 4. added permits stop at the origin (round 6 source): origins 2016-2019 use the ACS release ending at the origin and add
# no permits; origin 2025 = ACS 2020-24 + 2025 permits only. Checked on Madison, WI against the raw inputs.
import run_parking_comparison as rpc  # noqa: E402
from missing_middleware.paths import RAW  # noqa: E402
k0 = R.loc[R["name"].eq("Madison") & R["state_fips"].eq("55"), "key"].iloc[0]
acs24 = float(rpc.acs_table(RAW / "census_acs5_2024_tbsf" / "acsdt5y2024-b25002.dat", "B25002_E001")["160|5548000"])
H = pd.read_csv(REFERENCE / "parking_acs_history_homes.csv", dtype={"acs_geoid": str}).query("acs_geoid == '160|5548000'").set_index("year")["homes"]
r25 = R[(R["key"] == k0) & (R["origin"] == 2025)].iloc[0]
out.append(dict(check="added permits stop at origin (Madison, origin 2025)", value=f"{r25.homes - acs24:.0f}",
                note=f"homes(2025) - ACS 2020-24 homes ({acs24:.0f}) should equal 2025 permits ({r25.u4:.0f})"))
for o in (2016, 2019):
    ro = R[(R["key"] == k0) & (R["origin"] == o)].iloc[0]
    out.append(dict(check=f"homes = ACS release ending {o} (Madison)", value=f"{ro.homes - H[o]:.0f}", note=f"should be 0 (ACS {H[o]:.0f})"))
# 5. held-out reform misses by log error; Hartford and Ecorse
M = pd.read_csv(REFERENCE / "parking_net_wi_heldout_reform_r7.csv")
M["log_err"] = np.log((M["pred_on"] + 0.5) / (M["actual"] + 0.5))
top = M.reindex(M["log_err"].abs().sort_values(ascending=False).index).drop_duplicates("key").head(6)
for r in top.itertuples():
    out.append(dict(check="held-out reform miss by log error", value=f"{r.log_err:+.2f}",
                    note=f"{r.name} origin {r.origin} repeal {int(r.reform_year)}: predicted {r.pred_on:.0f}, actual {r.actual:.0f}, same pace {r.units_3y:.0f}, homes {r.homes:.0f}"))
for nm in ("Hartford", "Ecorse"):
    rows = R[R["name"].str.startswith(nm) & R["origin"].between(2014, 2025)]
    for k, g in rows.groupby("key"):
        hist = ", ".join(f"{int(o)}: {u:.0f}" for o, u in zip(g["origin"], g["u4"]))
        out.append(dict(check=f"trace {nm}", value=k, note=f"permits by year {hist}; homes {g['homes'].iloc[-1]:.0f}"))
O = pd.DataFrame(out)
O.to_csv(REFERENCE / "parking_net_wi_audit_checks_r7.csv", index=False)
pd.set_option("display.width", 250); pd.set_option("display.max_colwidth", 200)
print(O.to_string(index=False))
