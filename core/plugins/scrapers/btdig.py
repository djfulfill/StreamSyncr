"""BTDigg scraper — DHT search engine."""

import json
from urllib.request import Request, urlopen
from urllib.parse import urlencode, quote

from core.plugins.base import TorrentResult


class BTDiggScraper:
    """Search torrents via BTDigg DHT search engine (public, no auth)."""

    name = "btdig"
    category = "public-tracker"
    enabled = True
    base_url = "https://api.btdig.com"

    def search(self, media_type: str, item_id: str, config: dict,
               query: str | None = None, limit: int = 50) -> list[TorrentResult]:
        search_query = query or item_id
        params = {
            "q": search_query,
            "output": "json",
        }
        url = f"{self.base_url}/search?{urlencode(params)}"
        req = Request(url)
        req.add_header("User-Agent", "StreamSyncr/2.0")

        try:
            with urlopen(req, timeout=15) as resp:
                data = json.loads(resp.read())
        except Exception:
            return []

        results = []
        for item in data.get("torrents", [])[:limit]:
            info_hash = item.get("info_hash", "").upper()
            magnet = f"magnet:?xt=urn:btih:{info_hash}&dn={quote(item.get('title', ''))}"
            results.append(TorrentResult(
                title=item.get("title", "Unknown"),
                info_hash=info_hash,
                size=item.get("size", 0),
                seeders=item.get("seeders", 0),
                tracker="BTDigg",
                magnet=magnet,
            ))

        return results
