import sys
import os
from typing import List, Dict

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))
from sofasidekick_api import SofaSidekickClient


def _get_client(user_config: dict) -> SofaSidekickClient:
    session_id = (user_config.get("sofasidekick_session_id")
                  or user_config.get("session_id") or "")
    if not session_id:
        raise ValueError("Sofa Sidekick session ID required")
    return SofaSidekickClient(
        session_id=session_id,
        cf_clearance=(user_config.get("sofasidekick_cf_clearance")
                      or user_config.get("cf_clearance")) or None,
        cf_bm=(user_config.get("sofasidekick_cf_bm")
               or user_config.get("__cf_bm")) or None,
    )


def _show_to_meta(item: dict) -> dict:
    show = item.get("show", item)
    tvdb_id = show.get("tvdbId")
    return {
        "id": f"tvdb:{tvdb_id}" if tvdb_id else str(show.get("id", "")),
        "type": "series",
        "name": show.get("title", ""),
        "year": show.get("year"),
        "poster": show.get("posterUrl"),
        "imdb_rating": show.get("rating"),
    }


def _movie_to_meta(item: dict) -> dict:
    movie = item.get("movie", item)
    tvdb_id = movie.get("tvdbId")
    return {
        "id": f"tvdb:{tvdb_id}" if tvdb_id else str(movie.get("id", "")),
        "type": "movie",
        "name": movie.get("title", ""),
        "year": movie.get("year"),
        "poster": movie.get("posterUrl"),
        "imdb_rating": movie.get("rating"),
    }


def shows(user_config: dict, skip: int = 0, limit: int = 20) -> List[Dict]:
    client = _get_client(user_config)
    try:
        items = client.get_shows()
    except ValueError:
        return []
    return [_show_to_meta(i) for i in items[skip:skip + limit]]


def movies(user_config: dict, skip: int = 0, limit: int = 20) -> List[Dict]:
    client = _get_client(user_config)
    data = client.get_movies()
    items = data.get("movies", data) if isinstance(data, dict) else data
    return [_movie_to_meta(i) for i in items[skip:skip + limit]]


def watchlist(user_config: dict, skip: int = 0, limit: int = 20) -> List[Dict]:
    client = _get_client(user_config)
    try:
        items = client.get_watchlist()
    except ValueError:
        return []
    return [_movie_to_meta(i) for i in items[skip:skip + limit]]


def upcoming(user_config: dict, skip: int = 0, limit: int = 20) -> List[Dict]:
    client = _get_client(user_config)
    data = client.get_upcoming(days=30)
    shows_list = data.get("shows", data) if isinstance(data, dict) else data
    return [_show_to_meta(i) for i in shows_list[skip:skip + limit]]
