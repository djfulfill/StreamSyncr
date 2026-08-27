"""Multi-source metadata enricher.

Routes metadata requests to the user's preferred provider per type
(movie, series, anime), with a fallback chain if the preferred source
is unavailable or returns no data.

Supported providers:
  - TMDB (movies, series) — requires tmdb_api_key
  - AniList (anime) — no key required
  - Simkl (movies, series, anime) — requires simkl_client_id
  - IMDb (movies, series) — requires imdb_full_cookies

The enrich() function is the main entry point. It reads the provider
preference from user_config and tries providers in order until one returns data.
"""

import sys
import os
import logging
from typing import Optional

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

logger = logging.getLogger("streamsyncr")

# Default fallback chains per type
DEFAULT_PROVIDERS = {
    "movie": ["tmdb", "simkl", "imdb"],
    "series": ["tmdb", "simkl", "imdb"],
    "anime": ["anilist", "simkl", "tmdb"],
}


def _img_url(path: str, size: str = "w500") -> str:
    return f"https://image.tmdb.org/t/p/{size}{path}"


def _extract_year(item: dict) -> Optional[int]:
    date = item.get("release_date") or item.get("first_air_date") or ""
    return int(date[:4]) if date else None


# ── TMDB ─────────────────────────────────────────────────────

def enrich_tmdb(tmdb_id: int, media_type: str = "movie", api_key: str = None) -> Optional[dict]:
    """Enrich using TMDB as the metadata source."""
    from tmdb_api import TMDBClient
    tmdb = TMDBClient(api_key=api_key or os.environ.get("TMDB_API_KEY", ""))

    if not tmdb.api_key:
        return None

    if media_type == "movie":
        base = tmdb.movie(tmdb_id)
    else:
        base = tmdb.tv(tmdb_id)

    if not base:
        return None

    poster = base.get("poster_path")
    backdrop = base.get("backdrop_path")

    return {
        "id": f"tt{base.get('imdb_id', '')}" if base.get("imdb_id") else str(tmdb_id),
        "type": media_type,
        "name": base.get("title") or base.get("name", ""),
        "year": _extract_year(base),
        "poster": _img_url(poster) if poster else None,
        "background": _img_url(backdrop, "w1280") if backdrop else None,
        "description": base.get("overview"),
        "runtime": base.get("runtime"),
        "genres": [g["name"] for g in base.get("genres", [])],
        "imdb_rating": base.get("vote_average"),
        "release_info": base.get("release_date") or base.get("first_air_date"),
        "tmdb_id": tmdb_id,
        "imdb_id": base.get("imdb_id"),
    }


# ── AniList ──────────────────────────────────────────────────

def enrich_anilist(anilist_id: int, media_type: str = "anime") -> Optional[dict]:
    """Enrich using AniList as the metadata source."""
    try:
        from anilist_api import AniListClient
        client = AniListClient()
        item = client.get_anime(anilist_id)
        if not item:
            return None

        title = item.get("title", {})
        cover = item.get("coverImage", {})
        banner = item.get("bannerImage")

        return {
            "id": f"anilist:{anilist_id}",
            "type": "series",
            "name": title.get("english") or title.get("romaji", ""),
            "poster": cover.get("large"),
            "background": banner,
            "description": item.get("description"),
            "genres": item.get("genres", []),
            "imdb_rating": item.get("averageScore"),
            "runtime": item.get("duration"),
            "year": item.get("startDate", {}).get("year"),
            "studios": [s.get("name") for s in item.get("studios", {}).get("nodes", []) if s.get("isAnimationStudio")],
            "anilist_id": anilist_id,
        }
    except Exception as e:
        logger.warning(f"AniList enrich failed for {anilist_id}: {e}")
        return None


# ── Simkl ────────────────────────────────────────────────────

def enrich_simkl(simkl_id: int, media_type: str = "movie", user_config: dict = None) -> Optional[dict]:
    """Enrich using Simkl as the metadata source."""
    try:
        from simkl_api import SimklClient
        client_id = (user_config or {}).get("simkl_client_id", os.environ.get("SIMKL_CLIENT_ID", ""))
        if not client_id:
            return None
        client = SimklClient(client_id=client_id)

        if media_type == "movie":
            item = client.get_movie(simkl_id)
        elif media_type == "anime":
            item = client.get_anime(simkl_id)
        else:
            item = client.get_show(simkl_id)

        if not item:
            return None

        poster = item.get("poster") or item.get("images", {}).get("poster")
        title = item.get("title", "")
        overview = item.get("overview") or item.get("plot") or ""

        return {
            "id": f"simkl:{simkl_id}",
            "type": media_type,
            "name": title,
            "poster": poster,
            "description": overview,
            "genres": item.get("genres", []),
            "imdb_rating": item.get("rating", {}).get("simkl", {}).get("rating") if isinstance(item.get("rating"), dict) else item.get("rating"),
            "year": item.get("year"),
            "runtime": item.get("runtime"),
            "simkl_id": simkl_id,
        }
    except Exception as e:
        logger.warning(f"Simkl enrich failed for {simkl_id}: {e}")
        return None


# ── IMDb ──────────────────────────────────────────────────────

def enrich_imdb(imdb_id: str, media_type: str = "movie", user_config: dict = None) -> Optional[dict]:
    """Enrich using IMDb as the metadata source (requires cookies)."""
    try:
        cookies = (user_config or {}).get("imdb_full_cookies", "")
        if not cookies:
            return None
        from imdb_api import IMDbClient
        client = IMDbClient(full_cookies=cookies)
        # IMDb doesn't have a direct "get details by ID" method,
        # but we can use the recently_viewed / search to find the item
        # For now, return a minimal meta with the IMDb ID
        # Full implementation would call IMDb's GraphQL title endpoint
        return None
    except Exception as e:
        logger.warning(f"IMDb enrich failed for {imdb_id}: {e}")
        return None


# ── Main entry point ──────────────────────────────────────────

def enrich(item_id: str, media_type: str = "movie", user_config: dict = None) -> Optional[dict]:
    """Enrich metadata for an item using the configured provider chain.

    Args:
        item_id: Stremio item ID (tt1234567, tmdb:12345, anilist:456, simkl:789, or bare TMDB ID)
        media_type: "movie", "series", or "anime"
        user_config: Config dict with provider preferences and API keys

    Returns:
        Stremio meta dict, or None if all providers failed.
    """
    user_config = user_config or {}
    stremio_type = "series" if media_type in ("series", "anime") else "movie"

    # Determine provider chain from config or defaults
    config_key = f"meta_provider_{media_type}"
    preferred = user_config.get(config_key)
    if preferred:
        chain = [preferred] + [p for p in DEFAULT_PROVIDERS.get(media_type, ["tmdb"]) if p != preferred]
    else:
        chain = DEFAULT_PROVIDERS.get(media_type, ["tmdb"])

    # Try each provider in the chain
    for provider in chain:
        result = _try_provider(provider, item_id, media_type, user_config)
        if result:
            return result

    return None


def _try_provider(provider: str, item_id: str, media_type: str, user_config: dict) -> Optional[dict]:
    """Try a single metadata provider. Returns meta dict or None."""
    from utils.id_mapping import resolve_id

    if provider == "tmdb":
        tmdb_key = user_config.get("tmdb_api_key", os.environ.get("TMDB_API_KEY", ""))
        if not tmdb_key:
            return None
        tmdb_id = resolve_id(item_id, "tmdb", user_config)
        if tmdb_id:
            return enrich_tmdb(int(tmdb_id), "series" if media_type in ("series", "anime") else "movie", tmdb_key)

    elif provider == "anilist":
        if item_id.startswith("anilist:"):
            anilist_id = int(item_id.split(":")[1])
            return enrich_anilist(anilist_id, media_type)
        # Could try to resolve TMDB → AniList via ARM, but skip for now

    elif provider == "simkl":
        simkl_id = resolve_id(item_id, "simkl", user_config)
        if simkl_id:
            return enrich_simkl(int(simkl_id), media_type, user_config)

    elif provider == "imdb":
        if item_id.startswith("tt"):
            return enrich_imdb(item_id, media_type, user_config)

    return None
