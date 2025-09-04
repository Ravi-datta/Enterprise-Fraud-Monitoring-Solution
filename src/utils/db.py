from __future__ import annotations

from functools import lru_cache
from typing import Any, Optional

import pandas as pd
from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine

from .config import get_settings
from .logging import get_logger


logger = get_logger(__name__)


@lru_cache()
def get_engine() -> Engine:
    cfg = get_settings()
    url = cfg["database"]["url"]
    engine = create_engine(url, pool_pre_ping=True, future=True)
    logger.info("Connected engine to %s", url)
    return engine


def read_sql(query: str, params: Optional[dict[str, Any]] = None) -> pd.DataFrame:
    eng = get_engine()
    with eng.connect() as con:
        df = pd.read_sql(text(query), con, params=params)
    return df


def write_df(df: pd.DataFrame, table: str, if_exists: str = "append", index: bool = False, chunksize: Optional[int] = None) -> None:
    eng = get_engine()
    if chunksize is None:
        chunksize = get_settings()["app"]["batch_size"]
    with eng.begin() as con:
        df.to_sql(table, con, if_exists=if_exists, index=index, chunksize=chunksize, method="multi")
    logger.info("Wrote %d rows to %s", len(df), table)

