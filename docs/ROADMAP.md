# StreamSyncr Roadmap

## Completed

### Phase 1: API Clients
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
- [x] Emby API client (watch history, ratings, favorites, playback reporting)
- [x] React frontend (Dashboard, Library, Search, Sync, Settings)
- [x] IMDb frontend integration (proxy server, page, settings)
- [x] Stremio addon (30 catalogs, token-based auth, configure page)

### Phase 2: Cross-Platform Sync
- [x] Sync engine core (ID resolution, conflict resolution strategies)
- [x] Sync engine operations (watched, ratings, favorites push to all services)
- [x] Frontend Sync page (strategy selection, dry run, progress, change preview)
- [x] 4 resolution strategies: watched overrides, newest wins, service priority, most complete
- [x] Background sync service (configurable interval, start/stop)
- [x] Sync history/audit log (JSONL append-only, stats, clear)

### Phase 3: Data Export
- [x] **Data Export** — Export all user data from connected services (JSON download)
- [x] Export endpoint `/api/export/{token}` — fetches from Trakt, Simkl, WeTrakr, Sofa Sidekick, Plex, Jellyfin, AniList, MDBList
- [x] Export button on configure page — one-click download of all connected service data
- [x] AniList catalog fix — added browser headers to bypass Cloudflare

### Phase 4: Chrome Extension & Kodi Addon
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

### Phase 5: Real-Time Scrobbling
- [x] **Real-Time Scrobbling** — WebSocket-powered instant sync across all services
- [x] Scrobble endpoints (`/ws/scrobble`, `/api/scrobble`, `/api/scrobble/now-playing`)
- [x] Fan-out to Trakt, WeTrakr, Plex, Jellyfin, Simkl, Letterboxd, Sofa Sidekick, AniList
- [x] 90% threshold marks as watched, dedup window prevents duplicates

### Phase 6: Persistence & Resume
- [x] **Persistent Config** — SQLite database at `~/.streamsyncr/config.db`
- [x] ConfigStore class with dict-compatible interface (drop-in replacement)
- [x] Config survives server restarts (no more in-memory dict)
- [x] **Resume Position Sync** — Cross-device playback resume
- [x] ResumeStore class for position CRUD (UNIQUE per item per user)
- [x] Positions >95% cleared as "watched"
- [x] Resume endpoints (`/api/resume/{item_id}`, `/api/resume`, `/api/resume/all`)
- [x] Kodi addon integration: fetch resume on play, seek player, send position on events

### Phase 7: Streaming Capture & IPTV
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

## In Progress
- [ ] Serializd API integration (TV tracking)
- [ ] Emby sync engine + scrobble wiring (client exists at `apis/emby_api/`, needs integration into sync engine and scrobble fan-out)

## Competitive Gaps & Opportunities

These are areas where competitors (AIOStreams, WatchState, LimeStream, librarySync) have features we don't yet.

### High Priority
- [ ] **Docker deployment** — `docker-compose.yml` for one-command setup. WatchState and AIOStreams both have this. Critical for adoption.
- [ ] **Emby sync/scrobble wiring** — Client exists, needs integration into sync engine and scrobble fan-out (Phase 5 gap).

### Medium Priority
- [ ] **Multi-user support** — WatchState supports per-user sync profiles. Family use case.

### Lower Priority
- [ ] **Conflict resolution UI** — WatchState has a web UI for manual conflict resolution. We have strategies but no manual override.
- [ ] **Webhook-based real-time sync** — WatchState uses webhooks for instant sync. We use polling intervals.
- [ ] **Android/iOS apps** — LimeStream is building iOS/Android SDKs. Native mobile would differentiate.
- [ ] **Prowlarr integration** — AIOStreams supports Prowlarr for private tracker indexing.

## Future Ideas
- [ ] **MyAnimeList (MAL)** — Anime tracking (legacy, but large user base)
- [ ] **Kitsu** — Anime tracking with social features
- [ ] **JustWatch** — Where to stream content (note: TMDB watch providers already cover this)
- [ ] **TVMaze** — TV show metadata (free, no auth)
