"""Sootio stream backend client.

Calls the Sootio Stremio addon's HTTP API to resolve streams using its
7 debrid providers and 14+ scrapers. Sootio must be running locally
(default port 7000).

The Sootio addon exposes the standard Stremio protocol:
    GET /<json-config>/stream/{type}/{id}.json

where <json-config> is a URL-encoded JSON string containing debrid credentials.
"""

import json
import logging
from typing import List, Dict, Optional
from urllib.request import Request, urlopen
from urllib.error import HTTPError, URLError
from urllib.parse import quote

logger = logging.getLogger("streamsyncr")

SOOTIO_DEFAULT_URL = "http://localhost:7000"


def _build_sootio_config(user_config: dict) -> dict:
    """Map StreamSyncr config keys to Sootio's config format.

    Sootio accepts either:
      - DebridServices: [{provider, apiKey}, ...]  (new multi-service)
      - DebridProvider + DebridApiKey              (legacy single-service)
    """
    services = []

    provider_map = {
        "realdebrid_key": "RealDebrid",
        "torbox_key": "TorBox",
        "alldebrid_key": "AllDebrid",
    }

    for key, provider in provider_map.items():
        api_key = user_config.get(key, "")
        if api_key:
            services.append({"provider": provider, "apiKey": api_key})

    if not services:
        return {}

    sootio_config = {"DebridServices": services}

    # Optional language filter
    languages = user_config.get("sootio_languages", [])
    if languages:
        sootio_config["Languages"] = languages

    return sootio_config


def resolve_via_sootio(
    media_type: str,
    item_id: str,
    user_config: dict,
) -> Optional[List[Dict]]:
    """Call Sootio's HTTP API to resolve streams.

    Returns a list of Stremio stream dicts, or None if Sootio is
    unavailable (so the caller can fall back to the built-in resolver).
    """
    sootio_url = (user_config.get("sootio_url") or "").rstrip("/")
    if not sootio_url:
        sootio_url = SOOTIO_DEFAULT_URL

    sootio_config = _build_sootio_config(user_config)
    if not sootio_config:
        return None

    # Sootio expects the config as a JSON string in the URL path
    config_str = json.dumps(sootio_config, separators=(",", ":"))
    encoded_config = quote(config_str, safe="")

    # Sootio uses "movie" and "series" types; anime maps to series
    stremio_type = "series" if media_type in ("series", "anime") else "movie"

    url = f"{sootio_url}/{encoded_config}/stream/{stremio_type}/{item_id}.json"

    req = Request(url)
    try:
        with urlopen(req, timeout=30) as resp:
            data = json.loads(resp.read())
            streams = data.get("streams", [])
            logger.info(f"[Sootio] Resolved {len(streams)} streams for {item_id}")
            return streams
    except (HTTPError, URLError, ConnectionError, TimeoutError) as e:
        logger.warning(f"[Sootio] Backend unavailable at {sootio_url}: {e}")
        return None
    except Exception as e:
        logger.warning(f"[Sootio] Error resolving {item_id}: {e}")
        return None
