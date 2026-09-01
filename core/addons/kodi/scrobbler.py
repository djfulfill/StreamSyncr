"""Kodi scrobbler — mark watched on stop."""

import sys
import os
import logging

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "..", "apis"))

from core.addons.base import ScrobbleEvent

logger = logging.getLogger("streamsyncr.addons.kodi.scrobbler")


class KodiScrobbler:
    async def on_event(self, event: ScrobbleEvent, config: dict) -> dict:
        if not config.get("kodi_url") or event.progress < 90 or event.action != "stop":
            return {"skipped": True}

        try:
            from kodi_api import KodiClient
            client = KodiClient(
                base_url=config["kodi_url"],
                username=config.get("kodi_username"),
                password=config.get("kodi_password"),
            )
            if event.media_type == "movie" and event.title:
                results = client.search_movies(event.title)
                if results:
                    kodi_id = results[0].get("movieid")
                    if kodi_id:
                        client.mark_movie_watched(kodi_id)
                        return {"status": "watched"}
            elif event.media_type == "episode" and event.title:
                results = client.search_movies(event.title)
                if results:
                    kodi_id = results[0].get("episodeid")
                    if kodi_id:
                        client.mark_episode_watched(kodi_id)
                        return {"status": "watched"}
            return {"skipped": True, "reason": "no_match"}
        except Exception as e:
            logger.warning(f"Kodi scrobble failed: {e}")
            return {"error": str(e)}
