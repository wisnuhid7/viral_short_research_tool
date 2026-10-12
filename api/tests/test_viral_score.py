"""Port of server/test/viral-score.test.ts."""
from datetime import datetime, timedelta, timezone

from api.app.services.scoring.viral_score import (
    DEFAULT_WEIGHTS,
    calculate_viral_scores,
    compute_engagement,
    compute_reach_ratio,
    compute_velocity,
    is_young_video,
    percentile_normalize,
)
from api.tests.fixtures import mock_videos


def _iso_hours_ago(hours: float) -> str:
    return (datetime.now(timezone.utc) - timedelta(hours=hours)).strftime(
        "%Y-%m-%dT%H:%M:%S.%f"
    )[:-3] + "Z"


def _now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + "Z"


def test_percentile_normalize_empty():
    assert percentile_normalize([]) == []


def test_percentile_normalize_single():
    assert percentile_normalize([100]) == [0.5]


def test_percentile_normalize_multiple():
    assert percentile_normalize([10, 30, 20]) == [0, 1, 0.5]


def test_compute_velocity_per_hour():
    velocity = compute_velocity(1000, _iso_hours_ago(1))
    assert velocity > 950
    assert velocity < 1050


def test_compute_velocity_recent():
    assert compute_velocity(100, _now()) > 0


def test_compute_reach_ratio_basic():
    assert compute_reach_ratio(10000, 1000) == 10


def test_compute_reach_ratio_zero_or_negative_subscribers():
    assert compute_reach_ratio(10000, 0) == 0
    assert compute_reach_ratio(10000, -5) == 0


def test_compute_reach_ratio_capped():
    assert compute_reach_ratio(1000000, 10) == 100


def test_compute_engagement_basic():
    assert abs(compute_engagement(100, 20, 1000) - 0.12) < 1e-9


def test_compute_engagement_zero_views():
    assert compute_engagement(10, 5, 0) == 0


def test_is_young_video_true():
    assert is_young_video(_iso_hours_ago(1)) is True


def test_is_young_video_false():
    assert is_young_video(_iso_hours_ago(5)) is False


def test_calculate_viral_scores_empty():
    assert calculate_viral_scores([]) == []


def test_calculate_viral_scores_confidence_penalty():
    items = [
        {"video": mock_videos[0], "subscriberCount": 10000},
        {"video": mock_videos[1], "subscriberCount": 5000},
        {"video": mock_videos[2], "subscriberCount": 10000},
    ]
    scores = calculate_viral_scores(items, DEFAULT_WEIGHTS)
    assert len(scores) == 3

    young = next(s for s in scores if s["videoId"] == "vid3")
    assert young["confidencePenalty"] is True

    older = next(s for s in scores if s["videoId"] == "vid1")
    assert older["confidencePenalty"] is False