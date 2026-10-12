"""Tests for YouTube quota tracking (port behaviour of lib/quota-tracker.ts)."""
import pytest

from api.app.errors import QuotaExceededError
from api.app.lib.quota import (
    QUOTA_COSTS,
    check_quota,
    get_quota_status,
    record_quota_usage,
    reset_quota_state,
    set_quota_limit,
)


@pytest.fixture(autouse=True)
def _reset_quota():
    reset_quota_state()
    yield
    reset_quota_state()


def test_costs_match_ts_constants():
    assert QUOTA_COSTS == {"search.list": 100, "videos.list": 1, "channels.list": 1}


def test_default_status():
    status = get_quota_status()
    assert status["used"] == 0
    assert status["limit"] == 10000
    assert status["remaining"] == 10000
    assert status["resetsAt"].endswith("Z")


def test_check_quota_raises_with_expected_message():
    set_quota_limit(150)
    record_quota_usage("search.list")  # used = 100
    with pytest.raises(QuotaExceededError) as exc:
        check_quota("search.list")  # 100 + 100 > 150
    assert str(exc.value) == (
        "Kuota YouTube API tidak cukup. Digunakan: 100/150 unit. "
        "Operasi search.list membutuhkan 100 unit."
    )


def test_remaining_is_floored_at_zero():
    set_quota_limit(50)
    record_quota_usage("search.list")  # used = 100 > limit
    assert get_quota_status()["remaining"] == 0
