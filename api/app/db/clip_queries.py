"""Clip feature persistence.

Kept separate from `queries.py` (a faithful port of the TS queries module) so the
ported file stays a clean mirror of `server/src/db/queries.ts`.
"""
from typing import Any

from api.app.db.database import db_conn, now_iso, transaction

_SOURCE_FIELDS = {
    "title",
    "duration_seconds",
    "local_path",
    "transcript_path",
    "status",
    "error_message",
}

_CLIP_FIELDS = {
    "title",
    "reason",
    "start_seconds",
    "end_seconds",
    "mode",
    "subtitles",
    "status",
    "output_path",
    "error_message",
}


def _row_to_source(row) -> dict:
    return {
        "id": row["id"],
        "sourceType": row["source_type"],
        "sourceRef": row["source_ref"],
        "title": row["title"],
        "durationSeconds": row["duration_seconds"],
        "localPath": row["local_path"],
        "transcriptPath": row["transcript_path"],
        "status": row["status"],
        "errorMessage": row["error_message"],
        "createdAt": row["created_at"],
        "updatedAt": row["updated_at"],
    }


def _row_to_clip(row) -> dict:
    return {
        "id": row["id"],
        "sourceId": row["source_id"],
        "title": row["title"],
        "reason": row["reason"],
        "startSeconds": row["start_seconds"],
        "endSeconds": row["end_seconds"],
        "mode": row["mode"],
        "subtitles": bool(row["subtitles"]),
        "status": row["status"],
        "outputPath": row["output_path"],
        "errorMessage": row["error_message"],
        "createdAt": row["created_at"],
        "updatedAt": row["updated_at"],
    }


# ─── Sources ─────────────────────────────────────────────


def create_clip_source(source_type: str, source_ref: str, title: str | None = None) -> dict:
    now = now_iso()
    with db_conn() as db:
        cur = db.execute(
            """
            INSERT INTO clip_sources (source_type, source_ref, title, status, created_at, updated_at)
            VALUES (?, ?, ?, 'pending', ?, ?)
            """,
            (source_type, source_ref, title, now, now),
        )
        source_id = cur.lastrowid
    return get_clip_source(source_id)  # type: ignore[return-value]


def get_clip_source(source_id: int) -> dict | None:
    with db_conn() as db:
        row = db.execute("SELECT * FROM clip_sources WHERE id = ?", (source_id,)).fetchone()
    return _row_to_source(row) if row else None


def list_clip_sources() -> list[dict]:
    with db_conn() as db:
        rows = db.execute("SELECT * FROM clip_sources ORDER BY created_at DESC").fetchall()
    return [_row_to_source(r) for r in rows]


def update_clip_source(source_id: int, **fields: Any) -> None:
    updates = {k: v for k, v in fields.items() if k in _SOURCE_FIELDS}
    if not updates:
        return
    updates["updated_at"] = now_iso()
    assignments = ", ".join(f"{k} = ?" for k in updates)
    with db_conn() as db:
        db.execute(
            f"UPDATE clip_sources SET {assignments} WHERE id = ?",
            (*updates.values(), source_id),
        )


def delete_clip_source(source_id: int) -> None:
    with transaction() as db:
        db.execute("DELETE FROM clips WHERE source_id = ?", (source_id,))
        db.execute("DELETE FROM clip_sources WHERE id = ?", (source_id,))


# ─── Clips ───────────────────────────────────────────────


def create_clip(
    source_id: int,
    title: str,
    start_seconds: float,
    end_seconds: float,
    mode: str = "crop",
    subtitles: bool = False,
    reason: str | None = None,
    status: str = "pending",
) -> dict:
    now = now_iso()
    with db_conn() as db:
        cur = db.execute(
            """
            INSERT INTO clips (source_id, title, reason, start_seconds, end_seconds, mode,
              subtitles, status, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                source_id,
                title,
                reason,
                start_seconds,
                end_seconds,
                mode,
                1 if subtitles else 0,
                status,
                now,
                now,
            ),
        )
        clip_id = cur.lastrowid
    return get_clip(clip_id)  # type: ignore[return-value]


def get_clip(clip_id: int) -> dict | None:
    with db_conn() as db:
        row = db.execute("SELECT * FROM clips WHERE id = ?", (clip_id,)).fetchone()
    return _row_to_clip(row) if row else None


def list_clips(source_id: int | None = None) -> list[dict]:
    with db_conn() as db:
        if source_id is None:
            rows = db.execute("SELECT * FROM clips ORDER BY created_at DESC").fetchall()
        else:
            rows = db.execute(
                "SELECT * FROM clips WHERE source_id = ? ORDER BY created_at DESC", (source_id,)
            ).fetchall()
    return [_row_to_clip(r) for r in rows]


def update_clip(clip_id: int, **fields: Any) -> None:
    updates = {k: v for k, v in fields.items() if k in _CLIP_FIELDS}
    if "subtitles" in updates:
        updates["subtitles"] = 1 if updates["subtitles"] else 0
    if not updates:
        return
    updates["updated_at"] = now_iso()
    assignments = ", ".join(f"{k} = ?" for k in updates)
    with db_conn() as db:
        db.execute(f"UPDATE clips SET {assignments} WHERE id = ?", (*updates.values(), clip_id))


def delete_clip(clip_id: int) -> None:
    with db_conn() as db:
        db.execute("DELETE FROM clips WHERE id = ?", (clip_id,))
