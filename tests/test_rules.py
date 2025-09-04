from __future__ import annotations

import pandas as pd

from src.rules.predicates import high_value, rapid_fire, geo_velocity, high_risk_mcc, night_owl_cnp


def sample_df():
    return pd.DataFrame({
        "card_id": ["c1", "c1", "c1", "c2"],
        "ts": pd.to_datetime([
            "2024-01-01 00:00",
            "2024-01-01 00:01",
            "2024-01-01 00:03",
            "2024-01-01 10:00",
        ]),
        "amount": [10.0, 2000.0, 5.0, 100.0],
        "lat": [40.0, 40.1, 10.0, 40.0],
        "lon": [-74.0, -74.1, 10.0, -74.0],
        "channel": ["POS", "ECOM", "ECOM", "POS"],
        "mcc": [5411, 7995, 5967, 5732],
    })


def test_high_value():
    df = sample_df()
    mask = high_value(df, amount_threshold=1000)
    assert mask.sum() == 1


def test_rapid_fire():
    df = sample_df()
    mask = rapid_fire(df, tx_per_min_threshold=2, window_minutes=2)
    assert mask.any()


def test_geo_velocity():
    df = sample_df()
    mask = geo_velocity(df, geo_velocity_kmph=500)
    assert mask.iloc[2]  # the jump to lat/lon=10,10 is extreme


def test_high_risk_mcc():
    df = sample_df()
    mask = high_risk_mcc(df, [7995])
    assert mask.sum() == 1


def test_night_owl_cnp():
    df = sample_df()
    mask = night_owl_cnp(df, ["ECOM"], 0, 5)
    assert mask.sum() >= 1

