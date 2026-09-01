"""WeTrakr sync source — pull tracking data."""

import sys
import os
import logging
from typing import Any

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "..", "apis"))

from core.addons.base import CanonicalItem

logger = logging.getLogger("streamsyncr.addons.wetrakr.sync")


class WeTrakrSyncSource:
    def pull(self, config: dict) -> list[CanonicalItem]:
        from wetrakr_api.client import WeTrakrClient
        client = WeTrakrClient(
            access_token=config["wetrakr_access_token"],
            refresh_token=config.get("wetrakr_refresh_token", ""),
            username=config.get("wetrakr_username", ""),
        )
        items = []
        try:
            tracking = client._get("account/tracking")
            for entry in tracking.get("movies", []):
                canonical = CanonicalItem(
                    tmdb_id=entry.get("ids", {}).get("tmdb", {}).get("id"),
                    title=entry.get("title"),
                    year=entry.get("year"),
                    media_type="movie",
                )
                canonical.service_ids["wetrakr"] = entry.get("id")
                canonical.service_states["wetrakr"] = {"watched": True}
                items.append(canonical)
        except Exception as e:
            logger.warning(f"WeTrakr sync pull failed: {e}")
        return items

    def push_change(self, canonical: CanonicalItem, field: str, value: Any,
                    config: dict) -> None:
        from wetrakr_api.client import WeTrakrClient
        client = WeTrakrClient(
            access_token=config["wetrakr_access_token"],
            refresh_token=config.get("wetrakr_refresh_token", ""),
        )
        wetrakr_id = canonical.service_ids.get("wetrakr")
        if not wetrakr_id:
            return
        if field == "watched" and value:
            client.mark_watched(wetrakr_id, canonical.media_type)
        elif field == "favorite":
            if value:
                client.favorite(wetrakr_id, canonical.media_type)

    def supports_field(self, field: str) -> bool:
        return field in ("watched", "favorite")
