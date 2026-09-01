"""Standalone REST API — works without Stremio.

Provides a clean JSON API for catalogs, streams, metadata, scrobble,
sync, and export. This is the foundation for future clients (mobile,
desktop, CLI, etc.).
"""

import logging
from typing import Any

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse

logger = logging.getLogger("streamsyncr.standalone")

router = APIRouter(prefix="/api/v1", tags=["standalone"])


# ── Catalogs ────────────────────────────────────────────────

@router.get("/catalogs")
async def list_catalogs(config_token: str = ""):
    """List all available catalogs from configured addons."""
    from core.registry import registry
    from addon.db import config_store

    config = config_store.get(config_token, {}) if config_token else {}
    catalogs = []
    for addon in registry.addons.with_catalogs(config):
        for cat in addon.catalogs:
            if cat.auth and not addon.is_configured(config):
                continue
            for media_type in cat.type.split("|"):
                catalogs.append({
                    "id": cat.id,
                    "type": media_type,
                    "name": f"{cat.label} ({addon.name})",
                    "service": addon.slug,
                    "auth_required": cat.auth,
                })
    return JSONResponse({"catalogs": catalogs, "total": len(catalogs)})


@router.get("/catalogs/{catalog_id}")
async def get_catalog(catalog_id: str, type: str = "movie",
                      skip: int = 0, genre: str = "",
                      config_token: str = ""):
    """Fetch items from a specific catalog."""
    from core.registry import registry
    from addon.db import config_store

    config = config_store.get(config_token, {}) if config_token else {}
    items = registry.get_catalog(catalog_id, type, skip, config, genre or None)
    return JSONResponse({
        "catalog_id": catalog_id,
        "type": type,
        "skip": skip,
        "items": items,
        "total": len(items),
    })


# ── Streams ─────────────────────────────────────────────────

@router.get("/streams/{media_type}/{item_id}")
async def get_streams(media_type: str, item_id: str, config_token: str = ""):
    """Resolve streams for an item (IMDb ID)."""
    from core.registry import registry
    from addon.db import config_store

    config = config_store.get(config_token, {}) if config_token else {}
    streams = registry.resolve_streams(media_type, item_id, config)
    result = []
    for s in streams:
        result.append({
            "name": s.name,
            "title": s.title,
            "url": s.url,
            "duration": s.duration,
        })
    return JSONResponse({
        "type": media_type,
        "id": item_id,
        "streams": result,
        "total": len(result),
    })


# ── Metadata ────────────────────────────────────────────────

@router.get("/meta/{media_type}/{item_id}")
async def get_meta(media_type: str, item_id: str, config_token: str = ""):
    """Get enriched metadata for an item."""
    from core.registry import registry
    from addon.db import config_store

    config = config_store.get(config_token, {}) if config_token else {}
    metadata = registry.enrich_metadata(item_id, media_type, config)
    if not metadata:
        return JSONResponse({"error": "No metadata available"}, status_code=404)
    return JSONResponse(metadata)


# ── Scrobble ────────────────────────────────────────────────

@router.post("/scrobble")
async def scrobble(request: Request):
    """Send a scrobble event to all connected services."""
    from core.registry import registry
    from core.addons.base import ScrobbleEvent
    from addon.db import config_store

    body = await request.json()
    config_token = body.get("config_token", "")
    config = config_store.get(config_token, {}) if config_token else body.get("config", {})

    event = ScrobbleEvent(
        action=body.get("action", "stop"),
        item_id=body.get("item_id", ""),
        media_type=body.get("media_type", "movie"),
        progress=body.get("progress", 0),
        title=body.get("title", ""),
        year=body.get("year"),
        season=body.get("season"),
        episode=body.get("episode"),
        client_type=body.get("client_type", "api"),
        imdb_id=body.get("imdb_id"),
        tmdb_id=body.get("tmdb_id"),
        trakt_id=body.get("trakt_id"),
    )
    results = await registry.scrobble(event, config)
    return JSONResponse(results)


# ── Sync ────────────────────────────────────────────────────

@router.post("/sync/pull")
async def sync_pull(request: Request):
    """Pull watch state from all connected services."""
    from core.registry import registry
    from addon.db import config_store

    body = await request.json()
    config_token = body.get("config_token", "")
    config = config_store.get(config_token, {}) if config_token else body.get("config", {})

    items = registry.sync_pull(config)
    result = []
    for item in items:
        result.append({
            "imdb_id": item.imdb_id,
            "tmdb_id": item.tmdb_id,
            "title": item.title,
            "year": item.year,
            "media_type": item.media_type,
            "service_ids": item.service_ids,
            "service_states": item.service_states,
        })
    return JSONResponse({"items": result, "total": len(result)})


@router.post("/sync/push")
async def sync_push(request: Request):
    """Push a change to all connected services."""
    from core.registry import registry
    from core.addons.base import CanonicalItem
    from addon.db import config_store

    body = await request.json()
    config_token = body.get("config_token", "")
    config = config_store.get(config_token, {}) if config_token else body.get("config", {})

    canonical = CanonicalItem(
        imdb_id=body.get("imdb_id"),
        tmdb_id=body.get("tmdb_id"),
        title=body.get("title"),
        year=body.get("year"),
        media_type=body.get("media_type", "movie"),
        service_ids=body.get("service_ids", {}),
    )
    results = registry.sync_push(
        canonical,
        body.get("field", "watched"),
        body.get("value", True),
        config,
    )
    return JSONResponse(results)


# ── Services ────────────────────────────────────────────────

@router.get("/services")
async def list_services(config_token: str = ""):
    """List all addons and their connection status."""
    from core.registry import registry
    from addon.db import config_store

    config = config_store.get(config_token, {}) if config_token else {}
    services = []
    for addon in registry.addons:
        is_configured = addon.is_configured(config)
        capabilities = []
        if getattr(addon, "catalogs", None):
            capabilities.append("catalogs")
        if getattr(addon, "scrobbler", None):
            capabilities.append("scrobble")
        if getattr(addon, "sync_source", None):
            capabilities.append("sync")
        if getattr(addon, "exporter", None):
            capabilities.append("export")
        if getattr(addon, "metadata", None):
            capabilities.append("metadata")
        services.append({
            "slug": addon.slug,
            "name": addon.name,
            "description": addon.description,
            "connected": is_configured,
            "capabilities": capabilities,
        })
    return JSONResponse({"services": services, "total": len(services)})


# ── Export ──────────────────────────────────────────────────

@router.post("/export")
async def export_data(request: Request):
    """Export all user data from connected services."""
    from core.registry import registry
    from addon.db import config_store

    body = await request.json()
    config_token = body.get("config_token", "")
    config = config_store.get(config_token, {}) if config_token else body.get("config", {})

    result = registry.export_all(config)
    return JSONResponse(result)


# ── Health ──────────────────────────────────────────────────

@router.get("/health")
async def health():
    """API health check."""
    return JSONResponse({
        "status": "ok",
        "version": "2.0.0",
        "mode": "standalone",
    })
