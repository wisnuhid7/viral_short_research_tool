"""Whop → Campaign sync engine.

Port of server/src/services/whop/whop-sync.ts.
"""
import asyncio
import re
from datetime import datetime, timezone

from api.app.db.queries import get_latest_whop_sync_log, record_whop_sync_log, upsert_campaign
from api.app.lib.format import js_round
from api.app.services.whop.mcp_client import fetch_whop_bounties_from_mcp

is_syncing = False


def _now_iso() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + "Z"


# ─── Category classification ─────────────────────────────

_FINANCE_RE = re.compile(
    r"(crypto|bitcoin|btc|eth|solana|forex|trading|options|stock|signals|pips|invest)", re.I
)
_AI_TECH_RE = re.compile(
    r"(ai\b|bot|gpt|saas|software|automation|code|developer|tech|prompt|agent|tool)", re.I
)
_GAMING_RE = re.compile(
    r"(gaming|\bgames?\b|roblox|minecraft|fortnite|steam|twitch|esports|fps|\bgameplay\b)", re.I
)
_BIZ_RE = re.compile(
    r"(affiliate|ecom|dropship|sales|closing|b2b|lead|agency|hustle|client|money|income|masterclass|blueprint)",
    re.I,
)
_FITNESS_RE = re.compile(
    r"(gym|fitness|workout|calisthenics|diet|health|habits|glowup|physique|transformation)", re.I
)
_ENTERTAINMENT_RE = re.compile(
    r"(comedy|meme|humor|mystery|movie|stream|sweeper|bettor|bet|sports|picks|music|clip|tiktok|slideshow)",
    re.I,
)


def classify_category(title: str, description: str, brand: str) -> str:
    text = f"{title} {description} {brand}".lower()

    if _FINANCE_RE.search(text):
        return "finance_crypto"
    if _AI_TECH_RE.search(text):
        return "ai_tech"
    if _GAMING_RE.search(text):
        return "gaming"
    if _BIZ_RE.search(text):
        return "business_sidehustle"
    if _FITNESS_RE.search(text):
        return "fitness_lifestyle"
    if _ENTERTAINMENT_RE.search(text):
        return "entertainment"
    return "other"


def extract_url(description: str, hosting_route: str | None = None) -> str:
    url_match = re.search(r"https://(?:www\.)?whop\.com/[a-zA-Z0-9\-_/]+", description)
    if url_match:
        return url_match.group(0)
    if hosting_route:
        return f"https://whop.com/{hosting_route}"
    return "https://whop.com"


def calculate_rate(bounty: dict) -> float:
    reward = bounty.get("gross_reward_amount")
    if reward is None:
        reward = 1.0
    if bounty.get("business_goal_type") == "clipping":
        return max(0.5, min(20.0, reward))
    if reward >= 10:
        return min(10.0, max(4.0, reward * 0.5))
    if reward >= 1:
        return min(6.0, max(1.0, reward * 1.5))
    return max(0.5, reward * 5)


def extract_hashtags(description: str, category: str) -> list[str]:
    matches = re.findall(r"#[a-zA-Z0-9_]+", description)
    if matches:
        return matches[:5]
    cat_tag = re.sub(r"[^a-zA-Z0-9]", "", category)
    return ["#WhopRewards", "#WhopPartner", f"#{cat_tag}"]


_KEYWORD_STOP = {"this", "with", "from", "your", "have", "what", "only", "post"}


def extract_keywords(title: str, category: str) -> list[str]:
    words = [
        w
        for w in re.sub(r"[^a-zA-Z0-9\s]", " ", title.lower()).split()
        if len(w) > 3 and w not in _KEYWORD_STOP
    ]

    # Preserve insertion order while de-duplicating (like Array.from(new Set())).
    unique: list[str] = []
    for w in words:
        if w not in unique:
            unique.append(w)
    unique = unique[:4]

    if category == "ai_tech" and "ai" not in unique:
        unique.insert(0, "ai")
    if category == "finance_crypto" and "trading" not in unique:
        unique.insert(0, "trading")
    return unique


# ─── Mapping ─────────────────────────────────────────────

def map_bounty_to_campaign(bounty: dict) -> dict:
    hosting = bounty.get("hosting_account") or {}
    poster = bounty.get("poster") or {}
    description = bounty.get("description") or ""

    brand = hosting.get("title") or poster.get("name") or "Whop Partner"
    category = classify_category(bounty["title"], description, brand)
    url = extract_url(description, hosting.get("route"))
    now = _now_iso()

    budget_amount = bounty.get("budget_amount")
    gross_reward = bounty.get("gross_reward_amount")
    if budget_amount and budget_amount > 0:
        total_budget = budget_amount
    elif gross_reward:
        total_budget = gross_reward * 10
    else:
        total_budget = 100

    paid_out = bounty.get("gross_paid_out_amount") or 0
    remaining_budget = max(0, total_budget - paid_out)

    spots = bounty.get("spots_remaining")

    return {
        "id": bounty["id"],
        "name": bounty["title"],
        "creatorOrBrand": brand,
        "category": category,
        "url": url,
        "ratePerKViews": js_round(calculate_rate(bounty) * 100) / 100,
        "totalBudget": js_round(total_budget * 100) / 100,
        "remainingBudget": js_round(remaining_budget * 100) / 100,
        "deadline": bounty.get("submissions_closed_at") or None,
        "requiredHashtags": extract_hashtags(description, category),
        "requiredMentions": [f"@{hosting['route']}"] if hosting.get("route") else ["@Whop"],
        "allowedPlatforms": ["YouTube Shorts", "TikTok", "Instagram Reels"],
        "targetKeywords": extract_keywords(bounty["title"], category),
        "notes": description[:500] if description else "",
        "spotsRemaining": int(spots) if spots is not None else None,
        "isWhopLive": True,
        "whopGoalType": bounty.get("business_goal_type") or "bounty",
        "createdAt": bounty.get("created_at") or now,
        "updatedAt": bounty.get("updated_at") or now,
    }


# ─── Sync ────────────────────────────────────────────────

async def sync_whop_campaigns() -> dict:
    global is_syncing

    if is_syncing:
        return {
            "success": True,
            "count": 0,
            "syncedAt": _now_iso(),
            "message": "Sinkronisasi Whop MCP sedang berjalan di background...",
        }

    is_syncing = True
    synced_at = _now_iso()

    try:
        raw_bounties = await fetch_whop_bounties_from_mcp(50)
        count = 0

        for bounty in raw_bounties:
            if not bounty.get("id") or not bounty.get("title"):
                continue
            campaign = map_bounty_to_campaign(bounty)
            upsert_campaign(campaign)
            count += 1

        record_whop_sync_log(synced_at, count, "success")

        return {
            "success": True,
            "count": count,
            "syncedAt": synced_at,
            "message": f"Berhasil menyinkronkan {count} campaign live dari Whop MCP.",
        }
    except Exception as error:  # noqa: BLE001
        err_msg = str(error)
        record_whop_sync_log(synced_at, 0, "error", err_msg)
        raise
    finally:
        is_syncing = False


def get_whop_sync_status() -> dict:
    latest_log = get_latest_whop_sync_log()
    return {
        "lastSyncedAt": latest_log["syncedAt"] if latest_log else None,
        "campaignsCount": latest_log["campaignsCount"] if latest_log else 0,
        "status": "syncing" if is_syncing else (latest_log["status"] if latest_log else "idle"),
        "errorMessage": latest_log.get("errorMessage") if latest_log else None,
    }


def start_periodic_whop_sync() -> None:
    """Starts periodic sync in the background (every 30 minutes) + initial sync."""

    async def _initial() -> None:
        await asyncio.sleep(3)
        try:
            res = await sync_whop_campaigns()
            print(f"[WhopSync] Initial sync completed: {res['count']} campaigns synced.")
        except Exception as err:  # noqa: BLE001
            print(f"[WhopSync] Initial sync warning: {err}")

    async def _periodic() -> None:
        while True:
            await asyncio.sleep(30 * 60)
            try:
                res = await sync_whop_campaigns()
                print(f"[WhopSync] Scheduled sync completed: {res['count']} campaigns.")
            except Exception as err:  # noqa: BLE001
                print(f"[WhopSync] Scheduled sync failed: {err}")

    asyncio.create_task(_initial())
    asyncio.create_task(_periodic())
