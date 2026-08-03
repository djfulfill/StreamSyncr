"""
Trakt JSON → IMDb CSV Converter

Supports multiple Trakt export formats:
  1. Trakt Collections (multi-file): collection-movies-*.json, collection-episodes-*.json, collection-shows.json
  2. Lunova Export (single-file): watched_movies, watched_shows, collection, watchlist, etc.
  3. Stremio/MetaHub Export: array with {id, type, name, releaseInfo}

Usage:
  python trakt_to_csv.py /path/to/trakt/files/           # auto-detect format
  python trakt_to_csv.py /path/to/export.json             # single file
  python trakt_to_csv.py /path/to/collections/ -o out.csv # custom output
  python trakt_to_csv.py /path/to/files/ --types movies   # movies only
  python trakt_to_csv.py /path/to/files/ --types shows    # shows only
  python trakt_to_csv.py /path/to/files/ --imdb           # IMDb playlist format
"""

import argparse
import csv
import glob
import json
import os
import sys
from pathlib import Path
from typing import List, Dict, Optional


def imdb_url(imdb_id: str) -> str:
    return f"https://www.imdb.com/title/{imdb_id}/"


def parse_trakt_collections_file(filepath: str) -> List[Dict]:
    """Parse a single Trakt collections JSON file (collection-movies-*.json, etc.)"""
    with open(filepath) as f:
        data = json.load(f)

    rows = []
    for item in data:
        item_type = item.get("type", "")

        if item_type == "movie":
            m = item.get("movie", {})
            imdb_id = m.get("ids", {}).get("imdb")
            if imdb_id:
                rows.append({
                    "type": "movie",
                    "title": m.get("title", ""),
                    "year": m.get("year", ""),
                    "imdb_id": imdb_id,
                    "imdb_url": imdb_url(imdb_id),
                    "show": "",
                    "season": "",
                    "episode_number": "",
                })

        elif item_type == "episode":
            ep = item.get("episode", {})
            show = item.get("show", {})
            show_imdb = show.get("ids", {}).get("imdb", "")
            imdb_id = show_imdb or ep.get("ids", {}).get("imdb", "")
            if imdb_id:
                rows.append({
                    "type": "episode",
                    "title": ep.get("title", ""),
                    "year": show.get("year", ""),
                    "imdb_id": imdb_id,
                    "imdb_url": imdb_url(imdb_id),
                    "show": show.get("title", ""),
                    "season": ep.get("season", ""),
                    "episode_number": ep.get("number", ""),
                })

        elif item_type == "show":
            s = item.get("show", {})
            imdb_id = s.get("ids", {}).get("imdb")
            if imdb_id:
                rows.append({
                    "type": "show",
                    "title": s.get("title", ""),
                    "year": s.get("year", ""),
                    "imdb_id": imdb_id,
                    "imdb_url": imdb_url(imdb_id),
                    "show": "",
                    "season": "",
                    "episode_number": "",
                })

    return rows


def parse_trakt_collections_dir(dirpath: str) -> List[Dict]:
    """Parse a directory of Trakt collection JSON files."""
    rows = []
    for filepath in sorted(glob.glob(os.path.join(dirpath, "collection-*.json"))):
        rows.extend(parse_trakt_collections_file(filepath))

    # Also parse lists-*.json files
    for filepath in sorted(glob.glob(os.path.join(dirpath, "lists-*.json"))):
        with open(filepath) as f:
            data = json.load(f)
        for item in data:
            movie = item.get("movie", item.get("show", {}))
            imdb_id = movie.get("ids", {}).get("imdb")
            if imdb_id:
                rows.append({
                    "type": item.get("type", "movie"),
                    "title": movie.get("title", ""),
                    "year": movie.get("year", ""),
                    "imdb_id": imdb_id,
                    "imdb_url": imdb_url(imdb_id),
                    "show": "",
                    "season": "",
                    "episode_number": "",
                })
    return rows


def parse_lunova_export(filepath: str) -> List[Dict]:
    """Parse a Lunova-style Trakt export (single JSON with watched_movies, etc.)"""
    with open(filepath) as f:
        data = json.load(f)

    rows = []
    seen = set()

    # Index ratings by imdb id
    ratings_map = {}
    for r in data.get("ratings_movies", []):
        imdb_id = r.get("movie", {}).get("ids", {}).get("imdb")
        if imdb_id:
            ratings_map[imdb_id] = {"rating": r.get("rating", ""), "rated_at": r.get("rated_at", "")}
    for r in data.get("ratings_shows", []):
        imdb_id = r.get("show", {}).get("ids", {}).get("imdb")
        if imdb_id:
            ratings_map[imdb_id] = {"rating": r.get("rating", ""), "rated_at": r.get("rated_at", "")}
    for r in data.get("ratings_episodes", []):
        imdb_id = r.get("episode", {}).get("ids", {}).get("imdb")
        if imdb_id:
            ratings_map[imdb_id] = {"rating": r.get("rating", ""), "rated_at": r.get("rated_at", "")}

    def add(item_type, obj, extra=None):
        imdb_id = obj.get("ids", {}).get("imdb")
        if not imdb_id or imdb_id in seen:
            return
        seen.add(imdb_id)
        rat = ratings_map.get(imdb_id, {})
        row = {
            "type": item_type,
            "title": obj.get("title", ""),
            "year": obj.get("year", ""),
            "imdb_id": imdb_id,
            "imdb_url": imdb_url(imdb_id),
            "show": extra.get("show", "") if extra else "",
            "season": extra.get("season", "") if extra else "",
            "episode_number": extra.get("episode_number", "") if extra else "",
            "rating": rat.get("rating", ""),
            "rated_at": rat.get("rated_at", ""),
        }
        rows.append(row)

    # Watched movies
    for item in data.get("watched_movies", []):
        m = item.get("movie", {})
        add("movie", m)

    # Watched shows
    for item in data.get("watched_shows", []):
        s = item.get("show", {})
        add("show", s)

    # Collection (flat list with type + movie/show keys)
    collection = data.get("collection", [])
    if isinstance(collection, list):
        for item in collection:
            obj = item.get("movie", item.get("show", {}))
            add(item.get("type", "movie"), obj)
    elif isinstance(collection, dict):
        for item in collection.get("movies", []):
            add("movie", item)
        for item in collection.get("shows", []):
            add("show", item)

    # Watchlist
    for item in data.get("watchlist", []):
        obj = item.get("movie", item.get("show", {}))
        add(item.get("type", "movie"), obj)

    # History (movies + episodes)
    for item in data.get("history", []):
        item_type = item.get("type", "")
        if item_type == "movie":
            m = item.get("movie", {})
            add("movie", m)
        elif item_type == "episode":
            ep = item.get("episode", {})
            show = item.get("show", {})
            show_imdb = show.get("ids", {}).get("imdb", "")
            imdb_id = show_imdb or ep.get("ids", {}).get("imdb", "")
            if imdb_id and imdb_id not in seen:
                seen.add(imdb_id)
                rows.append({
                    "type": "episode",
                    "title": ep.get("title", ""),
                    "year": show.get("year", ""),
                    "imdb_id": imdb_id,
                    "imdb_url": imdb_url(imdb_id),
                    "show": show.get("title", ""),
                    "season": ep.get("season", ""),
                    "episode_number": ep.get("number", ""),
                })

    # List items
    for list_items in data.get("list_items", {}).values() if isinstance(data.get("list_items"), dict) else []:
        for item in list_items:
            obj = item.get("movie", item.get("show", {}))
            add(item.get("type", "movie"), obj)

    return rows


def parse_stremio_export(filepath: str) -> List[Dict]:
    """Parse a Stremio/MetaHub export (array of {id, type, name, releaseInfo})."""
    with open(filepath) as f:
        data = json.load(f)

    rows = []
    for item in data:
        imdb_id = item.get("id", "")
        if not imdb_id or not imdb_id.startswith("tt"):
            continue
        media_type = item.get("type", "")
        if media_type == "series":
            media_type = "show"
        rows.append({
            "type": media_type,
            "title": item.get("name", ""),
            "year": item.get("releaseInfo", ""),
            "imdb_id": imdb_id,
            "imdb_url": imdb_url(imdb_id),
            "show": "",
            "season": "",
            "episode_number": "",
        })
    return rows


def detect_format(path: str) -> str:
    """Detect whether path is a directory, Lunova export, Stremio export, or Trakt collections dir."""
    if os.path.isdir(path):
        files = os.listdir(path)
        if any(f.startswith("collection-") for f in files):
            return "trakt_collections_dir"
        return "unknown_dir"

    with open(path) as f:
        data = json.load(f)

    if isinstance(data, list):
        if data and "id" in data[0] and "name" in data[0]:
            return "stremio"
        return "unknown_list"

    if isinstance(data, dict):
        if "watched_movies" in data or "watchlist" in data:
            return "lunova"
        if "generated_at" in data and "profile" in data:
            return "lunova"

    return "unknown"


IMDB_FIELDNAMES = [
    "Position", "Const", "Created", "Modified", "Description", "Title",
    "Original Title", "URL", "Title Type", "IMDb Rating", "Runtime (mins)",
    "Year", "Genres", "Num Votes", "Release Date", "Directors", "Your Rating", "Date Rated"
]


def write_imdb_csv(rows: List[Dict], output: str, include_rating: bool = False, include_release_date: bool = False) -> None:
    """Write rows in IMDb playlist CSV format (movies only)."""
    movies = [r for r in rows if r["type"] == "movie"]
    with open(output, "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(IMDB_FIELDNAMES)
        for i, m in enumerate(movies, 1):
            year = m["year"]
            rating = m.get("rating", "") if include_rating else ""
            rated_at = ""
            if include_rating and m.get("rated_at"):
                rated_at = m["rated_at"][:10]  # YYYY-MM-DD
            release_date = ""
            if include_release_date:
                release_date = f"{year}-01-01" if year else ""
            writer.writerow([
                i, m["imdb_id"], "", "", "", m["title"], m["title"],
                m["imdb_url"], "movie", "", "", year, "", "",
                release_date, "", rating, rated_at
            ])


def convert(path: str, output: str = None, types: List[str] = None, imdb: bool = False,
            rating: bool = False, release_date: bool = False) -> str:
    """Main conversion entrypoint. Returns output filepath."""
    fmt = detect_format(path)

    if fmt == "trakt_collections_dir":
        rows = parse_trakt_collections_dir(path)
    elif fmt == "lunova":
        rows = parse_lunova_export(path)
    elif fmt == "stremio":
        rows = parse_stremio_export(path)
    else:
        print(f"Error: Unknown format for {path}", file=sys.stderr)
        sys.exit(1)

    # Filter by type if requested (accept plural forms)
    if types:
        type_map = {"movies": "movie", "shows": "show", "episodes": "episode"}
        types_normalized = [type_map.get(t.lower(), t.lower()) for t in types]
        rows = [r for r in rows if r["type"] in types_normalized]

    # Determine output path
    if not output:
        base = os.path.splitext(os.path.basename(path.rstrip("/")))[0]
        suffix = ".imdb.csv" if imdb else ".csv"
        output = os.path.join(os.path.dirname(path.rstrip("/")) or ".", f"{base}{suffix}")

    # Write CSV
    if imdb:
        write_imdb_csv(rows, output, rating, release_date)
    else:
        fieldnames = ["type", "title", "year", "imdb_id", "imdb_url", "show", "season", "episode_number"]
        with open(output, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(rows)

    # Summary
    movies = sum(1 for r in rows if r["type"] == "movie")
    shows = sum(1 for r in rows if r["type"] == "show")
    episodes = sum(1 for r in rows if r["type"] == "episode")

    print(f"Format: {fmt}")
    print(f"Output: {output}")
    print(f"Total: {len(rows)} rows ({movies} movies, {shows} shows, {episodes} episodes)")

    return output


def main():
    parser = argparse.ArgumentParser(
        description="Convert Trakt JSON exports to IMDb CSV"
    )
    parser.add_argument("path", help="Path to Trakt JSON file or directory of JSON files")
    parser.add_argument("-o", "--output", help="Output CSV path (default: auto)")
    parser.add_argument(
        "--types", nargs="+", choices=["movies", "shows", "episodes"],
        help="Filter to specific types (movies, shows, episodes)"
    )
    parser.add_argument(
        "--imdb", action="store_true",
        help="Output in IMDb playlist format (movies only)"
    )
    parser.add_argument(
        "--rating", action="store_true",
        help="Include Your Rating and Date Rated columns (IMDb format)"
    )
    parser.add_argument(
        "--release-date", action="store_true",
        help="Include Release Date column (IMDb format)"
    )
    args = parser.parse_args()

    convert(args.path, args.output, args.types, args.imdb, args.rating, args.release_date)


if __name__ == "__main__":
    main()
