import { describe, it, expect } from 'vitest';
import {
  searchRequestSchema,
  summaryRequestSchema,
  exportRequestSchema,
  createCollectionRequestSchema,
  videoSchema,
} from 'shared';
import { mockVideos } from './fixtures/videos.js';

describe('shared validation schemas', () => {
  it('validates search requests', () => {
    const valid = {
      keyword: 'crypto trading',
      timeRange: '24h',
      language: 'en',
      maxDuration: 60,
    };
    expect(searchRequestSchema.safeParse(valid).success).toBe(true);

    const invalid = {
      keyword: '', // min 1
      timeRange: 'invalid_range',
    };
    expect(searchRequestSchema.safeParse(invalid).success).toBe(false);
  });

  it('validates summarize requests', () => {
    expect(summaryRequestSchema.safeParse({ videoId: 'abc12345678' }).success).toBe(true);
    expect(summaryRequestSchema.safeParse({ videoId: '' }).success).toBe(false);
  });

  it('validates export requests', () => {
    const valid = {
      format: 'csv',
      videoIds: ['vid1', 'vid2'],
      includeSummaries: false,
    };
    expect(exportRequestSchema.safeParse(valid).success).toBe(true);
  });

  it('validates collection creation', () => {
    expect(createCollectionRequestSchema.safeParse({ name: 'Hook Library' }).success).toBe(true);
    expect(createCollectionRequestSchema.safeParse({ name: '' }).success).toBe(false);
  });

  it('validates video schema against mock videos', () => {
    for (const v of mockVideos) {
      expect(videoSchema.safeParse(v).success).toBe(true);
    }
  });
});
