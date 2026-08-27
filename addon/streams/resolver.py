import json
import os
import time
from typing import List, Dict
from urllib.request import Request, urlopen
from urllib.error import HTTPError
from urllib.parse import urlencode

from .torrent_search import TorrentSearchClient


async def resolve_streams(media_type: str, item_id: str, user_config: dict) -> List[Dict]:
    """Resolve streams for an IMDB ID.

    1. Search for torrents via Zilean/Jackett
    2. Add magnet to user's debrid service
    3. Get streaming URL
    """
    streams = []

    # Search for torrents
    searcher = TorrentSearchClient()
    try:
        torrents = searcher.search_by_imdb(item_id, limit=10)
    except Exception as e:
        print(f"[StreamSyncr] Torrent search error: {e}")
        torrents = []

    if not torrents:
        # Fallback: check existing debrid torrents
        return await _check_existing_torrents(item_id, user_config)

    # Try each debrid service in priority order
    priority = user_config.get("debrid_priority", ["realdebrid", "torbox", "alldebrid"])

    for service in priority:
        if service == "realdebrid" and user_config.get("realdebrid_key"):
            streams.extend(await _resolve_realdebrid(torrents, user_config["realdebrid_key"]))
        elif service == "torbox" and user_config.get("torbox_key"):
            streams.extend(await _resolve_torbox(torrents, user_config["torbox_key"]))
        elif service == "alldebrid" and user_config.get("alldebrid_key"):
            streams.extend(await _resolve_alldebrid(torrents, user_config["alldebrid_key"]))

        if streams:
            break  # Return results from first working service

    return streams


async def _check_existing_torrents(item_id: str, user_config: dict) -> List[Dict]:
    """Fallback: check existing debrid torrents."""
    streams = []

    if user_config.get("realdebrid_key"):
        try:
            from .providers.realdebrid import RealDebridClient
            client = RealDebridClient(user_config["realdebrid_key"])
            streams.extend(client.resolve_imdb(item_id))
        except Exception as e:
            print(f"[StreamSyncr] RD existing check error: {e}")

    return streams


async def _resolve_realdebrid(torrents: list, api_key: str) -> List[Dict]:
    """Add torrents to Real-Debrid and get streaming URLs."""
    from .providers.realdebrid import RealDebridClient

    client = RealDebridClient(api_key)
    streams = []

    for torrent in torrents[:5]:  # Limit to top 5
        try:
            result = client.add_and_resolve(torrent["magnet"])
            for s in result:
                s["name"] = f"RD • {torrent.get('source', '?')}"
                s["title"] = f"{torrent['title']}\n{s['title']}"
            streams.extend(result)
            if streams:
                break  # Got results from first torrent
        except Exception as e:
            print(f"[StreamSyncr] RD resolve error for {torrent.get('title', '?')}: {e}")
            continue

    return streams


async def _resolve_torbox(torrents: list, api_key: str) -> List[Dict]:
    """Add torrents to TorBox and get streaming URLs."""
    from .providers.torbox import TorBoxClient

    client = TorBoxClient(api_key)
    streams = []

    for torrent in torrents[:5]:
        try:
            result = client.add_and_resolve(torrent["magnet"])
            for s in result:
                s["name"] = f"TorBox • {torrent.get('source', '?')}"
                s["title"] = f"{torrent['title']}\n{s['title']}"
            streams.extend(result)
            if streams:
                break
        except Exception as e:
            print(f"[StreamSyncr] TorBox resolve error: {e}")
            continue

    return streams


async def _resolve_alldebrid(torrents: list, api_key: str) -> List[Dict]:
    """Add torrents to AllDebrid and get streaming URLs."""
    from .providers.alldebrid import AllDebridClient

    client = AllDebridClient(api_key)
    streams = []

    for torrent in torrents[:5]:
        try:
            result = client.add_and_resolve(torrent["magnet"])
            for s in result:
                s["name"] = f"AllDebrid • {torrent.get('source', '?')}"
                s["title"] = f"{torrent['title']}\n{s['title']}"
            streams.extend(result)
            if streams:
                break
        except Exception as e:
            print(f"[StreamSyncr] AD resolve error: {e}")
            continue

    return streams
