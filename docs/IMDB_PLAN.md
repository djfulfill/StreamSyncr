# IMDb Integration Plan for StreamSyncr

## Overview

Integrate IMDb data into StreamSyncr for syncing user's existing watch history, ratings, and lists.

## Confirmed Operations

### 1. `YourListsSidebar`
- **Hash**: `7e9a98408bca0450bffb02fbafc807ad32295ff4839bc6c3a5669c3afcb6a2da`
- **Purpose**: Fetch user's custom lists
- **Returns**: List ID, name, created/modified dates, item count, visibility, primary image
- **Variables**: `{ first: int, locale: string }`

### 2. `PersonalizedUserData`
- **Hash**: `7c4e0771d67f21fc27fd44fc46d49cc589225a9c5e63e51cc0b8d42f39ee99cc`
- **Purpose**: Get user's ratings and watched status for specific titles
- **Returns**: `userRating` (null if not rated), `userWatchedStatus.isWatched`, `primaryWatchOption` (streaming providers)
- **Variables**: `{ idArray: [string], includeUserData: bool, includeWatchedData: bool, locale: string, location: object, fetchOtherUserRating: bool }`

## Missing Operations (Need Discovery)

- **List Items**: Get movies/shows in a specific list (need operation hash)
- **Watchlist**: Get user's watchlist (need operation hash)
- **All Ratings**: Get all user ratings (need operation hash)

## Authentication

Cookie-based session authentication (same as current curl):
- `session-id`, `ubid-main`, `at-main`, `sess-at-main`, `session-token`
- Tokens expire periodically (need re-authentication)

## Integration Architecture

### Backend (Python)

Create `imdb_api/` module:
```
imdb_api/
├── __init__.py
├── client.py      # IMDb GraphQL client
├── operations.py  # Known operation hashes
└── README.md      # Documentation
```

### Frontend (React)

- Add IMDb service in Settings page
- Show IMDb lists alongside WeTrakr/Trakt
- Display user ratings from IMDb
- Show watched status indicators

## Sync Workflow

### Export from IMDb
1. Fetch user's lists via `YourListsSidebar`
2. For each list, fetch items (once we find the operation)
3. Get ratings/watched status via `PersonalizedUserData`
4. Store in StreamSyncr library

### Import to IMDb
- Limited (read-only API)
- Can only export data, not push changes

## Data Mapping

### IMDb → StreamSyncr
| IMDb Field | StreamSyncr Field |
|------------|-------------------|
| `id` (tt0000000) | `imdb_id` |
| `userRating` | `rating` |
| `userWatchedStatus.isWatched` | `watched` |
| `primaryWatchOption` | `streaming_providers` |

### TMDB ↔ IMDb
- Use `imdb_to_tmdb.py` converter to map IDs
- IMDb `tt0467200` → TMDB `27205` (Lost)

## Priority Features

1. **Phase 1: Read-only sync**
   - Import IMDb lists
   - Import ratings
   - Import watchlist

2. **Phase 2: Display**
   - Show IMDb data in library
   - Cross-reference with TMDB for posters/metadata

3. **Phase 3: Export (if API allows)**
   - Push ratings to IMDb
   - Add to watchlist

## Technical Challenges

1. **Persisted Query Hashes**: Need to discover hashes for list items, ratings, watchlist operations
2. **Session Expiry**: Cookies expire, need re-authentication flow
3. **Rate Limiting**: IMDb uses AWS WAF tokens
4. **Legal**: IMDb restricts commercial use (personal use OK)

## Next Steps

1. Discover remaining operation hashes (list items, ratings, watchlist)
2. Build Python client for IMDb GraphQL API
3. Add IMDb service to StreamSyncr frontend
4. Implement sync functionality
