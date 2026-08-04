import sys
import os
from typing import List, Dict, Optional

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))
from wetrakr_api.client import WeTrakrClient


# Known list IDs (updated 2026-08-02)
_LIST_MAP = {
    "favorites": 19879,
    "watchlist": 19876,
}


def _get_client(user_config: dict) -> WeTrakrClient:
    username = user_config.get("wetrakr_username", "")
    access_token = user_config.get("wetrakr_access_token", "")
    refresh_token = user_config.get("wetrakr_refresh_token", "")
    if not username or not access_token:
        raise ValueError("WeTrakr username and tokens required")
    return WeTrakrClient(
        access_token=access_token,
        refresh_token=refresh_token,
        username=username
    )


def _item_to_meta(item: dict, media_type: str) -> dict:
    ids = item.get("ids", {})
    tmdb = ids.get("tmdb", {})
    tmdb_id = tmdb.get("id") if isinstance(tmdb, dict) else tmdb
    return {
        "id": f"tmdb:{tmdb_id}" if tmdb_id else str(item.get("id", "")),
        "type": media_type,
        "name": item.get("title") or item.get("name", ""),
        "year": item.get("year"),
        "poster": item.get("poster"),
        "background": item.get("fanart"),
        "description": item.get("overview"),
        "imdb_rating": item.get("rating"),
        "tmdb_id": tmdb_id,
    }


def _find_list_id(client: WeTrakrClient, name: str) -> Optional[int]:
    key = name.lower().strip()
    if key in _LIST_MAP:
        return _LIST_MAP[key]
    lists = client.get_lists()
    for lst in lists:
        if lst.get("name", "").lower() == key:
            return lst.get("id")
    return None


def _get_list_items(client: WeTrakrClient, list_id: int,
                     skip: int = 0, limit: int = 20) -> List[Dict]:
    page = (skip // limit) + 1
    items = client.get_list_items(list_id, page=page, limit=limit)
    offset = skip % limit
    return items[offset:offset + limit]


def favorites(user_config: dict, skip: int = 0, limit: int = 20) -> List[Dict]:
    client = _get_client(user_config)
    list_id = _find_list_id(client, "favorites")
    if not list_id:
        return []
    items = _get_list_items(client, list_id, skip, limit)
    return [_item_to_meta(i, "movie") for i in items]


def watchlist(user_config: dict, skip: int = 0, limit: int = 20) -> List[Dict]:
    client = _get_client(user_config)
    list_id = _find_list_id(client, "watchlist")
    if not list_id:
        return []
    items = _get_list_items(client, list_id, skip, limit)
    return [_item_to_meta(i, "movie") for i in items]


def watching(user_config: dict, skip: int = 0, limit: int = 20) -> List[Dict]:
    return []


def ratings(user_config: dict, skip: int = 0, limit: int = 20) -> List[Dict]:
    return []


def list_items(user_config: dict, list_id: int, skip: int = 0, limit: int = 20) -> List[Dict]:
    client = _get_client(user_config)
    items = _get_list_items(client, list_id, skip, limit)
    return [_item_to_meta(i, "movie") for i in items]
