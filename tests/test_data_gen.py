from __future__ import annotations

from src.data_gen.generate_entities import generate_entities
from src.data_gen.inject_fraud_patterns import inject_fraud


def test_generate_entities_shapes():
    accounts, cards, merchants = generate_entities(seed=123)
    assert len(accounts) > 100
    assert len(cards) > len(accounts)
    assert len(merchants) > 100


def test_inject_fraud_shapes():
    import pandas as pd
    df = pd.DataFrame({
        "card_id": ["c1"] * 10,
        "merchant_id": ["m1"] * 10,
        "ts": pd.date_range("2024-01-01", periods=10, freq="H"),
        "amount": [10.0] * 10,
        "currency": ["USD"] * 10,
        "lat": [40.0] * 10,
        "lon": [-74.0] * 10,
        "channel": ["POS"] * 10,
        "device_id": ["d1"] * 10,
        "is_international": [False] * 10,
        "label_fraud": [None] * 10,
    })
    out = inject_fraud(df, fraud_ratio=0.2, seed=42)
    assert "label_fraud" in out.columns
    assert out["label_fraud"].sum() >= 1
