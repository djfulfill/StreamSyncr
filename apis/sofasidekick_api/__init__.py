"""
Sofa Sidekick API client for StreamSyncr.

Private show & movie tracker (TV Time replacement).
Uses TheTVDB for metadata, cookie-based auth.

Usage:
    from sofasidekick_api import SofaSidekickClient
    c = SofaSidekickClient(session_id="...", cf_clearance="...")
    c.get_movies()
    c.get_stats()
    c.search("Breaking Bad")
"""

import requests


class SofaSidekickClient:
    """Client for Sofa Sidekick's undocumented API."""

    BASE = "https://app.sofasidekick.com/api"

    def __init__(self, session_id, cf_clearance=None, cf_bm=None, timeout=10):
        self.timeout = timeout
        self.headers = {
            "accept": "*/*",
            "content-type": "application/json",
            "referer": "https://app.sofasidekick.com/",
            "user-agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/151.0.0.0 Safari/537.36",
        }
        cookies = {"session_id": session_id}
        if cf_clearance:
            cookies["cf_clearance"] = cf_clearance
        if cf_bm:
            cookies["__cf_bm"] = cf_bm
        self.session = requests.Session()
        self.session.headers.update(self.headers)
        self.session.cookies.update(cookies)

    def _get(self, path):
        res = self.session.get(f"{self.BASE}/{path}", timeout=self.timeout)
        res.raise_for_status()
        ct = res.headers.get("content-type", "")
        if "text/html" in ct:
            raise ValueError(f"Cloudflare blocked: /api/{path} returned HTML instead of JSON")
        return res.json()

    def _post(self, path, data=None):
        res = self.session.post(f"{self.BASE}/{path}", json=data or {}, timeout=self.timeout)
        res.raise_for_status()
        return res.json()

    def _patch(self, path, data=None):
        res = self.session.patch(f"{self.BASE}/{path}", json=data or {}, timeout=self.timeout)
        res.raise_for_status()
        return res.json()

    def _delete(self, path):
        res = self.session.delete(f"{self.BASE}/{path}", timeout=self.timeout)
        res.raise_for_status()
        return res.json() if res.text else {}

    # ── Auth ───────────────────────────────────────────────────────────

    def me(self):
        """Get current user profile."""
        return self._get("auth/me")

    # ── Shows ──────────────────────────────────────────────────────────

    def get_shows(self):
        """Get all followed shows with progress."""
        return self._get("shows")

    def get_show(self, show_id):
        """Get details for a single show."""
        return self._get(f"shows/{show_id}")

    def add_show(self, tvdb_id):
        """Follow a show by TVDB ID."""
        return self._post("shows", {"tvdbId": tvdb_id})

    def remove_show(self, show_id):
        """Unfollow a show."""
        return self._delete(f"shows/{show_id}")

    def update_show_status(self, show_id, status):
        """Update show status: watching, finished, on_hold, dropped, want_to_watch."""
        return self._patch(f"shows/{show_id}", {"status": status})

    def mark_episode_watched(self, episode_id):
        """Mark an episode as watched."""
        return self._post(f"episodes/{episode_id}/watch")

    def mark_episode_unwatched(self, episode_id):
        """Mark an episode as unwatched."""
        return self._delete(f"episodes/{episode_id}/watch")

    def get_next_episode(self, show_id):
        """Get the next unwatched episode for a show."""
        show = self.get_show(show_id)
        return show.get("nextEpisode")

    # ── Movies ─────────────────────────────────────────────────────────

    def get_movies(self):
        """Get all movies in library."""
        return self._get("movies")

    def add_movie(self, tvdb_id):
        """Add a movie to library by TVDB ID."""
        return self._post("movies", {"tvdbId": tvdb_id})

    def remove_movie(self, movie_id):
        """Remove a movie from library."""
        return self._delete(f"movies/{movie_id}")

    def mark_movie_watched(self, movie_id):
        """Mark a movie as watched."""
        return self._post(f"movies/{movie_id}/watch")

    def mark_movie_unwatched(self, movie_id):
        """Mark a movie as unwatched."""
        return self._delete(f"movies/{movie_id}/watch")

    # ── Watchlist ──────────────────────────────────────────────────────

    def get_watchlist(self):
        """Get the watchlist."""
        return self._get("watchlist")

    def add_to_watchlist(self, item_type, tvdb_id):
        """Add to watchlist. item_type: 'show' or 'movie'."""
        return self._post("watchlist", {"type": item_type, "tvdbId": tvdb_id})

    def remove_from_watchlist(self, item_type, tvdb_id):
        """Remove from watchlist."""
        return self._delete(f"watchlist/{item_type}/{tvdb_id}")

    # ── Search ─────────────────────────────────────────────────────────

    def search(self, query):
        """Search for shows and movies."""
        return self._get(f"search?q={requests.utils.quote(query)}")

    # ── Stats ──────────────────────────────────────────────────────────

    def get_stats(self):
        """Get user stats (episodes watched, watch time, most watched, etc.)."""
        return self._get("stats")

    # ── Upcoming ───────────────────────────────────────────────────────

    def get_upcoming(self, days=7):
        """Get upcoming episodes for followed shows."""
        return self._get(f"upcoming?days={days}")

    # ── History ────────────────────────────────────────────────────────

    def get_history(self):
        """Get watch history."""
        return self._get("history")

    # ── Settings ───────────────────────────────────────────────────────

    def get_settings(self):
        """Get user settings."""
        return self._get("settings")

    # ── Convenience ────────────────────────────────────────────────────

    def get_library_stats(self):
        """Get formatted library stats."""
        stats = self.get_stats()
        return {
            "episodes_watched": stats["totals"]["episodesWatched"],
            "movies_watched": stats["totals"]["moviesWatched"],
            "watch_time_hours": round(stats["totals"]["watchTimeMinutes"] / 60, 1),
            "rewatches": stats["totals"]["rewatches"],
            "shows_followed": stats["shows"]["followed"],
            "shows_watching": stats["shows"]["watching"],
            "shows_finished": stats["shows"]["finished"],
            "most_watched": stats["shows"]["mostWatched"],
            "busiest_month": stats["time"]["busiestMonth"],
        }

    def get_watched_tvdb_ids(self):
        """Get all TVDB IDs for watched shows and movies."""
        shows = self.get_shows()
        movies = self.get_movies()
        return {
            "shows": [s["show"]["tvdbId"] for s in shows if s.get("watched")],
            "movies": [m["movie"]["tvdbId"] for m in movies if m.get("watched")],
        }
