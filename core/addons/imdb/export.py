"""IMDb exporter — exports lists and recently viewed."""

import sys
import os
import logging

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "..", "apis"))

logger = logging.getLogger("streamsyncr.addons.imdb.export")


class IMDbExporter:
    def export(self, config: dict) -> dict:
        from imdb_api import IMDbClient
        client = IMDbClient(full_cookies=config.get("imdb_full_cookies", ""))
        data = {}
        try:
            lists = client.get_lists()
            data["lists"] = []
            for lst in lists:
                data["lists"].append({
                    "id": lst.get("id"),
                    "name": lst.get("name", {}).get("originalText", ""),
                    "item_count": lst.get("items", {}).get("total", 0),
                })
        except Exception:
            data["lists"] = []
        try:
            data["recently_viewed"] = client.get_recently_viewed(count=50)
        except Exception:
            data["recently_viewed"] = []
        return data
