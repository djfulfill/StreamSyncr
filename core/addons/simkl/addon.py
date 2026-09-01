"""Simkl addon — TV/movie/anime tracking with sync."""

import sys
import os
from typing import Any

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "..", "apis"))

from core.addons.base import (
    Addon, CatalogDef, CanonicalItem, ScrobbleEvent, VerifyResult,
)
from core.addons.simkl.scrobbler import SimklScrobbler
from core.addons.simkl.sync import SimklSyncSource
from core.addons.simkl.export import SimklExporter


class SimklAddon:
    name = "Simkl"
    slug = "simkl"
    description = "Track TV, movies, and anime across all platforms"

    config_schema = {
        "simkl_client_id": {"type": "string", "label": "Client ID", "required": True},
        "simkl_access_token": {"type": "string", "label": "Access Token", "secret": True},
    }

    config_keys = ["simkl_client_id", "simkl_access_token"]

    catalogs = [
        CatalogDef(id="simkl-trending", label="Trending", type="movie|series"),
        CatalogDef(id="simkl-popular", label="Popular", type="movie|series"),
        CatalogDef(id="simkl-trending-shows", label="Trending Shows", type="series"),
        CatalogDef(id="simkl-popular-shows", label="Popular Shows", type="series"),
        CatalogDef(id="simkl-anime-trending", label="Trending Anime", type="series"),
        CatalogDef(id="simkl-anime-popular", label="Popular Anime", type="series"),
        CatalogDef(id="simkl-watchlist", label="Watchlist", type="movie|series", auth=True),
        CatalogDef(id="simkl-watching", label="Watching", type="series", auth=True),
        CatalogDef(id="simkl-completed", label="Completed", type="movie|series", auth=True),
    ]

    scrobbler = SimklScrobbler()
    sync_source = SimklSyncSource()
    exporter = SimklExporter()

    def is_configured(self, config: dict) -> bool:
        return bool(config.get("simkl_client_id"))

    def verify(self, config: dict) -> VerifyResult:
        if not config.get("simkl_client_id"):
            return VerifyResult(status="missing_credentials")
        try:
            from simkl_api import SimklClient
            client = SimklClient(client_id=config["simkl_client_id"])
            if config.get("simkl_access_token"):
                client.access_token = config["simkl_access_token"]
            return VerifyResult(status="ok")
        except Exception as e:
            return VerifyResult(status="error", error=str(e))

    def get_catalog(self, catalog_id: str, media_type: str, skip: int,
                    config: dict, genre: str | None = None) -> list[dict]:
        from simkl_api import SimklClient

        client = SimklClient(client_id=config.get("simkl_client_id", ""))

        if catalog_id == "simkl-trending":
            items = client.trending_movies(period="week")
            return [_to_meta(i["movie"], "movie") for i in items[skip:skip + 20]]
        elif catalog_id == "simkl-popular":
            items = client.popular_movies()
            return [_to_meta(i, "movie") for i in items[skip:skip + 20]]
        elif catalog_id == "simkl-trending-shows":
            items = client.trending_shows(period="week")
            return [_to_meta(i["show"], "series") for i in items[skip:skip + 20]]
        elif catalog_id == "simkl-popular-shows":
            items = client.popular_shows()
            return [_to_meta(i, "series") for i in items[skip:skip + 20]]
        elif catalog_id == "simkl-anime-trending":
            items = client.trending_anime(period="week")
            return [_to_meta(i["anime"], "series") for i in items[skip:skip + 20]]
        elif catalog_id == "simkl-anime-popular":
            items = client.popular_anime()
            return [_to_meta(i, "series") for i in items[skip:skip + 20]]
        elif catalog_id in ("simkl-watchlist", "simkl-watching", "simkl-completed"):
            if not config.get("simkl_access_token"):
                return []
            client.access_token = config["simkl_access_token"]
            list_type = {"simkl-watchlist": "plantowatch", "simkl-watching": "watching",
                         "simkl-completed": "completed"}[catalog_id]
            data = client.get_all_items(list_type=list_type)
            all_items = []
            for key in ("movies", "shows", "anime"):
                all_items.extend(data.get(key, []) if isinstance(data, dict) else [])
            return [_to_meta(i, media_type) for i in all_items[skip:skip + 20]]
        return []


def _to_meta(item: dict, stremio_type: str) -> dict:
    ids = item.get("ids", {})
    return {
        "id": f"tt{ids.get('imdb', '')}" if ids.get("imdb") else str(ids.get("simkl", "")),
        "type": stremio_type,
        "name": item.get("title") or item.get("name", ""),
        "year": item.get("year"),
        "poster": item.get("poster"),
        "background": item.get("fanart"),
        "imdb_id": ids.get("imdb"),
        "simkl_id": ids.get("simkl"),
        "tmdb_id": ids.get("tmdb"),
    }
