"""YouTube Data API service.

Port of server/src/services/youtube.ts.

search.list = 100 quota units, videos.list = 1 unit, channels.list = 1 unit.
Quota is checked before each call and recorded after a successful response.
"""
import json
import re

import httpx

from api.app.config import settings
from api.app.db.database import now_iso
from api.app.errors import ExternalApiError
from api.app.lib.quota import check_quota, record_quota_usage
from api.app.logger import error as log_error
from api.app.logger import info as log_info
from api.app.logger import warn as log_warn

YOUTUBE_API_BASE = "https://www.googleapis.com/youtube/v3"


def _iso_utc(dt) -> str:
    from datetime import timezone

    return dt.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + "Z"


async def yt_fetch(endpoint: str, params: dict[str, str], quota_op: str) -> dict:
    check_quota(quota_op)

    url = httpx.URL(f"{YOUTUBE_API_BASE}/{endpoint}")
    query = {"key": settings.youtube_api_key, **params}

    async with httpx.AsyncClient() as client:
        response = await client.get(url, params=query, timeout=30.0)

    if response.status_code >= 400:
        error_body = response.text
        detailed_message = f"HTTP {response.status_code}"

        try:
            parsed = json.loads(error_body)
            errors = (parsed.get("error") or {}).get("errors") or []
            first_error = errors[0] if errors else parsed.get("error")
            if isinstance(first_error, dict) and first_error.get("message"):
                detailed_message = first_error["message"]
        except (ValueError, TypeError):
            pass

        log_error(
            "YouTube API error",
            {"endpoint": endpoint, "status": response.status_code, "details": detailed_message},
        )

        if response.status_code == 403:
            if "quotaExceeded" in error_body:
                raise ExternalApiError("YouTube", "Kuota harian terlampaui oleh Google.")
            raise ExternalApiError("YouTube", f"Akses ditolak (403): {detailed_message}")
        raise ExternalApiError("YouTube", detailed_message)

    record_quota_usage(quota_op)
    return response.json()


# ─── Time range → publishedAfter ─────────────────────────

def time_range_to_date(time_range: str) -> str:
    from datetime import datetime, timedelta

    now = datetime.now().astimezone()
    if time_range == "24h":
        now = now - timedelta(hours=24)
    elif time_range == "7d":
        now = now - timedelta(days=7)
    elif time_range == "30d":
        now = now - timedelta(days=30)
    return _iso_utc(now)


# ─── ISO 8601 duration → seconds ─────────────────────────

def parse_duration(iso: str) -> int:
    match = re.search(r"PT(?:(\d+)H)?(?:(\d+)M)?(?:(\d+)S)?", iso)
    if not match:
        return 0
    hours = int(match.group(1) or "0")
    minutes = int(match.group(2) or "0")
    seconds = int(match.group(3) or "0")
    return hours * 3600 + minutes * 60 + seconds


# ─── Search Shorts ───────────────────────────────────────

async def search_shorts(
    keyword: str,
    time_range: str,
    language: str,
    _max_duration: int | None = None,
) -> list[str]:
    params: dict[str, str] = {
        "part": "snippet",
        "q": f"{keyword} #shorts",
        "type": "video",
        "videoDuration": "short",  # ≤ 4 min
        "order": "viewCount",
        "maxResults": "50",
        "publishedAfter": time_range_to_date(time_range),
    }

    if language != "any":
        params["relevanceLanguage"] = language

    data = await yt_fetch("search", params, "search.list")

    log_info("YouTube search completed", {"keyword": keyword, "resultCount": len(data["items"])})

    return [item["id"]["videoId"] for item in data["items"]]


# ─── Video Details (batch) ───────────────────────────────

async def get_video_details(video_ids: list[str]) -> list[dict]:
    if len(video_ids) == 0:
        return []

    videos: list[dict] = []
    now = now_iso()

    for i in range(0, len(video_ids), 50):
        batch = video_ids[i : i + 50]
        data = await yt_fetch(
            "videos",
            {"part": "snippet,contentDetails,statistics", "id": ",".join(batch)},
            "videos.list",
        )

        for item in data["items"]:
            duration = parse_duration(item["contentDetails"]["duration"])
            title = item["snippet"]["title"]
            is_short = duration <= 180 or "#shorts" in title.lower()

            thumbnails = item["snippet"]["thumbnails"]
            thumbnail = (
                (thumbnails.get("high") or {}).get("url")
                or (thumbnails.get("medium") or {}).get("url")
                or (thumbnails.get("default") or {}).get("url")
                or ""
            )

            statistics = item["statistics"]
            videos.append(
                {
                    "id": item["id"],
                    "title": title,
                    "description": item["snippet"]["description"],
                    "channelId": item["snippet"]["channelId"],
                    "channelTitle": item["snippet"]["channelTitle"],
                    "publishedAt": item["snippet"]["publishedAt"],
                    "thumbnailUrl": thumbnail,
                    "duration": duration,
                    "viewCount": int(statistics.get("viewCount") or "0"),
                    "likeCount": int(statistics.get("likeCount") or "0"),
                    "commentCount": int(statistics.get("commentCount") or "0"),
                    "tags": item["snippet"].get("tags") or [],
                    "isShort": is_short,
                    "fetchedAt": now,
                }
            )

    return videos


# ─── Channel Details (batch) ─────────────────────────────

async def get_channel_details(channel_ids: list[str]) -> list[dict]:
    if len(channel_ids) == 0:
        return []

    channels: list[dict] = []
    now = now_iso()

    for i in range(0, len(channel_ids), 50):
        batch = channel_ids[i : i + 50]
        data = await yt_fetch(
            "channels",
            {"part": "snippet,statistics", "id": ",".join(batch)},
            "channels.list",
        )

        for item in data["items"]:
            statistics = item["statistics"]
            channels.append(
                {
                    "id": item["id"],
                    "title": item["snippet"]["title"],
                    "subscriberCount": 0
                    if statistics.get("hiddenSubscriberCount")
                    else int(statistics.get("subscriberCount") or "0"),
                    "thumbnailUrl": (item["snippet"]["thumbnails"].get("default") or {}).get("url"),
                    "fetchedAt": now,
                }
            )

    return channels


# ─── Captions / Transcript ───────────────────────────────
# YouTube Data API captions.list requires OAuth, so we use the
# unofficial timedtext endpoint as a best-effort approach.

async def get_transcript(video_id: str) -> str | None:
    try:
        url = f"https://www.youtube.com/watch?v={video_id}"
        async with httpx.AsyncClient(follow_redirects=True) as client:
            page_resp = await client.get(url, timeout=30.0)
            page_html = page_resp.text

        # Extract caption track URL from page source. NOTE: JS `.*?` without the
        # `s` flag does not cross newlines — keep identical semantics.
        caption_match = re.search(r'"captionTracks":\s*(\[.*?\])', page_html)
        if not caption_match:
            return None

        tracks = json.loads(caption_match.group(1))
        if len(tracks) == 0:
            return None

        track = next((t for t in tracks if t.get("languageCode") == "en"), None) or tracks[0]
        if not track:
            return None

        async with httpx.AsyncClient(follow_redirects=True) as client:
            caption_resp = await client.get(f"{track['baseUrl']}&fmt=srv3", timeout=30.0)
            caption_xml = caption_resp.text

        text_parts = re.findall(r"<text[^>]*>(.*?)</text>", caption_xml, re.DOTALL)
        if not text_parts:
            return None

        def clean(part: str) -> str:
            part = re.sub(r"<[^>]+>", "", part)
            return (
                part.replace("&amp;", "&")
                .replace("&lt;", "<")
                .replace("&gt;", ">")
                .replace("&quot;", '"')
                .replace("&#39;", "'")
            )

        transcript = " ".join(clean(p) for p in text_parts).strip()
        return transcript if len(transcript) > 0 else None
    except Exception as err:  # noqa: BLE001 - best-effort, mirrors TS catch-all
        log_warn("Failed to fetch transcript", {"videoId": video_id, "error": str(err)})
        return None
