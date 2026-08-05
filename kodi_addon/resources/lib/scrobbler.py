"""
Scrobbler for the StreamSyncr Kodi addon.

Tracks watch progress and reports it back to the StreamSyncr backend
via WebSocket (real-time) with HTTP POST fallback.
"""

import json
import time
import threading
import xbmcgui
import xbmcaddon
import xbmc


class StreamSyncrScrobbler:
    """
    Monitors Kodi playback and reports progress to StreamSyncr.

    Uses WebSocket for real-time updates with HTTP POST fallback.
    """

    def __init__(self, api):
        self.api = api
        self.imdb_id = None
        self.start_time = None
        self.last_report = 0
        self.report_interval = 30  # Report every 30 seconds
        self._ws = None
        self._ws_thread = None
        self._ws_connected = False
        self._title = ""
        self._year = None
        self._season = None
        self._episode = None

    def _connect_ws(self):
        """Connect to WebSocket endpoint."""
        try:
            import websocket
        except ImportError:
            xbmc.log("[StreamSyncr] websocket-client not available, using HTTP fallback", xbmc.LOGINFO)
            return False

        if self._ws and self._ws.sock:
            return True

        try:
            backend_url = self.api.base_url.replace("http", "ws")
            ws_url = f"{backend_url}/ws/scrobble?token={self.api.config_token}"

            self._ws = websocket.WebSocketApp(
                ws_url,
                on_message=self._on_ws_message,
                on_error=self._on_ws_error,
                on_close=self._on_ws_close,
                on_open=self._on_ws_open,
            )
            self._ws_thread = threading.Thread(target=self._ws.run_forever, daemon=True)
            self._ws_thread.start()
            return True
        except Exception as e:
            xbmc.log(f"[StreamSyncr] WebSocket connect failed: {e}", xbmc.LOGWARNING)
            return False

    def _on_ws_open(self, ws):
        """Called when WebSocket connects."""
        self._ws_connected = True
        xbmc.log("[StreamSyncr] WebSocket connected", xbmc.LOGDEBUG)

    def _on_ws_message(self, ws, message):
        """Handle incoming WebSocket messages."""
        pass  # We don't need to handle server messages for now

    def _on_ws_error(self, ws, error):
        """Handle WebSocket errors."""
        xbmc.log(f"[StreamSyncr] WebSocket error: {error}", xbmc.LOGWARNING)
        self._ws_connected = False

    def _on_ws_close(self, ws, close_status_code, close_msg):
        """Handle WebSocket close."""
        self._ws_connected = False
        xbmc.log("[StreamSyncr] WebSocket closed", xbmc.LOGDEBUG)

    def _send_event(self, action, progress):
        """Send scrobble event via WebSocket or HTTP fallback."""
        event = {
            "action": action,
            "item_id": self.imdb_id,
            "media_type": "episode" if self._season else "movie",
            "progress": progress,
            "client_type": "kodi",
            "title": self._title,
            "year": self._year,
            "season": self._season,
            "episode": self._episode,
        }

        # Try WebSocket first
        if self._ws and self._ws_connected:
            try:
                self._ws.send(json.dumps(event))
                return
            except Exception:
                pass

        # HTTP fallback
        self.api.scrobble(self.imdb_id, progress)

    def start(self, imdb_id, title="", year=None, season=None, episode=None):
        """Mark playback as started."""
        self.imdb_id = imdb_id
        self.start_time = time.time()
        self.last_report = 0
        self._title = title
        self._year = year
        self._season = season
        self._episode = episode

        # Connect WebSocket if not already connected
        if not self._ws_connected:
            self._connect_ws()

        # Report start to backend
        if self.imdb_id:
            self._send_event("start", 0)

    def stop(self):
        """Mark playback as stopped/finished."""
        if self.imdb_id:
            # Calculate progress
            progress = self._get_progress()
            self._send_event("stop", progress)

            # Show notification
            if progress >= 90:
                xbmcgui.Dialog().notification(
                    "StreamSyncr",
                    "Marked as watched",
                    xbmcgui.NOTIFICATION_INFO,
                    2000,
                )
            else:
                xbmcgui.Dialog().notification(
                    "StreamSyncr",
                    f"Progress saved ({progress}%)",
                    xbmcgui.NOTIFICATION_INFO,
                    2000,
                )

        self._reset()

    def pause(self):
        """Mark playback as paused."""
        if self.imdb_id:
            progress = self._get_progress()
            self._send_event("pause", progress)

    def resume(self):
        """Mark playback as resumed."""
        if self.imdb_id:
            progress = self._get_progress()
            self._send_event("resume", progress)

    def heartbeat(self):
        """Report periodic progress (called during playback)."""
        if not self.imdb_id:
            return

        now = time.time()
        if now - self.last_report < self.report_interval:
            return

        progress = self._get_progress()
        self._send_event("heartbeat", progress)
        self.last_report = now

    def _get_progress(self):
        """Calculate current playback progress percentage."""
        if not self.start_time:
            return 0

        # Get current playback time from Kodi
        try:
            player = xbmc.Player()
            if player.isPlaying():
                current_time = player.getTime()
                total_time = player.getTotalTime()
                if total_time > 0:
                    return min(100, int((current_time / total_time) * 100))
        except Exception:
            pass

        # Fallback: estimate based on elapsed time
        elapsed = time.time() - self.start_time
        # Assume ~20 min average movie
        return min(100, int((elapsed / 1200) * 100))

    def _reset(self):
        """Reset scrobbler state."""
        self.imdb_id = None
        self.start_time = None
        self.last_report = 0
        self._title = ""
        self._year = None
        self._season = None
        self._episode = None


# Global scrobbler instance
_scrobbler = None


def get_scrobbler(api):
    """Get or create the global scrobbler instance."""
    global _scrobbler
    if _scrobbler is None:
        _scrobbler = StreamSyncrScrobbler(api)
    return _scrobbler


def scrobble_start(imdb_id, title="", year=None, season=None, episode=None):
    """Quick helper to mark playback start."""
    addon = xbmcaddon.Addon()
    backend_url = addon.getSetting("backend_url") or "http://localhost:7800"
    config_token = addon.getSetting("config_token") or ""

    from resources.lib.api import StreamSyncrAPI
    api = StreamSyncrAPI(backend_url, config_token)

    scrobbler = get_scrobbler(api)
    scrobbler.start(imdb_id, title, year, season, episode)


def scrobble_stop():
    """Quick helper to mark playback stop."""
    if _scrobbler:
        _scrobbler.stop()


def scrobble_pause():
    """Quick helper to mark playback pause."""
    if _scrobbler:
        _scrobbler.pause()


def scrobble_resume():
    """Quick helper to mark playback resume."""
    if _scrobbler:
        _scrobbler.resume()


def scrobble_heartbeat():
    """Quick helper for periodic progress reports."""
    if _scrobbler:
        _scrobbler.heartbeat()


class PlaybackMonitor(xbmc.Monitor):
    """Monitor Kodi playback events for scrobbling."""

    def __init__(self, scrobbler):
        super().__init__()
        self.scrobbler = scrobbler

    def onPlayBackStarted(self):
        """Called when playback starts."""
        pass

    def onPlayBackPaused(self):
        """Called when playback pauses."""
        self.scrobbler.pause()

    def onPlayBackResumed(self):
        """Called when playback resumes."""
        self.scrobbler.resume()

    def onPlayBackStopped(self):
        """Called when playback stops."""
        self.scrobbler.stop()

    def onPlayBackEnded(self):
        """Called when playback ends naturally."""
        self.scrobbler.stop()
