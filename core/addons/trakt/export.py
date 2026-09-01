"""Trakt exporter — exports all user data from Trakt."""

import sys
import os
import logging
from typing import Any

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "..", "apis"))

logger = logging.getLogger("streamsyncr.addons.trakt.export")


def _safe_fetch(fn, *args, **kwargs):
    try:
        return fn(*args, **kwargs)
    except Exception:
        return []


class TraktExporter:
    """Export implementation for Trakt."""

    def export(self, config: dict) -> dict:
        from trakt_api import TraktClient

        client = TraktClient(
            api_key=config.get("trakt_client_id", ""),
            token=config.get("trakt_token"),
        )
        data = {}

        try:
            data["profile"] = client.me()
        except Exception:
            pass

        data["watched_movies"] = _safe_fetch(client.get_watched_movies, limit=5000)
        data["watched_shows"] = _safe_fetch(client.get_watched_shows, limit=5000)
        data["history_movies"] = _safe_fetch(client.history, "movies", limit=200)
        data["history_shows"] = _safe_fetch(client.history, "shows", limit=200)
        data["ratings_movies"] = _safe_fetch(client.ratings, "movies")
        data["ratings_shows"] = _safe_fetch(client.ratings, "shows")
        data["watchlist_movies"] = _safe_fetch(client.watchlist, "movies")
        data["watchlist_shows"] = _safe_fetch(client.watchlist, "shows")
        data["favorites"] = _safe_fetch(client.get_favorites, limit=5000)
        data["collection_movies"] = _safe_fetch(
            lambda: [i.get("movie", {}) for i in client.collection("movies")]
        )
        data["collection_shows"] = _safe_fetch(
            lambda: [i.get("show", {}) for i in client.collection("shows")]
        )

        # Lists with items
        try:
            lists = client.lists()
            data["lists"] = []
            for lst in lists:
                try:
                    items = client.list_items(lst["ids"]["trakt"])
                    data["lists"].append({
                        "name": lst.get("name"),
                        "item_count": len(items),
                        "items": items[:100],
                    })
                except Exception:
                    data["lists"].append({"name": lst.get("name"), "items": []})
        except Exception:
            data["lists"] = []

        return data
