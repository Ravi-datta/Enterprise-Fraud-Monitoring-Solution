from __future__ import annotations

import json
import os
from datetime import datetime
from typing import Tuple

import joblib
import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import classification_report
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler

from src.utils import get_logger
from .preprocessing import Dataset, load_feature_table, time_split


logger = get_logger(__name__)


def build_pipeline(numeric: list[str], categorical: list[str], algo: str = "rf") -> Pipeline:
    transformers = []
    if numeric:
        transformers.append(("num", StandardScaler(with_mean=False), numeric))
    if categorical:
        transformers.append(("cat", OneHotEncoder(handle_unknown="ignore"), categorical))
    pre = ColumnTransformer(transformers)

    if algo == "lr":
        clf = LogisticRegression(max_iter=200, class_weight="balanced")
    elif algo == "rf":
        clf = RandomForestClassifier(n_estimators=200, max_depth=8, min_samples_leaf=5, class_weight="balanced", n_jobs=-1)
    elif algo == "xgb":
        try:
            import xgboost as xgb  # type: ignore
        except Exception:
            raise RuntimeError("XGBoost not installed. Install xgboost to use --algo xgb.")
        clf = xgb.XGBClassifier(n_estimators=300, max_depth=6, learning_rate=0.1, subsample=0.8, colsample_bytree=0.8, n_jobs=-1, eval_metric="logloss")
    else:
        raise ValueError(f"Unknown algo: {algo}")

    pipe = Pipeline([("pre", pre), ("clf", clf)])
    return pipe


def train(algo: str = "rf", model_dir: str = "artifacts/models") -> tuple[str, str]:
    from src.utils import get_settings
    cfg = get_settings()
    model_cfg = cfg.get("ml", {})
    os.makedirs(model_dir, exist_ok=True)

    df = load_feature_table()
    if df.empty:
        raise RuntimeError("No features to train on. Run `python -m src.cli features` first.")

    # Use config/model.yaml for feature list
    model_yaml = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "config", "model.yaml")
    with open(model_yaml, "r", encoding="utf-8") as f:
        spec = json.loads(json.dumps(__import__("yaml").safe_load(f)))
    target = spec.get("target", "label_fraud")
    numeric = spec["features"].get("numeric", [])
    categorical = spec["features"].get("categorical", [])

    ds: Dataset = time_split(df, target=target, val_days=int(spec.get("split", {}).get("val_days", 7)))

    pipe = build_pipeline(numeric, categorical, algo)
    pipe.fit(ds.X_train, ds.y_train)
    y_pred = pipe.predict(ds.X_val)
    y_proba = None
    try:
        y_proba = pipe.predict_proba(ds.X_val)[:, 1]
    except Exception:
        pass
    logger.info("Validation report:\n%s", classification_report(ds.y_val, y_pred))

    ts = datetime.utcnow().strftime("%Y%m%d%H%M%S")
    model_name = f"{spec.get('model', {}).get('algo', algo)}_{ts}.joblib"
    model_path = os.path.join(model_dir, model_name)
    joblib.dump({"pipeline": pipe, "numeric": numeric, "categorical": categorical, "target": target}, model_path)
    feat_list_path = os.path.join(model_dir, "feature_list.json")
    with open(feat_list_path, "w", encoding="utf-8") as f:
        json.dump({"numeric": numeric, "categorical": categorical}, f, indent=2)
    logger.info("Saved model to %s", model_path)
    return model_path, feat_list_path


if __name__ == "__main__":
    train()

