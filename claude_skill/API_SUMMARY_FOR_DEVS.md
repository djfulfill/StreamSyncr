# WeTrakr API — Reverse Engineering Summary

**Date:** 2026-08-02  
**Status:** Beta app, no public API  
**Source:** Browser network request analysis

---

## Overview

This document summarizes all discovered API endpoints, authentication methods, and issues found during reverse engineering of the WeTrakr beta application. The goal is to assist the development team in building an official API.

---

## Authentication

### Headers Required
```
wetrakr-api-country: US
wetrakr-api-language: en-US
```

### Cookies
```
wta_auth=1
wta_at={JWT_ACCESS_TOKEN}
wta_rt={JWT_REFRESH_TOKEN}
```

### JWT Token Structure
- **Access Token (`wta_at`):** Expires ~2 days
- **Refresh Token (`wta_rt`):** Expires ~30 days
- **Payload:** `{client_id: "dashboard", user_id: 6797, email: "...", is_admin: false}`

---

## Discovered Endpoints

### User

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/proxy/frontend/users/{username}` | User profile with stats |
| GET | `/proxy/frontend/users/me/watching-progress` | Watching progress summary |
| GET | `/proxy/account/tracking/watching/total-time` | Total watched time |
| GET | `/proxy/account/last/tracking` | Recent tracking activity |

### Content

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/proxy/frontend/movies/{tmdb_id}` | Movie details |
| GET | `/proxy/frontend/shows/{tmdb_id}` | Show details |
| GET | `/proxy/frontend/shows/{id}/seasons/{n}` | Season details |
| GET | `/proxy/frontend/shows/{id}/seasons/{n}/episodes/{n}` | Episode details |
| GET | `/proxy/{type}/{id}/reviews` | User reviews |

### Search & Discovery

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/proxy/search/all?q=&type=&maxPerGroup=` | Search movies, shows, people |
| GET | `/proxy/search/trending?filter_type=&limit=` | Trending content |

### Filters

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/proxy/filters/auto/sys:watched` | Watched content |
| GET | `/proxy/filters/auto/sys:watching` | Currently watching |
| GET | `/proxy/filters/auto/sys:waiting` | Waiting for new episodes |
| GET | `/proxy/filters/auto/sys:plantowatch` | Plan to watch |
| GET | `/proxy/filters/auto/sys:nowplaying` | Now playing |
| GET | `/proxy/filters/auto/sys:nexttowatch` | Next to watch |
| GET | `/proxy/filters/auto/sys:upcoming` | Upcoming releases |
| GET | `/proxy/filters/auto/sys:favorites` | Favorites |
| GET | `/proxy/filters/auto/sys:ratings` | Rated content |

### Lists

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/proxy/account/lists` | All user lists |
| GET | `/proxy/account/lists/{id}/items` | Items from a list |
| POST | `/proxy/account/lists/item/{type}/{tmdb_id}` | Bulk list membership |

### Tracking (Write)

| Method | Endpoint | ID Type | Description |
|--------|----------|---------|-------------|
| POST | `/proxy/account/tracking` | Internal | Mark item watched |
| POST | `/proxy/account/tracking/remove/all` | TMDB | Unwatch item |
| POST | `/proxy/account/favorites` | Internal | Add to favorites |
| POST | `/proxy/account/favorites/remove` | TMDB | Remove from favorites |
| PUT | `/proxy/account/preferences/pinned-media` | Internal | Pin to profile |
| POST | `/proxy/account/notes` | TMDB | Add personal note |

### Social

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/proxy/users/{id}/follow` | Follow user |
| DELETE | `/proxy/users/{id}/follow` | Unfollow user |
| POST | `/proxy/reviews/{id}/like` | Like a review |
| POST | `/proxy/reviews/{id}/unlike` | Unlike a review |

---

## Payload Formats

### Mark Watched
```json
POST /proxy/account/tracking
{
  "movies": [{"id": INTERNAL_ID, "status": "watched", "use_release_date": true}],
  "shows": [{"id": INTERNAL_ID, "status": "watched", "use_release_date": true}]
}
```

### Unwatch
```json
POST /proxy/account/tracking/remove/all
{
  "movies": [{"id": TMDB_ID, "status": "watched"}],
  "shows": [{"id": TMDB_ID, "status": "watched"}]
}
```

### Add to Favorites
```json
POST /proxy/account/favorites
{
  "movies": [{"id": INTERNAL_ID}],
  "shows": [{"id": INTERNAL_ID}]
}
```

### Remove from Favorites
```json
POST /proxy/account/favorites/remove
{
  "movies": [{"id": TMDB_ID}],
  "shows": [{"id": TMDB_ID}]
}
```

### Pin to Profile
```json
PUT /proxy/account/preferences/pinned-media
{
  "media_id": INTERNAL_ID,
  "type": "movie"  // or "show"
}
```

### Bulk List Membership
```json
POST /proxy/account/lists/item/{type}/{tmdb_id}
{
  "lists": [
    {"id": LIST_ID, "included": true},   // add to list
    {"id": LIST_ID, "included": false}   // remove from list
  ]
}
```

### Add Note
```json
POST /proxy/account/notes
{
  "movies": [{"id": TMDB_ID, "text": "Your note here"}]
}
```

---

## Critical Issue: ID Confusion

WeTrakr uses **two different ID systems** that are inconsistently applied:

| ID Type | Source | Example |
|---------|--------|---------|
| **Internal ID** | WeTrakr's database | `5513` (Hackers) |
| **TMDB ID** | The Movie Database | `10428` (Hackers) |

### Current Behavior (Inconsistent)

| Operation | Uses Which ID? |
|-----------|---------------|
| Mark watched | Internal ID |
| Unwatch | TMDB ID |
| Add to favorites | Internal ID |
| Remove from favorites | TMDB ID |
| Pin to profile | Internal ID |
| Add note | TMDB ID |
| List membership | TMDB ID |

### Recommendation

**Standardize on TMDB IDs for all public-facing operations.** This is what users expect and what most integrations use. The internal ID should be an implementation detail, not exposed to API consumers.

---

## Bugs Found

### 1. Filter Endpoints Return Null State

**All filter endpoints return `state: null` even when data exists.**

```
GET /proxy/filters/auto/sys:watched
GET /proxy/filters/auto/sys:favorites
GET /proxy/filters/auto/sys:watching
... (all filters affected)
```

**Response:**
```json
{
  "list_key": "sys:watched",
  "state": null
}
```

**Expected:** Should return the list of items matching the filter.

**Workaround:** Use `profile_stats.tracking` for counts.

### 2. Display Endpoints Don't Reflect Tracking State

```
GET /proxy/frontend/movies/{tmdb_id}
```

Returns `interactions.user.tracking.last.status: "none"` even after marking as watched. The website displays correctly, but the API doesn't.

### 3. GET /account/favorites Returns 404

```
GET /proxy/account/favorites
→ 404 Not Found
```

The endpoint doesn't exist. Favorites can only be managed via POST/DELETE operations.

### 4. Trakt OAuth Redirect URL is Wrong

The Trakt integration link redirects to `trakt.tv/welcome` instead of `app.trakt.tv/oauth/authorize`. This is a dead URL.

**Fix:** Update the Trakt OAuth app settings on `app.trakt.tv/developer/apps` to use the correct redirect URI.

---

## Response Examples

### Profile Stats
```json
{
  "profile_stats": {
    "tracking": {
      "movies": {"watched": 613, "watching": 0, "plantowatch": 13},
      "shows": {"watched": 115, "watching": 0, "waiting": 18},
      "episodes": {"watched": 17889}
    },
    "favorites": {...},  // NOT AVAILABLE
    "community": {
      "reviews": 0,
      "lists": 15,
      "ratings": 8,
      "likes": 1
    },
    "watched_time": {
      "minutes": 623866,
      "hours": 10397.8
    }
  }
}
```

### List Items
```json
{
  "id": 5513,           // Internal ID
  "type": "movie",
  "title": "Hackers",
  "ids": {
    "tmdb": {"id": 10428},
    "imdb": {"id": "tt0113243"}
  },
  "interactions": {
    "user": {
      "tracking": {"last": {"status": "watched"}},
      "favorite": {"value": true}
    }
  }
}
```

---

## Recommendations for Official API

1. **Standardize IDs** — Use TMDB IDs consistently for all endpoints
2. **Fix filter endpoints** — They should return actual data, not `null`
3. **Fix display endpoints** — Should reflect current tracking state
4. **Add GET /account/favorites** — Currently returns 404
5. **Fix Trakt OAuth** — Update redirect URL to `app.trakt.tv`
6. **Add rate limit headers** — Return `X-RateLimit-*` headers in responses
7. **Document endpoint versions** — Consider URL versioning (`/v1/...`)
8. **Add pagination metadata** — Return `{total, page, per_page}` in list responses
9. **Standardize error responses** — Use consistent error format across all endpoints
10. **Add webhook support** — For real-time tracking updates

---

## Testing Notes

- **Rate Limit:** 300 requests per 60 seconds
- **CORS:** Enabled with credentials
- **Content-Type:** `application/json`
- **Auth:** Cookie-based JWT (not Bearer token)

---

## Files

- `client.py` — Full Python API client
- `mark_watched.py` — Bulk mark-watched script
- `unwatch_all.py` — Bulk unwatch script
- `README.md` — Complete API documentation

---

*Document generated from reverse engineering on 2026-08-02. Endpoints may change without notice.*
