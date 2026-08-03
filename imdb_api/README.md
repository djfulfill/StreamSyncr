# IMDb API Client

Python client for IMDb's GraphQL API with full read/write support for lists, ratings, and watchlist.

## Features

- **Lists**: Create, edit, delete, add/remove items
- **Ratings**: Rate titles (1-10), delete ratings
- **Watchlist**: Add/remove items
- **Read**: Get lists, ratings, watched status, recently viewed

## Setup

### 1. Get Session Cookies

1. Go to [imdb.com](https://www.imdb.com) and log in
2. Open DevTools (F12) → Application tab → Cookies
3. Copy these cookies:
   - `session-id`
   - `at-main`
   - `session-token`
   - `ubid-main` (optional)
   - `sess-at-main` (optional)
   - `x-main` (optional)

### 2. Set Environment Variables

```bash
export IMDB_SESSION_ID="your_session_id"
export IMDB_AT_MAIN="your_at_main"
export IMDB_SESSION_TOKEN="your_session_token"
export IMDB_UBID_MAIN="your_ubid_main"      # optional
export IMDB_SESS_AT_MAIN="your_sess_at_main" # optional
export IMDB_X_MAIN="your_x_main"            # optional
```

## Usage

### Python

```python
from imdb_api import IMDbClient

client = IMDbClient()

# Get lists
lists = client.get_lists()
for lst in lists:
    print(f"{lst['name']['originalText']}: {lst['items']['total']} items")

# Create a new list
new_list = client.create_list("My Movies", "Best films ever", "PUBLIC")
print(f"Created: {new_list['id']}")

# Add items to list
client.add_to_list(new_list['id'], "tt0467200")  # Lost
client.add_to_list(new_list['id'], "tt0133093")  # The Matrix

# Rate a title
client.rate_title("tt0467200", 9)  # Rate Lost 9/10

# Get ratings
ratings = client.get_ratings(["tt0467200", "tt0133093"])
for r in ratings:
    print(f"{r['id']}: {r.get('userRating', 'Not rated')}")

# Add to watchlist
client.add_to_watchlist("tt9244578")

# Recently viewed
recent = client.get_recently_viewed()
for item in recent:
    print(f"{item['titleText']['text']}")
```

### CLI

```bash
# Get lists
python -m imdb_api lists

# Get ratings
python -m imdb_api ratings tt0467200 tt0133093

# Rate a title
python -m imdb_api rate tt0467200 9

# Create a list
python -m imdb_api create-list "My Movies" --description "Best films" --visibility PUBLIC

# Add to list
python -m imdb_api add-to-list ls1234567 tt0467200

# Add to watchlist
python -m imdb_api watchlist tt9244578

# Recently viewed
python -m imdb_api recent
```

## ID Format

IMDb uses title IDs in format `tt0000000` (e.g., `tt0467200` for Lost).

You can convert between IMDb and TMDB IDs using the `imdb_to_tmdb.py` converter:

```bash
python imdb_to_tmdb.py tt0467200
# Returns: {tmdb_id: 27205, title: "Lost", ...}
```

## Limitations

- Session cookies expire periodically (re-authentication required)
- Personal use only (IMDb restricts commercial use)
- Rate limiting may apply
