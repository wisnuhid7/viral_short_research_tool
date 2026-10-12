"""SQLite connection manager + helpers.

Port of server/src/db/schema.ts connection lifecycle. A single shared
connection is used, guarded by a re-entrant lock so FastAPI's thread-pooled
sync endpoints cannot interleave statements. Default DB = repo root `data.db`
(override with VST_DB_PATH for tests).
"""
import sqlite3
import threading
from contextlib import contextmanager
from datetime import datetime, timedelta, timezone

from api.app.config import settings
from api.app.db.schema import run_migrations
from api.app.logger import info

_db: sqlite3.Connection | None = None
_db_lock = threading.RLock()

# Dropped in this order (children before parents) by reset_db().
_TABLES = [
    "collection_items",
    "collections",
    "summaries",
    "keyword_suggestions",
    "keyword_search_results",
    "keyword_searches",
    "videos",
    "channels",
    "campaigns",
    "whop_sync_logs",
    "clips",
    "clip_sources",
    "_migrations",
]


def _lossy_text(value: bytes) -> str:
    """Decode TEXT columns the way better-sqlite3 does.

    Live Whop data can contain bytes that are not valid UTF-8 (e.g. mangled
    emoji in campaign notes). Node decodes those lossily into U+FFFD instead of
    throwing; Python's default `str` factory raises UnicodeDecodeError, which
    surfaced as a 500 where the TS server returns 200.
    """
    return value.decode("utf-8", "replace")


def get_db() -> sqlite3.Connection:
    global _db
    with _db_lock:
        if _db is None:
            _db = sqlite3.connect(
                str(settings.db_path), isolation_level=None, check_same_thread=False
            )
            _db.row_factory = sqlite3.Row
            _db.text_factory = _lossy_text
            _db.execute("PRAGMA journal_mode = WAL")
            _db.execute("PRAGMA foreign_keys = ON")
            # The TS server and this server may both hold the DB open; wait
            # instead of failing immediately with "database is locked".
            _db.execute("PRAGMA busy_timeout = 5000")
            info("Database connected", {"path": str(settings.db_path)})
            run_migrations(_db)
        return _db


def close_db() -> None:
    global _db
    with _db_lock:
        if _db is not None:
            _db.close()
            _db = None
            info("Database closed")


def reset_db() -> None:
    """Drop all tables and re-run migrations. Test-only helper."""
    with _db_lock:
        db = get_db()
        db.execute("PRAGMA foreign_keys = OFF")
        try:
            for table in _TABLES:
                db.execute(f"DROP TABLE IF EXISTS {table}")
            run_migrations(db)
        finally:
            db.execute("PRAGMA foreign_keys = ON")


@contextmanager
def db_conn():
    """Serialize access to the shared connection."""
    with _db_lock:
        yield get_db()


@contextmanager
def transaction():
    """Explicit BEGIN/COMMIT with rollback, mirroring better-sqlite3 transactions."""
    with _db_lock:
        db = get_db()
        db.execute("BEGIN")
        try:
            yield db
            db.execute("COMMIT")
        except BaseException:
            db.execute("ROLLBACK")
            raise


def _fmt(dt: datetime) -> str:
    # Match JS Date.toISOString(): millisecond precision + 'Z', so string
    # comparisons against rows written by the TS server stay consistent.
    return dt.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + "Z"


def now_iso() -> str:
    return _fmt(datetime.now(timezone.utc))


def utc_iso(dt: datetime) -> str:
    return _fmt(dt)


def hours_ago_iso(hours: float) -> str:
    return _fmt(datetime.now(timezone.utc) - timedelta(hours=hours))