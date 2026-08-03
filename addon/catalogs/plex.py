import sys
import os
from typing import List, Dict

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))
from plex_api import PlexClient


def _get_client(user_config: dict) -> PlexClient:
    base_url = user_config.get("plex_url", "")
    token = user_config.get("plex_token", "")
    if not base_url or not token:
        raise ValueError("Plex URL and token required")
    return PlexClient(base_url=base_url, token=token)


def _item_to_meta(item: dict) -> dict:
    guids = {g["id"].split("://")[0]: g["id"].split("://")[1] for g in item.get("Guid", [])}
    imdb = guids.get("imdb", "")
    return {
        "id": f"tt{imdb}" if imdb else str(item.get("ratingKey", "")),
        "type": "movie",
        "name": item.get("title", ""),
        "year": item.get("year"),
        "poster": item.get("thumb"),
        "background": item.get("art"),
        "description": item.get("summary"),
        "imdb_rating": item.get("rating"),
        "imdb_id": imdb,
        "plex_rating_key": item.get("ratingKey"),
    }


def library_movies(user_config: dict, skip: int = 0, limit: int = 20) -> List[Dict]:
    client = _get_client(user_config)
    libraries = client.get_libraries()
    movies_lib = next((l for l in libraries if l.get("type") == "movie"), None)
    if not movies_lib:
        return []
    items = client.get_library_items(movies_lib["key"], libtype="movie")
    return [_item_to_meta(i) for i in items[skip:skip + limit]]
