import { Router } from 'express';
import { createCampaignRequestSchema } from 'shared';
import { ValidationError, NotFoundError } from '../lib/errors.js';
import {
  getCampaigns,
  getCampaignById,
  upsertCampaign,
  deleteCampaign,
  findCampaignsByKeyword,
} from '../db/queries.js';
import { calculateCampaignRating } from '../services/scoring/campaign-rating.js';
import { syncWhopCampaigns, getWhopSyncStatus } from '../services/whop/whop-sync.js';
import type { Campaign, CampaignWithRating } from 'shared';

export const campaignsRouter = Router();

/**
 * GET /api/campaigns/sync-status
 * Check the latest Whop MCP sync status.
 */
campaignsRouter.get('/sync-status', (_req, res) => {
  const status = getWhopSyncStatus();
  res.json(status);
});

/**
 * POST /api/campaigns/sync
 * Trigger sync with Whop MCP server to update live bounties & campaigns.
 */
campaignsRouter.post('/sync', async (_req, res, next) => {
  try {
    const result = await syncWhopCampaigns();
    res.json(result);
  } catch (err) {
    next(err);
  }
});

/**
 * GET /api/campaigns
 * List all campaigns with calculated opportunity & earning ratings, filtered by category.
 */
campaignsRouter.get('/', (req, res) => {
  const category = (req.query['category'] as string) || 'all';
  const rawCampaigns = getCampaigns(category);

  const campaignsWithRating: CampaignWithRating[] = rawCampaigns
    .map((c) => ({
      ...c,
      rating: calculateCampaignRating(c),
    }))
    .sort((a, b) => b.rating.opportunityScore - a.rating.opportunityScore);

  res.json(campaignsWithRating);
});

/**
 * GET /api/campaigns/match
 * Find active campaigns that match a searched keyword.
 */
campaignsRouter.get('/match', (req, res) => {
  const keyword = (req.query['keyword'] as string) || '';
  if (!keyword.trim()) {
    res.json([]);
    return;
  }

  const matching = findCampaignsByKeyword(keyword.trim());
  const ranked = matching
    .map((c) => ({
      ...c,
      rating: calculateCampaignRating(c),
    }))
    .sort((a, b) => b.rating.opportunityScore - a.rating.opportunityScore);

  res.json(ranked);
});

/**
 * GET /api/campaigns/:id
 * Get single campaign with rating.
 */
campaignsRouter.get('/:id', (req, res) => {
  const id = req.params['id'] ?? '';
  const campaign = getCampaignById(id);
  if (!campaign) {
    throw new NotFoundError(`Campaign ${id} tidak ditemukan.`);
  }

  res.json({
    ...campaign,
    rating: calculateCampaignRating(campaign),
  });
});

/**
 * POST /api/campaigns
 * Create a new campaign.
 */
campaignsRouter.post('/', (req, res, next) => {
  try {
    const parsed = createCampaignRequestSchema.safeParse(req.body);
    if (!parsed.success) {
      throw new ValidationError(
        `Input campaign tidak valid: ${parsed.error.issues.map((i) => i.message).join(', ')}`
      );
    }

    const now = new Date().toISOString();
    const newCampaign: Campaign = {
      id: 'cmp_' + Date.now(),
      ...parsed.data,
      isWhopLive: false,
      createdAt: now,
      updatedAt: now,
    };

    upsertCampaign(newCampaign);
    res.status(201).json({
      ...newCampaign,
      rating: calculateCampaignRating(newCampaign),
    });
  } catch (err) {
    next(err);
  }
});

/**
 * DELETE /api/campaigns/:id
 * Delete a campaign.
 */
campaignsRouter.delete('/:id', (req, res) => {
  const id = req.params['id'] ?? '';
  deleteCampaign(id);
  res.json({ message: 'Campaign berhasil dihapus.' });
});
