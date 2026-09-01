"""Protocol definitions for plugin contracts.

Plugins are utility providers (scrapers, debrid, metadata) that addons
or the core system consume. They can be Python or external HTTP services.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Protocol, Optional, runtime_checkable


# ── Data Models ─────────────────────────────────────────────

@dataclass
class TorrentResult:
    """A torrent search result."""
    title: str
    info_hash: str
    size: int            # bytes
    seeders: int
    tracker: str
    langs: list[str] = field(default_factory=list)
    magnet: str | None = None


@dataclass
class Stream:
    """A resolved stream for playback."""
    name: str
    title: str
    url: str
    duration: int | None = None
    behavior_hints: dict = field(default_factory=dict)


# ── Plugin Base ─────────────────────────────────────────────

@runtime_checkable
class Plugin(Protocol):
    """Base protocol for all plugins."""

    name: str
    version: str
    plugin_type: str       # "scraper", "debrid", "metadata", "resolver", "export-format"
    protocol: str          # "python" | "http"

    def health(self) -> dict:
        """Health check. Returns {"status": "ok"} or error."""
        ...


# ── Scraper Plugin ──────────────────────────────────────────

@runtime_checkable
class ScraperPlugin(Protocol):
    """Searches for torrents from a source."""

    name: str
    category: str          # "public-tracker" | "torznab" | "stremio-addon" | "specialized"
    enabled: bool = True

    def search(self, media_type: str, item_id: str, config: dict,
               query: str | None = None, limit: int = 50) -> list[TorrentResult]:
        """Search for torrents. item_id is IMDb (tt...) or search query."""
        ...


# ── Debrid Plugin ───────────────────────────────────────────

@runtime_checkable
class DebridPlugin(Protocol):
    """A debrid service that can cache-check and resolve magnets."""

    name: str

    def check_cached(self, api_key: str, hashes: list[str]) -> list[dict]:
        """Check which hashes are cached. Returns list of cached items."""
        ...

    def get_download_url(self, api_key: str, magnet: str, file_id: int | None = None) -> str:
        """Get a streaming URL from a magnet link."""
        ...

    def add_and_resolve(self, api_key: str, magnet: str) -> list[Stream]:
        """Add a magnet and resolve it to streams."""
        ...


# ── Metadata Plugin ─────────────────────────────────────────

@runtime_checkable
class MetadataPlugin(Protocol):
    """Provides metadata enrichment (ratings, genres, posters)."""

    name: str

    def is_available(self, config: dict) -> bool:
        """Check if this provider has the required config."""
        ...

    def enrich(self, item_id: str, media_type: str, config: dict) -> dict | None:
        """Enrich an item. Returns metadata dict or None."""
        ...
