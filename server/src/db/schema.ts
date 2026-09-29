import Database from 'better-sqlite3';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { logger } from '../lib/logger.js';

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const DB_PATH = path.resolve(__dirname, '../../../data.db');

let db: Database.Database | null = null;

export function getDb(): Database.Database {
  if (!db) {
    db = new Database(DB_PATH);
    db.pragma('journal_mode = WAL');
    db.pragma('foreign_keys = ON');
    logger.info('Database connected', { path: DB_PATH });
    runMigrations(db);
  }
  return db;
}

export function closeDb(): void {
  if (db) {
    db.close();
    db = null;
    logger.info('Database closed');
  }
}

function runMigrations(database: Database.Database): void {
  database.exec(`
    CREATE TABLE IF NOT EXISTS _migrations (
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      name TEXT NOT NULL UNIQUE,
      applied_at TEXT NOT NULL DEFAULT (datetime('now'))
    )
  `);

  const applied = new Set(
    database
      .prepare('SELECT name FROM _migrations')
      .all()
      .map((row) => (row as { name: string }).name)
  );

  for (const migration of MIGRATIONS) {
    if (!applied.has(migration.name)) {
      logger.info('Running migration', { name: migration.name });
      database.transaction(() => {
        database.exec(migration.sql);
        database.prepare('INSERT INTO _migrations (name) VALUES (?)').run(migration.name);
      })();
    }
  }

  logger.info('All migrations applied');
}

// ─── Migrations ──────────────────────────────────────────

interface Migration {
  name: string;
  sql: string;
}

const MIGRATIONS: Migration[] = [
  {
    name: '001_initial_schema',
    sql: `
      CREATE TABLE channels (
        id TEXT PRIMARY KEY,
        title TEXT NOT NULL,
        subscriber_count INTEGER NOT NULL DEFAULT 0,
        thumbnail_url TEXT,
        fetched_at TEXT NOT NULL
      );

      CREATE TABLE videos (
        id TEXT PRIMARY KEY,
        title TEXT NOT NULL,
        description TEXT NOT NULL DEFAULT '',
        channel_id TEXT NOT NULL,
        channel_title TEXT NOT NULL,
        published_at TEXT NOT NULL,
        thumbnail_url TEXT NOT NULL,
        duration INTEGER NOT NULL,
        view_count INTEGER NOT NULL DEFAULT 0,
        like_count INTEGER NOT NULL DEFAULT 0,
        comment_count INTEGER NOT NULL DEFAULT 0,
        tags TEXT NOT NULL DEFAULT '[]',
        is_short INTEGER NOT NULL DEFAULT 1,
        fetched_at TEXT NOT NULL,
        FOREIGN KEY (channel_id) REFERENCES channels(id)
      );

      CREATE TABLE keyword_searches (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        keyword TEXT NOT NULL,
        time_range TEXT NOT NULL,
        language TEXT NOT NULL DEFAULT 'any',
        max_duration INTEGER NOT NULL DEFAULT 180,
        result_count INTEGER NOT NULL DEFAULT 0,
        searched_at TEXT NOT NULL
      );

      CREATE INDEX idx_keyword_searches_keyword ON keyword_searches(keyword, time_range);
      CREATE INDEX idx_keyword_searches_time ON keyword_searches(searched_at);

      CREATE TABLE keyword_search_results (
        search_id INTEGER NOT NULL,
        video_id TEXT NOT NULL,
        PRIMARY KEY (search_id, video_id),
        FOREIGN KEY (search_id) REFERENCES keyword_searches(id),
        FOREIGN KEY (video_id) REFERENCES videos(id)
      );

      CREATE TABLE keyword_suggestions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        keyword TEXT NOT NULL,
        source TEXT NOT NULL,
        frequency INTEGER NOT NULL DEFAULT 1,
        parent_keyword TEXT NOT NULL,
        created_at TEXT NOT NULL DEFAULT (datetime('now'))
      );

      CREATE INDEX idx_keyword_suggestions_parent ON keyword_suggestions(parent_keyword);

      CREATE TABLE summaries (
        video_id TEXT NOT NULL,
        topic TEXT NOT NULL,
        hook_first_3_seconds TEXT NOT NULL,
        structure_hook TEXT NOT NULL,
        structure_body TEXT NOT NULL,
        structure_cta TEXT NOT NULL,
        style TEXT NOT NULL,
        key_moments TEXT NOT NULL DEFAULT '[]',
        confidence TEXT NOT NULL DEFAULT 'high',
        source_type TEXT NOT NULL DEFAULT 'transcript',
        prompt_version TEXT NOT NULL,
        created_at TEXT NOT NULL,
        PRIMARY KEY (video_id, prompt_version),
        FOREIGN KEY (video_id) REFERENCES videos(id)
      );

      CREATE TABLE collections (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        description TEXT NOT NULL DEFAULT '',
        created_at TEXT NOT NULL DEFAULT (datetime('now')),
        updated_at TEXT NOT NULL DEFAULT (datetime('now'))
      );

      CREATE TABLE collection_items (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        collection_id INTEGER NOT NULL,
        video_id TEXT NOT NULL,
        tags TEXT NOT NULL DEFAULT '[]',
        notes TEXT NOT NULL DEFAULT '',
        added_at TEXT NOT NULL DEFAULT (datetime('now')),
        FOREIGN KEY (collection_id) REFERENCES collections(id) ON DELETE CASCADE,
        FOREIGN KEY (video_id) REFERENCES videos(id),
        UNIQUE(collection_id, video_id)
      );
    `,
  },
];
