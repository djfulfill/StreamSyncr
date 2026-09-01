"""Plugin registry — discovers and manages utility plugins."""

import importlib
import logging
import os
import pkgutil
from typing import Iterator

from .base import Plugin

logger = logging.getLogger("streamsyncr.plugins")


class PluginRegistry:
    """Discovers and manages plugins (scrapers, debrid providers, etc.)."""

    def __init__(self):
        self._plugins: dict[str, Plugin] = {}
        self._scrapers = []
        self._debrid = {}
        self._resolver = None

    def discover(self):
        """Scan core/plugins/ for all built-in plugins."""
        # Discover scrapers
        try:
            from .scrapers import TorrentioScraper, JackettScraper, BTDiggScraper, MagnetDLScraper
            for scraper_cls in [TorrentioScraper, JackettScraper, BTDiggScraper, MagnetDLScraper]:
                instance = scraper_cls()
                self._scrapers.append(instance)
                logger.info(f"Registered scraper: {instance.name} ({instance.category})")
        except Exception as e:
            logger.warning(f"Failed to load scrapers: {e}")

        # Discover debrid providers
        try:
            from .debrid import RealDebridProvider, TorBoxProvider, AllDebridProvider
            for provider_cls in [RealDebridProvider, TorBoxProvider, AllDebridProvider]:
                instance = provider_cls()
                self._debrid[instance.name] = instance
                logger.info(f"Registered debrid provider: {instance.name}")
        except Exception as e:
            logger.warning(f"Failed to load debrid providers: {e}")

        # Initialize and wire the stream resolver
        try:
            from .resolver import stream_resolver
            for scraper in self._scrapers:
                stream_resolver.register_scraper(scraper)
            for name, provider in self._debrid.items():
                stream_resolver.register_debrid(name, provider)
            self._resolver = stream_resolver
            self._plugins[stream_resolver.name] = stream_resolver
            logger.info(f"Stream resolver ready: {len(self._scrapers)} scrapers, {len(self._debrid)} debrid")
        except Exception as e:
            logger.warning(f"Failed to initialize stream resolver: {e}")

    def register(self, plugin: Plugin):
        """Manually register a plugin instance."""
        self._plugins[plugin.name] = plugin

    def register_scraper(self, scraper):
        """Manually register a scraper."""
        self._scrapers.append(scraper)
        if self._resolver:
            self._resolver.register_scraper(scraper)

    def register_debrid(self, name: str, provider):
        """Manually register a debrid provider."""
        self._debrid[name] = provider
        if self._resolver:
            self._resolver.register_debrid(name, provider)

    def get(self, name: str) -> Plugin | None:
        return self._plugins.get(name)

    def by_type(self, plugin_type: str) -> list[Plugin]:
        """Return all plugins of a given type."""
        return [p for p in self._plugins.values() if p.plugin_type == plugin_type]

    @property
    def scrapers(self):
        return list(self._scrapers)

    @property
    def debrid_providers(self):
        return dict(self._debrid)

    @property
    def resolver(self):
        return self._resolver

    def all(self) -> list[Plugin]:
        return list(self._plugins.values())

    def __iter__(self) -> Iterator[Plugin]:
        return iter(self._plugins.values())

    def __len__(self) -> int:
        return len(self._plugins)
