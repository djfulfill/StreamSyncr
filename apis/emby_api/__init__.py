"""Emby Media Server API client."""

import json
from urllib.request import Request, urlopen
from urllib.parse import urlencode
from typing import Dict, List, Optional


class EmbyClient:
    def __init__(self, base_url: str, api_key: str = None, username: str = None, password: str = None):
        """
        Args:
            base_url: Emby server URL (e.g. http://192.168.1.10:8096)
            api_key: Emby API key (alternative to username/password)
            username: Emby username (for user auth)
            password: Emby password (for user auth)
        """
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self.username = username
        self.password = password
        self._token = None
        self._user_id = None

    def _headers(self) -> Dict:
        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json",
            "X-Emby-Authorization": 'Emby Client="StreamSyncr", Device="Linux", DeviceId="streamsyncr-001", Version="1.0.0"',
        }
        token = self.api_key or self._token
        if token:
            headers["X-Emby-Token"] = token
        return headers

    def _request(self, method: str, path: str, data: dict = None, params: dict = None) -> dict:
        url = f"{self.base_url}/emby{path}"
        if params:
            url += "?" + urlencode(params)

        body = json.dumps(data).encode() if data else None
        req = Request(url, data=body, method=method)
        for k, v in self._headers().items():
            req.add_header(k, v)

        with urlopen(req) as resp:
            return json.loads(resp.read())

    def _user_request(self, method: str, path: str, data: dict = None, params: dict = None) -> dict:
        """Make a request to a user-specific endpoint."""
        if not self._user_id:
            raise ValueError("user_id is required. Call authenticate() first.")
        return self._request(method, f"/Users/{self._user_id}{path}", data, params)

    # ── Authentication ──

    def authenticate(self) -> Dict:
        """Authenticate with username/password and get token + user_id."""
        if not self.username or not self.password:
            raise ValueError("username and password required for authenticate()")
        data = self._request("POST", "/Users/AuthenticateByName", data={
            "Username": self.username,
            "Pw": self.password,
        })
        self._token = data.get("AccessToken")
        self._user_id = data.get("User", {}).get("Id")
        return data

    def get_token(self) -> str:
        """Get the current auth token."""
        if self._token is None and self.api_key is None:
            self.authenticate()
        return self._token or self.api_key

    def get_user_id(self) -> str:
        """Get the current user ID."""
        if self._user_id is None and self.api_key is None:
            self.authenticate()
        return self._user_id

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
        return self._user_request("GET", "/Items/Resume", params={
            "Limit": limit,
            "Recursive": "true",
        })

    def get_item_playback_history(self, item_id: str) -> List[Dict]:
        """Get playback positions for an item."""
        return self._user_request("GET", f"/Items/{item_id}/PlaybackInfo")

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

    def set_favorite(self, item_id: str) -> bool:
        """Mark item as favorite."""
        try:
            self._user_request("POST", f"/Users/{self._user_id}/FavoriteItems/{item_id}")
            return True
        except Exception:
            return False

    def unset_favorite(self, item_id: str) -> bool:
        """Remove item from favorites."""
        try:
            self._user_request("DELETE", f"/Users/{self._user_id}/FavoriteItems/{item_id}")
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

    def report_playback_start(self, item_id: str) -> bool:
        """Report playback start (for scrobbling)."""
        try:
            self._request("POST", "/Sessions/Playing", data={
                "ItemId": item_id,
                "CanSeek": True,
                "IsPaused": False,
            })
            return True
        except Exception:
            return False

    def report_playback_progress(self, item_id: str, position_ticks: int) -> bool:
        """Report playback progress."""
        try:
            self._request("POST", "/Sessions/Playing/Progress", data={
                "ItemId": item_id,
                "PositionTicks": position_ticks,
                "CanSeek": True,
                "IsPaused": False,
            })
            return True
        except Exception:
            return False

    def report_playback_stop(self, item_id: str, position_ticks: int = 0) -> bool:
        """Report playback stopped (marks as watched if near end)."""
        try:
            self._request("POST", "/Sessions/Playing/Stopped", data={
                "ItemId": item_id,
                "PositionTicks": position_ticks,
            })
            return True
        except Exception:
            return False

    # ── Sessions ──

    def get_sessions(self) -> List[Dict]:
        """Get active playback sessions."""
        return self._request("GET", "/Sessions")

    # ── Helpers ──

    def get_provider_ids(self, item_id: str) -> Dict:
        """Extract external provider IDs (IMDb, TMDb, TVDB) from an item."""
        item = self.get_movie(item_id)
        return item.get("ProviderIds", {})

    def get_item_image_url(self, item_id: str, image_type: str = "Primary") -> str:
        """Get image URL for an item."""
        return f"{self.base_url}/emby/Items/{item_id}/Images/{image_type}"
