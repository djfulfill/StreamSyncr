import json
import os
import secrets
import threading
from urllib.parse import parse_qs

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse, HTMLResponse, RedirectResponse

from config import config
from catalogs import trakt, tmdb, anilist, simkl, wetrakr, sofasidekick, mdblist
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

app = FastAPI(title="StreamSyncr Stremio Addon")

# In-memory token → config store. Tokens are 64-char hex (32 random bytes).
# In production you'd use a DB/Redis so tokens survive restarts.
_config_store: dict[str, dict] = {}
_store_lock = threading.Lock()


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
        _config_store[token] = config_data
    return JSONResponse({"token": token})


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
    "trakt-trending": lambda t, s, c, g: trakt.trending_movies(skip=s, api_key=c.get("trakt_client_id",""), token=c.get("trakt_token","")) if t == "movie" else trakt.trending_shows(skip=s, api_key=c.get("trakt_client_id",""), token=c.get("trakt_token","")),
    "trakt-popular": lambda t, s, c, g: trakt.popular_movies(skip=s, api_key=c.get("trakt_client_id",""), token=c.get("trakt_token","")) if t == "movie" else trakt.popular_shows(skip=s, api_key=c.get("trakt_client_id",""), token=c.get("trakt_token","")),
    "trakt-trending-shows": lambda t, s, c, g: trakt.trending_shows(skip=s, api_key=c.get("trakt_client_id",""), token=c.get("trakt_token","")),
    "trakt-popular-shows": lambda t, s, c, g: trakt.popular_shows(skip=s, api_key=c.get("trakt_client_id",""), token=c.get("trakt_token","")),
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
}


def _resolve_user_config(config_token: str | None, request: Request) -> dict:
    """Resolve user config: token from path takes priority (secure store),
    falls back to legacy ?config= query param."""
    if config_token:
        with _store_lock:
            cfg = _config_store.get(config_token)
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

    if user_config.get("trakt_token"):
        data["catalogs"].extend([
            {"type": "movie", "id": "trakt-watchlist", "name": "My Trakt Watchlist"},
            {"type": "movie", "id": "trakt-favorites", "name": "My Trakt Favorites"},
            {"type": "series", "id": "trakt-watchlist-shows", "name": "My Trakt Watchlist Shows"},
        ])

    if user_config.get("wetrakr_access_token"):
        data["catalogs"].extend([
            {"type": "movie", "id": "wetrakr-favorites", "name": "WeTrakr Favorites"},
            {"type": "movie", "id": "wetrakr-watchlist", "name": "WeTrakr Plan to Watch"},
            {"type": "series", "id": "wetrakr-watching", "name": "WeTrakr Watching"},
            {"type": "movie", "id": "wetrakr-ratings", "name": "WeTrakr Ratings"},
        ])

    if user_config.get("sofasidekick_session_id"):
        data["catalogs"].extend([
            {"type": "series", "id": "sofasidekick-shows", "name": "Sofa Sidekick Shows"},
            {"type": "movie", "id": "sofasidekick-movies", "name": "Sofa Sidekick Movies"},
            {"type": "movie", "id": "sofasidekick-watchlist", "name": "Sofa Sidekick Watchlist"},
            {"type": "series", "id": "sofasidekick-upcoming", "name": "Sofa Sidekick Upcoming"},
        ])

    if user_config.get("mdblist_api_key"):
        try:
            user_lists = mdblist.user_lists(api_key=user_config["mdblist_api_key"])
            for lst in user_lists[:20]:
                catalog_id = f"mdblist-list-{lst['id']}"
                data["catalogs"].append({
                    "type": lst["type"],
                    "id": catalog_id,
                    "name": f"MDBList: {lst['name']}",
                })
        except Exception:
            pass

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
    token = user_config.get("trakt_token")
    api_key = user_config.get("trakt_client_id", os.environ.get("TRAKT_API_KEY", ""))
    if not token:
        return JSONResponse({"metas": [], "error": "Trakt token not configured"}, status_code=400)
    if not api_key:
        return JSONResponse({"metas": [], "error": "Trakt client_id not configured — add trakt_client_id to config or set TRAKT_API_KEY env var"}, status_code=400)

    try:
        from trakt_api import TraktClient
        client = TraktClient(api_key=api_key, token=token)

        if catalog_id == "trakt-watchlist":
            items = client.watchlist(media_type="movies")
            media_type = "movie"
        elif catalog_id == "trakt-favorites":
            items = client.get_favorites()
            media_type = "movie"
        else:
            items = client.watchlist(media_type="shows")
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
            metas.append({
                "id": f"tt{imdb}" if imdb else str(ids.get("trakt", "")),
                "type": media_type,
                "name": obj.get("title", ""),
                "year": obj.get("year"),
                "poster": obj.get("poster"),
            })

        return JSONResponse({"metas": metas})
    except Exception as e:
        return JSONResponse({"metas": [], "error": str(e)}, status_code=500)


@app.get("/catalog/{catalog_type}/{catalog_id}/{extra}.json")
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
    tmdb_key = user_config.get("tmdb_api_key", os.environ.get("TMDB_API_KEY", ""))
    try:
        if meta_id.startswith("tt"):
            from utils.id_mapping import imdb_to_tmdb
            tmdb_id = imdb_to_tmdb(meta_id)
            if tmdb_id:
                result = enricher.enrich(tmdb_id, meta_type, tmdb_key)
                if result:
                    return JSONResponse({"meta": result})

        if meta_id.isdigit():
            result = enricher.enrich(int(meta_id), meta_type, tmdb_key)
            if result:
                return JSONResponse({"meta": result})

        if meta_id.startswith("anilist:"):
            anime_id = int(meta_id.split(":")[1])
            from anilist_api import AniListClient
            client = AniListClient()
            item = client.get_anime(anime_id)
            if item:
                title = item.get("title", {})
                cover = item.get("coverImage", {})
                return JSONResponse({"meta": {
                    "id": meta_id,
                    "type": "series",
                    "name": title.get("english") or title.get("romaji", ""),
                    "poster": cover.get("large"),
                    "description": item.get("description"),
                    "genres": item.get("genres", []),
                    "imdb_rating": item.get("averageScore"),
                }})

        return JSONResponse({"meta": {}}, status_code=404)
    except Exception as e:
        return JSONResponse({"meta": {}, "error": str(e)}, status_code=500)


@app.get("/stream/{stream_type}/{stream_id}.json")
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
