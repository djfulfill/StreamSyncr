"""
TMDB API Client

Full-featured client for The Movie Database API.
Requires TMDB_API_KEY environment variable.

Usage:
    from tmdb_api import TMDBClient

    t = TMDBClient()
    print(t.trending())
    print(t.search("Inception"))
    print(t.movie(550))
"""

import json
import os
import sys
from typing import List, Dict, Optional, Union
from urllib.request import Request, urlopen
from urllib.error import HTTPError
from urllib.parse import urlencode


BASE_URL = "https://api.themoviedb.org/3"
IMG_BASE = "https://image.tmdb.org/t/p"


class TMDBClient:
    """Full TMDB API client."""

    def __init__(self, api_key: str = None):
        self.api_key = api_key or os.environ.get("TMDB_API_KEY")
        if not self.api_key:
            raise ValueError("TMDB_API_KEY not set")

    def _request(self, method: str, path: str, params: dict = None,
                 data: dict = None) -> Union[dict, list]:
        url = f"{BASE_URL}{path}"
        all_params = {"api_key": self.api_key}
        if params:
            all_params.update(params)
        url += "?" + urlencode(all_params)

        headers = {
            "Accept": "application/json",
            "User-Agent": "TMDB-Python-Client/1.0",
        }

        body = json.dumps(data).encode() if data else None
        req = Request(url, data=body, headers=headers, method=method)

        try:
            with urlopen(req) as resp:
                return json.loads(resp.read())
        except HTTPError as e:
            error_body = e.read().decode()
            print(f"TMDB API error {e.code}: {error_body}", file=sys.stderr)
            raise

    def _get(self, path: str, **params) -> Union[dict, list]:
        return self._request("GET", path, params=params)

    def _post(self, path: str, data: dict = None, **params) -> Union[dict, list]:
        return self._request("POST", path, params=params, data=data)

    def _delete(self, path: str, data: dict = None, **params) -> Union[dict, list, None]:
        return self._request("DELETE", path, params=params, data=data)

    def _put(self, path: str, data: dict = None, **params) -> Union[dict, list]:
        return self._request("PUT", path, params=params, data=data)

    # ── Configuration ────────────────────────────────────────

    def config(self) -> dict:
        """Get API configuration (image sizes, base URLs, etc.)."""
        return self._get("/configuration")

    def img_url(self, path: str, size: str = "w500") -> str:
        """Build full image URL from TMDB path."""
        return f"{IMG_BASE}/{size}{path}"

    # ── Search ───────────────────────────────────────────────

    def search(self, query: str, media_type: str = "movie",
               year: int = None, page: int = 1) -> dict:
        """Search TMDB. media_type: 'movie', 'tv', 'person', 'multi'."""
        params = {"query": query, "page": page}
        if year:
            if media_type == "movie":
                params["year"] = year
            else:
                params["first_air_date_year"] = year
        return self._get(f"/search/{media_type}", **params)

    def search_movie(self, title: str, year: int = None) -> List[dict]:
        """Search movies, return list of results."""
        data = self.search(title, "movie", year)
        return data.get("results", [])

    def search_tv(self, title: str, year: int = None) -> List[dict]:
        """Search TV shows."""
        data = self.search(title, "tv", year)
        return data.get("results", [])

    def search_multi(self, query: str) -> List[dict]:
        """Search all media types."""
        data = self.search(query, "multi")
        return data.get("results", [])

    def find_movie(self, title: str, year: int = None) -> Optional[dict]:
        """Find best movie match by title."""
        results = self.search_movie(title, year)
        return results[0] if results else None

    def find_by_imdb(self, imdb_id: str) -> Optional[dict]:
        """Find movie by IMDb ID (tt1234567)."""
        data = self._get(f"/find/{imdb_id}", external_source="imdb_id")
        movies = data.get("movie_results", [])
        return movies[0] if movies else None

    def find_by_imdb_tv(self, imdb_id: str) -> Optional[dict]:
        """Find TV show by IMDb ID."""
        data = self._get(f"/find/{imdb_id}", external_source="imdb_id")
        shows = data.get("tv_results", [])
        return shows[0] if shows else None

    # ── Trending / Popular / Top Rated ───────────────────────

    def trending(self, media_type: str = "movie", time_window: str = "week",
                 page: int = 1) -> List[dict]:
        """Get trending. media_type: 'movie', 'tv', 'person'. time_window: 'day', 'week'."""
        data = self._get(f"/trending/{media_type}/{time_window}", page=page)
        return data.get("results", [])

    def trending_movies(self, time_window: str = "week", limit: int = 20) -> List[dict]:
        """Get trending movies."""
        return self.trending("movie", time_window)[:limit]

    def trending_tv(self, time_window: str = "week", limit: int = 20) -> List[dict]:
        """Get trending TV shows."""
        return self.trending("tv", time_window)[:limit]

    def popular(self, media_type: str = "movie", page: int = 1) -> List[dict]:
        """Get popular. media_type: 'movie', 'tv'."""
        data = self._get(f"/{media_type}/popular", page=page)
        return data.get("results", [])

    def popular_movies(self, limit: int = 20) -> List[dict]:
        """Get popular movies."""
        return self.popular("movie")[:limit]

    def popular_tv(self, limit: int = 20) -> List[dict]:
        """Get popular TV shows."""
        return self.popular("tv")[:limit]

    def top_rated(self, media_type: str = "movie", page: int = 1) -> List[dict]:
        """Get top rated. media_type: 'movie', 'tv'."""
        data = self._get(f"/{media_type}/top_rated", page=page)
        return data.get("results", [])

    def top_rated_movies(self, limit: int = 20) -> List[dict]:
        """Get top rated movies."""
        return self.top_rated("movie")[:limit]

    def top_rated_tv(self, limit: int = 20) -> List[dict]:
        """Get top rated TV shows."""
        return self.top_rated("tv")[:limit]

    def now_playing(self, page: int = 1) -> List[dict]:
        """Get now playing movies."""
        data = self._get("/movie/now_playing", page=page)
        return data.get("results", [])

    def upcoming(self, page: int = 1) -> List[dict]:
        """Get upcoming movies."""
        data = self._get("/movie/upcoming", page=page)
        return data.get("results", [])

    def on_the_air(self, page: int = 1) -> List[dict]:
        """Get on the air TV shows."""
        data = self._get("/tv/on_the_air", page=page)
        return data.get("results", [])

    def airing_today(self, page: int = 1) -> List[dict]:
        """Get TV shows airing today."""
        data = self._get("/tv/airing_today", page=page)
        return data.get("results", [])

    # ── Movie Details ────────────────────────────────────────

    def movie(self, tmdb_id: int) -> dict:
        """Get movie details."""
        return self._get(f"/movie/{tmdb_id}")

    def movie_credits(self, tmdb_id: int) -> dict:
        """Get movie cast and crew."""
        return self._get(f"/movie/{tmdb_id}/credits")

    def movie_similar(self, tmdb_id: int, limit: int = 20) -> List[dict]:
        """Get similar movies."""
        data = self._get(f"/movie/{tmdb_id}/similar")
        return data.get("results", [])[:limit]

    def movie_recommendations(self, tmdb_id: int, limit: int = 20) -> List[dict]:
        """Get movie recommendations."""
        data = self._get(f"/movie/{tmdb_id}/recommendations")
        return data.get("results", [])[:limit]

    def movie_videos(self, tmdb_id: int) -> List[dict]:
        """Get movie videos (trailers, teasers, etc.)."""
        data = self._get(f"/movie/{tmdb_id}/videos")
        return data.get("results", [])

    def movie_watch_providers(self, tmdb_id: int) -> dict:
        """Get movie watch providers (streaming availability)."""
        data = self._get(f"/movie/{tmdb_id}/watch/providers")
        return data.get("results", {})

    # ── TV Show Details ──────────────────────────────────────

    def tv(self, tmdb_id: int) -> dict:
        """Get TV show details."""
        return self._get(f"/tv/{tmdb_id}")

    def tv_credits(self, tmdb_id: int) -> dict:
        """Get TV show cast and crew."""
        return self._get(f"/tv/{tmdb_id}/credits")

    def tv_similar(self, tmdb_id: int, limit: int = 20) -> List[dict]:
        """Get similar TV shows."""
        data = self._get(f"/tv/{tmdb_id}/similar")
        return data.get("results", [])[:limit]

    def tv_season(self, show_tmdb_id: int, season_number: int) -> dict:
        """Get TV season details."""
        return self._get(f"/tv/{show_tmdb_id}/season/{season_number}")

    def tv_episode(self, show_tmdb_id: int, season: int, episode: int) -> dict:
        """Get TV episode details."""
        return self._get(f"/tv/{show_tmdb_id}/season/{season}/episode/{episode}")

    # ── People ───────────────────────────────────────────────

    def person(self, tmdb_id: int) -> dict:
        """Get person details."""
        return self._get(f"/person/{tmdb_id}")

    def person_credits(self, tmdb_id: int) -> dict:
        """Get person movie + TV credits."""
        return self._get(f"/person/{tmdb_id}/combined_credits")

    # ── Genres ───────────────────────────────────────────────

    def genres_movie(self) -> List[dict]:
        """Get movie genres."""
        data = self._get("/genre/movie/list")
        return data.get("genres", [])

    def genres_tv(self) -> List[dict]:
        """Get TV genres."""
        data = self._get("/genre/tv/list")
        return data.get("genres", [])

    # ── Discover ─────────────────────────────────────────────

    def discover_movies(self, **kwargs) -> List[dict]:
        """Discover movies with filters. kwargs: genre, year, rating, sort_by, etc."""
        params = {"sort_by": "popularity.desc"}
        params.update(kwargs)
        if "genre" in kwargs:
            params["with_genres"] = kwargs.pop("genre")
        data = self._get("/discover/movie", **params)
        return data.get("results", [])

    def discover_tv(self, **kwargs) -> List[dict]:
        """Discover TV shows with filters."""
        params = {"sort_by": "popularity.desc"}
        params.update(kwargs)
        if "genre" in kwargs:
            params["with_genres"] = kwargs.pop("genre")
        data = self._get("/discover/tv", **params)
        return data.get("results", [])

    # ── Collection / List ────────────────────────────────────

    def collection(self, collection_id: int) -> dict:
        """Get collection details."""
        return self._get(f"/collection/{collection_id}")

    def collection_items(self, collection_id: int) -> List[dict]:
        """Get movies in a collection."""
        data = self._get(f"/collection/{collection_id}")
        return data.get("parts", [])

    # ── Lists (user-created) ─────────────────────────────────

    def list_details(self, list_id: int) -> dict:
        """Get list details."""
        return self._get(f"/list/{list_id}")

    def list_items(self, list_id: int, page: int = 1) -> List[dict]:
        """Get items in a list."""
        data = self._get(f"/list/{list_id}", page=page)
        return data.get("items", [])

    def list_create(self, session_id: str, name: str, description: str = "",
                    language: str = "en") -> dict:
        """Create a new list (requires session)."""
        return self._post(f"/list?session_id={session_id}", data={
            "name": name,
            "description": description,
            "language": language,
        })

    def list_update(self, list_id: int, session_id: str, name: str = None,
                    description: str = None, language: str = None) -> dict:
        """Update a list."""
        data = {}
        if name is not None:
            data["name"] = name
        if description is not None:
            data["description"] = description
        if language is not None:
            data["language"] = language
        return self._put(f"/list/{list_id}?session_id={session_id}", data=data)

    def list_delete(self, list_id: int, session_id: str) -> dict:
        """Delete a list."""
        return self._delete(f"/list/{list_id}?session_id={session_id}")

    def list_add_items(self, list_id: int, session_id: str,
                       movie_ids: List[int] = None) -> dict:
        """Add movies to a list."""
        items = []
        if movie_ids:
            items.extend([{"media_type": "movie", "media_id": mid} for mid in movie_ids])
        return self._post(f"/list/{list_id}/add_items?session_id={session_id}",
                          items=items)

    def list_remove_items(self, list_id: int, session_id: str,
                          movie_ids: List[int] = None) -> dict:
        """Remove movies from a list."""
        items = []
        if movie_ids:
            items.extend([{"media_type": "movie", "media_id": mid} for mid in movie_ids])
        return self._post(f"/list/{list_id}/remove_items?session_id={session_id}",
                          items=items)

    def list_clear(self, list_id: int, session_id: str) -> dict:
        """Clear all items from a list."""
        return self._post(f"/list/{list_id}/clear?session_id={session_id}")

    def list_check_item(self, list_id: int, movie_id: int) -> bool:
        """Check if a movie is in a list."""
        data = self._get(f"/list/{list_id}/item_status", movie_id=movie_id)
        return data.get("item_present", False)

    def my_lists(self, session_id: str, page: int = 1) -> List[dict]:
        """Get all lists for the authenticated user."""
        data = self._get(f"/account/{session_id}/lists", page=page)
        return data.get("results", [])

    # ── Authentication (for watchlist/ratings) ───────────────

    def request_token(self) -> dict:
        """Get request token for auth flow."""
        return self._get("/authentication/token/new")

    def validate_token(self, request_token: str, username: str,
                       password: str) -> dict:
        """Validate request token with user credentials."""
        return self._post("/authentication/token/validate_with_login",
                          request_token=request_token,
                          username=username, password=password)

    def session_id(self, request_token: str) -> dict:
        """Get session ID from validated request token."""
        return self._post("/authentication/session/new",
                          request_token=request_token)

    # ── Watchlist (requires session) ─────────────────────────

    def account_watchlist(self, session_id: str, media_type: str = "movie",
                          page: int = 1) -> List[dict]:
        """Get account watchlist."""
        data = self._get(f"/account/{session_id}/watchlist/{media_type}",
                         page=page)
        return data.get("results", [])

    def add_to_watchlist(self, session_id: str, media_type: str = "movie",
                         media_id: int = None) -> dict:
        """Add to watchlist."""
        return self._post(f"/account/{session_id}/watchlist",
                          media_type=media_type, media_id=media_id)

    def remove_from_watchlist(self, session_id: str, media_type: str = "movie",
                              media_id: int = None) -> dict:
        """Remove from watchlist."""
        return self._delete(f"/account/{session_id}/watchlist",
                            media_type=media_type, media_id=media_id)

    # ── Favorites (requires session) ─────────────────────────

    def account_favorites(self, session_id: str, media_type: str = "movie",
                          page: int = 1) -> List[dict]:
        """Get account favorites."""
        data = self._get(f"/account/{session_id}/favorite/{media_type}",
                         page=page)
        return data.get("results", [])

    def add_to_favorites(self, session_id: str, media_type: str = "movie",
                         media_id: int = None) -> dict:
        """Add to favorites."""
        return self._post(f"/account/{session_id}/favorite",
                          media_type=media_type, media_id=media_id)

    def remove_from_favorites(self, session_id: str, media_type: str = "movie",
                              media_id: int = None) -> dict:
        """Remove from favorites."""
        return self._delete(f"/account/{session_id}/favorite",
                            media_type=media_type, media_id=media_id)

    # ── Ratings (requires session) ───────────────────────────

    def account_rated(self, session_id: str, media_type: str = "movie",
                      page: int = 1) -> List[dict]:
        """Get account rated movies/shows."""
        data = self._get(f"/account/{session_id}/rated/{media_type}",
                         page=page)
        return data.get("results", [])

    def rate(self, session_id: str, media_type: str = "movie",
             media_id: int = None, rating: float = 8.0) -> dict:
        """Rate a movie/show (0.5 - 10.0)."""
        return self._post(f"/{media_type}/{media_id}/rating",
                          session_id=session_id, value=rating)

    def remove_rating(self, session_id: str, media_type: str = "movie",
                      media_id: int = None) -> dict:
        """Remove rating."""
        return self._delete(f"/{media_type}/{media_id}/rating",
                            session_id=session_id)
