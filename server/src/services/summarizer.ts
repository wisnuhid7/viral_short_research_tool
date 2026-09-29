import OpenAI from 'openai';
import { config } from '../lib/config.js';
import { logger } from '../lib/logger.js';
import { ExternalApiError } from '../lib/errors.js';
import { buildSummarizePrompt, PROMPT_VERSION } from './prompts/summarize-video.js';
import { getSummary, saveSummary } from '../db/queries.js';
import { getTranscript } from './youtube.js';
import type { Summary } from 'shared';
import { z } from 'zod';

const openai = new OpenAI({ apiKey: config.openai.apiKey || 'dummy-key' });

// Schema to validate LLM JSON output
const llmOutputSchema = z.object({
  topic: z.string(),
  hookFirst3Seconds: z.string(),
  structure: z.object({
    hook: z.string(),
    body: z.string(),
    cta: z.string(),
  }),
  style: z.string(),
  keyMoments: z.array(z.string()).default([]),
});

const MAX_RETRIES = 2;

/**
 * Summarize a video. Checks cache first, then calls LLM.
 * Only called for user-selected videos, not entire search results.
 */
export async function summarizeVideo(
  videoId: string,
  title: string,
  description: string,
): Promise<Summary> {
  // Check cache
  const cached = getSummary(videoId, PROMPT_VERSION);
  if (cached) {
    logger.debug('Summary cache hit', { videoId });
    return cached;
  }

  // Fetch transcript
  const transcript = await getTranscript(videoId);
  const { systemPrompt, userPrompt, sourceType } = buildSummarizePrompt(title, description, transcript);

  // Call OpenAI with retry for malformed JSON
  let lastError: unknown;
  for (let attempt = 0; attempt <= MAX_RETRIES; attempt++) {
    try {
      const response = await openai.chat.completions.create({
        model: 'gpt-4o-mini',
        response_format: { type: 'json_object' },
        messages: [
          { role: 'system', content: systemPrompt },
          { role: 'user', content: userPrompt },
        ],
        temperature: 0.3,
      });

      const content = response.choices[0]?.message?.content;
      if (!content) {
        throw new Error('No content returned in OpenAI response');
      }

      // Parse and validate JSON output
      const rawJson = extractJson(content);
      const parsed = llmOutputSchema.parse(JSON.parse(rawJson));

      const summary: Summary = {
        videoId,
        topic: parsed.topic,
        hookFirst3Seconds: parsed.hookFirst3Seconds,
        structure: parsed.structure,
        style: parsed.style,
        keyMoments: parsed.keyMoments,
        confidence: sourceType === 'transcript' ? 'high' : 'low',
        sourceType,
        promptVersion: PROMPT_VERSION,
        createdAt: new Date().toISOString(),
      };

      // Cache permanently
      saveSummary(summary);
      logger.info('Video summarized', { videoId, sourceType, attempt });

      return summary;
    } catch (err) {
      lastError = err;
      logger.warn('Summary attempt failed', { videoId, attempt, error: String(err) });
    }
  }

  throw new ExternalApiError('OpenAI', `Gagal meringkas video setelah ${MAX_RETRIES + 1} percobaan: ${String(lastError)}`);
}

/** Extract JSON from LLM response that might contain markdown fences or extra text */
function extractJson(text: string): string {
  // Try to find JSON in code fences
  const fenceMatch = text.match(/```(?:json)?\s*\n?([\s\S]*?)\n?\s*```/);
  if (fenceMatch?.[1]) return fenceMatch[1].trim();

  // Try to find raw JSON object
  const jsonMatch = text.match(/\{[\s\S]*\}/);
  if (jsonMatch?.[0]) return jsonMatch[0];

  return text.trim();
}
