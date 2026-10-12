"""Database queries.

Port of server/src/db/queries.ts. Same SQL and same returned shapes:
camelCase dicts for typed rows, raw snake_case rows for collections.
"""
import json

from api.app.db.database import db_conn, hours_ago_iso, now_iso, transaction

_CATEGORIES = [
    "all",
    "ai_tech",
    "finance_crypto",
    "gaming",
    "business_sidehustle",
    "fitness_lifestyle",
    "entertainment",
    "other",
]


def _dumps(value) -> str:
    # Match JSON.stringify() (compact, no spaces, raw non-ASCII — Node does not
    # escape unicode, but Python's json defaults to ensure_ascii=True).
    return json.dumps(value, separators=(",", ":"), ensure_ascii=False)


def _loads(value: str | None, default):
    if value is None or value == "":
        return default
    return json.loads(value)


# ─── Videos ──────────────────────────────────────────────


def upsert_video(video: dict) -> None:
    with db_conn() as db:
        db.execute(
            """
            INSERT INTO videos (id, title, description, channel_id, channel_title, published_at,
              thumbnail_url, duration, view_count, like_count, comment_count, tags, is_short, fetched_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(id) DO UPDATE SET
              view_count = excluded.view_count,
              like_count = excluded.like_count,
              comment_count = excluded.comment_count,
              fetched_at = excluded.fetched_at
            """,
            (
                video["id"],
                video["title"],
                video["description"],
                video["channelId"],
                video["channelTitle"],
                video["publishedAt"],
                video["thumbnailUrl"],
                video["duration"],
                video["viewCount"],
                video["likeCount"],
                video["commentCount"],
                _dumps(video.get("tags", [])),
                1 if video.get("isShort") else 0,
                video["fetchedAt"],
            ),
        )


def _row_to_video(row) -> dict:
    return {
        "id": row["id"],
        "title": row["title"],
        "description": row["description"],
        "channelId": row["channel_id"],
        "channelTitle": row["channel_title"],
        "publishedAt": row["published_at"],
        "thumbnailUrl": row["thumbnail_url"],
        "duration": row["duration"],
        "viewCount": row["view_count"],
        "likeCount": row["like_count"],
        "commentCount": row["comment_count"],
        "tags": json.loads(row["tags"]),
        "isShort": row["is_short"] == 1,
        "fetchedAt": row["fetched_at"],
    }


def get_video(video_id: str) -> dict | None:
    with db_conn() as db:
        row = db.execute("SELECT * FROM videos WHERE id = ?", (video_id,)).fetchone()
    if row is None:
        return None
    return _row_to_video(row)


def get_videos_by_ids(ids: list[str]) -> list[dict]:
    if not ids:
        return []
    placeholders = ",".join("?" for _ in ids)
    with db_conn() as db:
        rows = db.execute(f"SELECT * FROM videos WHERE id IN ({placeholders})", tuple(ids)).fetchall()
    return [_row_to_video(r) for r in rows]


# ─── Channels ────────────────────────────────────────────


def upsert_channel(channel: dict) -> None:
    with db_conn() as db:
        db.execute(
            """
            INSERT INTO channels (id, title, subscriber_count, thumbnail_url, fetched_at)
            VALUES (?, ?, ?, ?, ?)
            ON CONFLICT(id) DO UPDATE SET
              subscriber_count = excluded.subscriber_count,
              fetched_at = excluded.fetched_at
            """,
            (
                channel["id"],
                channel["title"],
                channel["subscriberCount"],
                channel.get("thumbnailUrl", None),
                channel["fetchedAt"],
            ),
        )


def _row_to_channel(row) -> dict:
    return {
        "id": row["id"],
        "title": row["title"],
        "subscriberCount": row["subscriber_count"],
        "thumbnailUrl": row["thumbnail_url"] if row["thumbnail_url"] is not None else None,
        "fetchedAt": row["fetched_at"],
    }


def get_channel(channel_id: str) -> dict | None:
    with db_conn() as db:
        row = db.execute("SELECT * FROM channels WHERE id = ?", (channel_id,)).fetchone()
    if row is None:
        return None
    return _row_to_channel(row)


def get_channels_by_ids(ids: list[str]) -> dict[str, dict]:
    if not ids:
        return {}
    placeholders = ",".join("?" for _ in ids)
    with db_conn() as db:
        rows = db.execute(f"SELECT * FROM channels WHERE id IN ({placeholders})", tuple(ids)).fetchall()
    out: dict[str, dict] = {}
    for row in rows:
        ch = _row_to_channel(row)
        out[ch["id"]] = ch
    return out


# ─── Keyword Searches (cache) ────────────────────────────


def get_cached_search(keyword: str, time_range: str, ttl_hours: int) -> dict | None:
    cutoff = hours_ago_iso(ttl_hours)
    with db_conn() as db:
        row = db.execute(
            """
            SELECT id FROM keyword_searches
            WHERE keyword = ? AND time_range = ? AND searched_at > ?
            ORDER BY searched_at DESC LIMIT 1
            """,
            (keyword.lower(), time_range, cutoff),
        ).fetchone()
        if row is None:
            return None
        results = db.execute(
            "SELECT video_id FROM keyword_search_results WHERE search_id = ?", (row["id"],)
        ).fetchall()
    return {
        "searchId": row["id"],
        "videoIds": [r["video_id"] for r in results],
    }


def save_search(
    keyword: str, time_range: str, language: str, max_duration: int, video_ids: list[str]
) -> int:
    with transaction() as db:
        cur = db.execute(
            """
            INSERT INTO keyword_searches (keyword, time_range, language, max_duration, result_count, searched_at)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (keyword.lower(), time_range, language, max_duration, len(video_ids), now_iso()),
        )
        search_id = cur.lastrowid
        for video_id in video_ids:
            db.execute(
                "INSERT OR IGNORE INTO keyword_search_results (search_id, video_id) VALUES (?, ?)",
                (search_id, video_id),
            )
    return search_id


def get_recent_searches(limit: int = 10) -> list[dict]:
    with db_conn() as db:
        rows = db.execute(
            """
            SELECT keyword, time_range as timeRange, language, max_duration as maxDuration,
                   result_count as resultCount, MAX(searched_at) as searchedAt
            FROM keyword_searches
            GROUP BY keyword
            ORDER BY searchedAt DESC
            LIMIT ?
            """,
            (limit,),
        ).fetchall()
    return [
        {
            "keyword": r["keyword"],
            "timeRange": r["timeRange"],
            "language": r["language"],
            "maxDuration": r["maxDuration"],
            "resultCount": r["resultCount"],
            "searchedAt": r["searchedAt"],
        }
        for r in rows
    ]


# ─── Summaries ───────────────────────────────────────────


def get_summary(video_id: str, prompt_version: str) -> dict | None:
    with db_conn() as db:
        row = db.execute(
            "SELECT * FROM summaries WHERE video_id = ? AND prompt_version = ?",
            (video_id, prompt_version),
        ).fetchone()
    if row is None:
        return None
    return {
        "videoId": row["video_id"],
        "topic": row["topic"],
        "hookFirst3Seconds": row["hook_first_3_seconds"],
        "structure": {
            "hook": row["structure_hook"],
            "body": row["structure_body"],
            "cta": row["structure_cta"],
        },
        "style": row["style"],
        "keyMoments": json.loads(row["key_moments"]),
        "confidence": row["confidence"],
        "sourceType": row["source_type"],
        "promptVersion": row["prompt_version"],
        "createdAt": row["created_at"],
    }


def save_summary(summary: dict) -> None:
    with db_conn() as db:
        db.execute(
            """
            INSERT INTO summaries (video_id, topic, hook_first_3_seconds, structure_hook,
              structure_body, structure_cta, style, key_moments, confidence, source_type,
              prompt_version, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(video_id, prompt_version) DO UPDATE SET
              topic = excluded.topic,
              hook_first_3_seconds = excluded.hook_first_3_seconds,
              structure_hook = excluded.structure_hook,
              structure_body = excluded.structure_body,
              structure_cta = excluded.structure_cta,
              style = excluded.style,
              key_moments = excluded.key_moments,
              confidence = excluded.confidence,
              source_type = excluded.source_type,
              created_at = excluded.created_at
            """,
            (
                summary["videoId"],
                summary["topic"],
                summary["hookFirst3Seconds"],
                summary["structure"]["hook"],
                summary["structure"]["body"],
                summary["structure"]["cta"],
                summary["style"],
                _dumps(summary.get("keyMoments", [])),
                summary["confidence"],
                summary["sourceType"],
                summary["promptVersion"],
                summary["createdAt"],
            ),
        )


# ─── Keyword Suggestions ────────────────────────────────


def save_keyword_suggestions(suggestions: list[dict]) -> None:
    with transaction() as db:
        for s in suggestions:
            db.execute(
                """
                INSERT INTO keyword_suggestions (keyword, source, frequency, parent_keyword)
                VALUES (?, ?, ?, ?)
                """,
                (s["keyword"], s["source"], s["frequency"], s["parentKeyword"]),
            )


def get_keyword_suggestions(parent_keyword: str) -> list[dict]:
    with db_conn() as db:
        rows = db.execute(
            """
            SELECT keyword, source, SUM(frequency) as frequency, parent_keyword
            FROM keyword_suggestions
            WHERE parent_keyword = ?
            GROUP BY keyword, source
            ORDER BY frequency DESC
            LIMIT 30
            """,
            (parent_keyword.lower(),),
        ).fetchall()
    return [
        {
            "keyword": row["keyword"],
            "source": row["source"],
            "frequency": row["frequency"],
            "parentKeyword": row["parent_keyword"],
        }
        for row in rows
    ]


# ─── Collections ─────────────────────────────────────────


def create_collection(name: str, description: str) -> int:
    now = now_iso()
    with db_conn() as db:
        cur = db.execute(
            "INSERT INTO collections (name, description, created_at, updated_at) VALUES (?, ?, ?, ?)",
            (name, description, now, now),
        )
        return cur.lastrowid


def get_collections() -> list[dict]:
    with db_conn() as db:
        rows = db.execute("SELECT * FROM collections ORDER BY updated_at DESC").fetchall()
    return [dict(row) for row in rows]


def get_collection_items(collection_id: int) -> list[dict]:
    with db_conn() as db:
        rows = db.execute(
            """
            SELECT ci.*, v.title as video_title, v.thumbnail_url, v.view_count, v.channel_title
            FROM collection_items ci
            JOIN videos v ON ci.video_id = v.id
            WHERE ci.collection_id = ?
            ORDER BY ci.added_at DESC
            """,
            (collection_id,),
        ).fetchall()
    return [dict(row) for row in rows]


def add_to_collection(collection_id: int, video_id: str, tags: list[str], notes: str) -> None:
    with transaction() as db:
        db.execute(
            """
            INSERT INTO collection_items (collection_id, video_id, tags, notes, added_at)
            VALUES (?, ?, ?, ?, ?)
            ON CONFLICT(collection_id, video_id) DO UPDATE SET
              tags = excluded.tags,
              notes = excluded.notes
            """,
            (collection_id, video_id, _dumps(tags), notes, now_iso()),
        )
        db.execute(
            "UPDATE collections SET updated_at = ? WHERE id = ?", (now_iso(), collection_id)
        )


def remove_from_collection(collection_id: int, video_id: str) -> None:
    with db_conn() as db:
        db.execute(
            "DELETE FROM collection_items WHERE collection_id = ? AND video_id = ?",
            (collection_id, video_id),
        )


def delete_collection(collection_id: int) -> None:
    with db_conn() as db:
        db.execute("DELETE FROM collections WHERE id = ?", (collection_id,))


# ─── Campaigns ───────────────────────────────────────────


def _row_to_campaign(row) -> dict:
    category = row["category"]
    if category not in _CATEGORIES:
        category = "other"
    spots = row["spots_remaining"]
    return {
        "id": row["id"],
        "name": row["name"],
        "creatorOrBrand": row["creator_or_brand"],
        "category": category,
        "url": row["url"] if row["url"] is not None else "",
        "ratePerKViews": row["rate_per_k_views"],
        "totalBudget": row["total_budget"],
        "remainingBudget": row["remaining_budget"],
        "deadline": row["deadline"] if row["deadline"] is not None else None,
        "requiredHashtags": _loads(row["required_hashtags"], []),
        "requiredMentions": _loads(row["required_mentions"], []),
        "allowedPlatforms": _loads(row["allowed_platforms"], ["YouTube Shorts"]),
        "targetKeywords": _loads(row["target_keywords"], []),
        "notes": row["notes"] if row["notes"] is not None else "",
        "spotsRemaining": int(spots) if spots is not None else None,
        "isWhopLive": bool(row["is_whop_live"]),
        "whopGoalType": row["whop_goal_type"] if row["whop_goal_type"] is not None else None,
        "createdAt": row["created_at"],
        "updatedAt": row["updated_at"],
    }


def get_campaigns(category: str | None = None) -> list[dict]:
    query = "SELECT * FROM campaigns"
    params: list = []
    if category and category != "all":
        query += " WHERE category = ?"
        params.append(category)
    query += " ORDER BY rate_per_k_views DESC"
    with db_conn() as db:
        rows = db.execute(query, tuple(params)).fetchall()
    return [_row_to_campaign(r) for r in rows]


def get_campaign_by_id(campaign_id: str) -> dict | None:
    with db_conn() as db:
        row = db.execute("SELECT * FROM campaigns WHERE id = ?", (campaign_id,)).fetchone()
    if row is None:
        return None
    return _row_to_campaign(row)


def upsert_campaign(campaign: dict) -> None:
    with db_conn() as db:
        db.execute(
            """
            INSERT INTO campaigns (
              id, name, creator_or_brand, category, url, rate_per_k_views, total_budget,
              remaining_budget, deadline, required_hashtags, required_mentions,
              allowed_platforms, target_keywords, notes, spots_remaining, is_whop_live,
              whop_goal_type, created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(id) DO UPDATE SET
              name = excluded.name,
              creator_or_brand = excluded.creator_or_brand,
              category = excluded.category,
              url = excluded.url,
              rate_per_k_views = excluded.rate_per_k_views,
              total_budget = excluded.total_budget,
              remaining_budget = excluded.remaining_budget,
              deadline = excluded.deadline,
              required_hashtags = excluded.required_hashtags,
              required_mentions = excluded.required_mentions,
              allowed_platforms = excluded.allowed_platforms,
              target_keywords = excluded.target_keywords,
              notes = excluded.notes,
              spots_remaining = excluded.spots_remaining,
              is_whop_live = excluded.is_whop_live,
              whop_goal_type = excluded.whop_goal_type,
              updated_at = excluded.updated_at
            """,
            (
                campaign["id"],
                campaign["name"],
                campaign["creatorOrBrand"],
                campaign["category"],
                campaign.get("url", "") or "",
                campaign["ratePerKViews"],
                campaign["totalBudget"],
                campaign["remainingBudget"],
                campaign.get("deadline", None),
                _dumps(campaign.get("requiredHashtags", [])),
                _dumps(campaign.get("requiredMentions", [])),
                _dumps(campaign.get("allowedPlatforms", ["YouTube Shorts"])),
                _dumps(campaign.get("targetKeywords", [])),
                campaign.get("notes", "") or "",
                campaign.get("spotsRemaining", None),
                1 if campaign.get("isWhopLive") else 0,
                campaign.get("whopGoalType", None),
                campaign["createdAt"],
                campaign["updatedAt"],
            ),
        )


def delete_campaign(campaign_id: str) -> None:
    with db_conn() as db:
        db.execute("DELETE FROM campaigns WHERE id = ?", (campaign_id,))


def find_campaigns_by_keyword(keyword: str) -> list[dict]:
    term = f"%{keyword.lower()}%"
    with db_conn() as db:
        rows = db.execute(
            """
            SELECT * FROM campaigns
            WHERE lower(name) LIKE ? OR lower(target_keywords) LIKE ? OR lower(notes) LIKE ? OR lower(category) LIKE ?
            ORDER BY rate_per_k_views DESC
            """,
            (term, term, term, term),
        ).fetchall()
    return [_row_to_campaign(r) for r in rows]


# ─── Whop Sync Logs ──────────────────────────────────────


def record_whop_sync_log(
    synced_at: str, campaigns_count: int, status: str, error_message: str | None = None
) -> None:
    with db_conn() as db:
        db.execute(
            """
            INSERT INTO whop_sync_logs (synced_at, campaigns_count, status, error_message)
            VALUES (?, ?, ?, ?)
            """,
            (synced_at, campaigns_count, status, error_message),
        )


def get_latest_whop_sync_log() -> dict | None:
    with db_conn() as db:
        row = db.execute(
            """
            SELECT synced_at, campaigns_count, status, error_message
            FROM whop_sync_logs
            ORDER BY id DESC
            LIMIT 1
            """
        ).fetchone()
    if row is None:
        return None
    return {
        "syncedAt": row["synced_at"],
        "campaignsCount": row["campaigns_count"],
        "status": row["status"],
        "errorMessage": row["error_message"],
    }