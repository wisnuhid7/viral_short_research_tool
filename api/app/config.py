"""Application configuration.

Port of server/src/lib/config.ts. Environment variables are loaded from the
repo root `.env` file. Unlike the TS version we do NOT fail at import when
YOUTUBE_API_KEY is missing; the YouTube service raises a clear AppError when
an actual call is made without a key, which keeps the app and tests runnable
without secrets.
"""
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

# api/app/config.py -> parents[0]=app, parents[1]=api, parents[2]=repo root
REPO_ROOT: Path = Path(__file__).resolve().parents[2]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=str(REPO_ROOT / ".env"),
        env_file_encoding="utf-8",
        extra="ignore",
        populate_by_name=True,
    )

    port: int = 3001
    node_env: str = "development"
    youtube_api_key: str = ""
    openai_api_key: str = ""
    anthropic_api_key: str = ""
    youtube_daily_quota_limit: int = 10000
    cache_ttl_hours: int = 24
    whop_sync_enabled: bool = Field(True, validation_alias="VST_WHOP_SYNC_ENABLED")
    db_path_override: Path | None = Field(None, validation_alias="VST_DB_PATH")
    media_root_override: Path | None = Field(None, validation_alias="VST_MEDIA_ROOT")
    # Clip tooling guards: every yt-dlp/ffmpeg/ffprobe call is bounded so a hung
    # download or render can never block a worker forever.
    clip_download_timeout_seconds: int = Field(1800, validation_alias="VST_CLIP_DOWNLOAD_TIMEOUT")
    clip_ffmpeg_timeout_seconds: int = Field(600, validation_alias="VST_CLIP_FFMPEG_TIMEOUT")
    clip_ffprobe_timeout_seconds: int = Field(60, validation_alias="VST_CLIP_FFPROBE_TIMEOUT")
    # "error" (default) = fail loudly when ffmpeg lacks the subtitles filter;
    # "skip" = render the clip without burned subtitles instead.
    clip_subtitles_fallback: str = Field("error", validation_alias="VST_CLIP_SUBTITLES_FALLBACK")

    @property
    def is_dev(self) -> bool:
        return self.node_env == "development"

    @property
    def db_path(self) -> Path:
        """Default = repo root data.db (same file as the TS server)."""
        if self.db_path_override:
            return self.db_path_override.expanduser().resolve()
        return REPO_ROOT / "data.db"

    @property
    def media_root(self) -> Path:
        """Root directory for clip source downloads and rendered clips."""
        if self.media_root_override:
            return self.media_root_override.expanduser().resolve()
        return REPO_ROOT / "media"

    @property
    def llm_api_key(self) -> str:
        # TS: optionalEnv('OPENAI_API_KEY','') || optionalEnv('ANTHROPIC_API_KEY','')
        return self.openai_api_key or self.anthropic_api_key


settings = Settings()