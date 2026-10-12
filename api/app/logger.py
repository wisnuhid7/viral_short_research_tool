"""Centralized logger — never logs API keys, tokens, or raw sensitive responses.

Port of server/src/lib/logger.ts. Output format:
`[<iso-utc>] LEVEL message {json-meta}` (meta omitted when not provided).
"""
import json
import logging
import sys
from datetime import datetime, timezone

from api.app.config import settings

_LOG_LEVELS = {
    "debug": logging.DEBUG,
    "info": logging.INFO,
    "warn": logging.WARNING,
    "error": logging.ERROR,
}

# TS: NODE_ENV === 'production' ? 'info' : 'debug'. Read via settings so a
# NODE_ENV defined only in the repo-root `.env` (not the process environment)
# selects the level, matching the TS logger which loads dotenv first.
_current = "info" if settings.node_env == "production" else "debug"


class _Formatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        ts = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + "Z"
        meta = getattr(record, "meta", None)
        # JSON.stringify() emits compact JSON (no spaces after separators).
        meta_str = f" {json.dumps(meta, separators=(',', ':'))}" if meta is not None else ""
        level = getattr(record, "vst_level", record.levelname)
        return f"[{ts}] {level} {record.getMessage()}{meta_str}"


_logger = logging.getLogger("vst")
_logger.setLevel(_LOG_LEVELS.get(_current, logging.DEBUG))
_logger.propagate = False
_handler = logging.StreamHandler(sys.stderr)
_handler.setFormatter(_Formatter())
_logger.addHandler(_handler)


def _log(level: str, message: str, meta: dict | None):
    extra = {"vst_level": level.upper(), "meta": meta}
    _logger.log(_LOG_LEVELS[level], message, extra=extra)


def debug(message: str, meta: dict | None = None) -> None:
    _log("debug", message, meta)


def info(message: str, meta: dict | None = None) -> None:
    _log("info", message, meta)


def warn(message: str, meta: dict | None = None) -> None:
    _log("warn", message, meta)


def error(message: str, meta: dict | None = None) -> None:
    _log("error", message, meta)