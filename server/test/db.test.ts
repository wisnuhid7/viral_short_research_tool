import { describe, it, expect, beforeEach } from 'vitest';
import {
  upsertVideo,
  getVideo,
  getVideosByIds,
  upsertChannel,
  getChannel,
  saveSearch,
  getCachedSearch,
  createCollection,
  getCollections,
  addToCollection,
  getCollectionItems,
  deleteCollection,
  saveSummary,
  getSummary,
} from '../src/db/queries.js';
import { mockVideos } from './fixtures/videos.js';
import type { Channel, Summary } from 'shared';

describe('database queries', () => {
  beforeEach(() => {
    upsertChannel({
      id: 'ch1',
      title: 'Tech Wizard',
      subscriberCount: 100000,
      fetchedAt: new Date().toISOString(),
    });
    upsertChannel({
      id: 'ch2',
      title: 'Side Hustle Pro',
      subscriberCount: 50000,
      fetchedAt: new Date().toISOString(),
    });
  });

  it('upserts and retrieves videos', () => {
    const video = mockVideos[0];
    upsertVideo(video);

    const retrieved = getVideo(video.id);
    expect(retrieved).toBeDefined();
    expect(retrieved?.id).toBe(video.id);
    expect(retrieved?.title).toBe(video.title);
    expect(retrieved?.viewCount).toBe(video.viewCount);

    const batch = getVideosByIds([video.id]);
    expect(batch.length).toBe(1);
    expect(batch[0].id).toBe(video.id);
  });

  it('upserts and retrieves channels', () => {
    const channel: Channel = {
      id: 'ch_test',
      title: 'Channel Test',
      subscriberCount: 50000,
      thumbnailUrl: 'https://example.com/thumb.jpg',
      fetchedAt: new Date().toISOString(),
    };

    upsertChannel(channel);
    const retrieved = getChannel('ch_test');
    expect(retrieved).toBeDefined();
    expect(retrieved?.title).toBe('Channel Test');
    expect(retrieved?.subscriberCount).toBe(50000);
  });

  it('saves and checks cached searches', () => {
    // Upsert videos first to satisfy foreign key constraints
    upsertVideo(mockVideos[0]);
    upsertVideo(mockVideos[1]);

    const keyword = 'test_keyword_' + Date.now();
    saveSearch(keyword, '24h', 'en', 60, [mockVideos[0].id, mockVideos[1].id]);

    const cached = getCachedSearch(keyword, '24h', 24);
    expect(cached).toBeDefined();
    expect(cached?.videoIds).toEqual([mockVideos[0].id, mockVideos[1].id]);

    const missed = getCachedSearch(keyword, '7d', 24);
    expect(missed).toBeUndefined();
  });

  it('handles collections lifecycle', () => {
    const collId = createCollection('My Test Collection', 'Test description');
    expect(collId).toBeGreaterThan(0);

    const collections = getCollections();
    expect(collections.some((c) => c.id === collId)).toBe(true);

    // Add video to collection
    upsertVideo(mockVideos[0]);
    addToCollection(collId, mockVideos[0].id, ['hook-test'], 'Check hook pattern');

    const collItems = getCollectionItems(collId);
    expect(collItems.length).toBe(1);
    expect(collItems[0].video_id).toBe(mockVideos[0].id);

    // Delete collection
    deleteCollection(collId);
    const afterDelete = getCollections();
    expect(afterDelete.some((c) => c.id === collId)).toBe(false);
  });

  it('saves and retrieves summaries', () => {
    upsertVideo(mockVideos[0]);

    const summary: Summary = {
      videoId: mockVideos[0].id,
      topic: 'AI Tools',
      hookFirst3Seconds: 'Stop scrolling if you want to save time',
      structure: {
        hook: 'Top 5 tools revealed in first 3s',
        body: 'Walkthrough of tools 1-5',
        cta: 'Comment for full prompt library',
      },
      style: 'Fast-paced screenshare with voiceover',
      keyMoments: ['0:00 Hook', '0:15 Tool 2', '0:40 CTA'],
      confidence: 'high',
      sourceType: 'transcript',
      promptVersion: 'v1.0',
      createdAt: new Date().toISOString(),
    };

    saveSummary(summary);
    const retrieved = getSummary(mockVideos[0].id, 'v1.0');
    expect(retrieved).toBeDefined();
    expect(retrieved?.structure.hook).toBe('Top 5 tools revealed in first 3s');
    expect(retrieved?.confidence).toBe('high');
  });
});
