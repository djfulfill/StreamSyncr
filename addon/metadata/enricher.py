import sys
import os
from typing import Optional

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))
from tmdb_api import TMDBClient


def _img_url(path: str, size: str = "w500") -> str:
    return f"https://image.tmdb.org/t/p/{size}{path}"


def _extract_year(item: dict) -> int:
    date = item.get("release_date") or item.get("first_air_date") or ""
    return int(date[:4]) if date else None


def enrich(tmdb_id: int, media_type: str = "movie") -> Optional[dict]:
    tmdb = TMDBClient()

    if media_type == "movie":
        base = tmdb.movie(tmdb_id)
    else:
        base = tmdb.tv(tmdb_id)

    if not base:
        return None

    poster = base.get("poster_path")
    backdrop = base.get("backdrop_path")

    return {
        "id": f"tt{base.get('imdb_id', '')}" if base.get("imdb_id") else str(tmdb_id),
        "type": media_type,
        "name": base.get("title") or base.get("name", ""),
        "year": _extract_year(base),
        "poster": _img_url(poster) if poster else None,
        "background": _img_url(backdrop, "w1280") if backdrop else None,
        "description": base.get("overview"),
        "runtime": base.get("runtime"),
        "genres": [g["name"] for g in base.get("genres", [])],
        "imdb_rating": base.get("vote_average"),
        "release_info": base.get("release_date") or base.get("first_air_date"),
        "tmdb_id": tmdb_id,
        "imdb_id": base.get("imdb_id"),
    }
