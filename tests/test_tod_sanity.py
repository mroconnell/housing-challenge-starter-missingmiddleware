import pandas as pd

from missing_middleware.tod import sanity as S


def test_policy_flag_catches_far_upzoned_lot():
    D = pd.DataFrame({"city": ["A", "A", "B"], "treated": [1, 1, 1], "dist_station_m": [100, 96000, 200]})
    F = S.policy_flags(D)
    assert list(F[0].values())[:2] == ["policy", "A"] and len(F) == 1


def test_unit_flag_catches_height_read_as_far():
    D = pd.DataFrame({"city": ["C", "C"], "far_before": [40.0, 75.0]})
    assert any(f["item"] == "far_before" for f in S.unit_flags(D, far_cities=("C",)))


def test_range_flag_catches_unseen_city():
    X = pd.DataFrame({"d": [1.0, 2, 3, 1, 2, 3, 100, 101]})
    city = pd.Series(list("AAABBBMM"))
    assert "M" in [f["city"] for f in S.range_flags(X, city)]
