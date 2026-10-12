"""LLM moment selection for shorts clips (gpt-4o-mini)."""
import json
import re

from api.app.config import settings
from api.app.errors import ExternalApiError

SELECT_MODEL = "gpt-4o-mini"
MAX_MOMENTS = 3
MIN_CLIP_SECONDS = 5

SYSTEM_PROMPT = (
    "Kamu adalah editor konten YouTube Shorts berbahasa Indonesia. "
    "Dari transkrip video, pilih momen paling menarik untuk dijadikan klip vertikal 9:16. "
    "Setiap momen harus berdiri sendiri, punya hook kuat, dan berdurasi 15-60 detik. "
    "Balas HANYA dengan JSON valid."
)


def _extract_json(text: str) -> str:
    fence_match = re.search(r"```(?:json)?\s*\n?([\s\S]*?)\n?\s*```", text)
    if fence_match and fence_match.group(1):
        return fence_match.group(1).strip()
    json_match = re.search(r"\{[\s\S]*\}", text)
    if json_match:
        return json_match.group(0)
    return text.strip()


def _user_prompt(transcript_text: str, duration: float, max_moments: int) -> str:
    return (
        f"Durasi video: {duration:.1f} detik.\n"
        f"Pilih maksimal {max_moments} momen.\n\n"
        "Format JSON:\n"
        '{"moments":[{"title":"judul singkat","reason":"alasan singkat",'
        '"start":0.0,"end":30.0}]}\n\n'
        "Transkrip:\n"
        f"{transcript_text}"
    )


def _clamp(moment: dict, duration: float) -> dict | None:
    try:
        start = float(moment["start"])
        end = float(moment["end"])
    except (KeyError, TypeError, ValueError):
        return None
    start = max(0.0, min(start, max(duration - 1.0, 0.0)))
    end = min(duration, max(end, start + 1.0))
    if end - start < MIN_CLIP_SECONDS:
        return None
    return {
        "title": str(moment.get("title") or "Highlight").strip() or "Highlight",
        "reason": str(moment.get("reason") or "").strip(),
        "start": round(start, 2),
        "end": round(end, 2),
    }


async def select_moments(
    transcript_text: str, duration: float, max_moments: int = MAX_MOMENTS
) -> list[dict]:
    if not transcript_text.strip():
        raise ExternalApiError("OpenAI", "Transkrip kosong, tidak ada momen yang bisa dipilih.")

    # Imported lazily so tests can run without an OpenAI key at import time.
    from openai import AsyncOpenAI

    client = AsyncOpenAI(api_key=settings.openai_api_key or "dummy-key")
    try:
        response = await client.chat.completions.create(
            model=SELECT_MODEL,
            response_format={"type": "json_object"},
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": _user_prompt(transcript_text, duration, max_moments)},
            ],
            temperature=0.3,
        )
        content = response.choices[0].message.content if response.choices else None
        if not content:
            raise ValueError("No content returned in OpenAI response")
        parsed = json.loads(_extract_json(content))
    except Exception as err:  # noqa: BLE001 - surface as upstream failure
        raise ExternalApiError("OpenAI", f"Pemilihan momen gagal: {err}") from err

    raw = parsed.get("moments") if isinstance(parsed, dict) else None
    if not isinstance(raw, list):
        raise ExternalApiError("OpenAI", "Model tidak mengembalikan daftar momen yang valid.")

    moments = [c for c in (_clamp(m, duration) for m in raw if isinstance(m, dict)) if c]
    if not moments:
        raise ExternalApiError("OpenAI", "Model tidak mengembalikan momen yang valid.")
    return moments[:max_moments]
