"""Whisper transcription for clip sources."""
from pathlib import Path

from api.app.config import settings
from api.app.errors import ExternalApiError

TRANSCRIBE_MODEL = "whisper-1"


async def transcribe_audio(audio_path: Path) -> dict:
    """Return {"text": str, "segments": [{"start","end","text"}]}."""
    # Imported lazily so the openai package does not need a key at import time.
    from openai import AsyncOpenAI

    client = AsyncOpenAI(api_key=settings.openai_api_key or "dummy-key")
    try:
        with audio_path.open("rb") as fh:
            response = await client.audio.transcriptions.create(
                model=TRANSCRIBE_MODEL,
                file=fh,
                response_format="verbose_json",
            )
    except Exception as err:  # noqa: BLE001 - surface as upstream failure
        raise ExternalApiError("OpenAI", f"Transkripsi audio gagal: {err}") from err

    text = getattr(response, "text", "") or ""
    raw_segments = getattr(response, "segments", None) or []
    segments: list[dict] = []
    for seg in raw_segments:
        try:
            segments.append(
                {
                    "start": float(getattr(seg, "start", 0) or 0),
                    "end": float(getattr(seg, "end", 0) or 0),
                    "text": str(getattr(seg, "text", "") or ""),
                }
            )
        except (TypeError, ValueError):
            continue
    return {"text": text, "segments": segments}
