![Description](./StreamSyncr-banner.png)

# StreamSyncr

A unified streaming tracker — sync your watch history across 11+ services, with a self-hosted Stremio addon.

## Architecture

```
StreamSyncr/
├── apis/                        # API clients (11 services)
│   ├── anilist_api/             # AniList (anime tracking)
│   ├── imdb_api/                # IMDb (lists, ratings)
│   ├── jellyfin_api/            # Jellyfin (media server)
│   ├── kodi_api/                # Kodi (JSON-RPC)
│   ├── letterboxd_api/          # Letterboxd (film tracking)
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
├── sync_engine/                 # Cross-platform sync
├── docs/                        # Documentation
│   ├── skills/                  # Claude skill + API summary
│   ├── ROADMAP.md
│   └── ...
└── README.md
```

## Services

| Service | Module | Auth Type | Status |
|---------|--------|-----------|--------|
| [WeTrakr](https://wetrakr.com) | `apis/wetrakr_api/` | Cookie (JWT) | ✅ Full client |
| [Trakt](https://trakt.tv) | `apis/trakt_api/` | API key + token | ✅ Full client |
| [TMDB](https://themoviedb.org) | `apis/tmdb_api/` | API key | ✅ Full client |
| [IMDb](https://www.imdb.com) | `apis/imdb_api/` | Cookie (GraphQL) | ✅ Full client |
| [Letterboxd](https://letterboxd.com) | `apis/letterboxd_api/` | Cookie (undocumented) | ✅ Lists + ratings |
| [Plex](https://plex.tv) | `apis/plex_api/` | Token | ✅ Full client |
| [AniList](https://anilist.co) | `apis/anilist_api/` | Optional OAuth | ✅ Full client |
| [Simkl](https://simkl.com) | `apis/simkl_api/` | Client ID + OAuth | ✅ Full client |
| [Jellyfin](https://jellyfin.org) | `apis/jellyfin_api/` | API key | ✅ Full client |
| [Kodi](https://kodi.tv) | `apis/kodi_api/` | JSON-RPC (HTTP) | ✅ Full client |
| [Sofa Sidekick](https://sofasidekick.com) | `apis/sofasidekick_api/` | Cookie | ✅ Full client |

## Stremio Addon

Self-hosted Stremio addon with hybrid auth — public catalogs + user-configured private catalogs and streams.

### Quick Start

```bash
cd addon
pip install -r requirements.txt

# Start server
screen -dmS stremio python3 -c "from server import app; import uvicorn; uvicorn.run(app, host='0.0.0.0', port=7800)"
```

### URLs

- **Configure:** http://localhost:7800/configure
- **Manifest:** http://localhost:7800/manifest.json

### Features

- **17 public catalogs** (Trakt, TMDB, AniList, Simkl trending/popular)
- **User catalogs** (WeTrakr, Sofa Sidekick, Trakt watchlists)
- **Debrid streams** (Real-Debrid, TorBox, AllDebrid)
- **Multi-source metadata** (TMDB + IMDb enrichment)
- **Web config UI** — collapsible sections for all 11 services

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
c = SofaSidekickClient(session_id="your_session_id")
c.get_shows()
```

## Frontend

React + Vite + Tailwind dashboard on port 3030.

```bash
cd frontend
npm install
npm run dev    # http://localhost:3030
npm run build  # production build
```

## Critical Notes

### WeTrakr ID Types
- **Mark watched**: Use internal ID (`item["id"]`)
- **Unwatch/Favorite**: Use TMDB ID (`item["ids"]["tmdb"]["id"]`)
- Mixing them causes silent failures.

### Letterboxd Film Codes
- Search: `GET /s/autocompletefilm?q={query}` → returns `lid`
- List ops use `lid` codes (e.g., `1Y0m` = Swordfish)
- Cloudflare protected — cookies expire periodically

### Trakt Rate Limits
- 300 requests / 60 seconds
- Scrobble stop returns 409 Conflict on success

### Simkl Sync Model
- Two-phase: initial pull + incremental via `date_from`
- Batch writes to avoid rate_limit errors

---

## License

MIT
