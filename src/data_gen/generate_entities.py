from __future__ import annotations

import random
from datetime import datetime, timedelta
from typing import Tuple

import numpy as np
import pandas as pd
from faker import Faker

from src.utils import get_settings, get_logger, write_df


logger = get_logger(__name__)


def generate_entities(seed: int | None = None) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    cfg = get_settings()
    if seed is None:
        seed = int(cfg["app"]["seed"])
    random.seed(seed)
    np.random.seed(seed)
    fake = Faker()
    Faker.seed(seed)

    n_customers = cfg["generation"]["num_customers"]
    regions = cfg["generation"]["regions"]
    brands = ["VISA", "MASTERCARD", "AMEX", "DISCOVER"]
    statuses = ["ACTIVE", "BLOCKED"]
    merchant_count = cfg["generation"]["merchants"]

    # Accounts
    accounts = []
    now = datetime.utcnow()
    for _ in range(n_customers):
        opened = now - timedelta(days=random.randint(30, 2000))
        accounts.append({
            "opened_at": opened,
            "region": random.choice(regions),
            "risk_score": round(np.clip(np.random.normal(0.2, 0.1), 0, 1) * 100, 2),
        })
    df_accounts = pd.DataFrame(accounts)

    # Cards: Poisson-distributed per account
    cards = []
    for account_idx in range(len(df_accounts)):
        k = max(1, np.random.poisson(cfg["generation"]["cards_per_account_mean"]))
        for _ in range(k):
            exp = now + timedelta(days=random.randint(100, 1200))
            cards.append({
                "account_id": None,  # to be backfilled after insert
                "pan_last4": f"{random.randint(0, 9999):04d}",
                "brand": random.choices(brands, weights=[0.5, 0.3, 0.15, 0.05])[0],
                "exp_date": exp.date(),
                "status": random.choices(statuses, weights=[0.97, 0.03])[0],
            })
    df_cards = pd.DataFrame(cards)

    # Merchants with MCC and risk tiers
    merchants = []
    for i in range(merchant_count):
        merchants.append({
            "name": fake.company(),
            "mcc": int(random.choice([5411, 5732, 5812, 5944, 5967, 7995, 7996, 6051])),
            "country": "US",
            "risk_tier": int(random.choices([1, 2, 3], weights=[0.7, 0.2, 0.1])[0]),
        })
    df_merchants = pd.DataFrame(merchants)

    logger.info("Generated %d accounts, %d cards (pre-link), %d merchants", len(df_accounts), len(df_cards), len(df_merchants))
    return df_accounts, df_cards, df_merchants


def seed_entities_to_db() -> None:
    """Create base entities into DB and link foreign keys after insert."""
    accounts, cards, merchants = generate_entities()
    # Insert accounts, get back ids
    write_df(accounts, "accounts")
    # Fetch ids to backfill account_id in cards
    from src.utils import read_sql
    accounts_db = read_sql("SELECT account_id FROM accounts ORDER BY opened_at LIMIT :n", {"n": len(accounts)})
    cards["account_id"] = np.random.choice(accounts_db["account_id"].values, size=len(cards))
    write_df(cards, "cards")
    write_df(merchants, "merchants")
    logger.info("Seeded entities to DB")

