"""Sofa Sidekick addon — shows, movies, watchlist, upcoming."""

import sys
import os
from typing import Any

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "..", "apis"))

from core.addons.base import (
    Addon, CatalogDef, VerifyResult,
)
from core.addons.sofasidekick.scrobbler import SofaSidekickScrobbler
from core.addons.sofasidekick.export import SofaSidekickExporter


class SofaSidekickAddon:
    name = "Sofa Sidekick"
    slug = "sofasidekick"
    description = "Track shows and movies with Sofa Sidekick"

    config_schema = {
        "sofasidekick_session_id": {"type": "string", "label": "Session ID", "secret": True, "required": True},
        "sofasidekick_cf_clearance": {"type": "string", "label": "CF Clearance", "secret": True},
        "sofasidekick_cf_bm": {"type": "string", "label": "CF BM", "secret": True},
    }

    config_keys = ["sofasidekick_session_id", "sofasidekick_cf_clearance", "sofasidekick_cf_bm"]

    catalogs = [
        CatalogDef(id="sofasidekick-shows", label="Shows", type="series", auth=True),
        CatalogDef(id="sofasidekick-movies", label="Movies", type="movie", auth=True),
        CatalogDef(id="sofasidekick-watchlist", label="Watchlist", type="movie|series", auth=True),
        CatalogDef(id="sofasidekick-upcoming", label="Upcoming", type="series", auth=True),
    ]

    scrobbler = SofaSidekickScrobbler()
    exporter = SofaSidekickExporter()

    def is_configured(self, config: dict) -> bool:
        return bool(config.get("sofasidekick_session_id"))

    def verify(self, config: dict) -> VerifyResult:
        if not config.get("sofasidekick_session_id"):
            return VerifyResult(status="missing_credentials")
        return VerifyResult(status="ok")

    def get_catalog(self, catalog_id: str, media_type: str, skip: int,
                    config: dict, genre: str | None = None) -> list[dict]:
        from sofasidekick_api import SofaSidekickClient
        client = SofaSidekickClient(
            session_id=config["sofasidekick_session_id"],
            cf_clearance=config.get("sofasidekick_cf_clearance"),
            cf_bm=config.get("sofasidekick_cf_bm"),
        )

        if catalog_id == "sofasidekick-shows":
            items = client.get_shows()
            return [_show_to_meta(i) for i in items[skip:skip + 20]]
        elif catalog_id == "sofasidekick-movies":
            data = client.get_movies()
            items = data.get("movies", data) if isinstance(data, dict) else data
            return [_movie_to_meta(i) for i in items[skip:skip + 20]]
        elif catalog_id == "sofasidekick-watchlist":
            items = client.get_watchlist()
            return [_movie_to_meta(i) for i in items[skip:skip + 20]]
        elif catalog_id == "sofasidekick-upcoming":
            data = client.get_upcoming(days=30)
            items = data.get("shows", data) if isinstance(data, dict) else data
            return [_show_to_meta(i) for i in items[skip:skip + 20]]
        return []


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
