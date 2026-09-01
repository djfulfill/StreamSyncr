"""Jellyfin exporter — exports recently played and resume state."""

import sys
import os
import logging

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "..", "apis"))

logger = logging.getLogger("streamsyncr.addons.jellyfin.export")


class JellyfinExporter:
    def export(self, config: dict) -> dict:
        from jellyfin_api import JellyfinClient
        client = JellyfinClient(
            base_url=config["jellyfin_url"],
            api_key=config["jellyfin_api_key"],
            user_id=config.get("jellyfin_user_id"),
        )
        data = {}
        try:
            data["recently_played"] = client.get_recently_played()
        except Exception:
            data["recently_played"] = []
        try:
            data["resume"] = client.get_watch_history()
        except Exception:
            data["resume"] = []
        return data
