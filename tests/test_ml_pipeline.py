from __future__ import annotations

import pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder
from sklearn.compose import ColumnTransformer

from src.ml.train import build_pipeline


def test_build_pipeline_lr():
    pipe = build_pipeline(numeric=["a"], categorical=["b"], algo="lr")
    assert isinstance(pipe, Pipeline)


def test_pipeline_fit_predict():
    X = pd.DataFrame({"a": [0.1, 1.2, 0.5, 3.0], "b": ["x", "y", "x", "z"]})
    y = pd.Series([0, 1, 0, 1])
    pipe = build_pipeline(numeric=["a"], categorical=["b"], algo="lr")
    pipe.fit(X, y)
    proba = pipe.predict_proba(X)[:, 1]
    assert len(proba) == len(X)

