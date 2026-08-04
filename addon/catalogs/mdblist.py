import sys
import os
from typing import List, Dict

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))
from mdblist_api import MDBListClient


def _get_client(api_key: str = None) -> MDBListClient:
    return MDBListClient(api_key=api_key or os.environ.get("MDBLIST_API_KEY", ""))


def _item_to_meta(item: dict, stremio_type: str) -> dict:
    ids = item.get("ids", {})
    # Search results use "imdbid", list items use "imdb"
    imdb_id = ids.get("imdb") or ids.get("imdbid") or item.get("imdb_id", "")
    if imdb_id and not imdb_id.startswith("tt"):
        imdb_id = f"tt{imdb_id}"
    tmdb_id = ids.get("tmdb") or ids.get("tmdbid") or item.get("id")
    return {
        "id": imdb_id or str(tmdb_id or item.get("id", "")),
        "type": stremio_type,
        "name": item.get("title", ""),
        "year": item.get("release_year") or item.get("year"),
        "imdb_id": imdb_id or None,
        "tmdb_id": tmdb_id,
    }


def user_lists(api_key: str = None) -> List[Dict]:
    """Fetch user's lists for dynamic catalog generation."""
    client = _get_client(api_key)
    lists = client.my_lists()
    result = []
    for lst in lists:
        result.append({
            "id": lst["id"],
            "name": lst["name"],
            "type": "movie" if lst.get("mediatype") == "movie" else "series",
            "items": lst.get("items", 0),
        })
    return result


def list_items(list_id: int, api_key: str = None, skip: int = 0,
               limit: int = 20) -> List[Dict]:
    """Fetch items from a specific MDBList list."""
    client = _get_client(api_key)
    data = client.list_items(list_id, limit=limit + skip, offset=skip)
    metas = []
    for item in data.get("movies", [])[:limit]:
        metas.append(_item_to_meta(item, "movie"))
    for item in data.get("shows", [])[:limit]:
        metas.append(_item_to_meta(item, "series"))
    return metas


def search(query: str, api_key: str = None, skip: int = 0,
           limit: int = 20) -> List[Dict]:
    """Search MDBList by title."""
    client = _get_client(api_key)
    data = client.search(query)
    results = data.get("search", [])
    metas = []
    for item in results[skip:skip + limit]:
        stremio_type = "movie" if item.get("type") == "movie" else "series"
        metas.append(_item_to_meta(item, stremio_type))
    return metas
