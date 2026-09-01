"""MagnetDL scraper — magnet link aggregator."""

import json
import re
from urllib.request import Request, urlopen
from urllib.parse import quote

from core.plugins.base import TorrentResult


class MagnetDLScraper:
    """Search torrents via MagnetDL (public, no auth)."""

    name = "magnetdl"
    category = "public-tracker"
    enabled = True
    base_url = "https://magnetdl.com"

    def search(self, media_type: str, item_id: str, config: dict,
               query: str | None = None, limit: int = 50) -> list[TorrentResult]:
        search_query = query or item_id
        url = f"{self.base_url}/search/?q={quote(search_query)}"
        req = Request(url)
        req.add_header("User-Agent", "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36")

        try:
            with urlopen(req, timeout=15) as resp:
                html = resp.read().decode("utf-8", errors="ignore")
        except Exception:
            return []

        results = []
        # Parse magnet links from HTML
        for match in re.finditer(r'href="(magnet:\?xt=urn:btih:[^"]+)"', html):
            magnet = match.group(1)
            info_hash = _extract_info_hash(magnet)
            if info_hash:
                results.append(TorrentResult(
                    title=_extract_title(magnet),
                    info_hash=info_hash,
                    size=0,
                    seeders=0,
                    tracker="MagnetDL",
                    magnet=magnet,
                ))

        # Deduplicate
        seen = set()
        unique = []
        for r in results:
            if r.info_hash not in seen:
                seen.add(r.info_hash)
                unique.append(r)

        return unique[:limit]


def _extract_info_hash(magnet: str) -> str:
    if "btih:" in magnet:
        start = magnet.lower().index("btih:") + 5
        end = magnet.index("&", start) if "&" in magnet[start:] else len(magnet)
        return magnet[start:end].upper()
    return ""


def _extract_title(magnet: str) -> str:
    if "dn=" in magnet:
        start = magnet.index("dn=") + 3
        end = magnet.index("&", start) if "&" in magnet[start:] else len(magnet)
        from urllib.parse import unquote
        return unquote(magnet[start:end])
    return "Unknown"
