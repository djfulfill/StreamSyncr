# StreamSyncr

A unified streaming tracker — sync your watch history across 10+ services.

## Services

| Service | Module | Auth Type | Status |
|---------|--------|-----------|--------|
| [WeTrakr](https://wetrakr.com) | `wetrakr_api/` | Cookie (JWT) | ✅ Full client |
| [Trakt](https://trakt.tv) | `trakt_api/` | API key + token | ✅ Full client |
| [TMDB](https://themoviedb.org) | `tmdb_api/` | API key | ✅ Full client |
| [IMDb](https://www.imdb.com) | `imdb_api/` | Cookie (GraphQL) | ✅ Full client |
| [Letterboxd](https://letterboxd.com) | `letterboxd_api/` | Cookie (undocumented) | ✅ Lists + ratings |
| [Plex](https://plex.tv) | `plex_api/` | Token | ✅ Full client |
| [AniList](https://anilist.co) | `anilist_api/` | Optional OAuth | ✅ Full client |
| [Simkl](https://simkl.com) | `simkl_api/` | Client ID + OAuth | ✅ Full client |
| [Jellyfin](https://jellyfin.org) | `jellyfin_api/` | API key | ✅ Full client |

## Tools

| Tool | Description |
|------|-------------|
| `imdb_to_tmdb.py` | IMDb → TMDB ID converter |
| `trakt_to_csv.py` | Trakt JSON → IMDb CSV converter |
| `frontend/` | React + Vite dashboard |

---

## Quick Start

```bash
pip install requests
```

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

---

## Python Usage

### WeTrakr

```python
from wetrakr_api.client import WeTrakrClient

c = WeTrakrClient()
c.search("Inception")
c.mark_watched(internal_id, "movie")   # uses INTERNAL id
c.unwatch(tmdb_id, "movie")           # uses TMDB id
c.favorite(internal_id, "movie")
c.get_lists()
```

### Trakt

```python
from trakt_api import TraktClient

t = TraktClient()
t.search("Swordfish")
t.mark_watched_now(movies=[4977])
t.rate(8, movies=[4977])
t.lists()
t.collection()
t.history()
t.following()
t.scrobble_start(4977)
```

### TMDB

```python
from tmdb_api import TMDBClient

t = TMDBClient()
t.search_movie("Swordfish", year=2001)
t.movie(9705)
t.movie_watch_providers(9705)
t.list_create(session_id, "My List")
t.collection_items(10)
```

### IMDb

```python
from imdb_api import IMDbClient

c = IMDbClient()
c.get_lists()
c.get_ratings()
c.create_list("My List")
c.add_to_list("ls123", "tt0244244")
c.rate_title("tt0244244", 8)
```

### Letterboxd

```python
from letterboxd_api import LetterboxdClient

c = LetterboxdClient(cookies="...", csrf_token="...")
films = c.search_film("Swordfish")  # returns lid codes
c.create_list("My List", film_lids=["1Y0m", "1WhU"])
c.add_to_list("WfRB8", ["1Y0m"])
c.mark_watched("1Y0m")
```

### Plex

```python
from plex_api import PlexClient

c = PlexClient(base_url="http://localhost:32400", token="your_token")
c.get_libraries()
c.get_watch_history()
c.mark_watched(rating_key)
c.rate(rating_key, 8)
```

### AniList

```python
from anilist_api import AniListClient

c = AniListClient()
c.search_anime("Naruto")
c.get_trending()
c.get_user_anime_list("username", status="COMPLETED")
c.save_anime_list_entry(media_id=1, status="COMPLETED", score=9)
```

### Simkl

```python
from simkl_api import SimklClient

c = SimklClient(client_id="your_client_id")
c.search("Breaking Bad", media_type="show")
c.trending_shows()
c.add_to_history(movies=[SimklClient.make_item(simkl_id)])
```

### Jellyfin

```python
from jellyfin_api import JellyfinClient

c = JellyfinClient(base_url="http://localhost:8096", api_key="your_key", user_id="user_id")
c.get_libraries()
c.get_watch_history()
c.mark_watched(item_id)
c.search("Breaking Bad")
```

---

## CLI Commands

```bash
# Trakt
python -m trakt_api.cli me
python -m trakt_api.cli lists
python -m trakt_api.cli search "Swordfish"
python -m trakt_api.cli trending
python -m trakt_api.cli scrobble-start 4977

# TMDB
python -m tmdb_api.cli search "Swordfish"
python -m tmdb_api.cli movie 9705
python -m tmdb_api.cli watch-providers 9705

# IMDb → TMDB converter
python imdb_to_tmdb.py tt0244244
python imdb_to_tmdb.py --batch tt0244244 tt0133093

# Trakt → CSV converter
python trakt_to_csv.py /path/to/trakt/files/
python trakt_to_csv.py export.json --imdb --rating
```

---

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

## Frontend

React + Vite + Tailwind dashboard running on port 3030.

```bash
cd frontend
npm install
npm run dev    # http://localhost:3030
npm run build  # production build
```

### Features
- 8 services in Settings page (WeTrakr, Trakt, TMDB, IMDb, Plex, AniList, Simkl, Jellyfin)
- Service status dots in sidebar
- Unified library with grid/list modes
- Search across TMDB
- IMDb page (lists, ratings, recently viewed)
- Movie/show detail pages with TMDB metadata
- Cross-platform sync engine

---

## Files

```
StreamSyncr/
├── wetrakr_api/
│   ├── client.py
│   ├── trakt_to_csv.py
│   ├── mark_watched.py
│   ├── unwatch_all.py
│   └── README.md
├── trakt_api/
│   ├── client.py
│   └── cli.py
├── tmdb_api/
│   ├── client.py
│   └── cli.py
├── imdb_api/
│   ├── client.py
│   └── operations.py
├── letterboxd_api/
│   └── __init__.py
├── plex_api/
│   └── __init__.py
├── anilist_api/
│   └── __init__.py
├── simkl_api/
│   └── __init__.py
├── jellyfin_api/
│   └── __init__.py
├── imdb_to_tmdb.py
├── ROADMAP.md
└── README.md
```

---

## License

MIT
