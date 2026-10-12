"""Port of server/test/schemas.test.ts."""
import pytest
from pydantic import ValidationError

from api.app.schemas import (
    CreateCollectionRequest,
    ExportRequest,
    SearchRequest,
    SummaryRequest,
    Video,
)
from api.tests.fixtures import mock_videos


def test_validates_search_requests():
    valid = {
        "keyword": "crypto trading",
        "timeRange": "24h",
        "language": "en",
        "maxDuration": 60,
    }
    assert SearchRequest.model_validate(valid)

    with pytest.raises(ValidationError):
        SearchRequest.model_validate({"keyword": "", "timeRange": "invalid_range"})


def test_validates_summarize_requests():
    assert SummaryRequest.model_validate({"videoId": "abc12345678"})
    with pytest.raises(ValidationError):
        SummaryRequest.model_validate({"videoId": ""})


def test_validates_export_requests():
    valid = {"format": "csv", "videoIds": ["vid1", "vid2"], "includeSummaries": False}
    assert ExportRequest.model_validate(valid)


def test_validates_collection_creation():
    assert CreateCollectionRequest.model_validate({"name": "Hook Library"})
    with pytest.raises(ValidationError):
        CreateCollectionRequest.model_validate({"name": ""})


def test_validates_video_schema_against_mock_videos():
    for video in mock_videos:
        assert Video.model_validate(video)