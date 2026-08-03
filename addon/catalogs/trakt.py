import sys
import os
from typing import List, Dict

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))
from trakt_api import TraktClient


def _get_client() -> TraktClient:
    return TraktClient()


def _item_to_meta(item: dict, stremio_type: str) -> dict:
    ids = item.get("ids", {})
    imdb = ids.get("imdb", "")
    return {
        "id": f"tt{imdb}" if imdb else str(ids.get("trakt", "")),
        "type": stremio_type,
        "name": item.get("title", ""),
        "year": item.get("year"),
        "poster": item.get("poster"),
        "background": item.get("fanart"),
        "imdb_id": ids.get("imdb"),
        "trakt_id": ids.get("trakt"),
        "tmdb_id": ids.get("tmdb"),
    }


def trending_movies(skip: int = 0, limit: int = 20) -> List[Dict]:
    client = _get_client()
    items = client.trending_movies(limit=limit + skip)
    return [_item_to_meta(i["movie"], "movie") for i in items[skip:skip + limit]]


def popular_movies(skip: int = 0, limit: int = 20) -> List[Dict]:
    client = _get_client()
    items = client.popular_movies(limit=limit + skip)
    return [_item_to_meta(i, "movie") for i in items[skip:skip + limit]]


def trending_shows(skip: int = 0, limit: int = 20) -> List[Dict]:
    client = _get_client()
    items = client.trending_shows(limit=limit + skip)
    return [_item_to_meta(i["show"], "series") for i in items[skip:skip + limit]]


def popular_shows(skip: int = 0, limit: int = 20) -> List[Dict]:
    client = _get_client()
    items = client.popular_shows(limit=limit + skip)
    return [_item_to_meta(i, "series") for i in items[skip:skip + limit]]
