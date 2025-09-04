from __future__ import annotations

import glob
import os
from datetime import datetime, timedelta

import joblib
import pandas as pd

from src.utils import get_logger, read_sql, write_df, get_settings


logger = get_logger(__name__)


def _latest_model(model_dir: str = "artifacts/models") -> str:
    paths = glob.glob(os.path.join(model_dir, "*.joblib"))
    if not paths:
        raise FileNotFoundError("No models found in artifacts/models. Train one first.")
    return sorted(paths)[-1]


def predict_and_store(threshold: float | None = None) -> int:
    cfg = get_settings()
    if threshold is None:
        threshold = float(cfg["app"]["alert_threshold"])
    model_path = _latest_model(cfg["ml"]["model_dir"])
    bundle = joblib.load(model_path)
    pipe = bundle["pipeline"]

    # Score last 1 day features
    df = read_sql("SELECT * FROM model_features WHERE ts >= NOW() - INTERVAL '1 day'")
    if df.empty:
        logger.warning("No features to score in last day.")
        return 0
    X = df.drop(columns=["label_fraud", "tx_id", "ts"])  # keep align with training
    proba = pipe.predict_proba(X)[:, 1]
    preds = (proba >= threshold)
    rows = []
    for tx_id, p, pred in zip(df["tx_id"].values, proba, preds):
        rows.append({
            "tx_id": tx_id,
            "model_name": os.path.basename(model_path),
            "proba": float(p),
            "predicted_label": bool(pred),
        })
    write_df(pd.DataFrame(rows), "model_scores")
    logger.info("Wrote %d model scores", len(rows))
    return len(rows)


if __name__ == "__main__":
    predict_and_store()

