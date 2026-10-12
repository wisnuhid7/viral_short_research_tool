"""Collection routes — port of server/src/routes/collections.ts."""
import re
from typing import Any

from fastapi import APIRouter, Body

from api.app.db.queries import (
    add_to_collection,
    create_collection,
    delete_collection,
    get_collection_items,
    get_collections,
    remove_from_collection,
)
from api.app.errors import ValidationError
from api.app.lib.validation import parse_body
from api.app.schemas import AddToCollectionRequest, CreateCollectionRequest

router = APIRouter()

# JS parseInt stops at the first non-digit and returns NaN when there is none.
_PARSE_INT = re.compile(r"^\s*[+-]?\d+")


def js_parse_int(value: str | None) -> int | None:
    if value is None:
        return None
    match = _PARSE_INT.match(value)
    if match is None:
        return None
    return int(match.group(0))


@router.get("")
@router.get("/", include_in_schema=False)
def list_collections():
    return get_collections()


@router.post("", status_code=201)
@router.post("/", status_code=201, include_in_schema=False)
def create_collection_route(body: Any = Body(default=None)):
    parsed: CreateCollectionRequest = parse_body(  # type: ignore[assignment]
        CreateCollectionRequest, body
    )
    collection_id = create_collection(parsed.name, parsed.description)
    return {"id": collection_id, "message": "Koleksi berhasil dibuat."}


@router.get("/{collection_id}/items")
def list_items(collection_id: str):
    parsed_id = js_parse_int(collection_id)
    if parsed_id is None:
        raise ValidationError("ID koleksi tidak valid.")
    return get_collection_items(parsed_id)


@router.post("/{collection_id}/items", status_code=201)
def add_item(collection_id: str, body: Any = Body(default=None)):
    parsed_id = js_parse_int(collection_id)
    if parsed_id is None:
        raise ValidationError("ID koleksi tidak valid.")

    parsed: AddToCollectionRequest = parse_body(  # type: ignore[assignment]
        AddToCollectionRequest, body
    )
    add_to_collection(parsed_id, parsed.videoId, parsed.tags, parsed.notes)
    return {"message": "Video berhasil ditambahkan ke koleksi."}


@router.delete("/{collection_id}/items/{video_id}")
def remove_item(collection_id: str, video_id: str):
    parsed_id = js_parse_int(collection_id)
    if parsed_id is None or not video_id:
        raise ValidationError("Parameter tidak valid.")
    remove_from_collection(parsed_id, video_id)
    return {"message": "Video berhasil dihapus dari koleksi."}


@router.delete("/{collection_id}")
def remove_collection(collection_id: str):
    parsed_id = js_parse_int(collection_id)
    if parsed_id is None:
        raise ValidationError("ID koleksi tidak valid.")
    delete_collection(parsed_id)
    return {"message": "Koleksi berhasil dihapus."}
