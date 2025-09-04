from __future__ import annotations

import json
import os
from typing import Dict

import matplotlib.pyplot as plt
import numpy as np
from sklearn.calibration import calibration_curve
from sklearn.metrics import (
    ConfusionMatrixDisplay,
    PrecisionRecallDisplay,
    RocCurveDisplay,
    average_precision_score,
    confusion_matrix,
    f1_score,
    precision_recall_curve,
    precision_score,
    roc_auc_score,
)


def compute_and_plot(y_true, y_proba, out_dir: str) -> Dict[str, float]:
    os.makedirs(out_dir, exist_ok=True)
    y_pred = (y_proba >= 0.5).astype(int)

    metrics = {
        "precision": float(precision_score(y_true, y_pred, zero_division=0)),
        "recall": float(
            np.sum((y_pred == 1) & (y_true == 1)) / max(1, np.sum(y_true == 1))
        ),
        "f1": float(f1_score(y_true, y_pred, zero_division=0)),
        "roc_auc": float(roc_auc_score(y_true, y_proba)),
        "pr_auc": float(average_precision_score(y_true, y_proba)),
    }

    # ROC
    RocCurveDisplay.from_predictions(y_true, y_proba)
    plt.title("ROC Curve")
    plt.savefig(os.path.join(out_dir, "roc_curve.png"), bbox_inches="tight")
    plt.close()

    # PR
    PrecisionRecallDisplay.from_predictions(y_true, y_proba)
    plt.title("Precision-Recall Curve")
    plt.savefig(os.path.join(out_dir, "pr_curve.png"), bbox_inches="tight")
    plt.close()

    # Confusion matrix at 0.5
    cm = confusion_matrix(y_true, y_pred)
    disp = ConfusionMatrixDisplay(confusion_matrix=cm)
    disp.plot()
    plt.title("Confusion Matrix (0.5)")
    plt.savefig(os.path.join(out_dir, "confusion_matrix.png"), bbox_inches="tight")
    plt.close()

    # Calibration
    frac_pos, mean_pred = calibration_curve(y_true, y_proba, n_bins=10)
    plt.plot(mean_pred, frac_pos, marker="o")
    plt.plot([0, 1], [0, 1], linestyle="--", color="gray")
    plt.title("Calibration Curve")
    plt.xlabel("Mean predicted value")
    plt.ylabel("Fraction of positives")
    plt.savefig(os.path.join(out_dir, "calibration.png"), bbox_inches="tight")
    plt.close()

    with open(os.path.join(out_dir, "metrics.json"), "w", encoding="utf-8") as f:
        json.dump(metrics, f, indent=2)
    return metrics

