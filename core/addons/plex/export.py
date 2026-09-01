"""Plex exporter — exports libraries, watch history, and ratings."""

import sys
import os
import logging

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "..", "apis"))

logger = logging.getLogger("streamsyncr.addons.plex.export")


def _safe_fetch(fn, *args, **kwargs):
    try:
        return fn(*args, **kwargs)
    except Exception:
        return []


class PlexExporter:
    def export(self, config: dict) -> dict:
        from plex_api import PlexClient
        client = PlexClient(base_url=config["plex_url"], token=config["plex_token"])
        data = {}

        try:
            data["libraries"] = client.get_libraries()
        except Exception:
            data["libraries"] = []

        data["watch_history"] = _safe_fetch(client.get_watch_history)
        data["ratings"] = []
        try:
            sections = client.get_libraries()
            for section in sections[:10]:
                lib_id = section.get("key")
                if lib_id:
                    data["ratings"].extend(_safe_fetch(client.get_user_ratings, lib_id))
        except Exception:
            pass

        return data
