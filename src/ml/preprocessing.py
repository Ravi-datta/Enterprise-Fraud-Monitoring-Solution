from __future__ import annotations

from dataclasses import dataclass
from typing import List, Tuple

import pandas as pd
from sklearn.model_selection import train_test_split

from src.utils import get_logger, read_sql


logger = get_logger(__name__)


@dataclass
class Dataset:
    X_train: pd.DataFrame
    X_val: pd.DataFrame
    y_train: pd.Series
    y_val: pd.Series
    feature_cols: List[str]


def load_feature_table() -> pd.DataFrame:
    return read_sql("SELECT * FROM model_features")


def time_split(df: pd.DataFrame, target: str, val_days: int = 7) -> Dataset:
    df = df.sort_values("ts")
    cutoff = df["ts"].max() - pd.Timedelta(days=val_days)
    train = df[df["ts"] <= cutoff]
    val = df[df["ts"] > cutoff]
    y_train = train[target].astype(int).fillna(0)
    y_val = val[target].astype(int).fillna(0)
    X_train = train.drop(columns=[target, "tx_id", "ts"])  # drop ids
    X_val = val.drop(columns=[target, "tx_id", "ts"])  # drop ids
    return Dataset(X_train, X_val, y_train, y_val, X_train.columns.tolist())


def mixed_dtypes_to_numeric(df: pd.DataFrame, categorical: list[str]) -> pd.DataFrame:
    df = df.copy()
    for col in df.columns:
        if col in categorical:
            df[col] = df[col].astype("category")
        elif df[col].dtype == "bool":
            df[col] = df[col].astype(int)
        else:
            df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0)
    return df

