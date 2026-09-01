"""Addon registry — discovers and manages service addons."""

import importlib
import logging
import os
import pkgutil
from typing import Iterator

from .base import Addon

logger = logging.getLogger("streamsyncr.addons")


class AddonRegistry:
    """Auto-discovers and manages addon packages under core/addons/."""

    def __init__(self):
        self._addons: dict[str, Addon] = {}

    def discover(self):
        """Scan core/addons/ for addon packages and register them."""
        package_dir = os.path.dirname(__file__)
        for finder, name, is_pkg in pkgutil.iter_modules([package_dir]):
            if name.startswith("_") or name == "base":
                continue
            if not is_pkg:
                continue
            try:
                mod = importlib.import_module(f"core.addons.{name}")
                addon_cls = getattr(mod, "Addon", None)
                if addon_cls is None:
                    # Try finding a class that implements the Addon protocol
                    for attr_name in dir(mod):
                        attr = getattr(mod, attr_name)
                        if isinstance(attr, type) and hasattr(attr, "slug") and attr is not Addon:
                            addon_cls = attr
                            break
                if addon_cls:
                    instance = addon_cls()
                    self._addons[instance.slug] = instance
                    logger.info(f"Registered addon: {instance.name} ({instance.slug})")
            except Exception as e:
                logger.warning(f"Failed to load addon '{name}': {e}")

    def register(self, addon: Addon):
        """Manually register an addon instance."""
        self._addons[addon.slug] = addon

    def get(self, slug: str) -> Addon | None:
        return self._addons.get(slug)

    def all(self) -> list[Addon]:
        return list(self._addons.values())

    def with_catalogs(self, config: dict) -> list[Addon]:
        """Return addons that have catalogs and are configured."""
        return [
            a for a in self._addons.values()
            if a.catalogs and a.is_configured(config)
        ]

    def with_scrobbler(self, config: dict) -> list[Addon]:
        """Return addons that have a scrobbler and are configured."""
        return [
            a for a in self._addons.values()
            if a.scrobbler and a.is_configured(config)
        ]

    def with_sync_source(self, config: dict) -> list[Addon]:
        """Return addons that have a sync source and are configured."""
        return [
            a for a in self._addons.values()
            if a.sync_source and a.is_configured(config)
        ]

    def with_exporter(self, config: dict) -> list[Addon]:
        """Return addons that have an exporter and are configured."""
        return [
            a for a in self._addons.values()
            if a.exporter and a.is_configured(config)
        ]

    def with_metadata(self, config: dict) -> list[Addon]:
        """Return addons that have a metadata source and are configured."""
        return [
            a for a in self._addons.values()
            if a.metadata and a.is_configured(config)
        ]

    def __iter__(self) -> Iterator[Addon]:
        return iter(self._addons.values())

    def __len__(self) -> int:
        return len(self._addons)
