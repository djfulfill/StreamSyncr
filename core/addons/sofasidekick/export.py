"""Sofa Sidekick exporter — exports profile, movies, stats, upcoming."""

import sys
import os
import logging

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "..", "apis"))

logger = logging.getLogger("streamsyncr.addons.sofasidekick.export")


class SofaSidekickExporter:
    def export(self, config: dict) -> dict:
        from sofasidekick_api import SofaSidekickClient
        client = SofaSidekickClient(
            session_id=config["sofasidekick_session_id"],
            cf_clearance=config.get("sofasidekick_cf_clearance"),
            cf_bm=config.get("sofasidekick_cf_bm"),
        )
        data = {}
        try:
            data["profile"] = client.me()
        except Exception:
            pass
        try:
            data["movies"] = client.get_movies()
        except Exception:
            data["movies"] = []
        try:
            data["stats"] = client.get_stats()
        except Exception:
            pass
        try:
            data["upcoming"] = client.get_upcoming()
        except Exception:
            data["upcoming"] = []
        return data
