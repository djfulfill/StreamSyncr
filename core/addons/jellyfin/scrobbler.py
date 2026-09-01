"""Jellyfin scrobbler — mark watched on stop."""

import sys
import os
import logging

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "..", "apis"))

from core.addons.base import ScrobbleEvent

logger = logging.getLogger("streamsyncr.addons.jellyfin.scrobbler")


class JellyfinScrobbler:
    async def on_event(self, event: ScrobbleEvent, config: dict) -> dict:
        if not config.get("jellyfin_api_key") or event.progress < 90 or event.action != "stop":
            return {"skipped": True}

        try:
            from jellyfin_api import JellyfinClient
            client = JellyfinClient(
                base_url=config["jellyfin_url"],
                api_key=config["jellyfin_api_key"],
                user_id=config.get("jellyfin_user_id"),
            )
            if event.title:
                results = client.search(event.title)
                if results:
                    item_id = results[0].get("Id")
                    if item_id:
                        client.mark_watched(item_id)
                        return {"status": "watched"}
            return {"skipped": True, "reason": "no_match"}
        except Exception as e:
            logger.warning(f"Jellyfin scrobble failed: {e}")
            return {"error": str(e)}
