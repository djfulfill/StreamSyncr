"""WeTrakr scrobbler — mark watched on stop."""

import sys
import os
import logging

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "..", "apis"))

from core.addons.base import ScrobbleEvent

logger = logging.getLogger("streamsyncr.addons.wetrakr.scrobbler")


class WeTrakrScrobbler:
    async def on_event(self, event: ScrobbleEvent, config: dict) -> dict:
        if not config.get("wetrakr_access_token") or event.progress < 90 or event.action != "stop":
            return {"skipped": True}

        try:
            from wetrakr_api.client import WeTrakrClient
            client = WeTrakrClient(
                access_token=config["wetrakr_access_token"],
                refresh_token=config.get("wetrakr_refresh_token", ""),
            )
            if event.title:
                client.mark_watched(item_id=0, media_type=event.media_type)
                return {"status": "watched"}
            return {"skipped": True, "reason": "no_title"}
        except Exception as e:
            logger.warning(f"WeTrakr scrobble failed: {e}")
            return {"error": str(e)}
