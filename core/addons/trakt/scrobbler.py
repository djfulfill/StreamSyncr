"""Trakt scrobbler — handles real-time playback events."""

import sys
import os
import logging
from typing import Any

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "..", "apis"))

from core.addons.base import ScrobbleEvent

logger = logging.getLogger("streamsyncr.addons.trakt.scrobbler")


class TraktScrobbler:
    """Scrobbler implementation for Trakt."""

    async def on_event(self, event: ScrobbleEvent, config: dict) -> dict:
        """Handle a scrobble event."""
        from trakt_api import TraktClient

        if not config.get("trakt_token") or not event.trakt_id:
            return {"skipped": True, "reason": "no_token_or_no_trakt_id"}

        client = TraktClient(
            api_key=config.get("trakt_client_id", ""),
            token=config["trakt_token"],
        )

        try:
            if event.action == "start":
                result = client.scrobble_start(event.trakt_id, event.media_type)
            elif event.action == "pause":
                result = client.scrobble_pause(
                    event.trakt_id, event.media_type, event.progress
                )
            elif event.action == "stop":
                if event.progress >= 90:
                    if event.media_type == "movie":
                        result = client.mark_watched_now(movies=[event.trakt_id])
                    else:
                        result = client.mark_watched_now(shows=[event.trakt_id])
                else:
                    result = client.scrobble_stop(
                        event.trakt_id, event.media_type, event.progress
                    )
            elif event.action == "heartbeat":
                result = client.scrobble_start(event.trakt_id, event.media_type)
            else:
                return {"skipped": True, "reason": f"unknown_action:{event.action}"}

            return result
        except Exception as e:
            logger.warning(f"Trakt scrobble failed: {e}")
            return {"error": str(e)}
