"""Nuvio integration — manifest generators and API endpoints.

Supports both Nuvio addon mode (Stremio-compatible) and
Nuvio plugin mode (native QuickJS providers).
"""

import json
import os
from typing import Any


def generate_stremio_manifest(config: dict = None) -> dict:
    """Generate a Stremio-compatible manifest optimized for Nuvio.

    This is the manifest Nuvio reads when StreamSyncr is installed
    as an addon (Settings > Addons > Add Addon).
    """
    config = config or {}
    base_url = config.get("base_url", "http://localhost:7800")

    catalogs = _build_catalogs(config)

    return {
        "id": f"com.streamsyncr.{config.get('token', 'default')}",
        "version": "2.0.0",
        "name": "StreamSyncr",
        "description": "Unified streaming tracker — 11 services, 33 catalogs, real-time sync",
        "logo": "https://raw.githubusercontent.com/djfulfill/StreamSyncr/master/StreamSyncr-logo.png",
        "resources": ["catalog", "stream", "meta"],
        "types": ["movie", "series"],
        "catalogs": catalogs,
        "behaviorHints": {
            "configurable": True,
            "configurationRequired": False,
        },
        # Nuvio-specific config block
        "stremioAddonsConfig": {
            "user_data": config.get("token", ""),
        },
    }


def generate_nuvio_plugin_manifest(base_url: str = "http://localhost:7800") -> dict:
    """Generate a Nuvio plugin repository manifest.

    This is the manifest users add in Nuvio's plugin section
    (Settings > Content & Discovery > Plugins > Add Repository).
    """
    return {
        "id": "com.streamsyncr.providers",
        "name": "StreamSyncr Providers",
        "description": "Unified streaming providers — scrapers from 11+ services via StreamSyncr backend",
        "version": "2.0.0",
        "author": "StreamSyncr",
        "logo": "https://raw.githubusercontent.com/djfulfill/StreamSyncr/master/StreamSyncr-logo.png",
        "providers": [
            {
                "id": "streamsyncr-torrentio",
                "name": "StreamSyncr • Torrentio",
                "description": "Multi-source torrent search (14+ scrapers)",
                "version": "2.0.0",
                "author": "StreamSyncr",
                "supportedTypes": ["movie", "tv"],
                "filename": "providers/torrentio.js",
                "enabled": True,
                "formats": ["mkv", "mp4"],
                "contentLanguage": ["en"],
            },
            {
                "id": "streamsyncr-jackett",
                "name": "StreamSyncr • Jackett",
                "description": "Self-hosted Jackett instance search",
                "version": "2.0.0",
                "author": "StreamSyncr",
                "supportedTypes": ["movie", "tv"],
                "filename": "providers/jackett.js",
                "enabled": False,
                "formats": ["mkv", "mp4"],
                "contentLanguage": ["en"],
            },
            {
                "id": "streamsyncr-btdig",
                "name": "StreamSyncr • BTDigg",
                "description": "DHT search engine (free, no auth)",
                "version": "2.0.0",
                "author": "StreamSyncr",
                "supportedTypes": ["movie", "tv"],
                "filename": "providers/btdig.js",
                "enabled": True,
                "formats": ["mkv", "mp4"],
                "contentLanguage": ["en"],
            },
            {
                "id": "streamsyncr-magnetdl",
                "name": "StreamSyncr • MagnetDL",
                "description": "Magnet link aggregator (free, no auth)",
                "version": "2.0.0",
                "author": "StreamSyncr",
                "supportedTypes": ["movie", "tv"],
                "filename": "providers/magnetdl.js",
                "enabled": True,
                "formats": ["mkv", "mp4"],
                "contentLanguage": ["en"],
            },
            {
                "id": "streamsyncr-metadata",
                "name": "StreamSyncr • Metadata",
                "description": "Enriched metadata from TMDB, AniList, Simkl",
                "version": "2.0.0",
                "author": "StreamSyncr",
                "supportedTypes": ["movie", "tv"],
                "filename": "providers/metadata.js",
                "enabled": True,
                "contentLanguage": ["en"],
            },
        ],
    }


def _build_catalogs(config: dict) -> list[dict]:
    """Build Stremio catalog entries from configured addons."""
    from core.registry import registry

    catalogs = []
    for addon in registry.addons:
        if not getattr(addon, "catalogs", None):
            continue
        if not addon.is_configured(config):
            continue
        for cat in addon.catalogs:
            if cat.auth and not addon.is_configured(config):
                continue
            for media_type in cat.type.split("|"):
                stremio_type = "series" if media_type == "series" else "movie"
                catalogs.append({
                    "id": cat.id,
                    "type": stremio_type,
                    "name": f"{cat.label} ({addon.name})",
                })
    return catalogs


def generate_nuvio_provider_js(scraper_name: str, base_url: str = "http://localhost:7800") -> str:
    """Generate a Nuvio-compatible JavaScript provider for a scraper."""
    return f"""/**
 * StreamSyncr {scraper_name.title()} Provider for Nuvio
 * 
 * Auto-generated by StreamSyncr.
 * Runs in Nuvio's QuickJS sandbox.
 */

const BASE_URL = "{base_url}";

async function getStreams(id, type, title, year, season, episode) {{
  try {{
    const mediaType = type === "tv" ? "series" : type;
    const imdbId = id || "";
    
    const url = `${{BASE_URL}}/api/v1/streams/${{mediaType}}/${{imdbId}}`;
    
    const response = await fetch(url, {{
      method: "GET",
      headers: {{
        "Content-Type": "application/json",
        "User-Agent": "Nuvio-StreamSyncr/2.0",
      }},
    }});
    
    if (!response.ok) return [];
    
    const data = await response.json();
    return (data.streams || []).map((stream) => ({{
      name: stream.name || "StreamSyncr",
      title: stream.title || "Unknown",
      url: stream.url,
      behaviorHints: {{
        bingeGroup: `streamsyncr-{scraper_name}-${{id}}`,
      }},
    }}));
  }} catch (error) {{
    console.error("StreamSyncr {scraper_name.title()} error:", error);
    return [];
  }}
}}

if (typeof globalThis !== "undefined") {{
  globalThis.getStreams = getStreams;
}}
"""
