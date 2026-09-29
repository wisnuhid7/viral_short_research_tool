import type { Video, KeywordSuggestion } from 'shared';
import { saveKeywordSuggestions, getKeywordSuggestions } from '../db/queries.js';
import { logger } from '../lib/logger.js';

// ─── Stop words (common Indonesian + English) ────────────

const STOP_WORDS = new Set([
  // English
  'the', 'a', 'an', 'is', 'are', 'was', 'were', 'be', 'been', 'being',
  'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would', 'could',
  'should', 'may', 'might', 'shall', 'can', 'this', 'that', 'these',
  'those', 'i', 'you', 'he', 'she', 'it', 'we', 'they', 'me', 'him',
  'her', 'us', 'them', 'my', 'your', 'his', 'its', 'our', 'their',
  'what', 'which', 'who', 'whom', 'where', 'when', 'why', 'how',
  'not', 'no', 'nor', 'but', 'and', 'or', 'if', 'then', 'else',
  'for', 'of', 'to', 'in', 'on', 'at', 'by', 'with', 'from', 'up',
  'about', 'into', 'over', 'after', 'so', 'than', 'too', 'very',
  // Indonesian
  'yang', 'dan', 'di', 'ke', 'dari', 'ini', 'itu', 'untuk', 'dengan',
  'pada', 'adalah', 'akan', 'sudah', 'juga', 'atau', 'ada', 'tidak',
  'bisa', 'saya', 'kamu', 'dia', 'kami', 'mereka', 'satu', 'dua',
  'tiga', 'nya', 'lagi', 'baru', 'jadi', 'aja', 'gak', 'ga', 'ya',
  'nih', 'dong', 'sih', 'loh', 'deh', 'kan', 'banget',
  // Common in titles
  'shorts', 'short', 'video', 'part',
]);

/**
 * Extract keyword suggestions from search result videos.
 * Sources: video tags and frequently-occurring title words.
 */
export function extractKeywordSuggestions(
  parentKeyword: string,
  videos: Video[],
): KeywordSuggestion[] {
  const tagFrequency = new Map<string, number>();
  const titleWordFrequency = new Map<string, number>();
  const parentLower = parentKeyword.toLowerCase();

  for (const video of videos) {
    // Tags
    for (const tag of video.tags) {
      const normalized = tag.toLowerCase().trim();
      if (normalized.length > 1 && normalized !== parentLower && !STOP_WORDS.has(normalized)) {
        tagFrequency.set(normalized, (tagFrequency.get(normalized) ?? 0) + 1);
      }
    }

    // Title words (2+ character words, not stop words)
    const words = video.title
      .toLowerCase()
      .replace(/[^\w\s]/g, ' ')
      .split(/\s+/)
      .filter((w) => w.length > 2 && !STOP_WORDS.has(w) && w !== parentLower);

    for (const word of words) {
      titleWordFrequency.set(word, (titleWordFrequency.get(word) ?? 0) + 1);
    }
  }

  const suggestions: KeywordSuggestion[] = [];

  // Tags with frequency ≥ 2
  for (const [keyword, freq] of tagFrequency) {
    if (freq >= 2) {
      suggestions.push({
        keyword,
        source: 'tag',
        frequency: freq,
        parentKeyword: parentLower,
      });
    }
  }

  // Title words with frequency ≥ 3
  for (const [keyword, freq] of titleWordFrequency) {
    if (freq >= 3) {
      suggestions.push({
        keyword,
        source: 'title_word',
        frequency: freq,
        parentKeyword: parentLower,
      });
    }
  }

  // Sort by frequency descending, limit to top 30
  suggestions.sort((a, b) => b.frequency - a.frequency);
  const top = suggestions.slice(0, 30);

  // Persist to DB
  if (top.length > 0) {
    saveKeywordSuggestions(top);
    logger.info('Keyword suggestions saved', { parentKeyword, count: top.length });
  }

  return top;
}

/**
 * Get cached keyword suggestions from DB.
 */
export function getCachedKeywordSuggestions(parentKeyword: string): KeywordSuggestion[] {
  return getKeywordSuggestions(parentKeyword);
}
