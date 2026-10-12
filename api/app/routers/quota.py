"""Quota route — port of server/src/routes/quota.ts."""
from fastapi import APIRouter

from api.app.lib.quota import get_quota_status

router = APIRouter()


@router.get("")
@router.get("/", include_in_schema=False)
def quota():
    return get_quota_status()
