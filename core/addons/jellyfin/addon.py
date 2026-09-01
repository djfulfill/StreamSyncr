"""Jellyfin addon — open-source media server integration."""

import sys
import os
from typing import Any

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "..", "apis"))

from core.addons.base import (
    Addon, CatalogDef, CanonicalItem, ScrobbleEvent, VerifyResult,
)
from core.addons.jellyfin.scrobbler import JellyfinScrobbler
from core.addons.jellyfin.sync import JellyfinSyncSource
from core.addons.jellyfin.export import JellyfinExporter


class JellyfinAddon:
    name = "Jellyfin"
    slug = "jellyfin"
    description = "Free and open media server — watch history, libraries, and ratings"

    config_schema = {
        "jellyfin_url": {"type": "string", "label": "Server URL", "required": True},
        "jellyfin_api_key": {"type": "string", "label": "API Key", "secret": True, "required": True},
        "jellyfin_user_id": {"type": "string", "label": "User ID"},
    }

    config_keys = ["jellyfin_url", "jellyfin_api_key", "jellyfin_user_id"]

    catalogs = [
        CatalogDef(id="jellyfin-library", label="Library", type="movie|series", auth=True),
    ]

    scrobbler = JellyfinScrobbler()
    sync_source = JellyfinSyncSource()
    exporter = JellyfinExporter()

    def is_configured(self, config: dict) -> bool:
        return bool(config.get("jellyfin_url") and config.get("jellyfin_api_key"))

    def verify(self, config: dict) -> VerifyResult:
        if not config.get("jellyfin_url") or not config.get("jellyfin_api_key"):
            return VerifyResult(status="missing_credentials")
        try:
            from jellyfin_api import JellyfinClient
            client = JellyfinClient(
                base_url=config["jellyfin_url"],
                api_key=config["jellyfin_api_key"],
                user_id=config.get("jellyfin_user_id"),
            )
            libraries = client.get_libraries()
            return VerifyResult(status="ok", details={"libraries": len(libraries)})
        except Exception as e:
            return VerifyResult(status="error", error=str(e))

    def get_catalog(self, catalog_id: str, media_type: str, skip: int,
                    config: dict, genre: str | None = None) -> list[dict]:
        from jellyfin_api import JellyfinClient
        client = JellyfinClient(
            base_url=config["jellyfin_url"],
            api_key=config["jellyfin_api_key"],
            user_id=config.get("jellyfin_user_id"),
        )
        if catalog_id == "jellyfin-library":
            libraries = client.get_libraries()
            lib_type = "movies" if media_type == "movie" else "series"
            lib = next((l for l in libraries if l.get("CollectionType") == lib_type), None)
            if not lib:
                return []
            items = client.get_library_items(lib["Id"], include_item_types=lib_type.rstrip("s"))
            return [_to_meta(i) for i in items[skip:skip + 20]]
        return []


def _to_meta(item: dict) -> dict:
    provider_ids = item.get("ProviderIds", {})
    imdb = provider_ids.get("Imdb", "")
    return {
        "id": f"tt{imdb}" if imdb else str(item.get("Id", "")),
        "type": "movie",
        "name": item.get("Name", ""),
        "year": item.get("ProductionYear"),
        "poster": item.get("ImageTags", {}).get("Primary"),
        "description": item.get("Overview"),
        "imdb_rating": item.get("CommunityRating"),
        "imdb_id": imdb,
        "jellyfin_id": item.get("Id"),
    }
