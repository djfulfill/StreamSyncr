"""Torrentio scraper — uses the public Torrentio Stremio addon."""

import json
from urllib.request import Request, urlopen
from urllib.parse import quote

from core.plugins.base import TorrentResult


class TorrentioScraper:
    """Search torrents via Torrentio (free, multi-source, 14+ scrapers built-in)."""

    name = "torrentio"
    category = "stremio-addon"
    enabled = True
    base_url = "https://torrentio.strem.fun"

    def search(self, media_type: str, item_id: str, config: dict,
               query: str | None = None, limit: int = 50) -> list[TorrentResult]:
        """Search by IMDb ID via Torrentio's stream endpoint."""
        url = f"{self.base_url}/stream/{media_type}/{item_id}.json"
        req = Request(url)
        req.add_header("Accept", "application/json")
        req.add_header("User-Agent", "StreamSyncr/2.0")

        try:
            with urlopen(req, timeout=20) as resp:
                data = json.loads(resp.read())
        except Exception:
            return []

        results = []
        for stream in data.get("streams", []):
            info_hash = stream.get("infoHash", "")
            if not info_hash:
                continue

            title = stream.get("title", "Unknown")
            description = stream.get("description", "")
            if "\n" in description:
                title_line = description.split("\n")[0]
                if title_line:
                    title = title_line

            size = _parse_size(description)
            magnet = f"magnet:?xt=urn:btih:{info_hash}&dn={quote(title)}"

            results.append(TorrentResult(
                title=title,
                info_hash=info_hash.upper(),
                size=size,
                seeders=0,
                tracker=stream.get("name", "Torrentio"),
                magnet=magnet,
            ))

        return results[:limit]


def _parse_size(description: str) -> int:
    for part in description.split("\n"):
        part = part.strip()
        if "GB" in part:
            try:
                return int(float(part.replace("GB", "").strip()) * 1024 * 1024 * 1024)
            except ValueError:
                pass
        elif "MB" in part:
            try:
                return int(float(part.replace("MB", "").strip()) * 1024 * 1024)
            except ValueError:
                pass
    return 0
