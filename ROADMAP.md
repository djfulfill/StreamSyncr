# StreamSyncr Roadmap

## Completed
- [x] WeTrakr API client (reverse-engineered)
- [x] Trakt API client (official)
- [x] TMDB API client (official)
- [x] IMDb GraphQL client (read + write)
- [x] React frontend (Dashboard, Library, Search, Sync, Settings)
- [x] IMDb frontend integration (proxy server, page, settings)

## In Progress
- [ ] Letterboxd API integration

## Planned

### Phase 1: Social Tracking
- [ ] **Letterboxd** — Lists, ratings, diary entries, watchlist
- [ ] **Serializd** — TV show tracking (Letterboxd for TV)

### Phase 2: Self-Hosted Media
- [ ] **Plex** — Watch history, ratings, collections
- [ ] **Jellyfin** — Open-source media server sync

### Phase 3: Anime
- [ ] **AniList** — GraphQL API, anime/manga tracking
- [ ] **MyAnimeList (MAL)** — Legacy anime database

### Phase 4: Streaming Discovery
- [ ] **JustWatch** — Where to stream content

### Phase 5: Cross-Platform Sync
- [ ] Bidirectional sync engine
- [ ] Conflict resolution
- [ ] Background sync service
- [ ] Sync history/audit log

## API Reference

### Letterboxd (undocumented, internal API)
- **Base URL**: `https://letterboxd.com`
- **Auth**: Cookie-based (`cf_clearance`, `letterboxd.user.CURRENT`, `com.xk72.webparts.csrf`)
- **Film lookup**: `GET /s/autocompletefilm?q={query}` → returns `lid` (Letterboxd ID)
- **List create**: `POST /api/v0/lists` with `entries` array using `lid` codes
- **List update**: `PATCH /api/v0/lists` with `lists` and `listables` arrays
- **Cloudflare protected**: Requires browser-like headers, may need periodic cookie refresh
- **Film code format**: Short alphanumeric `lid` (e.g., `1Y0m` for Swordfish)
