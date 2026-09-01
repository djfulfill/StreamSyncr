"""Central registry — ties addons and plugins together.

This is the main entry point for the StreamSyncr platform.
It replaces the hardcoded fan-out logic in server.py, scrobble.py, and engine.py.
"""

import logging
from typing import Any

from .addons import AddonRegistry
from .addons.base import (
    Addon, CanonicalItem, CatalogDef, ScrobbleEvent, VerifyResult,
)
from .plugins import PluginRegistry
from .plugins.base import Plugin, Stream, TorrentResult

logger = logging.getLogger("streamsyncr.registry")


class Registry:
    """Central registry that orchestrates addons and plugins."""

    def __init__(self):
        self.addons = AddonRegistry()
        self.plugins = PluginRegistry()

    def discover(self):
        """Discover all addons and plugins."""
        self.addons.discover()
        self.plugins.discover()
        logger.info(
            f"Registry ready: {len(self.addons)} addons, {len(self.plugins)} plugins"
        )

    # ── Catalog Resolution ───────────────────────────────────

    def get_catalog(self, catalog_id: str, media_type: str, skip: int,
                    config: dict, genre: str | None = None) -> list[dict]:
        """Resolve a catalog request by finding the right addon."""
        for addon in self.addons.with_catalogs(config):
            if any(c.id == catalog_id for c in addon.catalogs):
                try:
                    return addon.get_catalog(catalog_id, media_type, skip, config, genre)
                except Exception as e:
                    logger.warning(f"Catalog {catalog_id} failed from {addon.slug}: {e}")
                    return []
        return []

    def build_manifest_catalogs(self, config: dict) -> list[dict]:
        """Build Stremio catalog entries from all configured addons."""
        catalogs = []
        for addon in self.addons.with_catalogs(config):
            for cat in addon.catalogs:
                if cat.auth and not addon.is_configured(config):
                    continue
                for media_type in cat.type.split("|"):
                    catalogs.append({
                        "id": cat.id,
                        "type": media_type,
                        "name": f"{cat.label} ({addon.name})",
                    })
        return catalogs

    # ── Scrobble Fan-out ─────────────────────────────────────

    async def scrobble(self, event: ScrobbleEvent, config: dict) -> dict[str, Any]:
        """Fan-out a scrobble event to all configured addons."""
        results = {}
        for addon in self.addons.with_scrobbler(config):
            try:
                result = await addon.scrobbler.on_event(event, config)
                results[addon.slug] = result
            except Exception as e:
                results[addon.slug] = {"error": str(e)}
                logger.warning(f"Scrobble to {addon.slug} failed: {e}")
        return results

    # ── Sync ─────────────────────────────────────────────────

    def sync_pull(self, config: dict) -> list[CanonicalItem]:
        """Pull items from all configured sync sources."""
        all_items = []
        for addon in self.addons.with_sync_source(config):
            try:
                items = addon.sync_source.pull(config)
                all_items.extend(items)
            except Exception as e:
                logger.warning(f"Sync pull from {addon.slug} failed: {e}")
        return all_items

    def sync_push(self, canonical: CanonicalItem, field: str, value: Any,
                  config: dict) -> dict[str, Any]:
        """Push a change to all configured sync targets."""
        results = {}
        for addon in self.addons.with_sync_source(config):
            if addon.sync_source.supports_field(field):
                try:
                    addon.sync_source.push_change(canonical, field, value, config)
                    results[addon.slug] = "ok"
                except Exception as e:
                    results[addon.slug] = {"error": str(e)}
                    logger.warning(f"Sync push to {addon.slug} failed: {e}")
        return results

    # ── Export ───────────────────────────────────────────────

    def export_all(self, config: dict) -> dict:
        """Export data from all configured addons."""
        export = {"services": {}}
        for addon in self.addons.with_exporter(config):
            try:
                data = addon.exporter.export(config)
                export["services"][addon.slug] = data
            except Exception as e:
                export["services"][addon.slug] = {"error": str(e)}
        return export

    # ── Verification ─────────────────────────────────────────

    def verify_all(self, config: dict) -> dict[str, VerifyResult]:
        """Verify credentials for all configured addons."""
        results = {}
        for addon in self.addons:
            if addon.is_configured(config):
                try:
                    results[addon.slug] = addon.verify(config)
                except Exception as e:
                    results[addon.slug] = VerifyResult(status="error", error=str(e))
        return results

    # ── Stream Resolution ────────────────────────────────────

    def resolve_streams(self, media_type: str, item_id: str,
                        config: dict) -> list[Stream]:
        """Resolve streams using registered resolver plugins."""
        for plugin in self.plugins.by_type("resolver"):
            try:
                results = plugin.resolve(media_type, item_id, config)
                if results:
                    return results
            except Exception as e:
                logger.warning(f"Stream resolver {plugin.name} failed: {e}")
        return []

    # ── Metadata ─────────────────────────────────────────────

    def enrich_metadata(self, item_id: str, media_type: str,
                        config: dict) -> dict | None:
        """Enrich metadata using registered metadata addons."""
        for addon in self.addons.with_metadata(config):
            try:
                result = addon.metadata.enrich(item_id, media_type, config)
                if result:
                    return result
            except Exception as e:
                logger.warning(f"Metadata from {addon.slug} failed: {e}")
        return None


# ── Global Instance ─────────────────────────────────────────

registry = Registry()
