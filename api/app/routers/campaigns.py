"""Campaign routes — port of server/src/routes/campaigns.ts."""
import time
from typing import Any

from fastapi import APIRouter, Body, Query

from api.app.db.queries import (
    delete_campaign,
    find_campaigns_by_keyword,
    get_campaign_by_id,
    get_campaigns,
    upsert_campaign,
)
from api.app.db.database import now_iso
from api.app.errors import NotFoundError
from api.app.lib.validation import parse_body_campaign
from api.app.schemas import CreateCampaignRequest
from api.app.services.scoring.campaign_rating import calculate_campaign_rating
from api.app.services.whop.sync import get_whop_sync_status, sync_whop_campaigns

router = APIRouter()


@router.get("/sync-status")
def sync_status():
    return get_whop_sync_status()


@router.post("/sync")
async def sync():
    return await sync_whop_campaigns()


@router.get("")
@router.get("/", include_in_schema=False)
def list_campaigns(category: str = Query(default="all")):
    raw = get_campaigns(category or "all")
    with_rating = [{**c, "rating": calculate_campaign_rating(c)} for c in raw]
    with_rating.sort(key=lambda x: x["rating"]["opportunityScore"], reverse=True)
    return with_rating


@router.get("/match")
def match(keyword: str = Query(default="")):
    if not keyword.strip():
        return []
    matching = find_campaigns_by_keyword(keyword.strip())
    ranked = [{**c, "rating": calculate_campaign_rating(c)} for c in matching]
    ranked.sort(key=lambda x: x["rating"]["opportunityScore"], reverse=True)
    return ranked


@router.get("/{campaign_id}")
def get_one(campaign_id: str):
    campaign = get_campaign_by_id(campaign_id)
    if not campaign:
        raise NotFoundError(f"Campaign {campaign_id} tidak ditemukan.")
    return {**campaign, "rating": calculate_campaign_rating(campaign)}


@router.post("", status_code=201)
@router.post("/", status_code=201, include_in_schema=False)
def create(body: Any = Body(default=None)):
    parsed: CreateCampaignRequest = parse_body_campaign(  # type: ignore[assignment]
        CreateCampaignRequest, body
    )

    now = now_iso()
    new_campaign = {
        "id": f"cmp_{int(time.time() * 1000)}",
        **parsed.model_dump(),
        "isWhopLive": False,
        "createdAt": now,
        "updatedAt": now,
    }

    upsert_campaign(new_campaign)
    return {**new_campaign, "rating": calculate_campaign_rating(new_campaign)}


@router.delete("/{campaign_id}")
def remove(campaign_id: str):
    delete_campaign(campaign_id)
    return {"message": "Campaign berhasil dihapus."}
