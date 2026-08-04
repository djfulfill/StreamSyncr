import sys
import os
from typing import List, Dict, Optional

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))
from tmdb_api import TMDBClient


def _get_client(api_key: str = None) -> TMDBClient:
    """Get TMDB client with explicit key, falling back to env var."""
    return TMDBClient(api_key=api_key or os.environ.get("TMDB_API_KEY", ""))


def _item_to_meta(item: dict, stremio_type: str) -> dict:
    tmdb_id = item.get("id")
    title = item.get("title") or item.get("name", "")
    poster = item.get("poster_path")
    backdrop = item.get("backdrop_path")

    return {
        "id": f"tt{item.get('imdb_id', '')}" if item.get("imdb_id") else str(tmdb_id),
        "type": stremio_type,
        "name": title,
        "year": _extract_year(item),
        "poster": _img_url(poster) if poster else None,
        "background": _img_url(backdrop, "w1280") if backdrop else None,
        "description": item.get("overview"),
        "imdb_rating": item.get("vote_average"),
        "release_info": item.get("release_date") or item.get("first_air_date"),
        "tmdb_id": tmdb_id,
    }


def _img_url(path: str, size: str = "w500") -> str:
    return f"https://image.tmdb.org/t/p/{size}{path}"


def _extract_year(item: dict) -> int:
    date = item.get("release_date") or item.get("first_air_date") or ""
    return int(date[:4]) if date else None


def trending_movies(api_key: str = None, skip: int = 0, limit: int = 20) -> List[Dict]:
    client = _get_client(api_key)
    items = client.trending_movies(limit=limit + skip)
    return [_item_to_meta(i, "movie") for i in items[skip:skip + limit]]


def popular_movies(api_key: str = None, skip: int = 0, limit: int = 20) -> List[Dict]:
    client = _get_client(api_key)
    items = client.popular_movies(limit=limit + skip)
    return [_item_to_meta(i, "movie") for i in items[skip:skip + limit]]


def top_rated_movies(api_key: str = None, skip: int = 0, limit: int = 20) -> List[Dict]:
    client = _get_client(api_key)
    items = client.top_rated_movies(limit=limit + skip)
    return [_item_to_meta(i, "movie") for i in items[skip:skip + limit]]


def now_playing(api_key: str = None, skip: int = 0, limit: int = 20) -> List[Dict]:
    client = _get_client(api_key)
    items = client.now_playing()
    return [_item_to_meta(i, "movie") for i in items[skip:skip + limit]]


def upcoming(api_key: str = None, skip: int = 0, limit: int = 20) -> List[Dict]:
    client = _get_client(api_key)
    items = client.upcoming()
    return [_item_to_meta(i, "movie") for i in items[skip:skip + limit]]


def trending_tv(api_key: str = None, skip: int = 0, limit: int = 20) -> List[Dict]:
    client = _get_client(api_key)
    items = client.trending_tv(limit=limit + skip)
    return [_item_to_meta(i, "series") for i in items[skip:skip + limit]]


def popular_tv(api_key: str = None, skip: int = 0, limit: int = 20) -> List[Dict]:
    client = _get_client(api_key)
    items = client.popular_tv(limit=limit + skip)
    return [_item_to_meta(i, "series") for i in items[skip:skip + limit]]
