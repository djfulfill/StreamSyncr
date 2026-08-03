"""
IMDb → TMDB Converter

Convert IMDb IDs to TMDB IDs, URLs, and fetch movie details.

Usage:
    from imdb_to_tmdb import convert_id, convert_url, batch_convert

    # Single conversion
    result = convert_id("tt0244244")
    print(result["tmdb_id"])  # 9705

    # Batch conversion
    results = batch_convert(["tt0244244", "tt0133093", "tt0062622"])

    # CLI
    python imdb_to_tmdb.py tt0244244
    python imdb_to_tmdb.py --file imdb_ids.txt
    python imdb_to_tmdb.py --csv input.csv --output tmdb.csv
"""

import csv
import json
import os
import sys
from typing import List, Dict, Optional, Union
from urllib.request import Request, urlopen
from urllib.error import HTTPError
from urllib.parse import urlencode


BASE_URL = "https://api.themoviedb.org/3"
IMG_BASE = "https://image.tmdb.org/t/p"
TMDB_KEY = os.environ.get("TMDB_API_KEY", "")


def _get(path: str, **params) -> dict:
    all_params = {"api_key": TMDB_KEY}
    all_params.update(params)
    url = f"{BASE_URL}{path}?{urlencode(all_params)}"
    req = Request(url, headers={"Accept": "application/json"})
    with urlopen(req) as resp:
        return json.loads(resp.read())


def img_url(path: str, size: str = "w500") -> str:
    """Build full image URL from TMDB path."""
    if not path:
        return ""
    return f"{IMG_BASE}/{size}{path}"


def convert_id(imdb_id: str) -> Optional[dict]:
    """Convert a single IMDb ID to TMDB movie data.
    
    Args:
        imdb_id: IMDb ID (e.g., 'tt0244244' or '0244244')
    
    Returns:
        dict with tmdb_id, title, year, poster, backdrop, etc. or None
    """
    # Normalize IMDb ID
    if not imdb_id.startswith("tt"):
        imdb_id = f"tt{imdb_id.zfill(7)}"
    
    try:
        data = _get(f"/find/{imdb_id}", external_source="imdb_id")
        movies = data.get("movie_results", [])
        if not movies:
            return None
        
        m = movies[0]
        return {
            "imdb_id": imdb_id,
            "tmdb_id": m["id"],
            "title": m.get("title", ""),
            "year": m.get("release_date", "")[:4] if m.get("release_date") else "",
            "release_date": m.get("release_date", ""),
            "overview": m.get("overview", ""),
            "rating": m.get("vote_average", 0),
            "votes": m.get("vote_count", 0),
            "genre_ids": m.get("genre_ids", []),
            "poster": img_url(m.get("poster_path", "")),
            "poster_path": m.get("poster_path", ""),
            "backdrop": img_url(m.get("backdrop_path", "")),
            "backdrop_path": m.get("backdrop_path", ""),
            "language": m.get("original_language", ""),
            "popularity": m.get("popularity", 0),
            "adult": m.get("adult", False),
            "url": f"https://www.themoviedb.org/movie/{m['id']}",
            "imdb_url": f"https://www.imdb.com/title/{imdb_id}/",
        }
    except HTTPError as e:
        if e.code == 404:
            return None
        raise


def convert_url(imdb_url: str) -> Optional[dict]:
    """Convert an IMDb URL to TMDB movie data.
    
    Args:
        imdb_url: IMDb URL (e.g., 'https://www.imdb.com/title/tt0244244/')
    """
    # Extract IMDb ID from URL
    if "/title/" in imdb_url:
        part = imdb_url.split("/title/")[1]
        imdb_id = part.split("/")[0].split("?")[0]
        return convert_id(imdb_id)
    return None


def batch_convert(imdb_ids: List[str], delay: float = 0.1) -> List[dict]:
    """Convert multiple IMDb IDs to TMDB data.
    
    Args:
        imdb_ids: List of IMDb IDs
        delay: Delay between requests (rate limiting)
    
    Returns:
        List of dicts (None for failed lookups)
    """
    import time
    results = []
    for imdb_id in imdb_ids:
        result = convert_id(imdb_id)
        results.append(result)
        if delay > 0:
            time.sleep(delay)
    return results


def convert_csv(input_path: str, output_path: str = None,
                imdb_column: str = "imdb_id") -> str:
    """Convert a CSV with IMDb IDs to include TMDB data.
    
    Args:
        input_path: Input CSV path
        output_path: Output CSV path (default: auto)
        imdb_column: Column name containing IMDb IDs
    
    Returns:
        Output file path
    """
    if not output_path:
        base = os.path.splitext(input_path)[0]
        output_path = f"{base}_tmdb.csv"
    
    with open(input_path, encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        rows = list(reader)
    
    # Find IMDb column (case-insensitive)
    fieldnames = list(rows[0].keys()) if rows else []
    imdb_col = None
    for col in fieldnames:
        if col.lower() in (imdb_column.lower(), "imdb", "imdb_id", "imdbid"):
            imdb_col = col
            break
    
    if not imdb_col:
        print(f"Error: Column '{imdb_column}' not found in CSV", file=sys.stderr)
        print(f"Available columns: {', '.join(fieldnames)}", file=sys.stderr)
        sys.exit(1)
    
    # Add new columns
    new_fields = ["tmdb_id", "tmdb_title", "tmdb_year", "tmdb_url", "tmdb_poster"]
    all_fields = fieldnames + [f for f in new_fields if f not in fieldnames]
    
    # Convert each row
    for i, row in enumerate(rows):
        imdb_id = row.get(imdb_col, "")
        if not imdb_id:
            continue
        
        result = convert_id(imdb_id)
        if result:
            row["tmdb_id"] = result["tmdb_id"]
            row["tmdb_title"] = result["title"]
            row["tmdb_year"] = result["year"]
            row["tmdb_url"] = result["url"]
            row["tmdb_poster"] = result["poster"]
            print(f"  [{i+1}/{len(rows)}] {result['title']} ({result['year']}) — TMDB:{result['tmdb_id']}")
        else:
            row["tmdb_id"] = ""
            row["tmdb_title"] = ""
            print(f"  [{i+1}/{len(rows)}] Not found: {imdb_id}")
    
    # Write output
    with open(output_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=all_fields, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)
    
    print(f"\nWrote {len(rows)} rows to {output_path}")
    return output_path


def convert_file(input_path: str, output_path: str = None) -> str:
    """Convert a text file with one IMDb ID per line to CSV.
    
    Args:
        input_path: Input text file path
        output_path: Output CSV path
    
    Returns:
        Output file path
    """
    if not output_path:
        base = os.path.splitext(input_path)[0]
        output_path = f"{base}_tmdb.csv"
    
    with open(input_path) as f:
        imdb_ids = [line.strip() for line in f if line.strip()]
    
    results = batch_convert(imdb_ids)
    
    with open(output_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=[
            "imdb_id", "tmdb_id", "title", "year", "release_date",
            "rating", "votes", "poster", "url", "imdb_url"
        ])
        writer.writeheader()
        for r in results:
            if r:
                writer.writerow(r)
    
    print(f"Converted {len([r for r in results if r])}/{len(imdb_ids)} movies")
    print(f"Wrote to {output_path}")
    return output_path


# ── CLI ──────────────────────────────────────────────────────

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="IMDb → TMDB Converter")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("imdb_id", nargs="?", help="Single IMDb ID to convert")
    group.add_argument("--file", help="Text file with one IMDb ID per line")
    group.add_argument("--csv", help="CSV file with IMDb IDs")
    group.add_argument("--batch", nargs="+", help="Multiple IMDb IDs")
    
    parser.add_argument("-o", "--output", help="Output path")
    parser.add_argument("--column", default="imdb_id", help="CSV column name (default: imdb_id)")
    parser.add_argument("--json", action="store_true", help="Output as JSON")
    
    args = parser.parse_args()
    
    if not TMDB_KEY:
        print("Error: TMDB_API_KEY not set", file=sys.stderr)
        sys.exit(1)
    
    if args.imdb_id:
        result = convert_id(args.imdb_id)
        if result:
            if args.json:
                print(json.dumps(result, indent=2))
            else:
                print(f"Title: {result['title']} ({result['year']})")
                print(f"TMDB ID: {result['tmdb_id']}")
                print(f"TMDB URL: {result['url']}")
                print(f"Poster: {result['poster']}")
                print(f"Rating: {result['rating']}/10")
        else:
            print(f"Not found: {args.imdb_id}")
    
    elif args.file:
        convert_file(args.file, args.output)
    
    elif args.csv:
        convert_csv(args.csv, args.output, args.column)
    
    elif args.batch:
        results = batch_convert(args.batch)
        if args.json:
            print(json.dumps(results, indent=2, default=str))
        else:
            for r in results:
                if r:
                    print(f"  {r['imdb_id']} → TMDB:{r['tmdb_id']} | {r['title']} ({r['year']})")
                else:
                    print(f"  Not found")
