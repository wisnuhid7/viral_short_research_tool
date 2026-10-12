"""Search routes — port of server/src/routes/search.ts."""
from typing import Any

from fastapi import APIRouter, Body

from api.app.config import settings
from api.app.db.database import now_iso
from api.app.db.queries import (
    get_cached_search,
    get_channels_by_ids,
    get_recent_searches,
    get_videos_by_ids,
    save_search,
    upsert_channel,
    upsert_video,
)
from api.app.lib.quota import get_quota_status
from api.app.lib.validation import parse_body
from api.app.logger import info as log_info
from api.app.schemas import SearchRequest
from api.app.services.keyword_suggest import extract_keyword_suggestions
from api.app.services.scoring.viral_score import calculate_viral_scores
from api.app.services.youtube import get_channel_details, get_video_details, search_shorts

router = APIRouter()


@router.get("/history")
def get_history():
    return get_recent_searches(10)


@router.post("")
@router.post("/", include_in_schema=False)
async def create_search(body: Any = Body(default=None)):
    parsed: SearchRequest = parse_body(SearchRequest, body)  # type: ignore[assignment]
    keyword = parsed.keyword
    time_range = parsed.timeRange
    language = parsed.language
    max_duration = parsed.maxDuration
    min_views = parsed.minViews
    ttl = settings.cache_ttl_hours

    # 1. Check cache
    cached = get_cached_search(keyword, time_range, ttl)
    cached_at: str | None = None

    if cached and len(cached["videoIds"]) > 0:
        log_info("Search cache hit", {"keyword": keyword, "timeRange": time_range})
        cached_videos = get_videos_by_ids(cached["videoIds"])
        videos = [
            v for v in cached_videos if v["duration"] <= max_duration and v["isShort"] and v["viewCount"] >= min_views
        ]
        cached_at = now_iso()  # indicate it was from cache
    else:
        # 2. Search YouTube
        video_ids = await search_shorts(keyword, time_range, language, max_duration)

        if len(video_ids) == 0:
            quota = get_quota_status()
            return {
                "keyword": keyword,
                "videos": [],
                "suggestions": [],
                "quotaUsed": quota["used"],
                "quotaRemaining": quota["remaining"],
                "cachedAt": None,
            }

        # 3. Get video details (batch, 1 unit per call)
        video_details = await get_video_details(video_ids)

        videos = [
            v for v in video_details if v["duration"] <= max_duration and v["isShort"] and v["viewCount"] >= min_views
        ]

        # 4. Get channel details for subscriber counts (batch)
        unique_channel_ids = list(dict.fromkeys(v["channelId"] for v in videos))
        channel_details = await get_channel_details(unique_channel_ids)

        # 5. Persist to DB
        for ch in channel_details:
            upsert_channel(ch)
        for v in videos:
            upsert_video(v)

        save_search(keyword, time_range, language, max_duration, [v["id"] for v in videos])

    # 6. Get channel info for scoring
    channel_ids = list(dict.fromkeys(v["channelId"] for v in videos))
    channel_map = get_channels_by_ids(channel_ids)

    # 7. Calculate viral scores
    scoring_input = [
        {"video": v, "subscriberCount": (channel_map.get(v["channelId"]) or {}).get("subscriberCount", 0)}
        for v in videos
    ]

    scores = calculate_viral_scores(scoring_input)
    score_map = {s["videoId"]: s for s in scores}

    # 8. Build response sorted by viral score
    videos_with_scores = []
    for v in videos:
        item = {**v, "viralScore": score_map[v["id"]]}
        channel = channel_map.get(v["channelId"])
        if channel is not None:
            item["subscriberCount"] = channel["subscriberCount"]
        videos_with_scores.append(item)
    videos_with_scores.sort(key=lambda x: x["viralScore"]["totalScore"], reverse=True)

    # 9. Extract keyword suggestions
    suggestions = extract_keyword_suggestions(keyword, videos)

    # 10. Return
    quota = get_quota_status()
    return {
        "keyword": keyword,
        "videos": videos_with_scores,
        "suggestions": suggestions,
        "quotaUsed": quota["used"],
        "quotaRemaining": quota["remaining"],
        "cachedAt": cached_at,
    }
