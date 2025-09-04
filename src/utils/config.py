from __future__ import annotations

import os
from functools import lru_cache
from typing import Any, Dict

import yaml
from dotenv import load_dotenv


def _env_expand(value: str) -> str:
    if value is None:
        return value
    return os.path.expandvars(str(value))


@lru_cache()
def get_settings() -> Dict[str, Any]:
    """Load settings from config/settings.yaml with ${ENV} expansion and defaults.

    Environment variables are loaded from a local .env if present.
    DATABASE_URL overrides database section if set.
    """
    load_dotenv()
    cfg_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "config", "settings.yaml")
    with open(cfg_path, "r", encoding="utf-8") as f:
        raw = yaml.safe_load(f)

    # Expand environment variables inside values
    def expand(node):
        if isinstance(node, dict):
            return {k: expand(v) for k, v in node.items()}
        if isinstance(node, list):
            return [expand(v) for v in node]
        if isinstance(node, str):
            return _env_expand(node)
        return node

    cfg = expand(raw)

    # Assemble database URL
    db = cfg.get("database", {})
    url_env = os.getenv("DATABASE_URL")
    if url_env:
        cfg["database"]["url"] = url_env
    else:
        driver = db.get("driver", "postgresql+psycopg2")
        user = db.get("user")
        password = db.get("password")
        host = db.get("host")
        port = db.get("port")
        name = db.get("db")
        cfg["database"]["url"] = f"{driver}://{user}:{password}@{host}:{port}/{name}"

    # Normalize ints/floats
    try:
        cfg["app"]["batch_size"] = int(cfg["app"].get("batch_size", 5000))
        cfg["app"]["alert_threshold"] = float(cfg["app"].get("alert_threshold", 0.9))
    except Exception:
        pass

    return cfg

