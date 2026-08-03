import json
import os
from urllib.parse import parse_qs

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse, HTMLResponse, RedirectResponse

from config import config
from catalogs import trakt, tmdb, anilist, simkl, wetrakr, sofasidekick
from metadata import enricher
from streams import resolver
from auth.configure import CONFIGURE_HTML

app = FastAPI(title="StreamSyncr Stremio Addon")


def get_user_config(request: Request) -> dict:
    config_str = request.query_params.get("config", "{}")
    try:
        return json.loads(config_str)
    except json.JSONDecodeError:
        return {}


CATALOG_HANDLERS = {
    "trakt-trending": lambda t, s, c: trakt.trending_movies(skip=s) if t == "movie" else trakt.trending_shows(skip=s),
    "trakt-popular": lambda t, s, c: trakt.popular_movies(skip=s) if t == "movie" else trakt.popular_shows(skip=s),
    "trakt-trending-shows": lambda t, s, c: trakt.trending_shows(skip=s),
    "trakt-popular-shows": lambda t, s, c: trakt.popular_shows(skip=s),
    "tmdb-trending": lambda t, s, c: tmdb.trending_movies(skip=s),
    "tmdb-popular": lambda t, s, c: tmdb.popular_movies(skip=s),
    "tmdb-top-rated": lambda t, s, c: tmdb.top_rated_movies(skip=s),
    "tmdb-now-playing": lambda t, s, c: tmdb.now_playing(skip=s),
    "tmdb-upcoming": lambda t, s, c: tmdb.upcoming(skip=s),
    "tmdb-trending-tv": lambda t, s, c: tmdb.trending_tv(skip=s),
    "tmdb-popular-tv": lambda t, s, c: tmdb.popular_tv(skip=s),
    "simkl-trending": lambda t, s, c: simkl.trending_movies(skip=s),
    "simkl-popular": lambda t, s, c: simkl.popular_movies(skip=s),
    "simkl-trending-shows": lambda t, s, c: simkl.trending_shows(skip=s),
    "simkl-popular-shows": lambda t, s, c: simkl.popular_shows(skip=s),
    "anilist-trending": lambda t, s, c: anilist.trending(skip=s),
    "anilist-popular": lambda t, s, c: anilist.popular(skip=s),
    "wetrakr-favorites": lambda t, s, c: wetrakr.favorites(c, skip=s),
    "wetrakr-watchlist": lambda t, s, c: wetrakr.watchlist(c, skip=s),
    "wetrakr-watching": lambda t, s, c: wetrakr.watching(c, skip=s),
    "wetrakr-ratings": lambda t, s, c: wetrakr.ratings(c, skip=s),
    "sofasidekick-shows": lambda t, s, c: sofasidekick.shows(c, skip=s),
    "sofasidekick-movies": lambda t, s, c: sofasidekick.movies(c, skip=s),
    "sofasidekick-watchlist": lambda t, s, c: sofasidekick.watchlist(c, skip=s),
    "sofasidekick-upcoming": lambda t, s, c: sofasidekick.upcoming(c, skip=s),
}


@app.get("/manifest.json")
async def manifest(request: Request):
    manifest_path = os.path.join(os.path.dirname(__file__), "manifest.json")
    with open(manifest_path) as f:
        data = json.load(f)

    user_config = get_user_config(request)

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

    return JSONResponse(data)


@app.get("/catalog/{catalog_type}/{catalog_id}.json")
async def catalog(catalog_type: str, catalog_id: str, request: Request):
    user_config = get_user_config(request)
    extra = request.query_params.get("extra", "")
    skip = 0
    if extra:
        params = parse_qs(extra)
        skip = int(params.get("skip", [0])[0])

    handler = CATALOG_HANDLERS.get(catalog_id)
    if handler:
        try:
            items = handler(catalog_type, skip, user_config)
            return JSONResponse({"metas": items})
        except Exception as e:
            return JSONResponse({"metas": [], "error": str(e)}, status_code=500)

    if catalog_id in ("trakt-watchlist", "trakt-favorites", "trakt-watchlist-shows"):
        return await _trakt_user_catalog(catalog_type, catalog_id, skip, user_config)

    return JSONResponse({"metas": []}, status_code=404)


async def _trakt_user_catalog(catalog_type: str, catalog_id: str, skip: int, user_config: dict):
    token = user_config.get("trakt_token")
    if not token:
        return JSONResponse({"metas": [], "error": "Trakt token not configured"}, status_code=400)

    try:
        from trakt_api import TraktClient
        client = TraktClient(token=token)

        if catalog_id == "trakt-watchlist":
            items = client.watchlist(media_type="movies")
            media_type = "movie"
        elif catalog_id == "trakt-favorites":
            items = client.get_favorites()
            media_type = "movie"
        else:
            items = client.watchlist(media_type="shows")
            media_type = "series"

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
async def catalog_with_extra(catalog_type: str, catalog_id: str, extra: str, request: Request):
    user_config = get_user_config(request)
    params = parse_qs(extra)
    search = params.get("search", [None])[0]
    skip = int(params.get("skip", [0])[0])

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

    handler = CATALOG_HANDLERS.get(catalog_id)
    if handler:
        try:
            items = handler(catalog_type, skip, user_config)
            return JSONResponse({"metas": items})
        except Exception as e:
            return JSONResponse({"metas": [], "error": str(e)}, status_code=500)

    return JSONResponse({"metas": []}, status_code=404)


@app.get("/meta/{meta_type}/{meta_id}.json")
async def meta(meta_type: str, meta_id: str):
    try:
        if meta_id.startswith("tt"):
            from utils.id_mapping import imdb_to_tmdb
            tmdb_id = imdb_to_tmdb(meta_id)
            if tmdb_id:
                result = enricher.enrich(tmdb_id, meta_type)
                if result:
                    return JSONResponse({"meta": result})

        if meta_id.isdigit():
            result = enricher.enrich(int(meta_id), meta_type)
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
async def stream(stream_type: str, stream_id: str, request: Request):
    user_config = get_user_config(request)
    try:
        streams = await resolver.resolve_streams(stream_type, stream_id, user_config)
        return JSONResponse({"streams": streams})
    except Exception as e:
        return JSONResponse({"streams": [], "error": str(e)}, status_code=500)


@app.get("/configure")
async def configure():
    return HTMLResponse(CONFIGURE_HTML)


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
