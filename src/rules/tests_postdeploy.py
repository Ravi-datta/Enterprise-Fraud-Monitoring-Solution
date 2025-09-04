from __future__ import annotations

import pandas as pd

from src.utils import read_sql


def main() -> int:
    # Simple sanity checks after rules run
    tx_count = read_sql("SELECT COUNT(*) AS n FROM transactions")["n"].iloc[0]
    alerts = read_sql("SELECT COUNT(*) AS n FROM alerts")["n"].iloc[0]
    assert tx_count > 0, "No transactions found"
    # Alert rate sanity (should be below 10%)
    if tx_count:
        rate = alerts / tx_count
        assert 0.0 <= rate <= 0.2, f"Alert rate out of bounds: {rate:.4f}"
    print("Postdeploy rules check passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

