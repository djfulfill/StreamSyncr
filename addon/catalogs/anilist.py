import sys
import os
from typing import List, Dict

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))
from anilist_api import AniListClient


def _get_client() -> AniListClient:
    return AniListClient()


def _item_to_meta(item: dict) -> dict:
    title = item.get("title", {})
    cover = item.get("coverImage", {})
    start_date = item.get("startDate", {})

    return {
        "id": f"anilist:{item.get('id', '')}",
        "type": "series",
        "name": title.get("english") or title.get("romaji") or title.get("native", ""),
        "year": start_date.get("year"),
        "poster": cover.get("large") or cover.get("medium"),
        "description": item.get("description"),
        "imdb_rating": item.get("averageScore"),
        "genres": item.get("genres", []),
        "anime_id": item.get("id"),
        "status": item.get("status"),
        "episodes": item.get("episodes"),
    }


def trending(skip: int = 0, limit: int = 20) -> List[Dict]:
    client = _get_client()
    items = client.get_trending(per_page=limit + skip)
    return [_item_to_meta(i) for i in items[skip:skip + limit]]


def popular(skip: int = 0, limit: int = 20) -> List[Dict]:
    client = _get_client()
    items = client.get_popular(per_page=limit + skip)
    return [_item_to_meta(i) for i in items[skip:skip + limit]]
