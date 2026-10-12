"""OpenAI-backed video summarization with caching.

Port of server/src/services/summarizer.ts.

Only called for user-selected videos, not entire search results.
"""
import json
import re

from pydantic import BaseModel, Field

from api.app.config import settings
from api.app.db.queries import get_summary, save_summary
from api.app.errors import ExternalApiError
from api.app.logger import debug as log_debug
from api.app.logger import info as log_info
from api.app.logger import warn as log_warn
from api.app.services.prompts.summarize_video import PROMPT_VERSION, build_summarize_prompt
from api.app.services.youtube import get_transcript

MAX_RETRIES = 2


class _Structure(BaseModel):
    hook: str
    body: str
    cta: str


class _LlmOutput(BaseModel):
    topic: str
    hookFirst3Seconds: str
    structure: _Structure
    style: str
    keyMoments: list[str] = Field(default_factory=list)


def _extract_json(text: str) -> str:
    """Extract JSON from an LLM response that might contain fences or extra text."""
    fence_match = re.search(r"```(?:json)?\s*\n?([\s\S]*?)\n?\s*```", text)
    if fence_match and fence_match.group(1):
        return fence_match.group(1).strip()

    json_match = re.search(r"\{[\s\S]*\}", text)
    if json_match:
        return json_match.group(0)

    return text.strip()


async def summarize_video(video_id: str, title: str, description: str) -> dict:
    # Check cache
    cached = get_summary(video_id, PROMPT_VERSION)
    if cached:
        log_debug("Summary cache hit", {"videoId": video_id})
        return cached

    # Fetch transcript
    transcript = await get_transcript(video_id)
    prompt = build_summarize_prompt(title, description, transcript)
    system_prompt = prompt["systemPrompt"]
    user_prompt = prompt["userPrompt"]
    source_type = prompt["sourceType"]

    # Import here so tests can run without the openai package needing a key at import time.
    from openai import AsyncOpenAI

    client = AsyncOpenAI(api_key=settings.openai_api_key or "dummy-key")

    last_error: Exception | None = None
    for attempt in range(MAX_RETRIES + 1):
        try:
            response = await client.chat.completions.create(
                model="gpt-4o-mini",
                response_format={"type": "json_object"},
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                temperature=0.3,
            )

            content = response.choices[0].message.content if response.choices else None
            if not content:
                raise ValueError("No content returned in OpenAI response")

            raw_json = _extract_json(content)
            parsed = _LlmOutput.model_validate(json.loads(raw_json))

            summary = {
                "videoId": video_id,
                "topic": parsed.topic,
                "hookFirst3Seconds": parsed.hookFirst3Seconds,
                "structure": parsed.structure.model_dump(),
                "style": parsed.style,
                "keyMoments": parsed.keyMoments,
                "confidence": "high" if source_type == "transcript" else "low",
                "sourceType": source_type,
                "promptVersion": PROMPT_VERSION,
                "createdAt": _now_iso(),
            }

            # Cache permanently
            save_summary(summary)
            log_info("Video summarized", {"videoId": video_id, "sourceType": source_type, "attempt": attempt})

            return summary
        except Exception as err:  # noqa: BLE001 - retry loop mirrors TS
            last_error = err
            log_warn("Summary attempt failed", {"videoId": video_id, "attempt": attempt, "error": str(err)})

    raise ExternalApiError(
        "OpenAI",
        f"Gagal meringkas video setelah {MAX_RETRIES + 1} percobaan: {last_error}",
    )


def _now_iso() -> str:
    from datetime import datetime, timezone

    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + "Z"
