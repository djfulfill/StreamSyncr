"""Plex addon — media server integration."""

import sys
import os
from typing import Any

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "..", "apis"))

from core.addons.base import (
    Addon, CatalogDef, CanonicalItem, ScrobbleEvent, VerifyResult,
)
from core.addons.plex.scrobbler import PlexScrobbler
from core.addons.plex.sync import PlexSyncSource
from core.addons.plex.export import PlexExporter


class PlexAddon:
    name = "Plex"
    slug = "plex"
    description = "Your personal media server — watch history, libraries, and ratings"

    config_schema = {
        "plex_token": {"type": "string", "label": "Token", "secret": True, "required": True},
        "plex_url": {"type": "string", "label": "Server URL", "required": True},
    }

    config_keys = ["plex_token", "plex_url"]

    catalogs = [
        CatalogDef(id="plex-library", label="Library", type="movie|series", auth=True),
    ]

    scrobbler = PlexScrobbler()
    sync_source = PlexSyncSource()
    exporter = PlexExporter()

    def is_configured(self, config: dict) -> bool:
        return bool(config.get("plex_token") and config.get("plex_url"))

    def verify(self, config: dict) -> VerifyResult:
        if not config.get("plex_token") or not config.get("plex_url"):
            return VerifyResult(status="missing_credentials")
        try:
            from plex_api import PlexClient
            client = PlexClient(base_url=config["plex_url"], token=config["plex_token"])
            libraries = client.get_libraries()
            return VerifyResult(
                status="ok",
                details={"libraries": len(libraries)},
            )
        except Exception as e:
            return VerifyResult(status="error", error=str(e))

    def get_catalog(self, catalog_id: str, media_type: str, skip: int,
                    config: dict, genre: str | None = None) -> list[dict]:
        from plex_api import PlexClient

        client = PlexClient(base_url=config["plex_url"], token=config["plex_token"])

        if catalog_id == "plex-library":
            libraries = client.get_libraries()
            lib_type = "movie" if media_type == "movie" else "show"
            lib = next((l for l in libraries if l.get("type") == lib_type), None)
            if not lib:
                return []
            items = client.get_library_items(lib["key"], libtype=lib_type)
            return [_to_meta(i) for i in items[skip:skip + 20]]
        return []


def _to_meta(item: dict) -> dict:
    guids = {g["id"].split("://")[0]: g["id"].split("://")[1] for g in item.get("Guid", [])}
    imdb = guids.get("imdb", "")
    return {
        "id": f"tt{imdb}" if imdb else str(item.get("ratingKey", "")),
        "type": "movie",
        "name": item.get("title", ""),
        "year": item.get("year"),
        "poster": item.get("thumb"),
        "background": item.get("art"),
        "description": item.get("summary"),
        "imdb_rating": item.get("rating"),
        "imdb_id": imdb,
        "plex_rating_key": item.get("ratingKey"),
    }
