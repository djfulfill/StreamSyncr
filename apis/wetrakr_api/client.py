"""
WeTrakr API Client — Python client for the WeTrakr streaming tracker.

CRITICAL: Marking uses INTERNAL IDs, unwatching uses TMDB IDs.
See README.md for full documentation.

BROKEN (2026-08-02): All /filters/auto/sys:* endpoints return state: null.
Use list-based approach instead: get_lists() → get_list_items(list_id).

Endpoints (2026-08-02):
  GET  /proxy/frontend/users/{username}           → user profile
  GET  /proxy/frontend/movies/{tmdb_id}           → movie detail
  GET  /proxy/frontend/shows/{tmdb_id}            → show detail
  GET  /proxy/frontend/shows/{id}/seasons/{n}     → season detail
  GET  /proxy/frontend/shows/{id}/seasons/{n}/episodes/{n} → episode
  GET  /proxy/frontend/users/me/watching-progress → progress summary
  GET  /proxy/search/all?q=&type=&maxPerGroup=    → search
  GET  /proxy/search/trending?filter_type=&limit= → trending
  GET  /proxy/movies/{tmdb_id}/reviews            → reviews
  GET  /proxy/account/tracking/watching/total-time → total time
  GET  /proxy/account/last/tracking               → recent tracking activity
  GET  /proxy/filters/auto/sys:{name}             → filters
  GET  /proxy/account/lists                       → user lists
  GET  /proxy/account/lists/{id}/items            → list items
  POST /proxy/account/tracking                    → mark watched (INTERNAL id)
  POST /proxy/account/tracking/remove/all         → unwatch (TMDB id)
  POST /proxy/account/favorites                   → add to favorites (INTERNAL id)
  POST /proxy/account/favorites/remove            → remove from favorites (TMDB id)
  POST /proxy/account/notes                       → add notes (TMDB id)
  POST /proxy/reviews/{id}/like                   → like a review
  POST /proxy/reviews/{id}/unlike                 → unlike a review
  POST /proxy/account/lists/item/{type}/{id}      → bulk list membership
  PUT  /proxy/account/preferences/pinned-media    → pin to profile (INTERNAL id)
  POST /proxy/users/{id}/follow                   → follow user
  DELETE /proxy/users/{id}/follow                 → unfollow user
  GET  /proxy/users/{id}                          → get user by ID
  GET  /proxy/account/followers                   → list followers
  GET  /proxy/account/following                   → list following
  GET  /proxy/account/followers/requests          → pending follow requests
  GET  /proxy/account/blocked                     → blocked users
"""

import requests
import json
import os
from typing import Optional


class WeTrakrClient:
    """Authenticated WeTrakr API client."""

    def __init__(self, access_token: str = None, refresh_token: str = None,
                 username: str = None, country: str = "US",
                 language: str = "en-US"):
        self.access_token = access_token or os.environ.get("WETRAKR_ACCESS_TOKEN")
        self.refresh_token = refresh_token or os.environ.get("WETRAKR_REFRESH_TOKEN")
        self.username = username or os.environ.get("WETRAKR_USERNAME", "")
        self.country = country
        self.language = language
        self.base_url = "https://wetrakr.com/proxy"

        if not self.access_token or not self.refresh_token:
            raise ValueError(
                "Tokens required. Set WETRAKR_ACCESS_TOKEN and WETRAKR_REFRESH_TOKEN "
                "environment variables, or pass them to the constructor."
            )

    def _headers(self) -> dict:
        return {
            "accept": "application/json, text/plain, */*",
            "content-type": "application/json",
            "wetrakr-api-country": self.country,
            "wetrakr-api-language": self.language,
            "user-agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/151.0.0.0 Safari/537.36",
            "referer": f"https://wetrakr.com/user/{self.username}",
        }

    def _cookies(self) -> dict:
        return {
            "wta_auth": "1",
            "wta_at": self.access_token,
            "wta_rt": self.refresh_token,
        }

    def _get(self, path: str, params: dict = None) -> dict:
        url = f"{self.base_url}/{path}"
        resp = requests.get(url, headers=self._headers(), cookies=self._cookies(), params=params)
        resp.raise_for_status()
        return resp.json()

    def _post(self, path: str, data: dict = None) -> dict:
        url = f"{self.base_url}/{path}"
        resp = requests.post(url, headers=self._headers(), cookies=self._cookies(), json=data)
        resp.raise_for_status()
        return resp.json()

    def _delete(self, path: str, data: dict = None) -> dict:
        url = f"{self.base_url}/{path}"
        resp = requests.delete(url, headers=self._headers(), cookies=self._cookies(), json=data)
        resp.raise_for_status()
        return resp.json()

    def _put(self, path: str, data: dict = None) -> dict:
        url = f"{self.base_url}/{path}"
        resp = requests.put(url, headers=self._headers(), cookies=self._cookies(), json=data)
        resp.raise_for_status()
        return resp.json()

    # ── User ──────────────────────────────────────────────────────────────

    def get_user(self, username: str = None) -> dict:
        """Get user profile with stats, preferences, and activity."""
        username = username or self.username
        return self._get(f"frontend/users/{username}")

    def get_my_progress(self, sort_by: str = "time_left", sort_dir: str = "desc",
                        hide_upcoming: int = 0) -> dict:
        """Get watching progress summary (episodes_left, minutes_left, etc)."""
        return self._get("frontend/users/me/watching-progress", params={
            "sort_by": sort_by,
            "sort_dir": sort_dir,
            "hide_upcoming": hide_upcoming,
        })

    def get_total_time(self, target: str = "shows") -> dict:
        """Get total watched time. target: 'movies', 'shows', 'seasons', or 'episodes'"""
        return self._get("account/tracking/watching/total-time", params={"target": target})

    # ── Movies ────────────────────────────────────────────────────────────

    def get_movie(self, tmdb_id: int) -> dict:
        """Get full movie details (TMDB data + tracking state)."""
        return self._get(f"frontend/movies/{tmdb_id}")

    # ── Shows ─────────────────────────────────────────────────────────────

    def get_show(self, tmdb_id: int) -> dict:
        """Get full show details."""
        return self._get(f"frontend/shows/{tmdb_id}")

    def get_season(self, show_tmdb_id: int, season_number: int) -> dict:
        """Get season details for a show."""
        return self._get(f"frontend/shows/{show_tmdb_id}/seasons/{season_number}")

    def get_episode(self, show_tmdb_id: int, season: int, episode: int) -> dict:
        """Get episode details."""
        return self._get(f"frontend/shows/{show_tmdb_id}/seasons/{season}/episodes/{episode}")

    # ── Reviews ───────────────────────────────────────────────────────────

    def get_reviews(self, tmdb_id: int, media_type: str = "movie",
                    limit: int = 10, page: int = 1, sort: str = "top") -> dict:
        """Get reviews. sort: 'top' or 'newest'"""
        return self._get(f"{media_type}/{tmdb_id}/reviews", params={
            "limit": limit, "page": page, "sort": sort,
        })

    # ── Search ────────────────────────────────────────────────────────────

    def search(self, query: str, search_type: str = "all", max_per_group: int = 10) -> dict:
        """Search for movies, shows, or people."""
        return self._get("search/all", params={
            "q": query, "type": search_type, "maxPerGroup": max_per_group,
        })

    def trending(self, filter_type: str = "", limit: int = 20) -> dict:
        """Get trending content. filter_type: '', 'movie', 'show'"""
        return self._get("search/trending", params={
            "filter_type": filter_type, "limit": limit,
        })

    def trending_shows(self, limit: int = 5) -> dict:
        return self.trending(filter_type="show", limit=limit)

    def trending_movies(self, limit: int = 5) -> dict:
        return self.trending(filter_type="movie", limit=limit)

    # ── Tracking Activity ────────────────────────────────────────────────

    def get_last_tracking(self) -> dict:
        """Get recent tracking activity (now playing, watching, waiting)."""
        return self._get("account/last/tracking", params={
            "extended": "movie_level_1,show_level_1,season_level_1,"
                        "episode_level_1,episode_level_2,person_level_1"
        })

    # ── Filters / Lists ──────────────────────────────────────────────────

    def get_filter(self, filter_name: str, **params) -> dict:
        """Get a system filter. Available: watched, watching, waiting,
        plantowatch, nowplaying, nexttowatch, upcoming, favorites,
        ratings, dropped, paused"""
        return self._get(f"filters/auto/sys:{filter_name}", params=params or None)

    def get_watched(self) -> dict:
        return self.get_filter("watched")

    def get_watching(self) -> dict:
        return self.get_filter("watching")

    def get_waiting(self) -> dict:
        return self.get_filter("waiting")

    def get_plantowatch(self) -> dict:
        return self.get_filter("plantowatch")

    def get_nowplaying(self) -> dict:
        return self.get_filter("nowplaying")

    def get_next_to_watch(self) -> dict:
        return self.get_filter("nexttowatch")

    def get_upcoming(self) -> dict:
        return self.get_filter("upcoming")

    def get_favorites(self) -> dict:
        return self.get_filter("favorites")

    def get_ratings(self) -> dict:
        return self.get_filter("ratings")

    # ── Lists ─────────────────────────────────────────────────────────────

    def get_lists(self) -> list:
        """Get all user lists."""
        return self._get("account/lists")

    def get_list_items(self, list_id: int, page: int = 1, limit: int = 100) -> list:
        """Get items from a specific list."""
        return self._get(f"account/lists/{list_id}/items", params={"page": page, "limit": limit})

    def get_all_list_items(self, list_id: int) -> list:
        """Get ALL items from a list, handling pagination automatically."""
        all_items = []
        page = 1
        while True:
            r = requests.get(
                f"{self.base_url}/account/lists/{list_id}/items",
                headers=self._headers(), cookies=self._cookies(),
                params={"page": page, "limit": 100}
            )
            r.raise_for_status()
            items = r.json()
            if not items:
                break
            all_items.extend(items)
            total = r.headers.get("X-Pagination-Item-Count")
            if total and len(all_items) >= int(total):
                break
            if len(items) < 100:
                break
            page += 1
        return all_items

    # ── Tracking (Write) ─────────────────────────────────────────────────

    def mark_watched(self, item_id: int, media_type: str = "movie",
                     use_release_date: bool = False) -> dict:
        """Mark a title as watched.
        NOTE: item_id must be the INTERNAL id from list items (not TMDB id).
        For shows, always use internal id. For movies, TMDB id also works.
        """
        payload = {
            "movies" if media_type == "movie" else "shows": [
                {"id": item_id, "status": "watched", "use_release_date": use_release_date}
            ]
        }
        return self._post("account/tracking", payload)

    def mark_batch_watched(self, items: list, use_release_date: bool = False) -> dict:
        """Mark multiple items as watched in one request.
        items: [{"id": internal_id, "type": "movie"|"show"}, ...]
        """
        movies = [i["id"] for i in items if i.get("type") == "movie"]
        shows = [i["id"] for i in items if i.get("type") == "show"]
        payload = {}
        if movies:
            payload["movies"] = [{"id": mid, "status": "watched", "use_release_date": use_release_date} for mid in movies]
        if shows:
            payload["shows"] = [{"id": sid, "status": "watched", "use_release_date": use_release_date} for sid in shows]
        return self._post("account/tracking", payload)

    def unwatch(self, tmdb_id: int, media_type: str = "movie") -> dict:
        """Remove tracking for a single item (fully unwatch).
        NOTE: Uses TMDB id, not internal id.
        """
        payload = {
            "movies" if media_type == "movie" else "shows": [
                {"id": tmdb_id, "status": "watched"}
            ]
        }
        return self._post("account/tracking/remove/all", payload)

    def unwatch_batch(self, items: list) -> dict:
        """Remove tracking for multiple items (fully unwatch).
        items: [{"id": tmdb_id, "type": "movie"|"show"}, ...]
        Uses TMDB ids for removal.
        """
        movies = [i["id"] for i in items if i.get("type") == "movie"]
        shows = [i["id"] for i in items if i.get("type") == "show"]
        payload = {}
        if movies:
            payload["movies"] = [{"id": mid, "status": "watched"} for mid in movies]
        if shows:
            payload["shows"] = [{"id": sid, "status": "watched"} for sid in shows]
        return self._post("account/tracking/remove/all", payload)

    def unwatch_all(self, items: list) -> dict:
        """Remove ALL tracking in bulk. items from get_all_list_items().
        Uses TMDB ids for removal. Sends in batches of 100.
        Returns total removed count.
        """
        movies = [i["ids"]["tmdb"]["id"] for i in items
                  if i.get("type") != "show" and i.get("ids", {}).get("tmdb", {}).get("id")]
        shows = [i["ids"]["tmdb"]["id"] for i in items
                 if i.get("type") == "show" and i.get("ids", {}).get("tmdb", {}).get("id")]
        total_removed = {"movies": 0, "shows": 0}
        for i in range(0, max(len(movies), 1), 100):
            batch = movies[i:i+100]
            if batch:
                r = self._post("account/tracking/remove/all",
                               {"movies": [{"id": mid, "status": "watched"} for mid in batch]})
                total_removed["movies"] += r.get("removed", {}).get("watched", {}).get("movies", 0)
        for i in range(0, max(len(shows), 1), 100):
            batch = shows[i:i+100]
            if batch:
                r = self._post("account/tracking/remove/all",
                               {"shows": [{"id": sid, "status": "watched"} for sid in batch]})
                total_removed["shows"] += r.get("removed", {}).get("watched", {}).get("shows", 0)
        return total_removed

    def favorite(self, item_id: int, media_type: str = "movie") -> dict:
        """Add item to favorites. Uses INTERNAL id (same as mark_watched)."""
        key = "movies" if media_type == "movie" else "shows"
        return self._post("account/favorites", {key: [{"id": item_id}]})

    def unfavorite(self, tmdb_id: int, media_type: str = "movie") -> dict:
        """Remove item from favorites. Uses TMDB id (same as unwatch)."""
        key = "movies" if media_type == "movie" else "shows"
        return self._post("account/favorites/remove", {key: [{"id": tmdb_id}]})

    def favorite_batch(self, items: list) -> dict:
        """Add multiple items to favorites. Uses INTERNAL ids (same as mark_watched). Sends in batches of 100."""
        movies = [i["id"] for i in items
                  if i.get("type") != "show"]
        shows = [i["id"] for i in items
                 if i.get("type") == "show"]
        total = {"movies": 0, "shows": 0}
        for i in range(0, max(len(movies), 1), 100):
            batch = movies[i:i+100]
            if batch:
                r = self._post("account/favorites", {"movies": [{"id": mid} for mid in batch]})
                total["movies"] += r.get("added", {}).get("movies", 0)
        for i in range(0, max(len(shows), 1), 100):
            batch = shows[i:i+100]
            if batch:
                r = self._post("account/favorites", {"shows": [{"id": sid} for sid in batch]})
                total["shows"] += r.get("added", {}).get("shows", 0)
        return total

    # ── Notes ─────────────────────────────────────────────────────────────

    def add_note(self, tmdb_id: int, text: str, media_type: str = "movie") -> dict:
        """Add a personal note to an item. Uses TMDB id."""
        key = "movies" if media_type == "movie" else "shows"
        return self._post("account/notes", {key: [{"id": tmdb_id, "text": text}]})

    def get_notes(self, tmdb_id: int, media_type: str = "movie") -> dict:
        """Get notes for an item."""
        return self._get(f"account/notes/{media_type}/{tmdb_id}")

    def delete_note(self, tmdb_id: int, media_type: str = "movie") -> dict:
        """Delete note from an item."""
        return self._delete(f"account/notes/{media_type}/{tmdb_id}")

    # ── Pinned Media ──────────────────────────────────────────────────────

    def pin_media(self, item_id: int, media_type: str = "movie") -> dict:
        """Pin a movie/show to your profile. Uses INTERNAL id."""
        return self._put("account/preferences/pinned-media",
                         {"media_id": item_id, "type": media_type})

    def unpin_media(self) -> dict:
        """Unpin media from your profile."""
        return self._put("account/preferences/pinned-media", {"media_id": None})

    # ── Social ────────────────────────────────────────────────────────────

    def get_user_by_id(self, user_id: int) -> dict:
        """Get user profile by ID (includes plan/VIP status)."""
        return self._get(f"users/{user_id}")

    def get_followers(self) -> list:
        """Get list of users following you."""
        return self._get("account/followers")

    def get_following(self) -> list:
        """Get list of users you follow."""
        return self._get("account/following")

    def get_follow_requests(self) -> list:
        """Get pending follow requests received."""
        return self._get("account/followers/requests")

    def get_blocked_users(self) -> list:
        """Get list of blocked users."""
        return self._get("account/blocked")

    def follow_user(self, user_id: int) -> dict:
        """Follow a user."""
        return self._post(f"users/{user_id}/follow", {})

    def unfollow_user(self, user_id: int) -> dict:
        """Unfollow a user."""
        return self._delete(f"users/{user_id}/follow")

    # ── Reviews ───────────────────────────────────────────────────────────

    def like_review(self, review_id: int) -> dict:
        """Like a review."""
        return self._post(f"reviews/{review_id}/like")

    def unlike_review(self, review_id: int) -> dict:
        """Unlike a review."""
        return self._post(f"reviews/{review_id}/unlike")

    def get_reviews(self, tmdb_id: int, media_type: str = "movie",
                    limit: int = 10, page: int = 1, sort: str = "newest") -> dict:
        """Get reviews for an item."""
        return self._get(f"{media_type}/{tmdb_id}/reviews",
                         {"limit": limit, "page": page, "sort": sort})

    # ── Integrations ──────────────────────────────────────────────────────

    def get_integration_status(self, provider: str) -> dict:
        """Check connection status for a provider (discord, trakt, etc)."""
        return self._get(f"integrations/{provider}")

    def get_discord_status(self) -> dict:
        """Check if Discord is connected."""
        return self.get_integration_status("discord")

    def get_discord_connect_url(self) -> dict:
        """Get Discord OAuth2 authorize URL."""
        return self._get("integrations/discord/connect")

    def connect_discord(self, code: str, state: str) -> dict:
        """Complete Discord OAuth2 flow with auth code and state."""
        return self._post("integrations/discord/callback", {"code": code, "state": state})

    def disconnect_discord(self) -> dict:
        """Disconnect Discord account."""
        return self._delete("integrations/discord")

    def get_trakt_status(self) -> dict:
        """Check if Trakt is connected."""
        return self.get_integration_status("trakt")

    # ── List Membership ───────────────────────────────────────────────────

    def set_list_membership(self, tmdb_id: int, list_ids: list,
                            media_type: str = "movie") -> dict:
        """Add/remove item from multiple lists at once.
        list_ids: [{"id": 123, "included": true}, {"id": 456, "included": false}]
        """
        return self._post(f"account/lists/item/{media_type}/{tmdb_id}",
                          {"lists": list_ids})

    def add_to_list(self, tmdb_id: int, list_id: int, media_type: str = "movie") -> dict:
        """Add item to a single list."""
        return self.set_list_membership(tmdb_id, [{"id": list_id, "included": True}],
                                        media_type)

    def remove_from_list(self, tmdb_id: int, list_id: int, media_type: str = "movie") -> dict:
        """Remove item from a single list."""
        return self.set_list_membership(tmdb_id, [{"id": list_id, "included": False}],
                                        media_type)


# ── CLI ────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    import sys

    client = WeTrakrClient()

    commands = {
        "profile": lambda: client.get_user(),
        "progress": lambda: client.get_my_progress(),
        "time": lambda: client.get_total_time(),
        "lists": lambda: client.get_lists(),
        "last": lambda: client.get_last_tracking(),
        "search": lambda: client.search(sys.argv[2] if len(sys.argv) > 2 else "Inception"),
        "movie": lambda: client.get_movie(int(sys.argv[2]) if len(sys.argv) > 2 else 16330),
        "show": lambda: client.get_show(int(sys.argv[2]) if len(sys.argv) > 2 else 1399),
        "trending": lambda: client.trending(limit=5),
        "watched": lambda: client.get_watched(),
        "watching": lambda: client.get_watching(),
        "plantowatch": lambda: client.get_plantowatch(),
        "nowplaying": lambda: client.get_nowplaying(),
        "discord": lambda: client.get_discord_status(),
        "discord-connect": lambda: client.get_discord_connect_url(),
        "trakt": lambda: client.get_trakt_status(),
        "followers": lambda: client.get_followers(),
        "following": lambda: client.get_following(),
        "follow-requests": lambda: client.get_follow_requests(),
        "blocked": lambda: client.get_blocked_users(),
    }

    cmd = sys.argv[1] if len(sys.argv) > 1 else "profile"
    if cmd in commands:
        result = commands[cmd]()
        print(json.dumps(result, indent=2, default=str))
    else:
        print(f"Usage: python client.py [{'|'.join(commands.keys())}] [query/id]")
