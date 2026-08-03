"""
SyncEngine — bidirectional sync across streaming services.

Usage:
    from sync_engine import SyncEngine, ResolutionStrategy
    engine = SyncEngine(strategy=ResolutionStrategy.WATCHED_OVERRIDES)
    engine.register_service("trakt", trakt_client)
    engine.register_service("plex", plex_client)
    result = engine.sync()
"""

from .engine import SyncEngine, SyncResult, SyncItem
from .resolver import CanonicalItem, build_key, items_match, merge_items
from .resolution import ResolutionStrategy, resolve_all, resolve_watched, resolve_rating, resolve_favorite

__all__ = [
    "SyncEngine",
    "SyncResult",
    "SyncItem",
    "CanonicalItem",
    "ResolutionStrategy",
    "build_key",
    "items_match",
    "merge_items",
    "resolve_all",
    "resolve_watched",
    "resolve_rating",
    "resolve_favorite",
]
