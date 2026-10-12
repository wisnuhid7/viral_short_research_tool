"""Summary routes — port of server/src/routes/summaries.ts."""
from typing import Any

from fastapi import APIRouter, Body

from api.app.db.queries import get_video
from api.app.errors import NotFoundError
from api.app.lib.validation import parse_body
from api.app.schemas import SummaryRequest
from api.app.services.summarizer import summarize_video

router = APIRouter()


@router.post("")
@router.post("/", include_in_schema=False)
async def create_summary(body: Any = Body(default=None)):
    parsed: SummaryRequest = parse_body(SummaryRequest, body)  # type: ignore[assignment]
    video_id = parsed.videoId

    # Ensure video exists in our DB
    video = get_video(video_id)
    if not video:
        raise NotFoundError(
            f'Video dengan ID "{video_id}" tidak ditemukan. Lakukan pencarian terlebih dahulu.'
        )

    summary = await summarize_video(video_id, video["title"], video["description"])
    return summary
