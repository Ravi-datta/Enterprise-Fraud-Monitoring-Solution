from __future__ import annotations

import numpy as np
import pandas as pd

from src.utils import get_logger, read_sql, write_df


logger = get_logger(__name__)


def _features_for_group(g: pd.DataFrame) -> pd.DataFrame:
    g = g.sort_values("ts")
    g["last_tx_delta_minutes"] = g["ts"].diff().dt.total_seconds().div(60).fillna(1e6)
    # Rolling counts by time windows using pandas time-based rolling
    g = g.set_index("ts")
    g["tx_count_1h"] = g["amount"].rolling("1h").count().astype(int) - 1
    g["tx_count_24h"] = g["amount"].rolling("24h").count().astype(int) - 1
    g["amount_mean_24h"] = g["amount"].rolling("24h").mean().fillna(0.0)
    # Geo velocity vs previous point approx
    lat_prev = g["lat"].shift(1)
    lon_prev = g["lon"].shift(1)
    dt_hours = g.index.to_series().diff().dt.total_seconds().div(3600)
    dist_km = _haversine_km(lat_prev, lon_prev, g["lat"], g["lon"]).fillna(0.0)
    g["geo_velocity_kmph_prev"] = (dist_km / dt_hours.replace(0, np.nan)).fillna(0.0)
    return g.reset_index()


def _haversine_km(lat1, lon1, lat2, lon2):
    # Vectorized Haversine distance
    lat1 = np.radians(lat1.astype(float))
    lon1 = np.radians(lon1.astype(float))
    lat2 = np.radians(lat2.astype(float))
    lon2 = np.radians(lon2.astype(float))
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    a = np.sin(dlat / 2) ** 2 + np.cos(lat1) * np.cos(lat2) * np.sin(dlon / 2) ** 2
    c = 2 * np.arcsin(np.sqrt(a))
    return 6371 * c


def build_features() -> int:
    q = """
        SELECT t.tx_id, t.card_id, t.merchant_id, t.ts, t.amount::float, t.currency, t.lat, t.lon,
               t.channel, t.device_id, t.label_fraud, c.brand, m.risk_tier AS merchant_risk_tier
        FROM transactions t
        JOIN cards c ON c.card_id = t.card_id
        JOIN merchants m ON m.merchant_id = t.merchant_id
    """
    df = read_sql(q)
    if df.empty:
        logger.warning("No transactions to build features from.")
        return 0
    df["ts"] = pd.to_datetime(df["ts"])
    # Compute per-card rolling features
    df_feat = (
        df.groupby("card_id", group_keys=False)
        .apply(_features_for_group)
        .reset_index(drop=True)
    )
    # Select columns for model_features table
    cols = [
        "tx_id",
        "label_fraud",
        "amount",
        "last_tx_delta_minutes",
        "tx_count_1h",
        "tx_count_24h",
        "amount_mean_24h",
        "geo_velocity_kmph_prev",
        "channel",
        "device_id",
        "merchant_risk_tier",
        "brand",
        "ts",
    ]
    df_out = df_feat[cols].copy()
    write_df(df_out, "model_features", if_exists="append")
    return len(df_out)

