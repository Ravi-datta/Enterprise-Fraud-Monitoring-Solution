from __future__ import annotations

import pandas as pd

from src.utils import get_logger, read_sql


logger = get_logger(__name__)


def daily_kpis() -> pd.DataFrame:
    q = "SELECT * FROM vw_daily_kpis ORDER BY date DESC LIMIT 30"
    df = read_sql(q)
    logger.info("Loaded %d days of KPIs", len(df))
    return df

