import { getDb } from './schema.js';
import type { Video, Channel, Summary, KeywordSuggestion } from 'shared';

// ─── Videos ──────────────────────────────────────────────

export function upsertVideo(video: Video): void {
  const db = getDb();
  db.prepare(`
    INSERT INTO videos (id, title, description, channel_id, channel_title, published_at,
      thumbnail_url, duration, view_count, like_count, comment_count, tags, is_short, fetched_at)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ON CONFLICT(id) DO UPDATE SET
      view_count = excluded.view_count,
      like_count = excluded.like_count,
      comment_count = excluded.comment_count,
      fetched_at = excluded.fetched_at
  `).run(
    video.id, video.title, video.description, video.channelId, video.channelTitle,
    video.publishedAt, video.thumbnailUrl, video.duration, video.viewCount,
    video.likeCount, video.commentCount, JSON.stringify(video.tags),
    video.isShort ? 1 : 0, video.fetchedAt,
  );
}

export function getVideo(id: string): Video | undefined {
  const db = getDb();
  const row = db.prepare('SELECT * FROM videos WHERE id = ?').get(id) as Record<string, unknown> | undefined;
  if (!row) return undefined;
  return rowToVideo(row);
}

export function getVideosByIds(ids: string[]): Video[] {
  if (ids.length === 0) return [];
  const db = getDb();
  const placeholders = ids.map(() => '?').join(',');
  const rows = db.prepare(`SELECT * FROM videos WHERE id IN (${placeholders})`).all(...ids) as Record<string, unknown>[];
  return rows.map(rowToVideo);
}

function rowToVideo(row: Record<string, unknown>): Video {
  return {
    id: row['id'] as string,
    title: row['title'] as string,
    description: row['description'] as string,
    channelId: row['channel_id'] as string,
    channelTitle: row['channel_title'] as string,
    publishedAt: row['published_at'] as string,
    thumbnailUrl: row['thumbnail_url'] as string,
    duration: row['duration'] as number,
    viewCount: row['view_count'] as number,
    likeCount: row['like_count'] as number,
    commentCount: row['comment_count'] as number,
    tags: JSON.parse(row['tags'] as string) as string[],
    isShort: (row['is_short'] as number) === 1,
    fetchedAt: row['fetched_at'] as string,
  };
}

// ─── Channels ────────────────────────────────────────────

export function upsertChannel(channel: Channel): void {
  const db = getDb();
  db.prepare(`
    INSERT INTO channels (id, title, subscriber_count, thumbnail_url, fetched_at)
    VALUES (?, ?, ?, ?, ?)
    ON CONFLICT(id) DO UPDATE SET
      subscriber_count = excluded.subscriber_count,
      fetched_at = excluded.fetched_at
  `).run(channel.id, channel.title, channel.subscriberCount, channel.thumbnailUrl ?? null, channel.fetchedAt);
}

export function getChannel(id: string): Channel | undefined {
  const db = getDb();
  const row = db.prepare('SELECT * FROM channels WHERE id = ?').get(id) as Record<string, unknown> | undefined;
  if (!row) return undefined;
  return {
    id: row['id'] as string,
    title: row['title'] as string,
    subscriberCount: row['subscriber_count'] as number,
    thumbnailUrl: (row['thumbnail_url'] as string) ?? undefined,
    fetchedAt: row['fetched_at'] as string,
  };
}

export function getChannelsByIds(ids: string[]): Map<string, Channel> {
  if (ids.length === 0) return new Map();
  const db = getDb();
  const placeholders = ids.map(() => '?').join(',');
  const rows = db.prepare(`SELECT * FROM channels WHERE id IN (${placeholders})`).all(...ids) as Record<string, unknown>[];
  const map = new Map<string, Channel>();
  for (const row of rows) {
    const ch: Channel = {
      id: row['id'] as string,
      title: row['title'] as string,
      subscriberCount: row['subscriber_count'] as number,
      thumbnailUrl: (row['thumbnail_url'] as string) ?? undefined,
      fetchedAt: row['fetched_at'] as string,
    };
    map.set(ch.id, ch);
  }
  return map;
}

// ─── Keyword Searches (cache) ────────────────────────────

export function getCachedSearch(keyword: string, timeRange: string, ttlHours: number): { searchId: number; videoIds: string[] } | undefined {
  const db = getDb();
  const cutoff = new Date(Date.now() - ttlHours * 3600 * 1000).toISOString();
  const row = db.prepare(`
    SELECT id FROM keyword_searches
    WHERE keyword = ? AND time_range = ? AND searched_at > ?
    ORDER BY searched_at DESC LIMIT 1
  `).get(keyword.toLowerCase(), timeRange, cutoff) as { id: number } | undefined;

  if (!row) return undefined;

  const results = db.prepare(
    'SELECT video_id FROM keyword_search_results WHERE search_id = ?'
  ).all(row.id) as { video_id: string }[];

  return {
    searchId: row.id,
    videoIds: results.map((r) => r.video_id),
  };
}

export function saveSearch(keyword: string, timeRange: string, language: string, maxDuration: number, videoIds: string[]): number {
  const db = getDb();
  return db.transaction(() => {
    const result = db.prepare(`
      INSERT INTO keyword_searches (keyword, time_range, language, max_duration, result_count, searched_at)
      VALUES (?, ?, ?, ?, ?, ?)
    `).run(keyword.toLowerCase(), timeRange, language, maxDuration, videoIds.length, new Date().toISOString());

    const searchId = result.lastInsertRowid as number;

    const insert = db.prepare('INSERT OR IGNORE INTO keyword_search_results (search_id, video_id) VALUES (?, ?)');
    for (const videoId of videoIds) {
      insert.run(searchId, videoId);
    }

    return searchId;
  })();
}

// ─── Summaries ───────────────────────────────────────────

export function getSummary(videoId: string, promptVersion: string): Summary | undefined {
  const db = getDb();
  const row = db.prepare(
    'SELECT * FROM summaries WHERE video_id = ? AND prompt_version = ?'
  ).get(videoId, promptVersion) as Record<string, unknown> | undefined;

  if (!row) return undefined;

  return {
    videoId: row['video_id'] as string,
    topic: row['topic'] as string,
    hookFirst3Seconds: row['hook_first_3_seconds'] as string,
    structure: {
      hook: row['structure_hook'] as string,
      body: row['structure_body'] as string,
      cta: row['structure_cta'] as string,
    },
    style: row['style'] as string,
    keyMoments: JSON.parse(row['key_moments'] as string) as string[],
    confidence: row['confidence'] as 'high' | 'low',
    sourceType: row['source_type'] as 'transcript' | 'title_description',
    promptVersion: row['prompt_version'] as string,
    createdAt: row['created_at'] as string,
  };
}

export function saveSummary(summary: Summary): void {
  const db = getDb();
  db.prepare(`
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
  `).run(
    summary.videoId, summary.topic, summary.hookFirst3Seconds,
    summary.structure.hook, summary.structure.body, summary.structure.cta,
    summary.style, JSON.stringify(summary.keyMoments), summary.confidence,
    summary.sourceType, summary.promptVersion, summary.createdAt,
  );
}

// ─── Keyword Suggestions ────────────────────────────────

export function saveKeywordSuggestions(suggestions: KeywordSuggestion[]): void {
  const db = getDb();
  const insert = db.prepare(`
    INSERT INTO keyword_suggestions (keyword, source, frequency, parent_keyword)
    VALUES (?, ?, ?, ?)
  `);
  db.transaction(() => {
    for (const s of suggestions) {
      insert.run(s.keyword, s.source, s.frequency, s.parentKeyword);
    }
  })();
}

export function getKeywordSuggestions(parentKeyword: string): KeywordSuggestion[] {
  const db = getDb();
  const rows = db.prepare(`
    SELECT keyword, source, SUM(frequency) as frequency, parent_keyword
    FROM keyword_suggestions
    WHERE parent_keyword = ?
    GROUP BY keyword, source
    ORDER BY frequency DESC
    LIMIT 30
  `).all(parentKeyword.toLowerCase()) as Record<string, unknown>[];

  return rows.map((row) => ({
    keyword: row['keyword'] as string,
    source: row['source'] as 'tag' | 'title_word' | 'autocomplete',
    frequency: row['frequency'] as number,
    parentKeyword: row['parent_keyword'] as string,
  }));
}

// ─── Collections ─────────────────────────────────────────

export function createCollection(name: string, description: string): number {
  const db = getDb();
  const now = new Date().toISOString();
  const result = db.prepare(
    'INSERT INTO collections (name, description, created_at, updated_at) VALUES (?, ?, ?, ?)'
  ).run(name, description, now, now);
  return result.lastInsertRowid as number;
}

export function getCollections() {
  const db = getDb();
  return db.prepare('SELECT * FROM collections ORDER BY updated_at DESC').all() as {
    id: number; name: string; description: string; created_at: string; updated_at: string;
  }[];
}

export function getCollectionItems(collectionId: number) {
  const db = getDb();
  return db.prepare(`
    SELECT ci.*, v.title as video_title, v.thumbnail_url, v.view_count, v.channel_title
    FROM collection_items ci
    JOIN videos v ON ci.video_id = v.id
    WHERE ci.collection_id = ?
    ORDER BY ci.added_at DESC
  `).all(collectionId) as Record<string, unknown>[];
}

export function addToCollection(collectionId: number, videoId: string, tags: string[], notes: string): void {
  const db = getDb();
  db.transaction(() => {
    db.prepare(`
      INSERT INTO collection_items (collection_id, video_id, tags, notes, added_at)
      VALUES (?, ?, ?, ?, ?)
      ON CONFLICT(collection_id, video_id) DO UPDATE SET
        tags = excluded.tags,
        notes = excluded.notes
    `).run(collectionId, videoId, JSON.stringify(tags), notes, new Date().toISOString());

    db.prepare('UPDATE collections SET updated_at = ? WHERE id = ?')
      .run(new Date().toISOString(), collectionId);
  })();
}

export function removeFromCollection(collectionId: number, videoId: string): void {
  const db = getDb();
  db.prepare('DELETE FROM collection_items WHERE collection_id = ? AND video_id = ?')
    .run(collectionId, videoId);
}

export function deleteCollection(collectionId: number): void {
  const db = getDb();
  db.prepare('DELETE FROM collections WHERE id = ?').run(collectionId);
}
