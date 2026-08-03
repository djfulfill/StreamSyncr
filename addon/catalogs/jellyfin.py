import sys
import os
from typing import List, Dict

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))
from jellyfin_api import JellyfinClient


def _get_client(user_config: dict) -> JellyfinClient:
    base_url = user_config.get("jellyfin_url", "")
    api_key = user_config.get("jellyfin_api_key", "")
    user_id = user_config.get("jellyfin_user_id")
    if not base_url or not api_key:
        raise ValueError("Jellyfin URL and API key required")
    return JellyfinClient(base_url=base_url, api_key=api_key, user_id=user_id)


def _item_to_meta(item: dict) -> dict:
    provider_ids = item.get("ProviderIds", {})
    imdb = provider_ids.get("Imdb", "")
    return {
        "id": f"tt{imdb}" if imdb else str(item.get("Id", "")),
        "type": "movie",
        "name": item.get("Name", ""),
        "year": item.get("ProductionYear"),
        "poster": item.get("ImageTags", {}).get("Primary"),
        "background": item.get("ImageTags", {}).get("Backdrop"),
        "description": item.get("Overview"),
        "imdb_rating": item.get("CommunityRating"),
        "imdb_id": imdb,
        "jellyfin_id": item.get("Id"),
    }


def library_movies(user_config: dict, skip: int = 0, limit: int = 20) -> List[Dict]:
    client = _get_client(user_config)
    libraries = client.get_libraries()
    movies_lib = next((l for l in libraries if l.get("CollectionType") == "movies"), None)
    if not movies_lib:
        return []
    items = client.get_library_items(movies_lib["Id"], include_item_types="Movie")
    return [_item_to_meta(i) for i in items[skip:skip + limit]]
