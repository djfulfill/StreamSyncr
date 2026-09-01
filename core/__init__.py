"""StreamSyncr Core — Addon and Plugin platform."""

from .registry import Registry
from .addons.base import Addon, CatalogDef, VerifyResult, ScrobbleEvent
from .plugins.base import Plugin

__all__ = ["Registry", "Addon", "CatalogDef", "VerifyResult", "ScrobbleEvent", "Plugin"]
