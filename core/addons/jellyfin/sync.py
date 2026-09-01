"""Jellyfin sync source — pull and push watch state."""

import sys
import os
import logging
from typing import Any

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "..", "apis"))

from core.addons.base import CanonicalItem

logger = logging.getLogger("streamsyncr.addons.jellyfin.sync")


class JellyfinSyncSource:
    def pull(self, config: dict) -> list[CanonicalItem]:
        from jellyfin_api import JellyfinClient
        client = JellyfinClient(
            base_url=config["jellyfin_url"],
            api_key=config["jellyfin_api_key"],
            user_id=config.get("jellyfin_user_id"),
        )
        items = []
        try:
            history = client.get_watch_history()
            for entry in history:
                provider_ids = entry.get("ProviderIds", {})
                canonical = CanonicalItem(
                    imdb_id=provider_ids.get("Imdb"),
                    tmdb_id=provider_ids.get("Tmdb"),
                    title=entry.get("Name"),
                    year=entry.get("ProductionYear"),
                    media_type="movie" if entry.get("Type") == "Movie" else "show",
                )
                canonical.service_ids["jellyfin"] = entry.get("Id")
                canonical.service_states["jellyfin"] = {
                    "watched": entry.get("UserData", {}).get("Played", False),
                }
                items.append(canonical)
        except Exception as e:
            logger.warning(f"Jellyfin sync pull failed: {e}")
        return items

    def push_change(self, canonical: CanonicalItem, field: str, value: Any,
                    config: dict) -> None:
        from jellyfin_api import JellyfinClient
        client = JellyfinClient(
            base_url=config["jellyfin_url"],
            api_key=config["jellyfin_api_key"],
            user_id=config.get("jellyfin_user_id"),
        )
        jf_id = canonical.service_ids.get("jellyfin")
        if not jf_id:
            return
        if field == "watched":
            if value:
                client.mark_watched(jf_id)
            else:
                client.mark_unwatched(jf_id)
        elif field == "rating":
            client.rate(jf_id, int(value))

    def supports_field(self, field: str) -> bool:
        return field in ("watched", "rating")
