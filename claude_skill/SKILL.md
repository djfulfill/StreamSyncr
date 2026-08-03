---
name: streamsyncr
description: |
  StreamSyncr — unified streaming tracker with WeTrakr, Trakt, and TMDB integration.
  Also converts Trakt JSON exports to IMDb CSV.
  
  TRIGGER when:
  - User mentions StreamSyncr, WeTrakr, or streaming tracker
  - User wants to mark shows/movies as watched
  - User wants to manage their streaming profile or lists
  - User wants to search for movies/shows
  - User wants to favorite or unfavorite items
  - User wants to see their watching stats or history
  - User wants to follow/unfollow users
  - User has Trakt JSON exports and wants IMDb CSV
  - User mentions Trakt collections, Trakt export, or Stremio export
  - User wants to convert tracking data to CSV with IMDb URLs
---

# StreamSyncr

## Quick Start

```bash
pip install requests
```

```python
from wetrakr_api.client import WeTrakrClient

c = WeTrakrClient(
    access_token="your_wta_at_token",
    refresh_token="your_wta_rt_token",
    username="your_username"
)

# Check profile
c.get_user()

# Search
c.search("Inception")

# Follow a user
c.follow_user(user_id)

# Mark something watched (use INTERNAL id from list items)
c.mark_watched(internal_id, "movie", use_release_date=True)

# Favorite something (use TMDB id)
c.favorite(tmdb_id, "movie")
```

## Getting Your Tokens

1. Log into [wetrakr.com](https://wetrakr.com)
2. Open DevTools (F12) → Application tab → Cookies → `wetrakr.com`
3. Copy these two values:

| Cookie | What it is |
|--------|-----------|
| `wta_at` | Access token (JWT) |
| `wta_rt` | Refresh token (JWT) |

Tokens expire after ~2 days. Re-login to refresh.

## CRITICAL: ID Types

WeTrakr has TWO different IDs:

| Operation | Use Which ID? |
|-----------|--------------|
| Mark watched | **Internal ID** (`item["id"]`) |
| Unwatch | **TMDB ID** (`item["ids"]["tmdb"]["id"]`) |
| Favorite | **TMDB ID** |
| Unfavorite | **TMDB ID** |

Mixing them up causes **silent failures** — API returns `200 {}` but nothing changes.

## Common Operations

### Mark List as Watched

```python
items = c.get_all_list_items(list_id)

# Mark movies (uses internal IDs)
movies = [i for i in items if i.get("type") != "show"]
for i in range(0, len(movies), 50):
    batch = movies[i:i+50]
    c._post("account/tracking", {
        "movies": [{"id": m["id"], "status": "watched", "use_release_date": True} for m in batch]
    })

# Mark shows (uses internal IDs)
shows = [i for i in items if i.get("type") == "show"]
for i in range(0, len(shows), 50):
    batch = shows[i:i+50]
    c._post("account/tracking", {
        "shows": [{"id": s["id"], "status": "watched", "use_release_date": True} for s in batch]
    })
```

### Favorite Items

```python
# Single item (TMDB ID)
c.favorite(tmdb_id, "movie")

# Batch favorite (uses TMDB IDs from list items)
c.favorite_batch(items)
```

### Get Profile Stats

```python
profile = c.get_user("username")
stats = profile["profile_stats"]["tracking"]
print(f"Watched: {stats['movies']['watched']} movies, {stats['shows']['watched']} shows")
```

### Bulk Unwatch (Start Fresh)

```python
from wetrakr_api.unwatch_all import bulk_unwatch_all
bulk_unwatch_all(c)
```

## API Reference

| Method | Endpoint | ID Type | Description |
|--------|----------|---------|-------------|
| `get_user(username)` | `GET /frontend/users/{username}` | — | User profile |
| `get_movie(tmdb_id)` | `GET /frontend/movies/{tmdb_id}` | TMDB | Movie details |
| `get_show(tmdb_id)` | `GET /frontend/shows/{tmdb_id}` | TMDB | Show details |
| `search(query)` | `GET /search/all?q=` | — | Search |
| `trending()` | `GET /search/trending` | — | Trending content |
| `get_lists()` | `GET /account/lists` | — | User lists |
| `get_all_list_items(id)` | `GET /account/lists/{id}/items` | — | List items |
| `mark_watched(id)` | `POST /account/tracking` | **Internal** | Mark watched |
| `unwatch(id)` | `POST /account/tracking/remove/all` | **TMDB** | Unwatch |
| `favorite(id)` | `POST /account/favorites` | **Internal** | Add to favorites |
| `unfavorite(id)` | `POST /account/favorites/remove` | **TMDB** | Remove from favorites |
| `add_note(tmdb_id, text)` | `POST /account/notes` | TMDB | Add personal note |
| `like_review(review_id)` | `POST /reviews/{id}/like` | — | Like a review |
| `set_list_membership(id, lists)` | `POST /account/lists/item/{type}/{id}` | TMDB | Bulk list membership |
| `pin_media(id, type)` | `PUT /account/preferences/pinned-media` | **Internal** | Pin to profile |
| `unpin_media()` | `PUT /account/preferences/pinned-media` | — | Unpin from profile |
| `get_watched()` | `GET /filters/auto/sys:watched` | — | Watched filter |
| `follow_user(id)` | `POST /users/{id}/follow` | — | Follow user |
| `unfollow_user(id)` | `DELETE /users/{id}/follow` | — | Unfollow user |
| `get_followers()` | `GET /account/followers` | — | List followers |
| `get_following()` | `GET /account/following` | — | List following |

## Auth Headers

All requests require:
```python
headers = {
    "wetrakr-api-country": "US",
    "wetrakr-api-language": "en-US",
}
cookies = {
    "wta_auth": "1",
    "wta_at": "access_token",
    "wta_rt": "refresh_token",
}
```

## Tips & Tricks

### Re-order Favorites
Favorites show most recently favorited first. To move items to the top:
1. Unfavorite the item
2. Favorite it again

### Pin Media to Profile
Pin a movie/show to appear on your profile:
```python
c.pin_media(5513, "movie")  # internal ID
c.unpin_media()
```

## Known Issues

1. **Display endpoints lag** — `GET /frontend/movies/{id}` may show `status: "none"` even after marking. Use `profile_stats.tracking` for accurate counts.
2. **Wrong release dates** — WeTrakr's DB has incorrect dates for many titles (e.g., Inception=1977).
3. **GET /favorites not implemented** — Returns 404, but POST works.
4. **Trakt OAuth broken** — Redirect URL points to dead `trakt.tv/welcome` instead of `app.trakt.tv`.

## Social Features

### Follow/Unfollow Users

```python
# Search for a user first
result = c.search("username", search_type="users")
user_id = result["data"]["groups"]["community"]["items"][0]["id"]

# Follow
c.follow_user(user_id)

# Unfollow
c.unfollow_user(user_id)

# See who you follow
c.get_following()

# See your followers
c.get_followers()
```

## Trakt JSON → IMDb CSV

Convert Trakt JSON exports to IMDb-ready CSV. Supports:

- **Trakt Collections** — directory of `collection-movies-*.json`, `collection-episodes-*.json`, `collection-shows.json`
- **Lunova Export** — single JSON with `watched_movies`, `watchlist`, `collection`, etc.
- **Stremio/MetaHub Export** — array of `{id, type, name, releaseInfo}`

```bash
python trakt_to_csv.py /path/to/Trakt\ Collections/          # directory of JSONs
python trakt_to_csv.py /path/to/trakt-export.json             # single export file
python trakt_to_csv.py /path/to/files/ -o custom.csv          # custom output name
python trakt_to_csv.py /path/to/files/ --types movies         # movies only
python trakt_to_csv.py /path/to/files/ --types shows episodes # shows + episodes
```

Output columns: `type, title, year, imdb_id, imdb_url, show, season, episode_number`

```python
from trakt_to_csv import convert

# Auto-detect format, write CSV
convert("/home/user/Trakt Collections/")

# Filter to movies only
convert("trakt-export.json", "movies_only.csv", types=["movies"])

# IMDb playlist format with ratings
convert("trakt-export.json", "imdb.csv", imdb=True, rating=True, release_date=True)
```

## Trakt API Client

Full client for the official Trakt.tv API. Requires env vars:

```bash
export TRAKT_API_KEY="your_api_key"
export TRAKT_TOKEN="your_bearer_token"
```

### Python Usage

```python
from trakt_api import TraktClient

t = TraktClient()

# Profile
t.me()

# Lists
t.lists()                          # all lists
t.list_items(12345)                 # items in list
t.list_create("New List")           # create list
t.add_to_list("My Favorites", movies=[4977])  # add by trakt ID
t.remove_from_list("My Favorites", movies=[4977])
t.movie_in_lists(4977)             # which lists contain a movie

# Collection
t.collection()                     # all collection
t.collection("movies")             # movies only
t.add_to_collection(movies=[{"ids": {"trakt": 4977}}])

# Watchlist
t.watchlist()
t.add_to_watchlist(movies=[4977])
t.remove_from_watchlist(movies=[4977])

# History
t.history()
t.mark_watched(movies=[{"ids": {"trakt": 4977}, "watched_at": "now"}])

# Ratings
t.ratings()
t.rate(8, movies=[4977])           # rate 1-10

# Search
t.search("Swordfish")
t.search_movie("Swordfish", year=2001)

# Trending / Popular
t.trending_movies()
t.popular_movies()

# Social
t.following()                      # who you follow
t.followers()                      # who follows you
t.follow_user("user")          # follow by username
t.unfollow_user("user")        # unfollow
t.is_following("user")         # check
t.user_profile("user")         # get profile

# Watched
t.history()                        # watch history
t.get_watched()                    # watched summary
t.get_watched_movies()             # all watched movies
t.get_watched_shows()              # all watched shows
t.mark_watched_now(movies=[4977])  # mark watched now
t.unwatch(movies=[4977])           # remove from history

# Favorites
t.get_favorites()                  # get favorites
t.favorite(movies=[4977])          # add to favorites
t.unfavorite(movies=[4977])        # remove from favorites

# Ratings
t.ratings()                        # get ratings
t.rate(8, movies=[4977])           # rate 1-10
t.remove_rating(movies=[4977])     # remove rating

# Plan to Watch
t.get_plantowatch()                # plan to watch list
t.watchlist()                      # same as above
t.add_to_watchlist(movies=[4977])  # add to watchlist
t.remove_from_watchlist(movies=[4977])

# Scrobbling (real-time tracking)
t.scrobble_start(4977)             # start watching
t.scrobble_pause(4977, progress=50.0)  # pause at 50%
t.scrobble_stop(4977, progress=100.0)  # stop/mark as watched
```

### CLI Usage

```bash
python -m trakt_api.cli me
python -m trakt_api.cli lists
python -m trakt_api.cli collection
python -m trakt_api.cli watchlist
python -m trakt_api.cli plan-to-watch
python -m trakt_api.cli history
python -m trakt_api.cli watched
python -m trakt_api.cli watched-movies
python -m trakt_api.cli watched-shows
python -m trakt_api.cli unwatch 4977 1234
python -m trakt_api.cli unwatch-all
python -m trakt_api.cli ratings
python -m trakt_api.cli search "Swordfish"
python -m trakt_api.cli trending
python -m trakt_api.cli favorites
python -m trakt_api.cli favorite 4977
python -m trakt_api.cli unfavorite 4977
python -m trakt_api.cli movie-in-lists 4977
python -m trakt_api.cli add-to-list "My Favorites" 4977 1234
python -m trakt_api.cli remove-from-list "My Favorites" 4977
python -m trakt_api.cli rate 8 4977
python -m trakt_api.cli watch 4977
python -m trakt_api.cli scrobble-start 4977
python -m trakt_api.cli scrobble-stop 4977 --progress 100.0
python -m trakt_api.cli following
python -m trakt_api.cli followers
python -m trakt_api.cli follow user
python -m trakt_api.cli unfollow user
python -m trakt_api.cli is-following user
python -m trakt_api.cli user user
```

## TMDB API Client

Full client for The Movie Database API. Requires `TMDB_API_KEY` env var.

```bash
export TMDB_API_KEY="your_api_key"
```

### Python Usage

```python
from tmdb_api import TMDBClient

t = TMDBClient()

# Search
t.search_movie("Swordfish", year=2001)
t.search_tv("Breaking Bad")
t.find_by_imdb("tt0244265")
t.find_movie("Inception")

# Trending / Popular
t.trending_movies()
t.trending_tv()
t.popular_movies()
t.popular_tv()
t.top_rated_movies()
t.now_playing()
t.upcoming()

# Details
t.movie(9705)                    # movie by TMDB ID
t.movie_credits(9705)            # cast + crew
t.movie_similar(9705)            # similar movies
t.movie_recommendations(9705)    # recommendations
t.movie_videos(9705)             # trailers
t.movie_watch_providers(9705)    # streaming availability

# TV
t.tv(1396)                       # show details
t.tv_season(1396, 1)             # season details
t.tv_episode(1396, 1, 1)         # episode details

# Genres
t.genres_movie()
t.genres_tv()

# Discover
t.discover_movies(genre=28, year=2024, rating=7.0)

# Lists (requires session_id for create/update/delete)
t.my_lists(session_id)                         # your lists
t.list_details(7101656)                         # list info
t.list_items(7101656)                           # items in list
t.list_create(session_id, "My List")            # create list
t.list_update(7101656, session_id, name="New")  # update list
t.list_delete(7101656, session_id)              # delete list
t.list_add_items(7101656, session_id, [9705])   # add movies
t.list_remove_items(7101656, session_id, [9705])# remove movies
t.list_clear(7101656, session_id)               # clear list
t.list_check_item(7101656, 9705)                # check if movie in list

# Collections
t.collection_items(10)                          # Star Wars collection
```

### CLI Usage

```bash
python -m tmdb_api.cli search "Swordfish"
python -m tmdb_api.cli search-tv "Breaking Bad"
python -m tmdb_api.cli movie 9705
python -m tmdb_api.cli tv 1396
python -m tmdb_api.cli trending
python -m tmdb_api.cli trending-tv
python -m tmdb_api.cli popular
python -m tmdb_api.cli popular-tv
python -m tmdb_api.cli top-rated
python -m tmdb_api.cli now-playing
python -m tmdb_api.cli upcoming
python -m tmdb_api.cli genres
python -m tmdb_api.cli similar 9705
python -m tmdb_api.cli cast 9705
python -m tmdb_api.cli find-imdb tt0244265
python -m tmdb_api.cli watch-providers 9705
python -m tmdb_api.cli discover --genre 28 --year 2024
python -m tmdb_api.cli list 7101656
python -m tmdb_api.cli list-items 7101656
python -m tmdb_api.cli collection-items 10
python -m tmdb_api.cli in-list 7101656 9705
python -m tmdb_api.cli create-list "My List" --session-id XXX
python -m tmdb_api.cli add-to-list 7101656 9705 550 --session-id XXX
python -m tmdb_api.cli remove-from-list 7101656 9705 --session-id XXX
python -m tmdb_api.cli clear-list 7101656 --session-id XXX
python -m tmdb_api.cli delete-list 7101656 --session-id XXX
```

## IMDb → TMDB Converter

Convert IMDb IDs to TMDB data (IDs, URLs, posters).

```bash
python imdb_to_tmdb.py tt0244244                    # single ID
python imdb_to_tmdb.py --batch tt0244244 tt0133093  # multiple IDs
python imdb_to_tmdb.py --file imdb_ids.txt          # text file (one per line)
python imdb_to_tmdb.py --csv movies.csv             # CSV with imdb_id column
python imdb_to_tmdb.py --csv movies.csv --column imdb  # custom column name
```

**Python:**
```python
from imdb_to_tmdb import convert_id, convert_url, batch_convert, convert_csv

result = convert_id("tt0244244")
# {'tmdb_id': 9705, 'title': 'Swordfish', 'poster': '...', ...}

results = batch_convert(["tt0244244", "tt0133093"])
convert_csv("movies.csv", "output.csv")
```

## Files

- `wetrakr_api/client.py` — Main API client class
- `wetrakr_api/trakt_to_csv.py` — Trakt JSON to IMDb CSV converter
- `trakt_api/client.py` — Full Trakt.tv API client
- `trakt_api/cli.py` — CLI for Trakt API
- `tmdb_api/client.py` — Full TMDB API client
- `tmdb_api/cli.py` — CLI for TMDB API
- `imdb_to_tmdb.py` — IMDb → TMDB ID converter
- `wetrakr_api/mark_watched.py` — Bulk mark-watched script
- `wetrakr_api/unwatch_all.py` — Bulk unwatch script
- `wetrakr_api/README.md` — Full API documentation
