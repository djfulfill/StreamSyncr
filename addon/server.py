import json
import os
import secrets
import sys
import threading
import logging
from urllib.parse import parse_qs

import httpx
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse, HTMLResponse, RedirectResponse

from config import config
from catalogs import trakt, tmdb, anilist, simkl, wetrakr, sofasidekick, mdblist, imdb
from metadata import enricher
from streams import resolver
from auth.configure import CONFIGURE_HTML
from auth.oauth import (
    _consume_state as oauth_consume_state,
    _callback_html as oauth_callback_html,
    trakt_authorize_url, trakt_exchange_code,
    simkl_authorize_url, simkl_exchange_code,
    anilist_authorize_url, anilist_exchange_code,
)
from export import export_all
from db import config_store, resume_store

# ── Core Platform (addon/plugin registry) ───────────────────
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from core.registry import registry as core_registry

logger = logging.getLogger("streamsyncr")

app = FastAPI(title="StreamSyncr Stremio Addon", cors_origins=["http://localhost:3030", "http://127.0.0.1:3030"])


@app.on_event("startup")
async def _discover_addons():
    """Discover and register all addon packages on startup."""
    core_registry.discover()
    logger.info(f"Core registry: {len(core_registry.addons)} addons loaded")

# Persistent config store (SQLite-backed, survives restarts)
_store_lock = threading.Lock()

# Extension connection state
_extension_connected = False
_extension_last_seen: float = 0


def _generate_token() -> str:
    return secrets.token_hex(32)


@app.post("/api/save-config")
async def save_config(request: Request):
    """Store config server-side, return an opaque token.
    The token is used in the manifest URL instead of raw API keys."""
    body = await request.json()
    config_data = body.get("config", {})
    token = _generate_token()
    with _store_lock:
        config_store[token] = config_data
    return JSONResponse({"token": token})


@app.get("/api/export/{token}")
async def export_data(token: str):
    """Export all user data from connected services."""
    with _store_lock:
        user_config = _config_store.get(token, {})
    if not user_config:
        return JSONResponse({"error": "Invalid token"}, status_code=401)

    result = export_all(user_config)
    return JSONResponse(result)


# ── Core Platform Registry Endpoints ────────────────────────

@app.get("/api/registry/addons")
async def list_addons():
    """List all discovered addons and their capabilities."""
    addons = []
    for addon in core_registry.addons:
        info = {
            "name": addon.name,
            "slug": addon.slug,
            "description": addon.description,
            "capabilities": [],
        }
        if addon.catalogs:
            info["capabilities"].append("catalogs")
            info["catalogs"] = [{"id": c.id, "label": c.label, "auth": c.auth}
                                for c in addon.catalogs]
        if addon.scrobbler:
            info["capabilities"].append("scrobbler")
        if addon.sync_source:
            info["capabilities"].append("sync")
        if addon.exporter:
            info["capabilities"].append("export")
        if addon.metadata:
            info["capabilities"].append("metadata")
        addons.append(info)
    return JSONResponse({"addons": addons, "total": len(addons)})


@app.post("/api/registry/verify")
async def registry_verify(request: Request):
    """Verify credentials for all configured addons (registry-powered)."""
    body = await request.json()
    cfg = body.get("config", {})
    results = core_registry.verify_all(cfg)
    serialized = {}
    for slug, result in results.items():
        serialized[slug] = {
            "status": result.status,
            "error": result.error,
            "details": result.details,
        }
    return JSONResponse(serialized)


@app.post("/api/registry/export")
async def registry_export(request: Request):
    """Export data from all configured addons (registry-powered)."""
    body = await request.json()
    cfg = body.get("config", {})
    result = core_registry.export_all(cfg)
    return JSONResponse(result)


@app.get("/api/registry/catalogs/{config_token}")
async def registry_catalogs(config_token: str, request: Request):
    """Get dynamic catalog list from all configured addons."""
    user_config = _resolve_user_config(config_token, request)
    catalogs = core_registry.build_manifest_catalogs(user_config)
    return JSONResponse({"catalogs": catalogs})


@app.post("/api/registry/scrobble")
async def registry_scrobble(request: Request):
    """Scrobble via registry (replaces hardcoded fan-out)."""
    body = await request.json()
    cfg = body.get("config", {})
    from core.addons.base import ScrobbleEvent
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
    results = await core_registry.scrobble(event, cfg)
    return JSONResponse(results)


@app.post("/api/registry/sync/pull")
async def registry_sync_pull(request: Request):
    """Pull items from all configured sync sources."""
    body = await request.json()
    cfg = body.get("config", {})
    items = core_registry.sync_pull(cfg)
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


@app.get("/api/debug/imdb/{token}")
async def debug_imdb(token: str):
    """Debug IMDb credentials."""
    with _store_lock:
        user_config = config_store.get(token, {})
    if not user_config:
        return JSONResponse({"error": "Invalid token"}, status_code=401)

    has_full_cookies = bool(user_config.get("imdb_full_cookies"))

    result = {
        "has_full_cookies": has_full_cookies,
        "all_set": has_full_cookies,
    }

    if result["all_set"]:
        try:
            from imdb_api import IMDbClient
            client = IMDbClient(full_cookies=user_config["imdb_full_cookies"])
            lists = client.get_lists()
            result["lists_count"] = len(lists)
            result["lists"] = [{"id": l.get("id"), "name": l.get("name", {}).get("originalText", "")} for l in lists[:5]]

            recent = client.get_recently_viewed(count=5)
            result["recently_viewed_count"] = len(recent)
            result["recently_viewed"] = [{"id": i.get("id"), "title": i.get("titleText", {}).get("text", "")} for i in recent[:5]]

            result["status"] = "connected"
        except Exception as e:
            result["status"] = "error"
            result["error"] = str(e)
    else:
        result["status"] = "missing_credentials"

    return JSONResponse(result)


@app.get("/api/config/{token}/status")
async def get_config_status(token: str):
    """Return which services are configured for a given token."""
    with _store_lock:
        user_config = config_store.get(token, {})
    if not user_config:
        return JSONResponse({"error": "Invalid token"}, status_code=401)

    def has(key):
        val = user_config.get(key)
        return bool(val and val.strip() if isinstance(val, str) else bool(val))

    return JSONResponse({
        "debrid": {
            "realdebrid": has("realdebrid_key"),
            "torbox": has("torbox_key"),
            "alldebrid": has("alldebrid_key"),
        },
        "stream_backend": {
            "sootio_enabled": has("sootio_enabled") and user_config.get("sootio_enabled", "true") != "false",
            "sootio_url": has("sootio_url"),
        },
        "tracking": {
            "trakt": has("trakt_token"),
            "wetrakr": has("wetrakr_access_token"),
            "tmdb": has("tmdb_api_key"),
            "imdb": has("imdb_full_cookies") or has("imdb_api_key"),
            "anilist": has("anilist_token"),
            "simkl": has("simkl_client_id"),
            "mdblist": has("mdblist_api_key"),
            "letterboxd": has("letterboxd_cookies"),
            "sofasidekick": has("sofasidekick_session_id"),
        },
        "servers": {
            "plex": has("plex_token"),
            "jellyfin": has("jellyfin_api_key"),
            "kodi": has("kodi_url"),
        },
    })


def get_user_config(request: Request) -> dict:
    """Extract user config from the request.
    First checks the path token (secure), then falls back to legacy ?config= query param."""
    # Check if we already resolved config from a path token (attached by middleware or route)
    config_str = request.query_params.get("config", "{}")
    try:
        return json.loads(config_str)
    except json.JSONDecodeError:
        return {}


CATALOG_HANDLERS = {
    "trakt-trending": lambda t, s, c, g: trakt.trending_movies(skip=s, api_key=c.get("trakt_client_id",""), token=None) if t == "movie" else trakt.trending_shows(skip=s, api_key=c.get("trakt_client_id",""), token=None),
    "trakt-popular": lambda t, s, c, g: trakt.popular_movies(skip=s, api_key=c.get("trakt_client_id",""), token=None) if t == "movie" else trakt.popular_shows(skip=s, api_key=c.get("trakt_client_id",""), token=None),
    "trakt-trending-shows": lambda t, s, c, g: trakt.trending_shows(skip=s, api_key=c.get("trakt_client_id",""), token=None),
    "trakt-popular-shows": lambda t, s, c, g: trakt.popular_shows(skip=s, api_key=c.get("trakt_client_id",""), token=None),
    "tmdb-trending": lambda t, s, c, g: tmdb.trending_movies(api_key=c.get("tmdb_api_key",""), skip=s),
    "tmdb-popular": lambda t, s, c, g: tmdb.popular_movies(api_key=c.get("tmdb_api_key",""), skip=s),
    "tmdb-top-rated": lambda t, s, c, g: tmdb.top_rated_movies(api_key=c.get("tmdb_api_key",""), skip=s),
    "tmdb-now-playing": lambda t, s, c, g: tmdb.now_playing(api_key=c.get("tmdb_api_key",""), skip=s),
    "tmdb-upcoming": lambda t, s, c, g: tmdb.upcoming(api_key=c.get("tmdb_api_key",""), skip=s),
    "tmdb-trending-tv": lambda t, s, c, g: tmdb.trending_tv(api_key=c.get("tmdb_api_key",""), skip=s),
    "tmdb-popular-tv": lambda t, s, c, g: tmdb.popular_tv(api_key=c.get("tmdb_api_key",""), skip=s),
    "simkl-trending": lambda t, s, c, g: simkl.trending_movies(skip=s, user_config=c),
    "simkl-popular": lambda t, s, c, g: simkl.popular_movies(skip=s, user_config=c),
    "simkl-trending-shows": lambda t, s, c, g: simkl.trending_shows(skip=s, user_config=c),
    "simkl-popular-shows": lambda t, s, c, g: simkl.popular_shows(skip=s, user_config=c),
    "simkl-anime-trending": lambda t, s, c, g: simkl.trending_anime(skip=s, user_config=c),
    "simkl-anime-popular": lambda t, s, c, g: simkl.popular_anime(skip=s, user_config=c),
    "simkl-watchlist": lambda t, s, c, g: simkl.user_watchlist(skip=s, user_config=c),
    "simkl-watching": lambda t, s, c, g: simkl.user_watching(skip=s, user_config=c),
    "simkl-completed": lambda t, s, c, g: simkl.user_completed(skip=s, user_config=c),
    "anilist-trending": lambda t, s, c, g: anilist.trending(skip=s),
    "anilist-popular": lambda t, s, c, g: anilist.popular(skip=s),
    "wetrakr-favorites": lambda t, s, c, g: wetrakr.favorites(c, skip=s),
    "wetrakr-watchlist": lambda t, s, c, g: wetrakr.watchlist(c, skip=s),
    "wetrakr-watching": lambda t, s, c, g: wetrakr.watching(c, skip=s),
    "wetrakr-ratings": lambda t, s, c, g: wetrakr.ratings(c, skip=s),
    "sofasidekick-shows": lambda t, s, c, g: sofasidekick.shows(c, skip=s),
    "sofasidekick-movies": lambda t, s, c, g: sofasidekick.movies(c, skip=s),
    "sofasidekick-watchlist": lambda t, s, c, g: sofasidekick.watchlist(c, skip=s),
    "sofasidekick-upcoming": lambda t, s, c, g: sofasidekick.upcoming(c, skip=s),
    "mdblist-search": lambda t, s, c, g: mdblist.search(g or "", api_key=c.get("mdblist_api_key",""), skip=s) if g else [],
    "imdb-lists": lambda t, s, c, g: imdb.lists(skip=s, user_config=c),
    "imdb-recently-viewed": lambda t, s, c, g: imdb.recently_viewed(skip=s, user_config=c),
    "imdb-ratings": lambda t, s, c, g: imdb.ratings(skip=s, user_config=c),
}


def _resolve_user_config(config_token: str | None, request: Request) -> dict:
    """Resolve user config: token from path takes priority (secure store),
    falls back to legacy ?config= query param."""
    if config_token:
        with _store_lock:
            cfg = config_store.get(config_token)
        if cfg is not None:
            return cfg
    config_str = request.query_params.get("config", "{}")
    try:
        return json.loads(config_str)
    except json.JSONDecodeError:
        return {}


@app.get("/manifest.json")
@app.get("/{config_token}/manifest.json")
async def manifest(request: Request, config_token: str | None = None):
    manifest_path = os.path.join(os.path.dirname(__file__), "manifest.json")
    with open(manifest_path) as f:
        data = json.load(f)
    user_config = _resolve_user_config(config_token, request)
    return _build_manifest(data, user_config)


def _build_manifest(data: dict, user_config: dict) -> JSONResponse:
    # Build the full list of available catalogs (base + dynamic)
    available = list(data.get("catalogs", []))

    # Dynamic catalogs from connected services
    dynamic_catalogs = []

    if user_config.get("trakt_token"):
        dynamic_catalogs.extend([
            {"type": "movie", "id": "trakt-watchlist", "name": "My Trakt Watchlist"},
            {"type": "movie", "id": "trakt-favorites", "name": "My Trakt Favorites"},
            {"type": "series", "id": "trakt-watchlist-shows", "name": "My Trakt Watchlist Shows"},
        ])

    if user_config.get("wetrakr_access_token"):
        dynamic_catalogs.extend([
            {"type": "movie", "id": "wetrakr-favorites", "name": "WeTrakr Favorites"},
            {"type": "movie", "id": "wetrakr-watchlist", "name": "WeTrakr Plan to Watch"},
            {"type": "series", "id": "wetrakr-watching", "name": "WeTrakr Watching"},
            {"type": "movie", "id": "wetrakr-ratings", "name": "WeTrakr Ratings"},
        ])

    if user_config.get("sofasidekick_session_id"):
        dynamic_catalogs.extend([
            {"type": "series", "id": "sofasidekick-shows", "name": "Sofa Sidekick Shows"},
            {"type": "movie", "id": "sofasidekick-movies", "name": "Sofa Sidekick Movies"},
            {"type": "movie", "id": "sofasidekick-watchlist", "name": "Sofa Sidekick Watchlist"},
            {"type": "series", "id": "sofasidekick-upcoming", "name": "Sofa Sidekick Upcoming"},
        ])

    if user_config.get("mdblist_api_key"):
        try:
            user_lists = mdblist.user_lists(api_key=user_config["mdblist_api_key"])
            for lst in user_lists[:20]:
                dynamic_catalogs.append({
                    "type": lst["type"],
                    "id": f"mdblist-list-{lst['id']}",
                    "name": f"MDBList: {lst['name']}",
                })
        except Exception:
            pass

    if user_config.get("imdb_full_cookies"):
        dynamic_catalogs.extend([
            {"type": "movie", "id": "imdb-lists", "name": "IMDb Lists"},
            {"type": "movie", "id": "imdb-recently-viewed", "name": "IMDb Recently Viewed"},
            {"type": "movie", "id": "imdb-ratings", "name": "IMDb Ratings"},
        ])

    if user_config.get("simkl_access_token"):
        dynamic_catalogs.extend([
            {"type": "movie", "id": "simkl-watchlist", "name": "My Simkl Watchlist"},
            {"type": "series", "id": "simkl-watching", "name": "My Simkl Watching"},
            {"type": "movie", "id": "simkl-completed", "name": "My Simkl Completed"},
        ])

    available.extend(dynamic_catalogs)

    # If user has a custom catalog order, apply it
    custom_order = user_config.get("catalog_order", [])
    if custom_order:
        # Build ordered list: catalogs in custom_order first, then any remaining
        by_id = {c["id"]: c for c in available}
        ordered = []
        seen = set()
        for cat_id in custom_order:
            if cat_id in by_id:
                ordered.append(by_id[cat_id])
                seen.add(cat_id)
        # Append any catalogs not in the custom order
        for c in available:
            if c["id"] not in seen:
                ordered.append(c)
                seen.add(c["id"])
        data["catalogs"] = ordered
    else:
        data["catalogs"] = available

    # If user has disabled specific catalogs, filter them out
    disabled = user_config.get("disabled_catalogs", [])
    if disabled:
        data["catalogs"] = [c for c in data["catalogs"] if c["id"] not in disabled]

    return JSONResponse(data)


@app.get("/catalog/{catalog_type}/{catalog_id}.json")
async def catalog(catalog_type: str, catalog_id: str, request: Request):
    user_config = get_user_config(request)
    return await _handle_catalog(catalog_type, catalog_id, request, user_config)


@app.get("/catalog/{catalog_type}/{catalog_id}/{extra}.json")
async def catalog_with_extra(catalog_type: str, catalog_id: str, extra: str, request: Request):
    user_config = get_user_config(request)
    return await _handle_catalog_with_extra(catalog_type, catalog_id, extra, request, user_config)


@app.get("/stream/{stream_type}/{stream_id}.json")
async def stream(stream_type: str, stream_id: str, request: Request):
    user_config = get_user_config(request)
    return await _handle_stream(stream_type, stream_id, request, user_config)


# --- Token-prefixed routes (secure: config lives server-side) ---

@app.get("/{config_token}/catalog/{catalog_type}/{catalog_id}.json")
async def catalog_token(config_token: str, catalog_type: str, catalog_id: str, request: Request):
    user_config = _resolve_user_config(config_token, request)
    return await _handle_catalog(catalog_type, catalog_id, request, user_config)


@app.get("/{config_token}/catalog/{catalog_type}/{catalog_id}/{extra}.json")
async def catalog_with_extra_token(config_token: str, catalog_type: str, catalog_id: str, extra: str, request: Request):
    user_config = _resolve_user_config(config_token, request)
    return await _handle_catalog_with_extra(catalog_type, catalog_id, extra, request, user_config)


@app.get("/{config_token}/stream/{stream_type}/{stream_id}.json")
async def stream_token(config_token: str, stream_type: str, stream_id: str, request: Request):
    user_config = _resolve_user_config(config_token, request)
    return await _handle_stream(stream_type, stream_id, request, user_config)


# --- Handler implementations ---

async def _handle_catalog(catalog_type: str, catalog_id: str, request: Request, user_config: dict):
    extra = request.query_params.get("extra", "")
    skip = 0
    genre = None
    sort = None
    if extra:
        params = parse_qs(extra)
        skip = int(params.get("skip", [0])[0])
        genre = params.get("genre", [None])[0]
        sort = params.get("sort", [None])[0]

    # User-specific catalogs
    if catalog_id in ("trakt-watchlist", "trakt-favorites", "trakt-watchlist-shows"):
        return await _trakt_user_catalog(catalog_type, catalog_id, skip, sort, user_config)

    # MDBList dynamic list catalogs
    if catalog_id.startswith("mdblist-list-"):
        list_id = int(catalog_id.replace("mdblist-list-", ""))
        try:
            items = mdblist.list_items(list_id, api_key=user_config.get("mdblist_api_key", ""), skip=skip)
            return JSONResponse({"metas": items})
        except Exception as e:
            return JSONResponse({"metas": [], "error": str(e)}, status_code=500)

    handler = CATALOG_HANDLERS.get(catalog_id)
    if handler:
        try:
            items = handler(catalog_type, skip, user_config, genre)
            return JSONResponse({"metas": items})
        except Exception as e:
            return JSONResponse({"metas": [], "error": str(e)}, status_code=500)

    return JSONResponse({"metas": []}, status_code=404)


async def _trakt_user_catalog(catalog_type: str, catalog_id: str, skip: int, sort: str, user_config: dict):
    api_key = user_config.get("trakt_client_id", os.environ.get("TRAKT_API_KEY", ""))
    token = user_config.get("trakt_token", "")
    username = user_config.get("trakt_username", "")

    if not api_key:
        return JSONResponse({"metas": [], "error": "Trakt client_id not configured — add trakt_client_id to config or set TRAKT_API_KEY env var"}, status_code=400)

    try:
        from trakt_api import TraktClient
        # When using username-based endpoints (public), don't send the
        # OAuth token — it may be expired and cause 401. The API key
        # alone is sufficient for /users/{username}/watchlist etc.
        if username:
            client = TraktClient(api_key=api_key, token=None)
        else:
            client = TraktClient(api_key=api_key, token=token or None)

        if catalog_id == "trakt-watchlist":
            items = client.watchlist(media_type="movies", username=username or None)
            media_type = "movie"
        elif catalog_id == "trakt-favorites":
            items = client.get_favorites(username=username or None)
            media_type = "movie"
        else:
            items = client.watchlist(media_type="shows", username=username or None)
            media_type = "series"

        if sort and items:
            sort_key = sort.replace(":", "").replace(" ", "_").lower()
            reverse = "desc" in sort_key
            if "title" in sort_key:
                items.sort(key=lambda x: (x.get("movie") or x.get("show") or x).get("title", ""), reverse=reverse)
            elif "year" in sort_key or "released" in sort_key:
                items.sort(key=lambda x: (x.get("movie") or x.get("show") or x).get("year", 0), reverse=reverse)
            elif "rating" in sort_key:
                items.sort(key=lambda x: (x.get("movie") or x.get("show") or x).get("rating", 0), reverse=reverse)
            elif "added" in sort_key:
                items.sort(key=lambda x: x.get("listed_at", ""), reverse=reverse)

        metas = []
        for item in items[skip:skip + 20]:
            obj = item.get("movie") or item.get("show") or item
            ids = obj.get("ids", {})
            imdb = ids.get("imdb", "")
            imdb_id = f"tt{imdb}" if imdb and not imdb.startswith("tt") else imdb
            metas.append({
                "id": imdb_id or str(ids.get("trakt", "")),
                "type": media_type,
                "name": obj.get("title", ""),
                "year": obj.get("year"),
                "poster": obj.get("poster"),
                "imdb_id": imdb_id,
                "tmdb_id": ids.get("tmdb"),
            })

        return JSONResponse({"metas": metas})
    except Exception as e:
        return JSONResponse({"metas": [], "error": str(e)}, status_code=500)


async def _handle_catalog_with_extra(catalog_type: str, catalog_id: str, extra: str, request: Request, user_config: dict):
    params = parse_qs(extra)
    search = params.get("search", [None])[0]
    skip = int(params.get("skip", [0])[0])
    genre = params.get("genre", [None])[0]
    sort = params.get("sort", [None])[0]
    search = params.get("search", [None])[0]
    skip = int(params.get("skip", [0])[0])
    genre = params.get("genre", [None])[0]
    sort = params.get("sort", [None])[0]

    if search and catalog_id.startswith("tmdb-"):
        try:
            from tmdb_api import TMDBClient
            tmdb_client = TMDBClient()
            if catalog_type == "movie":
                results = tmdb_client.search_movie(search)
            else:
                results = tmdb_client.search_tv(search)
            metas = [{
                "id": str(r.get("id")),
                "type": catalog_type,
                "name": r.get("title") or r.get("name", ""),
                "year": _extract_year(r),
                "poster": _img_url(r.get("poster_path")) if r.get("poster_path") else None,
            } for r in results[:20]]
            return JSONResponse({"metas": metas})
        except Exception as e:
            return JSONResponse({"metas": [], "error": str(e)}, status_code=500)

    # MDBList search
    if search and catalog_id.startswith("mdblist-"):
        try:
            items = mdblist.search(search, api_key=user_config.get("mdblist_api_key", ""), skip=skip)
            return JSONResponse({"metas": items})
        except Exception as e:
            return JSONResponse({"metas": [], "error": str(e)}, status_code=500)

    handler = CATALOG_HANDLERS.get(catalog_id)
    if handler:
        try:
            items = handler(catalog_type, skip, user_config, genre)
            return JSONResponse({"metas": items})
        except Exception as e:
            return JSONResponse({"metas": [], "error": str(e)}, status_code=500)

    return JSONResponse({"metas": []}, status_code=404)


@app.get("/meta/{meta_type}/{meta_id}.json")
async def meta(meta_type: str, meta_id: str, request: Request):
    return await _handle_meta(meta_type, meta_id, get_user_config(request))


@app.get("/{config_token}/meta/{meta_type}/{meta_id}.json")
async def meta_token(config_token: str, meta_type: str, meta_id: str, request: Request):
    user_config = _resolve_user_config(config_token, request)
    return await _handle_meta(meta_type, meta_id, user_config)


async def _handle_meta(meta_type: str, meta_id: str, user_config: dict):
    try:
        # Multi-source enricher: routes to preferred provider with fallback chain
        result = enricher.enrich(meta_id, meta_type, user_config)
        if result:
            return JSONResponse({"meta": result})

        return JSONResponse({"meta": {}}, status_code=404)
    except Exception as e:
        return JSONResponse({"meta": {}, "error": str(e)}, status_code=500)


async def _handle_stream(stream_type: str, stream_id: str, request: Request, user_config: dict):
    try:
        streams = await resolver.resolve_streams(stream_type, stream_id, user_config)
        return JSONResponse({"streams": streams})
    except Exception as e:
        return JSONResponse({"streams": [], "error": str(e)}, status_code=500)


@app.get("/configure")
async def configure():
    return HTMLResponse(CONFIGURE_HTML)


# ── OAuth Endpoints (one-click service connection) ──────────

@app.get("/api/oauth/{service}/authorize")
async def oauth_authorize(service: str):
    """Returns the OAuth authorization URL for the given service.
    The configure page redirects the user here first, then to the service."""
    auth_funcs = {
        "trakt": trakt_authorize_url,
        "simkl": simkl_authorize_url,
        "anilist": anilist_authorize_url,
    }
    func = auth_funcs.get(service)
    if not func:
        return JSONResponse({"error": f"Unknown service: {service}"}, status_code=400)
    url, error = func()
    if error:
        return JSONResponse({"error": error}, status_code=500)
    return RedirectResponse(url)


@app.get("/api/oauth/{service}/callback")
async def oauth_callback(service: str, code: str = "", state: str = ""):
    """OAuth callback. Verifies state, exchanges code for token,
    and returns an HTML page that sends the token to the opener window."""
    verified_service = oauth_consume_state(state)
    if not verified_service or verified_service != service:
        return HTMLResponse(oauth_callback_html(service, "", "", error="Invalid or expired state token"))

    exchange_funcs = {
        "trakt": (trakt_exchange_code, "trakt_token"),
        "simkl": (simkl_exchange_code, "simkl_client_id"),
        "anilist": (anilist_exchange_code, "anilist_token"),
    }
    entry = exchange_funcs.get(service)
    if not entry:
        return HTMLResponse(oauth_callback_html(service, "", "", error=f"Unknown service: {service}"))

    exchange, field_id = entry
    token, error = exchange(code)
    if error:
        return HTMLResponse(oauth_callback_html(service, "", field_id, error=error))

    return HTMLResponse(oauth_callback_html(service, token, field_id))


# ── Chrome Extension Endpoints ─────────────────────────────────

@app.post("/api/extension/cookies")
async def extension_cookies(request: Request):
    """Receive cookies from the Chrome extension.
    The extension posts extracted cookies for a service, and we store them
    in the in-memory config store."""
    import time
    global _extension_connected, _extension_last_seen

    body = await request.json()
    service = body.get("service")
    cookies = body.get("cookies", {})
    tokens = body.get("tokens", {})
    valid = body.get("valid", False)

    if not service:
        return JSONResponse({"error": "Missing 'service' field"}, status_code=400)

    _extension_connected = True
    _extension_last_seen = time.time()

    # Map service cookies to config format.
    # The mapper receives the cookies dict; for services that store auth in
    # localStorage (wetrakr, trakt, anilist, simkl), we also pass tokens so the
    # mapper can extract username/client_id/etc.
    mapper_ctx = dict(cookies)
    if tokens:
        mapper_ctx["tokens"] = tokens
        # Also flatten token keys into the top level for easy .get() access
        for k, v in tokens.items():
            if k not in mapper_ctx:
                mapper_ctx[k] = v

    # Map service cookies to config format
    def _trakt_mapper(c):
        """Extract Trakt config from cookies + tokens.

        Trakt auth comes from two sources:
        1. Cookies (trakt-oidc-auth) — web session, not an API token
        2. Tokens (access_token, client_id) — from localStorage via content script

        The cookie token is NOT a valid API bearer token, but we store it
        as trakt_cf_clearance for Cloudflare-protected web endpoints.
        The real API token comes from the tokens dict (OAuth2 flow).
        """
        result = {}
        # API token from tokens dict (set by content script or OAuth flow)
        token = (c.get("access_token", "") or
                 c.get("id_token", "") or
                 (c.get("tokens", {}).get("access_token", "") if isinstance(c.get("tokens"), dict) else "") or
                 (c.get("tokens", {}).get("id_token", "") if isinstance(c.get("tokens"), dict) else ""))
        if token:
            result["trakt_token"] = token

        client_id = (c.get("client_id", "") or
                     (c.get("tokens", {}).get("client_id", "") if isinstance(c.get("tokens"), dict) else ""))
        if client_id:
            result["trakt_client_id"] = client_id

        # cf_clearance cookie for Cloudflare-protected web endpoints
        cf = c.get("cf_clearance", "")
        if cf:
            result["trakt_cf_clearance"] = cf

        return result

    config_mapping = {
        "imdb": lambda c: {
            "imdb_full_cookies": "; ".join(f"{k}={v}" for k, v in c.items()),
            "imdb_session_id": c.get("session-id", ""),
            "imdb_at_main": c.get("at-main", ""),
            "imdb_session_token": c.get("session-token", ""),
            "imdb_ubid_main": c.get("ubid-main", ""),
            "imdb_sess_at_main": c.get("sess-at-main", ""),
        },
        "letterboxd": lambda c: {
            "letterboxd_cookies": "; ".join(f"{k}={v}" for k, v in c.items()),
            "letterboxd_session": c.get("letterboxd.user", ""),
            "letterboxd_csrf": c.get("com.xk72.webparts.csrf", ""),
        },
        "wetrakr": lambda c: {
            "wetrakr_access_token": c.get("wta_at", "") or c.get("access_token", ""),
            "wetrakr_refresh_token": c.get("wta_rt", "") or c.get("refresh_token", ""),
            "wetrakr_username": c.get("username", "") or (c.get("tokens", {}).get("username", "") if isinstance(c.get("tokens"), dict) else ""),
        },
        "sofasidekick": lambda c: {
            "sofasidekick_session_id": c.get("session_id", ""),
            "sofasidekick_cf_clearance": c.get("cf_clearance", ""),
            "sofasidekick_cf_bm": c.get("__cf_bm", ""),
        },
        "trakt": lambda c: _trakt_mapper(c),
        "anilist": lambda c: {
            "anilist_token": c.get("access_token", "") or (c.get("tokens", {}).get("access_token", "") if isinstance(c.get("tokens"), dict) else ""),
        },
        "simkl": lambda c: {
            "simkl_client_id": c.get("client_id", "") or (c.get("tokens", {}).get("idToState", {}).get("client_id", "") if isinstance(c.get("tokens"), dict) and isinstance(c.get("tokens", {}).get("idToState"), dict) else ""),
            "simkl_access_token": c.get("access_token", "") or (c.get("tokens", {}).get("idToState", {}).get("access_token", "") if isinstance(c.get("tokens"), dict) and isinstance(c.get("tokens", {}).get("idToState"), dict) else ""),
        },
        "netflix": lambda c: {
            "netflix_id": c.get("NetflixId", ""),
            "netflix_secure_id": c.get("SecureNetflixId", ""),
        },
        "primevideo": lambda c: {
            "primevideo_session_id": c.get("session-id", ""),
            "primevideo_at_main": c.get("at-main", ""),
        },
        "disneyplus": lambda c: {
            "disneyplus_ct": c.get("ct_", ""),
        },
        "max": lambda c: {
            "max_jwt": c.get("jwt", ""),
        },
    }

    mapper = config_mapping.get(service)
    if not mapper:
        return JSONResponse({"error": f"Unknown service: {service}"}, status_code=400)

    config_updates = mapper(mapper_ctx)

    # Store in the extension slot AND merge into all user config tokens
    with _store_lock:
        ext_key = "__extension__"
        if ext_key not in config_store:
            config_store[ext_key] = {}
        config_store.update(ext_key, config_updates)

        # Also merge into every user token so Stremio sees fresh cookies
        for tok in list(config_store.keys()):
            if tok == ext_key:
                continue
            existing = config_store.get(tok, {})
            if not existing:
                continue
            for key, value in config_updates.items():
                if value:  # Only set non-empty values
                    existing[key] = value
            config_store[tok] = existing

    return JSONResponse({
        "success": True,
        "service": service,
        "config_updates": config_updates,
    })


@app.get("/api/extension/status")
async def extension_status():
    """Check if the Chrome extension is connected and when it was last seen."""
    import time
    return JSONResponse({
        "connected": _extension_connected,
        "last_seen": _extension_last_seen,
        "age_seconds": time.time() - _extension_last_seen if _extension_last_seen else None,
    })


@app.post("/api/extension/connect")
async def extension_connect():
    """Extension registers itself as connected."""
    import time
    global _extension_connected, _extension_last_seen
    _extension_connected = True
    _extension_last_seen = time.time()
    return JSONResponse({"success": True, "message": "Extension connected"})


@app.get("/api/extension/config")
async def extension_config():
    """Get the current extension-sourced config (for the frontend to read)."""
    with _store_lock:
        config = config_store.get("__extension__", {})
    return JSONResponse({"config": config})


# ── Browser Cookie Loader (browser_cookie3) ──────────────────

@app.get("/api/browser-cookies/scan")
async def browser_cookies_scan():
    """Scan the local browser cookie database and return what's available.

    Does not modify any config — just reports what cookies were found.
    """
    from browser_cookies import load_browser_cookies
    try:
        results = load_browser_cookies()
    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=500)

    # Summarize for the response (don't expose raw cookie values)
    summary = {}
    for service_id, data in results.items():
        summary[service_id] = {
            "valid": data["valid"],
            "cookie_count": len(data["cookies"]),
            "missing": data.get("missing", []),
            "source": data.get("source", "browser"),
        }
    return JSONResponse({"services": summary})


@app.post("/api/browser-cookies/merge")
async def browser_cookies_merge(request: Request):
    """Scan browser cookies + extension data and merge into a user's config token.

    Body: {"token": "<config_token>"} or {"token": "all"} to merge into every token.
    """
    from browser_cookies import load_browser_cookies, merge_into_config, merge_extension_config

    body = await request.json()
    token = body.get("token", "all")

    # Load browser cookies
    try:
        browser_cookies = load_browser_cookies()
    except Exception as e:
        return JSONResponse({"error": f"Browser cookie scan failed: {e}"}, status_code=500)

    # Load extension-sourced config
    with _store_lock:
        ext_config = config_store.get("__extension__", {})

    # Determine which tokens to update
    if token == "all":
        tokens = list(config_store.keys())
    else:
        if token not in config_store:
            return JSONResponse({"error": "Invalid token"}, status_code=404)
        tokens = [token]

    updated = []
    with _store_lock:
        for tok in tokens:
            if tok == "__extension__":
                continue
            existing = config_store.get(tok, {})
            if not existing:
                continue

            # Merge: browser cookies first, then extension (extension wins on conflict)
            merged = merge_into_config(existing, browser_cookies)
            merged = merge_extension_config(merged, ext_config)

            config_store[tok] = merged
            updated.append(tok)

    return JSONResponse({
        "success": True,
        "tokens_updated": updated,
        "browser_services": list(browser_cookies.keys()),
        "extension_keys": len(ext_config),
    })


# ── Trakt Device Code Auth ────────────────────────────────────

@app.post("/api/trakt/device/start")
async def trakt_device_start(request: Request):
    """Start a Trakt device-code auth flow. Returns a URL + code for the user
    to visit, plus a device_code to poll for completion.

    Body: {"client_id": "<trakt_client_id>"}
    """
    from browser_cookies import trakt_device_flow

    body = await request.json()
    client_id = body.get("client_id", "")
    if not client_id:
        return JSONResponse({"error": "client_id required"}, status_code=400)

    try:
        result = trakt_device_flow(client_id)
        return JSONResponse(result)
    except Exception as e:
        return JSONResponse({"error": str(e)}, status_code=500)


@app.post("/api/trakt/device/poll")
async def trakt_device_poll_endpoint(request: Request):
    """Poll for a Trakt device-code token. Save the access_token to config.

    Body: {"client_id": "...", "client_secret": "...", "device_code": "...",
           "token": "<config_token>"}
    """
    from browser_cookies import trakt_device_poll as _poll

    body = await request.json()
    client_id = body.get("client_id", "")
    client_secret = body.get("client_secret", "")
    device_code = body.get("device_code", "")
    config_token = body.get("token", "")

    if not all([client_id, client_secret, device_code]):
        return JSONResponse({"error": "client_id, client_secret, device_code required"}, status_code=400)

    result = _poll(client_id, client_secret, device_code)

    if result.get("access_token"):
        # Save to config store
        with _store_lock:
            if config_token and config_token in config_store:
                cfg = config_store[config_token]
                cfg["trakt_token"] = result["access_token"]
                config_store[config_token] = cfg
            # Also save to extension slot
            ext = config_store.get("__extension__", {})
            ext["trakt_token"] = result["access_token"]
            config_store["__extension__"] = ext

        return JSONResponse({
            "success": True,
            "access_token": result["access_token"],
            "refresh_token": result.get("refresh_token", ""),
        })

    return JSONResponse(result)


# ── Catalog Preview with TMDB Posters ─────────────────────────

@app.get("/api/preview/{token}/catalog/{catalog_type}/{catalog_id}")
async def preview_catalog(token: str, catalog_type: str, catalog_id: str):
    """Fetch catalog items and enrich with TMDB poster URLs.

    Returns metas with poster URLs from TMDB image API, looked up by
    IMDb or TMDB ID. Used by the configure page for interactive preview.
    """
    with _store_lock:
        user_config = config_store.get(token, {})
    if not user_config:
        return JSONResponse({"error": "Invalid token"}, status_code=401)

    # Fetch catalog items using the existing handler logic
    metas = []
    error = None

    # User-specific catalogs (Trakt watchlist/favorites)
    if catalog_id in ("trakt-watchlist", "trakt-favorites", "trakt-watchlist-shows"):
        result = await _trakt_user_catalog(catalog_type, catalog_id, 0, None, user_config)
        import json as _json
        data = _json.loads(result.body)
        metas = data.get("metas", [])
        error = data.get("error")
    else:
        handler = CATALOG_HANDLERS.get(catalog_id)
        if handler:
            try:
                metas = handler(catalog_type, 0, user_config, None)
            except Exception as e:
                error = str(e)
        else:
            error = f"Unknown catalog: {catalog_id}"

    if not metas and error:
        return JSONResponse({"metas": [], "error": error})

    # Enrich with TMDB posters
    tmdb_key = user_config.get("tmdb_api_key", "")
    if tmdb_key and metas:
        from tmdb_api import TMDBClient
        tmdb = TMDBClient(api_key=tmdb_key)
        poster_quality = user_config.get("poster_quality", "w500")

        for meta in metas[:20]:
            if meta.get("poster"):
                continue

            imdb_id = meta.get("imdb_id", "")
            tmdb_id = meta.get("tmdb_id", "")

            try:
                if imdb_id and imdb_id.startswith("tt"):
                    result = tmdb.find_by_imdb(imdb_id)
                    if result and result.get("poster_path"):
                        meta["poster"] = tmdb.img_url(result["poster_path"], poster_quality)
            except Exception:
                pass

    return JSONResponse({"metas": metas[:20]})


# ── Service Verification ────────────────────────────────────

@app.post("/api/verify")
async def verify_services(request: Request):
    """Verify which configured services are actually reachable.
    Accepts raw config (pre-save) or a token (post-save)."""
    body = await request.json()
    config = body.get("config", {})

    results = {}

    # ── Debrid Services (API key auth) ────────────────────

    # Real-Debrid
    if config.get("realdebrid_key"):
        try:
            async with httpx.AsyncClient() as c:
                resp = await c.get(
                    "https://api.real-debrid.com/rest/1.0/user",
                    headers={"Authorization": f"Bearer {config['realdebrid_key']}"}
                )
                if resp.status_code == 200:
                    user = resp.json()
                    results["realdebrid"] = {"status": "ok", "username": user.get("username", "unknown")}
                else:
                    results["realdebrid"] = {"status": "error", "error": f"HTTP {resp.status_code}"}
        except Exception as e:
            results["realdebrid"] = {"status": "error", "error": str(e)}
    else:
        results["realdebrid"] = {"status": "not_configured"}

    # TorBox
    if config.get("torbox_key"):
        try:
            async with httpx.AsyncClient() as c:
                resp = await c.get(
                    "https://api.torbox.app/v1/api/user/me",
                    headers={"Authorization": f"Bearer {config['torbox_key']}"}
                )
                if resp.status_code == 200:
                    results["torbox"] = {"status": "ok"}
                else:
                    results["torbox"] = {"status": "error", "error": f"HTTP {resp.status_code}"}
        except Exception as e:
            results["torbox"] = {"status": "error", "error": str(e)}
    else:
        results["torbox"] = {"status": "not_configured"}

    # AllDebrid
    if config.get("alldebrid_key"):
        try:
            async with httpx.AsyncClient() as c:
                resp = await c.get(
                    "https://api.alldebrid.com/v2/user?agent=streamsyncr",
                    headers={"Authorization": f"Bearer {config['alldebrid_key']}"}
                )
                if resp.status_code == 200:
                    results["alldebrid"] = {"status": "ok"}
                else:
                    results["alldebrid"] = {"status": "error", "error": f"HTTP {resp.status_code}"}
        except Exception as e:
            results["alldebrid"] = {"status": "error", "error": str(e)}
    else:
        results["alldebrid"] = {"status": "not_configured"}

    # ── Sootio Stream Backend ────────────────────────────

    sootio_url = (config.get("sootio_url") or "http://localhost:55771").rstrip("/")
    try:
        async with httpx.AsyncClient() as c:
            resp = await c.get(f"{sootio_url}/manifest.json", timeout=5.0)
            if resp.status_code == 200:
                m = resp.json()
                results["sootio"] = {"status": "ok", "name": m.get("name", "Sootio"), "version": m.get("version", "?")}
            else:
                results["sootio"] = {"status": "error", "error": f"HTTP {resp.status_code}"}
    except Exception as e:
        results["sootio"] = {"status": "offline", "error": str(e)}

    # ── Tracking Services (OAuth / token auth) ────────────

    # Trakt — needs both token AND client_id
    if config.get("trakt_token") and config.get("trakt_client_id"):
        try:
            from trakt_api import TraktClient
            client = TraktClient(api_key=config["trakt_client_id"], token=config["trakt_token"])
            user = client.users_me()
            results["trakt"] = {"status": "ok", "username": user.get("username", "unknown")}
        except Exception as e:
            results["trakt"] = {"status": "error", "error": str(e)}
    elif config.get("trakt_token") or config.get("trakt_client_id"):
        results["trakt"] = {"status": "incomplete", "error": "Need both trakt_token and trakt_client_id"}
    else:
        results["trakt"] = {"status": "not_configured"}

    # TMDB
    if config.get("tmdb_api_key"):
        try:
            async with httpx.AsyncClient() as c:
                resp = await c.get(f"https://api.themoviedb.org/3/movie/550?api_key={config['tmdb_api_key']}")
                if resp.status_code == 200:
                    results["tmdb"] = {"status": "ok"}
                else:
                    results["tmdb"] = {"status": "error", "error": f"HTTP {resp.status_code}"}
        except Exception as e:
            results["tmdb"] = {"status": "error", "error": str(e)}
    else:
        results["tmdb"] = {"status": "not_configured"}

    # Simkl — client_id is public; just check it's valid format
    if config.get("simkl_client_id"):
        results["simkl"] = {"status": "ok", "note": "Client ID configured (public key)"}
    else:
        results["simkl"] = {"status": "not_configured"}

    # AniList
    if config.get("anilist_token"):
        try:
            async with httpx.AsyncClient() as c:
                resp = await c.post(
                    "https://graphql.anilist.co",
                    json={"query": "{ Viewer { name } }"},
                    headers={"Authorization": f"Bearer {config['anilist_token']}"}
                )
                if resp.status_code == 200:
                    data = resp.json()
                    username = data.get("data", {}).get("Viewer", {}).get("name", "unknown")
                    results["anilist"] = {"status": "ok", "username": username}
                else:
                    results["anilist"] = {"status": "error", "error": f"HTTP {resp.status_code}"}
        except Exception as e:
            results["anilist"] = {"status": "error", "error": str(e)}
    else:
        results["anilist"] = {"status": "not_configured", "note": "Public catalogs work without token"}

    # MDBList
    if config.get("mdblist_api_key"):
        try:
            async with httpx.AsyncClient() as c:
                resp = await c.get(f"https://api.mdblist.com/?apikey={config['mdblist_api_key']}")
                if resp.status_code == 200:
                    results["mdblist"] = {"status": "ok"}
                else:
                    results["mdblist"] = {"status": "error", "error": f"HTTP {resp.status_code}"}
        except Exception as e:
            results["mdblist"] = {"status": "error", "error": str(e)}
    else:
        results["mdblist"] = {"status": "not_configured"}

    # ── Cookie / Session Auth ─────────────────────────────

    # WeTrakr — needs username + access_token
    if config.get("wetrakr_access_token") and config.get("wetrakr_username"):
        try:
            async with httpx.AsyncClient() as c:
                resp = await c.get(
                    "https://wetrakr.com/api/v2/account/user",
                    headers={
                        "wetrakr-api-country": "US",
                        "wetrakr-api-language": "en-US",
                        "Cookie": f"wta_at={config['wetrakr_access_token']}"
                    }
                )
                if resp.status_code == 200:
                    results["wetrakr"] = {"status": "ok"}
                else:
                    results["wetrakr"] = {"status": "error", "error": f"HTTP {resp.status_code}"}
        except Exception as e:
            results["wetrakr"] = {"status": "error", "error": str(e)}
    elif config.get("wetrakr_access_token") or config.get("wetrakr_username"):
        results["wetrakr"] = {"status": "incomplete", "error": "Need both wetrakr_username and wetrakr_access_token"}
    else:
        results["wetrakr"] = {"status": "not_configured"}

    # IMDb — cookie-based
    if config.get("imdb_full_cookies"):
        try:
            from imdb_api import IMDbClient
            client = IMDbClient(full_cookies=config["imdb_full_cookies"])
            lists = client.get_lists()
            results["imdb"] = {"status": "ok", "lists_count": len(lists)}
        except Exception as e:
            results["imdb"] = {"status": "error", "error": str(e)}
    elif config.get("imdb_api_key"):
        results["imdb"] = {"status": "partial", "note": "API key set, but lists/ratings need cookies"}
    else:
        results["imdb"] = {"status": "not_configured"}

    # Letterboxd — needs cookies + CSRF
    if config.get("letterboxd_cookies") and config.get("letterboxd_csrf"):
        try:
            from letterboxd_api import LetterboxdClient
            client = LetterboxdClient(
                cookies=config["letterboxd_cookies"],
                csrf_token=config["letterboxd_csrf"]
            )
            client.search_film("test")
            results["letterboxd"] = {"status": "ok"}
        except Exception as e:
            results["letterboxd"] = {"status": "error", "error": str(e)}
    elif config.get("letterboxd_cookies") or config.get("letterboxd_csrf"):
        results["letterboxd"] = {"status": "incomplete", "error": "Need both letterboxd_cookies and letterboxd_csrf"}
    else:
        results["letterboxd"] = {"status": "not_configured"}

    # Sofa Sidekick — session cookies
    if config.get("sofasidekick_session_id"):
        try:
            from sofasidekick_api import SofaSidekickClient
            client = SofaSidekickClient(
                session_id=config["sofasidekick_session_id"],
                cf_clearance=config.get("sofasidekick_cf_clearance"),
                cf_bm=config.get("sofasidekick_cf_bm"),
            )
            # NOTE: /shows is Cloudflare-blocked — verify via /movies instead
            client.get_movies()
            results["sofasidekick"] = {"status": "ok"}
        except Exception as e:
            results["sofasidekick"] = {"status": "error", "error": str(e)}
    else:
        results["sofasidekick"] = {"status": "not_configured"}

    # ── Media Servers (URL + token/key auth) ──────────────

    # Plex — needs both token AND url
    if config.get("plex_token") and config.get("plex_url"):
        try:
            async with httpx.AsyncClient() as c:
                resp = await c.get(
                    f"{config['plex_url']}/library/sections",
                    headers={"X-Plex-Token": config["plex_token"]},
                    timeout=5.0
                )
                if resp.status_code == 200:
                    results["plex"] = {"status": "ok"}
                else:
                    results["plex"] = {"status": "error", "error": f"HTTP {resp.status_code}"}
        except Exception as e:
            results["plex"] = {"status": "error", "error": str(e)}
    elif config.get("plex_token") or config.get("plex_url"):
        results["plex"] = {"status": "incomplete", "error": "Need both plex_token and plex_url"}
    else:
        results["plex"] = {"status": "not_configured"}

    # Jellyfin — needs both api_key AND url
    if config.get("jellyfin_api_key") and config.get("jellyfin_url"):
        try:
            async with httpx.AsyncClient() as c:
                resp = await c.get(
                    f"{config['jellyfin_url']}/System/Info",
                    headers={"X-Emby-Token": config["jellyfin_api_key"]},
                    timeout=5.0
                )
                if resp.status_code == 200:
                    results["jellyfin"] = {"status": "ok"}
                else:
                    results["jellyfin"] = {"status": "error", "error": f"HTTP {resp.status_code}"}
        except Exception as e:
            results["jellyfin"] = {"status": "error", "error": str(e)}
    elif config.get("jellyfin_api_key") or config.get("jellyfin_url"):
        results["jellyfin"] = {"status": "incomplete", "error": "Need both jellyfin_api_key and jellyfin_url"}
    else:
        results["jellyfin"] = {"status": "not_configured"}

    # Kodi — JSON-RPC URL (optional username/password)
    if config.get("kodi_url"):
        try:
            from kodi_api import KodiClient
            client = KodiClient(
                base_url=config["kodi_url"],
                username=config.get("kodi_username"),
                password=config.get("kodi_password"),
            )
            client.ping()
            results["kodi"] = {"status": "ok"}
        except Exception as e:
            results["kodi"] = {"status": "error", "error": str(e)}
    else:
        results["kodi"] = {"status": "not_configured"}

    return JSONResponse(results)


@app.post("/api/services/health")
async def services_health(request: Request):
    """Check health of all services from frontend config.
    Accepts the raw streamsyncr_config from localStorage."""
    body = await request.json()
    config = body.get("config", {})

    results = {}

    def has(key):
        val = config.get(key)
        return bool(val and val.strip() if isinstance(val, str) else bool(val))

    # ── Debrid Services ──
    if has("realdebrid_key"):
        try:
            async with httpx.AsyncClient() as c:
                resp = await c.get(
                    "https://api.real-debrid.com/rest/1.0/user",
                    headers={"Authorization": f"Bearer {config['realdebrid_key']}"}
                )
                if resp.status_code == 200:
                    user = resp.json()
                    results["realdebrid"] = {"status": "ok", "username": user.get("username"), "premium": bool(user.get("premium"))}
                else:
                    results["realdebrid"] = {"status": "error", "error": f"HTTP {resp.status_code}"}
        except Exception as e:
            results["realdebrid"] = {"status": "error", "error": str(e)}
    else:
        results["realdebrid"] = {"status": "not_configured"}

    if has("torbox_key"):
        try:
            async with httpx.AsyncClient() as c:
                resp = await c.get(
                    "https://api.torbox.app/v1/api/user/me",
                    headers={"Authorization": f"Bearer {config['torbox_key']}"}
                )
                if resp.status_code == 200:
                    results["torbox"] = {"status": "ok"}
                else:
                    results["torbox"] = {"status": "error", "error": f"HTTP {resp.status_code}"}
        except Exception as e:
            results["torbox"] = {"status": "error", "error": str(e)}
    else:
        results["torbox"] = {"status": "not_configured"}

    if has("alldebrid_key"):
        try:
            async with httpx.AsyncClient() as c:
                resp = await c.get(
                    "https://api.alldebrid.com/v4/user?agent=streamsyncr",
                    headers={"Authorization": f"Bearer {config['alldebrid_key']}"}
                )
                if resp.status_code == 200:
                    data = resp.json().get("data", {}).get("user", {})
                    results["alldebrid"] = {"status": "ok", "username": data.get("username"), "premium": bool(data.get("isPremium"))}
                else:
                    results["alldebrid"] = {"status": "error", "error": f"HTTP {resp.status_code}"}
        except Exception as e:
            results["alldebrid"] = {"status": "error", "error": str(e)}
    else:
        results["alldebrid"] = {"status": "not_configured"}

    # ── Tracking Services ──
    if has("trakt_token") and has("trakt_client_id"):
        try:
            async with httpx.AsyncClient() as c:
                resp = await c.get(
                    "https://api.trakt.tv/users/me",
                    headers={
                        "Authorization": f"Bearer {config['trakt_token']}",
                        "trakt-api-version": "2",
                        "trakt-api-key": config["trakt_client_id"],
                    }
                )
                if resp.status_code == 200:
                    user = resp.json()
                    results["trakt"] = {"status": "ok", "username": user.get("username")}
                else:
                    results["trakt"] = {"status": "error", "error": f"HTTP {resp.status_code}"}
        except Exception as e:
            results["trakt"] = {"status": "error", "error": str(e)}
    else:
        results["trakt"] = {"status": "not_configured"}

    if has("tmdb_api_key"):
        try:
            async with httpx.AsyncClient() as c:
                resp = await c.get(f"https://api.themoviedb.org/3/movie/550?api_key={config['tmdb_api_key']}")
                if resp.status_code == 200:
                    results["tmdb"] = {"status": "ok"}
                else:
                    results["tmdb"] = {"status": "error", "error": f"HTTP {resp.status_code}"}
        except Exception as e:
            results["tmdb"] = {"status": "error", "error": str(e)}
    else:
        results["tmdb"] = {"status": "not_configured"}

    if has("imdb_full_cookies"):
        try:
            from imdb_api import IMDbClient
            client = IMDbClient(full_cookies=config["imdb_full_cookies"])
            lists = client.get_lists()
            results["imdb"] = {"status": "ok", "lists_count": len(lists)}
        except Exception as e:
            results["imdb"] = {"status": "error", "error": str(e)}
    else:
        results["imdb"] = {"status": "not_configured"}

    if has("letterboxd_cookies") and has("letterboxd_csrf"):
        try:
            from letterboxd_api import LetterboxdClient
            client = LetterboxdClient(cookies=config["letterboxd_cookies"], csrf_token=config["letterboxd_csrf"])
            client.search_film("test")
            results["letterboxd"] = {"status": "ok"}
        except Exception as e:
            results["letterboxd"] = {"status": "error", "error": str(e)}
    else:
        results["letterboxd"] = {"status": "not_configured"}

    if has("sofasidekick_session_id"):
        try:
            from sofasidekick_api import SofaSidekickClient
            client = SofaSidekickClient(
                session_id=config["sofasidekick_session_id"],
                cf_clearance=config.get("sofasidekick_cf_clearance"),
                cf_bm=config.get("sofasidekick_cf_bm"),
            )
            client.get_movies()
            results["sofasidekick"] = {"status": "ok"}
        except Exception as e:
            results["sofasidekick"] = {"status": "error", "error": str(e)}
    else:
        results["sofasidekick"] = {"status": "not_configured"}

    if has("mdblist_api_key"):
        try:
            async with httpx.AsyncClient() as c:
                resp = await c.get(f"https://mdblist.com/api/?apikey={config['mdblist_api_key']}&i=tt0133093&type=imdb")
                if resp.status_code == 200:
                    results["mdblist"] = {"status": "ok"}
                else:
                    results["mdblist"] = {"status": "error", "error": f"HTTP {resp.status_code}"}
        except Exception as e:
            results["mdblist"] = {"status": "error", "error": str(e)}
    else:
        results["mdblist"] = {"status": "not_configured"}

    if has("simkl_client_id"):
        results["simkl"] = {"status": "ok", "note": "Client ID set (public key)"}
    else:
        results["simkl"] = {"status": "not_configured"}

    if has("wetrakr_access_token") and has("wetrakr_username"):
        try:
            async with httpx.AsyncClient() as c:
                resp = await c.get(
                    "https://wetrakr.com/proxy/frontend/users/" + config["wetrakr_username"],
                    headers={
                        "wetrakr-api-country": "US",
                        "wetrakr-api-language": "en-US",
                        "Cookie": f"wta_at={config['wetrakr_access_token']}"
                    }
                )
                if resp.status_code == 200:
                    results["wetrakr"] = {"status": "ok"}
                else:
                    results["wetrakr"] = {"status": "error", "error": f"HTTP {resp.status_code}"}
        except Exception as e:
            results["wetrakr"] = {"status": "error", "error": str(e)}
    else:
        results["wetrakr"] = {"status": "not_configured"}

    # ── Media Servers ──
    if has("plex_token") and has("plex_url"):
        try:
            async with httpx.AsyncClient() as c:
                resp = await c.get(
                    f"{config['plex_url']}/library/sections",
                    headers={"X-Plex-Token": config["plex_token"]},
                    timeout=5.0
                )
                if resp.status_code == 200:
                    results["plex"] = {"status": "ok"}
                else:
                    results["plex"] = {"status": "error", "error": f"HTTP {resp.status_code}"}
        except Exception as e:
            results["plex"] = {"status": "error", "error": str(e)}
    else:
        results["plex"] = {"status": "not_configured"}

    if has("jellyfin_api_key") and has("jellyfin_url"):
        try:
            async with httpx.AsyncClient() as c:
                resp = await c.get(
                    f"{config['jellyfin_url']}/System/Info",
                    headers={"X-Emby-Token": config["jellyfin_api_key"]},
                    timeout=5.0
                )
                if resp.status_code == 200:
                    results["jellyfin"] = {"status": "ok"}
                else:
                    results["jellyfin"] = {"status": "error", "error": f"HTTP {resp.status_code}"}
        except Exception as e:
            results["jellyfin"] = {"status": "error", "error": str(e)}
    else:
        results["jellyfin"] = {"status": "not_configured"}

    if has("kodi_url"):
        try:
            from kodi_api import KodiClient
            client = KodiClient(base_url=config["kodi_url"])
            client.ping()
            results["kodi"] = {"status": "ok"}
        except Exception as e:
            results["kodi"] = {"status": "error", "error": str(e)}
    else:
        results["kodi"] = {"status": "not_configured"}

    if has("anilist_token"):
        try:
            async with httpx.AsyncClient() as c:
                resp = await c.post(
                    "https://graphql.anilist.co",
                    json={"query": "{ Viewer { name } }"},
                    headers={"Authorization": f"Bearer {config['anilist_token']}"}
                )
                if resp.status_code == 200:
                    username = resp.json().get("data", {}).get("Viewer", {}).get("name")
                    results["anilist"] = {"status": "ok", "username": username}
                else:
                    results["anilist"] = {"status": "error", "error": f"HTTP {resp.status_code}"}
        except Exception as e:
            results["anilist"] = {"status": "error", "error": str(e)}
    else:
        results["anilist"] = {"status": "not_configured"}

    return JSONResponse(results)


# ── Real-Time Scrobbling ────────────────────────────────────

from fastapi import WebSocket, WebSocketDisconnect
from scrobble import scrobble_manager, ScrobbleEvent
import time as _time


@app.websocket("/ws/scrobble")
async def websocket_scrobble(websocket: WebSocket, token: str = None):
    """Real-time bidirectional scrobble channel.

    Clients connect with ?token=<config_token> query param.
    Messages are JSON with format:
        {"action": "start|pause|resume|stop|heartbeat", "item_id": "tt1234567", ...}
    """
    if not token or token not in config_store:
        await websocket.close(code=4001, reason="Invalid token")
        return

    await scrobble_manager.connect(websocket, token)
    try:
        while True:
            data = await websocket.receive_json()
            event = ScrobbleEvent(
                action=data.get("action", "heartbeat"),
                item_id=data.get("item_id", ""),
                media_type=data.get("media_type", "movie"),
                progress=data.get("progress", 0),
                title=data.get("title", ""),
                year=data.get("year"),
                season=data.get("season"),
                episode=data.get("episode"),
                client_type=data.get("client_type", "unknown"),
                position_seconds=data.get("position_seconds"),
                total_seconds=data.get("total_seconds"),
            )
            with _store_lock:
                await scrobble_manager.handle_event(token, event, config_store)
    except WebSocketDisconnect:
        await scrobble_manager.disconnect(token)
    except Exception as e:
        logger.warning(f"WebSocket scrobble error: {e}")
        await scrobble_manager.disconnect(token)


@app.post("/api/scrobble")
async def scrobble_rest(request: Request):
    """HTTP fallback for clients that can't use WebSocket.
    Kodi addon currently calls this endpoint."""
    body = await request.json()

    # Extract token from header or use extension default
    token = request.headers.get("X-Config-Token", "__extension__")

    # Build event from body
    progress = body.get("progress", 0)
    action = body.get("action", "")
    if not action:
        action = "stop" if progress >= 90 else "heartbeat"

    event = ScrobbleEvent(
        action=action,
        item_id=body.get("imdb_id", body.get("item_id", "")),
        media_type=body.get("media_type", "movie"),
        progress=progress,
        title=body.get("title", ""),
        year=body.get("year"),
        season=body.get("season"),
        episode=body.get("episode"),
        client_type=body.get("client_type", "kodi"),
    )

    with _store_lock:
        # Ensure token exists in config store
        if token not in config_store:
            config_store[token] = {}
        await scrobble_manager.handle_event(token, event, config_store)

    return JSONResponse({"status": "ok"})


@app.get("/api/scrobble/now-playing")
async def now_playing():
    """Get currently playing sessions across all clients."""
    sessions = []
    for token, session in scrobble_manager.active_sessions.items():
        if session.is_playing:
            sessions.append({
                "token": token[:8] + "...",
                "client_type": session.client_type,
                "title": session.title,
                "year": session.year,
                "progress": session.progress,
                "is_playing": session.is_playing,
                "media_type": session.media_type,
                "started_at": session.started_at,
            })
    return JSONResponse({"sessions": sessions})


# ── Resume Position Sync ────────────────────────────────────

@app.get("/api/resume/{item_id}")
async def get_resume(item_id: str, token: str = "", media_type: str = "movie",
                     season: int = None, episode: int = None):
    """Get resume position for an item."""
    if not token:
        return JSONResponse({"resume": None})
    pos = resume_store.get_position(token, item_id, media_type, season, episode)
    return JSONResponse({"resume": pos})


@app.post("/api/resume")
async def save_resume(request: Request):
    """Save resume position (called by Kodi on heartbeat/stop)."""
    body = await request.json()
    token = request.headers.get("X-Config-Token", "")
    if not token:
        return JSONResponse({"error": "Missing token"}, status_code=400)

    resume_store.save_position(
        token=token,
        item_id=body.get("item_id", ""),
        position_seconds=body.get("position_seconds", 0),
        total_seconds=body.get("total_seconds", 0),
        media_type=body.get("media_type", "movie"),
        season=body.get("season"),
        episode=body.get("episode"),
        title=body.get("title", ""),
        year=body.get("year"),
    )
    return JSONResponse({"status": "ok"})


@app.get("/api/resume/all")
async def get_all_resumes(token: str = ""):
    """Get all resume positions for a user (Kodi fetches on start)."""
    if not token:
        return JSONResponse({"positions": []})
    positions = resume_store.get_all_positions(token)
    return JSONResponse({"positions": positions})


@app.get("/")
async def root():
    return RedirectResponse("/manifest.json")


def _extract_year(item: dict) -> int:
    date = item.get("release_date") or item.get("first_air_date") or ""
    return int(date[:4]) if date else None


def _img_url(path: str, size: str = "w500") -> str:
    return f"https://image.tmdb.org/t/p/{size}{path}"


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host=config.host, port=config.port)
