"""Kodi addon — JSON-RPC media center integration."""

import sys
import os
from typing import Any

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "..", "apis"))

from core.addons.base import (
    Addon, CatalogDef, CanonicalItem, VerifyResult,
)
from core.addons.kodi.scrobbler import KodiScrobbler
from core.addons.kodi.sync import KodiSyncSource


class KodiAddon:
    name = "Kodi"
    slug = "kodi"
    description = "Kodi media center — watch history, libraries, and scrobbling"

    config_schema = {
        "kodi_url": {"type": "string", "label": "JSON-RPC URL", "required": True},
        "kodi_username": {"type": "string", "label": "Username"},
        "kodi_password": {"type": "string", "label": "Password", "secret": True},
    }

    config_keys = ["kodi_url", "kodi_username", "kodi_password"]

    catalogs = [
        CatalogDef(id="kodi-movies", label="Movies", type="movie", auth=True),
        CatalogDef(id="kodi-shows", label="Shows", type="series", auth=True),
    ]

    scrobbler = KodiScrobbler()
    sync_source = KodiSyncSource()

    def is_configured(self, config: dict) -> bool:
        return bool(config.get("kodi_url"))

    def verify(self, config: dict) -> VerifyResult:
        if not config.get("kodi_url"):
            return VerifyResult(status="missing_credentials")
        try:
            from kodi_api import KodiClient
            client = KodiClient(
                base_url=config["kodi_url"],
                username=config.get("kodi_username"),
                password=config.get("kodi_password"),
            )
            if client.ping():
                return VerifyResult(status="ok")
            return VerifyResult(status="error", error="Ping failed")
        except Exception as e:
            return VerifyResult(status="error", error=str(e))

    def get_catalog(self, catalog_id: str, media_type: str, skip: int,
                    config: dict, genre: str | None = None) -> list[dict]:
        from kodi_api import KodiClient
        client = KodiClient(
            base_url=config["kodi_url"],
            username=config.get("kodi_username"),
            password=config.get("kodi_password"),
        )

        if catalog_id == "kodi-movies":
            movies = client.get_movies(["title", "year", "rating", "art"])
            return [_movie_to_meta(m) for m in movies[skip:skip + 20]]
        elif catalog_id == "kodi-shows":
            shows = client.get_shows(["title", "year", "rating", "art"])
            return [_show_to_meta(s) for s in shows[skip:skip + 20]]
        return []


def _movie_to_meta(item: dict) -> dict:
    art = item.get("art", {})
    return {
        "id": f"kodi:{item.get('movieid', '')}",
        "type": "movie",
        "name": item.get("title", ""),
        "year": item.get("year"),
        "poster": art.get("poster"),
        "background": art.get("fanart"),
        "imdb_rating": item.get("rating"),
    }


def _show_to_meta(item: dict) -> dict:
    art = item.get("art", {})
    return {
        "id": f"kodi:{item.get('tvshowid', '')}",
        "type": "series",
        "name": item.get("title", ""),
        "year": item.get("year"),
        "poster": art.get("poster"),
        "background": art.get("fanart"),
        "imdb_rating": item.get("rating"),
    }
