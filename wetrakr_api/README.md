# WeTrakr API Client

Reverse-engineered Python client for [WeTrakr](https://wetrakr.com) — a streaming tracker in super beta with no public API.

**This is not official.** Endpoints were captured from browser network requests and may break at any time.

---

## For Beginners (Step-by-Step)

### What You Need

1. **Python 3** installed on your computer
2. **Your WeTrakr username** (e.g., `djfulfill`)
3. **Two JWT tokens** from your browser (explained below)
4. **List IDs** from the URLs on your lists page

### Step 1: Install Python & Requests

```bash
pip install requests
```

### Step 2: Get Your JWT Tokens

1. Go to [wetrakr.com](https://wetrakr.com) and log in
2. Open **DevTools** (press `F12` or right-click → Inspect)
3. Click the **Application** tab (Chrome) or **Storage** tab (Firefox)
4. On the left, expand **Cookies** → click `https://wetrakr.com`
5. Find and copy these two values:

| Cookie Name | What It Is | Looks Like |
|-------------|-----------|------------|
| `wta_at` | Access token | `eyJhbGciOiJIUzI1NiIs...` (long string) |
| `wta_rt` | Refresh token | `eyJhbGciOiJIUzI1NiIs...` (long string) |

6. Save them somewhere safe — you'll need them every time you run the script

### Step 3: Find Your List IDs

1. Go to your lists page on WeTrakr
2. Click on a list — the URL will look like: `wetrakr.com/lists/19882`
3. The number at the end is your **List ID** (e.g., `19882`)

### Step 4: Run the Script

```bash
python3 mark_watched.py
```

The script will ask you for:
- Your **username**
- Your **access token** (`wta_at`)
- Your **refresh token** (`wta_rt`)
- Which **list IDs** to mark (comma-separated, e.g., `19882, 19881`)

It will then mark everything as watched with release dates.

### Step 5: Verify

Go back to WeTrakr and check your profile — the watched counts should match.

### Token Expiry

JWT tokens expire after about **2 days**. If you get auth errors:
1. Log back into WeTrakr
2. Copy the new `wta_at` and `wta_rt` cookies
3. Re-run the script with the new tokens

---

## Quick Start (Developer)

```bash
pip install requests
export WETRAKR_ACCESS_TOKEN="your_access_token"
export WETRAKR_REFRESH_TOKEN="your_refresh_token"
```

```python
from client import WeTrakrClient

c = WeTrakrClient()

# Search
c.search("Inception")

# Movie details
c.get_movie(27205)  # Inception

# Your profile
c.get_user()

# Mark something watched (use INTERNAL id from list items)
c.mark_watched(internal_id, "movie", use_release_date=True)

# Unwatch something (use TMDB id)
c.unwatch(27205, "movie")

# Favorite something (use INTERNAL id, same as mark_watched)
c.favorite(internal_id, "movie")

# Unfavorite something (use TMDB id, same as unwatch)
c.unfavorite(27205, "movie")
```

## Tips & Tricks

### Re-order Favorites

Favorites are displayed with the **most recently favorited first**. To move items to the top of your favorites (and thus to the main screen):

1. Unfavorite the item
2. Favorite it again

```python
# Move to top of favorites
c.unfavorite(tmdb_id, "movie")  # remove
c.favorite(internal_id, "movie")  # re-add (now at top)
```

This is useful for featuring specific items on your profile's main screen.

### Pin Media to Profile

Pin a specific movie or show to your profile page:

```python
# Pin Hackers to your profile
c.pin_media(5513, "movie")  # uses internal ID

# Unpin
c.unpin_media()
```

The pinned media appears prominently on your profile. Requires both `media_id` (internal ID) and `type` ("movie" or "show").

## CLI

```bash
python client.py profile
python client.py search "Breaking Bad"
python client.py movie 27205
python client.py trending
python client.py lists
python client.py last          # recent tracking activity
python client.py watched       # watched filter
python client.py watching      # watching filter
python client.py plantowatch   # plan to watch filter
python client.py nowplaying    # now playing filter
```

## Bulk Mark as Watched

Mark all items from your lists as watched (with release dates):

```bash
python mark_watched.py              # interactive confirm
python mark_watched.py --dry-run    # preview only
python mark_watched.py --no-release-date  # use today's date
```

## Bulk Unwatch (Start Fresh)

Remove ALL tracking from your account:

```bash
python unwatch_all.py
```

## Getting Your Tokens (Advanced)

1. Log into [wetrakr.com](https://wetrakr.com)
2. Open DevTools → Network tab → filter by Fetch/XHR
3. Navigate to your profile
4. Find any request to `/proxy/...`
5. Copy from the `Cookie` header:
   - `wta_at=...` → `WETRAKR_ACCESS_TOKEN`
   - `wta_rt=...` → `WETRAKR_REFRESH_TOKEN`
6. Optionally copy the username from the `wta_user` cookie → `WETRAKR_USERNAME`

## CRITICAL: ID Types

**This is the most important thing to understand about this API.**

WeTrakr items have TWO different IDs:
- **TMDB ID** — from The Movie Database (e.g., `27205` for Inception)
- **Internal ID** — WeTrakr's own ID (e.g., `212517` for Alita: Battle Angel)

| Operation | Use Which ID? | Example |
|-----------|--------------|---------|
| **Mark watched** | Internal ID | `{"movies": [{"id": 212517, "status": "watched"}]}` |
| **Unwatch (remove/all)** | TMDB ID | `{"movies": [{"id": 399579, "status": "watched"}]}` |
| **Favorite** | Internal ID | `{"movies": [{"id": 212517}]}` |
| **Unfavorite (remove)** | TMDB ID | `{"movies": [{"id": 399579}]}` |
| **Get movie details** | TMDB ID | `GET /frontend/movies/399579` |
| **Get show details** | TMDB ID | `GET /frontend/shows/1399` |

**Why?** The tracking and favorites systems use internal IDs, but the remove endpoints use TMDB IDs. Mixing them up causes silent failures — the API returns `200 {}` but nothing changes.

### How to Get Internal IDs

Internal IDs are in list items:

```python
items = c.get_all_list_items(list_id)
for item in items:
    internal_id = item["id"]              # ← use this for mark_watched
    tmdb_id = item["ids"]["tmdb"]["id"]   # ← use this for unwatch
```

## Integrations

### Discord (OAuth2)

| Method | Endpoint | Description |
|--------|----------|-------------|
| `get_discord_status()` | `GET /proxy/integrations/discord` | Check connection status |
| `get_discord_connect_url()` | `GET /proxy/integrations/discord/connect` | Get OAuth2 authorize URL |
| `connect_discord(code, state)` | `POST /proxy/integrations/discord/callback` | Complete OAuth2 flow |
| `disconnect_discord()` | `DELETE /proxy/integrations/discord` | Disconnect Discord |

### Trakt

| Method | Endpoint | Description |
|--------|----------|-------------|
| `get_trakt_status()` | `GET /proxy/integrations/trakt` | Check connection status |

**See [DISCORD_OAUTH2_GUIDE.md](../DISCORD_OAUTH2_GUIDE.md) for full implementation guide.**

---

## API Reference

### User

| Method | Endpoint | Description |
|--------|----------|-------------|
| `get_user(username)` | `GET /frontend/users/{username}` | User profile with stats |
| `get_my_progress()` | `GET /frontend/users/me/watching-progress` | Watching progress summary |
| `get_total_time(target)` | `GET /account/tracking/watching/total-time` | Total watched time |
| `get_last_tracking()` | `GET /account/last/tracking` | Recent tracking activity |

### Content

| Method | Endpoint | Description |
|--------|----------|-------------|
| `get_movie(tmdb_id)` | `GET /frontend/movies/{tmdb_id}` | Full movie details + tracking state |
| `get_show(tmdb_id)` | `GET /frontend/shows/{tmdb_id}` | Full show details |
| `get_season(show_id, n)` | `GET /frontend/shows/{id}/seasons/{n}` | Season details |
| `get_episode(show_id, s, e)` | `GET /frontend/shows/{id}/seasons/{s}/episodes/{e}` | Episode details |
| `get_reviews(tmdb_id, type)` | `GET /{type}/{id}/reviews` | User reviews |

### Search & Discovery

| Method | Endpoint | Description |
|--------|----------|-------------|
| `search(query, type, max)` | `GET /search/all?q=&type=&maxPerGroup=` | Search movies, shows, people |
| `trending(filter_type, limit)` | `GET /search/trending?filter_type=&limit=` | Trending content |

### Filters

| Method | Endpoint | Description |
|--------|----------|-------------|
| `get_watched()` | `GET /filters/auto/sys:watched` | Watched content |
| `get_watching()` | `GET /filters/auto/sys:watching` | Currently watching |
| `get_waiting()` | `GET /filters/auto/sys:waiting` | Waiting for new episodes |
| `get_plantowatch()` | `GET /filters/auto/sys:plantowatch` | Plan to watch |
| `get_nowplaying()` | `GET /filters/auto/sys:nowplaying` | Now playing |
| `get_next_to_watch()` | `GET /filters/auto/sys:nexttowatch` | Next to watch |
| `get_upcoming()` | `GET /filters/auto/sys:upcoming` | Upcoming releases |
| `get_favorites()` | `GET /filters/auto/sys:favorites` | Favorites |
| `get_ratings()` | `GET /filters/auto/sys:ratings` | Rated content |

### Lists

| Method | Endpoint | Description |
|--------|----------|-------------|
| `get_lists()` | `GET /account/lists` | All user lists |
| `get_list_items(list_id)` | `GET /account/lists/{id}/items` | Items from a list |
| `get_all_list_items(list_id)` | `GET /account/lists/{id}/items` | All items (auto-paginates) |

### Social

| Method | Endpoint | Description |
|--------|----------|-------------|
| `get_user_by_id(user_id)` | `GET /users/{id}` | Get user by ID (includes VIP status) |
| `get_followers()` | `GET /account/followers` | List your followers |
| `get_following()` | `GET /account/following` | List users you follow |
| `get_follow_requests()` | `GET /account/followers/requests` | Pending follow requests |
| `get_blocked_users()` | `GET /account/blocked` | Blocked users |
| `follow_user(user_id)` | `POST /users/{id}/follow` | Follow a user |
| `unfollow_user(user_id)` | `DELETE /users/{id}/follow` | Unfollow a user |

### Tracking (Write)

| Method | Endpoint | ID Type | Description |
|--------|----------|---------|-------------|
| `mark_watched(id, type, release)` | `POST /account/tracking` | Internal | Mark single item watched |
| `mark_batch_watched(items, release)` | `POST /account/tracking` | Internal | Mark multiple items watched |
| `unwatch(tmdb_id, type)` | `POST /account/tracking/remove/all` | TMDB | Unwatch single item |
| `unwatch_batch(items)` | `POST /account/tracking/remove/all` | TMDB | Unwatch multiple items |
| `unwatch_all(items)` | `POST /account/tracking/remove/all` | TMDB | Bulk unwatch all items |
| `favorite(id, type)` | `POST /account/favorites` | Internal | Add to favorites |
| `unfavorite(tmdb_id, type)` | `POST /account/favorites/remove` | TMDB | Remove from favorites |
| `add_note(tmdb_id, text)` | `POST /account/notes` | TMDB | Add personal note |
| `like_review(review_id)` | `POST /reviews/{id}/like` | — | Like a review |
| `unlike_review(review_id)` | `POST /reviews/{id}/unlike` | — | Unlike a review |
| `set_list_membership(id, lists)` | `POST /account/lists/item/{type}/{id}` | TMDB | Bulk list membership |
| `pin_media(id, type)` | `PUT /account/preferences/pinned-media` | Internal | Pin to profile |
| `unpin_media()` | `PUT /account/preferences/pinned-media` | — | Unpin from profile |

## All Discovered Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/proxy/frontend/users/{username}` | User profile |
| GET | `/proxy/frontend/movies/{tmdb_id}` | Movie detail |
| GET | `/proxy/frontend/shows/{tmdb_id}` | Show detail |
| GET | `/proxy/frontend/shows/{id}/seasons/{n}` | Season detail |
| GET | `/proxy/frontend/shows/{id}/seasons/{n}/episodes/{n}` | Episode detail |
| GET | `/proxy/frontend/users/me/watching-progress` | Watch progress |
| GET | `/proxy/search/all?q=&type=&maxPerGroup=` | Search |
| GET | `/proxy/search/trending?filter_type=&limit=` | Trending |
| GET | `/proxy/movies/{id}/reviews?limit=&page=&sort=` | Reviews |
| GET | `/proxy/account/tracking/watching/total-time` | Total time |
| GET | `/proxy/account/last/tracking` | Recent tracking activity |
| GET | `/proxy/filters/auto/sys:{name}` | Filters (see table above) |
| GET | `/proxy/account/lists` | User lists |
| GET | `/proxy/account/lists/{id}/items` | List items |
| POST | `/proxy/account/tracking` | Mark watched (INTERNAL id) |
| POST | `/proxy/account/tracking/remove/all` | Unwatch (TMDB id) |
| POST | `/proxy/account/favorites` | Add to favorites (INTERNAL id) |
| POST | `/proxy/account/favorites/remove` | Remove from favorites (TMDB id) |
| POST | `/proxy/account/notes` | Add personal note (TMDB id) |
| POST | `/proxy/reviews/{id}/like` | Like a review |
| POST | `/proxy/reviews/{id}/unlike` | Unlike a review |
| POST | `/proxy/account/lists/item/{type}/{id}` | Bulk list membership (TMDB id) |
| PUT | `/proxy/account/preferences/pinned-media` | Pin to profile (INTERNAL id) |
| GET | `/proxy/users/{id}` | Get user by ID |
| GET | `/proxy/account/followers` | List followers |
| GET | `/proxy/account/following` | List following |
| GET | `/proxy/account/followers/requests` | Pending follow requests |
| GET | `/proxy/account/blocked` | Blocked users |
| POST | `/proxy/users/{id}/follow` | Follow user |
| DELETE | `/proxy/users/{id}/follow` | Unfollow user |

## Payload Formats

### Mark Watched (POST /account/tracking)

```json
{
  "movies": [
    {"id": 212517, "status": "watched", "use_release_date": true}
  ],
  "shows": [
    {"id": 1593087, "status": "watched", "use_release_date": true}
  ]
}
```

**Note:** `id` must be the internal ID from list items, NOT the TMDB ID.

### Unwatch (POST /account/tracking/remove/all)

```json
{
  "movies": [
    {"id": 399579, "status": "watched"}
  ],
  "shows": [
    {"id": 1399, "status": "watched"}
  ]
}
```

**Note:** `id` must be the TMDB ID, NOT the internal ID. The `status` field is required but just `"watched"`.

## Tracking Statuses

Items can have these statuses:
- `watched` — watched
- `watching` — currently watching
- `plantowatch` — plan to watch
- `waiting` — waiting for new episodes
- `nowplaying` — currently playing
- `unwatch` — removed from tracking
- `none` — no tracking data

## Auth Details

- JWT tokens in cookies: `wta_at` (access), `wta_rt` (refresh)
- Custom headers: `wetrakr-api-country`, `wetrakr-api-language`
- Rate limit: 300 requests / 60 seconds
- CORS enabled with credentials

## Account State (2026-08-02)

After reverse engineering and testing:
- **Watched: 611 movies, 114 shows, 17,871 episodes**
- Lists: 15 lists fully marked as watched

### Known Issues

1. **Wrong release dates** — WeTrakr's internal DB has incorrect dates for many titles (e.g., Inception=1977, The Matrix=1953). Using `use_release_date: true` imports these wrong dates.
2. **ID confusion** — Marking needs internal IDs, unwatching needs TMDB IDs. The API silently ignores wrong IDs.
3. **Stats caching** — `profile_stats.tracking` counts may lag behind actual state.
4. **Filter endpoints broken** — All `GET /filters/auto/sys:*` endpoints return `state: null` even when data exists. Affects: watched, favorites, watching, plantowatch, etc. Use `profile_stats.tracking` for counts, website for verification.
5. **GET /account/favorites returns 404** — Not implemented. Use `GET /filters/auto/sys:favorites` (but it's also broken per #4).

## Bug Report (for WeTrakr devs)

**Date:** 2026-08-02

### Bug: Tracking data not reflected in display API endpoints

**Status:** Confirmed — data IS stored correctly and displays on the website, but API display endpoints return stale/empty data.

**Steps to reproduce:**
1. Mark items as watched via `POST /proxy/account/tracking`
2. Check profile stats via `GET /proxy/frontend/users/{username}` — shows correct counts ✓
3. Check individual item via `GET /proxy/frontend/movies/{tmdb_id}` — shows `status: "none"` with empty history ✗
4. Check watched filter via `GET /proxy/filters/auto/sys:watched` — returns `{"list_key":"sys:watched","state":null}` ✗
5. View on website — items correctly show as watched ✓

**Expected:** API display endpoints should match website behavior.

**Actual:** `profile_stats.tracking` and website show correct counts, but:
- `GET /frontend/movies/{tmdb_id}` returns `interactions.user.tracking.last.status: "none"` and empty `history: []`
- `GET /filters/auto/sys:watched` returns `state: null` (empty)

**Test data:**
- User: `djfulfill` (user_id: 6797)
- List: Cyber Crimes (list_id: 19884) — 34 movies, 5 shows marked as watched
- Profile stats: `movies.watched: 34, shows.watched: 5, episodes.watched: 178`
- Individual items (e.g., Hackers tmdb=10428): `status: "none"` via API, but shows watched on website

**Workaround:** Use `profile_stats.tracking` for counts, website for verification. Don't rely on `/frontend/movies/{id}` or `/filters/auto/sys:watched` for tracking status.

**Possible cause:** Display endpoints may be reading from a different data source or cache than the tracking write endpoint. The website frontend likely joins tracking data differently than the API endpoints.

### Bug: Trakt OAuth redirect URL is wrong

**Status:** Confirmed — link goes to dead URL instead of authorization page.

**Steps to reproduce:**
1. Go to Settings → Integrations → Connect Trakt
2. Click the connect button
3. Redirects to `https://trakt.tv/welcome` ✗

**Expected:** Should redirect to `https://app.trakt.tv/oauth/authorize?client_id=...&redirect_uri=...&response_type=code`

**Actual:** Redirects to `https://trakt.tv/welcome` — a dead/legacy URL that doesn't work. `trakt.tv` now redirects to `app.trakt.tv`, but `/welcome` is not a valid path.

**Fix:** Update the Trakt OAuth app settings on `app.trakt.tv/developer/apps`:
- Change the `redirect_uri` from `trakt.tv/welcome` to the correct WeTrakr callback URL (e.g., `https://wetrakr.com/integrations/trakt/callback` or similar)
- Ensure the OAuth URL uses `app.trakt.tv` domain, not `trakt.tv`

**Note:** `GET /proxy/integrations/trakt` returns `{"provider":"trakt","connected":false,"data":null}` — endpoint works, just the OAuth URL is wrong.

## License

MIT — Use at your own risk. This is an unofficial client.
