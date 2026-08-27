"""ID normalization layer — cross-reference IDs between services.

Provides bidirectional mapping between IMDb, TMDB, Simkl, and AniList IDs.
Uses TMDB's /find endpoint and Simkl's /redirect endpoint as primary sources.
"""

import sys
import os
import logging
from typing import Optional

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

logger = logging.getLogger("streamsyncr")


def imdb_to_tmdb(imdb_id: str) -> Optional[int]:
    """IMDb ID (tt1234567) → TMDB ID."""
    from tmdb_api import TMDBClient
    tmdb = TMDBClient()
    result = tmdb.find_by_imdb(imdb_id)
    if result:
        movie_results = result.get("movie_results", [])
        if movie_results:
            return movie_results[0].get("id")
        tv_results = result.get("tv_results", [])
        if tv_results:
            return tv_results[0].get("id")
    return None


def tmdb_to_imdb(tmdb_id: int, media_type: str = "movie") -> Optional[str]:
    """TMDB ID → IMDb ID (tt1234567)."""
    from tmdb_api import TMDBClient
    tmdb = TMDBClient()
    if media_type == "movie":
        result = tmdb.movie(tmdb_id)
    else:
        result = tmdb.tv(tmdb_id)
    return result.get("imdb_id") if result else None


def imdb_to_simkl(imdb_id: str, client_id: str = None) -> Optional[int]:
    """IMDb ID → Simkl ID via Simkl redirect endpoint."""
    try:
        from simkl_api import SimklClient
        client = SimklClient(client_id=client_id or os.environ.get("SIMKL_CLIENT_ID", ""))
        result = client.redirect(imdb_id, id_type="imdb")
        return result.get("simkl_id") or result.get("id")
    except Exception as e:
        logger.debug(f"imdb_to_simkl failed for {imdb_id}: {e}")
        return None


def tmdb_to_simkl(tmdb_id: int, media_type: str = "movie", client_id: str = None) -> Optional[int]:
    """TMDB ID → Simkl ID via Simkl redirect endpoint."""
    try:
        from simkl_api import SimklClient
        client = SimklClient(client_id=client_id or os.environ.get("SIMKL_CLIENT_ID", ""))
        result = client.redirect(str(tmdb_id), id_type="tmdb")
        return result.get("simkl_id") or result.get("id")
    except Exception as e:
        logger.debug(f"tmdb_to_simkl failed for {tmdb_id}: {e}")
        return None


def resolve_id(item_id: str, target: str, user_config: dict = None) -> Optional[str]:
    """Resolve any supported ID to a target service ID.

    Args:
        item_id: Source ID (tt1234567, tmdb:12345, anilist:456, simkl:789)
        target: Target service ("tmdb", "imdb", "simkl", "anilist")
        user_config: Optional config dict with API keys

    Returns:
        Target ID as string, or None if resolution failed.
    """
    user_config = user_config or {}

    # Parse the source ID
    if item_id.startswith("tt"):
        source = "imdb"
        raw_id = item_id
    elif item_id.startswith("tmdb:"):
        source = "tmdb"
        raw_id = item_id[5:]
    elif item_id.startswith("anilist:"):
        source = "anilist"
        raw_id = item_id[8:]
    elif item_id.startswith("simkl:"):
        source = "simkl"
        raw_id = item_id[6:]
    elif item_id.isdigit():
        source = "tmdb"
        raw_id = item_id
    else:
        return None

    if source == target:
        return raw_id

    simkl_client_id = user_config.get("simkl_client_id", os.environ.get("SIMKL_CLIENT_ID", ""))

    if source == "imdb" and target == "tmdb":
        result = imdb_to_tmdb(raw_id)
        return str(result) if result else None

    if source == "tmdb" and target == "imdb":
        return tmdb_to_imdb(int(raw_id)) or None

    if source == "imdb" and target == "simkl":
        result = imdb_to_simkl(raw_id, simkl_client_id)
        return str(result) if result else None

    if source == "tmdb" and target == "simkl":
        result = tmdb_to_simkl(int(raw_id), client_id=simkl_client_id)
        return str(result) if result else None

    return None
