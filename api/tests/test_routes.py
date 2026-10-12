"""Endpoint tests for the FastAPI routers.

External services (YouTube, OpenAI, Whop MCP) are monkeypatched — no network.
"""
import re

import pytest
from fastapi.testclient import TestClient

from api.app.db import queries
from api.app.lib.quota import reset_quota_state
from api.app.main import app
from api.tests.fixtures import mock_videos


@pytest.fixture
def client():
    with TestClient(app, raise_server_exceptions=False) as c:
        yield c


@pytest.fixture(autouse=True)
def _reset_quota():
    reset_quota_state()
    yield
    reset_quota_state()


def _seed_video(video: dict) -> None:
    """Insert a channel then a video (videos.channel_id is a FK to channels)."""
    queries.upsert_channel(
        {
            "id": video["channelId"],
            "title": video["channelTitle"],
            "subscriberCount": 100000,
            "thumbnailUrl": video["thumbnailUrl"],
            "fetchedAt": video["fetchedAt"],
        }
    )
    queries.upsert_video(video)


# ─── health & quota ──────────────────────────────────────


def test_health(client):
    r = client.get("/api/health")
    assert r.status_code == 200
    assert r.json()["status"] == "ok"
    assert r.json()["timestamp"].endswith("Z")


def test_quota(client):
    r = client.get("/api/quota")
    assert r.status_code == 200
    body = r.json()
    assert body["used"] == 0
    assert body["limit"] == 10000
    assert body["remaining"] == 10000


# ─── search ──────────────────────────────────────────────


def test_search_returns_scored_sorted_videos(client, monkeypatch):
    videos = mock_videos[:2]

    async def fake_search(*_a, **_k):
        return ["vid1", "vid2"]

    async def fake_videos(*_a, **_k):
        return videos

    async def fake_channels(ids):
        return [
            {"id": cid, "title": cid, "subscriberCount": 100000, "thumbnailUrl": None, "fetchedAt": mock_videos[0]["fetchedAt"]}
            for cid in ids
        ]

    monkeypatch.setattr("api.app.routers.search.search_shorts", fake_search)
    monkeypatch.setattr("api.app.routers.search.get_video_details", fake_videos)
    monkeypatch.setattr("api.app.routers.search.get_channel_details", fake_channels)

    r = client.post("/api/search", json={"keyword": "ai tools", "timeRange": "7d"})
    assert r.status_code == 200
    body = r.json()
    assert body["keyword"] == "ai tools"
    assert len(body["videos"]) == 2
    scores = [v["viralScore"]["totalScore"] for v in body["videos"]]
    assert scores == sorted(scores, reverse=True)
    assert all("subscriberCount" in v for v in body["videos"])
    assert body["quotaRemaining"] == 10000


def test_search_validation_error(client):
    r = client.post("/api/search", json={})
    assert r.status_code == 400
    assert r.json()["code"] == "VALIDATION_ERROR"
    assert r.json()["message"] == "Input tidak valid: Required"


def test_search_invalid_time_range(client):
    r = client.post("/api/search", json={"keyword": "x", "timeRange": "99d"})
    assert r.status_code == 400
    assert r.json()["message"].startswith("Input tidak valid: Invalid enum value.")


# ─── summaries ───────────────────────────────────────────


def test_summary_video_not_found(client):
    r = client.post("/api/summaries", json={"videoId": "missing"})
    assert r.status_code == 404
    assert r.json()["code"] == "NOT_FOUND"


def test_summary_ok(client, monkeypatch):
    _seed_video(mock_videos[0])

    async def fake_summarize(video_id, *_a, **_k):
        return {
            "videoId": video_id,
            "topic": "AI tools",
            "hookFirst3Seconds": "Hook",
            "structure": {"hook": "h", "body": "b", "cta": "c"},
            "style": "fast",
            "keyMoments": [],
            "confidence": "high",
            "sourceType": "title_description",
            "promptVersion": "v1.0",
            "createdAt": mock_videos[0]["fetchedAt"],
        }

    monkeypatch.setattr("api.app.routers.summaries.summarize_video", fake_summarize)
    r = client.post("/api/summaries", json={"videoId": "vid1"})
    assert r.status_code == 200
    assert r.json()["topic"] == "AI tools"


# ─── collections ─────────────────────────────────────────


def test_collections_crud(client):
    r = client.post("/api/collections", json={"name": "Riset", "description": "d"})
    assert r.status_code == 201
    body = r.json()
    assert body["message"] == "Koleksi berhasil dibuat."
    cid = body["id"]

    r = client.get("/api/collections")
    assert r.status_code == 200
    assert len(r.json()) == 1
    # raw snake_case rows, per TS contract
    assert "created_at" in r.json()[0]

    # add item requires the video to exist (JOIN on videos)
    _seed_video(mock_videos[0])
    r = client.post(f"/api/collections/{cid}/items", json={"videoId": "vid1", "tags": ["a"], "notes": "n"})
    assert r.status_code == 201
    assert r.json()["message"] == "Video berhasil ditambahkan ke koleksi."

    r = client.get(f"/api/collections/{cid}/items")
    assert r.status_code == 200
    items = r.json()
    assert len(items) == 1
    assert items[0]["video_id"] == "vid1"
    assert items[0]["video_title"] == mock_videos[0]["title"]

    r = client.delete(f"/api/collections/{cid}/items/vid1")
    assert r.status_code == 200
    assert client.get(f"/api/collections/{cid}/items").json() == []

    r = client.delete(f"/api/collections/{cid}")
    assert r.status_code == 200
    assert r.json()["message"] == "Koleksi berhasil dihapus."


def test_collection_invalid_id(client):
    r = client.get("/api/collections/abc/items")
    assert r.status_code == 400
    assert r.json() == {"code": "VALIDATION_ERROR", "message": "ID koleksi tidak valid."}


def test_collection_parse_int_prefix(client):
    # JS parseInt("3abc") === 3
    r = client.get("/api/collections/3abc/items")
    assert r.status_code == 200


def test_create_collection_validation(client):
    r = client.post("/api/collections", json={"name": ""})
    assert r.status_code == 400
    assert r.json()["message"] == "Input tidak valid: String must contain at least 1 character(s)"


# ─── export ──────────────────────────────────────────────


def test_export_csv(client):
    _seed_video(mock_videos[0])
    r = client.post("/api/export", json={"videoIds": ["vid1"], "format": "csv", "includeSummaries": False})
    assert r.status_code == 200
    assert r.headers["content-type"] == "text/csv; charset=utf-8"
    assert r.headers["content-disposition"] == 'attachment; filename="shorts_research.csv"'
    lines = r.text.split("\n")
    assert lines[0] == "ID,Judul,Channel,Views,Likes,Komentar,Durasi (detik),Tanggal Upload"
    assert lines[1].startswith("vid1,")


def test_export_csv_escapes_commas(client):
    video = {**mock_videos[0], "id": "vidX", "title": "a,b"}
    _seed_video(video)
    r = client.post("/api/export", json={"videoIds": ["vidX"], "format": "csv"})
    assert '"a,b"' in r.text


def test_export_markdown_locale(client):
    video = {**mock_videos[0], "id": "vidY", "viewCount": 2500000}
    _seed_video(video)
    r = client.post("/api/export", json={"videoIds": ["vidY"], "format": "markdown"})
    assert r.status_code == 200
    assert r.headers["content-type"] == "text/markdown; charset=utf-8"
    assert "**Views:** 2.500.000" in r.text


def test_export_empty(client):
    r = client.post("/api/export", json={"videoIds": ["nope"], "format": "csv"})
    assert r.status_code == 400
    assert r.json()["message"] == "Tidak ada video ditemukan untuk ID yang diberikan."


def test_export_invalid_format(client):
    r = client.post("/api/export", json={"videoIds": ["a"], "format": "md"})
    assert r.status_code == 400
    assert r.json()["message"] == "Input tidak valid: Invalid enum value. Expected 'csv' | 'markdown', received 'md'"


# ─── campaigns ───────────────────────────────────────────


def test_campaigns_list_has_ratings(client):
    r = client.get("/api/campaigns")
    assert r.status_code == 200
    campaigns = r.json()
    assert len(campaigns) > 0
    scores = [c["rating"]["opportunityScore"] for c in campaigns]
    assert scores == sorted(scores, reverse=True)


def test_campaigns_category_filter(client):
    r = client.get("/api/campaigns", params={"category": "gaming"})
    assert r.status_code == 200
    assert all(c["category"] == "gaming" for c in r.json())


def test_campaigns_match_empty_keyword(client):
    assert client.get("/api/campaigns/match", params={"keyword": "  "}).json() == []


def test_campaign_not_found(client):
    r = client.get("/api/campaigns/nope")
    assert r.status_code == 404
    assert r.json() == {"code": "NOT_FOUND", "message": "Campaign nope tidak ditemukan."}


def test_campaign_create_and_delete(client):
    payload = {
        "name": "Test Campaign",
        "creatorOrBrand": "Tester",
        "category": "ai_tech",
        "ratePerKViews": 5,
        "totalBudget": 1000,
        "remainingBudget": 1000,
    }
    r = client.post("/api/campaigns", json=payload)
    assert r.status_code == 201
    body = r.json()
    assert body["id"].startswith("cmp_")
    assert body["isWhopLive"] is False
    assert "rating" in body

    r = client.get(f"/api/campaigns/{body['id']}")
    assert r.status_code == 200
    assert r.json()["name"] == "Test Campaign"

    r = client.delete(f"/api/campaigns/{body['id']}")
    assert r.status_code == 200
    assert r.json()["message"] == "Campaign berhasil dihapus."
    assert client.get(f"/api/campaigns/{body['id']}").status_code == 404


def test_campaign_create_validation_prefix(client):
    r = client.post("/api/campaigns", json={"name": "x"})
    assert r.status_code == 400
    assert r.json()["message"].startswith("Input campaign tidak valid: ")


def test_integral_floats_serialized_like_js(client):
    """JSON.stringify never emits a trailing `.0`, so neither may we."""
    from api.app.lib.js_json import JsJSONResponse, _js_numbers

    body = JsJSONResponse(content={"a": 500.0, "b": 400.0, "c": 1.05, "d": [2.0, {"e": 0.0}]}).body.decode()
    assert body == '{"a":500,"b":400,"c":1.05,"d":[2,{"e":0}]}'
    # JSON.stringify serializes non-finite numbers as null.
    assert _js_numbers(float("nan")) is None
    assert _js_numbers(float("inf")) is None
    assert JsJSONResponse(content={"x": float("nan")}).body.decode() == '{"x":null}'

    payload = {
        "name": "Float Campaign",
        "creatorOrBrand": "Tester",
        "category": "ai_tech",
        "ratePerKViews": 500,
        "totalBudget": 500,
        "remainingBudget": 400,
    }
    r = client.post("/api/campaigns", json=payload)
    assert r.status_code == 201
    assert '"totalBudget":500,' in r.text
    assert '"remainingBudget":400,' in r.text
    # No numeric token may carry a trailing `.0` (stringified as `500`, not
    # `500.0`). Target number tokens so ISO timestamps like `...59.016Z` — which
    # legitimately contain ".0" — do not trip the check.
    assert not re.search(r"\d\.0(?=[,}\]])", r.text)
    client.delete(f"/api/campaigns/{r.json()['id']}")


# ─── campaign sync ───────────────────────────────────────


def test_sync_status(client):
    r = client.get("/api/campaigns/sync-status")
    assert r.status_code == 200
    assert r.json()["status"] in ("idle", "syncing", "success", "error")


def test_sync_monkeypatched(client, monkeypatch):
    async def fake_sync():
        return {"success": True, "count": 3, "syncedAt": mock_videos[0]["fetchedAt"], "message": "ok"}

    monkeypatch.setattr("api.app.routers.campaigns.sync_whop_campaigns", fake_sync)
    r = client.post("/api/campaigns/sync")
    assert r.status_code == 200
    assert r.json()["count"] == 3


# ─── parity regression (oracle review fixes) ─────────────


def test_json_content_type_has_charset(client):
    """Express `res.json` sends `application/json; charset=utf-8`."""
    r = client.get("/api/quota")
    assert r.headers["content-type"] == "application/json; charset=utf-8"


def test_trailing_slash_is_served_not_redirected(client):
    """Express (strict routing off) serves `/api/health/` with 200, no 307."""
    assert client.get("/api/health/", follow_redirects=False).status_code == 200
    assert client.get("/api/search/history/", follow_redirects=False).status_code == 200


def test_missing_body_reports_single_required(client):
    r = client.post("/api/export")
    assert r.status_code == 400
    assert r.json()["message"] == "Input tidak valid: Required"


def test_array_body_reports_expected_object(client):
    r = client.post("/api/export", json=[])
    assert r.status_code == 400
    assert r.json()["message"] == "Input tidak valid: Expected object, received array"


def test_malformed_json_is_500_envelope(client):
    """Express strict JSON parsing collapses syntax errors into the 500 handler."""
    r = client.post(
        "/api/campaigns",
        content=b'{"name":',
        headers={"content-type": "application/json"},
    )
    assert r.status_code == 500
    assert r.json()["code"] == "INTERNAL_ERROR"


def test_unicode_is_not_escaped(client):
    """`ensure_ascii=False` keeps raw unicode (Express does not escape it)."""
    payload = {
        "name": "Uji",
        "creatorOrBrand": "T",
        "category": "ai_tech",
        "ratePerKViews": 1,
        "totalBudget": 10,
        "remainingBudget": 5,
        "requiredHashtags": ["#kucing😺", "#café"],
    }
    r = client.post("/api/campaigns", json=payload)
    assert r.status_code == 201
    assert "😺" in r.text and "café" in r.text
    assert "\\ud83d" not in r.text
    client.delete(f"/api/campaigns/{r.json()['id']}")
