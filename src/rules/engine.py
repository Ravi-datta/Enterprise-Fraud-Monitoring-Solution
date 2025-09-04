from __future__ import annotations

import json
import os
from typing import Callable, Dict

import pandas as pd
import yaml

from src.utils import get_logger, read_sql, write_df
from . import predicates as P


logger = get_logger(__name__)


def load_rules() -> list[dict]:
    cfg_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "config", "rules.yaml")
    with open(cfg_path, "r", encoding="utf-8") as f:
        rules = yaml.safe_load(f).get("rules", [])
    return rules


def _get_predicate(name: str) -> Callable[..., pd.Series]:
    if not hasattr(P, name):
        raise ValueError(f"Unknown rule predicate: {name}")
    return getattr(P, name)


def score_rules(limit_days: int | None = 2) -> int:
    rules = [r for r in load_rules() if r.get("active", True)]
    if not rules:
        logger.warning("No active rules found.")
        return 0

    q = """
        SELECT t.tx_id, t.card_id, t.merchant_id, t.ts, t.amount::float, t.lat, t.lon, t.channel,
               m.mcc, m.risk_tier
        FROM transactions t
        JOIN merchants m ON m.merchant_id = t.merchant_id
        WHERE t.ts >= NOW() - INTERVAL ':days days'
    """
    if limit_days is None:
        df = read_sql("""
            SELECT t.tx_id, t.card_id, t.merchant_id, t.ts, t.amount::float, t.lat, t.lon, t.channel,
                   m.mcc, m.risk_tier
            FROM transactions t
            JOIN merchants m ON m.merchant_id = t.merchant_id
        """)
    else:
        df = read_sql(q, {"days": int(limit_days)})
    if df.empty:
        logger.warning("No transactions to score.")
        return 0
    df["ts"] = pd.to_datetime(df["ts"])  # ensure datetime

    alerts_to_write = []
    for rule in rules:
        name = rule["name"]
        params = rule.get("params", {})
        pred = _get_predicate(name)
        try:
            mask = pred(df, **params)
        except TypeError as e:
            raise RuntimeError(f"Invalid params for rule {name}: {e}")
        flagged = df[mask]
        logger.info("Rule %s flagged %d / %d", name, len(flagged), len(df))
        for _, row in flagged.iterrows():
            alerts_to_write.append({
                "tx_id": row["tx_id"],
                "rule_name": name,
                "score": 1.0,
            })

    if not alerts_to_write:
        logger.info("No alerts generated.")
        return 0
    write_df(pd.DataFrame(alerts_to_write), "alerts")
    return len(alerts_to_write)

