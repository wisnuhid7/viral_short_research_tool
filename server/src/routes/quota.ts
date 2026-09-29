import { Router } from 'express';
import { getQuotaStatus } from '../lib/quota-tracker.js';

export const quotaRouter = Router();

/** GET /api/quota — current YouTube API quota status */
quotaRouter.get('/', (_req, res) => {
  res.json(getQuotaStatus());
});
