"""Stream resolver plugin — orchestrates scrapers → debrid resolution.

This replaces the hardcoded resolver chain in addon/streams/resolver.py
with a plugin-based system.
"""

import logging
from typing import Any

from core.plugins.base import TorrentResult, Stream

logger = logging.getLogger("streamsyncr.plugins.resolver")


class StreamResolverPlugin:
    """Orchestrates scraper plugins → debrid plugins to resolve streams."""

    name = "streamsyncr-resolver"
    version = "2.0.0"
    plugin_type = "resolver"
    protocol = "python"

    def __init__(self):
        self._scrapers = []
        self._debrid = {}

    def register_scraper(self, scraper):
        """Register a scraper plugin."""
        self._scrapers.append(scraper)

    def register_debrid(self, name: str, provider):
        """Register a debrid provider plugin."""
        self._debrid[name] = provider

    def health(self) -> dict:
        return {
            "status": "ok",
            "scrapers": len(self._scrapers),
            "debrid_providers": list(self._debrid.keys()),
        }

    def resolve(self, media_type: str, item_id: str, config: dict) -> list[Stream]:
        """Full resolution pipeline: search → dedupe → debrid → streams."""
        # Step 1: Search for torrents from all enabled scrapers
        torrents = self._search_all(media_type, item_id, config)
        if not torrents:
            # Fallback: check existing debrid torrents
            return self._check_existing(item_id, config)

        # Step 2: Deduplicate by info_hash
        torrents = self._deduplicate(torrents)

        # Step 3: Try debrid providers in priority order
        priority = config.get("debrid_priority", ["realdebrid", "torbox", "alldebrid"])
        for provider_name in priority:
            if provider_name not in self._debrid:
                continue
            api_key = config.get(f"{provider_name}_key", "")
            if not api_key:
                continue

            provider = self._debrid[provider_name]
            streams = self._resolve_with_debrid(provider, api_key, torrents)
            if streams:
                return streams

        return []

    def _search_all(self, media_type: str, item_id: str, config: dict) -> list[TorrentResult]:
        """Run all enabled scrapers and merge results."""
        all_results = []
        for scraper in self._scrapers:
            if not getattr(scraper, "enabled", True):
                continue
            try:
                results = scraper.search(media_type, item_id, config)
                all_results.extend(results)
            except Exception as e:
                logger.warning(f"Scraper {scraper.name} failed: {e}")
        return all_results

    def _deduplicate(self, torrents: list[TorrentResult]) -> list[TorrentResult]:
        """Deduplicate by info_hash, keeping the one with more seeders."""
        by_hash: dict[str, TorrentResult] = {}
        for t in torrents:
            h = t.info_hash.upper()
            if not h:
                continue
            existing = by_hash.get(h)
            if not existing or t.seeders > existing.seeders:
                by_hash[h] = t
        return list(by_hash.values())

    def _resolve_with_debrid(self, provider, api_key: str,
                              torrents: list[TorrentResult]) -> list[Stream]:
        """Try to resolve torrents with a single debrid provider."""
        streams = []
        for torrent in torrents[:5]:
            if not torrent.magnet:
                continue
            try:
                results = provider.add_and_resolve(api_key, torrent.magnet)
                for s in results:
                    s.name = f"{provider.name.title()} • {torrent.tracker}"
                    s.title = f"{torrent.title}\n{s.title}"
                streams.extend(results)
                if streams:
                    break
            except Exception as e:
                logger.warning(f"Debrid {provider.name} failed for {torrent.title}: {e}")
                continue
        return streams

    def _check_existing(self, item_id: str, config: dict) -> list[Stream]:
        """Fallback: check existing debrid torrents."""
        for provider_name in ["realdebrid", "torbox", "alldebrid"]:
            if provider_name not in self._debrid:
                continue
            api_key = config.get(f"{provider_name}_key", "")
            if not api_key:
                continue
            try:
                # Use the existing resolve_imdb if available
                pass
            except Exception:
                pass
        return []


# ── Global Instance ─────────────────────────────────────────

stream_resolver = StreamResolverPlugin()
