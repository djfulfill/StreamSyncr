"""Simkl exporter — exports all items and activities."""

import sys
import os
import logging

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "..", "apis"))

logger = logging.getLogger("streamsyncr.addons.simkl.export")


class SimklExporter:
    def export(self, config: dict) -> dict:
        from simkl_api import SimklClient
        client = SimklClient(
            client_id=config.get("simkl_client_id", ""),
            access_token=config.get("simkl_access_token"),
        )
        data = {}
        try:
            data["all_items"] = client.get_all_items()
        except Exception:
            pass
        try:
            data["activities"] = client.get_activities()
        except Exception:
            pass
        return data
