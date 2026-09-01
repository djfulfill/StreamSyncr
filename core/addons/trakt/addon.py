"""Trakt addon — full service integration."""

import sys
import os
from typing import Any

# Ensure apis/ is importable
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "..", "apis"))

from core.addons.base import (
    Addon, CatalogDef, CanonicalItem, ScrobbleEvent, VerifyResult,
)
from core.addons.trakt.scrobbler import TraktScrobbler
from core.addons.trakt.sync import TraktSyncSource
from core.addons.trakt.export import TraktExporter


class TraktAddon:
    """Trakt service addon — provides catalogs, scrobble, sync, and export."""

    name = "Trakt"
    slug = "trakt"
    description = "Track what you watch across all platforms"

    config_schema = {
        "trakt_client_id": {"type": "string", "label": "API Key", "required": True},
        "trakt_token": {"type": "string", "label": "Auth Token", "secret": True},
        "trakt_username": {"type": "string", "label": "Username"},
    }

    config_keys = [
        "trakt_client_id",
        "trakt_token",
        "trakt_username",
    ]

    catalogs = [
        CatalogDef(id="trakt-trending", label="Trending", type="movie|series"),
        CatalogDef(id="trakt-popular", label="Popular", type="movie|series"),
        CatalogDef(id="trakt-trending-shows", label="Trending Shows", type="series"),
        CatalogDef(id="trakt-popular-shows", label="Popular Shows", type="series"),
        CatalogDef(id="trakt-watchlist", label="Watchlist", type="movie|series", auth=True),
        CatalogDef(id="trakt-favorites", label="Favorites", type="movie|series", auth=True),
    ]

    scrobbler = TraktScrobbler()
    sync_source = TraktSyncSource()
    exporter = TraktExporter()

    def is_configured(self, config: dict) -> bool:
        return bool(config.get("trakt_client_id"))

    def verify(self, config: dict) -> VerifyResult:
        if not config.get("trakt_client_id"):
            return VerifyResult(status="missing_credentials")
        try:
            from trakt_api import TraktClient
            client = TraktClient(
                api_key=config["trakt_client_id"],
                token=config.get("trakt_token"),
            )
            if config.get("trakt_token"):
                me = client.me()
                return VerifyResult(
                    status="ok",
                    details={"username": me.get("username", "")},
                )
            return VerifyResult(status="ok", details={"mode": "api_key_only"})
        except Exception as e:
            return VerifyResult(status="error", error=str(e))

    def get_catalog(self, catalog_id: str, media_type: str, skip: int,
                    config: dict, genre: str | None = None) -> list[dict]:
        from trakt_api import TraktClient

        client = TraktClient(
            api_key=config.get("trakt_client_id", ""),
            token=config.get("trakt_token"),
        )

        if catalog_id == "trakt-trending":
            items = client.trending_movies(limit=20 + skip)
            return [_to_meta(i["movie"], "movie") for i in items[skip:skip + 20]]
        elif catalog_id == "trakt-popular":
            items = client.popular_movies(limit=20 + skip)
            return [_to_meta(i, "movie") for i in items[skip:skip + 20]]
        elif catalog_id == "trakt-trending-shows":
            items = client.trending_shows(limit=20 + skip)
            return [_to_meta(i["show"], "series") for i in items[skip:skip + 20]]
        elif catalog_id == "trakt-popular-shows":
            items = client.popular_shows(limit=20 + skip)
            return [_to_meta(i, "series") for i in items[skip:skip + 20]]
        elif catalog_id == "trakt-watchlist":
            items = client.watchlist(media_type="movies" if media_type == "movie" else "shows")
            return [_to_meta(i.get("movie") or i.get("show", {}), media_type)
                    for i in items[skip:skip + 20]]
        elif catalog_id == "trakt-favorites":
            items = client.get_favorites(limit=20 + skip)
            result = []
            for i in items[skip:skip + 20]:
                item_data = i.get("movie") or i.get("show")
                if item_data:
                    result.append(_to_meta(item_data, media_type))
            return result
        return []


def _to_meta(item: dict, stremio_type: str) -> dict:
    """Convert a Trakt item to Stremio meta format."""
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
