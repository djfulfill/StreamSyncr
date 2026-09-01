"""MDBList exporter — exports profile and lists."""

import sys
import os
import logging

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "..", "apis"))

logger = logging.getLogger("streamsyncr.addons.mdblist.export")


class MDBListExporter:
    def export(self, config: dict) -> dict:
        from mdblist_api import MDBListClient
        client = MDBListClient(api_key=config.get("mdblist_api_key", ""))
        data = {}
        try:
            data["profile"] = client.user()
        except Exception:
            pass
        try:
            lists = client.my_lists()
            data["lists"] = []
            for lst in lists:
                data["lists"].append({
                    "id": lst.get("id"),
                    "name": lst.get("name"),
                    "item_count": lst.get("items", 0),
                })
        except Exception:
            data["lists"] = []
        return data
