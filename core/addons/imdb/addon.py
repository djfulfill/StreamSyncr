"""IMDb addon — lists, ratings, recently viewed via GraphQL."""

import sys
import os
from typing import Any

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "..", "apis"))

from core.addons.base import (
    Addon, CatalogDef, VerifyResult,
)
from core.addons.imdb.export import IMDbExporter


class IMDbAddon:
    name = "IMDb"
    slug = "imdb"
    description = "Your IMDb lists, ratings, and recently viewed titles"

    config_schema = {
        "imdb_full_cookies": {"type": "string", "label": "Session Cookies", "secret": True, "required": True},
    }

    config_keys = ["imdb_full_cookies"]

    catalogs = [
        CatalogDef(id="imdb-lists", label="Lists", type="movie|series", auth=True),
        CatalogDef(id="imdb-recently-viewed", label="Recently Viewed", type="movie|series", auth=True),
        CatalogDef(id="imdb-ratings", label="Ratings", type="movie|series", auth=True),
    ]

    exporter = IMDbExporter()

    def is_configured(self, config: dict) -> bool:
        return bool(config.get("imdb_full_cookies"))

    def verify(self, config: dict) -> VerifyResult:
        if not config.get("imdb_full_cookies"):
            return VerifyResult(status="missing_credentials")
        try:
            from imdb_api import IMDbClient
            client = IMDbClient(full_cookies=config["imdb_full_cookies"])
            lists = client.get_lists()
            return VerifyResult(status="ok", details={"lists": len(lists)})
        except Exception as e:
            return VerifyResult(status="error", error=str(e))

    def get_catalog(self, catalog_id: str, media_type: str, skip: int,
                    config: dict, genre: str | None = None) -> list[dict]:
        from imdb_api import IMDbClient
        client = IMDbClient(full_cookies=config.get("imdb_full_cookies", ""))

        if catalog_id == "imdb-recently-viewed":
            items = client.get_recently_viewed(count=skip + 20)
            return [_to_meta(i, "movie") for i in items[skip:skip + 20]]
        elif catalog_id == "imdb-lists":
            lists = client.get_lists()
            result = []
            for lst in lists[skip:skip + 20]:
                list_id = lst.get("id", "")
                name = lst.get("name", {})
                if isinstance(name, dict):
                    name = name.get("originalText", "")
                result.append({
                    "id": f"imdb-list:{list_id}",
                    "type": "movie",
                    "name": f"{name} ({lst.get('items', {}).get('total', 0)} items)",
                })
            return result
        return []


def _to_meta(item: dict, stremio_type: str) -> dict:
    title_id = item.get("id", "")
    title_text = item.get("titleText", {})
    if isinstance(title_text, dict):
        title_text = title_text.get("text", "")
    year = item.get("releaseYear", {})
    if isinstance(year, dict):
        year = year.get("year")
    primary_image = item.get("primaryImage", {})
    poster = primary_image.get("url") if isinstance(primary_image, dict) else None
    return {
        "id": title_id if title_id.startswith("tt") else f"tt{title_id}",
        "type": stremio_type,
        "name": title_text,
        "year": year,
        "poster": poster,
        "imdb_id": title_id,
    }
