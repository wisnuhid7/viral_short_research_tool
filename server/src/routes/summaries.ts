import { Router } from 'express';
import { summaryRequestSchema } from 'shared';
import { ValidationError, NotFoundError } from '../lib/errors.js';
import { getVideo } from '../db/queries.js';
import { summarizeVideo } from '../services/summarizer.js';

export const summariesRouter = Router();

/**
 * POST /api/summaries
 * Generate or retrieve a cached summary for a video.
 * Only called for user-selected videos (not bulk).
 */
summariesRouter.post('/', async (req, res, next) => {
  try {
    const parsed = summaryRequestSchema.safeParse(req.body);
    if (!parsed.success) {
      throw new ValidationError(
        `Input tidak valid: ${parsed.error.issues.map((i) => i.message).join(', ')}`
      );
    }

    const { videoId } = parsed.data;

    // Ensure video exists in our DB
    const video = getVideo(videoId);
    if (!video) {
      throw new NotFoundError(`Video dengan ID "${videoId}" tidak ditemukan. Lakukan pencarian terlebih dahulu.`);
    }

    const summary = await summarizeVideo(videoId, video.title, video.description);

    res.json(summary);
  } catch (err) {
    next(err);
  }
});
