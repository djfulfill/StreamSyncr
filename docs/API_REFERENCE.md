# StreamSyncr API Reference

Detailed API documentation for all 15+ services integrated with StreamSyncr — architecture, addon flow, catalogs, streams, scrobbling, data export, resume sync, and per-service endpoint details.

---

## Architecture

```
StreamSyncr/
├── apis/                        # API clients (12 services)
│   ├── anilist_api/             # AniList (anime tracking)
│   ├── imdb_api/                # IMDb (lists, ratings)
│   ├── jellyfin_api/            # Jellyfin (media server)
│   ├── kodi_api/                # Kodi (JSON-RPC)
│   ├── letterboxd_api/          # Letterboxd (film tracking)
│   ├── mdblist_api/             # MDBList (multi-rating lists)
│   ├── plex_api/                # Plex (media server)
│   ├── simkl_api/               # Simkl (tracking)
│   ├── sofasidekick_api/        # Sofa Sidekick (TV tracking)
│   ├── tmdb_api/                # TMDB (metadata, search)
│   ├── trakt_api/               # Trakt (universal tracking)
│   ├── wetrakr_api/             # WeTrakr (watch tracking)
│   └── utils/                   # Shared utilities
├── addon/                       # Stremio addon (port 7800)
│   ├── server.py                # FastAPI server
│   ├── auth/configure.py        # Web config page
│   ├── catalogs/                # Catalog handlers
│   ├── metadata/                # Metadata enricher
│   ├── streams/                 # Debrid stream resolver
│   └── manifest.json            # Addon manifest
├── frontend/                    # React + Vite dashboard (port 3030)
├── kodi_addon/                  # Kodi addon (plugin.video.streamsyncr)
│   ├── addon.xml                # Kodi addon manifest
│   ├── default.py               # Main entry point
│   └── resources/               # Settings, language, art
├── extension/                   # Chrome extension (cookie auto-sync)
├── sync_engine/                 # Cross-platform sync
├── docs/                        # Documentation
│   ├── skills/                  # Claude skill + API summary
│   ├── ROADMAP.md
│   └── ...
└── README.md
```

---

## Services Overview

### Tracking & Lists

| Service | Module | Auth Type |
|---------|--------|-----------|
| Trakt | `apis/trakt_api/` | API key + token |
| TMDB | `apis/tmdb_api/` | API key |
| IMDb | `apis/imdb_api/` | Cookie (GraphQL) |
| WeTrakr | `apis/wetrakr_api/` | Cookie (JWT) |
| AniList | `apis/anilist_api/` | Optional OAuth |
| Simkl | `apis/simkl_api/` | Client ID + OAuth |
| MDBList | `apis/mdblist_api/` | API key |
| Sofa Sidekick | `apis/sofasidekick_api/` | Cookie (3 cookies) |
| Letterboxd | `apis/letterboxd_api/` | Cookie (undocumented) |

### Media Servers

| Service | Module | Auth Type |
|---------|--------|-----------|
| Plex | `apis/plex_api/` | Token |
| Jellyfin | `apis/jellyfin_api/` | API key |
| Kodi | `apis/kodi_api/` | JSON-RPC (HTTP) |

### Debrid Services

| Service | Module | Auth Type |
|---------|--------|-----------|
| Real-Debrid | `apis/realdebrid_api/` | API token |
| TorBox | `apis/torbox_api/` | API key |
| AllDebrid | `apis/alldebrid_api/` | API key |

---

## Addon Flow

1. User visits `/configure`
2. Enters API keys and tokens for desired services
3. Gets a token-based manifest URL
4. Adds the URL to Stremio

---

## Catalogs (30 total)

**Public (no auth required):**
- Trakt Trending/Popular (movies + shows)
- TMDB Trending/Popular/Top Rated/Now Playing/Upcoming (movies + TV)
- Simkl Trending/Popular (movies + shows + anime)
- AniList Trending/Popular (anime)

**Private (user-configured):**
- WeTrakr Favorites/Watchlist (from user lists)
- Sofa Sidekick Movies/Upcoming (from library)
- MDBList — dynamic catalogs from user's lists
- Trakt Watchlist/Favorites
- IMDb Recently Viewed/Lists/Ratings
- Letterboxd — search catalog (read endpoints Cloudflare-protected)

---

## Streams (Debrid)

When a user selects a title, the addon resolves streams from:
- **Real-Debrid** — Torrents, unrestricted links
- **TorBox** — Torrents, unrestricted links
- **AllDebrid** — Torrents, unrestricted links

---

## Data Export

Export all user data from connected services as JSON:

```bash
# Export data
curl -s http://localhost:7800/api/export/{token} > export.json
```

**Supported services:** Trakt, Simkl, WeTrakr, Sofa Sidekick, Plex, Jellyfin, AniList, MDBList, IMDb

---

## Real-Time Scrobbling

When you press play in Kodi or Stremio, StreamSyncr instantly reports your activity to all connected services.

**How it works:**
- Kodi/Stremio connects via WebSocket for real-time bidirectional events
- HTTP POST fallback for clients that can't use WebSocket
- ID resolution chain: IMDb → TMDB → Trakt → service-specific IDs
- 90% threshold marks as watched
- Auto-reconnect with exponential backoff on disconnect

**Services that receive scrobbles:**
| Service | Start | Pause | Stop/Watched | Notes |
|---------|-------|-------|--------------|-------|
| Trakt | ✓ | ✓ | ✓ | Full scrobble API (start/pause/stop) |
| WeTrakr | - | - | ✓ | Mark watched only |
| Plex | - | - | ✓ | Mark watched only |
| Jellyfin | - | - | ✓ | Mark watched only |
| Simkl | - | - | ✓ | Add to history |
| Letterboxd | - | - | ✓ | Mark watched |
| Sofa Sidekick | - | - | ✓ | Mark watched |
| AniList | - | - | ✓ | Progress update |
| IMDb | - | - | - | Read-only, no write API |

### Scrobble Endpoints

- `WS /ws/scrobble?token={token}` — Real-time bidirectional WebSocket
- `POST /api/scrobble` — HTTP fallback for Kodi
- `GET /api/scrobble/now-playing` — Active sessions across all clients

---

## Resume Position Sync

Resume playback across devices. Positions are stored in SQLite and synced to Kodi/Jellyfin where supported.

### Resume Endpoints

- `GET /api/resume/{item_id}?token={token}&media_type=movie` — Get resume position
- `POST /api/resume` — Save position (Kodi sends on heartbeat/stop)
- `GET /api/resume/all?token={token}` — All resume positions for a user

### How it works

- Kodi sends `position_seconds` and `total_seconds` on each heartbeat/stop
- On play, Kodi fetches resume position and seeks the player
- Positions >95% are cleared (treated as "watched")
- SQLite database at `~/.streamsyncr/config.db`

---

## API Reference

### WeTrakr (REST, unofficial)

- **Base URL:** `https://wetrakr.com/proxy`
- **Auth:** JWT cookies (`wta_at`, `wta_rt`) + custom headers
- **Headers:** `wetrakr-api-country: US`, `wetrakr-api-language: en-US`
- **Key endpoints:**
  - `GET /proxy/frontend/users/{username}` — profile
  - `GET /proxy/frontend/movies/{tmdb_id}` — movie detail
  - `GET /proxy/frontend/shows/{tmdb_id}` — show detail
  - `GET /proxy/search/all?q=&type=` — search
  - `GET /proxy/account/lists` — user lists (18+ lists)
  - `GET /proxy/account/lists/{id}/items` — list items
  - `POST /proxy/account/tracking` — mark watched (INTERNAL id)
  - `POST /proxy/account/tracking/remove/all` — unwatch (TMDB id)
- **BROKEN (2026-08-02):** All `/filters/auto/sys:*` endpoints return `state: null`
- **Workaround:** Use list-based approach: `get_lists()` → `get_list_items(list_id)`
- **ID types:** Mark watched = internal ID, unwatch/favorite = TMDB ID

### Trakt (REST, documented)

- **Base URL:** `https://api.trakt.tv`
- **Auth:** Client ID (`trakt-api-key`) + Bearer token (`trakt-api-version: 2`)
- **Key endpoints:**
  - `GET /search/{id_type}/{id}` — search by IMDb/TMDb
  - `GET /movies/trending` — trending movies
  - `GET /shows/trending` — trending shows
  - `GET /sync/watchlist` — user watchlist
  - `POST /scrobble/stop` — mark watched
- **Rate limits:** 300 requests / 60 seconds
- **Scrobble:** Stop returns 409 Conflict on success

### TMDB (REST, documented)

- **Base URL:** `https://api.themoviedb.org/3`
- **Auth:** API key (query param or header)
- **Key endpoints:**
  - `GET /trending/movie/week` — trending movies
  - `GET /movie/popular` — popular movies
  - `GET /tv/popular` — popular TV
  - `GET /search/movie?query=` — search movies
  - `GET /movie/{id}/watch/providers` — streaming availability

### Letterboxd (undocumented, cookie-based)

- **Base URL:** `https://letterboxd.com`
- **Auth:** Cookie-based + CSRF token
- **Required cookies:**
  - `cf_clearance` — Cloudflare clearance
  - `letterboxd.user.CURRENT` — user session
  - `com.xk72.webparts.csrf` — CSRF token (also used as `x-csrf-token` header)
- **Working endpoints:**
  - `GET /s/autocompletefilm?q={query}` — search films (returns `lid` codes)
  - `POST /api/v0/lists` — create list
  - `PATCH /api/v0/lists` — add to list
  - `DELETE /api/v0/lists` — remove from list
  - `POST /ajax/film:{lid}/filmlistentry` — mark watched
  - `POST /film/{slug}/add-to-watchlist/` — add to watchlist
- **Blocked endpoints (Cloudflare):** diary, watchlist read, ratings, user data
- **Film codes:** Short alphanumeric `lid` (e.g., `1skk` = Inception)

### MDBList (REST, documented)

- **Base URL:** `https://api.mdblist.com`
- **Auth:** API key (`apikey` query param)
- **Key endpoints:**
  - `GET /user` — user profile
  - `GET /lists/user` — user lists
  - `GET /lists/{listid}/items` — list items
  - `GET /search/{media_type}?query=` — search movies/shows
  - `GET /{provider}/{media_type}/{media_id}` — get by IMDb/TMDb/TVDB
- **Rate limits:** 1,000/day (free), up to 250,000/day (VIP)

### Sofa Sidekick (undocumented, cookie-based)

- **Base URL:** `https://app.sofasidekick.com/api`
- **Auth:** Cookie-based (`session_id`, `cf_clearance`, `__cf_bm`)
- **Working endpoints:**
  - `GET /movies` — user's movie library (235 items)
  - `GET /upcoming?days=30` — upcoming episodes
  - `GET /stats` — watch stats
  - `GET /account` — user profile
- **Blocked endpoints (Cloudflare):** `/api/shows`, `/api/watchlist`, `/api/history`
- **Data source:** TheTVDB for metadata

### AniList (GraphQL, documented)

- **Endpoint:** `https://graphql.anilist.co`
- **Auth:** Optional OAuth2 (90 req/min without auth)
- **Key queries:** `Page`, `Media`, `MediaListCollection`, `Viewer`
- **Mutations:** `SaveMediaListEntry`, `DeleteMediaListEntry`, `ToggleFavourite`

### Simkl (REST, documented)

- **Base URL:** `https://api.simkl.com`
- **Auth:** Client ID + optional OAuth2
- **Key endpoints:**
  - `GET /sync/history` — watch history
  - `GET /sync/all-items` — all items
  - `GET /sync/activities` — activity feed
- **Sync model:** Two-phase — initial pull + incremental via `date_from`
- **Rate limit:** Batch writes to avoid `rate_limit` errors

### Jellyfin (REST, documented)

- **Base URL:** `http://<server>:8096`
- **Auth:** API key (`X-Emby-Token`)
- **Key endpoints:**
  - `GET /Users/{id}/Items` — library items
  - `GET /Shows/{id}/Episodes` — show episodes
  - `GET /Items/{id}/Played` — mark played

### Plex (REST, documented)

- **Base URL:** `http://<server>:32400`
- **Auth:** Token-based (`X-Plex-Token`)
- **Key endpoints:**
  - `GET /library/sections` — library sections
  - `GET /library/metadata/{id}` — item details
  - `POST /:/scrobble` — mark watched

### Kodi (JSON-RPC)

- **Base URL:** `http://<host>:8080/jsonrpc`
- **Auth:** None (HTTP basic optional)
- **Key methods:** `VideoLibrary.GetMovies`, `VideoLibrary.GetTVShows`

### Real-Debrid (REST, documented)

- **Base URL:** `https://api.real-debrid.com/rest/1.0`
- **Auth:** Bearer token (`Authorization: Bearer YOUR_TOKEN`)
- **Key endpoints:**
  - `GET /torrents` — list torrents
  - `POST /torrents/addMagnet` — add magnet link
  - `GET /torrents/{id}` — torrent info
  - `POST /torrents/{id}/selectFiles` — select files
  - `GET /unrestrict/link` — unrestricted download link
  - `GET /user` — user info (limits, points)
- **Rate limits:** 120 requests / minute

### TorBox (REST, documented)

- **Base URL:** `https://api.torbox.app/v1`
- **Auth:** API key (`Authorization: Bearer YOUR_API_KEY`)
- **Key endpoints:**
  - `GET /torrents/list` — list torrents
  - `POST /torrents/createlink` — create download link
  - `GET /torrents/{id}` — torrent info
  - `GET /usenet/list` — list usenet downloads
  - `GET /user` — user info
- **Rate limits:** Varies by plan

### AllDebrid (REST, documented)

- **Base URL:** `https://api.alldebrid.com/v4`
- **Auth:** API key (`?agent=StreamSyncr&apikey=YOUR_KEY`)
- **Key endpoints:**
  - `GET /magnet/upload` — add magnet link
  - `GET /magnet/status` — check magnet status
  - `GET /link/unlock` — unrestricted download link
  - `GET /user` — user info (limits, premium status)
- **Rate limits:** 120 requests / minute

---

## Python Usage

### Environment Variables

```bash
# WeTrakr
export WETRAKR_ACCESS_TOKEN="your_wta_at"
export WETRAKR_REFRESH_TOKEN="your_wta_rt"
export WETRAKR_USERNAME="user"

# Trakt
export TRAKT_API_KEY="your_api_key"
export TRAKT_TOKEN="your_bearer_token"

# TMDB
export TMDB_API_KEY="your_tmdb_key"

# MDBList
export MDBLIST_API_KEY="your_mdblist_key"

# Real-Debrid
export REALDEBRID_TOKEN="your_api_token"

# TorBox
export TORBOX_API_KEY="your_api_key"

# AllDebrid
export ALLDEBRID_API_KEY="your_api_key"
```

### Quick Examples

```python
# WeTrakr
from apis.wetrakr_api.client import WeTrakrClient
c = WeTrakrClient()
c.search("Inception")
c.mark_watched(internal_id, "movie")

# Trakt
from apis.trakt_api import TraktClient
t = TraktClient()
t.search("Swordfish")
t.mark_watched_now(movies=[4977])

# TMDB
from apis.tmdb_api import TMDBClient
t = TMDBClient()
t.search_movie("Swordfish", year=2001)

# IMDb
from apis.imdb_api import IMDbClient
c = IMDbClient()
c.get_lists()
c.rate_title("tt0244244", 8)

# Letterboxd
from apis.letterboxd_api import LetterboxdClient
c = LetterboxdClient(cookies="...", csrf_token="...")
films = c.search_film("Swordfish")
c.create_list("My List", film_lids=["1skk", "eDGs"])

# Plex
from apis.plex_api import PlexClient
c = PlexClient(base_url="http://localhost:32400", token="your_token")
c.get_libraries()

# AniList
from apis.anilist_api import AniListClient
c = AniListClient()
c.search_anime("Naruto")

# Simkl
from apis.simkl_api import SimklClient
c = SimklClient(client_id="your_client_id")
c.search("Breaking Bad", media_type="show")

# Jellyfin
from apis.jellyfin_api import JellyfinClient
c = JellyfinClient(base_url="http://localhost:8096", api_key="your_key", user_id="user_id")
c.get_libraries()

# Kodi
from apis.kodi_api import KodiClient
c = KodiClient("http://192.168.1.50:8080")
c.get_movies()

# Sofa Sidekick
from apis.sofasidekick_api import SofaSidekickClient
c = SofaSidekickClient(session_id="...", cf_clearance="...", cf_bm="...")
c.get_movies()  # 235 items

# MDBList
from apis.mdblist_api import MDBListClient
m = MDBListClient()
m.my_lists()
m.list_items(1176)

# Real-Debrid
from apis.realdebrid_api import RealDebridClient
c = RealDebridClient(token="your_token")
c.add_magnet("magnet:?xt=...")
c.unrestrict_link("https://real-debrid.com/d/...")

# TorBox
from apis.torbox_api import TorBoxClient
c = TorBoxClient(api_key="your_api_key")
c.list_torrents()
c.create_download_link(torrent_id=123, file_id=1)

# AllDebrid
from apis.alldebrid_api import AllDebridClient
c = AllDebridClient(api_key="your_api_key")
c.upload_magnet("magnet:?xt=...")
c.unrestrict_link("https://alldebrid.com/d/...")
```

---

## Frontend

React + Vite + Tailwind dashboard on port 3030.

```bash
cd frontend
npm install
npm run dev    # http://localhost:3030
npm run build  # production build
```

---

## Critical Notes

### WeTrakr ID Types
- **Mark watched:** Use internal ID (`item["id"]`)
- **Unwatch/Favorite:** Use TMDB ID (`item["ids"]["tmdb"]["id"]`)
- Mixing them causes silent failures.

### WeTrakr Filter Endpoints Broken
- All `/filters/auto/sys:*` endpoints return `state: null` (server-side bug)
- **Workaround:** Use list-based approach: `get_lists()` → `get_list_items(list_id)`

### Letterboxd Cloudflare
- Read endpoints (diary, watchlist, ratings) are Cloudflare-protected
- Write endpoints (create list, mark watched, add to watchlist) work
- Search works: `GET /s/autocompletefilm?q={query}` → returns `lid` codes
- Cookies expire periodically — users need to refresh from browser

### Sofa Sidekick Cloudflare
- `/api/movies` and `/api/upcoming` work
- `/api/shows` and `/api/watchlist` are Cloudflare-blocked
- Movies: 235 items with TVDB IDs, posters, years
- Upcoming: shows with next episode dates

### Trakt Token Format
- User's `trakt_token` may be a cookie string (`value; cf_clearance=...`)
- Clean Bearer token needed for `TraktClient`
- Pass both `api_key` and `token` to catalog handlers

### MDBList Path-Based Endpoints
- Search: `GET /search/{media_type}?query={query}`
- By provider: `GET /{provider}/{media_type}/{media_id}`
- List items: `GET /lists/{listid}/items` (IDs use `ids.imdb` not `ids.imdbid`)
