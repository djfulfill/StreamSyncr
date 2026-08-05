# StreamSyncr Roadmap

## Completed
- [x] WeTrakr API client (unofficial, JWT cookies)
- [x] Trakt API client (official, API key + token)
- [x] TMDB API client (official, API key)
- [x] IMDb GraphQL client (read + write, cookie-based)
- [x] Letterboxd API client (undocumented, search + list CRUD, Cloudflare-protected reads)
- [x] Plex API client (watch history, ratings, libraries)
- [x] AniList GraphQL client (anime/manga, user lists)
- [x] Simkl API client (TV/movie/anime, sync)
- [x] Jellyfin API client (watch history, ratings)
- [x] Kodi JSON-RPC client (movies, shows, episodes, library stats)
- [x] MDBList API client (multi-rating lists, search, path-based endpoints)
- [x] Sofa Sidekick API client (movies, upcoming, stats, cookie-based)
- [x] React frontend (Dashboard, Library, Search, Sync, Settings)
- [x] IMDb frontend integration (proxy server, page, settings)
- [x] Stremio addon (30 catalogs, token-based auth, configure page)

## In Progress
- [ ] Serializd API integration (TV tracking)

## Completed (Phase 2)
- [x] Sync engine core (ID resolution, conflict resolution strategies)
- [x] Sync engine operations (watched, ratings, favorites push to all services)
- [x] Frontend Sync page (strategy selection, dry run, progress, change preview)
- [x] 4 resolution strategies: watched overrides, newest wins, service priority, most complete
- [x] Background sync service (configurable interval, start/stop)
- [x] Sync history/audit log (JSONL append-only, stats, clear)

## Completed (Phase 3)
- [x] **Data Export** — Export all user data from connected services (JSON download)
- [x] Export endpoint `/api/export/{token}` — fetches from Trakt, Simkl, WeTrakr, Sofa Sidekick, Plex, Jellyfin, AniList, MDBList
- [x] Export button on configure page — one-click download of all connected service data
- [x] AniList catalog fix — added browser headers to bypass Cloudflare

## Competitive Gaps & Opportunities

These are areas where competitors (AIOStreams, WatchState, LimeStream, librarySync) have features we don't yet.

### High Priority
- [ ] **Docker deployment** — `docker-compose.yml` for one-command setup. WatchState and AIOStreams both have this. Critical for adoption.
- [ ] **Persistent config storage** — SQLite or Redis. Currently in-memory, lost on restart. WatchState uses SQLite.
- [ ] **Real-time scrobbling** — Auto-mark watched in Trakt/Simkl when playback completes in Stremio. Trakt Integration addon does this.
- [ ] **Emby support** — Add `emby_api/` client. WatchState supports Emby. Gap in media server coverage.

### Medium Priority
- [ ] **Netflix/Disney+/HBO Max tracking** — LimeStream's 15 platforms are compelling. Chrome extension could scrape these via cookie extraction.
- [ ] **Public hosted instance** — AIOStreams and LimeStream offer hosted versions. Lower barrier to entry.
- [ ] **Resume position sync** — WatchState syncs play progress (resume point). We only sync watched/unwatched.
- [ ] **Multi-user support** — WatchState supports per-user sync profiles. Family use case.

### Lower Priority
- [ ] **Webhook-based real-time sync** — WatchState uses webhooks for instant sync. We use polling intervals.
- [ ] **Conflict resolution UI** — WatchState has a web UI for manual conflict resolution. We have strategies but no manual override.
- [ ] **Android/iOS apps** — LimeStream is building iOS/Android SDKs. Native mobile would differentiate.
- [ ] **Prowlarr integration** — AIOStreams supports Prowlarr for private tracker indexing.

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
- [x] **Sofa Sidekick** — Private show & movie tracker (TV Time replacement)

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

### Letterboxd (undocumented, cookie-based)
- **Base URL**: `https://letterboxd.com`
- **Auth**: Cookie-based (`cf_clearance`, `letterboxd.user.CURRENT`, `com.xk72.webparts.csrf`)
- **Required cookies**: 3 cookies from browser after logging in
- **CSRF token**: `com.xk72.webparts.csrf` value (used as `x-csrf-token` header)
- **Working endpoints**: Search, create list, add to list, remove from list, mark watched, add to watchlist
- **Blocked endpoints (Cloudflare)**: Diary, watchlist read, ratings, user data
- **Film lookup**: `GET /s/autocompletefilm?q={query}` → returns `lid` (Letterboxd ID)
- **List create**: `POST /api/v0/lists` with `entries` array using `lid` codes
- **Film code format**: Short alphanumeric `lid` (e.g., `1skk` = Inception, `eDGs` = The Batman)

### Serializd (unofficial, community-maintained)
- **Library**: `serializd-py` (Python)
- **Auth**: Token-based
- **Status**: Community-maintained, may break

### JustWatch (unofficial GraphQL)
- **Note**: No official public API
- **Workaround**: Third-party wrappers (RapidAPI, Apify)
- **Alternative**: Use TMDB watch providers (already integrated)

### Sofa Sidekick (undocumented, cookie-based)
- **Base URL**: `https://app.sofasidekick.com/api`
- **Auth**: Cookie-based (`session_id`, `cf_clearance`, `__cf_bm`)
- **Data source**: TheTVDB
- **Working endpoints**: `movies` (235 items), `upcoming`, `stats`, `account`
- **Blocked endpoints (Cloudflare)**: `shows`, `watchlist`, `history`
- **Show operations**: follow/unfollow, mark episode watched/unwatched, update status
- **Movie operations**: add/remove, mark watched/unwatched
- **Stats**: episodes watched, watch time, most watched shows, busiest month

### MDBList (REST, documented)
- **Base URL**: `https://api.mdblist.com`
- **Auth**: API key (`apikey` query param) or OAuth 2.0
- **Path-based endpoints**:
  - `GET /search/{media_type}?query={query}` — search movies/shows
  - `GET /{provider}/{media_type}/{media_id}` — get by IMDb/TMDb/TVDB
  - `GET /lists/{listid}/items` — list items (IDs use `ids.imdb` not `ids.imdbid`)
- **Key endpoints**: `/user`, `/lists/user`, `/lists/{listid}/items`
- **Lists**: User's lists become dynamic Stremio catalogs
- **Rate limits**: 1,000/day (free), up to 250,000/day (VIP)
