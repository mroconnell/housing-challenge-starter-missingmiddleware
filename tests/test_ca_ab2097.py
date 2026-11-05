"""Synthetic checks for the CA AB 2097 estimate helpers (scripts/ca_ab2097_estimate.py). No real data."""
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))

import ca_ab2097_estimate as E  # noqa: E402


def _toy(effect: float = 2.0):
    """Two jurisdictions; near and ring each 1,000 homes; 10 homes a year everywhere, plus `effect` per 1,000 homes a
    year near transit from 2023."""
    cells = pd.DataFrame([{"juris": j, "upz": False, "zone": z, "homes": 1000.0, "acres": 100.0}
                          for j in ("A", "B") for z in ("near", "ring")])
    rows = []
    for j in ("A", "B"):
        for y in E.YEARS:
            for z in ("near", "ring"):
                u = 10.0 + (effect if (z == "near" and y >= 2023) else 0.0)
                rows.append({"juris": j, "project": f"{j}{y}{z}", "year": y, "zone": z, "upz": False,
                             "homes_non_adu": u})
    return cells, pd.DataFrame(rows)


def test_event_study_and_headline_recover_effect():
    cells, permits = _toy(2.0)
    g = E.group("main", ["A", "B"])
    est, dr = E.event_study(g, cells, permits, "homes_non_adu", draws=50)
    assert np.allclose(est[:5], 0.0)            # leads, relative to 2022
    assert np.allclose(est[5:], 2.0)            # 2 homes per 1,000 existing homes a year after
    e, d = E.period_contrast(est, dr, E.BEFORE, E.AFTER)
    assert abs(e - 2.0) < 1e-9 and np.allclose(d, 2.0)
    s, sd = E.lead_slope(est, dr)
    assert abs(s) < 1e-9


def test_equal_weight_matches_pooled_when_equal():
    cells, permits = _toy(3.0)
    g = E.group("main", ["A", "B"])
    e, _ = E.equal_weight(g, cells, permits, "homes_non_adu", draws=20)
    assert abs(e - 3.0) < 1e-9


def test_zones_of_edge_donut():
    d = np.array([E.MILE / 2 - 10, E.MILE / 2 - 30, E.MILE / 2 + 30, E.MILE / 2 + 10])
    z = E.zones_of(d)["edge"]
    assert list(z) == ["other", "inside", "outside", "other"]
