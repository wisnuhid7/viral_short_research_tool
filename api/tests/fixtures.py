"""Port of server/test/fixtures/videos.ts."""
from datetime import datetime, timedelta, timezone


def _iso_hours_ago(hours: float) -> str:
    return (datetime.now(timezone.utc) - timedelta(hours=hours)).strftime(
        "%Y-%m-%dT%H:%M:%S.%f"
    )[:-3] + "Z"


def _now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + "Z"


def _mock_videos() -> list[dict]:
    return [
        {
            "id": "vid1",
            "title": "5 AI Tools That Will Blow Your Mind #shorts",
            "description": "Check out these top AI tools for productivity in 2024!",
            "channelId": "ch1",
            "channelTitle": "Tech Wizard",
            "publishedAt": _iso_hours_ago(24),
            "thumbnailUrl": "https://i.ytimg.com/vi/vid1/hqdefault.jpg",
            "duration": 45,
            "viewCount": 150000,
            "likeCount": 12000,
            "commentCount": 450,
            "tags": ["ai", "tech", "tools"],
            "isShort": True,
            "fetchedAt": _now(),
        },
        {
            "id": "vid2",
            "title": "How to make $100/day online without coding",
            "description": "Full breakdown of beginner side hustles.",
            "channelId": "ch2",
            "channelTitle": "Side Hustle Pro",
            "publishedAt": _iso_hours_ago(48),
            "thumbnailUrl": "https://i.ytimg.com/vi/vid2/hqdefault.jpg",
            "duration": 58,
            "viewCount": 300000,
            "likeCount": 25000,
            "commentCount": 800,
            "tags": ["sidehustle", "money", "online"],
            "isShort": True,
            "fetchedAt": _now(),
        },
        {
            "id": "vid3",
            "title": "Brand new short just released",
            "description": "Fresh upload test",
            "channelId": "ch1",
            "channelTitle": "Tech Wizard",
            "publishedAt": _iso_hours_ago(1),
            "thumbnailUrl": "https://i.ytimg.com/vi/vid3/hqdefault.jpg",
            "duration": 30,
            "viewCount": 2000,
            "likeCount": 100,
            "commentCount": 10,
            "tags": ["tech"],
            "isShort": True,
            "fetchedAt": _now(),
        },
    ]


mock_videos = _mock_videos()