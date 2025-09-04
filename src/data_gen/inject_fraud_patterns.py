from __future__ import annotations

import random
from datetime import timedelta
from typing import Tuple

import numpy as np
import pandas as pd

from src.utils import get_settings, get_logger


logger = get_logger(__name__)


def inject_fraud(df: pd.DataFrame, fraud_ratio: float | None = None, seed: int | None = None) -> pd.DataFrame:
    """Inject simple fraud patterns in-place and return the modified DataFrame.

    Patterns:
    - High-value single spike
    - Rapid-fire micro-transactions
    - Geo-velocity impossible travel
    - Merchant high-risk tier spikes
    - Night-owl CNP burst
    """
    cfg = get_settings()
    if seed is None:
        seed = int(cfg["app"]["seed"])
    random.seed(seed)
    np.random.seed(seed)
    if fraud_ratio is None:
        fraud_ratio = float(cfg["generation"]["fraud_ratio"])

    n = len(df)
    k = max(1, int(n * fraud_ratio))
    idx = df.sample(k, random_state=seed).index
    df.loc[idx, "label_fraud"] = True

    # High value spikes
    hv_idx = idx[: max(1, k // 5)]
    df.loc[hv_idx, "amount"] = df.loc[hv_idx, "amount"].astype(float) * np.random.uniform(10, 30)

    # Rapid fire: create additional tiny transactions near a selected tx
    rf_idx = idx[max(1, k // 5) : max(1, (2 * k) // 5)]
    for i in rf_idx:
        base = df.loc[i]
        for j in range(random.randint(2, 5)):
            row = base.copy()
            row["ts"] = base["ts"] + timedelta(seconds=random.randint(5, 45))
            row["amount"] = round(float(np.random.uniform(0.5, 2.5)), 2)
            df = pd.concat([df, pd.DataFrame([row])], ignore_index=True)

    # Geo velocity: move far away instantly
    gv_idx = idx[max(1, (2 * k) // 5) : max(1, (3 * k) // 5)]
    df.loc[gv_idx, ["lat", "lon"]] = [
        np.random.uniform(-40, 55),
        np.random.uniform(100, 140),
    ]

    # High risk merchant: simulate by extreme amounts
    hr_idx = idx[max(1, (3 * k) // 5) : max(1, (4 * k) // 5)]
    df.loc[hr_idx, "amount"] = df.loc[hr_idx, "amount"].astype(float) * np.random.uniform(5, 15)

    # Night owl CNP burst
    no_idx = idx[max(1, (4 * k) // 5) :]
    df.loc[no_idx, "channel"] = "ECOM"
    df.loc[no_idx, "ts"] = pd.to_datetime(df.loc[no_idx, "ts"]).dt.floor("D") + pd.to_timedelta(np.random.randint(0, 5, size=len(no_idx)), unit="h")

    logger.info("Injected fraud patterns into %d base txs -> %d rows total", k, len(df))
    return df

