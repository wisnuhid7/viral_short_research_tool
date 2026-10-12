"""Port of server/test/keyword-suggest.test.ts."""
from api.app.services.keyword_suggest import extract_keyword_suggestions
from api.tests.fixtures import mock_videos


def test_extracts_suggestions_from_tags_and_recurring_words():
    videos = [
        *mock_videos,
        {
            **mock_videos[0],
            "id": "vid4",
            "title": "Another top AI tools video for beginners",
            "tags": ["tech", "ai", "productivity"],
        },
        {
            **mock_videos[0],
            "id": "vid5",
            "title": "Must have AI tools in your workflow",
            "tags": ["tech", "ai"],
        },
    ]

    suggestions = extract_keyword_suggestions("ai", videos)
    assert len(suggestions) > 0

    # 'tech' appears 4 times in tags (freq >= 2)
    tech_tag = next((s for s in suggestions if s["keyword"] == "tech" and s["source"] == "tag"), None)
    assert tech_tag is not None
    assert tech_tag["frequency"] >= 2

    # Parent keyword 'ai' should be excluded from suggestions
    assert not any(s["keyword"] == "ai" for s in suggestions)


def test_returns_empty_array_when_no_videos_provided():
    assert extract_keyword_suggestions("ai", []) == []
