"""Simkl scrobbler — add to history on stop."""

import sys
import os
import logging

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "..", "apis"))

from core.addons.base import ScrobbleEvent

logger = logging.getLogger("streamsyncr.addons.simkl.scrobbler")


class SimklScrobbler:
    async def on_event(self, event: ScrobbleEvent, config: dict) -> dict:
        if not config.get("simkl_access_token") or event.progress < 90 or event.action != "stop":
            return {"skipped": True}
        if not event.imdb_id:
            return {"skipped": True, "reason": "no_imdb_id"}

        try:
            from simkl_api import SimklClient
            client = SimklClient(
                client_id=config["simkl_client_id"],
                access_token=config["simkl_access_token"],
            )
            if event.media_type == "movie":
                result = client.add_to_history(movies=[{"ids": {"imdb": event.imdb_id}}])
            else:
                result = client.add_to_history(episodes=[{"ids": {"imdb": event.imdb_id}}])
            return result
        except Exception as e:
            logger.warning(f"Simkl scrobble failed: {e}")
            return {"error": str(e)}
