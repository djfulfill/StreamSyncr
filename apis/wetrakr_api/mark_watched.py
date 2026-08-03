"""
Mark all items in all WeTrakr lists as watched.
Uses release dates by default so history looks natural.

CRITICAL: Uses INTERNAL IDs for marking (not TMDB IDs).
See README.md for ID details.
"""

import requests
import json
import time
import sys
import os

# ── Config ─────────────────────────────────────────────────────────────────
BASE = "https://wetrakr.com/proxy"

ACCESS_TOKEN = os.environ.get("WETRAKR_ACCESS_TOKEN")
REFRESH_TOKEN = os.environ.get("WETRAKR_REFRESH_TOKEN")

if not ACCESS_TOKEN or not REFRESH_TOKEN:
    print("Error: Set WETRAKR_ACCESS_TOKEN and WETRAKR_REFRESH_TOKEN environment variables.")
    print("See README.md for how to get your tokens.")
    sys.exit(1)

HEADERS = {
    "accept": "application/json, text/plain, */*",
    "content-type": "application/json",
    "wetrakr-api-country": "US",
    "wetrakr-api-language": "en-US",
    "user-agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 Chrome/151.0.0.0 Safari/537.36",
}
COOKIES = {
    "wta_auth": "1",
    "wta_at": ACCESS_TOKEN,
    "wta_rt": REFRESH_TOKEN,
}
BATCH_SIZE = 50


def get(path, params=None):
    r = requests.get(f"{BASE}/{path}", headers=HEADERS, cookies=COOKIES, params=params)
    r.raise_for_status()
    return r.json()


def post_tracking(payload):
    r = requests.post(f"{BASE}/account/tracking", headers=HEADERS, cookies=COOKIES, json=payload)
    r.raise_for_status()
    return r.json()


def get_all_list_items(list_id: int) -> list:
    """Get all items from a list, handling pagination."""
    all_items = []
    page = 1
    while True:
        r = requests.get(
            f"{BASE}/account/lists/{list_id}/items",
            headers=HEADERS, cookies=COOKIES,
            params={"page": page, "limit": 100}
        )
        r.raise_for_status()
        items = r.json()
        if not items:
            break
        all_items.extend(items)
        total = r.headers.get("X-Pagination-Item-Count")
        if total and len(all_items) >= int(total):
            break
        if len(items) < 100:
            break
        page += 1
    return all_items


def main():
    dry_run = "--dry-run" in sys.argv
    use_release = "--no-release-date" not in sys.argv

    print("Fetching lists...")
    lists = get("account/lists")
    print(f"Found {len(lists)} lists\n")

    seen_ids = set()
    movies = []
    shows = []

    for lst in lists:
        list_id = lst["id"]
        name = lst["name"]
        total = lst["total_items"]
        print(f"  [{list_id}] {name} ({total} items)...", end=" ", flush=True)
        items = get_all_list_items(list_id)
        for item in items:
            # CRITICAL: Use INTERNAL id for marking (not TMDB id)
            internal_id = item.get("id")
            tmdb_id = item.get("ids", {}).get("tmdb", {}).get("id")
            media_type = item.get("type", "movie")
            title = item.get("title") or item.get("name") or item.get("original_title", "?")
            if internal_id and internal_id not in seen_ids:
                seen_ids.add(internal_id)
                entry = {"internal_id": internal_id, "tmdb_id": tmdb_id, "title": title}
                if media_type == "show":
                    shows.append(entry)
                else:
                    movies.append(entry)
        print(f"got {len(items)} items ({len(seen_ids)} unique so far)")

    total_items = len(movies) + len(shows)
    print(f"\nTotal unique items to mark watched: {total_items}")
    print(f"  Movies: {len(movies)}")
    print(f"  Shows:  {len(shows)}")
    print(f"  Use release dates: {use_release}\n")

    if dry_run:
        print("DRY RUN — not marking anything")
        for item in movies[:5]:
            print(f"  movie | internal={item['internal_id']:>8} tmdb={item['tmdb_id']:>8} | {item['title']}")
        for item in shows[:5]:
            print(f"  show  | internal={item['internal_id']:>8} tmdb={item['tmdb_id']:>8} | {item['title']}")
        remaining = total_items - 10
        if remaining > 0:
            print(f"  ... and {remaining} more")
        return

    confirm = input(f"Mark {total_items} items as watched? [y/N] ")
    if confirm.lower() != "y":
        print("Aborted.")
        return

    success = 0
    failed = 0
    errors = []

    # Batch movies (using internal IDs)
    for i in range(0, len(movies), BATCH_SIZE):
        batch = movies[i:i+BATCH_SIZE]
        payload = {"movies": [{"id": m["internal_id"], "status": "watched", "use_release_date": use_release} for m in batch]}
        try:
            post_tracking(payload)
            success += len(batch)
            for m in batch:
                print(f"  [{success}/{total_items}] ✓ movie | {m['internal_id']:>8} | {m['title']}")
        except Exception as e:
            failed += len(batch)
            for m in batch:
                errors.append((m, str(e)))
                print(f"  [{success+failed}/{total_items}] ✗ movie | {m['internal_id']:>8} | {m['title']}: {e}")
        if (i + BATCH_SIZE) % 200 == 0:
            time.sleep(0.5)

    # Batch shows (using internal IDs — TMDB IDs don't work for shows!)
    for i in range(0, len(shows), BATCH_SIZE):
        batch = shows[i:i+BATCH_SIZE]
        payload = {"shows": [{"id": s["internal_id"], "status": "watched", "use_release_date": use_release} for s in batch]}
        try:
            post_tracking(payload)
            success += len(batch)
            for s in batch:
                print(f"  [{success}/{total_items}] ✓ show  | {s['internal_id']:>8} | {s['title']}")
        except Exception as e:
            failed += len(batch)
            for s in batch:
                errors.append((s, str(e)))
                print(f"  [{success+failed}/{total_items}] ✗ show  | {s['internal_id']:>8} | {s['title']}: {e}")
        if (i + BATCH_SIZE) % 200 == 0:
            time.sleep(0.5)

    print(f"\nDone! {success} marked, {failed} failed")
    if errors:
        print("\nFailed items:")
        for item, err in errors[:20]:
            print(f"  {item['internal_id']} ({item['title']}): {err}")


if __name__ == "__main__":
    main()
