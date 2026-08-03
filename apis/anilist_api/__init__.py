"""AniList GraphQL API client."""

import json
from urllib.request import Request, urlopen
from typing import Dict, List, Optional


class AniListClient:
    ENDPOINT = "https://graphql.anilist.co"

    def __init__(self, access_token: str = None):
        self.access_token = access_token

    def _query(self, query: str, variables: dict = None) -> dict:
        data = {"query": query}
        if variables:
            data["variables"] = variables

        body = json.dumps(data).encode()
        req = Request(self.ENDPOINT, data=body, method="POST")
        req.add_header("Content-Type", "application/json")
        req.add_header("Accept", "application/json")
        if self.access_token:
            req.add_header("Authorization", f"Bearer {self.access_token}")

        with urlopen(req) as resp:
            return json.loads(resp.read())

    # ── Read Operations (no auth required) ──

    def search_anime(self, query: str, page: int = 1, per_page: int = 10) -> List[Dict]:
        """Search for anime by title."""
        q = """
        query ($search: String, $page: Int, $perPage: Int) {
            Page(page: $page, perPage: $perPage) {
                media(search: $search, type: ANIME) {
                    id
                    title { romaji english native }
                    episodes
                    status
                    coverImage { large medium }
                    averageScore
                    genres
                    startDate { year month day }
                }
            }
        }
        """
        data = self._query(q, {"search": query, "page": page, "perPage": per_page})
        return data.get("data", {}).get("Page", {}).get("media", [])

    def search_manga(self, query: str, page: int = 1, per_page: int = 10) -> List[Dict]:
        """Search for manga by title."""
        q = """
        query ($search: String, $page: Int, $perPage: Int) {
            Page(page: $page, perPage: $perPage) {
                media(search: $search, type: MANGA) {
                    id
                    title { romaji english native }
                    chapters
                    status
                    coverImage { large medium }
                    averageScore
                    genres
                    startDate { year month day }
                }
            }
        }
        """
        data = self._query(q, {"search": query, "page": page, "perPage": per_page})
        return data.get("data", {}).get("Page", {}).get("media", [])

    def get_anime(self, media_id: int) -> Dict:
        """Get anime details by ID."""
        q = """
        query ($id: Int) {
            Media(id: $id, type: ANIME) {
                id
                title { romaji english native }
                description(asHtml: false)
                episodes
                duration
                status
                coverImage { large medium }
                bannerImage
                averageScore
                meanScore
                popularity
                genres
                startDate { year month day }
                endDate { year month day }
                season
                seasonYear
                nextAiringEpisode { episode airingAt }
                externalLinks { site url }
            }
        }
        """
        data = self._query(q, {"id": media_id})
        return data.get("data", {}).get("Media", {})

    def get_manga(self, media_id: int) -> Dict:
        """Get manga details by ID."""
        q = """
        query ($id: Int) {
            Media(id: $id, type: MANGA) {
                id
                title { romaji english native }
                description(asHtml: false)
                chapters
                volumes
                status
                coverImage { large medium }
                bannerImage
                averageScore
                meanScore
                popularity
                genres
                startDate { year month day }
                endDate { year month day }
                externalLinks { site url }
            }
        }
        """
        data = self._query(q, {"id": media_id})
        return data.get("data", {}).get("Media", {})

    def get_trending(self, media_type: str = "ANIME", per_page: int = 10) -> List[Dict]:
        """Get trending anime/manga."""
        q = """
        query ($type: MediaType, $perPage: Int) {
            Page(perPage: $perPage) {
                media(sort: TRENDING_DESC, type: $type) {
                    id
                    title { romaji english }
                    coverImage { large }
                    averageScore
                    trending
                    genres
                }
            }
        }
        """
        data = self._query(q, {"type": media_type, "perPage": per_page})
        return data.get("data", {}).get("Page", {}).get("media", [])

    def get_popular(self, media_type: str = "ANIME", per_page: int = 10) -> List[Dict]:
        """Get popular anime/manga."""
        q = """
        query ($type: MediaType, $perPage: Int) {
            Page(perPage: $perPage) {
                media(sort: POPULARITY_DESC, type: $type) {
                    id
                    title { romaji english }
                    coverImage { large }
                    averageScore
                    popularity
                    genres
                }
            }
        }
        """
        data = self._query(q, {"type": media_type, "perPage": per_page})
        return data.get("data", {}).get("Page", {}).get("media", [])

    def get_seasonal(self, year: int, season: str, per_page: int = 20) -> List[Dict]:
        """Get seasonal anime."""
        q = """
        query ($season: MediaSeason, $year: Int, $perPage: Int) {
            Page(perPage: $perPage) {
                media(season: $season, seasonYear: $year, type: ANIME, sort: POPULARITY_DESC) {
                    id
                    title { romaji english }
                    coverImage { large }
                    averageScore
                    episodes
                    genres
                }
            }
        }
        """
        data = self._query(q, {"season": season, "year": year, "perPage": per_page})
        return data.get("data", {}).get("Page", {}).get("media", [])

    # ── User List Operations (auth required) ──

    def get_user_anime_list(self, user_name: str, status: str = "COMPLETED") -> List[Dict]:
        """Get a user's anime list."""
        q = """
        query ($userName: String, $status: MediaListStatus) {
            MediaListCollection(userName: $userName, type: ANIME, status: $status) {
                lists {
                    name
                    entries {
                        mediaId
                        status
                        score
                        progress
                        repeat
                        media {
                            id
                            title { romaji english }
                            episodes
                            coverImage { large }
                        }
                    }
                }
            }
        }
        """
        data = self._query(q, {"userName": user_name, "status": status})
        collections = data.get("data", {}).get("MediaListCollection", {}).get("lists", [])
        entries = []
        for lst in collections:
            entries.extend(lst.get("entries", []))
        return entries

    def get_user_manga_list(self, user_name: str, status: str = "COMPLETED") -> List[Dict]:
        """Get a user's manga list."""
        q = """
        query ($userName: String, $status: MediaListStatus) {
            MediaListCollection(userName: $userName, type: MANGA, status: $status) {
                lists {
                    name
                    entries {
                        mediaId
                        status
                        score
                        progress
                        repeat
                        media {
                            id
                            title { romaji english }
                            chapters
                            coverImage { large }
                        }
                    }
                }
            }
        }
        """
        data = self._query(q, {"userName": user_name, "status": status})
        collections = data.get("data", {}).get("MediaListCollection", {}).get("lists", [])
        entries = []
        for lst in collections:
            entries.extend(lst.get("entries", []))
        return entries

    def get_viewer(self) -> Dict:
        """Get the authenticated user's profile."""
        q = """
        query {
            Viewer {
                id
                name
                about
                avatar { large medium }
                bannerImage
                statistics {
                    anime { count meanScore minutesWatched episodesWatched }
                    manga { count meanScore chaptersRead volumesRead }
                }
            }
        }
        """
        data = self._query(q)
        return data.get("data", {}).get("Viewer", {})

    # ── Write Operations (auth required) ──

    def save_anime_list_entry(
        self,
        media_id: int,
        status: str = "COMPLETED",
        score: int = 0,
        progress: int = 0,
    ) -> Dict:
        """Save/update an anime list entry."""
        q = """
        mutation ($mediaId: Int, $status: MediaListStatus, $score: Int, $progress: Int) {
            SaveMediaListEntry(mediaId: $mediaId, status: $status, score: $score, progress: $progress) {
                id
                status
                score
                progress
            }
        }
        """
        return self._query(q, {
            "mediaId": media_id,
            "status": status,
            "score": score,
            "progress": progress,
        }).get("data", {}).get("SaveMediaListEntry", {})

    def delete_anime_list_entry(self, list_entry_id: int) -> bool:
        """Delete an anime list entry."""
        q = """
        mutation ($id: Int) {
            DeleteMediaListEntry(id: $id) { deleted }
        }
        """
        data = self._query(q, {"id": list_entry_id})
        return data.get("data", {}).get("DeleteMediaListEntry", {}).get("deleted", False)

    def toggle_favourite(self, media_id: int) -> bool:
        """Toggle favourite status for an anime."""
        q = """
        mutation ($animeId: Int) {
            ToggleFavourite(animeId: $animeId) { anime { id } }
        }
        """
        data = self._query(q, {"animeId": media_id})
        return data.get("data", {}).get("ToggleFavourite") is not None
