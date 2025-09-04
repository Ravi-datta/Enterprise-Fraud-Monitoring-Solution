from __future__ import annotations

import base64
import io
import os
from datetime import datetime

import matplotlib.pyplot as plt
import pandas as pd

from src.reporting.kpis import daily_kpis
from src.utils import get_logger


logger = get_logger(__name__)


def _plot_series(df: pd.DataFrame, x: str, y: str) -> str:
    plt.figure(figsize=(8, 3))
    plt.plot(df[x], df[y], marker="o")
    plt.title(y)
    plt.xticks(rotation=45)
    plt.tight_layout()
    buf = io.BytesIO()
    plt.savefig(buf, format="png")
    plt.close()
    return base64.b64encode(buf.getvalue()).decode("utf-8")


def generate_daily_report() -> str:
    df = daily_kpis()
    if df.empty:
        raise RuntimeError("No KPIs found to report.")
    out_dir = os.path.join("reports")
    os.makedirs(out_dir, exist_ok=True)
    today = datetime.utcnow().strftime("%Y-%m-%d")
    path = os.path.join(out_dir, f"report_{today}.md")

    img1 = _plot_series(df.sort_values("date"), "date", "tx_count")
    img2 = _plot_series(df.sort_values("date"), "date", "alerts_count")

    with open(path, "w", encoding="utf-8") as f:
        f.write(f"# Daily Fraud Report — {today}\n\n")
        f.write("## KPIs (last 30 days)\n\n")
        f.write(df.to_markdown(index=False))
        f.write("\n\n")
        f.write("## Transactions\n\n")
        f.write(f"![tx_count](data:image/png;base64,{img1})\n\n")
        f.write("## Alerts\n\n")
        f.write(f"![alerts_count](data:image/png;base64,{img2})\n")
    logger.info("Wrote report to %s", path)
    return path


if __name__ == "__main__":
    print(generate_daily_report())

