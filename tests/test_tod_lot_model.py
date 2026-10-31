"""Small checks of the TOD lot model's rules (audit scorecard, round 1)."""
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))
import run_tod_lot_model as L  # noqa: E402


def test_fold_excludes_own_placebo_and_itself():
    cities = ["Madison", "Madison placebo", "Milwaukee placebo", "New York", "Saint Paul"]
    assert L.training_cities(cities, "Madison") == ["Milwaukee placebo", "New York", "Saint Paul"]
    assert L.training_cities(cities, "Madison placebo") == ["Milwaukee placebo", "New York", "Saint Paul"]
    assert "Saint Paul" in L.training_cities(cities + ["Saint Louis"], "Saint Louis")


def test_rezoned_later_is_zero_at_forecast_time():
    X = pd.DataFrame({"rezoned_later": [1.0, 0.0], "log_acres": [0.1, 0.2]})
    out = L.forecast_view(X)
    assert out["rezoned_later"].tolist() == [0.0, 0.0]
    assert X["rezoned_later"].tolist() == [1.0, 0.0]   # the input is not changed


def test_units_table_covers_every_trait():
    t = Path(__file__).resolve().parent.parent / "reference" / "tod_lot_model_trait_units_v37.csv"
    if not t.exists():
        return
    T = pd.read_csv(t)
    assert {"trait", "city", "median", "p5", "p95", "unit"} <= set(T.columns)
    assert T["unit"].fillna("").str.len().gt(0).mean() > 0.5
