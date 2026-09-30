import { describe, it, expect } from 'vitest';
import { mapBountyToCampaign } from '../src/services/whop/whop-sync.js';
import { calculateCampaignRating } from '../src/services/scoring/campaign-rating.js';
import type { WhopBounty } from '../src/services/whop/whop-mcp-client.js';

describe('Whop MCP Sync Engine', () => {
  it('correctly maps a clipping bounty to a Campaign model', () => {
    const rawBounty: WhopBounty = {
      id: 'bnty_4nQb37p7bvjna',
      title: 'Clip Content into Short Video (1k view minimum)',
      description: 'Clip best moments from our show: https://whop.com/anon-exclusive-play/clips. Requirements: 1080p, #AnonSports, @AnonPicks.',
      status: 'open',
      gross_reward_amount: 3.0,
      budget_amount: 60.0,
      gross_paid_out_amount: 15.0,
      spots_remaining: 3,
      business_goal_type: 'clipping',
      hosting_account: {
        id: 'biz_anon_sports',
        title: 'Anon Sports Picks',
        route: 'anon-exclusive-play',
      },
    };

    const campaign = mapBountyToCampaign(rawBounty);

    expect(campaign.id).toBe('bnty_4nQb37p7bvjna');
    expect(campaign.name).toBe('Clip Content into Short Video (1k view minimum)');
    expect(campaign.creatorOrBrand).toBe('Anon Sports Picks');
    expect(campaign.category).toBe('entertainment');
    expect(campaign.url).toBe('https://whop.com/anon-exclusive-play/clips');
    expect(campaign.ratePerKViews).toBe(3.0);
    expect(campaign.totalBudget).toBe(60.0);
    expect(campaign.remainingBudget).toBe(45.0);
    expect(campaign.spotsRemaining).toBe(3);
    expect(campaign.isWhopLive).toBe(true);
    expect(campaign.whopGoalType).toBe('clipping');

    // Rating evaluation
    const rating = calculateCampaignRating(campaign);
    expect(rating.opportunityScore).toBeGreaterThan(0);
    expect(rating.viewsNeededForTarget.for25USD).toBe(8334);
  });

  it('correctly categorizes AI software bounty and computes url from route', () => {
    const rawBounty: WhopBounty = {
      id: 'bnty_ai_tool_99',
      title: 'Create Viral TikTok & Shorts showcasing AI Video Bot SaaS',
      description: 'Promote our software tool. Earn rewards for every approved video.',
      status: 'open',
      gross_reward_amount: 5.0,
      budget_amount: 500.0,
      spots_remaining: 25,
      business_goal_type: 'ugc_content',
      hosting_account: {
        title: 'Kling AI Lab',
        route: 'kling-ai-creators',
      },
    };

    const campaign = mapBountyToCampaign(rawBounty);

    expect(campaign.category).toBe('ai_tech');
    expect(campaign.url).toBe('https://whop.com/kling-ai-creators');
    expect(campaign.isWhopLive).toBe(true);
    expect(campaign.spotsRemaining).toBe(25);

    const rating = calculateCampaignRating(campaign);
    expect(rating.targetEaseLevel).toBe('very_easy');
  });

  it('handles crypto and finance bounty categories', () => {
    const rawBounty: WhopBounty = {
      id: 'bnty_crypto_trade',
      title: 'Bitcoin & Solana Trading Signals Highlights',
      description: 'Make shorts about crypto alpha signals.',
      status: 'open',
      gross_reward_amount: 8.0,
      budget_amount: 1000.0,
      hosting_account: {
        title: 'Alpha Traders Whop',
        route: 'alpha-traders',
      },
    };

    const campaign = mapBountyToCampaign(rawBounty);
    expect(campaign.category).toBe('finance_crypto');
    expect(campaign.isWhopLive).toBe(true);
  });
});
