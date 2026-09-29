import type { Video, ViralScore } from 'shared';

// ─── Configuration ───────────────────────────────────────
// Weights are configurable, not hardcoded throughout the codebase

export interface ScoringWeights {
  velocity: number;
  reachRatio: number;
  engagement: number;
}

export const DEFAULT_WEIGHTS: ScoringWeights = {
  velocity: 0.45,
  reachRatio: 0.30,
  engagement: 0.25,
};

const REACH_RATIO_CAP = 100; // cap to avoid outliers
const YOUNG_VIDEO_HOURS = 3; // penalty threshold

// ─── Normalization ───────────────────────────────────────
// Percentile-based normalization relative to the search batch

/**
 * Normalize values to [0, 1] using percentile ranking within the batch.
 * Pure function — easy to test.
 */
export function percentileNormalize(values: number[]): number[] {
  if (values.length === 0) return [];
  if (values.length === 1) return [0.5]; // single item gets middle score

  const sorted = [...values].sort((a, b) => a - b);

  return values.map((val) => {
    const rank = sorted.filter((v) => v < val).length;
    return rank / (sorted.length - 1);
  });
}

// ─── Raw Metric Computation ──────────────────────────────

export function computeVelocity(viewCount: number, publishedAt: string): number {
  const hoursSinceUpload = Math.max(
    (Date.now() - new Date(publishedAt).getTime()) / (1000 * 60 * 60),
    0.1, // avoid division by zero
  );
  return viewCount / hoursSinceUpload;
}

export function computeReachRatio(viewCount: number, subscriberCount: number): number {
  if (subscriberCount <= 0) return 0;
  return Math.min(viewCount / subscriberCount, REACH_RATIO_CAP);
}

export function computeEngagement(likeCount: number, commentCount: number, viewCount: number): number {
  if (viewCount <= 0) return 0;
  return (likeCount + commentCount) / viewCount;
}

export function isYoungVideo(publishedAt: string): boolean {
  const hoursSince = (Date.now() - new Date(publishedAt).getTime()) / (1000 * 60 * 60);
  return hoursSince < YOUNG_VIDEO_HOURS;
}

// ─── Batch Scoring ───────────────────────────────────────

interface VideoWithSubscribers {
  video: Video;
  subscriberCount: number;
}

/**
 * Calculate viral scores for a batch of videos.
 * Normalization is relative to the batch (percentile-based).
 */
export function calculateViralScores(
  items: VideoWithSubscribers[],
  weights: ScoringWeights = DEFAULT_WEIGHTS,
): ViralScore[] {
  if (items.length === 0) return [];

  // 1. Compute raw metrics
  const velocities = items.map((i) => computeVelocity(i.video.viewCount, i.video.publishedAt));
  const reachRatios = items.map((i) => computeReachRatio(i.video.viewCount, i.subscriberCount));
  const engagements = items.map((i) => computeEngagement(i.video.likeCount, i.video.commentCount, i.video.viewCount));

  // 2. Normalize within batch
  const velNorms = percentileNormalize(velocities);
  const reachNorms = percentileNormalize(reachRatios);
  const engNorms = percentileNormalize(engagements);

  // 3. Weighted sum
  return items.map((item, idx) => {
    const velN = velNorms[idx] ?? 0;
    const reachN = reachNorms[idx] ?? 0;
    const engN = engNorms[idx] ?? 0;

    let totalScore = weights.velocity * velN + weights.reachRatio * reachN + weights.engagement * engN;

    const hasConfidencePenalty = isYoungVideo(item.video.publishedAt);
    // Videos < 3 hours old get 20% penalty
    if (hasConfidencePenalty) {
      totalScore *= 0.8;
    }

    return {
      videoId: item.video.id,
      velocity: velocities[idx] ?? 0,
      velocityNorm: velN,
      reachRatio: reachRatios[idx] ?? 0,
      reachRatioNorm: reachN,
      engagement: engagements[idx] ?? 0,
      engagementNorm: engN,
      totalScore: Math.round(totalScore * 1000) / 1000,
      confidencePenalty: hasConfidencePenalty,
      sampleSize: items.length,
    };
  });
}
