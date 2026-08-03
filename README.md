# WeTrakr API Suite

A collection of Python clients for streaming tracker APIs, plus tools for data conversion and a unified React frontend.

## Overview

| Module | Description | Auth |
|--------|-------------|------|
| `wetrakr_api/` | Reverse-engineered [WeTrakr](https://wetrakr.com) client | JWT cookies |
| `trakt_api/` | Full [Trakt.tv](https://trakt.tv) API client with scrobbling | API key + token |
| `tmdb_api/` | Full [TMDB](https://themoviedb.org) API client | API key |
| `imdb_to_tmdb.py` | IMDb → TMDB ID converter | TMDB API key |
| `trakt_to_csv.py` | Trakt JSON export → IMDb CSV converter | None |
| `frontend/` | React frontend - unified dashboard | Local storage |

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

## WeTrakr API

Reverse-engineered Python client for [WeTrakr](https://wetrakr.com) — a streaming tracker with no public API.

**This is not official.** Endpoints were captured from browser network requests and may break at any time.

### Getting Your Tokens

1. Go to [wetrakr.com](https://wetrakr.com) and log in
2. Open DevTools (F12) → Application tab → Cookies
3. Copy `wta_at` (access) and `wta_rt` (refresh)
4. Tokens expire after ~2 days

### Usage

```python
from wetrakr_api.client import WeTrakrClient

c = WeTrakrClient()

# Profile
c.get_user()

# Search
c.search("Inception")

# Mark watched (uses INTERNAL id from list items)
c.mark_watched(internal_id, "movie", use_release_date=True)

# Unwatch (uses TMDB id)
c.unwatch(tmdb_id, "movie")

# Favorites
c.favorite(internal_id, "movie")
c.unfavorite(tmdb_id, "movie")

# Lists
c.get_lists()
c.get_list_items(list_id)
```

### Critical: ID Types

WeTrakr has TWO different IDs:
- **TMDB ID** — from The Movie Database (e.g., `27205`)
- **Internal ID** — WeTrakr's own ID (e.g., `212517`)

| Operation | Use Which ID? |
|-----------|--------------|
| Mark watched | Internal ID |
| Unwatch | TMDB ID |
| Favorite | Internal ID |
| Unfavorite | TMDB ID |

---

## Trakt API

Full client for the [Trakt.tv](https://trakt.tv) API with scrobbling, lists, social features, and ratings.

### Usage

```python
from trakt_api import TraktClient

t = TraktClient()

# Profile
t.me()

# Lists
t.lists()
t.list_items(list_id)
t.add_to_list("My Favorites", movies=[4977])
t.remove_from_list("My Favorites", movies=[4977])
t.movie_in_lists(4977)

# Collection
t.collection()
t.add_to_collection(movies=[{"ids": {"trakt": 4977}}])

# Watchlist
t.watchlist()
t.add_to_watchlist(movies=[4977])

# History
t.history()
t.get_watched_movies()
t.mark_watched_now(movies=[4977])

# Ratings
t.ratings()
t.rate(8, movies=[4977])

# Favorites
t.get_favorites()
t.favorite(movies=[4977])

# Social
t.following()
t.followers()
t.follow_user("username")
t.unfollow_user("username")

# Scrobbling
t.scrobble_start(4977)
t.scrobble_pause(4977, progress=50.0)
t.scrobble_stop(4977, progress=100.0)

# Search
t.search("Swordfish")
t.search_movie("Swordfish", year=2001)

# Trending
t.trending_movies()
t.popular_movies()
```

### CLI

```bash
python -m trakt_api.cli me
python -m trakt_api.cli lists
python -m trakt_api.cli collection
python -m trakt_api.cli watchlist
python -m trakt_api.cli watched
python -m trakt_api.cli favorites
python -m trakt_api.cli ratings
python -m trakt_api.cli following
python -m trakt_api.cli follow user
python -m trakt_api.cli scrobble-start 4977
python -m trakt_api.cli scrobble-stop 4977 --progress 100.0
python -m trakt_api.cli search "Swordfish"
python -m trakt_api.cli trending
python -m trakt_api.cli add-to-list "My List" 4977 1234
python -m trakt_api.cli rate 8 4977
```

---

## TMDB API

Full client for [The Movie Database](https://themoviedb.org) API.

### Usage

```python
from tmdb_api import TMDBClient

t = TMDBClient()

# Search
t.search_movie("Swordfish", year=2001)
t.search_tv("Breaking Bad")
t.find_by_imdb("tt0244244")

# Trending / Popular
t.trending_movies()
t.popular_movies()
t.top_rated_movies()
t.now_playing()
t.upcoming()

# Details
t.movie(9705)
t.movie_credits(9705)
t.movie_similar(9705)
t.movie_watch_providers(9705)

# TV
t.tv(1396)
t.tv_season(1396, 1)

# Genres
t.genres_movie()

# Discover
t.discover_movies(genre=28, year=2024)

# Lists (requires session_id)
t.list_details(7101656)
t.list_items(7101656)
t.list_create(session_id, "My List")
t.list_add_items(7101656, session_id, [9705])
t.list_check_item(7101656, 9705)
t.collection_items(10)  # Star Wars collection
```

### CLI

```bash
python -m tmdb_api.cli search "Swordfish"
python -m tmdb_api.cli movie 9705
python -m tmdb_api.cli trending
python -m tmdb_api.cli popular
python -m tmdb_api.cli genres
python -m tmdb_api.cli cast 9705
python -m tmdb_api.cli watch-providers 9705
python -m tmdb_api.cli collection-items 10
python -m tmdb_api.cli list 7101656
```

---

## IMDb → TMDB Converter

Convert IMDb IDs to TMDB IDs, URLs, and poster images.

### Usage

```bash
# Single ID
python imdb_to_tmdb.py tt0244244

# Batch
python imdb_to_tmdb.py --batch tt0244244 tt0133093 tt0062622

# Text file (one ID per line)
python imdb_to_tmdb.py --file imdb_ids.txt

# CSV with IMDb column
python imdb_to_tmdb.py --csv movies.csv --column imdb_id
```

### Python

```python
from imdb_to_tmdb import convert_id, batch_convert, convert_csv

result = convert_id("tt0244244")
# {'tmdb_id': 9705, 'title': 'Swordfish', 'poster': '...', 'url': '...'}

results = batch_convert(["tt0244244", "tt0133093"])
convert_csv("movies.csv", "output.csv")
```

---

## Trakt CSV Converter

Convert Trakt JSON exports to IMDb CSV format.

### Supported Formats

1. **Trakt Collections** — `collection-movies-*.json` files
2. **Lunova Export** — single JSON with `watched_movies`, `collection`, etc.
3. **Stremio/MetaHub** — array of `{id, type, name}`

### Usage

```bash
# Auto-detect format
python trakt_to_csv.py /path/to/trakt/files/

# Filter to movies only
python trakt_to_csv.py export.json --types movies

# IMDb playlist format
python trakt_to_csv.py export.json --imdb

# Include ratings
python trakt_to_csv.py export.json --imdb --rating

# Include release dates
python trakt_to_csv.py export.json --imdb --release-date
```

### Python

```python
from trakt_to_csv import convert

convert("/path/to/Trakt Collections/")
convert("export.json", "movies.csv", types=["movies"])
convert("export.json", "imdb.csv", imdb=True, rating=True)
```

---

## API Comparison

| Feature | WeTrakr | Trakt | TMDB |
|---------|---------|-------|------|
| Scrobbling | ❌ | ✅ | ❌ |
| Lists | ✅ | ✅ | ✅ |
| Ratings | ❌ | ✅ | ✅ (session) |
| Favorites | ✅ | ✅ | ✅ (session) |
| Follow Users | ✅ | ✅ | ❌ |
| Watch History | ✅ | ✅ | ❌ |
| Search | ✅ | ✅ | ✅ |
| Trending | ✅ | ✅ | ✅ |
| Streaming Providers | ❌ | ❌ | ✅ |
| Poster Images | ❌ | ❌ | ✅ |

---

## Files

```
wetrakr/
├── wetrakr_api/
│   ├── client.py           # WeTrakr API client
│   ├── trakt_to_csv.py     # Trakt → IMDb CSV converter
│   ├── mark_watched.py     # Bulk mark-watched script
│   ├── unwatch_all.py      # Bulk unwatch script
│   └── README.md           # WeTrakr API docs
├── trakt_api/
│   ├── client.py           # Trakt API client
│   └── cli.py              # CLI for Trakt
├── tmdb_api/
│   ├── client.py           # TMDB API client
│   └── cli.py              # CLI for TMDB
├── imdb_to_tmdb.py         # IMDb → TMDB converter
└── README.md               # This file
```

---

## License

MIT — Use at your own risk. WeTrakr API is unofficial.
