"""YouTube API quota tracking.

Port of server/src/lib/quota-tracker.ts.

search.list = 100 units, videos.list = 1 unit, channels.list = 1 unit.
Default daily limit: 10,000 units. Resets at the start of a new UTC day.
"""
from datetime import datetime, timedelta, timezone

from api.app.errors import QuotaExceededError
from api.app.logger import debug, info

QUOTA_COSTS: dict[str, int] = {
    "search.list": 100,
    "videos.list": 1,
    "channels.list": 1,
}


def _get_today_string() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%d")


# Module-level mutable state (mirrors the TS module singletons).
_quota_date: str = _get_today_string()
_quota_used: int = 0
_quota_limit: int = 10000


def _reset_if_new_day() -> None:
    global _quota_date, _quota_used
    today = _get_today_string()
    if _quota_date != today:
        info("YouTube quota reset for new day", {"previousUsed": _quota_used})
        _quota_date = today
        _quota_used = 0


def set_quota_limit(limit: int) -> None:
    global _quota_limit
    _quota_limit = limit


def check_quota(operation: str) -> None:
    """Check if we can afford the operation, raise if not."""
    _reset_if_new_day()
    cost = QUOTA_COSTS[operation]
    if _quota_used + cost > _quota_limit:
        raise QuotaExceededError(
            f"Kuota YouTube API tidak cukup. Digunakan: {_quota_used}/{_quota_limit} unit. "
            f"Operasi {operation} membutuhkan {cost} unit."
        )


def record_quota_usage(operation: str) -> None:
    """Record quota usage after a successful API call."""
    global _quota_used
    _reset_if_new_day()
    cost = QUOTA_COSTS[operation]
    _quota_used += cost
    debug(
        "YouTube quota used",
        {
            "operation": operation,
            "cost": cost,
            "totalUsed": _quota_used,
            "remaining": _quota_limit - _quota_used,
        },
    )


def get_quota_status() -> dict:
    """Get current quota status."""
    _reset_if_new_day()
    tomorrow = datetime.now(timezone.utc) + timedelta(days=1)
    tomorrow = tomorrow.replace(hour=0, minute=0, second=0, microsecond=0)
    resets_at = tomorrow.strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + "Z"

    return {
        "used": _quota_used,
        "limit": _quota_limit,
        "remaining": max(0, _quota_limit - _quota_used),
        "resetsAt": resets_at,
    }


def reset_quota_state(limit: int = 10000) -> None:
    """Test helper: reset in-memory quota state."""
    global _quota_date, _quota_used, _quota_limit
    _quota_date = _get_today_string()
    _quota_used = 0
    _quota_limit = limit
