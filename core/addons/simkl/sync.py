"""Simkl sync source — pull and push watch state."""

import sys
import os
import logging
from typing import Any

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "..", "apis"))

from core.addons.base import CanonicalItem

logger = logging.getLogger("streamsyncr.addons.simkl.sync")


class SimklSyncSource:
    def pull(self, config: dict) -> list[CanonicalItem]:
        from simkl_api import SimklClient
        client = SimklClient(client_id=config.get("simkl_client_id", ""))
        if config.get("simkl_access_token"):
            client.access_token = config["simkl_access_token"]
        items = []
        try:
            data = client.get_all_items()
            for key in ("movies", "shows", "anime"):
                for entry in data.get(key, []):
                    ids = entry.get("ids", {})
                    canonical = CanonicalItem(
                        imdb_id=ids.get("imdb"),
                        tmdb_id=ids.get("tmdb"),
                        title=entry.get("title"),
                        year=entry.get("year"),
                        media_type="movie" if key == "movies" else "show",
                    )
                    canonical.service_ids["simkl"] = ids.get("simkl")
                    canonical.service_states["simkl"] = {"watched": True}
                    items.append(canonical)
        except Exception as e:
            logger.warning(f"Simkl sync pull failed: {e}")
        return items

    def push_change(self, canonical: CanonicalItem, field: str, value: Any,
                    config: dict) -> None:
        from simkl_api import SimklClient
        client = SimklClient(
            client_id=config.get("simkl_client_id", ""),
            access_token=config.get("simkl_access_token"),
        )
        simkl_id = canonical.service_ids.get("simkl")
        if not simkl_id:
            return
        if field == "watched" and value:
            client.add_to_history(items=[client.make_item(simkl_id)])

    def supports_field(self, field: str) -> bool:
        return field == "watched"
