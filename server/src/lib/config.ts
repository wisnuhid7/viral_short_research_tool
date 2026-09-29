import dotenv from 'dotenv';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const __dirname = path.dirname(fileURLToPath(import.meta.url));

// Load .env from project root
dotenv.config({ path: path.resolve(__dirname, '../../../.env') });

function requireEnv(key: string): string {
  const value = process.env[key];
  if (!value) {
    throw new Error(`Missing required environment variable: ${key}`);
  }
  return value;
}

function optionalEnv(key: string, defaultValue: string): string {
  return process.env[key] ?? defaultValue;
}

export const config = {
  port: parseInt(optionalEnv('PORT', '3001'), 10),
  nodeEnv: optionalEnv('NODE_ENV', 'development'),
  isDev: optionalEnv('NODE_ENV', 'development') === 'development',

  youtube: {
    apiKey: requireEnv('YOUTUBE_API_KEY'),
    dailyQuotaLimit: parseInt(optionalEnv('YOUTUBE_DAILY_QUOTA_LIMIT', '10000'), 10),
  },

  openai: {
    apiKey: optionalEnv('OPENAI_API_KEY', '') || optionalEnv('ANTHROPIC_API_KEY', ''),
  },

  cache: {
    ttlHours: parseInt(optionalEnv('CACHE_TTL_HOURS', '24'), 10),
  },
} as const;
