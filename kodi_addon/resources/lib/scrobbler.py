"""
Scrobbler for the StreamSyncr Kodi addon.

Tracks watch progress and reports it back to the StreamSyncr backend,
which then syncs it to all connected services (Trakt, IMDb, WeTrakr, etc.).
"""

import time
import xbmcgui
import xbmcaddon
import xbmc


class StreamSyncrScrobbler:
    """
    Monitors Kodi playback and reports progress to StreamSyncr.

    Usage:
        scrobbler = StreamSyncrScrobbler(api)
        scrobbler.start("tt1234567")  # Called when playback starts
        # ... Kodi plays the video ...
        scrobbler.stop()  # Called when playback stops
    """

    def __init__(self, api):
        self.api = api
        self.imdb_id = None
        self.start_time = None
        self.last_report = 0
        self.report_interval = 60  # Report every 60 seconds

    def start(self, imdb_id):
        """Mark playback as started."""
        self.imdb_id = imdb_id
        self.start_time = time.time()
        self.last_report = 0

        # Report start to backend
        if self.imdb_id:
            self.api.scrobble(self.imdb_id, progress=0)

    def stop(self):
        """Mark playback as stopped/finished."""
        if self.imdb_id:
            # Calculate progress
            progress = self._get_progress()
            self.api.scrobble(self.imdb_id, progress=progress)

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

    def heartbeat(self):
        """Report periodic progress (called during playback)."""
        if not self.imdb_id:
            return

        now = time.time()
        if now - self.last_report < self.report_interval:
            return

        progress = self._get_progress()
        self.api.scrobble(self.imdb_id, progress=progress)
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


# Global scrobbler instance
_scrobbler = None


def get_scrobbler(api):
    """Get or create the global scrobbler instance."""
    global _scrobbler
    if _scrobbler is None:
        _scrobbler = StreamSyncrScrobbler(api)
    return _scrobbler


def scrobble_start(imdb_id):
    """Quick helper to mark playback start."""
    addon = xbmcaddon.Addon()
    backend_url = addon.getSetting("backend_url") or "http://localhost:7800"
    config_token = addon.getSetting("config_token") or ""

    from resources.lib.api import StreamSyncrAPI
    api = StreamSyncrAPI(backend_url, config_token)

    scrobbler = get_scrobbler(api)
    scrobbler.start(imdb_id)


def scrobble_stop():
    """Quick helper to mark playback stop."""
    if _scrobbler:
        _scrobbler.stop()


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

    def onPlayBackStopped(self):
        """Called when playback stops."""
        self.scrobbler.stop()

    def onPlayBackEnded(self):
        """Called when playback ends naturally."""
        self.scrobbler.stop()