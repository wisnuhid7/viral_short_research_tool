"""Port of server/test/db.test.ts."""
from datetime import datetime, timezone

from api.app.db.queries import (
    add_to_collection,
    create_collection,
    delete_collection,
    get_cached_search,
    get_channel,
    get_collection_items,
    get_collections,
    get_summary,
    get_video,
    get_videos_by_ids,
    save_search,
    save_summary,
    upsert_channel,
    upsert_video,
)
from api.tests.fixtures import mock_videos


def _now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + "Z"


def _seed_channels() -> None:
    upsert_channel(
        {"id": "ch1", "title": "Tech Wizard", "subscriberCount": 100000, "fetchedAt": _now()}
    )
    upsert_channel(
        {"id": "ch2", "title": "Side Hustle Pro", "subscriberCount": 50000, "fetchedAt": _now()}
    )


def test_upserts_and_retrieves_videos():
    _seed_channels()
    video = mock_videos[0]
    upsert_video(video)

    retrieved = get_video(video["id"])
    assert retrieved is not None
    assert retrieved["id"] == video["id"]
    assert retrieved["title"] == video["title"]
    assert retrieved["viewCount"] == video["viewCount"]

    batch = get_videos_by_ids([video["id"]])
    assert len(batch) == 1
    assert batch[0]["id"] == video["id"]


def test_upserts_and_retrieves_channels():
    channel = {
        "id": "ch_test",
        "title": "Channel Test",
        "subscriberCount": 50000,
        "thumbnailUrl": "https://example.com/thumb.jpg",
        "fetchedAt": _now(),
    }
    upsert_channel(channel)
    retrieved = get_channel("ch_test")
    assert retrieved is not None
    assert retrieved["title"] == "Channel Test"
    assert retrieved["subscriberCount"] == 50000


def test_saves_and_checks_cached_searches():
    _seed_channels()
    upsert_video(mock_videos[0])
    upsert_video(mock_videos[1])

    keyword = "test_keyword_" + str(int(datetime.now().timestamp() * 1000))
    save_search(keyword, "24h", "en", 60, [mock_videos[0]["id"], mock_videos[1]["id"]])

    cached = get_cached_search(keyword, "24h", 24)
    assert cached is not None
    assert cached["videoIds"] == [mock_videos[0]["id"], mock_videos[1]["id"]]

    missed = get_cached_search(keyword, "7d", 24)
    assert missed is None


def test_handles_collections_lifecycle():
    _seed_channels()
    coll_id = create_collection("My Test Collection", "Test description")
    assert coll_id > 0

    collections = get_collections()
    assert any(c["id"] == coll_id for c in collections)

    upsert_video(mock_videos[0])
    add_to_collection(coll_id, mock_videos[0]["id"], ["hook-test"], "Check hook pattern")

    coll_items = get_collection_items(coll_id)
    assert len(coll_items) == 1
    assert coll_items[0]["video_id"] == mock_videos[0]["id"]

    delete_collection(coll_id)
    after_delete = get_collections()
    assert not any(c["id"] == coll_id for c in after_delete)


def test_saves_and_retrieves_summaries():
    _seed_channels()
    upsert_video(mock_videos[0])

    summary = {
        "videoId": mock_videos[0]["id"],
        "topic": "AI Tools",
        "hookFirst3Seconds": "Stop scrolling if you want to save time",
        "structure": {
            "hook": "Top 5 tools revealed in first 3s",
            "body": "Walkthrough of tools 1-5",
            "cta": "Comment for full prompt library",
        },
        "style": "Fast-paced screenshare with voiceover",
        "keyMoments": ["0:00 Hook", "0:15 Tool 2", "0:40 CTA"],
        "confidence": "high",
        "sourceType": "transcript",
        "promptVersion": "v1.0",
        "createdAt": _now(),
    }

    save_summary(summary)
    retrieved = get_summary(mock_videos[0]["id"], "v1.0")
    assert retrieved is not None
    assert retrieved["structure"]["hook"] == "Top 5 tools revealed in first 3s"
    assert retrieved["confidence"] == "high"