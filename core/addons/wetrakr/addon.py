"""WeTrakr addon — unofficial tracking with lists and favorites."""

import sys
import os
from typing import Any

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "..", "apis"))

from core.addons.base import (
    Addon, CatalogDef, CanonicalItem, ScrobbleEvent, VerifyResult,
)
from core.addons.wetrakr.scrobbler import WeTrakrScrobbler
from core.addons.wetrakr.sync import WeTrakrSyncSource
from core.addons.wetrakr.export import WeTrakrExporter


class WeTrakrAddon:
    name = "WeTrakr"
    slug = "wetrakr"
    description = "Track your favorites and watchlists"

    config_schema = {
        "wetrakr_access_token": {"type": "string", "label": "Access Token", "secret": True, "required": True},
        "wetrakr_refresh_token": {"type": "string", "label": "Refresh Token", "secret": True},
        "wetrakr_username": {"type": "string", "label": "Username", "required": True},
    }

    config_keys = ["wetrakr_access_token", "wetrakr_refresh_token", "wetrakr_username"]

    _LIST_MAP = {"favorites": 19879, "watchlist": 19876}

    catalogs = [
        CatalogDef(id="wetrakr-favorites", label="Favorites", type="movie|series", auth=True),
        CatalogDef(id="wetrakr-watchlist", label="Watchlist", type="movie|series", auth=True),
        CatalogDef(id="wetrakr-watching", label="Watching", type="movie|series", auth=True),
        CatalogDef(id="wetrakr-ratings", label="Ratings", type="movie|series", auth=True),
    ]

    scrobbler = WeTrakrScrobbler()
    sync_source = WeTrakrSyncSource()
    exporter = WeTrakrExporter()

    def is_configured(self, config: dict) -> bool:
        return bool(config.get("wetrakr_access_token"))

    def verify(self, config: dict) -> VerifyResult:
        if not config.get("wetrakr_access_token"):
            return VerifyResult(status="missing_credentials")
        try:
            from wetrakr_api.client import WeTrakrClient
            client = WeTrakrClient(
                access_token=config["wetrakr_access_token"],
                refresh_token=config.get("wetrakr_refresh_token", ""),
                username=config.get("wetrakr_username", ""),
            )
            client.get_user()
            return VerifyResult(status="ok")
        except Exception as e:
            return VerifyResult(status="error", error=str(e))

    def get_catalog(self, catalog_id: str, media_type: str, skip: int,
                    config: dict, genre: str | None = None) -> list[dict]:
        from wetrakr_api.client import WeTrakrClient
        client = WeTrakrClient(
            access_token=config["wetrakr_access_token"],
            refresh_token=config.get("wetrakr_refresh_token", ""),
            username=config.get("wetrakr_username", ""),
        )

        catalog_list = catalog_id.replace("wetrakr-", "")
        list_id = self._LIST_MAP.get(catalog_list)
        if not list_id:
            return []

        page = (skip // 20) + 1
        items = client.get_list_items(list_id, page=page, limit=20)
        offset = skip % 20
        return [_to_meta(i, media_type) for i in items[offset:offset + 20]]


def _to_meta(item: dict, media_type: str) -> dict:
    ids = item.get("ids", {})
    tmdb = ids.get("tmdb", {})
    tmdb_id = tmdb.get("id") if isinstance(tmdb, dict) else tmdb
    return {
        "id": f"tmdb:{tmdb_id}" if tmdb_id else str(item.get("id", "")),
        "type": media_type,
        "name": item.get("title") or item.get("name", ""),
        "year": item.get("year"),
        "poster": item.get("poster"),
        "background": item.get("fanart"),
        "description": item.get("overview"),
        "imdb_rating": item.get("rating"),
        "tmdb_id": tmdb_id,
    }
