"""Data export — fetches user data from all connected services."""

import sys
import os
import json
import time
from datetime import datetime
from typing import Dict, Any, List

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "apis"))


def export_all(user_config: dict) -> Dict[str, Any]:
    """Export data from all connected services."""
    export = {
        "exported_at": datetime.utcnow().isoformat() + "Z",
        "services": {}
    }

    # Trakt
    if user_config.get("trakt_token") and user_config.get("trakt_client_id"):
        try:
            from trakt_api import TraktClient
            client = TraktClient(
                api_key=user_config["trakt_client_id"],
                token=user_config["trakt_token"]
            )
            trakt_data = _export_trakt(client)
            export["services"]["trakt"] = trakt_data
        except Exception as e:
            export["services"]["trakt"] = {"error": str(e)}

    # Simkl
    if user_config.get("simkl_client_id") and user_config.get("simkl_token"):
        try:
            from simkl_api import SimklClient
            client = SimklClient(
                client_id=user_config["simkl_client_id"],
                access_token=user_config.get("simkl_token")
            )
            simkl_data = _export_simkl(client)
            export["services"]["simkl"] = simkl_data
        except Exception as e:
            export["services"]["simkl"] = {"error": str(e)}

    # WeTrakr
    if user_config.get("wetrakr_access_token"):
        try:
            from wetrakr_api.client import WeTrakrClient
            client = WeTrakrClient(
                access_token=user_config["wetrakr_access_token"],
                refresh_token=user_config.get("wetrakr_refresh_token", ""),
                username=user_config.get("wetrakr_username", "")
            )
            wetrakr_data = _export_wetrakr(client)
            export["services"]["wetrakr"] = wetrakr_data
        except Exception as e:
            export["services"]["wetrakr"] = {"error": str(e)}

    # Sofa Sidekick
    if user_config.get("sofasidekick_session_id"):
        try:
            from sofasidekick_api import SofaSidekickClient
            cookies = {
                "session_id": user_config["sofasidekick_session_id"],
                "cf_clearance": user_config.get("sofasidekick_cf_clearance", ""),
                "__cf_bm": user_config.get("sofasidekick_cf_bm", ""),
            }
            client = SofaSidekickClient(cookies=cookies)
            sofa_data = _export_sofasidekick(client)
            export["services"]["sofasidekick"] = sofa_data
        except Exception as e:
            export["services"]["sofasidekick"] = {"error": str(e)}

    # Plex
    if user_config.get("plex_token") and user_config.get("plex_url"):
        try:
            from plex_api import PlexClient
            client = PlexClient(
                server_url=user_config["plex_url"],
                token=user_config["plex_token"]
            )
            plex_data = _export_plex(client)
            export["services"]["plex"] = plex_data
        except Exception as e:
            export["services"]["plex"] = {"error": str(e)}

    # Jellyfin
    if user_config.get("jellyfin_api_key") and user_config.get("jellyfin_url"):
        try:
            from jellyfin_api import JellyfinClient
            client = JellyfinClient(
                server_url=user_config["jellyfin_url"],
                api_key=user_config["jellyfin_api_key"],
                user_id=user_config.get("jellyfin_user_id", "")
            )
            jellyfin_data = _export_jellyfin(client)
            export["services"]["jellyfin"] = jellyfin_data
        except Exception as e:
            export["services"]["jellyfin"] = {"error": str(e)}

    # AniList
    if user_config.get("anilist_token"):
        try:
            from anilist_api import AniListClient
            client = AniListClient(access_token=user_config["anilist_token"])
            anilist_data = _export_anilist(client)
            export["services"]["anilist"] = anilist_data
        except Exception as e:
            export["services"]["anilist"] = {"error": str(e)}

    # MDBList
    if user_config.get("mdblist_api_key"):
        try:
            from mdblist_api.client import MDBListClient
            client = MDBListClient(api_key=user_config["mdblist_api_key"])
            mdblist_data = _export_mdblist(client)
            export["services"]["mdblist"] = mdblist_data
        except Exception as e:
            export["services"]["mdblist"] = {"error": str(e)}

    # Letterboxd (write-only, but we can export what we know)
    if user_config.get("letterboxd_cookies"):
        export["services"]["letterboxd"] = {
            "note": "Letterboxd API is write-only — no user data export available",
            "connected": True
        }

    return export


def _safe_fetch(fn, *args, **kwargs):
    """Try to fetch data, return empty list on error."""
    try:
        return fn(*args, **kwargs)
    except Exception:
        return []


def _export_trakt(client) -> Dict[str, Any]:
    """Export all Trakt data."""
    data = {}

    # Profile
    try:
        data["profile"] = client.me()
    except Exception:
        pass

    # Watched
    data["watched_movies"] = _safe_fetch(client.get_watched_movies, limit=5000)
    data["watched_shows"] = _safe_fetch(client.get_watched_shows, limit=5000)

    # History
    data["history_movies"] = _safe_fetch(client.history, "movies", limit=200)
    data["history_shows"] = _safe_fetch(client.history, "shows", limit=200)

    # Ratings
    data["ratings_movies"] = _safe_fetch(client.ratings, "movies")
    data["ratings_shows"] = _safe_fetch(client.ratings, "shows")

    # Watchlist
    data["watchlist_movies"] = _safe_fetch(client.watchlist, "movies")
    data["watchlist_shows"] = _safe_fetch(client.watchlist, "shows")

    # Favorites
    data["favorites"] = _safe_fetch(client.get_favorites, limit=5000)

    # Collection
    data["collection_movies"] = _safe_fetch(client.collection, "movies")
    data["collection_shows"] = _safe_fetch(client.collection, "shows")

    # Lists
    try:
        lists = client.lists("me")
        data["lists"] = []
        for lst in lists[:20]:  # Limit to 20 lists
            list_data = {
                "name": lst.get("name"),
                "type": lst.get("type"),
                "item_count": lst.get("item_count", 0),
                "items": _safe_fetch(client.list_items, lst.get("ids", {}).get("trakt"), None)
            }
            data["lists"].append(list_data)
    except Exception:
        data["lists"] = []

    return data


def _export_simkl(client) -> Dict[str, Any]:
    """Export all Simkl data."""
    data = {}

    # All items (bulk fetch)
    try:
        all_items = client.get_all_items()
        data["all_items"] = all_items
    except Exception:
        pass

    # Activities
    try:
        data["activities"] = client.get_activities()
    except Exception:
        pass

    return data


def _export_wetrakr(client) -> Dict[str, Any]:
    """Export all WeTrakr data."""
    data = {}

    # Profile
    try:
        data["profile"] = client.get_user()
    except Exception:
        pass

    # Lists (the working approach)
    try:
        lists = client.get_lists()
        data["lists"] = []
        for lst in lists[:20]:
            list_id = lst.get("id") or lst.get("list_id")
            if list_id:
                items = _safe_fetch(client.get_list_items, list_id)
                data["lists"].append({
                    "name": lst.get("name") or lst.get("title"),
                    "id": list_id,
                    "item_count": len(items),
                    "items": items
                })
    except Exception:
        data["lists"] = []

    # Stats
    try:
        data["stats"] = client.get_my_progress()
    except Exception:
        pass

    return data


def _export_sofasidekick(client) -> Dict[str, Any]:
    """Export all Sofa Sidekick data."""
    data = {}

    # Profile
    try:
        data["profile"] = client.me()
    except Exception:
        pass

    # Movies
    try:
        data["movies"] = client.get_movies()
    except Exception:
        data["movies"] = []

    # Stats
    try:
        data["stats"] = client.get_stats()
    except Exception:
        pass

    # Upcoming
    try:
        data["upcoming"] = client.get_upcoming()
    except Exception:
        data["upcoming"] = []

    return data


def _export_plex(client) -> Dict[str, Any]:
    """Export all Plex data."""
    data = {}

    # Libraries
    try:
        sections = client.get_library_sections()
        data["libraries"] = sections
    except Exception:
        data["libraries"] = []

    # Watch history (from each library)
    data["watch_history"] = []
    data["ratings"] = []
    try:
        sections = client.get_library_sections()
        for section in sections[:10]:
            lib_id = section.get("key")
            if lib_id:
                history = _safe_fetch(client.get_watch_history, lib_id)
                data["watch_history"].extend(history)

                ratings = _safe_fetch(client.get_user_ratings, lib_id)
                data["ratings"].extend(ratings)
    except Exception:
        pass

    return data


def _export_jellyfin(client) -> Dict[str, Any]:
    """Export all Jellyfin data."""
    data = {}

    # Recently played
    try:
        data["recently_played"] = client.get_recently_played()
    except Exception:
        data["recently_played"] = []

    # Watch history (resume)
    try:
        data["resume"] = client.get_watch_history()
    except Exception:
        data["resume"] = []

    return data


def _export_anilist(client) -> Dict[str, Any]:
    """Export all AniList data."""
    data = {}

    # Profile
    try:
        data["profile"] = client.get_viewer()
    except Exception:
        pass

    # Anime lists by status
    statuses = ["CURRENT", "COMPLETED", "PLANNED", "DROPPED", "PAUSED", "REPEATING"]
    data["anime"] = {}
    for status in statuses:
        items = _safe_fetch(client.get_user_anime_list, None, status)
        if items:
            data["anime"][status] = items

    # Manga lists by status
    data["manga"] = {}
    for status in statuses:
        items = _safe_fetch(client.get_user_manga_list, None, status)
        if items:
            data["manga"][status] = items

    return data


def _export_mdblist(client) -> Dict[str, Any]:
    """Export all MDBList data."""
    data = {}

    # Profile
    try:
        data["profile"] = client.user()
    except Exception:
        pass

    # Lists
    try:
        lists = client.my_lists()
        data["lists"] = []
        for lst in lists[:20]:
            list_id = lst.get("id")
            if list_id:
                items = _safe_fetch(client.list_items, list_id)
                data["lists"].append({
                    "name": lst.get("name"),
                    "id": list_id,
                    "items": items
                })
    except Exception:
        data["lists"] = []

    return data
