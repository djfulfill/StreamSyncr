"""Plugin registry — discovers and manages utility plugins."""

import importlib
import json
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

    def discover(self):
        """Scan core/plugins/ for built-in plugin packages."""
        package_dir = os.path.dirname(__file__)
        for finder, name, is_pkg in pkgutil.iter_modules([package_dir]):
            if name.startswith("_") or name == "base":
                continue
            if not is_pkg:
                continue
            try:
                mod = importlib.import_module(f"core.plugins.{name}")
                plugin_cls = getattr(mod, "Plugin", None)
                if plugin_cls and plugin_cls is not Plugin:
                    instance = plugin_cls()
                    self._plugins[instance.name] = instance
                    logger.info(f"Registered plugin: {instance.name} ({instance.plugin_type})")
            except Exception as e:
                logger.warning(f"Failed to load plugin '{name}': {e}")

    def register(self, plugin: Plugin):
        """Manually register a plugin instance."""
        self._plugins[plugin.name] = plugin

    def get(self, name: str) -> Plugin | None:
        return self._plugins.get(name)

    def by_type(self, plugin_type: str) -> list[Plugin]:
        """Return all plugins of a given type."""
        return [p for p in self._plugins.values() if p.plugin_type == plugin_type]

    def all(self) -> list[Plugin]:
        return list(self._plugins.values())

    def __iter__(self) -> Iterator[Plugin]:
        return iter(self._plugins.values())

    def __len__(self) -> int:
        return len(self._plugins)
