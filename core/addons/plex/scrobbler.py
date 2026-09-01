"""Plex scrobbler — mark watched on stop."""

import sys
import os
import logging

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "..", "apis"))

from core.addons.base import ScrobbleEvent

logger = logging.getLogger("streamsyncr.addons.plex.scrobbler")


class PlexScrobbler:
    async def on_event(self, event: ScrobbleEvent, config: dict) -> dict:
        if not config.get("plex_token") or event.progress < 90 or event.action != "stop":
            return {"skipped": True}

        try:
            from plex_api import PlexClient
            client = PlexClient(base_url=config["plex_url"], token=config["plex_token"])
            if event.title:
                results = client.search(event.title, event.media_type)
                if results:
                    rating_key = results[0].get("ratingKey")
                    if rating_key:
                        client.mark_watched(int(rating_key))
                        return {"status": "watched"}
            return {"skipped": True, "reason": "no_match"}
        except Exception as e:
            logger.warning(f"Plex scrobble failed: {e}")
            return {"error": str(e)}
