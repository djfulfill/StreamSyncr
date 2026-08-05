"""
Real-time scrobble orchestration for StreamSyncr.

Receives playback events from Kodi/Stremio via WebSocket,
resolves item IDs across services, and fans out to all
connected platforms (Trakt, WeTrakr, Plex, etc.).
"""

import asyncio
import time
import logging
from dataclasses import dataclass, field
from typing import Optional

from fastapi import WebSocket, WebSocketDisconnect

logger = logging.getLogger("scrobble")

# ── Data Models ─────────────────────────────────────────────


@dataclass
class ScrobbleEvent:
    """Incoming event from a client."""
    action: str  # "start", "pause", "resume", "stop", "heartbeat"
    item_id: str  # IMDb ID (tt...) or TMDB ID
    media_type: str = "movie"  # "movie" or "episode"
    progress: float = 0.0  # 0-100
    title: str = ""
    year: Optional[int] = None
    season: Optional[int] = None
    episode: Optional[int] = None
    client_type: str = "unknown"


@dataclass
class ScrobbleSession:
    """Tracks active playback for a client."""
    token: str
    client_type: str
    item_id: str
    media_type: str
    progress: float
    started_at: float
    last_updated: float
    is_playing: bool = True
    title: str = ""
    year: Optional[int] = None
    season: Optional[int] = None
    episode: Optional[int] = None
    poster: str = ""
    # Resolved IDs
    imdb_id: Optional[str] = None
    tmdb_id: Optional[int] = None
    trakt_id: Optional[int] = None


# ── Scrobble Manager ────────────────────────────────────────


class ScrobbleManager:
    """Manages real-time scrobble state and fan-out."""

    def __init__(self):
        self.active_sessions: dict[str, ScrobbleSession] = {}
        self._ws_connections: dict[str, WebSocket] = {}
        self._lock = asyncio.Lock()
        self._dedup_window = 5.0  # seconds
        self._recent_events: dict[str, float] = {}

    async def connect(self, websocket: WebSocket, token: str):
        """Register a WebSocket client."""
        await websocket.accept()
        async with self._lock:
            self._ws_connections[token] = websocket
            logger.info(f"WebSocket connected: {token[:8]}...")

        # Send current now_playing state to new client
        now_playing = self._build_now_playing_message()
        await websocket.send_json(now_playing)

    async def disconnect(self, token: str):
        """Remove a WebSocket client."""
        async with self._lock:
            self._ws_connections.pop(token, None)
            session = self.active_sessions.pop(token, None)
            if session:
                session.is_playing = False
                await self._fan_out_now_playing()
            logger.info(f"WebSocket disconnected: {token[:8]}...")

    async def handle_event(self, token: str, event: ScrobbleEvent, config_store: dict):
        """Process incoming scrobble event and fan-out."""
        # Dedup check
        dedup_key = f"{token}:{event.action}:{event.item_id}:{event.progress:.0f}"
        now = time.time()
        if dedup_key in self._recent_events:
            if now - self._recent_events[dedup_key] < self._dedup_window:
                return
        self._recent_events[dedup_key] = now

        # Clean old dedup entries
        cutoff = now - self._dedup_window * 2
        self._recent_events = {
            k: v for k, v in self._recent_events.items() if v > cutoff
        }

        # Update or create session
        async with self._lock:
            if event.action == "stop":
                # Remove session on stop
                session = self.active_sessions.pop(token, None)
                if session:
                    session.is_playing = False
                    session.progress = event.progress
            else:
                # Update or create session
                if token in self.active_sessions:
                    session = self.active_sessions[token]
                    session.progress = event.progress
                    session.last_updated = now
                    session.is_playing = event.action != "pause"
                else:
                    session = ScrobbleSession(
                        token=token,
                        client_type=event.client_type,
                        item_id=event.item_id,
                        media_type=event.media_type,
                        progress=event.progress,
                        started_at=now,
                        last_updated=now,
                        is_playing=event.action != "pause",
                        title=event.title,
                        year=event.year,
                        season=event.season,
                        episode=event.episode,
                    )
                    self.active_sessions[token] = session

        # Resolve IDs if needed
        if session and not session.trakt_id:
            await self._resolve_ids(session, config_store.get(token, {}))

        # Fan out to services
        if session:
            await self._push_to_services(session, config_store.get(token, {}), event.action)

        # Broadcast now_playing to all frontend clients
        await self._fan_out_now_playing()

    # ── ID Resolution ────────────────────────────────────────

    async def _resolve_ids(self, session: ScrobbleSession, user_config: dict):
        """Resolve item IDs across all services."""
        if session.item_id.startswith("tt"):
            session.imdb_id = session.item_id
        elif session.item_id.isdigit():
            session.tmdb_id = int(session.item_id)

        # Resolve Trakt ID
        if not session.trakt_id and user_config.get("trakt_token"):
            try:
                from apis.trakt_api.client import TraktClient
                client = TraktClient(
                    api_key=user_config.get("trakt_client_id", ""),
                    token=user_config["trakt_token"],
                )
                if session.imdb_id:
                    results = client.search(session.imdb_id, session.media_type)
                elif session.title:
                    results = client.search(session.title, session.media_type, session.year)
                else:
                    results = []

                if results:
                    item_key = session.media_type if session.media_type in results[0] else "movie"
                    if session.media_type == "episode" and "show" in results[0]:
                        item_key = "show"
                    item_data = results[0].get(item_key, results[0].get("movie", results[0].get("show", {})))
                    session.trakt_id = item_data.get("ids", {}).get("trakt")
            except Exception as e:
                logger.warning(f"Trakt ID resolution failed: {e}")

        # Resolve TMDB ID from IMDb if needed
        if not session.tmdb_id and session.imdb_id:
            try:
                from apis.tmdb_api import TMDBClient
                client = TMDBClient(api_key=user_config.get("tmdb_api_key", ""))
                result = client.find_by_imdb(session.imdb_id)
                if result:
                    session.tmdb_id = result.get("id")
            except Exception as e:
                logger.warning(f"TMDB ID resolution failed: {e}")

    # ── Service Fan-out ──────────────────────────────────────

    async def _push_to_services(self, session: ScrobbleSession, user_config: dict, action: str):
        """Fan-out scrobble event to all configured services."""
        results = {}

        # Trakt (start/pause/stop with progress)
        if user_config.get("trakt_token") and session.trakt_id:
            try:
                from apis.trakt_api.client import TraktClient
                client = TraktClient(
                    api_key=user_config.get("trakt_client_id", ""),
                    token=user_config["trakt_token"],
                )
                if action == "start":
                    results["trakt"] = client.scrobble_start(session.trakt_id, session.media_type)
                elif action == "pause":
                    results["trakt"] = client.scrobble_pause(
                        session.trakt_id, session.media_type, session.progress
                    )
                elif action == "stop":
                    if session.progress >= 90:
                        if session.media_type == "movie":
                            results["trakt"] = client.mark_watched_now(movies=[session.trakt_id])
                        else:
                            results["trakt"] = client.mark_watched_now(shows=[session.trakt_id])
                    else:
                        results["trakt"] = client.scrobble_stop(
                            session.trakt_id, session.media_type, session.progress
                        )
                elif action == "heartbeat":
                    results["trakt"] = client.scrobble_start(session.trakt_id, session.media_type)
            except Exception as e:
                results["trakt"] = {"error": str(e)}
                logger.warning(f"Trakt scrobble failed: {e}")

        # WeTrakr (mark_watched only on stop with >= 90%)
        if action == "stop" and session.progress >= 90 and user_config.get("wetrakr_access_token"):
            try:
                from apis.wetrakr_api.client import WeTrakrClient
                client = WeTrakrClient(
                    access_token=user_config["wetrakr_access_token"],
                    refresh_token=user_config.get("wetrakr_refresh_token", ""),
                )
                # WeTrakr uses internal IDs - search by title
                if session.title:
                    results["wetrakr"] = client.mark_watched(
                        item_id=0,  # Will search by title internally
                        media_type=session.media_type,
                    )
            except Exception as e:
                results["wetrakr"] = {"error": str(e)}
                logger.warning(f"WeTrakr scrobble failed: {e}")

        # Plex (mark_watched on stop)
        if action == "stop" and session.progress >= 90 and user_config.get("plex_token"):
            try:
                from apis.plex_api import PlexClient
                client = PlexClient(
                    base_url=user_config.get("plex_base_url", ""),
                    token=user_config["plex_token"],
                )
                # Search for item by title
                if session.title:
                    search_results = client.search(session.title, session.media_type)
                    if search_results:
                        rating_key = search_results[0].get("ratingKey")
                        if rating_key:
                            results["plex"] = client.mark_watched(int(rating_key))
            except Exception as e:
                results["plex"] = {"error": str(e)}
                logger.warning(f"Plex scrobble failed: {e}")

        # Jellyfin (mark_watched on stop)
        if action == "stop" and session.progress >= 90 and user_config.get("jellyfin_token"):
            try:
                from apis.jellyfin_api import JellyfinClient
                client = JellyfinClient(
                    base_url=user_config.get("jellyfin_base_url", ""),
                    token=user_config["jellyfin_token"],
                )
                # Search for item by title
                if session.title:
                    search_results = client.search(session.title)
                    if search_results:
                        item_id = search_results[0].get("Id")
                        if item_id:
                            results["jellyfin"] = client.mark_watched(item_id)
            except Exception as e:
                results["jellyfin"] = {"error": str(e)}
                logger.warning(f"Jellyfin scrobble failed: {e}")

        # Simkl (add to history on stop)
        if action == "stop" and session.progress >= 90 and user_config.get("simkl_token"):
            try:
                from apis.simkl_api import SimklClient
                client = SimklClient(token=user_config["simkl_token"])
                if session.media_type == "movie" and session.imdb_id:
                    results["simkl"] = client.add_to_history(
                        movies=[{"ids": {"imdb": session.imdb_id}}]
                    )
                elif session.media_type == "episode" and session.imdb_id:
                    results["simkl"] = client.add_to_history(
                        episodes=[{"ids": {"imdb": session.imdb_id}}]
                    )
            except Exception as e:
                results["simkl"] = {"error": str(e)}
                logger.warning(f"Simkl scrobble failed: {e}")

        # Letterboxd (mark_watched on stop, movies only)
        if action == "stop" and session.progress >= 90 and session.media_type == "movie":
            if user_config.get("letterboxd_session"):
                try:
                    from apis.letterboxd_api import LetterboxdClient
                    client = LetterboxdClient(session_id=user_config["letterboxd_session"])
                    if session.imdb_id:
                        # Letterboxd uses its own film_lid - would need lookup
                        pass
                except Exception as e:
                    logger.warning(f"Letterboxd scrobble failed: {e}")

        # Sofa Sidekick (mark_watched on stop)
        if action == "stop" and session.progress >= 90 and user_config.get("sofasidekick_token"):
            try:
                from apis.sofasidekick_api import SofaSidekickClient
                client = SofaSidekickClient(token=user_config["sofasidekick_token"])
                if session.media_type == "movie" and session.imdb_id:
                    results["sofasidekick"] = client.mark_movie_watched(session.imdb_id)
                elif session.media_type == "episode" and session.imdb_id:
                    results["sofasidekick"] = client.mark_episode_watched(session.imdb_id)
            except Exception as e:
                results["sofasidekick"] = {"error": str(e)}
                logger.warning(f"Sofa Sidekick scrobble failed: {e}")

        # AniList (progress update on stop, anime only)
        if action == "stop" and session.media_type == "episode" and user_config.get("anilist_token"):
            if session.progress >= 90:
                try:
                    from apis.anilist_api import AniListClient
                    client = AniListClient(token=user_config["anilist_token"])
                    if session.imdb_id:
                        results["anilist"] = client.save_anime_list_entry(
                            media_id=0,  # Would need AniList media ID
                            status="CURRENT",
                            progress=session.episode or 1,
                        )
                except Exception as e:
                    logger.warning(f"AniList scrobble failed: {e}")

        if results:
            logger.info(f"Scrobble results for {session.title}: {results}")

    # ── Broadcasting ─────────────────────────────────────────

    async def _fan_out_now_playing(self):
        """Broadcast now_playing state to all connected clients."""
        message = self._build_now_playing_message()
        disconnected = []
        for token, ws in self._ws_connections.items():
            try:
                await ws.send_json(message)
            except Exception:
                disconnected.append(token)

        for token in disconnected:
            self._ws_connections.pop(token, None)

    def _build_now_playing_message(self) -> dict:
        """Build now_playing message from active sessions."""
        sessions = []
        for token, session in self.active_sessions.items():
            if session.is_playing:
                sessions.append({
                    "token": token[:8] + "...",
                    "client_type": session.client_type,
                    "title": session.title,
                    "year": session.year,
                    "progress": session.progress,
                    "is_playing": session.is_playing,
                    "media_type": session.media_type,
                    "poster": session.poster,
                    "started_at": session.started_at,
                })
        return {"type": "now_playing", "sessions": sessions}


# ── Global Instance ─────────────────────────────────────────

scrobble_manager = ScrobbleManager()
