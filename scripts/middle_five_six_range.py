"""Post hoc (Ryan, 2026-11-10): 90% range for extra homes in 5-6 unit buildings in Wisconsin, 2027-2031.
Effect draws: Test 1 (M2, four states, reported-only) real rate difference minus fake-set noise (20,000 draws).
Share of 5-6 within 2-6 unit homes: uniform 7.2%-26.6% (law states; FIVE_SIX_UNIT_ESTIMATE.md), or 1.5%-26.6%.
Homes: 1,839,569 single-family homes x 5 years."""
from pathlib import Path
import numpy as np
import pandas as pd

REF = Path(__file__).resolve().parents[1] / "reference"
rng = np.random.default_rng(20261103)
s = pd.read_csv(REF / "middle_test1_summary.csv")
real = s[(s.data.str.startswith("reported")) & (s.measure == "M2") & (s.set == "four states")].iloc[0].real_diff_per_1000
f = pd.read_csv(REF / "middle_test1_fakestates.csv")
f = f[(f.data.str.startswith("reported")) & (f.measure == "M2")]
eff = []
for _ in range(20000):
    used, v = set(), []
    for st in ["Oregon", "California", "Maine", "Vermont"]:
        c = f[(f.windows_of == st) & ~f.fake_state.isin(used)]
        p = c.iloc[int(rng.integers(len(c)))]
        used.add(p.fake_state)
        v.append(p["diff"])
    eff.append(real - np.mean(v))
eff = np.array(eff)
for label, (lo, hi) in {"law states 7.2-26.6%": (0.072, 0.266), "with Wisconsin 1.5%": (0.015, 0.266)}.items():
    sh = rng.uniform(lo, hi, len(eff))
    x = eff * sh / (1 - sh) * 1839.569 * 5
    print(label, [round(np.quantile(x, q)) for q in (0.05, 0.5, 0.95)])
