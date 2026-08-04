"""
MDBList API Client

Full-featured client for the MDBList.com API.
Requires MDBLIST_API_KEY environment variable or pass api_key directly.

Usage:
    from mdblist_api import MDBListClient

    m = MDBListClient()
    print(m.user())
    print(m.my_lists())
    items = m.list_items(1176)
"""

import json
import os
import sys
from typing import List, Dict, Optional, Union
from urllib.request import Request, urlopen
from urllib.error import HTTPError
from urllib.parse import urlencode


BASE_URL = "https://api.mdblist.com"


class MDBListClient:
    """Full MDBList API client."""

    def __init__(self, api_key: str = None):
        self.api_key = api_key or os.environ.get("MDBLIST_API_KEY")
        if not self.api_key:
            raise ValueError("MDBLIST_API_KEY not set — get one at https://mdblist.com/preferences/#api")

    def _request(self, method: str, path: str, params: dict = None,
                 data: dict = None) -> Union[dict, list]:
        url = f"{BASE_URL}{path}"
        query = {"apikey": self.api_key}
        if params:
            query.update(params)
        url += "?" + urlencode(query)

        headers = {
            "Content-Type": "application/json",
            "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36",
        }

        body = json.dumps(data).encode() if data else None
        req = Request(url, data=body, headers=headers, method=method)

        try:
            with urlopen(req) as resp:
                return json.loads(resp.read())
        except HTTPError as e:
            error_body = e.read().decode()
            print(f"MDBList API error {e.code}: {error_body}", file=sys.stderr)
            raise

    def _get(self, path: str, **params) -> Union[dict, list]:
        return self._request("GET", path, params=params)

    def _post(self, path: str, data: dict = None) -> Union[dict, list]:
        return self._request("POST", path, data=data)

    def _put(self, path: str, data: dict = None) -> Union[dict, list]:
        return self._request("PUT", path, data=data)

    def _delete(self, path: str) -> Union[dict, list, None]:
        return self._request("DELETE", path)

    # ── User ──────────────────────────────────────────────────

    def user(self) -> dict:
        """Get current user profile, plan, and rate limits."""
        return self._get("/user")

    # ── Lists ─────────────────────────────────────────────────

    def my_lists(self, sort: str = "ranked", unified: bool = False) -> List[dict]:
        """Get all lists for the authenticated user.
        sort: 'ranked', 'name', 'created'
        unified: merge movie+show twin lists into single entry."""
        params = {"sort": sort}
        if unified:
            params["unified"] = "true"
        return self._get("/lists/user", **params)

    def user_lists(self, username: str, sort: str = "ranked") -> List[dict]:
        """Get public lists for a user by username."""
        return self._get(f"/lists/{username}", sort=sort)

    def user_lists_by_id(self, userid: int, sort: str = "ranked") -> List[dict]:
        """Get public lists for a user by user ID."""
        return self._get(f"/lists/user/{userid}", sort=sort)

    def list_info(self, list_id: int) -> dict:
        """Get list metadata by list ID."""
        results = self._get(f"/lists/{list_id}")
        return results[0] if isinstance(results, list) and results else results

    def list_items(self, list_id: int, limit: int = 100, offset: int = 0,
                   mediatype: str = None, append_ratings: bool = False) -> dict:
        """Get items from a list.
        Returns dict with 'movies' and 'shows' arrays.
        mediatype: filter by 'movie' or 'show' (optional).
        append_ratings: include ratings for each item."""
        params = {"limit": limit, "offset": offset}
        if mediatype:
            params["mediatype"] = mediatype
        if append_ratings:
            params["append_to_response"] = "ratings"
        return self._get(f"/lists/{list_id}/items", **params)

    def list_by_name(self, username: str, listname: str) -> List[dict]:
        """Get list by username and slug name."""
        return self._get(f"/lists/{username}/{listname}")

    def list_create(self, name: str, private: bool = True) -> dict:
        """Create a new static list."""
        return self._post("/lists", data={"name": name, "private": private})

    def list_update(self, list_id: int, name: str = None, private: bool = None) -> dict:
        """Update a list's name and/or privacy."""
        data = {}
        if name is not None:
            data["name"] = name
        if private is not None:
            data["private"] = private
        return self._put(f"/lists/{list_id}", data=data)

    def list_delete(self, list_id: int) -> dict:
        """Delete a static list (must own it)."""
        return self._delete(f"/lists/{list_id}")

    # ── Search ─────────────────────────────────────────────────

    def search(self, query: str, mediatype: str = "any", year: int = None,
               limit: int = 100) -> dict:
        """Search for media by title.
        mediatype: 'movie', 'show', or 'any'.
        Returns dict with 'search' array and 'total'."""
        params = {"query": query}
        if year:
            params["year"] = year
        if limit:
            params["limit"] = limit
        return self._get(f"/search/{mediatype}", **params)

    def search_by_imdb(self, imdb_id: str, mediatype: str = "movie") -> dict:
        """Lookup by IMDb ID (e.g., 'tt0244244' or '0244244')."""
        clean_id = imdb_id.replace("tt", "")
        return self._get(f"/imdb/{mediatype}/{clean_id}")

    def search_by_tmdb(self, tmdb_id: int, mediatype: str = "movie") -> dict:
        """Lookup by TMDb ID."""
        return self._get(f"/tmdb/{mediatype}/{tmdb_id}")

    def search_by_trakt(self, trakt_id: int, mediatype: str = "movie") -> dict:
        """Lookup by Trakt ID."""
        return self._get(f"/trakt/{mediatype}/{trakt_id}")

    def search_by_tvdb(self, tvdb_id: int, mediatype: str = "show") -> dict:
        """Lookup by TVDB ID."""
        return self._get(f"/tvdb/{mediatype}/{tvdb_id}")
