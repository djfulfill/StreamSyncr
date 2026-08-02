#!/usr/bin/env python3
"""
Bulk unwatch ALL items on WeTrakr using POST /account/tracking/remove/all.
Uses TMDB IDs (not internal IDs) for removal.
"""

import requests
import json
import os
import time
import sys

ACCESS_TOKEN = os.environ.get("WETRAKR_ACCESS_TOKEN", "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJjbGllbnRfaWQiOiJkYXNoYm9hcmQiLCJ1c2VyX2lkIjo2Nzk3LCJlbWFpbCI6ImRqZnVsZmlsbEBnbWFpbC5jb20iLCJpc19hZG1pbiI6ZmFsc2UsImlhdCI6MTc4NTYwMjgxMiwiZXhwIjoxNzg1Nzc1NjEyfQ.DH1u7R4L3rYK3-r80edTAK-GpCnsoTtO81lEBsOgZE8")
REFRESH_TOKEN = os.environ.get("WETRAKR_REFRESH_TOKEN", "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJjbGllbnRfaWQiOiJkYXNoYm9hcmQiLCJ1c2VyX2lkIjo2Nzk3LCJ0eXBlIjoicmVmcmVzaCIsImlhdCI6MTc4NTYwMjgxMiwiZXhwIjoxNzg4MTk0ODEyfQ.eb9P3_fCt7U_kj4Y2nYIq9XdsJYIPvl6ty3OACdDHA0")

HEADERS = {
    "accept": "application/json, text/plain, */*",
    "content-type": "application/json",
    "wetrakr-api-country": "US",
    "wetrakr-api-language": "en-US",
}
COOKIES = {"wta_auth": "1", "wta_at": ACCESS_TOKEN, "wta_rt": REFRESH_TOKEN}
BASE = "https://wetrakr.com/proxy"


def get(path, params=None):
    r = requests.get(f"{BASE}/{path}", headers=HEADERS, cookies=COOKIES, params=params)
    r.raise_for_status()
    return r.json()


def post(path, data):
    r = requests.post(f"{BASE}/{path}", headers=HEADERS, cookies=COOKIES, json=data)
    r.raise_for_status()
    return r.json()


def get_all_list_items(list_id):
    all_items = []
    page = 1
    while True:
        items = get(f"account/lists/{list_id}/items", {"page": page, "limit": 100})
        if not items:
            break
        all_items.extend(items)
        if len(items) < 100:
            break
        page += 1
    return all_items


def get_watched_counts():
    profile = get("frontend/users/djfulfill")
    t = profile["profile_stats"]["tracking"]
    return t["movies"]["watched"], t["shows"]["watched"]


def main():
    movies_before, shows_before = get_watched_counts()
    print(f"BEFORE: {movies_before} movies watched, {shows_before} shows watched\n")

    # 1. Get all lists
    lists = get("account/lists")
    print(f"Found {len(lists)} lists")

    # 2. Collect all unique items with TMDB IDs
    all_movies = {}  # tmdb_id -> title
    all_shows = {}   # tmdb_id -> title

    for lst in lists:
        list_id = lst["id"]
        list_name = lst.get("name", f"List {list_id}")
        items = get_all_list_items(list_id)
        for item in items:
            tmdb_id = item.get("ids", {}).get("tmdb", {}).get("id")
            item_type = item.get("type", "movie")
            title = item.get("title") or item.get("name") or item.get("original_title", "?")
            if not tmdb_id:
                continue
            if item_type == "show":
                if tmdb_id not in all_shows:
                    all_shows[tmdb_id] = title
            else:
                if tmdb_id not in all_movies:
                    all_movies[tmdb_id] = title
        print(f"  {list_name}: {len(items)} items")

    print(f"\nUNIQUE: {len(all_movies)} movies, {len(all_shows)} shows\n")

    # 3. Bulk remove movies via remove/all (batches of 100)
    movie_ids = list(all_movies.keys())
    total_removed_m = 0
    for i in range(0, len(movie_ids), 100):
        batch = movie_ids[i:i+100]
        payload = {"movies": [{"id": mid, "status": "watched"} for mid in batch]}
        result = post("account/tracking/remove/all", payload)
        removed = result.get("removed", {}).get("watched", {}).get("movies", 0)
        total_removed_m += removed
        print(f"  Movies batch {i//100 + 1}/{(len(movie_ids)-1)//100 + 1}: removed {removed}")
        time.sleep(0.5)

    # 4. Bulk remove shows via remove/all (batches of 100)
    show_ids = list(all_shows.keys())
    total_removed_s = 0
    for i in range(0, len(show_ids), 100):
        batch = show_ids[i:i+100]
        payload = {"shows": [{"id": sid, "status": "watched"} for sid in batch]}
        result = post("account/tracking/remove/all", payload)
        removed = result.get("removed", {}).get("watched", {}).get("shows", 0)
        total_removed_s += removed
        print(f"  Shows batch {i//100 + 1}/{(len(show_ids)-1)//100 + 1}: removed {removed}")
        time.sleep(0.5)

    # 5. Final counts
    movies_after, shows_after = get_watched_counts()
    print(f"\n=== RESULTS ===")
    print(f"Movies: {movies_before} → {movies_after} (removed {movies_before - movies_after})")
    print(f"Shows:  {shows_before} → {shows_after} (removed {shows_before - shows_after})")


if __name__ == "__main__":
    main()
