"""AniList scrobbler — progress update on stop."""

import sys
import os
import logging

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "..", "apis"))

from core.addons.base import ScrobbleEvent

logger = logging.getLogger("streamsyncr.addons.anilist.scrobbler")


class AniListScrobbler:
    async def on_event(self, event: ScrobbleEvent, config: dict) -> dict:
        if not config.get("anilist_token") or event.progress < 90 or event.action != "stop":
            return {"skipped": True}
        if event.media_type != "episode":
            return {"skipped": True, "reason": "not_episode"}

        try:
            from anilist_api import AniListClient
            client = AniListClient(token=config["anilist_token"])
            if event.imdb_id:
                client.save_anime_list_entry(
                    media_id=0,
                    status="CURRENT",
                    progress=event.episode or 1,
                )
                return {"status": "updated"}
            return {"skipped": True, "reason": "no_anilist_id"}
        except Exception as e:
            logger.warning(f"AniList scrobble failed: {e}")
            return {"error": str(e)}
