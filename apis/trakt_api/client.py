"""
Trakt API Client

Full-featured client for the Trakt.tv API.
Requires TRAKT_API_KEY and TRAKT_TOKEN environment variables.

Usage:
    from trakt_api import TraktClient

    t = TraktClient()
    print(t.lists())
    print(t.collection())
    t.add_to_list("My Favorites", movies=[4977])
"""

import json
import os
import sys
from typing import List, Dict, Optional, Union
from urllib.request import Request, urlopen
from urllib.error import HTTPError
from urllib.parse import urlencode


BASE_URL = "https://apiz.trakt.tv"


class TraktClient:
    """Full Trakt API client."""

    def __init__(self, api_key: str = None, token: str = None):
        self.api_key = api_key or os.environ.get("TRAKT_API_KEY")
        self.token = token or os.environ.get("TRAKT_TOKEN")
        if not self.api_key:
            raise ValueError("TRAKT_API_KEY not set")
        # Token is optional — public endpoints (trending, popular) work
        # with just the API key. User endpoints (watchlist, favorites)
        # require a valid OAuth2 bearer token.

    def _request(self, method: str, path: str, params: dict = None,
                 data: dict = None, allow_409: bool = False) -> Union[dict, list]:
        url = f"{BASE_URL}{path}"
        if params:
            url += "?" + urlencode(params)

        headers = {
            "Content-Type": "application/json",
            "trakt-api-key": self.api_key,
            "trakt-api-version": "2",
            "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/151.0.0.0 Safari/537.36",
            "Origin": "https://app.trakt.tv",
            "Referer": "https://app.trakt.tv/",
        }
        # Only send Authorization header when we have a token
        if self.token:
            headers["Authorization"] = f"Bearer {self.token}"

        body = json.dumps(data).encode() if data else None
        req = Request(url, data=body, headers=headers, method=method)

        try:
            with urlopen(req) as resp:
                return json.loads(resp.read())
        except HTTPError as e:
            # 409 Conflict is used by scrobble endpoints to confirm
            if e.code == 409 and allow_409:
                try:
                    return json.loads(e.read())
                except Exception:
                    return {"status": "accepted"}
            error_body = e.read().decode()
            print(f"Trakt API error {e.code}: {error_body}", file=sys.stderr)
            raise

    def _get(self, path: str, **params) -> Union[dict, list]:
        return self._request("GET", path, params=params)

    def _post(self, path: str, data: dict = None, allow_409: bool = False) -> Union[dict, list]:
        return self._request("POST", path, data=data, allow_409=allow_409)

    def _delete(self, path: str, data: dict = None) -> Union[dict, list, None]:
        return self._request("DELETE", path, data=data)

    # ── Profile ──────────────────────────────────────────────

    def me(self) -> dict:
        """Get current user profile."""
        return self._get("/users/me")

    # ── Lists ────────────────────────────────────────────────

    def lists(self, username: str = "me") -> List[dict]:
        """Get all lists for a user."""
        return self._get(f"/users/{username}/lists", limit=200)

    def list_items(self, list_id: int, media_type: str = None) -> List[dict]:
        """Get items in a list. media_type: 'movies', 'shows', 'episodes'."""
        path = f"/users/me/lists/{list_id}/items"
        if media_type:
            path += f"/{media_type}"
        return self._get(path, limit=200)

    def list_create(self, name: str, description: str = "",
                    privacy: str = "private", sort_by: str = "rank",
                    display_numbers: bool = False, allow_comments: bool = False) -> dict:
        """Create a new list."""
        return self._post("/users/me/lists", data={
            "name": name,
            "description": description,
            "privacy": privacy,
            "sort_by": sort_by,
            "display_numbers": display_numbers,
            "allow_comments": allow_comments,
        })

    def list_update(self, list_id: int, **kwargs) -> dict:
        """Update a list."""
        return self._request("PUT", f"/users/me/lists/{list_id}", data=kwargs)

    def list_delete(self, list_id: int) -> None:
        """Delete a list."""
        self._delete(f"/users/me/lists/{list_id}")

    def add_to_list(self, list_name: str, movies: List[int] = None,
                    shows: List[int] = None) -> dict:
        """Add items to a list by name. Pass trakt IDs."""
        lists = self.lists()
        target = next((l for l in lists if l["name"] == list_name), None)
        if not target:
            raise ValueError(f"List '{list_name}' not found")

        items = {"movies": [], "shows": []}
        if movies:
            items["movies"] = [{"ids": {"trakt": tid}} for tid in movies]
        if shows:
            items["shows"] = [{"ids": {"trakt": tid}} for tid in shows]

        return self._post(f"/users/me/lists/{target['ids']['trakt']}/items", data=items)

    def remove_from_list(self, list_name: str, movies: List[int] = None,
                         shows: List[int] = None) -> dict:
        """Remove items from a list by name."""
        lists = self.lists()
        target = next((l for l in lists if l["name"] == list_name), None)
        if not target:
            raise ValueError(f"List '{list_name}' not found")

        items = {"movies": [], "shows": []}
        if movies:
            items["movies"] = [{"ids": {"trakt": tid}} for tid in movies]
        if shows:
            items["shows"] = [{"ids": {"trakt": tid}} for tid in shows]

        return self._delete(f"/users/me/lists/{target['ids']['trakt']}/items", data=items)

    def movie_in_lists(self, trakt_id: int) -> List[dict]:
        """Find which lists a movie belongs to."""
        lists = self.lists()
        found = []
        for lst in lists:
            items = self.list_items(lst["ids"]["trakt"], "movies")
            for item in items:
                if item.get("movie", {}).get("ids", {}).get("trakt") == trakt_id:
                    found.append(lst)
                    break
        return found

    # ── Collection ───────────────────────────────────────────

    def collection(self, media_type: str = None) -> List[dict]:
        """Get collection items. media_type: 'movies', 'shows', 'episodes'."""
        path = "/users/me/collection"
        if media_type:
            path += f"/{media_type}"
        return self._get(path)

    def add_to_collection(self, movies: List[dict] = None,
                          shows: List[dict] = None) -> dict:
        """Add to collection. Pass list of {ids: {trakt: id}} dicts."""
        data = {}
        if movies:
            data["movies"] = movies
        if shows:
            data["shows"] = shows
        return self._post("/users/me/collection", data=data)

    def remove_from_collection(self, movies: List[dict] = None,
                               shows: List[dict] = None) -> dict:
        """Remove from collection."""
        data = {}
        if movies:
            data["movies"] = movies
        if shows:
            data["shows"] = shows
        return self._delete("/users/me/collection", data=data)

    # ── Watchlist ────────────────────────────────────────────

    def watchlist(self, media_type: str = None) -> List[dict]:
        """Get watchlist. media_type: 'movies', 'shows'."""
        path = "/users/me/watchlist"
        if media_type:
            path += f"/{media_type}"
        return self._get(path)

    def add_to_watchlist(self, movies: List[int] = None,
                         shows: List[int] = None) -> dict:
        """Add to watchlist."""
        data = {"movies": [], "shows": []}
        if movies:
            data["movies"] = [{"ids": {"trakt": tid}} for tid in movies]
        if shows:
            data["shows"] = [{"ids": {"trakt": tid}} for tid in shows]
        return self._post("/users/me/watchlist", data=data)

    def remove_from_watchlist(self, movies: List[int] = None,
                              shows: List[int] = None) -> dict:
        """Remove from watchlist."""
        data = {"movies": [], "shows": []}
        if movies:
            data["movies"] = [{"ids": {"trakt": tid}} for tid in movies]
        if shows:
            data["shows"] = [{"ids": {"trakt": tid}} for tid in shows]
        return self._delete("/users/me/watchlist", data=data)

    # ── History / Watched ────────────────────────────────────

    def history(self, media_type: str = None) -> List[dict]:
        """Get watch history. media_type: 'movies', 'shows', 'episodes'."""
        path = "/users/me/history"
        if media_type:
            path += f"/{media_type}"
        return self._get(path, limit=200)

    def get_watched(self) -> dict:
        """Get watched summary (movies + shows counts)."""
        return self._get("/users/me/watched")

    def get_watched_movies(self) -> List[dict]:
        """Get all watched movies."""
        return self._get("/users/me/history/movies", limit=5000)

    def get_watched_shows(self) -> List[dict]:
        """Get all watched shows."""
        return self._get("/users/me/history/shows", limit=5000)

    def mark_watched(self, movies: List[dict] = None,
                     shows: List[dict] = None) -> dict:
        """Mark items as watched. Pass list of {ids: {trakt: id}} dicts."""
        data = {}
        if movies:
            data["movies"] = movies
        if shows:
            data["shows"] = shows
        return self._post("/users/me/history", data=data)

    def mark_watched_now(self, movies: List[int] = None,
                         shows: List[int] = None) -> dict:
        """Mark items as watched with current timestamp."""
        data = {"movies": [], "shows": []}
        if movies:
            data["movies"] = [{"ids": {"trakt": tid}} for tid in movies]
        if shows:
            data["shows"] = [{"ids": {"trakt": tid}} for tid in shows]
        return self._post("/users/me/history", data=data)

    def unwatch(self, movies: List[int] = None, shows: List[int] = None) -> dict:
        """Remove items from watch history."""
        data = {"movies": [], "shows": []}
        if movies:
            data["movies"] = [{"ids": {"trakt": tid}} for tid in movies]
        if shows:
            data["shows"] = [{"ids": {"trakt": tid}} for tid in shows]
        return self._delete("/users/me/history", data=data)

    def unwatch_all(self) -> None:
        """Remove all items from watch history."""
        history = self.history()
        if history:
            movies = [item["movie"]["ids"]["trakt"] for item in history
                      if item.get("type") == "movie" and item.get("movie")]
            shows = [item["show"]["ids"]["trakt"] for item in history
                     if item.get("type") == "show" and item.get("show")]
            if movies:
                self.unwatch(movies=movies)
            if shows:
                self.unwatch(shows=shows)

    # ── Plan to Watch / Watchlist ────────────────────────────

    def get_plantowatch(self) -> List[dict]:
        """Get plan to watch list (alias for watchlist)."""
        return self.watchlist()

    # ── Ratings ──────────────────────────────────────────────

    def ratings(self, media_type: str = None) -> List[dict]:
        """Get ratings. media_type: 'movies', 'shows', 'episodes'."""
        path = "/users/me/ratings"
        if media_type:
            path += f"/{media_type}"
        return self._get(path)

    def rate(self, rating: int, movies: List[int] = None,
             shows: List[int] = None) -> dict:
        """Rate items (1-10)."""
        data = {"rating": rating, "movies": [], "shows": []}
        if movies:
            data["movies"] = [{"ids": {"trakt": tid}} for tid in movies]
        if shows:
            data["shows"] = [{"ids": {"trakt": tid}} for tid in shows]
        return self._post("/users/me/ratings", data=data)

    def remove_rating(self, movies: List[int] = None,
                      shows: List[int] = None) -> dict:
        """Remove ratings."""
        data = {"movies": [], "shows": []}
        if movies:
            data["movies"] = [{"ids": {"trakt": tid}} for tid in movies]
        if shows:
            data["shows"] = [{"ids": {"trakt": tid}} for tid in shows]
        return self._delete("/users/me/ratings", data=data)

    # ── Favorites ────────────────────────────────────────────

    def get_favorites(self) -> List[dict]:
        """Get favorites list."""
        return self._get("/users/me/favorites", limit=5000)

    def favorite(self, movies: List[int] = None, shows: List[int] = None) -> dict:
        """Add to favorites."""
        data = {"movies": [], "shows": []}
        if movies:
            data["movies"] = [{"ids": {"trakt": tid}} for tid in movies]
        if shows:
            data["shows"] = [{"ids": {"trakt": tid}} for tid in shows]
        return self._post("/users/me/favorites", data=data)

    def unfavorite(self, movies: List[int] = None, shows: List[int] = None) -> dict:
        """Remove from favorites."""
        data = {"movies": [], "shows": []}
        if movies:
            data["movies"] = [{"ids": {"trakt": tid}} for tid in movies]
        if shows:
            data["shows"] = [{"ids": {"trakt": tid}} for tid in shows]
        return self._delete("/users/me/favorites", data=data)

    # ── Search ───────────────────────────────────────────────

    def search(self, query: str, media_type: str = "movie",
               year: int = None) -> List[dict]:
        """Search Trakt. media_type: 'movie', 'show', 'episode', 'person'."""
        params = {"query": query, "type": media_type}
        if year:
            params["year"] = year
        return self._get("/search", **params)

    def search_movie(self, title: str, year: int = None) -> Optional[dict]:
        """Search for a movie, return first match or None."""
        results = self.search(title, "movie", year)
        if results:
            m = results[0].get("movie", {})
            m["_trakt_id"] = m.get("ids", {}).get("trakt")
            return m
        return None

    def search_show(self, title: str, year: int = None) -> Optional[dict]:
        """Search for a show, return first match or None."""
        results = self.search(title, "show", year)
        if results:
            s = results[0].get("show", {})
            s["_trakt_id"] = s.get("ids", {}).get("trakt")
            return s
        return None

    def find_movie(self, title: str, year: int = None) -> Optional[int]:
        """Find movie by title, return trakt ID or None."""
        m = self.search_movie(title, year)
        return m.get("_trakt_id") if m else None

    # ── Trending ─────────────────────────────────────────────

    def trending_movies(self, limit: int = 20) -> List[dict]:
        """Get trending movies."""
        return self._get("/movies/trending", limit=limit)

    def trending_shows(self, limit: int = 20) -> List[dict]:
        """Get trending shows."""
        return self._get("/shows/trending", limit=limit)

    def popular_movies(self, limit: int = 20) -> List[dict]:
        """Get popular movies."""
        return self._get("/movies/popular", limit=limit)

    def popular_shows(self, limit: int = 20) -> List[dict]:
        """Get popular shows."""
        return self._get("/shows/popular", limit=limit)

    # ── Movie/Show Details ───────────────────────────────────

    def movie(self, trakt_id: int) -> dict:
        """Get movie details."""
        return self._get(f"/movies/{trakt_id}", extended="full")

    def show(self, trakt_id: int) -> dict:
        """Get show details."""
        return self._get(f"/shows/{trakt_id}", extended="full")

    def episode(self, show_trakt_id: int, season: int, number: int) -> dict:
        """Get episode details."""
        return self._get(f"/shows/{show_trakt_id}/seasons/{season}/episodes/{number}",
                         extended="full")

    # ── People/Social ─────────────────────────────────────────

    def followers(self) -> List[dict]:
        """Get followers. Returns list of user objects."""
        data = self._get("/users/me/followers", limit=100)
        return [item["user"] for item in data]

    def following(self) -> List[dict]:
        """Get who the user is following. Returns list of user objects."""
        data = self._get("/users/me/following", limit=100)
        return [item["user"] for item in data]

    def user_profile(self, username: str) -> dict:
        """Get a user's profile by username."""
        return self._get(f"/users/{username}")

    def follow_user(self, username: str) -> dict:
        """Follow a user by username. Returns approved user info."""
        return self._post(f"/users/{username}/follow")

    def unfollow_user(self, username: str) -> None:
        """Unfollow a user by username."""
        self._delete(f"/users/{username}/follow")

    def is_following(self, username: str) -> bool:
        """Check if you're following a user."""
        following = self.following()
        return any(u.get("username") == username for u in following)

    def is_followed_by(self, username: str) -> bool:
        """Check if a user is following you."""
        followers = self.followers()
        return any(u.get("username") == username for u in followers)

    # ── Scrobbling ───────────────────────────────────────────

    def scrobble_start(self, trakt_id: int, media_type: str = "movie") -> dict:
        """Start watching (scrobble start). media_type: 'movie' or 'episode'."""
        payload = {media_type: {"ids": {"trakt": trakt_id}}}
        return self._post("/scrobble/start", data=payload, allow_409=True)

    def scrobble_pause(self, trakt_id: int, media_type: str = "movie",
                       progress: float = 0.0) -> dict:
        """Pause watching. progress: 0.0-100.0."""
        payload = {media_type: {"ids": {"trakt": trakt_id}}, "progress": progress}
        return self._post("/scrobble/pause", data=payload, allow_409=True)

    def scrobble_stop(self, trakt_id: int, media_type: str = "movie",
                      progress: float = 100.0) -> dict:
        """Stop watching. progress >= 1.0 to mark as watched."""
        payload = {media_type: {"ids": {"trakt": trakt_id}}, "progress": progress}
        return self._post("/scrobble/stop", data=payload, allow_409=True)

    def scrobble_check(self) -> dict:
        """Check what's currently being scrobbled (active watchers)."""
        return self._get("/scrobble/movies/watching")
