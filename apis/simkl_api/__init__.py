"""Simkl API client — TV, movie, and anime tracking."""

import json
from urllib.request import Request, urlopen
from urllib.parse import urlencode
from typing import Dict, List, Optional


class SimklClient:
    BASE = "https://api.simkl.com"

    def __init__(self, client_id: str, access_token: str = None):
        self.client_id = client_id
        self.access_token = access_token

    def _request(self, method: str, path: str, data: dict = None, params: dict = None) -> dict:
        url = f"{self.BASE}{path}"
        if params:
            url += "?" + urlencode(params)

        body = json.dumps(data).encode() if data else None
        req = Request(url, data=body, method=method)
        req.add_header("Content-Type", "application/json")
        req.add_header("simkl-api-key", self.client_id)
        req.add_header("User-Agent", "StreamSyncr/1.0")
        if self.access_token:
            req.add_header("Authorization", f"Bearer {self.access_token}")

        with urlopen(req) as resp:
            return json.loads(resp.read())

    # ── Search ──

    def search(self, query: str, media_type: str = "movie") -> List[Dict]:
        """Search for movies, shows, or anime."""
        params = {"q": query, "type": media_type}
        return self._request("GET", "/search", params=params)

    def get_movie(self, simkl_id: int) -> Dict:
        """Get movie details."""
        return self._request("GET", f"/movies/{simkl_id}")

    def get_show(self, simkl_id: int) -> Dict:
        """Get TV show details."""
        return self._request("GET", f"/tv/{simkl_id}")

    def get_anime(self, simkl_id: int) -> Dict:
        """Get anime details."""
        return self._request("GET", f"/anime/{simkl_id}")

    def redirect(self, external_id: str, id_type: str = "imdb") -> Dict:
        """Redirect from external ID (imdb, tmdb, tvdb) to Simkl ID."""
        return self._request("GET", f"/redirect/{id_type}/{external_id}")

    # ── Trending / Popular ──

    def trending_movies(self, period: str = "week") -> List[Dict]:
        """Get trending movies (day/week/month/year)."""
        return self._request("GET", f"/movies/trending/{period}")

    def trending_shows(self, period: str = "week") -> List[Dict]:
        """Get trending TV shows."""
        return self._request("GET", f"/tv/trending/{period}")

    def trending_anime(self, period: str = "week") -> List[Dict]:
        """Get trending anime."""
        return self._request("GET", f"/anime/trending/{period}")

    def popular_movies(self) -> List[Dict]:
        """Get popular movies."""
        return self._request("GET", "/movies/popular")

    def popular_shows(self) -> List[Dict]:
        """Get popular TV shows."""
        return self._request("GET", "/tv/popular")

    def popular_anime(self) -> List[Dict]:
        """Get popular anime."""
        return self._request("GET", "/anime/popular")

    # ── Sync (auth required) ──

    def get_activities(self) -> Dict:
        """Get sync activity timestamps for incremental sync."""
        return self._request("GET", "/sync/activities")

    def get_all_items(self, list_type: str = None) -> Dict:
        """Get all items in lists."""
        params = {}
        if list_type:
            params["type"] = list_type
        return self._request("GET", "/sync/all-items", params=params)

    def add_to_history(self, movies: List[Dict] = None, shows: List[Dict] = None, episodes: List[Dict] = None) -> Dict:
        """Add items to watch history."""
        data = {}
        if movies:
            data["movies"] = movies
        if shows:
            data["shows"] = shows
        if episodes:
            data["episodes"] = episodes
        return self._request("POST", "/sync/history", data=data)

    def remove_from_history(self, movies: List[Dict] = None, shows: List[Dict] = None) -> Dict:
        """Remove items from watch history."""
        data = {}
        if movies:
            data["movies"] = movies
        if shows:
            data["shows"] = shows
        return self._request("POST", "/sync/history/remove", data=data)

    def add_to_list(self, list_name: str, movies: List[Dict] = None, shows: List[Dict] = None) -> Dict:
        """Add items to a watchlist (watching, plantowatch, hold, dropped, completed)."""
        data = {"to": list_name}
        if movies:
            data["movies"] = movies
        if shows:
            data["shows"] = shows
        return self._request("POST", "/sync/add-to-list", data=data)

    def add_ratings(self, movies: List[Dict] = None, shows: List[Dict] = None, episodes: List[Dict] = None) -> Dict:
        """Add/update ratings (1-10 scale)."""
        data = {}
        if movies:
            data["movies"] = movies
        if shows:
            data["shows"] = shows
        if episodes:
            data["episodes"] = episodes
        return self._request("POST", "/sync/ratings", data=data)

    def remove_ratings(self, movies: List[Dict] = None, shows: List[Dict] = None) -> Dict:
        """Remove ratings."""
        data = {}
        if movies:
            data["movies"] = movies
        if shows:
            data["shows"] = shows
        return self._request("POST", "/sync/ratings/remove", data=data)

    # ── Calendars ──

    def calendar(self, from_date: str, days: int = 7, media_type: str = "shows") -> List[Dict]:
        """Get calendar entries (from_date format: YYYY-MM-DD)."""
        return self._request("GET", f"/calendars/{media_type}/days/{from_date}/{days}")

    # ── Helpers ──

    @staticmethod
    def make_item(simkl_id: int) -> Dict:
        """Create an item dict for Simkl API calls."""
        return {"ids": {"simkl": simkl_id}}

    @staticmethod
    def make_rated_item(simkl_id: int, rating: int) -> Dict:
        """Create a rated item dict."""
        return {"ids": {"simkl": simkl_id}, "rating": rating}
