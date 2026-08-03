import sys
import os
from typing import List, Dict

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))
from sofasidekick_api import SofaSidekickClient


def _get_client(user_config: dict) -> SofaSidekickClient:
    session_id = user_config.get("sofasidekick_session_id", "")
    if not session_id:
        raise ValueError("Sofa Sidekick session ID required")
    return SofaSidekickClient(session_id=session_id)


def _item_to_meta(item: dict, media_type: str) -> dict:
    return {
        "id": f"tvdb:{item.get('tvdb_id', '')}" if item.get("tvdb_id") else str(item.get("id", "")),
        "type": media_type,
        "name": item.get("title") or item.get("name", ""),
        "year": item.get("year"),
        "poster": item.get("poster"),
        "background": item.get("fanart"),
        "description": item.get("overview"),
        "imdb_rating": item.get("rating"),
    }


def shows(user_config: dict, skip: int = 0, limit: int = 20) -> List[Dict]:
    client = _get_client(user_config)
    items = client.get_shows()
    return [_item_to_meta(i, "series") for i in items[skip:skip + limit]]


def movies(user_config: dict, skip: int = 0, limit: int = 20) -> List[Dict]:
    client = _get_client(user_config)
    items = client.get_movies()
    return [_item_to_meta(i, "movie") for i in items[skip:skip + limit]]


def watchlist(user_config: dict, skip: int = 0, limit: int = 20) -> List[Dict]:
    client = _get_client(user_config)
    items = client.get_watchlist()
    return [_item_to_meta(i, "movie") for i in items[skip:skip + limit]]


def upcoming(user_config: dict, skip: int = 0, limit: int = 20) -> List[Dict]:
    client = _get_client(user_config)
    items = client.get_upcoming(days=30)
    return [_item_to_meta(i, "series") for i in items[skip:skip + limit]]
