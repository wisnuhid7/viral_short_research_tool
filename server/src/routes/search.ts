import { Router } from 'express';
import { searchRequestSchema } from 'shared';
import { ValidationError } from '../lib/errors.js';
import { config } from '../lib/config.js';
import { getQuotaStatus } from '../lib/quota-tracker.js';
import { logger } from '../lib/logger.js';
import {
  searchShorts,
  getVideoDetails,
  getChannelDetails,
} from '../services/youtube.js';
import { calculateViralScores } from '../services/scoring/viral-score.js';
import { extractKeywordSuggestions } from '../services/keyword-suggest.js';
import {
  getCachedSearch,
  saveSearch,
  upsertVideo,
  upsertChannel,
  getVideosByIds,
  getChannelsByIds,
} from '../db/queries.js';

export const searchRouter = Router();

/**
 * POST /api/search
 * Search YouTube Shorts by keyword, return scored results with suggestions.
 */
searchRouter.post('/', async (req, res, next) => {
  try {
    const parsed = searchRequestSchema.safeParse(req.body);
    if (!parsed.success) {
      throw new ValidationError(
        `Input tidak valid: ${parsed.error.issues.map((i) => i.message).join(', ')}`
      );
    }

    const { keyword, timeRange, language, maxDuration } = parsed.data;
    const ttl = config.cache.ttlHours;

    // 1. Check cache
    const cached = getCachedSearch(keyword, timeRange, ttl);
    let videos;
    let cachedAt: string | null = null;

    if (cached && cached.videoIds.length > 0) {
      logger.info('Search cache hit', { keyword, timeRange });
      videos = getVideosByIds(cached.videoIds);
      cachedAt = new Date().toISOString(); // indicate it was from cache
    } else {
      // 2. Search YouTube
      const videoIds = await searchShorts(keyword, timeRange, language, maxDuration);

      if (videoIds.length === 0) {
        const quota = getQuotaStatus();
        res.json({
          keyword,
          videos: [],
          suggestions: [],
          quotaUsed: quota.used,
          quotaRemaining: quota.remaining,
          cachedAt: null,
        });
        return;
      }

      // 3. Get video details (batch, 1 unit per call)
      const videoDetails = await getVideoDetails(videoIds);

      // Filter by maxDuration and isShort
      videos = videoDetails.filter(
        (v) => v.duration <= maxDuration && v.isShort
      );

      // 4. Get channel details for subscriber counts (batch)
      const uniqueChannelIds = [...new Set(videos.map((v) => v.channelId))];
      const channelDetails = await getChannelDetails(uniqueChannelIds);

      // 5. Persist to DB
      for (const ch of channelDetails) {
        upsertChannel(ch);
      }
      for (const v of videos) {
        upsertVideo(v);
      }

      // Save search for cache
      saveSearch(keyword, timeRange, language, maxDuration, videos.map((v) => v.id));
    }

    // 6. Get channel info for scoring
    const channelIds = [...new Set(videos.map((v) => v.channelId))];
    const channelMap = getChannelsByIds(channelIds);

    // 7. Calculate viral scores
    const scoringInput = videos.map((v) => ({
      video: v,
      subscriberCount: channelMap.get(v.channelId)?.subscriberCount ?? 0,
    }));

    const scores = calculateViralScores(scoringInput);
    const scoreMap = new Map(scores.map((s) => [s.videoId, s]));

    // 8. Build response sorted by viral score
    const videosWithScores = videos
      .map((v) => ({
        ...v,
        viralScore: scoreMap.get(v.id)!,
        subscriberCount: channelMap.get(v.channelId)?.subscriberCount,
      }))
      .sort((a, b) => b.viralScore.totalScore - a.viralScore.totalScore);

    // 9. Extract keyword suggestions
    const suggestions = extractKeywordSuggestions(keyword, videos);

    // 10. Return
    const quota = getQuotaStatus();
    res.json({
      keyword,
      videos: videosWithScores,
      suggestions,
      quotaUsed: quota.used,
      quotaRemaining: quota.remaining,
      cachedAt,
    });
  } catch (err) {
    next(err);
  }
});
