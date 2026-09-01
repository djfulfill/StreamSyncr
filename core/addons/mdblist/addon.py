"""MDBList addon — multi-rating lists and search."""

import sys
import os
from typing import Any

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "..", "apis"))

from core.addons.base import (
    Addon, CatalogDef, VerifyResult,
)
from core.addons.mdblist.export import MDBListExporter


class MDBListAddon:
    name = "MDBList"
    slug = "mdblist"
    description = "Multi-source rating lists and search"

    config_schema = {
        "mdblist_api_key": {"type": "string", "label": "API Key", "secret": True, "required": True},
    }

    config_keys = ["mdblist_api_key"]

    catalogs = [
        CatalogDef(id="mdblist-search", label="Search", type="movie|series", auth=True),
    ]

    exporter = MDBListExporter()

    def is_configured(self, config: dict) -> bool:
        return bool(config.get("mdblist_api_key"))

    def verify(self, config: dict) -> VerifyResult:
        if not config.get("mdblist_api_key"):
            return VerifyResult(status="missing_credentials")
        return VerifyResult(status="ok")

    def get_catalog(self, catalog_id: str, media_type: str, skip: int,
                    config: dict, genre: str | None = None) -> list[dict]:
        from mdblist_api import MDBListClient
        client = MDBListClient(api_key=config.get("mdblist_api_key", ""))

        if catalog_id == "mdblist-search" and genre:
            data = client.search(genre)
            results = data.get("search", [])
            return [_to_meta(i, media_type) for i in results[skip:skip + 20]]
        return []


def _to_meta(item: dict, stremio_type: str) -> dict:
    ids = item.get("ids", {})
    imdb_id = ids.get("imdb") or ids.get("imdbid") or item.get("imdb_id", "")
    if imdb_id and not imdb_id.startswith("tt"):
        imdb_id = f"tt{imdb_id}"
    return {
        "id": imdb_id or str(item.get("id", "")),
        "type": stremio_type,
        "name": item.get("title", ""),
        "year": item.get("release_year") or item.get("year"),
        "imdb_id": imdb_id or None,
    }
