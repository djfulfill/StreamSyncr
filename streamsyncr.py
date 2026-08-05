#!/usr/bin/env python3
"""
StreamSyncr CLI — Unified streaming tracker from the command line.

Usage:
    streamsyncr <service> <command> [options]
    streamsyncr trakt search "Inception"
    streamsyncr plex mark-watched 12345
    streamsyncr emby libraries
    streamsyncr xtream live-streams --category 1
    streamsyncr sync --from trakt --to plex
    streamsyncr export --format json
"""

import os
import sys
import json
import click

# ── Service Imports ─────────────────────────────────────────────

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "apis"))

from trakt_api import TraktClient
from tmdb_api import TMDBClient
from plex_api import PlexClient
from jellyfin_api import JellyfinClient
from emby_api import EmbyClient
from anilist_api import AniListClient
from simkl_api import SimklClient
from mdblist_api import MDBListClient
from wetrakr_api import WeTrakrClient
from imdb_api import IMDbClient
from letterboxd_api import LetterboxdClient
from sofasidekick_api import SofaSidekickClient
from kodi_api import KodiClient
from xtream_api import XtreamClient

# ── Helpers ─────────────────────────────────────────────────────

def print_table(items, columns):
    """Print a list of dicts as a table."""
    if not items:
        click.echo("No results.")
        return

    widths = {col: len(col) for col in columns}
    for item in items:
        for col in columns:
            val = str(item.get(col, ""))
            widths[col] = max(widths[col], min(len(val), 40))

    header = "  ".join(col.ljust(widths[col]) for col in columns)
    click.echo(click.style(header, bold=True))
    click.echo("-" * len(header))

    for item in items:
        row = "  ".join(str(item.get(col, ""))[:40].ljust(widths[col]) for col in columns)
        click.echo(row)

def print_json(data):
    """Print data as formatted JSON."""
    click.echo(json.dumps(data, indent=2, default=str))

def env_or_prompt(env_var, prompt_text, hide_input=False):
    """Get value from env var or prompt user."""
    val = os.environ.get(env_var)
    if not val:
        val = click.prompt(prompt_text, hide_input=hide_input)
    return val

# ── Trakt ───────────────────────────────────────────────────────

@click.group()
def cli():
    """StreamSyncr — Unified streaming tracker CLI."""
    pass

@cli.group()
def trakt():
    """Trakt.tv commands."""
    pass

@trakt.command("search")
@click.argument("query")
@click.option("--type", "media_type", default="movie", help="movie or show")
def trakt_search(query, media_type):
    """Search Trakt for movies or shows."""
    api_key = env_or_prompt("TRAKT_API_KEY", "Trakt API key")
    token = env_or_prompt("TRAKT_TOKEN", "Trakt token")
    t = TraktClient(api_key=api_key, token=token)
    results = t.search(query, media_type)
    print_table(results, ["title", "year", "type", "slug"])

@trakt.command("trending")
@click.option("--limit", default=10, help="Number of results")
def trakt_trending(limit):
    """Get trending movies/shows from Trakt."""
    api_key = env_or_prompt("TRAKT_API_KEY", "Trakt API key")
    token = env_or_prompt("TRAKT_TOKEN", "Trakt token")
    t = TraktClient(api_key=api_key, token=token)
    results = t.trending("movies", limit=limit)
    print_table(results, ["title", "year", "watchers"])

@trakt.command("mark-watched")
@click.argument("ids", nargs=-1, type=int)
@click.option("--type", "media_type", default="movie", help="movie or show")
def trakt_mark_watched(ids, media_type):
    """Mark items as watched on Trakt."""
    api_key = env_or_prompt("TRAKT_API_KEY", "Trakt API key")
    token = env_or_prompt("TRAKT_TOKEN", "Trakt token")
    t = TraktClient(api_key=api_key, token=token)
    if media_type == "movie":
        t.mark_watched_now(movies=list(ids))
    else:
        t.mark_watched_now(shows=list(ids))
    click.echo(f"Marked {len(ids)} {media_type}(s) as watched.")

# ── Plex ────────────────────────────────────────────────────────

@cli.group()
def plex():
    """Plex Media Server commands."""
    pass

@plex.command("libraries")
def plex_libraries():
    """List Plex libraries."""
    url = env_or_prompt("PLEX_URL", "Plex server URL")
    token = env_or_prompt("PLEX_TOKEN", "Plex token")
    p = PlexClient(url, token)
    libs = p.get_libraries()
    print_table(libs, ["title", "type", "key"])

@plex.command("movies")
@click.option("--library", default=1, help="Library ID")
@click.option("--limit", default=20, help="Number of results")
def plex_movies(library, limit):
    """List movies in a Plex library."""
    url = env_or_prompt("PLEX_URL", "Plex server URL")
    token = env_or_prompt("PLEX_TOKEN", "Plex token")
    p = PlexClient(url, token)
    items = p.get_library_items(library, "movie")[:limit]
    print_table(items, ["title", "year", "ratingKey", "viewCount"])

@plex.command("search")
@click.argument("query")
def plex_search(query):
    """Search Plex libraries."""
    url = env_or_prompt("PLEX_URL", "Plex server URL")
    token = env_or_prompt("PLEX_TOKEN", "Plex token")
    p = PlexClient(url, token)
    results = p.search(query)
    print_table(results, ["title", "year", "type", "ratingKey"])

@plex.command("mark-watched")
@click.argument("rating_key", type=int)
def plex_mark_watched(rating_key):
    """Mark a Plex item as watched."""
    url = env_or_prompt("PLEX_URL", "Plex server URL")
    token = env_or_prompt("PLEX_TOKEN", "Plex token")
    p = PlexClient(url, token)
    if p.mark_watched(rating_key):
        click.echo(f"Marked {rating_key} as watched.")
    else:
        click.echo("Failed to mark as watched.")

# ── Emby ────────────────────────────────────────────────────────

@cli.group()
def emby():
    """Emby Media Server commands."""
    pass

@emby.command("libraries")
def emby_libraries():
    """List Emby libraries."""
    url = env_or_prompt("EMBY_URL", "Emby server URL")
    api_key = env_or_prompt("EMBY_API_KEY", "Emby API key")
    e = EmbyClient(url, api_key=api_key)
    libs = e.get_libraries()
    print_table(libs, ["Name", "Id", "CollectionType"])

@emby.command("movies")
@click.option("--limit", default=20, help="Number of results")
def emby_movies(limit):
    """List Emby movies."""
    url = env_or_prompt("EMBY_URL", "Emby server URL")
    api_key = env_or_prompt("EMBY_API_KEY", "Emby API key")
    e = EmbyClient(url, api_key=api_key)
    e.authenticate()
    items = e.get_movies(limit=limit)
    print_table(items, ["Name", "Year", "Id", "UserData PlayedCount"])

@emby.command("search")
@click.argument("query")
def emby_search(query):
    """Search Emby libraries."""
    url = env_or_prompt("EMBY_URL", "Emby server URL")
    api_key = env_or_prompt("EMBY_API_KEY", "Emby API key")
    e = EmbyClient(url, api_key=api_key)
    e.authenticate()
    results = e.search(query)
    print_table(results, ["Name", "Year", "Id", "Type"])

@emby.command("mark-watched")
@click.argument("item_id")
def emby_mark_watched(item_id):
    """Mark an Emby item as watched."""
    url = env_or_prompt("EMBY_URL", "Emby server URL")
    api_key = env_or_prompt("EMBY_API_KEY", "Emby API key")
    e = EmbyClient(url, api_key=api_key)
    e.authenticate()
    if e.mark_watched(item_id):
        click.echo(f"Marked {item_id} as watched.")
    else:
        click.echo("Failed to mark as watched.")

# ── Jellyfin ────────────────────────────────────────────────────

@cli.group()
def jellyfin():
    """Jellyfin Media Server commands."""
    pass

@jellyfin.command("libraries")
def jellyfin_libraries():
    """List Jellyfin libraries."""
    url = env_or_prompt("JELLYFIN_URL", "Jellyfin server URL")
    api_key = env_or_prompt("JELLYFIN_API_KEY", "Jellyfin API key")
    user_id = env_or_prompt("JELLYFIN_USER_ID", "Jellyfin user ID")
    j = JellyfinClient(url, api_key, user_id)
    libs = j.get_libraries()
    print_table(libs, ["Name", "Id", "CollectionType"])

@jellyfin.command("movies")
@click.option("--limit", default=20, help="Number of results")
def jellyfin_movies(limit):
    """List Jellyfin movies."""
    url = env_or_prompt("JELLYFIN_URL", "Jellyfin server URL")
    api_key = env_or_prompt("JELLYFIN_API_KEY", "Jellyfin API key")
    user_id = env_or_prompt("JELLYFIN_USER_ID", "Jellyfin user ID")
    j = JellyfinClient(url, api_key, user_id)
    items = j.get_movies(limit=limit)
    print_table(items, ["Name", "Year", "Id"])

# ── Xtream Codes ────────────────────────────────────────────────

@cli.group()
def xtream():
    """Xtream Codes IPTV commands."""
    pass

@xtream.command("info")
def xtream_info():
    """Get Xtream account info."""
    url = env_or_prompt("XTREAM_URL", "Xtream server URL")
    user = env_or_prompt("XTREAM_USER", "Xtream username")
    pwd = env_or_prompt("XTREAM_PASS", "Xtream password", hide_input=True)
    x = XtreamClient(url, user, pwd)
    info = x.auth()
    ui = info.get("user_info", {})
    si = info.get("server_info", {})
    click.echo(f"Status: {ui.get('status')}")
    click.echo(f"Expiry: {x.expiry()}")
    conns = x.connections()
    click.echo(f"Connections: {conns['active']}/{conns['max']}")
    click.echo(f"Server: {si.get('url')}:{si.get('port')}")

@xtream.command("live-categories")
def xtream_live_categories():
    """List live TV categories."""
    url = env_or_prompt("XTREAM_URL", "Xtream server URL")
    user = env_or_prompt("XTREAM_USER", "Xtream username")
    pwd = env_or_prompt("XTREAM_PASS", "Xtream password", hide_input=True)
    x = XtreamClient(url, user, pwd)
    cats = x.live_categories()
    print_table(cats, ["category_id", "category_name"])

@xtream.command("live-streams")
@click.option("--category", default=None, type=int, help="Category ID")
@click.option("--limit", default=20, help="Number of results")
def xtream_live_streams(category, limit):
    """List live TV streams."""
    url = env_or_prompt("XTREAM_URL", "Xtream server URL")
    user = env_or_prompt("XTREAM_USER", "Xtream username")
    pwd = env_or_prompt("XTREAM_PASS", "Xtream password", hide_input=True)
    x = XtreamClient(url, user, pwd)
    streams = x.live_streams(category)[:limit]
    print_table(streams, ["num", "name", "stream_id", "category_id"])

@xtream.command("vod-categories")
def xtream_vod_categories():
    """List VOD categories."""
    url = env_or_prompt("XTREAM_URL", "Xtream server URL")
    user = env_or_prompt("XTREAM_USER", "Xtream username")
    pwd = env_or_prompt("XTREAM_PASS", "Xtream password", hide_input=True)
    x = XtreamClient(url, user, pwd)
    cats = x.vod_categories()
    print_table(cats, ["category_id", "category_name"])

@xtream.command("vod-streams")
@click.option("--category", default=None, type=int, help="Category ID")
@click.option("--limit", default=20, help="Number of results")
def xtream_vod_streams(category, limit):
    """List VOD streams."""
    url = env_or_prompt("XTREAM_URL", "Xtream server URL")
    user = env_or_prompt("XTREAM_USER", "Xtream username")
    pwd = env_or_prompt("XTREAM_PASS", "Xtream password", hide_input=True)
    x = XtreamClient(url, user, pwd)
    streams = x.vod_streams(category)[:limit]
    print_table(streams, ["num", "name", "stream_id", "rating", "category_id"])

@xtream.command("series")
@click.option("--category", default=None, type=int, help="Category ID")
@click.option("--limit", default=20, help="Number of results")
def xtream_series(category, limit):
    """List series."""
    url = env_or_prompt("XTREAM_URL", "Xtream server URL")
    user = env_or_prompt("XTREAM_USER", "Xtream username")
    pwd = env_or_prompt("XTREAM_PASS", "Xtream password", hide_input=True)
    x = XtreamClient(url, user, pwd)
    series = x.series(category)[:limit]
    print_table(series, ["name", "series_id", "category_id", "rating"])

@xtream.command("epg")
@click.argument("stream_id", type=int)
@click.option("--limit", default=24, help="Number of programs")
def xtream_epg(stream_id, limit):
    """Get EPG for a live stream."""
    url = env_or_prompt("XTREAM_URL", "Xtream server URL")
    user = env_or_prompt("XTREAM_USER", "Xtream username")
    pwd = env_or_prompt("XTREAM_PASS", "Xtream password", hide_input=True)
    x = XtreamClient(url, user, pwd)
    epg = x.short_epg(stream_id, limit)
    print_json(epg)

@xtream.command("m3u")
def xtream_m3u():
    """Get M3U playlist URL."""
    url = env_or_prompt("XTREAM_URL", "Xtream server URL")
    user = env_or_prompt("XTREAM_USER", "Xtream username")
    pwd = env_or_prompt("XTREAM_PASS", "Xtream password", hide_input=True)
    x = XtreamClient(url, user, pwd)
    click.echo(f"M3U URL: {x.m3u_url()}")

# ── AniList ─────────────────────────────────────────────────────

@cli.group()
def anilist():
    """AniList commands."""
    pass

@anilist.command("search")
@click.argument("query")
@click.option("--type", "media_type", default="anime", help="anime or manga")
def anilist_search(query, media_type):
    """Search AniList for anime/manga."""
    c = AniListClient()
    if media_type == "anime":
        results = c.search_anime(query)
    else:
        results = c.search_manga(query)
    for r in results:
        title = r.get("title", {})
        click.echo(f"  {title.get('english') or title.get('romaji')} (Score: {r.get('averageScore', 'N/A')})")

@anilist.command("trending")
@click.option("--limit", default=10, help="Number of results")
def anilist_trending(limit):
    """Get trending anime."""
    c = AniListClient()
    results = c.get_trending(per_page=limit)
    for r in results:
        title = r.get("title", {})
        click.echo(f"  {title.get('english') or title.get('romaji')} (Score: {r.get('averageScore', 'N/A')})")

@anilist.command("reviews")
@click.argument("media_id", type=int)
@click.option("--limit", default=5, help="Number of reviews")
def anilist_reviews(media_id, limit):
    """Get reviews for an anime/manga."""
    c = AniListClient()
    reviews = c.get_media_reviews(media_id, per_page=limit)
    for r in reviews:
        user = r.get("user", {}).get("name", "Unknown")
        rating = r.get("rating", "N/A")
        summary = r.get("summary", "")[:80]
        click.echo(f"  [{rating}] {user}: {summary}")

# ── TMDB ────────────────────────────────────────────────────────

@cli.group()
def tmdb():
    """TMDB commands."""
    pass

@tmdb.command("search")
@click.argument("query")
@click.option("--type", "media_type", default="movie", help="movie or tv")
def tmdb_search(query, media_type):
    """Search TMDB for movies/shows."""
    api_key = env_or_prompt("TMDB_API_KEY", "TMDB API key")
    t = TMDBClient(api_key)
    if media_type == "movie":
        results = t.search_movie(query)
    else:
        results = t.search_tv(query)
    for r in results:
        title = r.get("title") or r.get("name")
        year = (r.get("release_date") or r.get("first_air_date", ""))[:4]
        click.echo(f"  {title} ({year}) [ID: {r.get('id')}]")

@tmdb.command("trending")
@click.option("--limit", default=10, help="Number of results")
def tmdb_trending(limit):
    """Get trending movies from TMDB."""
    api_key = env_or_prompt("TMDB_API_KEY", "TMDB API key")
    t = TMDBClient(api_key)
    results = t.trending(media_type="movie")[:limit]
    for r in results:
        title = r.get("title")
        year = (r.get("release_date", ""))[:4]
        click.echo(f"  {title} ({year}) [ID: {r.get('id')}]")

# ── IMDb ────────────────────────────────────────────────────────

@cli.group()
def imdb():
    """IMDb commands."""
    pass

@imdb.command("search")
@click.argument("query")
def imdb_search(query):
    """Search IMDb."""
    c = IMDbClient()
    results = c.search(query)
    for r in results:
        click.echo(f"  {r.get('titleText', {}).get('text', 'N/A')} ({r.get('releaseYear', {}).get('year', 'N/A')}) [IMDb: {r.get('id', 'N/A')}]")

# ── Kodi ────────────────────────────────────────────────────────

@cli.group()
def kodi():
    """Kodi JSON-RPC commands."""
    pass

@kodi.command("movies")
def kodi_movies():
    """List Kodi movies."""
    url = env_or_prompt("KODI_URL", "Kodi JSON-RPC URL")
    c = KodiClient(url)
    movies = c.get_movies()
    print_table(movies, ["label", "year", "rating", "movieid"])

@kodi.command("shows")
def kodi_shows():
    """List Kodi TV shows."""
    url = env_or_prompt("KODI_URL", "Kodi JSON-RPC URL")
    c = KodiClient(url)
    shows = c.get_tvshows()
    print_table(shows, ["label", "year", "rating", "tvshowid"])

# ── Export ──────────────────────────────────────────────────────

@cli.command("export")
@click.option("--format", "fmt", default="json", type=click.Choice(["json", "table"]), help="Output format")
@click.option("--output", "-o", default=None, help="Output file (default: stdout)")
def export_data(fmt, output):
    """Export all connected service data."""
    click.echo("Exporting data from all connected services...")
    # This would call the backend export endpoint
    click.echo("Use the Stremio addon at /api/export/{token} for full export.")

# ── Status ──────────────────────────────────────────────────────

@cli.command("status")
def status():
    """Show status of all configured services."""
    services = {
        "Trakt": ["TRAKT_API_KEY", "TRAKT_TOKEN"],
        "TMDB": ["TMDB_API_KEY"],
        "Plex": ["PLEX_URL", "PLEX_TOKEN"],
        "Emby": ["EMBY_URL", "EMBY_API_KEY"],
        "Jellyfin": ["JELLYFIN_URL", "JELLYFIN_API_KEY"],
        "Xtream": ["XTREAM_URL", "XTREAM_USER"],
        "AniList": [],
        "Kodi": ["KODI_URL"],
    }

    click.echo(click.style("StreamSyncr Service Status", bold=True))
    click.echo("-" * 40)

    for name, env_vars in services.items():
        configured = all(os.environ.get(v) for v in env_vars)
        if not env_vars:
            configured = True  # No env needed
        status_icon = "✓" if configured else "✗"
        color = "green" if configured else "red"
        click.echo(f"  {click.style(status_icon, fg=color)} {name}")

if __name__ == "__main__":
    cli()
