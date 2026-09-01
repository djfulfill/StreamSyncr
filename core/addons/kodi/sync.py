"""Kodi sync source — pull and push watch state."""

import sys
import os
import logging
from typing import Any

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "..", "apis"))

from core.addons.base import CanonicalItem

logger = logging.getLogger("streamsyncr.addons.kodi.sync")


class KodiSyncSource:
    def pull(self, config: dict) -> list[CanonicalItem]:
        from kodi_api import KodiClient
        client = KodiClient(
            base_url=config["kodi_url"],
            username=config.get("kodi_username"),
            password=config.get("kodi_password"),
        )
        items = []
        try:
            properties = ["title", "year", "imdbnumber", "rating", "playcount"]
            movies = client.get_movies(properties)
            for m in movies:
                canonical = CanonicalItem(
                    imdb_id=m.get("imdbnumber"),
                    title=m.get("title"),
                    year=m.get("year"),
                    media_type="movie",
                )
                canonical.service_ids["kodi"] = m.get("movieid")
                canonical.service_states["kodi"] = {
                    "watched": m.get("playcount", 0) > 0,
                    "rating": m.get("rating"),
                }
                items.append(canonical)
        except Exception as e:
            logger.warning(f"Kodi sync pull movies failed: {e}")
        try:
            properties = ["title", "year", "imdbnumber", "rating", "playcount"]
            episodes = client.get_episodes(properties)
            for ep in episodes:
                canonical = CanonicalItem(
                    imdb_id=ep.get("imdbnumber"),
                    title=ep.get("title"),
                    year=ep.get("year"),
                    media_type="show",
                )
                canonical.service_ids["kodi"] = ep.get("episodeid")
                canonical.service_states["kodi"] = {
                    "watched": ep.get("playcount", 0) > 0,
                    "rating": ep.get("rating"),
                }
                items.append(canonical)
        except Exception as e:
            logger.warning(f"Kodi sync pull episodes failed: {e}")
        return items

    def push_change(self, canonical: CanonicalItem, field: str, value: Any,
                    config: dict) -> None:
        from kodi_api import KodiClient
        client = KodiClient(
            base_url=config["kodi_url"],
            username=config.get("kodi_username"),
            password=config.get("kodi_password"),
        )
        kodi_id = canonical.service_ids.get("kodi")
        if not kodi_id:
            return
        if field == "watched":
            if canonical.media_type == "movie":
                if value:
                    client.mark_movie_watched(kodi_id)
                else:
                    client.mark_movie_unwatched(kodi_id)
            else:
                if value:
                    client.mark_episode_watched(kodi_id)
                else:
                    client.mark_episode_unwatched(kodi_id)

    def supports_field(self, field: str) -> bool:
        return field == "watched"
