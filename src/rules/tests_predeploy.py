from __future__ import annotations

import os
import yaml
import pandas as pd

from .engine import load_rules, _get_predicate


def _sample_df() -> pd.DataFrame:
    return pd.DataFrame({
        "tx_id": [1, 2, 3],
        "card_id": ["c1", "c1", "c2"],
        "merchant_id": ["m1", "m2", "m3"],
        "ts": pd.to_datetime(["2024-01-01 00:10", "2024-01-01 00:11", "2024-01-01 13:00"]),
        "amount": [50.0, 5000.0, 10.0],
        "lat": [40.0, 41.0, 0.0],
        "lon": [-74.0, -75.0, 0.0],
        "channel": ["POS", "ECOM", "ECOM"],
        "mcc": [5411, 7995, 5967],
    })


def main() -> int:
    rules = load_rules()
    assert isinstance(rules, list) and rules, "rules.yaml must contain a non-empty 'rules' list"
    # Validate syntax
    for r in rules:
        assert "name" in r and "params" in r, f"Invalid rule spec: {r}"
        _ = _get_predicate(r["name"])  # should not raise
    # Dry run
    df = _sample_df()
    for r in rules:
        pred = _get_predicate(r["name"]) 
        _ = pred(df, **r.get("params", {}))
    print("Predeploy rules check passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

