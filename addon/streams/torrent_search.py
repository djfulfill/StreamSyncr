"""Torrent search using public Stremio addons (no pip install needed).

Uses:
- Torrentio (public, free, 14+ scrapers built-in)
- Jackett API (if configured)
"""

import json
import os
from urllib.request import Request, urlopen
from urllib.error import HTTPError
from urllib.parse import urlencode, quote


class TorrentSearchClient:
    """Search for torrents by IMDB ID using public APIs."""

    TORRENTIO_URL = os.environ.get("TORRENTIO_URL", "https://torrentio.strem.fun")
    JACKETT_URL = os.environ.get("JACKETT_URL", "")
    JACKETT_API_KEY = os.environ.get("JACKETT_API_KEY", "")

    def search_by_imdb(self, imdb_id: str, limit: int = 30) -> list:
        """Search for torrents matching an IMDB ID.

        Returns list of dicts: {title, magnet, seeders, size, source}
        """
        results = []

        # Try Torrentio first (free, fast, multi-source)
        try:
            results.extend(self._search_torrentio(imdb_id, limit))
        except Exception as e:
            print(f"[TorrentSearch] Torrentio error: {e}")

        # Fallback to Jackett if configured
        if not results and self.JACKETT_URL and self.JACKETT_API_KEY:
            try:
                results.extend(self._search_jackett(imdb_id, limit))
            except Exception as e:
                print(f"[TorrentSearch] Jackett error: {e}")

        # Deduplicate by info_hash
        seen = set()
        unique = []
        for r in results:
            h = r.get("info_hash", "")
            if h and h in seen:
                continue
            if h:
                seen.add(h)
            unique.append(r)

        return unique[:limit]

    def _search_torrentio(self, imdb_id: str, limit: int) -> list:
        """Search via Torrentio's stream endpoint."""
        # Torrentio returns streams with magnet links embedded
        url = f"{self.TORRENTIO_URL}/stream/movie/{imdb_id}.json"

        req = Request(url)
        req.add_header("Accept", "application/json")
        req.add_header("User-Agent", "StreamSyncr/1.0")

        with urlopen(req, timeout=20) as resp:
            data = json.loads(resp.read())

        results = []
        for stream in data.get("streams", []):
            # Torrentio embeds info in the stream object
            info_hash = stream.get("infoHash", "")
            if not info_hash:
                continue

            # Build magnet from info_hash
            title = stream.get("title", "Unknown")
            name = stream.get("name", "Torrentio")

            # Extract title from description (after first newline)
            description = stream.get("description", "")
            if "\n" in description:
                title_line = description.split("\n")[0]
                if title_line:
                    title = title_line

            # Parse size from description
            size = 0
            for part in description.split("\n"):
                if "GB" in part or "MB" in part:
                    try:
                        size_str = part.strip()
                        if "GB" in size_str:
                            size = int(float(size_str.replace("GB", "").strip()) * 1024 * 1024 * 1024)
                        elif "MB" in size_str:
                            size = int(float(size_str.replace("MB", "").strip()) * 1024 * 1024)
                    except:
                        pass
                    break

            magnet = f"magnet:?xt=urn:btih:{info_hash}&dn={quote(title)}"

            results.append({
                "title": title,
                "magnet": magnet,
                "info_hash": info_hash.upper(),
                "seeders": 0,  # Torrentio doesn't expose seeders
                "size": size,
                "source": name,
            })

        return results

    def _search_jackett(self, imdb_id: str, limit: int) -> list:
        """Search via Jackett API."""
        params = {
            "apikey": self.JACKETT_API_KEY,
            "imdbid": imdb_id.replace("tt", ""),
            "limit": limit,
            "sort": "seeders",
            "order": "desc",
        }

        url = f"{self.JACKETT_URL}/api/v2.0/indexers/all/results?{urlencode(params)}"

        req = Request(url)
        req.add_header("Accept", "application/json")
        req.add_header("User-Agent", "StreamSyncr/1.0")

        with urlopen(req, timeout=15) as resp:
            data = json.loads(resp.read())

        results = []
        for item in data.get("Results", []):
            magnet = item.get("MagnetUri", "")
            if not magnet:
                continue

            info_hash = self._extract_info_hash(magnet)
            results.append({
                "title": item.get("Title", "Unknown"),
                "magnet": magnet,
                "info_hash": info_hash,
                "seeders": item.get("Seeders", 0),
                "size": item.get("Size", 0),
                "source": item.get("Tracker", "jackett"),
            })

        return results

    @staticmethod
    def _extract_info_hash(magnet: str) -> str:
        """Extract info hash from a magnet URI."""
        if "btih:" in magnet:
            start = magnet.lower().index("btih:") + 5
            end = magnet.index("&", start) if "&" in magnet[start:] else len(magnet)
            return magnet[start:end].upper()
        return ""
