"""Jellyfin Media Server API client."""

import json
from urllib.request import Request, urlopen
from urllib.parse import urlencode
from typing import Dict, List, Optional


class JellyfinClient:
    def __init__(self, base_url: str, api_key: str, user_id: str = None):
        """
        Args:
            base_url: Jellyfin server URL (e.g. http://192.168.1.10:8096)
            api_key: Jellyfin API key
            user_id: Optional user ID for user-specific operations
        """
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self.user_id = user_id

    def _request(self, method: str, path: str, data: dict = None, params: dict = None) -> dict:
        url = f"{self.base_url}{path}"
        if params:
            url += "?" + urlencode(params)

        body = json.dumps(data).encode() if data else None
        req = Request(url, data=body, method=method)
        req.add_header("X-Emby-Token", self.api_key)
        req.add_header("Content-Type", "application/json")
        req.add_header("Accept", "application/json")

        with urlopen(req) as resp:
            return json.loads(resp.read())

    def _user_request(self, method: str, path: str, data: dict = None, params: dict = None) -> dict:
        """Make a request to a user-specific endpoint."""
        if not self.user_id:
            raise ValueError("user_id is required for this operation")
        return self._request(method, f"/Users/{self.user_id}{path}", data, params)

    # ── Server Info ──

    def get_server_info(self) -> Dict:
        """Get server system info."""
        return self._request("GET", "/System/Info/Public")

    def get_users(self) -> List[Dict]:
        """Get all users on the server."""
        return self._request("GET", "/Users/Public")

    # ── Libraries ──

    def get_libraries(self) -> List[Dict]:
        """Get all media libraries."""
        return self._user_request("GET", "/Views")

    def get_library_items(self, parent_id: str, include_item_types: str = "Movie") -> List[Dict]:
        """Get items in a library."""
        return self._user_request("GET", "/Items", params={
            "ParentId": parent_id,
            "IncludeItemTypes": include_item_types,
            "Recursive": "true",
            "Fields": "ProviderIds,Overview",
        })

    # ── Movies ──

    def get_movie(self, item_id: str) -> Dict:
        """Get movie details."""
        return self._user_request("GET", f"/Items/{item_id}")

    def get_movies(self, limit: int = 50) -> List[Dict]:
        """Get all movies."""
        return self._user_request("GET", "/Items", params={
            "IncludeItemTypes": "Movie",
            "Recursive": "true",
            "Limit": limit,
            "Fields": "ProviderIds",
        })

    # ── TV Shows ──

    def get_show(self, item_id: str) -> Dict:
        """Get TV show details."""
        return self._user_request("GET", f"/Items/{item_id}")

    def get_seasons(self, show_id: str) -> List[Dict]:
        """Get seasons for a show."""
        return self._user_request("GET", f"/Shows/{show_id}/Seasons")

    def get_episodes(self, show_id: str, season_id: str = None) -> List[Dict]:
        """Get episodes for a show or season."""
        params = {}
        if season_id:
            params["SeasonId"] = season_id
        return self._user_request("GET", f"/Shows/{show_id}/Episodes", params=params)

    # ── Watch History ──

    def get_watch_history(self, limit: int = 50) -> List[Dict]:
        """Get the user's watch history."""
        return self._user_request("GET", "/Items/Resume", params={
            "Limit": limit,
            "Recursive": "true",
            "Fields": "ProviderIds",
        })

    def get_recently_played(self, limit: int = 20) -> List[Dict]:
        """Get recently played items."""
        return self._user_request("GET", "/Users/Items/Resume", params={
            "Limit": limit,
            "Recursive": "true",
        })

    def mark_watched(self, item_id: str) -> bool:
        """Mark an item as watched."""
        try:
            self._user_request("POST", f"/Items/{item_id}/Played")
            return True
        except Exception:
            return False

    def mark_unwatched(self, item_id: str) -> bool:
        """Mark an item as unwatched."""
        try:
            self._user_request("POST", f"/Items/{item_id}/Unplayed")
            return True
        except Exception:
            return False

    # ── Ratings ──

    def rate(self, item_id: str, rating: int) -> bool:
        """Rate an item (scale varies by item type)."""
        try:
            self._user_request("POST", f"/Items/{item_id}/Rating", params={"Likes": rating})
            return True
        except Exception:
            return False

    # ── Search ──

    def search(self, query: str, limit: int = 10) -> List[Dict]:
        """Search across all libraries."""
        return self._user_request("GET", "/Search/Items", params={
            "SearchTerm": query,
            "Limit": limit,
            "IncludeItemTypes": "Movie,Series",
        })

    # ── Playback Reporting ──

    def get_playback_stats(self) -> List[Dict]:
        """Get playback statistics (requires Playback Reporting plugin)."""
        return self._user_request("GET", "/Items/Resume", params={
            "Limit": 100,
            "Recursive": "true",
        })

    # ── Sessions ──

    def get_sessions(self) -> List[Dict]:
        """Get active playback sessions."""
        return self._request("GET", "/Sessions")

    # ── Helpers ──

    def get_provider_ids(self, item_id: str) -> Dict:
        """Extract external provider IDs (IMDb, TMDb, TVDB) from an item."""
        item = self.get_movie(item_id)
        return item.get("ProviderIds", {})
