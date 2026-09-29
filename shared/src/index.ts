import { z } from 'zod';

// ─── Channel ─────────────────────────────────────────────

export const channelSchema = z.object({
  id: z.string(),
  title: z.string(),
  subscriberCount: z.number().int().nonnegative(),
  thumbnailUrl: z.string().url().optional(),
  fetchedAt: z.string().datetime(),
});

export type Channel = z.infer<typeof channelSchema>;

// ─── Video ───────────────────────────────────────────────

export const videoSchema = z.object({
  id: z.string(),
  title: z.string(),
  description: z.string(),
  channelId: z.string(),
  channelTitle: z.string(),
  publishedAt: z.string().datetime(),
  thumbnailUrl: z.string().url(),
  duration: z.number().int().positive(), // seconds
  viewCount: z.number().int().nonnegative(),
  likeCount: z.number().int().nonnegative(),
  commentCount: z.number().int().nonnegative(),
  tags: z.array(z.string()).default([]),
  isShort: z.boolean(),
  fetchedAt: z.string().datetime(),
});

export type Video = z.infer<typeof videoSchema>;

// ─── Viral Score ─────────────────────────────────────────

export const viralScoreSchema = z.object({
  videoId: z.string(),
  velocity: z.number(),
  velocityNorm: z.number().min(0).max(1),
  reachRatio: z.number(),
  reachRatioNorm: z.number().min(0).max(1),
  engagement: z.number(),
  engagementNorm: z.number().min(0).max(1),
  totalScore: z.number().min(0).max(1),
  confidencePenalty: z.boolean(), // true if video < 3 hours old
  sampleSize: z.number().int().positive(),
});

export type ViralScore = z.infer<typeof viralScoreSchema>;

// ─── Video with Score (combined for API response) ────────

export const videoWithScoreSchema = videoSchema.extend({
  viralScore: viralScoreSchema,
  subscriberCount: z.number().int().nonnegative().optional(),
});

export type VideoWithScore = z.infer<typeof videoWithScoreSchema>;

// ─── Summary ─────────────────────────────────────────────

export const summarySchema = z.object({
  videoId: z.string(),
  topic: z.string(),
  hookFirst3Seconds: z.string(),
  structure: z.object({
    hook: z.string(),
    body: z.string(),
    cta: z.string(),
  }),
  style: z.string(),
  keyMoments: z.array(z.string()).default([]),
  confidence: z.enum(['high', 'low']),
  sourceType: z.enum(['transcript', 'title_description']),
  promptVersion: z.string(),
  createdAt: z.string().datetime(),
});

export type Summary = z.infer<typeof summarySchema>;

// ─── Keyword Search ──────────────────────────────────────

export const timeRangeSchema = z.enum(['24h', '7d', '30d']);
export type TimeRange = z.infer<typeof timeRangeSchema>;

export const keywordSearchSchema = z.object({
  id: z.number().int().positive().optional(),
  keyword: z.string().min(1),
  timeRange: timeRangeSchema,
  language: z.string().default('any'),
  maxDuration: z.number().int().positive().default(180), // seconds
  resultCount: z.number().int().nonnegative(),
  searchedAt: z.string().datetime(),
});

export type KeywordSearch = z.infer<typeof keywordSearchSchema>;

// ─── Keyword Suggestion ──────────────────────────────────

export const keywordSuggestionSchema = z.object({
  keyword: z.string(),
  source: z.enum(['tag', 'title_word', 'autocomplete']),
  frequency: z.number().int().positive(),
  parentKeyword: z.string(),
});

export type KeywordSuggestion = z.infer<typeof keywordSuggestionSchema>;

// ─── Collection ──────────────────────────────────────────

export const collectionSchema = z.object({
  id: z.number().int().positive().optional(),
  name: z.string().min(1),
  description: z.string().default(''),
  createdAt: z.string().datetime(),
  updatedAt: z.string().datetime(),
});

export type Collection = z.infer<typeof collectionSchema>;

export const collectionItemSchema = z.object({
  id: z.number().int().positive().optional(),
  collectionId: z.number().int().positive(),
  videoId: z.string(),
  tags: z.array(z.string()).default([]),
  notes: z.string().default(''),
  addedAt: z.string().datetime(),
});

export type CollectionItem = z.infer<typeof collectionItemSchema>;

// ─── API Request / Response ──────────────────────────────

export const searchRequestSchema = z.object({
  keyword: z.string().min(1).max(200),
  timeRange: timeRangeSchema.default('7d'),
  language: z.string().default('any'),
  maxDuration: z.number().int().min(1).max(180).default(180),
});

export type SearchRequest = z.infer<typeof searchRequestSchema>;

export const searchResponseSchema = z.object({
  keyword: z.string(),
  videos: z.array(videoWithScoreSchema),
  suggestions: z.array(keywordSuggestionSchema),
  quotaUsed: z.number().int(),
  quotaRemaining: z.number().int(),
  cachedAt: z.string().datetime().nullable(),
});

export type SearchResponse = z.infer<typeof searchResponseSchema>;

export const summaryRequestSchema = z.object({
  videoId: z.string().min(1),
});

export type SummaryRequest = z.infer<typeof summaryRequestSchema>;

export const quotaStatusSchema = z.object({
  used: z.number().int().nonnegative(),
  limit: z.number().int().positive(),
  remaining: z.number().int().nonnegative(),
  resetsAt: z.string().datetime(),
});

export type QuotaStatus = z.infer<typeof quotaStatusSchema>;

export const apiErrorSchema = z.object({
  code: z.string(),
  message: z.string(),
});

export type ApiError = z.infer<typeof apiErrorSchema>;

// ─── Collection API ──────────────────────────────────────

export const createCollectionRequestSchema = z.object({
  name: z.string().min(1).max(100),
  description: z.string().max(500).default(''),
});

export type CreateCollectionRequest = z.infer<typeof createCollectionRequestSchema>;

export const addToCollectionRequestSchema = z.object({
  videoId: z.string().min(1),
  tags: z.array(z.string()).default([]),
  notes: z.string().max(2000).default(''),
});

export type AddToCollectionRequest = z.infer<typeof addToCollectionRequestSchema>;

// ─── Export ──────────────────────────────────────────────

export const exportFormatSchema = z.enum(['csv', 'markdown']);
export type ExportFormat = z.infer<typeof exportFormatSchema>;

export const exportRequestSchema = z.object({
  videoIds: z.array(z.string()).min(1),
  format: exportFormatSchema,
  includeSummaries: z.boolean().default(false),
});

export type ExportRequest = z.infer<typeof exportRequestSchema>;
