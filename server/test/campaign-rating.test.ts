import { describe, it, expect } from 'vitest';
import { calculateCampaignRating } from '../src/services/scoring/campaign-rating.js';
import type { Campaign } from 'shared';

describe('calculateCampaignRating service', () => {
  it('correctly assigns Tier S to high-paying and high-budget campaigns', () => {
    const highTierCampaign: Campaign = {
      id: 'test_s',
      name: 'High Tier Crypto Campaign',
      creatorOrBrand: 'Crypto Alpha',
      category: 'finance_crypto',
      url: 'https://whop.com/discover/test-crypto',
      ratePerKViews: 6.0,
      totalBudget: 10000,
      remainingBudget: 8000,
      deadline: '2026-12-31',
      requiredHashtags: ['#crypto'],
      requiredMentions: ['@alpha'],
      allowedPlatforms: ['YouTube Shorts'],
      targetKeywords: ['crypto'],
      notes: '',
      createdAt: new Date().toISOString(),
      updatedAt: new Date().toISOString(),
    };

    const rating = calculateCampaignRating(highTierCampaign);
    expect(rating.tier).toBe('S');
    expect(rating.opportunityScore).toBeGreaterThanOrEqual(80);
    expect(rating.budgetHealth).toBe('safe');
    expect(rating.projectedEarnings.views100k).toBe(600); // 100 * $6
    expect(rating.targetEaseLevel).toBe('very_easy');
    expect(rating.targetEaseScore).toBeGreaterThanOrEqual(80);
    expect(rating.viewsNeededForTarget.for50USD).toBeLessThanOrEqual(10000);
    expect(rating.budgetSafetyPockets).toBeGreaterThan(100);
    expect(rating.strategyTips.length).toBeGreaterThan(0);
  });

  it('assigns lower tier and hard difficulty when budget is low and rate is small', () => {
    const lowTierCampaign: Campaign = {
      id: 'test_c',
      name: 'Low Budget Contest',
      creatorOrBrand: 'Unknown',
      category: 'other',
      url: 'https://whop.com/discover/low-test',
      ratePerKViews: 1.0,
      totalBudget: 500,
      remainingBudget: 150,
      deadline: '2026-10-01',
      requiredHashtags: [],
      requiredMentions: [],
      allowedPlatforms: ['YouTube Shorts'],
      targetKeywords: [],
      notes: '',
      createdAt: new Date().toISOString(),
      updatedAt: new Date().toISOString(),
    };

    const rating = calculateCampaignRating(lowTierCampaign);
    expect(rating.tier).toBe('C');
    expect(rating.opportunityScore).toBeLessThan(50);
    expect(rating.budgetHealth).toBe('low');
    expect(rating.projectedEarnings.views10k).toBe(10);
    expect(rating.targetEaseLevel).toBe('hard');
    expect(rating.viewsNeededForTarget.for50USD).toBe(50000);
    expect(rating.budgetSafetyPockets).toBe(3);
  });
});
