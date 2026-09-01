"""Trakt sync source — pull and push watch state."""

import sys
import os
import logging
from typing import Any

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "..", "apis"))

from core.addons.base import CanonicalItem

logger = logging.getLogger("streamsyncr.addons.trakt.sync")


def _normalize_title(title: str) -> str:
    return title.lower().strip() if title else ""


class TraktSyncSource:
    """Sync implementation for Trakt — pull and push watch state."""

    def pull(self, config: dict) -> list[CanonicalItem]:
        from trakt_api import TraktClient

        client = TraktClient(
            api_key=config.get("trakt_client_id", ""),
            token=config.get("trakt_token"),
        )
        items = []

        # Watched
        try:
            watched = client.history()
            for entry in watched:
                item_data = entry.get("movie") or entry.get("show") or entry.get("episode")
                if not item_data:
                    continue
                ids = item_data.get("ids", {})
                canonical = CanonicalItem(
                    imdb_id=ids.get("imdb"),
                    tmdb_id=ids.get("tmdb"),
                    title=item_data.get("title"),
                    year=item_data.get("year"),
                    media_type="show" if "show" in entry else "movie",
                )
                canonical.service_ids["trakt"] = ids.get("trakt")
                canonical.service_states["trakt"] = {
                    "watched": True,
                    "watched_at": entry.get("watched_at"),
                }
                items.append(canonical)
        except Exception as e:
            logger.warning(f"Trakt pull watched failed: {e}")

        # Ratings
        try:
            ratings = client.ratings()
            for entry in ratings:
                item_data = entry.get("movie") or entry.get("show")
                if not item_data:
                    continue
                ids = item_data.get("ids", {})
                canonical = CanonicalItem(
                    imdb_id=ids.get("imdb"),
                    tmdb_id=ids.get("tmdb"),
                    title=item_data.get("title"),
                    year=item_data.get("year"),
                )
                canonical.service_ids["trakt"] = ids.get("trakt")
                canonical.service_states["trakt"] = {
                    "rating": entry.get("rating"),
                    "rated_at": entry.get("rated_at"),
                }
                items.append(canonical)
        except Exception as e:
            logger.warning(f"Trakt pull ratings failed: {e}")

        return items

    def push_change(self, canonical: CanonicalItem, field: str, value: Any,
                    config: dict) -> None:
        from trakt_api import TraktClient

        client = TraktClient(
            api_key=config.get("trakt_client_id", ""),
            token=config["trakt_token"],
        )
        trakt_id = canonical.service_ids.get("trakt")
        if not trakt_id:
            return

        if field == "watched" and value:
            client.mark_watched_now(
                movies=[trakt_id] if canonical.media_type == "movie" else [],
                shows=[trakt_id] if canonical.media_type == "show" else [],
            )
        elif field == "rating":
            client.rate(int(value), movies=[trakt_id])
        elif field == "favorite":
            if value:
                client.favorite(movies=[trakt_id])
            else:
                client.unfavorite(movies=[trakt_id])

    def supports_field(self, field: str) -> bool:
        return field in ("watched", "rating", "favorite")
