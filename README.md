![Description](./StreamSyncr-banner.png)

# StreamSyncr

A unified streaming tracker — sync your watch history across 12+ services, with a self-hosted Stremio addon.

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

## Services

### Tracking & Lists

| Service | Module | Auth Type | Status |
|---------|--------|-----------|--------|
| [Trakt](https://trakt.tv) | `apis/trakt_api/` | API key + token | ✅ Full client |
| [TMDB](https://themoviedb.org) | `apis/tmdb_api/` | API key | ✅ Full client |
| [IMDb](https://www.imdb.com) | `apis/imdb_api/` | Cookie (GraphQL) | ✅ Recently viewed, lists, ratings |
| [WeTrakr](https://wetrakr.com) | `apis/wetrakr_api/` | Cookie (JWT) | ✅ Favorites, watchlist, ratings |
| [AniList](https://anilist.co) | `apis/anilist_api/` | Optional OAuth | ✅ Trending, popular |
| [Simkl](https://simkl.com) | `apis/simkl_api/` | Client ID + OAuth | ✅ Trending, popular |
| [MDBList](https://mdblist.com) | `apis/mdblist_api/` | API key | ✅ Lists + search |
| [Sofa Sidekick](https://sofasidekick.com) | `apis/sofasidekick_api/` | Cookie (3 cookies) | ✅ Movies + upcoming |
| [Letterboxd](https://letterboxd.com) | `apis/letterboxd_api/` | Cookie (undocumented) | ✅ Search + list CRUD |

### Media Servers

| Service | Module | Auth Type | Status |
|---------|--------|-----------|--------|
| [Plex](https://plex.tv) | `apis/plex_api/` | Token | ✅ Full client |
| [Jellyfin](https://jellyfin.org) | `apis/jellyfin_api/` | API key | ✅ Full client |
| [Kodi](https://kodi.tv) | `apis/kodi_api/` | JSON-RPC (HTTP) | ✅ Full client |

### Debrid Services (Stream Sources)

| Service | Module | Auth Type | Status |
|---------|--------|-----------|--------|
| [Real-Debrid](https://real-debrid.com) | `apis/realdebrid_api/` | API token | ✅ Torrents, unrestricted links |
| [TorBox](https://torbox.app) | `apis/torbox_api/` | API key | ✅ Torrents, unrestricted links |
| [AllDebrid](https://alldebrid.com) | `apis/alldebrid_api/` | API key | ✅ Torrents, unrestricted links |

## Why StreamSyncr?

The streaming landscape is fragmented. You track content on Trakt, IMDb, Letterboxd, WeTrakr — none of them talk to each other. StreamSyncr is the **only self-hosted tool** that combines a Stremio addon, cross-service watch history sync, and a web dashboard in one package.

**The Linux and open-source way:** Self-managed, self-owned. No cloud dependency, no monthly fees, no vendor lock-in. Your data stays on your machine.

### How We Compare

| Feature | StreamSyncr | AIOStreams | WatchState | LimeStream | librarySync |
|---------|:-----------:|:----------:|:----------:|:----------:|:-----------:|
| **Stremio Addon** | ✅ | ✅ | ❌ | ❌ | ❌ |
| **Stream Resolution (Debrid)** | ✅ | ✅ | ❌ | ❌ | ❌ |
| **Catalog Browsing** | ✅ | ✅ | ❌ | ❌ | ❌ |
| **Real-Time Scrobbling** | ✅ | ❌ | ❌ | ❌ | ❌ |
| **Watch History Sync** | ✅ | ❌ | ✅ | ✅ | ✅ |
| **Cross-Service Sync** | ✅ | ❌ | ✅ | ❌ | ✅ |
| **Netflix/Disney+/HBO Max** | ❌ | ❌ | ❌ | ✅ | ❌ |
| **Trakt** | ✅ | ❌ | ✅ | ❌ | ✅ |
| **TMDB** | ✅ | ❌ | ❌ | ❌ | ❌ |
| **IMDb** | ✅ | ❌ | ❌ | ❌ | ❌ |
| **Letterboxd** | ✅ | ❌ | ❌ | ❌ | ✅ |
| **WeTrakr** | ✅ | ❌ | ❌ | ❌ | ❌ |
| **AniList** | ✅ | ❌ | ❌ | ❌ | ✅ |
| **Simkl** | ✅ | ❌ | ❌ | ❌ | ✅ |
| **MDBList** | ✅ | ❌ | ❌ | ❌ | ✅ |
| **Sofa Sidekick** | ✅ | ❌ | ❌ | ❌ | ❌ |
| **Plex/Jellyfin/Kodi** | ✅ | ❌ | ✅ | ❌ | ❌ |
| **Real-Debrid/TorBox/AllDebrid** | ✅ | ✅ | ❌ | ❌ | ❌ |
| **Chrome Extension** | ✅ | ❌ | ❌ | ✅ | ❌ |
| **Self-Hosted** | ✅ | ✅ | ✅ | ❌ | ✅ |
| **Open Source** | ✅ | ✅ | ✅ | ❌ | ✅ |

### What Sets Us Apart

1. **Only tool that does it all** — Stremio addon + sync engine + dashboard in one package
2. **Widest service coverage** — 16+ services, including unique ones like WeTrakr and Sofa Sidekick
3. **Cookie-based services via Chrome extension** — No more manual DevTools copy-paste
4. **Real-time scrobbling** — WebSocket-powered, instant sync across all services when you press play
5. **Persistent config** — SQLite-backed, survives server restarts
6. **Resume position sync** — Pick up where you left off across devices
7. **Self-hosted and open-source** — Your data never leaves your machine. The Linux way.

---

## Stremio Addon

Self-hosted Stremio addon with hybrid auth — public catalogs + user-configured private catalogs and streams.

### Quick Start

```bash
cd addon
pip install -r requirements.txt

# Start server (with API modules on path)
cd addon
PYTHONPATH=/home/user/StreamSyncr/apis:/home/user/StreamSyncr/addon \
  screen -dmS stremio python3 server.py
```

### URLs

- **Configure:** http://localhost:7800/configure
- **Manifest:** http://localhost:7800/manifest.json
- **Token Manifest:** http://localhost:7800/{token}/manifest.json

### Flow

1. User visits `/configure`
2. Enters API keys and tokens for desired services
3. Gets a token-based manifest URL
4. Adds the URL to Stremio

### Catalogs (30 total)

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

### Streams (Debrid)

When a user selects a title, the addon resolves streams from:
- **Real-Debrid** — Torrents, unrestricted links
- **TorBox** — Torrents, unrestricted links  
- **AllDebrid** — Torrents, unrestricted links

### Data Export

Export all user data from connected services as JSON:

```bash
# Export data
curl -s http://localhost:7800/api/export/{token} > export.json
```

**Supported services:** Trakt, Simkl, WeTrakr, Sofa Sidekick, Plex, Jellyfin, AniList, MDBList, IMDb

### Real-Time Scrobbling

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

**Endpoints:**
- `WS /ws/scrobble?token={token}` — Real-time bidirectional WebSocket
- `POST /api/scrobble` — HTTP fallback for Kodi
- `GET /api/scrobble/now-playing` — Active sessions across all clients

### Resume Position Sync

Resume playback across devices. Positions are stored in SQLite and synced to Kodi/Jellyfin where supported.

**Endpoints:**
- `GET /api/resume/{item_id}?token={token}&media_type=movie` — Get resume position
- `POST /api/resume` — Save position (Kodi sends on heartbeat/stop)
- `GET /api/resume/all?token={token}` — All resume positions for a user

**How it works:**
- Kodi sends `position_seconds` and `total_seconds` on each heartbeat/stop
- On play, Kodi fetches resume position and seeks the player
- Positions >95% are cleared (treated as "watched")
- SQLite database at `~/.streamsyncr/config.db`

---

## API Reference

For detailed API documentation for all 15+ services, environment variables, Python usage examples, and critical notes, see **[docs/API_REFERENCE.md](docs/API_REFERENCE.md)**.

---

## License

MIT
