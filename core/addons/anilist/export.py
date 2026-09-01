"""AniList exporter — exports anime/manga lists by status."""

import sys
import os
import logging

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "..", "apis"))

logger = logging.getLogger("streamsyncr.addons.anilist.export")


def _safe_fetch(fn, *args, **kwargs):
    try:
        return fn(*args, **kwargs)
    except Exception:
        return []


class AniListExporter:
    def export(self, config: dict) -> dict:
        from anilist_api import AniListClient
        client = AniListClient(token=config.get("anilist_token"))
        data = {}
        try:
            data["profile"] = client.get_viewer()
        except Exception:
            pass
        statuses = ["CURRENT", "COMPLETED", "PLANNED", "DROPPED", "PAUSED", "REPEATING"]
        data["anime"] = {}
        for status in statuses:
            items = _safe_fetch(client.get_user_anime_list, None, status)
            if items:
                data["anime"][status] = items
        data["manga"] = {}
        for status in statuses:
            items = _safe_fetch(client.get_user_manga_list, None, status)
            if items:
                data["manga"][status] = items
        return data
