![Description](./StreamSyncr-banner.png)

# StreamSyncr

A unified streaming tracker — sync your watch history across 17+ services, with a self-hosted Stremio addon.

## Services

### Tracking & Lists

| Service | Status |
|---------|--------|
| [Trakt](https://trakt.tv) | ✅ Full client |
| [TMDB](https://themoviedb.org) | ✅ Full client |
| [IMDb](https://www.imdb.com) | ✅ Recently viewed, lists, ratings |
| [WeTrakr](https://wetrakr.com) | ✅ Favorites, watchlist, ratings |
| [AniList](https://anilist.co) | ✅ Trending, popular |
| [Simkl](https://simkl.com) | ✅ Trending, popular |
| [MDBList](https://mdblist.com) | ✅ Lists + search |
| [Sofa Sidekick](https://sofasidekick.com) | ✅ Movies + upcoming |
| [Letterboxd](https://letterboxd.com) | ✅ Search + list CRUD |

### Media Servers

| Service | Status |
|---------|--------|
| [Plex](https://plex.tv) | ✅ Full client |
| [Jellyfin](https://jellyfin.org) | ✅ Full client |
| [Emby](https://emby.media) | ✅ Full client |
| [Kodi](https://kodi.tv) | ✅ Full client |

### Debrid Services (Stream Sources)

| Service | Status |
|---------|--------|
| [Real-Debrid](https://real-debrid.com) | ✅ Full client |
| [TorBox](https://torbox.app) | ✅ Full client |
| [AllDebrid](https://alldebrid.com) | ✅ Full client |

### IPTV Services

| Service | Status |
|---------|--------|
| Xtream Codes | ✅ Live TV, VOD, Series, EPG |

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
2. **Widest service coverage** — 17+ services, including unique ones like WeTrakr and Sofa Sidekick
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

For addon flow, catalogs, stream resolution, data export, and resume sync details, see **[docs/API_REFERENCE.md](docs/API_REFERENCE.md)**.

## Frontend

React + Vite + Tailwind dashboard on port 3030.

```bash
cd frontend
npm install
npm run dev    # http://localhost:3030
npm run build  # production build
```

## CLI

Command-line interface for all services. Set env vars or enter them interactively.

```bash
# Check service status
python3 streamsyncr.py status

# Search & browse
python3 streamsyncr.py trakt search "Inception"
python3 streamsyncr.py plex libraries
python3 streamsyncr.py emby movies --limit 10
python3 streamsyncr.py xtream live-streams --category 1
python3 streamsyncr.py anilist trending

# Mark watched
python3 streamsyncr.py plex mark-watched 12345
python3 streamsyncr.py trakt mark-watched 4977

# IPTV
python3 streamsyncr.py xtream info
python3 streamsyncr.py xtream vod-categories
python3 streamsyncr.py xtream m3u
```

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

---

## API Reference

For detailed API documentation for all 17+ services, architecture, environment variables, Python usage examples, and critical notes, see **[docs/API_REFERENCE.md](docs/API_REFERENCE.md)**.

---

## License

MIT
