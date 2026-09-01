"""Protocol definitions for addon contracts.

Every service addon must implement the Addon protocol.
Sub-protocols (Scrobble, SyncSource, etc.) are optional capabilities.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable, Protocol, Optional, runtime_checkable


# ── Data Models ─────────────────────────────────────────────

@dataclass
class CatalogDef:
    """Declares a catalog an addon provides."""
    id: str                           # e.g. "trakt-trending"
    label: str                        # e.g. "Trending"
    type: str = "movie|series"        # pipe-separated Stremio types
    auth: bool = False                # requires user auth to access


@dataclass
class VerifyResult:
    """Result of addon credential verification."""
    status: str            # "ok", "error", "missing_credentials"
    error: str | None = None
    details: dict = field(default_factory=dict)


@dataclass
class ScrobbleEvent:
    """A playback event from a client."""
    action: str            # "start", "pause", "resume", "stop", "heartbeat"
    item_id: str           # IMDb ID (tt...) or TMDB ID
    media_type: str = "movie"
    progress: float = 0.0  # 0-100
    title: str = ""
    year: int | None = None
    season: int | None = None
    episode: int | None = None
    client_type: str = "unknown"
    position_seconds: float | None = None
    total_seconds: float | None = None
    # Resolved IDs (mutated by plugins)
    imdb_id: str | None = None
    tmdb_id: int | None = None
    trakt_id: int | None = None


@dataclass
class CanonicalItem:
    """Unified item representation for sync."""
    imdb_id: str | None = None
    tmdb_id: int | None = None
    title: str | None = None
    year: int | None = None
    media_type: str = "movie"  # "movie" or "show"
    service_ids: dict[str, Any] = field(default_factory=dict)
    service_states: dict[str, dict] = field(default_factory=dict)


# ── Sub-Protocols (Capabilities) ────────────────────────────

@runtime_checkable
class Scrobbler(Protocol):
    """Can receive and process scrobble events."""

    async def on_event(self, event: ScrobbleEvent, config: dict) -> dict:
        """Handle a scrobble event. Returns result dict."""
        ...


@runtime_checkable
class SyncSource(Protocol):
    """Can pull and push watch state for sync."""

    def pull(self, config: dict) -> list[CanonicalItem]:
        """Pull all items from this service."""
        ...

    def push_change(self, canonical: CanonicalItem, field: str, value: Any, config: dict) -> None:
        """Push a single field change to this service."""
        ...

    def supports_field(self, field: str) -> bool:
        """Whether this service supports the given field (watched/rating/favorite)."""
        ...


@runtime_checkable
class Exporter(Protocol):
    """Can export user data from this service."""

    def export(self, config: dict) -> dict:
        """Export all user data. Returns service-specific dict."""
        ...


@runtime_checkable
class MetadataSource(Protocol):
    """Can enrich item metadata (ratings, genres, posters)."""

    def enrich(self, item_id: str, media_type: str, config: dict) -> dict | None:
        """Enrich an item. Returns metadata dict or None."""
        ...


@runtime_checkable
class CookieMapper(Protocol):
    """Maps browser cookies to addon config keys."""

    service_name: str

    def map(self, cookies: dict, tokens: dict) -> dict:
        """Map browser cookies/tokens to config keys."""
        ...


# ── Main Addon Protocol ─────────────────────────────────────

@runtime_checkable
class Addon(Protocol):
    """Base protocol every service addon must implement."""

    name: str                           # "Trakt", "Plex", etc.
    slug: str                           # "trakt", "plex", etc.
    description: str

    # Auth & Config
    config_schema: dict                 # JSON Schema for user config fields
    config_keys: list[str]              # Flat list of config keys this addon reads

    def is_configured(self, config: dict) -> bool:
        """Check if this addon has enough config to operate."""
        ...

    def verify(self, config: dict) -> VerifyResult:
        """Check if credentials are valid."""
        ...

    # Capabilities (all optional — None means not supported)
    catalogs: list[CatalogDef] | None = None
    scrobbler: Scrobbler | None = None
    sync_source: SyncSource | None = None
    exporter: Exporter | None = None
    metadata: MetadataSource | None = None
    cookie_mapper: CookieMapper | None = None

    def get_catalog(self, catalog_id: str, media_type: str, skip: int,
                    config: dict, genre: str | None = None) -> list[dict]:
        """Fetch catalog items. Only called if catalogs is not None."""
        ...
