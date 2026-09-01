"""WeTrakr exporter — exports profile, lists, and stats."""

import sys
import os
import logging

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "..", "apis"))

logger = logging.getLogger("streamsyncr.addons.wetrakr.export")


def _safe_fetch(fn, *args, **kwargs):
    try:
        return fn(*args, **kwargs)
    except Exception:
        return []


class WeTrakrExporter:
    def export(self, config: dict) -> dict:
        from wetrakr_api.client import WeTrakrClient
        client = WeTrakrClient(
            access_token=config["wetrakr_access_token"],
            refresh_token=config.get("wetrakr_refresh_token", ""),
            username=config.get("wetrakr_username", ""),
        )
        data = {}
        try:
            data["profile"] = client.get_user()
        except Exception:
            pass
        try:
            lists = client.get_lists()
            data["lists"] = []
            for lst in lists[:20]:
                list_id = lst.get("id") or lst.get("list_id")
                if list_id:
                    items = _safe_fetch(client.get_list_items, list_id)
                    data["lists"].append({
                        "name": lst.get("name") or lst.get("title"),
                        "id": list_id,
                        "item_count": len(items),
                        "items": items,
                    })
        except Exception:
            data["lists"] = []
        try:
            data["stats"] = client.get_my_progress()
        except Exception:
            pass
        return data
