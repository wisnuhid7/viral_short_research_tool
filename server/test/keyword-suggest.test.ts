import { describe, it, expect } from 'vitest';
import { extractKeywordSuggestions } from '../src/services/keyword-suggest.js';
import { mockVideos } from './fixtures/videos.js';

describe('keyword-suggest service', () => {
  it('extracts suggestions from tags and recurring words', () => {
    // Add multiple videos with repeated tags and title words
    const videos = [
      ...mockVideos,
      {
        ...mockVideos[0],
        id: 'vid4',
        title: 'Another top AI tools video for beginners',
        tags: ['tech', 'ai', 'productivity'],
      },
      {
        ...mockVideos[0],
        id: 'vid5',
        title: 'Must have AI tools in your workflow',
        tags: ['tech', 'ai'],
      },
    ];

    const suggestions = extractKeywordSuggestions('ai', videos);
    expect(suggestions.length).toBeGreaterThan(0);

    // 'tech' appears 4 times in tags (freq >= 2)
    const techTag = suggestions.find((s) => s.keyword === 'tech' && s.source === 'tag');
    expect(techTag).toBeDefined();
    expect(techTag?.frequency).toBeGreaterThanOrEqual(2);

    // Parent keyword 'ai' should be excluded from suggestions
    const parentInSuggestions = suggestions.some((s) => s.keyword === 'ai');
    expect(parentInSuggestions).toBe(false);
  });

  it('returns empty array when no videos provided', () => {
    const suggestions = extractKeywordSuggestions('ai', []);
    expect(suggestions).toEqual([]);
  });
});
