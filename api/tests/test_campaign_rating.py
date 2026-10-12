"""Port of server/test/campaign-rating.test.ts."""
from datetime import datetime, timezone

from api.app.services.scoring.campaign_rating import calculate_campaign_rating


def _now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3] + "Z"


def test_assigns_tier_s_to_high_paying_high_budget():
    campaign = {
        "id": "test_s",
        "name": "High Tier Crypto Campaign",
        "creatorOrBrand": "Crypto Alpha",
        "category": "finance_crypto",
        "url": "https://whop.com/discover/test-crypto",
        "ratePerKViews": 6.0,
        "totalBudget": 10000,
        "remainingBudget": 8000,
        "deadline": "2026-12-31",
        "requiredHashtags": ["#crypto"],
        "requiredMentions": ["@alpha"],
        "allowedPlatforms": ["YouTube Shorts"],
        "targetKeywords": ["crypto"],
        "notes": "",
        "createdAt": _now(),
        "updatedAt": _now(),
    }
    rating = calculate_campaign_rating(campaign)
    assert rating["tier"] == "S"
    assert rating["opportunityScore"] >= 80
    assert rating["budgetHealth"] == "safe"
    assert rating["projectedEarnings"]["views100k"] == 600
    assert rating["targetEaseLevel"] == "very_easy"
    assert rating["targetEaseScore"] >= 80
    assert rating["viewsNeededForTarget"]["for50USD"] <= 10000
    assert rating["budgetSafetyPockets"] > 100
    assert len(rating["strategyTips"]) > 0


def test_assigns_lower_tier_hard_difficulty():
    campaign = {
        "id": "test_c",
        "name": "Low Budget Contest",
        "creatorOrBrand": "Unknown",
        "category": "other",
        "url": "https://whop.com/discover/low-test",
        "ratePerKViews": 1.0,
        "totalBudget": 500,
        "remainingBudget": 150,
        "deadline": "2026-10-01",
        "requiredHashtags": [],
        "requiredMentions": [],
        "allowedPlatforms": ["YouTube Shorts"],
        "targetKeywords": [],
        "notes": "",
        "createdAt": _now(),
        "updatedAt": _now(),
    }
    rating = calculate_campaign_rating(campaign)
    assert rating["tier"] == "C"
    assert rating["opportunityScore"] < 50
    assert rating["budgetHealth"] == "low"
    assert rating["projectedEarnings"]["views10k"] == 10
    assert rating["targetEaseLevel"] == "hard"
    assert rating["viewsNeededForTarget"]["for50USD"] == 50000
    assert rating["budgetSafetyPockets"] == 3