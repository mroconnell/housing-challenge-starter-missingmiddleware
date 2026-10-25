import numpy as np
import pandas as pd
import pytest

from missing_middleware.comparison import eligible_basis as E


def units():
    return pd.DataFrame({"sf_det": [1000.0], "sf_att": [100.0], "mf2": [40.0], "mf3_4": [35.0], "mf5_9": [70.0],
                         "mf10_19": [145.0], "mf20_49": [345.0], "mf50p": [1000.0], "mobile": [50.0]})


def test_buildings_mid_sizes():
    b = E.buildings(units(), E.SIZES["mid"]).iloc[0]
    assert b["mf2"] == 20 and b["mf3_4"] == 10 and b["mf5_9"] == 10
    assert b["mf10_19"] == 10 and b["mf20_49"] == 10 and b["mf50p"] == 10
    assert b["sf_det"] == 1000 and b["mobile"] == 50


def test_larger_sizes_mean_fewer_properties():
    n = {k: float(E.mf_properties(units(), s).iloc[0]) for k, s in E.SIZES.items()}
    assert n["small"] > n["mid"] > n["large"] > n["very_large"]


def test_eligible_scope_weights():
    u = units()
    assert float(E.eligible(u, {"sf_det": 1.0}, E.SIZES["mid"]).iloc[0]) == 1000
    me = E.eligible(u, E.LAW_SCOPE["ME"][1], E.SIZES["mid"]).iloc[0]
    assert me == pytest.approx(1000 + 100 + 20 + 0.5 * 10)
    # Oregon (detached only) never exceeds California (all multifamily)
    assert E.scenario_eligible(u, "OR", "central").iloc[0] < E.scenario_eligible(u, "CA", "central").iloc[0]
    assert E.scenario_eligible(u, "CA", "low").iloc[0] <= E.scenario_eligible(u, "CA", "central").iloc[0] \
        <= E.scenario_eligible(u, "CA", "high").iloc[0]


def test_every_series_has_a_law_scope():
    for k in list(E.STATE_OF_SERIES.values()) + ["CA", "seattle", "portland", "austin", "denver", "minneapolis"]:
        assert k in E.LAW_SCOPE and len(E.LAW_SCOPE[k]) == 5


def test_site_key_fallback_order():
    par = pd.Series(["123", None, None])
    addr = pd.Series(["1 Main St", "2 Oak  Ave.", None])
    key, basis = E.site_key(par, addr, pd.Series(["a", "b", "c"]))
    assert key.tolist() == ["123", "A:2 OAK AVE", "R:c"]
    assert basis.tolist() == ["parcel", "address", "row"]


def test_flatten_one_permit_per_parcel_year():
    df = pd.DataFrame({"j": ["X"] * 5, "year": [2023, 2023, 2023, 2024, 2024],
                       "site": ["p1", "p1", "p2", "p1", "R:9"], "units": [1, 2, 1, 1, 3]})
    f = E.flatten(df, ["j", "year"]).set_index("year")
    assert f.loc[2023, "units"] == 4 and f.loc[2023, "permits"] == 2
    assert f.loc[2024, "permits"] == 2
    assert f.loc[2023, "units_per_permit"] == 2


def test_capped_events_keeps_two_years_per_parcel():
    df = pd.DataFrame({"juris_name": ["X"] * 4, "year": [2021, 2022, 2023, 2023],
                       "site": ["p1", "p1", "p1", "R:1"]})
    e = E.capped_events(df)
    assert e.set_index(["site", "year"]).loc[("p1", 2023), "keep"] == False  # noqa: E712
    assert e["keep"].sum() == 3


def test_propensity_and_blended_identity():
    p = E.propensity(permits_sf=50, permits_mf=30, props_sf=10_000, props_mf=2_000)
    assert p["rate_sf"] == pytest.approx(5.0) and p["rate_mf"] == pytest.approx(15.0)
    assert p["ratio_mf_to_sf"] == pytest.approx(3.0)
    # recover the single-family rate from the blended rate with the ratio
    assert E.sf_rate_from_blended(p["rate_blended"], 10_000, 2_000, 3.0) == pytest.approx(5.0)
    assert E.sf_rate_from_blended(4.0, 10_000, 2_000, 1.0) == pytest.approx(4.0)


def test_components_from_acs():
    acs = pd.DataFrame({"geoid": ["06037"], "sumlevel": ["050"],
                        **{c: [str(i)] for i, c in enumerate(E.COMPONENTS.values(), start=1)}})
    c = E.components_from_acs(acs)
    assert c["sf_det"].iloc[0] == 1 and c["mobile"].iloc[0] == 9
    assert np.isfinite(c[list(E.COMPONENTS)].to_numpy(float)).all()
