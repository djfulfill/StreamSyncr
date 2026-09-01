"""Sofa Sidekick scrobbler — mark watched on stop."""

import sys
import os
import logging

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "..", "apis"))

from core.addons.base import ScrobbleEvent

logger = logging.getLogger("streamsyncr.addons.sofasidekick.scrobbler")


class SofaSidekickScrobbler:
    async def on_event(self, event: ScrobbleEvent, config: dict) -> dict:
        if not config.get("sofasidekick_session_id") or event.progress < 90 or event.action != "stop":
            return {"skipped": True}

        try:
            from sofasidekick_api import SofaSidekickClient
            client = SofaSidekickClient(
                session_id=config["sofasidekick_session_id"],
                cf_clearance=config.get("sofasidekick_cf_clearance"),
                cf_bm=config.get("sofasidekick_cf_bm"),
            )
            if event.media_type == "movie" and event.imdb_id:
                client.mark_movie_watched(event.imdb_id)
                return {"status": "watched"}
            elif event.media_type == "episode" and event.imdb_id:
                client.mark_episode_watched(event.imdb_id)
                return {"status": "watched"}
            return {"skipped": True, "reason": "no_imdb_id"}
        except Exception as e:
            logger.warning(f"Sofa Sidekick scrobble failed: {e}")
            return {"error": str(e)}
