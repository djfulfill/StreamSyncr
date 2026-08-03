import sys
import os
from typing import List, Dict

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))
from wetrakr_api.client import WeTrakrClient


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


def favorites(user_config: dict, skip: int = 0, limit: int = 20) -> List[Dict]:
    client = _get_client(user_config)
    items = client.get_favorites()
    results = []
    for item in items[skip:skip + limit]:
        media_type = item.get("type", "movie")
        obj = item.get("movie") or item.get("show") or item
        results.append(_item_to_meta(obj, "movie" if media_type == "movie" else "series"))
    return results


def watchlist(user_config: dict, skip: int = 0, limit: int = 20) -> List[Dict]:
    client = _get_client(user_config)
    items = client.get_plantowatch()
    results = []
    for item in items[skip:skip + limit]:
        obj = item.get("movie") or item.get("show") or item
        results.append(_item_to_meta(obj, "movie"))
    return results


def watching(user_config: dict, skip: int = 0, limit: int = 20) -> List[Dict]:
    client = _get_client(user_config)
    items = client.get_watching()
    results = []
    for item in items[skip:skip + limit]:
        obj = item.get("movie") or item.get("show") or item
        results.append(_item_to_meta(obj, "series"))
    return results


def ratings(user_config: dict, skip: int = 0, limit: int = 20) -> List[Dict]:
    client = _get_client(user_config)
    items = client.get_ratings()
    results = []
    for item in items[skip:skip + limit]:
        obj = item.get("movie") or item.get("show") or item
        results.append(_item_to_meta(obj, "movie"))
    return results


def list_items(user_config: dict, list_id: int, skip: int = 0, limit: int = 20) -> List[Dict]:
    client = _get_client(user_config)
    items = client.get_list_items(list_id, page=(skip // limit) + 1, limit=limit)
    return [_item_to_meta(i, "movie") for i in items]
