import sys
import os
from typing import List, Dict

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))
from simkl_api import SimklClient


def _get_client(user_config: dict = None) -> SimklClient:
    client_id = ""
    if user_config:
        client_id = user_config.get("simkl_client_id", "")
    if not client_id:
        client_id = os.environ.get("SIMKL_CLIENT_ID", "")
    return SimklClient(client_id=client_id)


def _item_to_meta(item: dict, stremio_type: str) -> dict:
    ids = item.get("ids", {})
    return {
        "id": f"tt{ids.get('imdb', '')}" if ids.get("imdb") else str(ids.get("simkl", "")),
        "type": stremio_type,
        "name": item.get("title") or item.get("name", ""),
        "year": item.get("year"),
        "poster": item.get("poster"),
        "background": item.get("fanart"),
        "imdb_id": ids.get("imdb"),
        "simkl_id": ids.get("simkl"),
        "tmdb_id": ids.get("tmdb"),
    }


def trending_movies(skip: int = 0, limit: int = 20, user_config: dict = None) -> List[Dict]:
    client = _get_client(user_config)
    items = client.trending_movies(period="week")
    return [_item_to_meta(i["movie"], "movie") for i in items[skip:skip + limit]]


def popular_movies(skip: int = 0, limit: int = 20, user_config: dict = None) -> List[Dict]:
    client = _get_client(user_config)
    items = client.popular_movies()
    return [_item_to_meta(i, "movie") for i in items[skip:skip + limit]]


def trending_shows(skip: int = 0, limit: int = 20, user_config: dict = None) -> List[Dict]:
    client = _get_client(user_config)
    items = client.trending_shows(period="week")
    return [_item_to_meta(i["show"], "series") for i in items[skip:skip + limit]]


def popular_shows(skip: int = 0, limit: int = 20, user_config: dict = None) -> List[Dict]:
    client = _get_client(user_config)
    items = client.popular_shows()
    return [_item_to_meta(i, "series") for i in items[skip:skip + limit]]


def trending_anime(skip: int = 0, limit: int = 20, user_config: dict = None) -> List[Dict]:
    client = _get_client(user_config)
    items = client.trending_anime(period="week")
    return [_item_to_meta(i["anime"], "anime") for i in items[skip:skip + limit]]


def popular_anime(skip: int = 0, limit: int = 20, user_config: dict = None) -> List[Dict]:
    client = _get_client(user_config)
    items = client.popular_anime()
    return [_item_to_meta(i, "anime") for i in items[skip:skip + limit]]


# ── User lists (require access_token) ──────────────────────────

def _get_auth_client(user_config: dict) -> SimklClient:
    """Get a Simkl client with access token for user-specific calls."""
    client_id = (user_config or {}).get("simkl_client_id", "") or os.environ.get("SIMKL_CLIENT_ID", "")
    access_token = (user_config or {}).get("simkl_access_token", "")
    if not client_id:
        raise ValueError("Simkl client_id required")
    if not access_token:
        raise ValueError("Simkl access_token required for user lists")
    return SimklClient(client_id=client_id, access_token=access_token)


def _user_item_to_meta(item: dict, stremio_type: str) -> dict:
    """Convert a Simkl user-list item to Stremio meta."""
    # Simkl user items have: title, year, ids (imdb, tmdb, simkl), poster, fanart
    return _item_to_meta(item, stremio_type)


def user_watchlist(skip: int = 0, limit: int = 20, user_config: dict = None) -> List[Dict]:
    """Get user's plan-to-watch list."""
    client = _get_auth_client(user_config)
    data = client.get_all_items(list_type="plantowatch")
    items = _extract_simkl_items(data)
    return [_user_item_to_meta(i, "movie") for i in items[skip:skip + limit]]


def user_watching(skip: int = 0, limit: int = 20, user_config: dict = None) -> List[Dict]:
    """Get user's currently watching list."""
    client = _get_auth_client(user_config)
    data = client.get_all_items(list_type="watching")
    items = _extract_simkl_items(data)
    return [_user_item_to_meta(i, "series") for i in items[skip:skip + limit]]


def user_completed(skip: int = 0, limit: int = 20, user_config: dict = None) -> List[Dict]:
    """Get user's completed list."""
    client = _get_auth_client(user_config)
    data = client.get_all_items(list_type="completed")
    items = _extract_simkl_items(data)
    return [_user_item_to_meta(i, "movie") for i in items[skip:skip + limit]]


def _extract_simkl_items(data: dict) -> List[dict]:
    """Extract items from Simkl /sync/all-items response.

    Response format: {"movies": [...], "shows": [...], "anime": [...]}
    Each item has: title, year, ids, poster, fanart, last_watched, etc.
    """
    all_items = []
    for key in ("movies", "shows", "anime"):
        items = data.get(key, []) if isinstance(data, dict) else []
        all_items.extend(items)
    return all_items
