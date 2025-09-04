from __future__ import annotations

from datetime import datetime
import pytz

from .config import get_settings


def localize_ts(ts: datetime) -> datetime:
    tzname = get_settings()["app"]["timezone"]
    tz = pytz.timezone(tzname)
    if ts.tzinfo is None:
        return tz.localize(ts)
    return ts.astimezone(tz)

