import { config } from '../lib/config.js';
import { logger } from '../lib/logger.js';
import { ExternalApiError } from '../lib/errors.js';
import {
  checkQuota,
  recordQuotaUsage,
  type QuotaOperation,
} from '../lib/quota-tracker.js';
import type { Video, Channel, TimeRange } from 'shared';

const YOUTUBE_API_BASE = 'https://www.googleapis.com/youtube/v3';

// ─── Helpers ─────────────────────────────────────────────

async function ytFetch<T>(
  endpoint: string,
  params: Record<string, string>,
  quotaOp: QuotaOperation,
): Promise<T> {
  checkQuota(quotaOp);

  const url = new URL(`${YOUTUBE_API_BASE}/${endpoint}`);
  url.searchParams.set('key', config.youtube.apiKey);
  for (const [key, value] of Object.entries(params)) {
    url.searchParams.set(key, value);
  }

  const response = await fetch(url.toString());

  if (!response.ok) {
    const errorBody = await response.text();
    let detailedMessage = `HTTP ${response.status}`;
    
    try {
      const parsed = JSON.parse(errorBody);
      const firstError = parsed.error?.errors?.[0] || parsed.error;
      if (firstError?.message) {
        detailedMessage = firstError.message;
      }
    } catch {
      // ignore JSON parse error
    }

    logger.error('YouTube API error', { endpoint, status: response.status, details: detailedMessage });

    if (response.status === 403) {
      if (errorBody.includes('quotaExceeded')) {
        throw new ExternalApiError('YouTube', 'Kuota harian terlampaui oleh Google.');
      }
      throw new ExternalApiError('YouTube', `Akses ditolak (403): ${detailedMessage}`);
    }
    throw new ExternalApiError('YouTube', detailedMessage);
  }

  recordQuotaUsage(quotaOp);
  return response.json() as Promise<T>;
}

// ─── Time range → publishedAfter ─────────────────────────

function timeRangeToDate(range: TimeRange): string {
  const now = new Date();
  switch (range) {
    case '24h':
      now.setHours(now.getHours() - 24);
      break;
    case '7d':
      now.setDate(now.getDate() - 7);
      break;
    case '30d':
      now.setDate(now.getDate() - 30);
      break;
  }
  return now.toISOString();
}

// ─── ISO 8601 duration → seconds ─────────────────────────

function parseDuration(iso: string): number {
  const match = iso.match(/PT(?:(\d+)H)?(?:(\d+)M)?(?:(\d+)S)?/);
  if (!match) return 0;
  const hours = parseInt(match[1] ?? '0', 10);
  const minutes = parseInt(match[2] ?? '0', 10);
  const seconds = parseInt(match[3] ?? '0', 10);
  return hours * 3600 + minutes * 60 + seconds;
}

// ─── Search Shorts ───────────────────────────────────────

interface YTSearchItem {
  id: { videoId: string };
  snippet: {
    title: string;
    description: string;
    channelId: string;
    channelTitle: string;
    publishedAt: string;
    thumbnails: { medium?: { url: string }; default?: { url: string } };
  };
}

interface YTSearchResponse {
  items: YTSearchItem[];
  pageInfo: { totalResults: number };
}

export async function searchShorts(
  keyword: string,
  timeRange: TimeRange,
  language: string,
  _maxDuration?: number,
): Promise<string[]> {
  const params: Record<string, string> = {
    part: 'snippet',
    q: `${keyword} #shorts`,
    type: 'video',
    videoDuration: 'short', // ≤ 4 min
    order: 'viewCount',
    maxResults: '50',
    publishedAfter: timeRangeToDate(timeRange),
  };

  if (language !== 'any') {
    params['relevanceLanguage'] = language;
  }

  const data = await ytFetch<YTSearchResponse>('search', params, 'search.list');

  logger.info('YouTube search completed', {
    keyword,
    resultCount: data.items.length,
  });

  return data.items.map((item) => item.id.videoId);
}

// ─── Video Details (batch) ───────────────────────────────

interface YTVideoItem {
  id: string;
  snippet: {
    title: string;
    description: string;
    channelId: string;
    channelTitle: string;
    publishedAt: string;
    tags?: string[];
    thumbnails: { medium?: { url: string }; high?: { url: string }; default?: { url: string } };
  };
  contentDetails: { duration: string };
  statistics: {
    viewCount?: string;
    likeCount?: string;
    commentCount?: string;
  };
}

interface YTVideoResponse {
  items: YTVideoItem[];
}

export async function getVideoDetails(videoIds: string[]): Promise<Video[]> {
  if (videoIds.length === 0) return [];

  const videos: Video[] = [];
  const now = new Date().toISOString();

  // Batch in groups of 50
  for (let i = 0; i < videoIds.length; i += 50) {
    const batch = videoIds.slice(i, i + 50);
    const data = await ytFetch<YTVideoResponse>('videos', {
      part: 'snippet,contentDetails,statistics',
      id: batch.join(','),
    }, 'videos.list');

    for (const item of data.items) {
      const duration = parseDuration(item.contentDetails.duration);
      const title = item.snippet.title;
      const isShort = duration <= 180 || title.toLowerCase().includes('#shorts');

      const thumbnail =
        item.snippet.thumbnails.high?.url ??
        item.snippet.thumbnails.medium?.url ??
        item.snippet.thumbnails.default?.url ??
        '';

      videos.push({
        id: item.id,
        title,
        description: item.snippet.description,
        channelId: item.snippet.channelId,
        channelTitle: item.snippet.channelTitle,
        publishedAt: item.snippet.publishedAt,
        thumbnailUrl: thumbnail,
        duration,
        viewCount: parseInt(item.statistics.viewCount ?? '0', 10),
        likeCount: parseInt(item.statistics.likeCount ?? '0', 10),
        commentCount: parseInt(item.statistics.commentCount ?? '0', 10),
        tags: item.snippet.tags ?? [],
        isShort,
        fetchedAt: now,
      });
    }
  }

  return videos;
}

// ─── Channel Details (batch) ─────────────────────────────

interface YTChannelItem {
  id: string;
  snippet: {
    title: string;
    thumbnails: { default?: { url: string } };
  };
  statistics: {
    subscriberCount?: string;
    hiddenSubscriberCount?: boolean;
  };
}

interface YTChannelResponse {
  items: YTChannelItem[];
}

export async function getChannelDetails(channelIds: string[]): Promise<Channel[]> {
  if (channelIds.length === 0) return [];

  const channels: Channel[] = [];
  const now = new Date().toISOString();

  // Batch in groups of 50
  for (let i = 0; i < channelIds.length; i += 50) {
    const batch = channelIds.slice(i, i + 50);
    const data = await ytFetch<YTChannelResponse>('channels', {
      part: 'snippet,statistics',
      id: batch.join(','),
    }, 'channels.list');

    for (const item of data.items) {
      channels.push({
        id: item.id,
        title: item.snippet.title,
        subscriberCount: item.statistics.hiddenSubscriberCount
          ? 0
          : parseInt(item.statistics.subscriberCount ?? '0', 10),
        thumbnailUrl: item.snippet.thumbnails.default?.url,
        fetchedAt: now,
      });
    }
  }

  return channels;
}

// ─── Captions / Transcript ───────────────────────────────
// YouTube Data API captions.list requires OAuth, so we use the
// unofficial timedtext endpoint as a best-effort approach.

export async function getTranscript(videoId: string): Promise<string | null> {
  try {
    // Try fetching auto-generated captions via the timedtext endpoint
    const url = `https://www.youtube.com/watch?v=${videoId}`;
    const pageResp = await fetch(url);
    const pageHtml = await pageResp.text();

    // Extract caption track URL from page source
    const captionMatch = pageHtml.match(/"captionTracks":\s*(\[.*?\])/);
    if (!captionMatch?.[1]) return null;

    const tracks = JSON.parse(captionMatch[1]) as { baseUrl: string; languageCode: string }[];
    if (tracks.length === 0) return null;

    // Prefer English or first available
    const track = tracks.find((t) => t.languageCode === 'en') ?? tracks[0];
    if (!track) return null;

    const captionResp = await fetch(`${track.baseUrl}&fmt=srv3`);
    const captionXml = await captionResp.text();

    // Extract text from XML
    const textParts = captionXml.match(/<text[^>]*>(.*?)<\/text>/gs);
    if (!textParts) return null;

    const transcript = textParts
      .map((part) =>
        part
          .replace(/<[^>]+>/g, '')
          .replace(/&amp;/g, '&')
          .replace(/&lt;/g, '<')
          .replace(/&gt;/g, '>')
          .replace(/&quot;/g, '"')
          .replace(/&#39;/g, "'")
      )
      .join(' ')
      .trim();

    return transcript.length > 0 ? transcript : null;
  } catch (err) {
    logger.warn('Failed to fetch transcript', { videoId, error: String(err) });
    return null;
  }
}
