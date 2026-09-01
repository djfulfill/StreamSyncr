"""AniList addon — anime/manga tracking with GraphQL."""

import sys
import os
from typing import Any

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "..", "apis"))

from core.addons.base import (
    Addon, CatalogDef, CanonicalItem, ScrobbleEvent, VerifyResult,
)
from core.addons.anilist.scrobbler import AniListScrobbler
from core.addons.anilist.export import AniListExporter


class AniListAddon:
    name = "AniList"
    slug = "anilist"
    description = "Track anime and manga across the AniList community"

    config_schema = {
        "anilist_token": {"type": "string", "label": "Access Token", "secret": True},
    }

    config_keys = ["anilist_token"]

    catalogs = [
        CatalogDef(id="anilist-trending", label="Trending", type="series"),
        CatalogDef(id="anilist-popular", label="Popular", type="series"),
    ]

    scrobbler = AniListScrobbler()
    exporter = AniListExporter()

    def is_configured(self, config: dict) -> bool:
        return True  # Public API, no auth required for basic use

    def verify(self, config: dict) -> VerifyResult:
        if not config.get("anilist_token"):
            return VerifyResult(status="ok", details={"mode": "public_only"})
        return VerifyResult(status="ok")

    def get_catalog(self, catalog_id: str, media_type: str, skip: int,
                    config: dict, genre: str | None = None) -> list[dict]:
        from anilist_api import AniListClient
        client = AniListClient()

        if catalog_id == "anilist-trending":
            items = client.get_trending(per_page=20 + skip)
            return [_to_meta(i) for i in items[skip:skip + 20]]
        elif catalog_id == "anilist-popular":
            items = client.get_popular(per_page=20 + skip)
            return [_to_meta(i) for i in items[skip:skip + 20]]
        return []


def _to_meta(item: dict) -> dict:
    title = item.get("title", {})
    cover = item.get("coverImage", {})
    start_date = item.get("startDate", {})
    return {
        "id": f"anilist:{item.get('id', '')}",
        "type": "series",
        "name": title.get("english") or title.get("romaji") or title.get("native", ""),
        "year": start_date.get("year"),
        "poster": cover.get("large") or cover.get("medium"),
        "description": item.get("description"),
        "imdb_rating": item.get("averageScore"),
        "genres": item.get("genres", []),
        "anime_id": item.get("id"),
        "status": item.get("status"),
        "episodes": item.get("episodes"),
    }
