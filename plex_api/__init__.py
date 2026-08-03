"""Plex Media Server API client."""

import json
from urllib.request import Request, urlopen
from urllib.parse import urlencode
from typing import Dict, List, Optional


class PlexClient:
    def __init__(self, base_url: str, token: str):
        """
        Args:
            base_url: Plex server URL (e.g. http://192.168.1.10:32400)
            token: Plex authentication token
        """
        self.base_url = base_url.rstrip("/")
        self.token = token

    def _request(self, method: str, path: str, params: dict = None, headers: dict = None) -> dict:
        url = f"{self.base_url}{path}"
        if params:
            params["X-Plex-Token"] = self.token
            url += "?" + urlencode(params)
        else:
            url += "?" + urlencode({"X-Plex-Token": self.token})

        req = Request(url, method=method)
        req.add_header("Accept", "application/json")
        if headers:
            for k, v in headers.items():
                req.add_header(k, v)

        with urlopen(req) as resp:
            return json.loads(resp.read())

    def get_libraries(self) -> List[Dict]:
        """Get all libraries on the server."""
        data = self._request("GET", "/library/sections")
        return data.get("MediaContainer", {}).get("Directory", [])

    def get_library_items(self, library_id: int, libtype: str = "movie") -> List[Dict]:
        """Get all items in a library."""
        data = self._request("GET", f"/library/sections/{library_id}/all", {"type": libtype})
        return data.get("MediaContainer", {}).get("Metadata", [])

    def get_movie(self, rating_key: int) -> Dict:
        """Get movie details."""
        data = self._request("GET", f"/library/metadata/{rating_key}")
        items = data.get("MediaContainer", {}).get("Metadata", [])
        return items[0] if items else {}

    def get_show(self, rating_key: int) -> Dict:
        """Get TV show details."""
        data = self._request("GET", f"/library/metadata/{rating_key}")
        items = data.get("MediaContainer", {}).get("Metadata", [])
        return items[0] if items else {}

    def get_seasons(self, show_rating_key: int) -> List[Dict]:
        """Get seasons for a show."""
        data = self._request("GET", f"/library/metadata/{show_rating_key}/children")
        return data.get("MediaContainer", {}).get("Metadata", [])

    def get_episodes(self, season_rating_key: int) -> List[Dict]:
        """Get episodes for a season."""
        data = self._request("GET", f"/library/metadata/{season_rating_key}/children")
        return data.get("MediaContainer", {}).get("Metadata", [])

    def get_watch_history(self, library_id: int = None, max_results: int = 50) -> List[Dict]:
        """Get watch history for the server or specific library."""
        if library_id:
            data = self._request("GET", f"/library/sections/{library_id}/history", {"maxResults": max_results})
        else:
            data = self._request("GET", "/status/sessions/history", {"maxResults": max_results})
        return data.get("MediaContainer", {}).get("Metadata", [])

    def get_user_ratings(self, library_id: int) -> List[Dict]:
        """Get user ratings for a library."""
        data = self._request("GET", f"/library/sections/{library_id}/all", {"userRating!": ""})
        return data.get("MediaContainer", {}).get("Metadata", [])

    def search(self, query: str, libtype: str = None) -> List[Dict]:
        """Search for media across all libraries."""
        params = {"query": query}
        if libtype:
            params["type"] = libtype
        data = self._request("GET", "/search", params)
        return data.get("MediaContainer", {}).get("Metadata", [])

    def get_server_info(self) -> Dict:
        """Get server identity and version info."""
        data = self._request("GET", "/identity")
        return data.get("MediaContainer", {})

    def get_recently_added(self, library_id: int, libtype: str = "movie", count: int = 10) -> List[Dict]:
        """Get recently added items."""
        data = self._request("GET", f"/library/sections/{library_id}/recentlyAdded", {
            "type": libtype,
            "X-Plex-Container-Size": count,
        })
        return data.get("MediaContainer", {}).get("Metadata", [])

    def mark_watched(self, rating_key: int) -> bool:
        """Mark an item as watched."""
        try:
            self._request("PUT", f"/:/scrobble", {"identifier": "com.plexapp.plugins.library", "ratingKey": rating_key})
            return True
        except Exception:
            return False

    def mark_unwatched(self, rating_key: int) -> bool:
        """Mark an item as unwatched."""
        try:
            self._request("PUT", f"/:/unscrobble", {"identifier": "com.plexapp.plugins.library", "ratingKey": rating_key})
            return True
        except Exception:
            return False

    def rate(self, rating_key: int, rating: int) -> bool:
        """Rate an item (scale 1-10 in Plex)."""
        try:
            self._request("PUT", f"/:/rate", {
                "identifier": "com.plexapp.plugins.library",
                "ratingKey": rating_key,
                "rating": rating,
            })
            return True
        except Exception:
            return False

    def get_all_guids(self, library_id: int, libtype: str = "movie") -> List[Dict]:
        """Get all items with their GUIDs (IMDb, TMDb, TVDB IDs)."""
        items = self.get_library_items(library_id, libtype)
        guids = []
        for item in items:
            guids.append({
                "rating_key": item.get("ratingKey"),
                "title": item.get("title"),
                "year": item.get("year"),
                "guids": item.get("Guids", []),
                "type": libtype,
            })
        return guids
