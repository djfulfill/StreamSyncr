import sys
import os
from typing import Optional

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))
from tmdb_api import TMDBClient


def imdb_to_tmdb(imdb_id: str) -> Optional[int]:
    tmdb = TMDBClient()
    result = tmdb.find_by_imdb(imdb_id)
    if result:
        movie_results = result.get("movie_results", [])
        if movie_results:
            return movie_results[0].get("id")
        tv_results = result.get("tv_results", [])
        if tv_results:
            return tv_results[0].get("id")
    return None


def tmdb_to_imdb(tmdb_id: int, media_type: str = "movie") -> Optional[str]:
    tmdb = TMDBClient()
    if media_type == "movie":
        result = tmdb.movie(tmdb_id)
    else:
        result = tmdb.tv(tmdb_id)
    return result.get("imdb_id") if result else None
