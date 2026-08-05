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

## Completed (Phase 4)
- [x] **Chrome Extension** — Auto-extract cookies for IMDb, Letterboxd, WeTrakr, Sofa Sidekick
- [x] Extension auto-sync via `chrome.cookies.onChanged` listener + 5-min alarm
- [x] Content script bridges extension ↔ React app via `postMessage`
- [x] Backend extension endpoints (`/api/extension/*`)
- [x] Settings.jsx ExtensionPanel with install instructions + service status grid
- [x] **Kodi Addon** — `plugin.video.streamsyncr` for Kodi 21 Omega+
- [x] Kodi addon catalog browsing (Trakt, TMDB, IMDb, WeTrakr catalogs)
- [x] Kodi addon debrid stream resolution (Real-Debrid, TorBox, AllDebrid)
- [x] Kodi addon scrobbling (auto-sync watch progress to all services)
- [x] Kodi addon settings dialog (backend URL, config token, catalog preferences)
- [x] **Real-Time Scrobbling** — WebSocket-powered instant sync across all services
- [x] Scrobble endpoints (`/ws/scrobble`, `/api/scrobble`, `/api/scrobble/now-playing`)
- [x] Fan-out to Trakt, WeTrakr, Plex, Jellyfin, Simkl, Letterboxd, Sofa Sidekick, AniList
- [x] 90% threshold marks as watched, dedup window prevents duplicates

## Completed (Phase 5)
- [x] **Persistent Config** — SQLite database at `~/.streamsyncr/config.db`
- [x] ConfigStore class with dict-compatible interface (drop-in replacement)
- [x] Config survives server restarts (no more in-memory dict)
- [x] **Resume Position Sync** — Cross-device playback resume
- [x] ResumeStore class for position CRUD (UNIQUE per item per user)
- [x] Positions >95% cleared as "watched"
- [x] Resume endpoints (`/api/resume/{item_id}`, `/api/resume`, `/api/resume/all`)
- [x] Kodi addon integration: fetch resume on play, seek player, send position on events

## Completed (Phase 6)
- [x] **Streaming Service Capture** — Chrome extension captures Netflix, Prime Video, Disney+, Max (HBO) via cookies
- [x] Extension host permissions for `*.netflix.com`, `*.primevideo.com`, `*.disneyplus.com`, `*.max.com`
- [x] **Cloud Relay Mode** — Extension sends cookies to configurable cloud endpoint alongside local
- [x] Cloud relay toggle in popup UI with endpoint + token config
- [x] Dual delivery: local self-hosted + cloud relay in parallel
- [x] **AniList Reviews** — Get, create, delete, rate reviews (`get_media_reviews`, `create_review`, `rate_review`)
- [x] **Xtream Codes IPTV** — Full API client for IPTV providers (URL + user + pass)
- [x] Xtream: live TV categories/streams, VOD categories/streams/info, series categories/streams/info
- [x] Xtream: EPG (short + full + XMLTV), search, M3U playlist, timeshift URLs
- [x] Extension popup split into Tracking Services + Streaming Services sections

## Competitive Gaps & Opportunities

These are areas where competitors (AIOStreams, WatchState, LimeStream, librarySync) have features we don't yet.

### High Priority
- [ ] **Docker deployment** — `docker-compose.yml` for one-command setup. WatchState and AIOStreams both have this. Critical for adoption.
- [ ] **Emby support** — Add `emby_api/` client. WatchState supports Emby. Gap in media server coverage.

### Medium Priority
- [x] ~~**Netflix/Disney+/HBO Max tracking**~~ — ✅ Done via Chrome extension cookie capture (Netflix, Prime Video, Disney+, Max)
- [x] ~~**Public hosted instance**~~ — ✅ Cloud relay mode enables hosted option without self-hosting
- [x] ~~**Resume position sync**~~ — ✅ Done (Phase 5)
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
