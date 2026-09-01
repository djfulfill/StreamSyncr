"""Nuvio API endpoints for cross-compatibility.

Provides:
- /api/nuvio/manifest.json — Stremio addon manifest optimized for Nuvio
- /api/nuvio/plugin-manifest.json — Nuvio native plugin repository manifest
- /api/nuvio/providers/{name}.js — JavaScript providers for Nuvio's QuickJS runtime
- /api/nuvio/stream — Stream resolver proxy for Nuvio plugins
"""

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse, HTMLResponse
import importlib
import os

router = APIRouter(prefix="/api/nuvio", tags=["nuvio"])


@router.get("/manifest.json")
async def stremio_manifest_for_nuvio(request: Request):
    """Stremio addon manifest optimized for Nuvio.

    Add this URL in Nuvio: Settings > Addons > Install from URL.
    """
    from nuvio.manifest_generator import generate_stremio_manifest

    base_url = str(request.base_url).rstrip("/")
    manifest = generate_stremio_manifest({
        "base_url": base_url,
        "token": "",
    })
    return JSONResponse(content=manifest)


@router.get("/plugin-manifest.json")
async def nuvio_plugin_manifest(request: Request):
    """Nuvio native plugin repository manifest.

    Add this URL in Nuvio: Settings > Plugins > Add Repository.
    """
    from nuvio.manifest_generator import generate_nuvio_plugin_manifest

    base_url = str(request.base_url).rstrip("/")
    manifest = generate_nuvio_plugin_manifest(base_url)
    return JSONResponse(content=manifest)


@router.get("/providers/{provider_name}.js")
async def nuvio_provider_js(provider_name: str, request: Request):
    """Serve a Nuvio-compatible JavaScript provider.

    Nuvio fetches these files from the plugin manifest's filename field.
    """
    from nuvio.manifest_generator import generate_nuvio_provider_js

    # Try to load existing provider first
    provider_path = os.path.join(
        os.path.dirname(__file__), "..", "..", "nuvio", "providers", f"{provider_name}.js"
    )
    if os.path.exists(provider_path):
        with open(provider_path, "r") as f:
            content = f.read()
        return HTMLResponse(content=content, media_type="application/javascript")

    # Generate provider dynamically
    base_url = str(request.base_url).rstrip("/")
    content = generate_nuvio_provider_js(provider_name, base_url)
    return HTMLResponse(content=content, media_type="application/javascript")


@router.get("/stream")
async def nuvio_stream_proxy(
    request: Request,
    id: str = "",
    type: str = "movie",
    title: str = "",
    year: str = "",
    season: str = "",
    episode: str = "",
    config_token: str = "",
):
    """Stream resolver proxy for Nuvio plugins.

    Nuvio plugins call this endpoint to resolve streams via StreamSyncr's
    full plugin chain (scrapers → dedupe → debrid).
    """
    from core.registry import registry

    media_type = "series" if type == "tv" else "movie"

    config = {}
    if config_token:
        config["token"] = config_token

    streams = await registry.resolve_streams(
        media_type=media_type,
        imdb_id=id,
        config=config,
        season=int(season) if season else None,
        episode=int(episode) if episode else None,
    )

    return JSONResponse(content={"streams": streams})


@router.get("/catalog/{catalog_type}/{catalog_id}.json")
async def nuvio_catalog(
    catalog_type: str,
    catalog_id: str,
    request: Request,
    skip: int = 0,
    genre: str = "",
    config_token: str = "",
):
    """Catalog endpoint for Nuvio addon mode.

    Returns catalog data from StreamSyncr's configured addons.
    """
    from core.registry import registry

    config = {}
    if config_token:
        config["token"] = config_token

    items = await registry.get_catalog(
        catalog_type=catalog_type,
        catalog_id=catalog_id,
        skip=skip,
        genre=genre or None,
        config=config,
    )

    return JSONResponse(content={"metas": items})


@router.get("/health")
async def nuvio_health():
    """Health check for Nuvio integration."""
    from core.registry import registry

    return JSONResponse(content={
        "status": "ok",
        "version": "2.0.0",
        "addons_loaded": len(registry.addons),
        "plugins_loaded": len(registry.plugins),
        "addon_names": [a.name for a in registry.addons],
        "plugin_names": [p.name for p in registry.plugins],
        "endpoints": {
            "stremio_manifest": "/api/nuvio/manifest.json",
            "plugin_manifest": "/api/nuvio/plugin-manifest.json",
            "stream_proxy": "/api/nuvio/stream",
            "catalog": "/api/nuvio/catalog/{type}/{id}.json",
        },
    })
