from __future__ import annotations

import math
import random
from datetime import datetime, timedelta
from typing import Tuple

import numpy as np
import pandas as pd

from src.utils import get_settings, get_logger, read_sql, write_df


logger = get_logger(__name__)


def _diurnal_weight(dt: datetime) -> float:
    # Higher during 10am-8pm, lower at night
    hour = dt.hour
    base = 0.2 + 0.8 * (1 - abs((hour - 15) / 10))
    return max(0.05, min(1.0, base))


def _random_walk(base_lat: float, base_lon: float) -> Tuple[float, float]:
    dlat = np.random.normal(0, 0.05)
    dlon = np.random.normal(0, 0.05)
    return base_lat + dlat, base_lon + dlon


def generate_transactions(days: int = 1, tx_per_day: int = 50_000, seed: int | None = None) -> pd.DataFrame:
    cfg = get_settings()
    if seed is None:
        seed = int(cfg["app"]["seed"])
    random.seed(seed)
    np.random.seed(seed)

    # Fetch supporting entities
    cards = read_sql("SELECT card_id, brand FROM cards")
    merchants = read_sql("SELECT merchant_id, mcc, risk_tier FROM merchants")
    if cards.empty or merchants.empty:
        raise RuntimeError("No cards or merchants found. Run `python -m src.cli seed` first.")

    channels = cfg["generation"]["tx_channels"]
    now = datetime.utcnow()
    start_day = now - timedelta(days=days)

    txs = []
    # Assign a home base for each card
    card_home = {cid: (np.random.uniform(25, 49), np.random.uniform(-124, -67)) for cid in cards["card_id"].values}

    for d in range(days):
        day = start_day + timedelta(days=d)
        for i in range(tx_per_day):
            ts = day + timedelta(seconds=random.randint(0, 86400))
            # weight sampling for diurnal pattern
            if random.random() > _diurnal_weight(ts):
                continue
            card = cards.sample(1).iloc[0]
            merch = merchants.sample(1).iloc[0]
            base_lat, base_lon = card_home[card.card_id]
            lat, lon = _random_walk(base_lat, base_lon)
            channel = random.choices(channels, weights=[0.6, 0.35, 0.05])[0]
            amount = float(max(1.0, np.random.lognormal(mean=3.5, sigma=0.7)))
            is_international = random.random() < 0.05
            txs.append({
                "card_id": card.card_id,
                "merchant_id": merch.merchant_id,
                "ts": ts,
                "amount": round(amount, 2),
                "currency": "USD",
                "lat": lat,
                "lon": lon,
                "channel": channel,
                "device_id": f"dev_{random.randint(1, 150000)}",
                "is_international": is_international,
                "label_fraud": None,
            })

    df = pd.DataFrame(txs)
    logger.info("Generated %d raw transactions", len(df))
    return df


def write_transactions(days: int, tx_per_day: int) -> int:
    df = generate_transactions(days=days, tx_per_day=tx_per_day)
    if df.empty:
        logger.warning("No transactions generated for days=%s tx_per_day=%s", days, tx_per_day)
        return 0
    write_df(df, "transactions")
    return len(df)

