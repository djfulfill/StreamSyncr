"""IMDb catalog handler — lists, ratings, recently viewed."""

import sys
import os
import traceback
from typing import List, Dict

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "apis"))
from imdb_api import IMDbClient


def _get_client(user_config: dict) -> IMDbClient:
    return IMDbClient(full_cookies=user_config.get("imdb_full_cookies", ""))


def _item_to_meta(item: dict, stremio_type: str) -> dict:
    title_id = item.get("id", "")
    title_text = item.get("titleText", {}).get("text", "") if isinstance(item.get("titleText"), dict) else item.get("titleText", "")
    year = item.get("releaseYear", {}).get("year") if isinstance(item.get("releaseYear"), dict) else item.get("releaseYear")
    primary_image = item.get("primaryImage", {})
    poster = primary_image.get("url") if isinstance(primary_image, dict) else None

    return {
        "id": title_id if title_id.startswith("tt") else f"tt{title_id}",
        "type": stremio_type,
        "name": title_text,
        "year": year,
        "poster": poster,
        "imdb_id": title_id,
    }


def recently_viewed(skip: int = 0, limit: int = 20, user_config: dict = None) -> List[Dict]:
    """Get recently viewed titles."""
    if not user_config or not user_config.get("imdb_full_cookies"):
        return []
    client = _get_client(user_config)
    try:
        items = client.get_recently_viewed(count=skip + limit)
        return [_item_to_meta(i, "movie") for i in items[skip:skip + limit]]
    except Exception as e:
        print(f"[IMDb] recently_viewed error: {e}")
        return []


def lists(skip: int = 0, limit: int = 20, user_config: dict = None) -> List[Dict]:
    """Get user's IMDb lists as catalog entries."""
    if not user_config or not user_config.get("imdb_full_cookies"):
        return []
    client = _get_client(user_config)
    try:
        lists_data = client.get_lists()
        items = []
        for lst in lists_data[skip:skip + limit]:
            list_id = lst.get("id", "")
            name = lst.get("name", {})
            if isinstance(name, dict):
                name = name.get("originalText", "")
            item_count = lst.get("items", {}).get("total", 0)
            items.append({
                "id": f"imdb-list:{list_id}",
                "type": "movie",
                "name": f"📋 {name} ({item_count} items)",
                "imdb_list_id": list_id,
            })
        return items
    except Exception as e:
        print(f"[IMDb] lists error: {e}")
        return []


def ratings(skip: int = 0, limit: int = 20, user_config: dict = None) -> List[Dict]:
    """Get user's ratings — fetches recently viewed and filters for rated items."""
    if not user_config or not user_config.get("imdb_full_cookies"):
        return []
    client = _get_client(user_config)
    try:
        items = client.get_recently_viewed(count=50)
        rated = []
        for item in items:
            title_id = item.get("id", "")
            if title_id:
                try:
                    ratings_data = client.get_ratings([title_id])
                    if ratings_data and ratings_data[0].get("userRating"):
                        rated.append(item)
                except Exception:
                    continue
        return [_item_to_meta(i, "movie") for i in rated[skip:skip + limit]]
    except Exception as e:
        print(f"[IMDb] ratings error: {e}")
        return []
