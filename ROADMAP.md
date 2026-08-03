# StreamSyncr Roadmap

## Completed
- [x] WeTrakr API client (unofficial)
- [x] Trakt API client (official)
- [x] TMDB API client (official)
- [x] IMDb GraphQL client (read + write)
- [x] Letterboxd API client (undocumented, list CRUD)
- [x] Plex API client (watch history, ratings, libraries)
- [x] AniList GraphQL client (anime/manga, user lists)
- [x] Simkl API client (TV/movie/anime, sync)
- [x] Jellyfin API client (watch history, ratings)
- [x] Kodi JSON-RPC client (movies, shows, episodes, library stats)
- [x] React frontend (Dashboard, Library, Search, Sync, Settings)
- [x] IMDb frontend integration (proxy server, page, settings)

## In Progress
- [ ] Serializd API integration (TV tracking)

## Completed (Phase 2)
- [x] Sync engine core (ID resolution, conflict resolution strategies)
- [x] Sync engine operations (watched, ratings, favorites push to all services)
- [x] Frontend Sync page (strategy selection, dry run, progress, change preview)
- [x] 4 resolution strategies: watched overrides, newest wins, service priority, most complete
- [x] Background sync service (configurable interval, start/stop)
- [x] Sync history/audit log (JSONL append-only, stats, clear)

## Planned

### Phase 1: Streaming Discovery
- [ ] **JustWatch** — Where to stream content (unofficial GraphQL)
- [ ] **TVMaze** — TV show metadata (free, no auth)

### Phase 2: Cross-Platform Sync ✅
- [x] Bidirectional sync engine (`sync_engine/`)
- [x] Conflict resolution (4 strategies)
- [x] Frontend sync page with progress tracking
- [x] Background sync service (auto-sync on interval)
- [x] Sync history/audit log

### Phase 3: Additional Services
- [ ] **MyAnimeList (MAL)** — Legacy anime database
- [ ] **Kitsu** — Anime tracking with social features
- [ ] **TV Time** — TV tracking (shutting down July 2026, migrate users)
- [ ] **Kinopoisk** — Russian movie database

## API Reference

### Plex (REST, documented)
- **Base URL**: `http://<server>:32400`
- **Auth**: Token-based (`X-Plex-Token`)
- **Returns**: JSON (add `Accept: application/json`)
- **Key endpoints**: `/library/sections`, `/library/metadata/{id}`, `/:/scrobble`
- **GUIDs**: Each item has `Guids` array with IMDb, TMDb, TVDB IDs

### AniList (GraphQL, documented)
- **Endpoint**: `https://graphql.anilist.co`
- **Auth**: Optional OAuth2 (90 req/min without auth)
- **Key queries**: `Page`, `Media`, `MediaListCollection`, `Viewer`
- **Mutations**: `SaveMediaListEntry`, `DeleteMediaListEntry`, `ToggleFavourite`

### Simkl (REST, documented)
- **Base URL**: `https://api.simkl.com`
- **Auth**: Client ID + optional OAuth2
- **Key endpoints**: `/sync/history`, `/sync/all-items`, `/sync/activities`
- **Sync model**: Two-phase — initial pull + incremental via `date_from`
- **Rate limit**: Batch writes to avoid `rate_limit` errors

### Jellyfin (REST, documented)
- **Base URL**: `http://<server>:8096`
- **Auth**: API key (`X-Emby-Token`)
- **Key endpoints**: `/Users/{id}/Items`, `/Shows/{id}/Episodes`, `/Items/{id}/Played`
- **Plugins**: Playback Reporting, Trakt, Simkl sync available

### Letterboxd (undocumented, internal API)
- **Base URL**: `https://letterboxd.com`
- **Auth**: Cookie-based (`cf_clearance`, `letterboxd.user.CURRENT`, `com.xk72.webparts.csrf`)
- **Film lookup**: `GET /s/autocompletefilm?q={query}` → returns `lid` (Letterboxd ID)
- **List create**: `POST /api/v0/lists` with `entries` array using `lid` codes
- **List update**: `PATCH /api/v0/lists` with `lists` and `listables` arrays
- **Cloudflare protected**: Requires browser-like headers, may need periodic cookie refresh
- **Film code format**: Short alphanumeric `lid` (e.g., `1Y0m` for Swordfish)

### Serializd (unofficial, community-maintained)
- **Library**: `serializd-py` (Python)
- **Auth**: Token-based
- **Status**: Community-maintained, may break

### JustWatch (unofficial GraphQL)
- **Note**: No official public API
- **Workaround**: Third-party wrappers (RapidAPI, Apify)
- **Alternative**: Use TMDB watch providers (already integrated)
