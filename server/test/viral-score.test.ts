import { describe, it, expect } from 'vitest';
import {
  percentileNormalize,
  computeVelocity,
  computeReachRatio,
  computeEngagement,
  isYoungVideo,
  calculateViralScores,
  DEFAULT_WEIGHTS,
} from '../src/services/scoring/viral-score.js';
import { mockVideos } from './fixtures/videos.js';

describe('viral-score service', () => {
  describe('percentileNormalize', () => {
    it('returns empty array for empty input', () => {
      expect(percentileNormalize([])).toEqual([]);
    });

    it('returns 0.5 for single item', () => {
      expect(percentileNormalize([100])).toEqual([0.5]);
    });

    it('normalizes multiple values properly between 0 and 1', () => {
      const result = percentileNormalize([10, 30, 20]);
      // 10 is lowest (rank 0 / 2 = 0)
      // 20 is middle (rank 1 / 2 = 0.5)
      // 30 is highest (rank 2 / 2 = 1.0)
      expect(result).toEqual([0, 1, 0.5]);
    });
  });

  describe('computeVelocity', () => {
    it('computes views per hour correctly', () => {
      const oneHourAgo = new Date(Date.now() - 3600 * 1000).toISOString();
      const velocity = computeVelocity(1000, oneHourAgo);
      expect(velocity).toBeGreaterThan(950);
      expect(velocity).toBeLessThan(1050);
    });

    it('handles zero or recent publishedAt without crashing', () => {
      const now = new Date().toISOString();
      const velocity = computeVelocity(100, now);
      expect(velocity).toBeGreaterThan(0);
    });
  });

  describe('computeReachRatio', () => {
    it('calculates ratio of views to subscribers', () => {
      expect(computeReachRatio(10000, 1000)).toBe(10);
    });

    it('returns 0 when subscriber count is 0 or negative', () => {
      expect(computeReachRatio(10000, 0)).toBe(0);
      expect(computeReachRatio(10000, -5)).toBe(0);
    });

    it('caps ratio at 100 to prevent extreme outliers', () => {
      expect(computeReachRatio(1000000, 10)).toBe(100);
    });
  });

  describe('computeEngagement', () => {
    it('calculates (likes + comments) / views', () => {
      const eng = computeEngagement(100, 20, 1000);
      expect(eng).toBeCloseTo(0.12);
    });

    it('returns 0 for 0 views', () => {
      expect(computeEngagement(10, 5, 0)).toBe(0);
    });
  });

  describe('isYoungVideo', () => {
    it('returns true for videos younger than 3 hours', () => {
      const oneHourAgo = new Date(Date.now() - 3600 * 1000).toISOString();
      expect(isYoungVideo(oneHourAgo)).toBe(true);
    });

    it('returns false for videos older than 3 hours', () => {
      const fiveHoursAgo = new Date(Date.now() - 5 * 3600 * 1000).toISOString();
      expect(isYoungVideo(fiveHoursAgo)).toBe(false);
    });
  });

  describe('calculateViralScores', () => {
    it('returns empty array when no videos provided', () => {
      expect(calculateViralScores([])).toEqual([]);
    });

    it('calculates score with confidence penalty for young videos', () => {
      const items = [
        { video: mockVideos[0], subscriberCount: 10000 },
        { video: mockVideos[1], subscriberCount: 5000 },
        { video: mockVideos[2], subscriberCount: 10000 }, // < 3h old
      ];

      const scores = calculateViralScores(items, DEFAULT_WEIGHTS);
      expect(scores.length).toBe(3);

      const youngScore = scores.find((s) => s.videoId === 'vid3');
      expect(youngScore?.confidencePenalty).toBe(true);

      const olderScore = scores.find((s) => s.videoId === 'vid1');
      expect(olderScore?.confidencePenalty).toBe(false);
    });
  });
});
