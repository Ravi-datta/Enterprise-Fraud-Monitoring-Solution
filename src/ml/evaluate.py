from __future__ import annotations

import os
import joblib
import numpy as np

from src.utils import get_logger
from .preprocessing import load_feature_table, time_split
from .metrics import compute_and_plot


logger = get_logger(__name__)


def evaluate(model_path: str, out_dir: str = "artifacts/plots") -> None:
    df = load_feature_table()
    if df.empty:
        raise RuntimeError("No features to evaluate.")
    y_col = "label_fraud"
    ds = time_split(df, target=y_col)
    model = joblib.load(model_path)["pipeline"]
    y_proba = model.predict_proba(ds.X_val)[:, 1]
    os.makedirs(out_dir, exist_ok=True)
    compute_and_plot(ds.y_val.values, y_proba, out_dir)
    logger.info("Saved evaluation plots and metrics to %s", out_dir)


if __name__ == "__main__":
    evaluate("artifacts/models/latest.joblib")

