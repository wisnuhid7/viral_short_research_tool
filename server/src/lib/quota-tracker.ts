import { logger } from './logger.js';
import { QuotaExceededError } from './errors.js';

/**
 * Tracks YouTube API quota usage per day.
 * search.list = 100 units, videos.list = 1 unit, channels.list = 1 unit.
 * Default daily limit: 10,000 units.
 */

const QUOTA_COSTS = {
  'search.list': 100,
  'videos.list': 1,
  'channels.list': 1,
} as const;

export type QuotaOperation = keyof typeof QUOTA_COSTS;

interface DailyQuota {
  date: string; // YYYY-MM-DD
  used: number;
}

let dailyQuota: DailyQuota = {
  date: getTodayString(),
  used: 0,
};

let quotaLimit = 10000;

function getTodayString(): string {
  return new Date().toISOString().slice(0, 10);
}

function resetIfNewDay(): void {
  const today = getTodayString();
  if (dailyQuota.date !== today) {
    logger.info('YouTube quota reset for new day', { previousUsed: dailyQuota.used });
    dailyQuota = { date: today, used: 0 };
  }
}

export function setQuotaLimit(limit: number): void {
  quotaLimit = limit;
}

/** Check if we can afford the operation, throw if not */
export function checkQuota(operation: QuotaOperation): void {
  resetIfNewDay();
  const cost = QUOTA_COSTS[operation];
  if (dailyQuota.used + cost > quotaLimit) {
    throw new QuotaExceededError(
      `Kuota YouTube API tidak cukup. Digunakan: ${dailyQuota.used}/${quotaLimit} unit. ` +
      `Operasi ${operation} membutuhkan ${cost} unit.`
    );
  }
}

/** Record quota usage after a successful API call */
export function recordQuotaUsage(operation: QuotaOperation): void {
  resetIfNewDay();
  const cost = QUOTA_COSTS[operation];
  dailyQuota.used += cost;
  logger.debug('YouTube quota used', {
    operation,
    cost,
    totalUsed: dailyQuota.used,
    remaining: quotaLimit - dailyQuota.used,
  });
}

/** Get current quota status */
export function getQuotaStatus() {
  resetIfNewDay();
  const tomorrow = new Date();
  tomorrow.setUTCDate(tomorrow.getUTCDate() + 1);
  tomorrow.setUTCHours(0, 0, 0, 0);

  return {
    used: dailyQuota.used,
    limit: quotaLimit,
    remaining: Math.max(0, quotaLimit - dailyQuota.used),
    resetsAt: tomorrow.toISOString(),
  };
}
