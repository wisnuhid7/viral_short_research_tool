"""Port of server/test/whop-sync.test.ts."""
from api.app.services.scoring.campaign_rating import calculate_campaign_rating
from api.app.services.whop.sync import map_bounty_to_campaign


def test_maps_clipping_bounty_to_campaign_model():
    raw_bounty = {
        "id": "bnty_4nQb37p7bvjna",
        "title": "Clip Content into Short Video (1k view minimum)",
        "description": (
            "Clip best moments from our show: https://whop.com/anon-exclusive-play/clips. "
            "Requirements: 1080p, #AnonSports, @AnonPicks."
        ),
        "status": "open",
        "gross_reward_amount": 3.0,
        "budget_amount": 60.0,
        "gross_paid_out_amount": 15.0,
        "spots_remaining": 3,
        "business_goal_type": "clipping",
        "hosting_account": {
            "id": "biz_anon_sports",
            "title": "Anon Sports Picks",
            "route": "anon-exclusive-play",
        },
    }

    campaign = map_bounty_to_campaign(raw_bounty)

    assert campaign["id"] == "bnty_4nQb37p7bvjna"
    assert campaign["name"] == "Clip Content into Short Video (1k view minimum)"
    assert campaign["creatorOrBrand"] == "Anon Sports Picks"
    assert campaign["category"] == "entertainment"
    assert campaign["url"] == "https://whop.com/anon-exclusive-play/clips"
    assert campaign["ratePerKViews"] == 3.0
    assert campaign["totalBudget"] == 60.0
    assert campaign["remainingBudget"] == 45.0
    assert campaign["spotsRemaining"] == 3
    assert campaign["isWhopLive"] is True
    assert campaign["whopGoalType"] == "clipping"

    rating = calculate_campaign_rating(campaign)
    assert rating["opportunityScore"] > 0
    assert rating["viewsNeededForTarget"]["for25USD"] == 8334


def test_categorizes_ai_software_bounty_and_computes_url_from_route():
    raw_bounty = {
        "id": "bnty_ai_tool_99",
        "title": "Create Viral TikTok & Shorts showcasing AI Video Bot SaaS",
        "description": "Promote our software tool. Earn rewards for every approved video.",
        "status": "open",
        "gross_reward_amount": 5.0,
        "budget_amount": 500.0,
        "spots_remaining": 25,
        "business_goal_type": "ugc_content",
        "hosting_account": {"title": "Kling AI Lab", "route": "kling-ai-creators"},
    }

    campaign = map_bounty_to_campaign(raw_bounty)

    assert campaign["category"] == "ai_tech"
    assert campaign["url"] == "https://whop.com/kling-ai-creators"
    assert campaign["isWhopLive"] is True
    assert campaign["spotsRemaining"] == 25

    rating = calculate_campaign_rating(campaign)
    assert rating["targetEaseLevel"] == "very_easy"


def test_handles_crypto_and_finance_bounty_categories():
    raw_bounty = {
        "id": "bnty_crypto_trade",
        "title": "Bitcoin & Solana Trading Signals Highlights",
        "description": "Make shorts about crypto alpha signals.",
        "status": "open",
        "gross_reward_amount": 8.0,
        "budget_amount": 1000.0,
        "hosting_account": {"title": "Alpha Traders Whop", "route": "alpha-traders"},
    }

    campaign = map_bounty_to_campaign(raw_bounty)
    assert campaign["category"] == "finance_crypto"
    assert campaign["isWhopLive"] is True
