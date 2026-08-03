"""
Kodi JSON-RPC API client for StreamSyncr.

Kodi exposes a local JSON-RPC API at http://<host>:<port>/jsonrpc
Enable it in Settings → Services → Control → Allow remote control via HTTP.

Usage:
    from kodi_api import KodiClient
    c = KodiClient("http://192.168.1.50:8080")
    c.get_movies()
    c.mark_watched(123)
"""

import requests


class KodiClient:
    """Client for Kodi's JSON-RPC API over HTTP."""

    def __init__(self, base_url="http://localhost:8080", username=None, password=None, timeout=10):
        """
        Args:
            base_url: Kodi HTTP API URL (e.g. http://192.168.1.50:8080)
            username: Optional HTTP auth username (set in Kodi settings)
            password: Optional HTTP auth password (set in Kodi settings)
        """
        self.base_url = base_url.rstrip("/")
        self.rpc_url = f"{self.base_url}/jsonrpc"
        self.timeout = timeout
        self.auth = (username, password) if username else None
        self._id = 0

    def _rpc(self, method, params=None):
        """Send a JSON-RPC request to Kodi."""
        self._id += 1
        payload = {
            "jsonrpc": "2.0",
            "method": method,
            "id": self._id,
        }
        if params:
            payload["params"] = params

        res = requests.post(
            self.rpc_url,
            json=payload,
            auth=self.auth,
            timeout=self.timeout,
        )
        res.raise_for_status()
        data = res.json()
        if "error" in data:
            raise Exception(f"Kodi RPC error: {data['error']}")
        return data.get("result")

    def ping(self):
        """Ping Kodi instance."""
        return self._rpc("JSONRPC.Ping")

    def get_version(self):
        """Get Kodi JSON-RPC API version."""
        result = self._rpc("JSONRPC.Version")
        return result.get("version", {})

    def get_volume(self):
        """Get current volume."""
        result = self._rpc("Application.GetProperties", {"properties": ["volume", "muted"]})
        return result

    def set_volume(self, volume):
        """Set volume (0-100)."""
        return self._rpc("Application.SetVolume", {"volume": volume})

    def show_notification(self, title, message, image=None):
        """Show a Kodi notification."""
        params = {"title": title, "message": message, "displaytime": 5000}
        if image:
            params["image"] = image
        return self._rpc("GUI.ShowNotification", params)

    # ── Video Library ──────────────────────────────────────────────────

    def get_movies(self, properties=None, sort=None, limits=None):
        """
        Get all movies from the video library.

        Args:
            properties: List of properties to return (default: standard set)
            sort: Dict with 'method', 'order', 'ignorearticle'
            limits: Dict with 'start', 'end'
        """
        if properties is None:
            properties = [
                "title", "year", "imdbnumber", "rating", "plot",
                "genre", "director", "studio", "mpaa", "runtime",
                "playcount", "dateadded", "art", "file", "resume",
            ]
        params = {"properties": properties}
        if sort:
            params["sort"] = sort
        if limits:
            params["limits"] = limits
        result = self._rpc("VideoLibrary.GetMovies", params)
        return result.get("movies", [])

    def get_movie_details(self, movie_id, properties=None):
        """Get details for a single movie."""
        if properties is None:
            properties = [
                "title", "year", "imdbnumber", "rating", "plot",
                "genre", "director", "studio", "mpaa", "runtime",
                "playcount", "dateadded", "art", "file", "resume",
            ]
        result = self._rpc("VideoLibrary.GetMovieDetails", {
            "movieid": movie_id,
            "properties": properties,
        })
        return result.get("moviedetails")

    def get_shows(self, properties=None, sort=None, limits=None):
        """Get all TV shows."""
        if properties is None:
            properties = [
                "title", "year", "imdbnumber", "rating", "plot",
                "genre", "studio", "mpaa", "episodeguide",
                "playcount", "dateadded", "art", "watchedepisodes", "episode",
            ]
        params = {"properties": properties}
        if sort:
            params["sort"] = sort
        if limits:
            params["limits"] = limits
        result = self._rpc("VideoLibrary.GetTVShows", params)
        return result.get("tvshows", [])

    def get_show_details(self, show_id, properties=None):
        """Get details for a single TV show."""
        if properties is None:
            properties = [
                "title", "year", "imdbnumber", "rating", "plot",
                "genre", "studio", "mpaa", "episodeguide",
                "playcount", "dateadded", "art", "watchedepisodes", "episode",
            ]
        result = self._rpc("VideoLibrary.GetTVShowDetails", {
            "tvshowid": show_id,
            "properties": properties,
        })
        return result.get("tvshowdetails")

    def get_seasons(self, show_id, properties=None):
        """Get seasons for a TV show."""
        if properties is None:
            properties = ["title", "season", "episode", "playcount", "art"]
        result = self._rpc("VideoLibrary.GetSeasons", {
            "tvshowid": show_id,
            "properties": properties,
        })
        return result.get("seasons", [])

    def get_episodes(self, show_id=None, season=None, properties=None, sort=None, limits=None):
        """
        Get episodes. Optionally filter by show and/or season.
        If show_id is None, returns ALL episodes across all shows.
        """
        if properties is None:
            properties = [
                "title", "season", "episode", "rating", "plot",
                "firstaired", "playcount", "dateadded", "art",
                "file", "resume", "tvshowid",
            ]
        params = {"properties": properties}
        if show_id is not None:
            params["tvshowid"] = show_id
        if season is not None:
            params["season"] = season
        if sort:
            params["sort"] = sort
        if limits:
            params["limits"] = limits
        result = self._rpc("VideoLibrary.GetEpisodes", params)
        return result.get("episodes", [])

    def get_episode_details(self, episode_id, properties=None):
        """Get details for a single episode."""
        if properties is None:
            properties = [
                "title", "season", "episode", "rating", "plot",
                "firstaired", "playcount", "dateadded", "art",
                "file", "resume", "tvshowid",
            ]
        result = self._rpc("VideoLibrary.GetEpisodeDetails", {
            "episodeid": episode_id,
            "properties": properties,
        })
        return result.get("episodedetails")

    def get_recently_added_movies(self, properties=None, limits=None):
        """Get recently added movies."""
        if properties is None:
            properties = ["title", "year", "imdbnumber", "rating", "playcount", "art", "dateadded"]
        params = {"properties": properties}
        if limits:
            params["limits"] = limits
        result = self._rpc("VideoLibrary.GetRecentlyAddedMovies", params)
        return result.get("movies", [])

    def get_recently_added_episodes(self, properties=None, limits=None):
        """Get recently added episodes."""
        if properties is None:
            properties = ["title", "season", "episode", "playcount", "art", "dateadded", "tvshowid"]
        params = {"properties": properties}
        if limits:
            params["limits"] = limits
        result = self._rpc("VideoLibrary.GetRecentlyAddedEpisodes", params)
        return result.get("episodes", [])

    # ── Mark Watched / Unwatched ───────────────────────────────────────

    def mark_movie_watched(self, movie_id):
        """Mark a movie as watched."""
        return self._rpc("VideoLibrary.SetMovieDetails", {
            "movieid": movie_id,
            "playcount": 1,
        })

    def mark_movie_unwatched(self, movie_id):
        """Mark a movie as unwatched."""
        return self._rpc("VideoLibrary.SetMovieDetails", {
            "movieid": movie_id,
            "playcount": 0,
        })

    def mark_episode_watched(self, episode_id):
        """Mark an episode as watched."""
        return self._rpc("VideoLibrary.SetEpisodeDetails", {
            "episodeid": episode_id,
            "playcount": 1,
        })

    def mark_episode_unwatched(self, episode_id):
        """Mark an episode as unwatched."""
        return self._rpc("VideoLibrary.SetEpisodeDetails", {
            "episodeid": episode_id,
            "playcount": 0,
        })

    def scan_library(self):
        """Scan the video library for new content."""
        return self._rpc("VideoLibrary.Scan")

    def clean_library(self):
        """Clean the video library (remove deleted files)."""
        return self._rpc("VideoLibrary.Clean")

    # ── Audio Library ──────────────────────────────────────────────────

    def get_artists(self, properties=None, sort=None, limits=None):
        """Get all artists."""
        if properties is None:
            properties = ["instrument", "style", "mood", "born", "formed"]
        params = {"properties": properties}
        if sort:
            params["sort"] = sort
        if limits:
            params["limits"] = limits
        result = self._rpc("AudioLibrary.GetArtists", params)
        return result.get("artists", [])

    def get_albums(self, properties=None, sort=None, limits=None):
        """Get all albums."""
        if properties is None:
            properties = ["title", "artist", "year", "genre", "rating"]
        params = {"properties": properties}
        if sort:
            params["sort"] = sort
        if limits:
            params["limits"] = limits
        result = self._rpc("AudioLibrary.GetAlbums", params)
        return result.get("albums", [])

    def get_songs(self, properties=None, sort=None, limits=None):
        """Get all songs."""
        if properties is None:
            properties = ["title", "artist", "album", "track", "duration", "rating"]
        params = {"properties": properties}
        if sort:
            params["sort"] = sort
        if limits:
            params["limits"] = limits
        result = self._rpc("AudioLibrary.GetSongs", params)
        return result.get("songs", [])

    # ── Player ─────────────────────────────────────────────────────────

    def get_active_players(self):
        """Get currently active players."""
        return self._rpc("Player.GetActivePlayers")

    def get_now_playing(self, properties=None):
        """Get info about currently playing item."""
        if properties is None:
            properties = ["title", "artist", "album", "year", "rating", "duration", "thumbnail", "fanart"]
        players = self.get_active_players()
        if not players:
            return None
        player_id = players[0]["playerid"]
        return self._rpc("Player.GetItem", {
            "playerid": player_id,
            "properties": properties,
        })

    def get_player_properties(self, properties=None):
        """Get player state (playing, paused, speed, time, etc.)."""
        if properties is None:
            properties = ["speed", "time", "totaltime", "percentage", "repeat", "shuffled"]
        players = self.get_active_players()
        if not players:
            return None
        player_id = players[0]["playerid"]
        return self._rpc("Player.GetProperties", {
            "playerid": player_id,
            "properties": properties,
        })

    def play_pause(self, player_id=1, play=None):
        """Toggle play/pause. play=True to play, play=False to pause."""
        params = {"playerid": player_id}
        if play is not None:
            params["play"] = play
        return self._rpc("Player.PlayPause", params)

    def stop(self, player_id=1):
        """Stop playback."""
        return self._rpc("Player.Stop", {"playerid": player_id})

    def play_item(self, item, player_id=1):
        """Play a specific item (movie, episode, etc.)."""
        return self._rpc("Player.Open", {
            "item": item,
            "options": {"playerid": player_id},
        })

    def play_movie(self, movie_id):
        """Play a movie by library ID."""
        return self.play_item({"movieid": movie_id})

    def play_episode(self, episode_id):
        """Play an episode by library ID."""
        return self.play_item({"episodeid": episode_id})

    # ── Search ─────────────────────────────────────────────────────────

    def search_movies(self, query):
        """Search movies by title."""
        result = self._rpc("VideoLibrary.GetMovies", {
            "properties": ["title", "year", "imdbnumber", "rating", "playcount", "art"],
            "sort": {"method": "title", "order": "ascending"},
        })
        movies = result.get("movies", [])
        q = query.lower()
        return [m for m in movies if q in m.get("title", "").lower()]

    def search_shows(self, query):
        """Search TV shows by title."""
        result = self._rpc("VideoLibrary.GetTVShows", {
            "properties": ["title", "year", "imdbnumber", "rating", "playcount", "art", "episode"],
            "sort": {"method": "title", "order": "ascending"},
        })
        shows = result.get("tvshows", [])
        q = query.lower()
        return [s for s in shows if q in s.get("title", "").lower()]

    def search_episodes(self, query):
        """Search episodes by title (across all shows)."""
        result = self._rpc("VideoLibrary.GetEpisodes", {
            "properties": ["title", "season", "episode", "playcount", "tvshowid", "art"],
            "sort": {"method": "title", "order": "ascending"},
        })
        eps = result.get("episodes", [])
        q = query.lower()
        return [e for e in eps if q in e.get("title", "").lower()]

    def global_search(self, query):
        """Search across movies, shows, and episodes."""
        return {
            "movies": self.search_movies(query),
            "shows": self.search_shows(query),
            "episodes": self.search_episodes(query),
        }

    # ── Sync Helpers ───────────────────────────────────────────────────

    def get_watched_movies(self):
        """Get all movies marked as watched (playcount > 0)."""
        movies = self.get_movies(properties=[
            "title", "year", "imdbnumber", "rating", "playcount", "art",
        ])
        return [m for m in movies if m.get("playcount", 0) > 0]

    def get_unwatched_movies(self):
        """Get all movies NOT yet watched."""
        movies = self.get_movies(properties=[
            "title", "year", "imdbnumber", "rating", "playcount", "art",
        ])
        return [m for m in movies if m.get("playcount", 0) == 0]

    def get_watched_episodes(self):
        """Get all episodes marked as watched."""
        episodes = self.get_episodes(properties=[
            "title", "season", "episode", "playcount", "tvshowid", "art",
        ])
        return [e for e in episodes if e.get("playcount", 0) > 0]

    def get_unwatched_episodes(self):
        """Get all episodes NOT yet watched."""
        episodes = self.get_episodes(properties=[
            "title", "season", "episode", "playcount", "tvshowid", "art",
        ])
        return [e for e in episodes if e.get("playcount", 0) == 0]

    def get_library_stats(self):
        """Get summary stats of the video library."""
        movies = self.get_movies(properties=["playcount"])
        shows = self.get_shows(properties=["playcount", "watchedepisodes", "episode"])
        episodes = self.get_episodes(properties=["playcount"])

        watched_movies = sum(1 for m in movies if m.get("playcount", 0) > 0)
        watched_episodes = sum(1 for e in episodes if e.get("playcount", 0) > 0)

        return {
            "total_movies": len(movies),
            "watched_movies": watched_movies,
            "total_shows": len(shows),
            "total_episodes": len(episodes),
            "watched_episodes": watched_episodes,
        }

    def get_imdb_ids(self, media_type="both"):
        """Get all IMDb IDs from the library. media_type: 'movies', 'shows', or 'both'."""
        results = {"movies": [], "shows": []}

        if media_type in ("movies", "both"):
            movies = self.get_movies(properties=["title", "year", "imdbnumber"])
            results["movies"] = [
                {"imdb_id": m["imdbnumber"], "title": m["title"], "year": m.get("year")}
                for m in movies
                if m.get("imdbnumber", "").startswith("tt")
            ]

        if media_type in ("shows", "both"):
            shows = self.get_shows(properties=["title", "year", "imdbnumber"])
            results["shows"] = [
                {"imdb_id": s["imdbnumber"], "title": s["title"], "year": s.get("year")}
                for s in shows
                if s.get("imdbnumber", "").startswith("tt")
            ]

        return results
