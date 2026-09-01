"""Plex sync source — pull and push watch state."""

import sys
import os
import logging
from typing import Any

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "..", "apis"))

from core.addons.base import CanonicalItem

logger = logging.getLogger("streamsyncr.addons.plex.sync")


class PlexSyncSource:
    def pull(self, config: dict) -> list[CanonicalItem]:
        from plex_api import PlexClient
        client = PlexClient(base_url=config["plex_url"], token=config["plex_token"])
        items = []
        try:
            history = client.get_watch_history()
            for entry in history:
                guids = entry.get("Guids", [])
                imdb_id = next((g["id"].replace("imdb://", "") for g in guids
                              if g.get("id", "").startswith("imdb://")), None)
                tmdb_id = next((g["id"].replace("tmdb://", "") for g in guids
                               if g.get("id", "").startswith("tmdb://")), None)
                canonical = CanonicalItem(
                    imdb_id=imdb_id,
                    tmdb_id=tmdb_id,
                    title=entry.get("title"),
                    year=entry.get("year"),
                    media_type="movie" if entry.get("type") == "movie" else "show",
                )
                canonical.service_ids["plex"] = entry.get("ratingKey")
                canonical.service_states["plex"] = {
                    "watched": entry.get("viewCount", 0) > 0,
                }
                items.append(canonical)
        except Exception as e:
            logger.warning(f"Plex sync pull failed: {e}")
        return items

    def push_change(self, canonical: CanonicalItem, field: str, value: Any,
                    config: dict) -> None:
        from plex_api import PlexClient
        client = PlexClient(base_url=config["plex_url"], token=config["plex_token"])
        plex_key = canonical.service_ids.get("plex")
        if not plex_key:
            return
        if field == "watched":
            if value:
                client.mark_watched(plex_key)
            else:
                client.mark_unwatched(plex_key)
        elif field == "rating":
            client.rate(plex_key, int(value))

    def supports_field(self, field: str) -> bool:
        return field in ("watched", "rating")
