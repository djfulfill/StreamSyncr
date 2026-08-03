"""
Sync engine — orchestrates bidirectional sync across all services.

Flow:
  1. Pull state from all connected services
  2. Resolve canonical items (IMDb/TMDB/title+year matching)
  3. Detect conflicts
  4. Apply resolution strategy
  5. Push winning state back to all services
  6. Log all changes
"""

import time
from dataclasses import dataclass, field
from typing import Optional

from .resolver import (
    CanonicalItem, build_key, items_match, merge_items, normalize_title, normalize_year
)
from .resolution import (
    ResolutionStrategy, resolve_all, DEFAULT_SERVICE_PRIORITY
)


@dataclass
class SyncItem:
    """An item being synced between services."""
    canonical: CanonicalItem
    changes: dict = field(default_factory=dict)  # {service: {field: (old, new)}}
    conflicts: list = field(default_factory=list)


@dataclass
class SyncResult:
    """Result of a sync operation."""
    strategy: str
    services_synced: list = field(default_factory=list)
    items_synced: int = 0
    watched_synced: int = 0
    ratings_synced: int = 0
    favorites_synced: int = 0
    errors: list = field(default_factory=list)
    changes: list = field(default_factory=list)  # [SyncItem]
    dry_run: bool = False
    duration_ms: int = 0


class SyncEngine:
    """
    Main sync orchestrator.

    Usage:
        engine = SyncEngine(strategy=ResolutionStrategy.WATCHED_OVERRIDES)
        engine.register_service("trakt", trakt_client)
        engine.register_service("plex", plex_client)
        result = engine.sync()
    """

    def __init__(self, strategy=ResolutionStrategy.WATCHED_OVERRIDES,
                 service_priority=None):
        self.strategy = strategy
        self.service_priority = service_priority or DEFAULT_SERVICE_PRIORITY
        self.services = {}  # {name: client}
        self._cache = {}  # {key: CanonicalItem}

    def register_service(self, name, client):
        """Register a service client."""
        self.services[name] = client

    def sync(self, dry_run=False, sync_watched=True, sync_ratings=True,
             sync_favorites=True, progress_callback=None):
        """
        Run a full sync.

        Args:
            dry_run: If True, don't write to any service
            sync_watched: Sync watch history
            sync_ratings: Sync ratings
            sync_favorites: Sync favorites
            progress_callback: Function called with (current, total, message)

        Returns:
            SyncResult
        """
        start = time.time()
        result = SyncResult(strategy=self.strategy.value, dry_run=dry_run)
        self._cache = {}

        # Step 1: Pull from all services
        all_items = {}
        services_to_sync = list(self.services.keys())

        for i, svc_name in enumerate(services_to_sync):
            if progress_callback:
                progress_callback(i, len(services_to_sync), f"Pulling from {svc_name}...")
            try:
                items = self._pull_service(svc_name)
                for item in items:
                    key = build_key(item)
                    if key in all_items:
                        all_items[key] = merge_items(all_items[key], item)
                    else:
                        all_items[key] = item
            except Exception as e:
                result.errors.append(f"Pull from {svc_name} failed: {e}")

        if progress_callback:
            progress_callback(len(services_to_sync), len(services_to_sync),
                            f"Resolving {len(all_items)} items...")

        # Step 2: Resolve conflicts and determine changes
        sync_items = []
        for key, item in all_items.items():
            resolution = resolve_all(item, self.strategy, self.service_priority)

            # Build change list
            changes = {}
            for svc_name in services_to_sync:
                svc_state = item.service_states.get(svc_name, {})
                svc_changes = {}

                if sync_watched:
                    target_watched = resolution["watched"].get(svc_name)
                    current_watched = svc_state.get("watched", False)
                    if target_watched is not None and target_watched != current_watched:
                        svc_changes["watched"] = (current_watched, target_watched)

                if sync_ratings:
                    target_rating = resolution["rating"].get(svc_name)
                    current_rating = svc_state.get("rating")
                    if target_rating is not None and target_rating != current_rating:
                        svc_changes["rating"] = (current_rating, target_rating)

                if sync_favorites:
                    target_fav = resolution["favorite"].get(svc_name)
                    current_fav = svc_state.get("favorite", False)
                    if target_fav is not None and target_fav != current_fav:
                        svc_changes["favorite"] = (current_fav, target_fav)

                if svc_changes:
                    changes[svc_name] = svc_changes

            if changes:
                sync_items.append(SyncItem(canonical=item, changes=changes))

        result.items_synced = len(sync_items)

        # Step 3: Apply changes
        for i, sync_item in enumerate(sync_items):
            if progress_callback:
                progress_callback(i, len(sync_items),
                                f"Syncing {sync_item.canonical.display_name}...")

            for svc_name, svc_changes in sync_item.changes.items():
                for field_name, (old_val, new_val) in svc_changes.items():
                    change_desc = {
                        "item": sync_item.canonical.display_name,
                        "service": svc_name,
                        "field": field_name,
                        "old": old_val,
                        "new": new_val,
                        "imdb_id": sync_item.canonical.imdb_id,
                        "tmdb_id": sync_item.canonical.tmdb_id,
                    }
                    result.changes.append(change_desc)

                    if field_name == "watched":
                        result.watched_synced += 1
                    elif field_name == "rating":
                        result.ratings_synced += 1
                    elif field_name == "favorite":
                        result.favorites_synced += 1

                    if not dry_run:
                        try:
                            self._push_change(svc_name, sync_item.canonical,
                                           field_name, new_val)
                        except Exception as e:
                            result.errors.append(
                                f"Push to {svc_name} failed for "
                                f"{sync_item.canonical.display_name}: {e}"
                            )

        result.services_synced = services_to_sync
        result.duration_ms = int((time.time() - start) * 1000)

        if progress_callback:
            progress_callback(len(sync_items), len(sync_items), "Sync complete")

        return result

    def get_preview(self, sync_watched=True, sync_ratings=True, sync_favorites=True):
        """Get a preview of what would be synced (dry run)."""
        return self.sync(
            dry_run=True,
            sync_watched=sync_watched,
            sync_ratings=sync_ratings,
            sync_favorites=sync_favorites,
        )

    def _pull_service(self, svc_name):
        """Pull all items from a service. Returns list of CanonicalItem."""
        client = self.services[svc_name]
        items = []

        if svc_name == "trakt":
            items = self._pull_trakt(client)
        elif svc_name == "wetrakr":
            items = self._pull_wetrakr(client)
        elif svc_name == "plex":
            items = self._pull_plex(client)
        elif svc_name == "jellyfin":
            items = self._pull_jellyfin(client)
        elif svc_name == "kodi":
            items = self._pull_kodi(client)
        elif svc_name == "imdb":
            items = self._pull_imdb(client)
        elif svc_name == "anilist":
            items = self._pull_anilist(client)
        elif svc_name == "simkl":
            items = self._pull_simkl(client)
        elif svc_name == "letterboxd":
            items = self._pull_letterboxd(client)

        return items

    def _pull_trakt(self, client):
        items = []
        # Watched
        try:
            watched = client.history()
            for entry in watched:
                item_data = entry.get("movie") or entry.get("show") or entry.get("episode")
                if not item_data:
                    continue
                ids = item_data.get("ids", {})
                canonical = CanonicalItem(
                    imdb_id=ids.get("imdb"),
                    tmdb_id=ids.get("tmdb"),
                    title=item_data.get("title"),
                    year=item_data.get("year"),
                    media_type="show" if "show" in entry else "movie",
                )
                canonical.trakt_id = ids.get("trakt")
                canonical.service_states["trakt"] = {
                    "watched": True,
                    "watched_at": entry.get("watched_at"),
                }
                items.append(canonical)
        except Exception:
            pass

        # Ratings
        try:
            ratings = client.ratings()
            for entry in ratings:
                item_data = entry.get("movie") or entry.get("show")
                if not item_data:
                    continue
                ids = item_data.get("ids", {})
                key = f"imdb:{ids.get('imdb')}" if ids.get("imdb") else \
                      f"tmdb:{ids.get('tmdb')}" if ids.get("tmdb") else \
                      f"titleyear:{normalize_title(item_data.get('title'))}:{item_data.get('year', '')}"
                existing = self._cache.get(key)
                if existing:
                    existing.service_states.setdefault("trakt", {})["rating"] = entry.get("rating")
                    existing.service_states["trakt"]["rated_at"] = entry.get("rated_at")
                else:
                    canonical = CanonicalItem(
                        imdb_id=ids.get("imdb"),
                        tmdb_id=ids.get("tmdb"),
                        title=item_data.get("title"),
                        year=item_data.get("year"),
                    )
                    canonical.trakt_id = ids.get("trakt")
                    canonical.service_states["trakt"] = {
                        "rating": entry.get("rating"),
                        "rated_at": entry.get("rated_at"),
                    }
                    items.append(canonical)
        except Exception:
            pass

        return items

    def _pull_wetrakr(self, client):
        items = []
        try:
            profile = client.get_user()
            # WeTrakr doesn't have a direct watched endpoint in client
            # but we can get tracking data
            tracking = client._get("account/tracking")
            for entry in tracking.get("movies", []):
                canonical = CanonicalItem(
                    tmdb_id=entry.get("ids", {}).get("tmdb", {}).get("id"),
                    title=entry.get("title"),
                    year=entry.get("year"),
                    media_type="movie",
                )
                canonical.wetrakr_id = entry.get("id")
                canonical.service_states["wetrakr"] = {"watched": True}
                items.append(canonical)
        except Exception:
            pass
        return items

    def _pull_plex(self, client):
        items = []
        try:
            history = client.get_watch_history()
            for entry in history:
                guids = entry.get("Guids", [])
                imdb_id = next((g["id"].replace("imdb://", "") for g in guids
                              if g.get("id", "").startswith("imdb://")), None)
                tmdb_id = next((g["id"].replace("tmdb://", "") for g in guids
                               if g.get("id", "").startswith("tmdb://")), None)
                canonical = CanonicalItem(
                    imdb_id=imdb_id,
                    tmdb_id=tmdb_id,
                    title=entry.get("title"),
                    year=entry.get("year"),
                    media_type="movie" if entry.get("type") == "movie" else "show",
                )
                canonical.plex_rating_key = entry.get("ratingKey")
                canonical.service_states["plex"] = {
                    "watched": entry.get("viewCount", 0) > 0,
                }
                items.append(canonical)
        except Exception:
            pass
        return items

    def _pull_jellyfin(self, client):
        items = []
        try:
            history = client.get_watch_history()
            for entry in history:
                canonical = CanonicalItem(
                    imdb_id=entry.get("imdbId") or entry.get("ProviderIds", {}).get("Imdb"),
                    tmdb_id=entry.get("ProviderIds", {}).get("Tmdb"),
                    title=entry.get("name") or entry.get("originalTitle"),
                    year=entry.get("productionYear"),
                    media_type="movie" if entry.get("type") == "Movie" else "show",
                )
                canonical.jellyfin_id = entry.get("id")
                canonical.service_states["jellyfin"] = {
                    "watched": entry.get("played", False),
                }
                items.append(canonical)
        except Exception:
            pass
        return items

    def _pull_kodi(self, client):
        items = []
        try:
            movies = client.get_movies(properties=[
                "title", "year", "imdbnumber", "playcount", "rating",
            ])
            for m in movies:
                canonical = CanonicalItem(
                    imdb_id=m.get("imdbnumber"),
                    title=m.get("title"),
                    year=m.get("year"),
                    media_type="movie",
                )
                canonical.kodi_id = m.get("movieid")
                canonical.service_states["kodi"] = {
                    "watched": m.get("playcount", 0) > 0,
                    "rating": m.get("rating") if m.get("rating") else None,
                }
                items.append(canonical)

            episodes = client.get_episodes(properties=[
                "title", "season", "episode", "playcount", "tvshowid",
            ])
            for e in episodes:
                canonical = CanonicalItem(
                    title=e.get("title"),
                    media_type="show",
                )
                canonical.kodi_id = e.get("episodeid")
                canonical.service_states["kodi"] = {
                    "watched": e.get("playcount", 0) > 0,
                }
                items.append(canonical)
        except Exception:
            pass
        return items

    def _pull_imdb(self, client):
        items = []
        try:
            ratings_data = client.get_ratings()
            for edge in ratings_data.get("data", {}).get("currentUser", {}).get("ratings", {}).get("edges", []):
                node = edge.get("node", {})
                canonical = CanonicalItem(
                    imdb_id=node.get("id"),
                    title=node.get("titleText"),
                    year=node.get("year") or (node.get("releaseDate", {}) or {}).get("year"),
                )
                canonical.service_states["imdb"] = {
                    "rating": node.get("rating", {}).get("currentRating"),
                }
                items.append(canonical)
        except Exception:
            pass
        return items

    def _pull_anilist(self, client):
        items = []
        try:
            trending = client.get_trending()
            for entry in trending:
                title_obj = entry.get("title", {})
                canonical = CanonicalItem(
                    title=title_obj.get("romaji") or title_obj.get("english"),
                    year=entry.get("startDate", {}).get("year"),
                    media_type="show" if entry.get("format") in ["TV", "TV_SHORT"] else "movie",
                )
                canonical.anilist_id = entry.get("id")
                items.append(canonical)
        except Exception:
            pass
        return items

    def _pull_simkl(self, client):
        items = []
        try:
            history = client.get_all_items()
            for entry in history:
                canonical = CanonicalItem(
                    imdb_id=entry.get("ids", {}).get("imdb"),
                    tmdb_id=entry.get("ids", {}).get("tmdb"),
                    title=entry.get("title"),
                    year=entry.get("year"),
                    media_type="show" if entry.get("type") == "show" else "movie",
                )
                canonical.simkl_id = entry.get("ids", {}).get("simkl")
                items.append(canonical)
        except Exception:
            pass
        return items

    def _pull_letterboxd(self, client):
        items = []
        try:
            films = client.get_watched_films()
            for film in films:
                canonical = CanonicalItem(
                    imdb_id=film.get("imdbId"),
                    title=film.get("name"),
                    year=film.get("releaseYear"),
                    media_type="movie",
                )
                canonical.letterboxd_lid = film.get("lid")
                canonical.service_states["letterboxd"] = {"watched": True}
                items.append(canonical)
        except Exception:
            pass
        return items

    def _push_change(self, svc_name, canonical, field, value):
        """Push a single change to a service."""
        client = self.services[svc_name]

        if svc_name == "trakt":
            if field == "watched" and value:
                client.mark_watched_now(
                    movies=[canonical.trakt_id] if canonical.media_type == "movie" else [],
                    shows=[canonical.trakt_id] if canonical.media_type == "show" else [],
                )
            elif field == "rating":
                client.rate(int(value), movies=[canonical.trakt_id])
            elif field == "favorite":
                if value:
                    client.favorite(movies=[canonical.trakt_id])
                else:
                    client.unfavorite(movies=[canonical.trakt_id])

        elif svc_name == "wetrakr":
            if field == "watched" and value:
                client.mark_watched(canonical.wetrakr_id, canonical.media_type)
            elif field == "favorite":
                if value:
                    client.favorite(canonical.wetrakr_id, canonical.media_type)

        elif svc_name == "plex":
            if field == "watched":
                if value:
                    client.mark_watched(canonical.plex_rating_key)
                else:
                    client.mark_unwatched(canonical.plex_rating_key)
            elif field == "rating":
                client.rate(canonical.plex_rating_key, int(value))

        elif svc_name == "jellyfin":
            if field == "watched":
                if value:
                    client.mark_watched(canonical.jellyfin_id)
                else:
                    client.mark_unwatched(canonical.jellyfin_id)
            elif field == "rating":
                client.rate(canonical.jellyfin_id, int(value))

        elif svc_name == "kodi":
            if field == "watched":
                if canonical.media_type == "movie":
                    if value:
                        client.mark_movie_watched(canonical.kodi_id)
                    else:
                        client.mark_movie_unwatched(canonical.kodi_id)
                else:
                    if value:
                        client.mark_episode_watched(canonical.kodi_id)
                    else:
                        client.mark_episode_unwatched(canonical.kodi_id)

        elif svc_name == "imdb":
            if field == "rating":
                if value:
                    client.rate_title(canonical.imdb_id, int(value))
                else:
                    client.delete_rating(canonical.imdb_id)

        elif svc_name == "simkl":
            if field == "watched" and value:
                client.add_to_history(items=[client.make_item(canonical.simkl_id)])

        # Letterboxd and AniList are read-only for now
