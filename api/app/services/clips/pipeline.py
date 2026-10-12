"""Orchestration for clip sources and clips.

Flow: create source (pending) -> process_source (download/probe/transcribe) ->
ready -> create_clip (auto-select or manual window) -> render_clip (ffmpeg).
"""
import json
from pathlib import Path

from api.app.config import settings
from api.app.db import clip_queries as cq
from api.app.errors import NotFoundError, ValidationError
from api.app.logger import info as log_info
from api.app.logger import warn as log_warn
from api.app.services.clips import media, select, transcribe
from api.app.services.clips.media import ClipToolingError

MIN_WINDOW_SECONDS = 1.0


def media_root() -> Path:
    return settings.media_root


def source_dir(source_id: int) -> Path:
    return media_root() / "sources" / str(source_id)


def clip_dir() -> Path:
    return media_root() / "clips"


def _load_transcript(source: dict) -> dict:
    path = source.get("transcriptPath")
    if not path or not Path(path).is_file():
        return {"text": "", "segments": []}
    try:
        return json.loads(Path(path).read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {"text": "", "segments": []}


async def process_source(source_id: int) -> None:
    """Download + transcribe a source. Never raises; failures land on the row."""
    source = cq.get_clip_source(source_id)
    if source is None:
        return
    try:
        dest = source_dir(source_id)
        if source["sourceType"] == "youtube":
            cq.update_clip_source(source_id, status="downloading")
            local = await media.download_source(source["sourceRef"], dest)
        else:
            local = Path(source["sourceRef"]).expanduser()
            if not local.is_file():
                raise ClipToolingError(f"Berkas sumber tidak ditemukan: {local}")

        duration = await media.probe_duration(local)
        cq.update_clip_source(
            source_id, status="transcribing", local_path=str(local), duration_seconds=duration
        )

        audio = await media.extract_audio(local, dest / "audio.wav")
        transcript = await transcribe.transcribe_audio(audio)
        transcript_path = dest / "transcript.json"
        transcript_path.parent.mkdir(parents=True, exist_ok=True)
        transcript_path.write_text(json.dumps(transcript, ensure_ascii=False), encoding="utf-8")

        cq.update_clip_source(
            source_id,
            status="ready",
            transcript_path=str(transcript_path),
            error_message=None,
        )
        log_info(
            "Clip source ready",
            {"sourceId": source_id, "duration": round(duration, 2), "segments": len(transcript["segments"])},
        )
    except Exception as err:  # noqa: BLE001 - status row carries the failure
        cq.update_clip_source(source_id, status="error", error_message=str(err))
        log_warn("Clip source failed", {"sourceId": source_id, "error": str(err)})


async def create_clip_from_source(
    source_id: int,
    start: float | None = None,
    end: float | None = None,
    mode: str = "crop",
    subtitles: bool = False,
    title: str | None = None,
    moment_index: int = 0,
) -> dict:
    source = cq.get_clip_source(source_id)
    if source is None:
        raise NotFoundError(f"Sumber klip {source_id} tidak ditemukan.")
    if source["status"] != "ready":
        raise ValidationError(
            "Sumber klip belum siap. Tunggu hingga status 'ready' sebelum membuat klip."
        )

    duration = float(source.get("durationSeconds") or 0.0)

    if start is not None and end is not None:
        # Explicit user input is validated, not silently re-clamped: a requested
        # window that falls outside the source is a mistake worth surfacing.
        if end <= start:
            raise ValidationError("Waktu akhir harus lebih besar dari waktu mulai.")
        if end - start < MIN_WINDOW_SECONDS:
            raise ValidationError(f"Durasi klip minimal {MIN_WINDOW_SECONDS:g} detik.")
        if duration > 0:
            if start < 0 or start >= duration:
                raise ValidationError(
                    f"Waktu mulai harus berada di antara 0 dan {duration:g} detik."
                )
            if end > duration:
                raise ValidationError(
                    f"Waktu akhir tidak boleh melebihi durasi video ({duration:g} detik)."
                )
        chosen = {
            "title": title or "Klip manual",
            "reason": None,
            "start": float(start),
            "end": float(end),
        }
    else:
        transcript = _load_transcript(source)
        moments = await select.select_moments(transcript["text"], duration)
        idx = moment_index if 0 <= moment_index < len(moments) else 0
        chosen = dict(moments[idx])
        if title:
            chosen["title"] = title
        # LLM output is untrusted, so auto moments are clamped to the source.
        if duration > 0:
            chosen["start"] = max(0.0, min(float(chosen["start"]), max(duration - MIN_WINDOW_SECONDS, 0.0)))
            chosen["end"] = min(duration, max(float(chosen["end"]), float(chosen["start"]) + MIN_WINDOW_SECONDS))

    return cq.create_clip(
        source_id,
        chosen["title"],
        float(chosen["start"]),
        float(chosen["end"]),
        mode=mode,
        subtitles=subtitles,
        reason=chosen.get("reason"),
        status="pending",
    )


async def render_clip(clip_id: int) -> None:
    """Render a pending clip. Never raises; failures land on the row."""
    clip = cq.get_clip(clip_id)
    if clip is None:
        return
    source = cq.get_clip_source(clip["sourceId"])
    if source is None or not source.get("localPath"):
        cq.update_clip(clip_id, status="error", error_message="Berkas sumber tidak tersedia.")
        return

    try:
        cq.update_clip(clip_id, status="rendering", error_message=None)
        out = clip_dir() / f"clip_{clip_id}.mp4"

        srt_path: Path | None = None
        if clip["subtitles"]:
            transcript = _load_transcript(source)
            if transcript["segments"]:
                if media.has_filter("subtitles"):
                    srt_path = media.write_srt(
                        transcript["segments"],
                        clip["startSeconds"],
                        clip["endSeconds"],
                        clip_dir() / f"clip_{clip_id}.srt",
                    )
                elif settings.clip_subtitles_fallback == "skip":
                    log_warn(
                        "Subtitle dilewati: ffmpeg tanpa libass",
                        {"clipId": clip_id, "fallback": "skip"},
                    )
                else:
                    raise ClipToolingError(
                        "ffmpeg ini tidak mendukung filter 'subtitles' (libass tidak aktif). "
                        "Pasang ffmpeg dengan libass, atau buat klip tanpa subtitle."
                    )

        await media.render_clip(
            Path(source["localPath"]),
            out,
            clip["startSeconds"],
            clip["endSeconds"],
            clip["mode"],
            srt_path,
        )
        cq.update_clip(clip_id, status="done", output_path=str(out))
        log_info("Clip rendered", {"clipId": clip_id, "mode": clip["mode"]})
    except Exception as err:  # noqa: BLE001 - status row carries the failure
        cq.update_clip(clip_id, status="error", error_message=str(err))
        log_warn("Clip render failed", {"clipId": clip_id, "error": str(err)})


def delete_clip_artifacts(clip: dict) -> None:
    """Best-effort removal of rendered files for a deleted clip."""
    path = clip.get("outputPath")
    if not path:
        return
    targets = [Path(path)]
    # The burned-in subtitles live next to the mp4 with the same stem.
    targets.append(Path(path).with_suffix(".srt"))
    for target in targets:
        try:
            target.unlink(missing_ok=True)
        except OSError as err:  # pragma: no cover - best effort
            log_warn("Gagal menghapus artefak klip", {"clipId": clip["id"], "error": str(err)})


def delete_source_artifacts(source_id: int) -> None:
    """Best-effort removal of a source's media directory."""
    import shutil

    try:
        shutil.rmtree(source_dir(source_id), ignore_errors=True)
    except OSError as err:  # pragma: no cover - best effort
        log_warn("Gagal menghapus berkas sumber", {"sourceId": source_id, "error": str(err)})
