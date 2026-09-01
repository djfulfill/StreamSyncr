"""Jackett scraper — searches via Jackett API."""

import json
import os
from urllib.request import Request, urlopen
from urllib.parse import urlencode

from core.plugins.base import TorrentResult


class JackettScraper:
    """Search torrents via Jackett API (requires self-hosted Jackett instance)."""

    name = "jackett"
    category = "torznab"
    enabled = True

    def search(self, media_type: str, item_id: str, config: dict,
               query: str | None = None, limit: int = 50) -> list[TorrentResult]:
        jackett_url = config.get("jackett_url") or os.environ.get("JACKETT_URL", "")
        jackett_key = config.get("jackett_api_key") or os.environ.get("JACKETT_API_KEY", "")
        if not jackett_url or not jackett_key:
            return []

        params = {
            "apikey": jackett_key,
            "imdbid": item_id.replace("tt", ""),
            "limit": limit,
            "sort": "seeders",
            "order": "desc",
        }
        url = f"{jackett_url}/api/v2.0/indexers/all/results?{urlencode(params)}"
        req = Request(url)
        req.add_header("Accept", "application/json")
        req.add_header("User-Agent", "StreamSyncr/2.0")

        try:
            with urlopen(req, timeout=15) as resp:
                data = json.loads(resp.read())
        except Exception:
            return []

        results = []
        for item in data.get("Results", []):
            magnet = item.get("MagnetUri", "")
            if not magnet:
                continue
            info_hash = _extract_info_hash(magnet)
            results.append(TorrentResult(
                title=item.get("Title", "Unknown"),
                info_hash=info_hash,
                size=item.get("Size", 0),
                seeders=item.get("Seeders", 0),
                tracker=item.get("Tracker", "jackett"),
                magnet=magnet,
            ))

        return results[:limit]


def _extract_info_hash(magnet: str) -> str:
    if "btih:" in magnet:
        start = magnet.lower().index("btih:") + 5
        end = magnet.index("&", start) if "&" in magnet[start:] else len(magnet)
        return magnet[start:end].upper()
    return ""
