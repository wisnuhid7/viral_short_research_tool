import { fetchWhopBountiesFromMcp, type WhopBounty } from './whop-mcp-client.js';
import { upsertCampaign, recordWhopSyncLog, getLatestWhopSyncLog } from '../../db/queries.js';
import type { Campaign, CampaignCategory, WhopSyncResponse, WhopSyncStatus } from 'shared';

let isSyncing = false;

function classifyCategory(title: string, description: string, brand: string): CampaignCategory {
  const text = `${title} ${description} ${brand}`.toLowerCase();

  if (/(crypto|bitcoin|btc|eth|solana|forex|trading|options|stock|signals|pips|invest)/i.test(text)) {
    return 'finance_crypto';
  }
  if (/(ai\b|bot|gpt|saas|software|automation|code|developer|tech|prompt|agent|tool)/i.test(text)) {
    return 'ai_tech';
  }
  if (/(gaming|\bgames?\b|roblox|minecraft|fortnite|steam|twitch|esports|fps|\bgameplay\b)/i.test(text)) {
    return 'gaming';
  }
  if (/(affiliate|ecom|dropship|sales|closing|b2b|lead|agency|hustle|client|money|income|masterclass|blueprint)/i.test(text)) {
    return 'business_sidehustle';
  }
  if (/(gym|fitness|workout|calisthenics|diet|health|habits|glowup|physique|transformation)/i.test(text)) {
    return 'fitness_lifestyle';
  }
  if (/(comedy|meme|humor|mystery|movie|stream|sweeper|bettor|bet|sports|picks|music|clip|tiktok|slideshow)/i.test(text)) {
    return 'entertainment';
  }
  return 'other';
}

function extractUrl(description: string, hostingRoute?: string): string {
  const urlMatch = description.match(/https:\/\/(?:www\.)?whop\.com\/[a-zA-Z0-9\-_/]+/);
  if (urlMatch) {
    return urlMatch[0];
  }
  if (hostingRoute) {
    return `https://whop.com/${hostingRoute}`;
  }
  return 'https://whop.com';
}

function calculateRate(bounty: WhopBounty): number {
  const reward = bounty.gross_reward_amount ?? 1.0;
  if (bounty.business_goal_type === 'clipping') {
    return Math.max(0.5, Math.min(20.0, reward));
  }
  if (reward >= 10) {
    return Math.min(10.0, Math.max(4.0, reward * 0.5));
  }
  if (reward >= 1) {
    return Math.min(6.0, Math.max(1.0, reward * 1.5));
  }
  return Math.max(0.5, reward * 5);
}

function extractHashtags(description: string, category: string): string[] {
  const matches = description.match(/#[a-zA-Z0-9_]+/g);
  if (matches && matches.length > 0) {
    return matches.slice(0, 5);
  }
  const catTag = category.replace(/[^a-zA-Z0-9]/g, '');
  return ['#WhopRewards', '#WhopPartner', `#${catTag}`];
}

function extractKeywords(title: string, category: string): string[] {
  const words = title
    .toLowerCase()
    .replace(/[^a-zA-Z0-9\s]/g, ' ')
    .split(/\s+/)
    .filter((w) => w.length > 3 && !['this', 'with', 'from', 'your', 'have', 'what', 'only', 'post'].includes(w));

  const unique = Array.from(new Set(words)).slice(0, 4);
  if (category === 'ai_tech' && !unique.includes('ai')) unique.unshift('ai');
  if (category === 'finance_crypto' && !unique.includes('trading')) unique.unshift('trading');
  return unique;
}

/**
 * Maps raw Whop bounty to our application Campaign model
 */
export function mapBountyToCampaign(bounty: WhopBounty): Campaign {
  const brand = bounty.hosting_account?.title || bounty.poster?.name || 'Whop Partner';
  const category = classifyCategory(bounty.title, bounty.description || '', brand);
  const url = extractUrl(bounty.description || '', bounty.hosting_account?.route);
  const now = new Date().toISOString();

  const totalBudget = bounty.budget_amount && bounty.budget_amount > 0
    ? bounty.budget_amount
    : (bounty.gross_reward_amount ? bounty.gross_reward_amount * 10 : 100);

  const paidOut = bounty.gross_paid_out_amount ?? 0;
  const remainingBudget = Math.max(0, totalBudget - paidOut);

  return {
    id: bounty.id,
    name: bounty.title,
    creatorOrBrand: brand,
    category,
    url,
    ratePerKViews: Math.round(calculateRate(bounty) * 100) / 100,
    totalBudget: Math.round(totalBudget * 100) / 100,
    remainingBudget: Math.round(remainingBudget * 100) / 100,
    deadline: bounty.submissions_closed_at ?? null,
    requiredHashtags: extractHashtags(bounty.description || '', category),
    requiredMentions: bounty.hosting_account?.route ? [`@${bounty.hosting_account.route}`] : ['@Whop'],
    allowedPlatforms: ['YouTube Shorts', 'TikTok', 'Instagram Reels'],
    targetKeywords: extractKeywords(bounty.title, category),
    notes: bounty.description ? bounty.description.slice(0, 500) : '',
    spotsRemaining: bounty.spots_remaining !== undefined && bounty.spots_remaining !== null ? Number(bounty.spots_remaining) : null,
    isWhopLive: true,
    whopGoalType: bounty.business_goal_type ?? 'bounty',
    createdAt: bounty.created_at || now,
    updatedAt: bounty.updated_at || now,
  };
}

/**
 * Triggers a sync of live open bounties from Whop via MCP
 */
export async function syncWhopCampaigns(): Promise<WhopSyncResponse> {
  if (isSyncing) {
    return {
      success: true,
      count: 0,
      syncedAt: new Date().toISOString(),
      message: 'Sinkronisasi Whop MCP sedang berjalan di background...',
    };
  }

  isSyncing = true;
  const syncedAt = new Date().toISOString();

  try {
    const rawBounties = await fetchWhopBountiesFromMcp(50);
    let count = 0;

    for (const bounty of rawBounties) {
      if (!bounty.id || !bounty.title) continue;
      const campaign = mapBountyToCampaign(bounty);
      upsertCampaign(campaign);
      count++;
    }

    recordWhopSyncLog(syncedAt, count, 'success');

    return {
      success: true,
      count,
      syncedAt,
      message: `Berhasil menyinkronkan ${count} campaign live dari Whop MCP.`,
    };
  } catch (error) {
    const errMsg = error instanceof Error ? error.message : String(error);
    recordWhopSyncLog(syncedAt, 0, 'error', errMsg);
    throw error;
  } finally {
    isSyncing = false;
  }
}

/**
 * Retrieves the current sync status
 */
export function getWhopSyncStatus(): WhopSyncStatus {
  const latestLog = getLatestWhopSyncLog();
  return {
    lastSyncedAt: latestLog ? latestLog.syncedAt : null,
    campaignsCount: latestLog ? latestLog.campaignsCount : 0,
    status: isSyncing ? 'syncing' : (latestLog ? (latestLog.status as any) : 'idle'),
    errorMessage: latestLog?.errorMessage,
  };
}

/**
 * Starts periodic sync in the background (every 30 minutes) + initial sync
 */
export function startPeriodicWhopSync(): void {
  // Run initial sync after 3 seconds so the server starts up instantly
  setTimeout(() => {
    syncWhopCampaigns()
      .then((res) => {
        console.log(`[WhopSync] Initial sync completed: ${res.count} campaigns synced.`);
      })
      .catch((err) => {
        console.warn(`[WhopSync] Initial sync warning: ${err.message}`);
      });
  }, 3000);

  // Periodic interval every 30 minutes
  setInterval(() => {
    syncWhopCampaigns()
      .then((res) => {
        console.log(`[WhopSync] Scheduled sync completed: ${res.count} campaigns.`);
      })
      .catch((err) => {
        console.warn(`[WhopSync] Scheduled sync failed: ${err.message}`);
      });
  }, 30 * 60 * 1000);
}
