"""Clip routes — new feature (create vertical shorts from source footage)."""
from pathlib import Path
from typing import Any

from fastapi import APIRouter, BackgroundTasks, Body, Query
from fastapi.responses import FileResponse

from api.app.db import clip_queries as cq
from api.app.errors import NotFoundError, ValidationError
from api.app.lib.validation import parse_body
from api.app.schemas import CreateClipRequest, CreateClipSourceRequest
from api.app.services.clips.pipeline import (
    create_clip_from_source,
    delete_clip_artifacts,
    delete_source_artifacts,
    process_source,
    render_clip,
)

router = APIRouter()


# ─── Sources ─────────────────────────────────────────────
# NOTE: declared before /{clip_id} so the literal segment wins.


@router.post("/sources", status_code=201)
def create_source(background_tasks: BackgroundTasks, body: Any = Body(default=None)):
    parsed: CreateClipSourceRequest = parse_body(  # type: ignore[assignment]
        CreateClipSourceRequest, body
    )
    source = cq.create_clip_source(parsed.sourceType, parsed.sourceRef, parsed.title)
    background_tasks.add_task(process_source, source["id"])
    return source


@router.get("/sources")
def list_sources():
    return cq.list_clip_sources()


@router.get("/sources/{source_id}")
def get_source(source_id: int):
    source = cq.get_clip_source(source_id)
    if source is None:
        raise NotFoundError(f"Sumber klip {source_id} tidak ditemukan.")
    return source


@router.delete("/sources/{source_id}")
def remove_source(source_id: int):
    if cq.get_clip_source(source_id) is None:
        raise NotFoundError(f"Sumber klip {source_id} tidak ditemukan.")
    # Collect rendered clips before their rows are cascade-deleted so their
    # media files (media/clips/clip_<id>.mp4|.srt) are cleaned up too.
    clips = cq.list_clips(source_id)
    cq.delete_clip_source(source_id)
    delete_source_artifacts(source_id)
    for clip in clips:
        delete_clip_artifacts(clip)
    return {"message": "Sumber klip berhasil dihapus."}


# ─── Clips ───────────────────────────────────────────────


@router.get("")
@router.get("/", include_in_schema=False)
def list_clips(sourceId: int | None = Query(default=None)):
    return cq.list_clips(sourceId)


@router.post("", status_code=201)
@router.post("/", status_code=201, include_in_schema=False)
async def create_clip(background_tasks: BackgroundTasks, body: Any = Body(default=None)):
    parsed: CreateClipRequest = parse_body(  # type: ignore[assignment]
        CreateClipRequest, body
    )
    if (parsed.start is None) != (parsed.end is None):
        raise ValidationError("Parameter start dan end harus diberikan bersamaan.")

    clip = await create_clip_from_source(
        parsed.sourceId,
        start=parsed.start,
        end=parsed.end,
        mode=parsed.mode,
        subtitles=parsed.subtitles,
        title=parsed.title,
        moment_index=parsed.momentIndex,
    )
    background_tasks.add_task(render_clip, clip["id"])
    return clip


@router.get("/{clip_id}")
def get_one(clip_id: int):
    clip = cq.get_clip(clip_id)
    if clip is None:
        raise NotFoundError(f"Klip {clip_id} tidak ditemukan.")
    return clip


@router.get("/{clip_id}/download")
def download(clip_id: int):
    clip = cq.get_clip(clip_id)
    if clip is None:
        raise NotFoundError(f"Klip {clip_id} tidak ditemukan.")
    output = clip.get("outputPath")
    if clip["status"] != "done" or not output or not Path(output).is_file():
        raise NotFoundError("Berkas klip belum tersedia. Tunggu hingga proses render selesai.")
    return FileResponse(
        output,
        media_type="video/mp4",
        filename=f"clip_{clip_id}.mp4",
    )


@router.delete("/{clip_id}")
def remove_clip(clip_id: int):
    clip = cq.get_clip(clip_id)
    if clip is None:
        raise NotFoundError(f"Klip {clip_id} tidak ditemukan.")
    cq.delete_clip(clip_id)
    delete_clip_artifacts(clip)
    return {"message": "Klip berhasil dihapus."}
