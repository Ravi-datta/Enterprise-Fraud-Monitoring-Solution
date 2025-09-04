from __future__ import annotations

import pandas as pd


def high_value(df: pd.DataFrame, amount_threshold: float) -> pd.Series:
    return df["amount"].astype(float) >= float(amount_threshold)


def rapid_fire(df: pd.DataFrame, tx_per_min_threshold: int, window_minutes: int) -> pd.Series:
    g = df.sort_values("ts").groupby("card_id", group_keys=False)
    counts = g["ts"].rolling(f"{int(window_minutes)}min").count().reset_index(level=0, drop=True)
    return (counts - 1) >= int(tx_per_min_threshold)


def geo_velocity(df: pd.DataFrame, geo_velocity_kmph: float) -> pd.Series:
    g = df.sort_values("ts").groupby("card_id", group_keys=False)
    lat_prev = g["lat"].shift(1)
    lon_prev = g["lon"].shift(1)
    dt_hours = df["ts"].sort_values().groupby(df["card_id"]).diff().dt.total_seconds().div(3600)
    dist_km = _haversine_km(lat_prev, lon_prev, df["lat"], df["lon"]).fillna(0.0)
    speed = (dist_km / dt_hours.replace(0, pd.NA)).fillna(0.0)
    return speed >= float(geo_velocity_kmph)


def high_risk_mcc(df: pd.DataFrame, high_risk_mcc: list[int]) -> pd.Series:
    return df["mcc"].astype(int).isin([int(x) for x in high_risk_mcc])


def night_owl_cnp(df: pd.DataFrame, cnp_channels: list[str], start_hour: int, end_hour: int) -> pd.Series:
    hours = pd.to_datetime(df["ts"]).dt.hour
    cnp = df["channel"].isin(cnp_channels)
    return cnp & (hours >= int(start_hour)) & (hours < int(end_hour))


def _haversine_km(lat1, lon1, lat2, lon2):
    import numpy as np
    lat1 = pd.to_numeric(lat1, errors="coerce").astype(float)
    lon1 = pd.to_numeric(lon1, errors="coerce").astype(float)
    lat2 = pd.to_numeric(lat2, errors="coerce").astype(float)
    lon2 = pd.to_numeric(lon2, errors="coerce").astype(float)
    lat1 = np.radians(lat1)
    lon1 = np.radians(lon1)
    lat2 = np.radians(lat2)
    lon2 = np.radians(lon2)
    dlat = lat2 - lat1
    dlon = lon2 - lon1
    a = np.sin(dlat / 2) ** 2 + np.cos(lat1) * np.cos(lat2) * np.sin(dlon / 2) ** 2
    c = 2 * np.arcsin(np.sqrt(a))
    return 6371 * c

