"""Viral score calculation. Port of server/src/services/scoring/viral-score.ts."""
from datetime import datetime, timezone

from api.app.lib.format import js_round

DEFAULT_WEIGHTS = {"velocity": 0.45, "reachRatio": 0.30, "engagement": 0.25}

REACH_RATIO_CAP = 100
YOUNG_VIDEO_HOURS = 3


def _now_ms() -> float:
    return datetime.now(timezone.utc).timestamp() * 1000


def _parse_ms(iso: str) -> float:
    return datetime.fromisoformat(iso.replace("Z", "+00:00")).timestamp() * 1000


def percentile_normalize(values: list[float]) -> list[float]:
    if len(values) == 0:
        return []
    if len(values) == 1:
        return [0.5]
    sorted_vals = sorted(values)
    return [sum(1 for v in sorted_vals if v < val) / (len(sorted_vals) - 1) for val in values]


def compute_velocity(view_count: int, published_at: str) -> float:
    hours_since_upload = max((_now_ms() - _parse_ms(published_at)) / (1000 * 60 * 60), 0.1)
    return view_count / hours_since_upload


def compute_reach_ratio(view_count: int, subscriber_count: int) -> float:
    if subscriber_count <= 0:
        return 0
    return min(view_count / subscriber_count, REACH_RATIO_CAP)


def compute_engagement(like_count: int, comment_count: int, view_count: int) -> float:
    if view_count <= 0:
        return 0
    return (like_count + comment_count) / view_count


def is_young_video(published_at: str) -> bool:
    hours_since = (_now_ms() - _parse_ms(published_at)) / (1000 * 60 * 60)
    return hours_since < YOUNG_VIDEO_HOURS


def calculate_viral_scores(
    items: list[dict], weights: dict | None = None
) -> list[dict]:
    """items: [{ "video": Video, "subscriberCount": int }, ...]"""
    if len(items) == 0:
        return []
    if weights is None:
        weights = DEFAULT_WEIGHTS

    velocities = [compute_velocity(i["video"]["viewCount"], i["video"]["publishedAt"]) for i in items]
    reach_ratios = [
        compute_reach_ratio(i["video"]["viewCount"], i["subscriberCount"]) for i in items
    ]
    engagements = [
        compute_engagement(
            i["video"]["likeCount"], i["video"]["commentCount"], i["video"]["viewCount"]
        )
        for i in items
    ]

    vel_norms = percentile_normalize(velocities)
    reach_norms = percentile_normalize(reach_ratios)
    eng_norms = percentile_normalize(engagements)

    results: list[dict] = []
    for idx, item in enumerate(items):
        vel_n = vel_norms[idx] if idx < len(vel_norms) else 0
        reach_n = reach_norms[idx] if idx < len(reach_norms) else 0
        eng_n = eng_norms[idx] if idx < len(eng_norms) else 0

        total_score = (
            weights["velocity"] * vel_n
            + weights["reachRatio"] * reach_n
            + weights["engagement"] * eng_n
        )

        has_penalty = is_young_video(item["video"]["publishedAt"])
        if has_penalty:
            total_score *= 0.8

        results.append(
            {
                "videoId": item["video"]["id"],
                "velocity": velocities[idx] if idx < len(velocities) else 0,
                "velocityNorm": vel_n,
                "reachRatio": reach_ratios[idx] if idx < len(reach_ratios) else 0,
                "reachRatioNorm": reach_n,
                "engagement": engagements[idx] if idx < len(engagements) else 0,
                "engagementNorm": eng_n,
                "totalScore": js_round(total_score * 1000) / 1000,
                "confidencePenalty": has_penalty,
                "sampleSize": len(items),
            }
        )
    return results