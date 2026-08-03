#!/usr/bin/env python3
"""
TMDB CLI — command-line interface to TMDB API

Usage:
    tmdb search <query>                    # search movies
    tmdb search-tv <query>                 # search TV shows
    tmdb movie <tmdb_id>                   # movie details
    tmdb tv <tmdb_id>                      # TV show details
    tmdb trending                          # trending movies
    tmdb trending-tv                       # trending TV shows
    tmdb popular                           # popular movies
    tmdb popular-tv                        # popular TV shows
    tmdb top-rated                         # top rated movies
    tmdb now-playing                       # now playing
    tmdb upcoming                          # upcoming movies
    tmdb genres                            # movie genres
    tmdb similar <tmdb_id>                 # similar movies
    tmdb cast <tmdb_id>                    # movie cast
    tmdb find-imdb <imdb_id>               # find by IMDb ID
    tmdb watch-providers <tmdb_id>         # streaming availability
"""

import argparse
import json
import sys


def pp(data):
    print(json.dumps(data, indent=2, default=str))


def main():
    parser = argparse.ArgumentParser(description="TMDB CLI")
    sub = parser.add_subparsers(dest="command")

    # search
    p = sub.add_parser("search", help="Search movies")
    p.add_argument("query")
    p.add_argument("--year", type=int)

    p = sub.add_parser("search-tv", help="Search TV shows")
    p.add_argument("query")

    p = sub.add_parser("search-multi", help="Search all media")
    p.add_argument("query")

    # details
    p = sub.add_parser("movie", help="Movie details")
    p.add_argument("tmdb_id", type=int)

    p = sub.add_parser("tv", help="TV show details")
    p.add_argument("tmdb_id", type=int)

    # lists
    sub.add_parser("trending", help="Trending movies")
    sub.add_parser("trending-tv", help="Trending TV shows")
    sub.add_parser("popular", help="Popular movies")
    sub.add_parser("popular-tv", help="Popular TV shows")
    sub.add_parser("top-rated", help="Top rated movies")
    sub.add_parser("top-rated-tv", help="Top rated TV shows")
    sub.add_parser("now-playing", help="Now playing movies")
    sub.add_parser("upcoming", help="Upcoming movies")
    sub.add_parser("on-the-air", help="On the air TV")
    sub.add_parser("airing-today", help="TV airing today")

    # genres
    sub.add_parser("genres", help="Movie genres")
    sub.add_parser("genres-tv", help="TV genres")

    # details
    p = sub.add_parser("similar", help="Similar movies")
    p.add_argument("tmdb_id", type=int)

    p = sub.add_parser("recommendations", help="Movie recommendations")
    p.add_argument("tmdb_id", type=int)

    p = sub.add_parser("cast", help="Movie cast")
    p.add_argument("tmdb_id", type=int)

    p = sub.add_parser("find-imdb", help="Find movie by IMDb ID")
    p.add_argument("imdb_id")

    p = sub.add_parser("watch-providers", help="Streaming availability")
    p.add_argument("tmdb_id", type=int)

    # discover
    p = sub.add_parser("discover", help="Discover movies")
    p.add_argument("--genre", type=int)
    p.add_argument("--year", type=int)
    p.add_argument("--rating", type=float)

    # lists
    p = sub.add_parser("list", help="List details")
    p.add_argument("list_id", type=int)

    p = sub.add_parser("list-items", help="Items in a list")
    p.add_argument("list_id", type=int)

    p = sub.add_parser("my-lists", help="Your lists (requires session)")

    p = sub.add_parser("create-list", help="Create a list (requires session)")
    p.add_argument("name")
    p.add_argument("--description", default="")
    p.add_argument("--session-id", required=True)

    p = sub.add_parser("delete-list", help="Delete a list (requires session)")
    p.add_argument("list_id", type=int)
    p.add_argument("--session-id", required=True)

    p = sub.add_parser("add-to-list", help="Add movies to list")
    p.add_argument("list_id", type=int)
    p.add_argument("movie_ids", nargs="+", type=int)
    p.add_argument("--session-id", required=True)

    p = sub.add_parser("remove-from-list", help="Remove movies from list")
    p.add_argument("list_id", type=int)
    p.add_argument("movie_ids", nargs="+", type=int)
    p.add_argument("--session-id", required=True)

    p = sub.add_parser("clear-list", help="Clear a list")
    p.add_argument("list_id", type=int)
    p.add_argument("--session-id", required=True)

    p = sub.add_parser("in-list", help="Check if movie is in a list")
    p.add_argument("list_id", type=int)
    p.add_argument("movie_id", type=int)

    p = sub.add_parser("collection-items", help="Movies in a collection")
    p.add_argument("collection_id", type=int)

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return

    from tmdb_api import TMDBClient
    t = TMDBClient()

    if args.command == "search":
        results = t.search_movie(args.query, args.year)
        for r in results:
            print(f"  {r['title']} ({r.get('release_date', '')[:4]}) — TMDB:{r['id']}")

    elif args.command == "search-tv":
        results = t.search_tv(args.query)
        for r in results:
            print(f"  {r['name']} ({r.get('first_air_date', '')[:4]}) — TMDB:{r['id']}")

    elif args.command == "search-multi":
        results = t.search_multi(args.query)
        for r in results:
            title = r.get("title", r.get("name", ""))
            year = r.get("release_date", r.get("first_air_date", ""))[:4]
            print(f"  {title} ({year}) — {r.get('media_type', '?')} — TMDB:{r['id']}")

    elif args.command == "movie":
        m = t.movie(args.tmdb_id)
        print(f"{m['title']} ({m.get('release_date', '')[:4]})")
        print(f"  Rating: {m.get('vote_average', 0)}/10 ({m.get('vote_count', 0)} votes)")
        print(f"  Runtime: {m.get('runtime', '?')} min")
        genres = ", ".join(g["name"] for g in m.get("genres", []))
        print(f"  Genres: {genres}")
        print(f"  Overview: {m.get('overview', '')[:200]}")

    elif args.command == "tv":
        s = t.tv(args.tmdb_id)
        print(f"{s['name']} ({s.get('first_air_date', '')[:4]})")
        print(f"  Rating: {s.get('vote_average', 0)}/10 ({s.get('vote_count', 0)} votes)")
        print(f"  Seasons: {s.get('number_of_seasons', '?')}")
        print(f"  Episodes: {s.get('number_of_episodes', '?')}")
        genres = ", ".join(g["name"] for g in s.get("genres", []))
        print(f"  Genres: {genres}")
        print(f"  Overview: {s.get('overview', '')[:200]}")

    elif args.command == "trending":
        items = t.trending_movies()
        for i, m in enumerate(items[:20], 1):
            print(f"  {i}. {m['title']} ({m.get('release_date', '')[:4]})")

    elif args.command == "trending-tv":
        items = t.trending_tv()
        for i, s in enumerate(items[:20], 1):
            print(f"  {i}. {s['name']} ({s.get('first_air_date', '')[:4]})")

    elif args.command == "popular":
        items = t.popular_movies()
        for i, m in enumerate(items[:20], 1):
            print(f"  {i}. {m['title']} ({m.get('release_date', '')[:4]})")

    elif args.command == "popular-tv":
        items = t.popular_tv()
        for i, s in enumerate(items[:20], 1):
            print(f"  {i}. {s['name']} ({s.get('first_air_date', '')[:4]})")

    elif args.command == "top-rated":
        items = t.top_rated_movies()
        for i, m in enumerate(items[:20], 1):
            print(f"  {i}. {m['title']} ({m.get('release_date', '')[:4]}) — {m.get('vote_average', 0)}/10")

    elif args.command == "top-rated-tv":
        items = t.top_rated_tv()
        for i, s in enumerate(items[:20], 1):
            print(f"  {i}. {s['name']} ({s.get('first_air_date', '')[:4]}) — {s.get('vote_average', 0)}/10")

    elif args.command == "now-playing":
        items = t.now_playing()
        for i, m in enumerate(items[:20], 1):
            print(f"  {i}. {m['title']} ({m.get('release_date', '')[:4]})")

    elif args.command == "upcoming":
        items = t.upcoming()
        for i, m in enumerate(items[:20], 1):
            print(f"  {i}. {m['title']} ({m.get('release_date', '')[:4]})")

    elif args.command == "on-the-air":
        items = t.on_the_air()
        for i, s in enumerate(items[:20], 1):
            print(f"  {i}. {s['name']} ({s.get('first_air_date', '')[:4]})")

    elif args.command == "airing-today":
        items = t.airing_today()
        for i, s in enumerate(items[:20], 1):
            print(f"  {i}. {s['name']} ({s.get('first_air_date', '')[:4]})")

    elif args.command == "genres":
        for g in t.genres_movie():
            print(f"  {g['id']}: {g['name']}")

    elif args.command == "genres-tv":
        for g in t.genres_tv():
            print(f"  {g['id']}: {g['name']}")

    elif args.command == "similar":
        items = t.movie_similar(args.tmdb_id)
        for i, m in enumerate(items[:20], 1):
            print(f"  {i}. {m['title']} ({m.get('release_date', '')[:4]})")

    elif args.command == "recommendations":
        items = t.movie_recommendations(args.tmdb_id)
        for i, m in enumerate(items[:20], 1):
            print(f"  {i}. {m['title']} ({m.get('release_date', '')[:4]})")

    elif args.command == "cast":
        credits = t.movie_credits(args.tmdb_id)
        print("Cast:")
        for c in credits.get("cast", [])[:15]:
            print(f"  {c['name']} as {c.get('character', '?')}")

    elif args.command == "find-imdb":
        m = t.find_by_imdb(args.imdb_id)
        if m:
            print(f"{m['title']} ({m.get('release_date', '')[:4]}) — TMDB:{m['id']}")
        else:
            print("Not found")

    elif args.command == "watch-providers":
        providers = t.movie_watch_providers(args.tmdb_id)
        if providers:
            for country, info in providers.items():
                print(f"  {country}:")
                for p in info.get("flatrate", []):
                    print(f"    Stream: {p['provider_name']}")
                for p in info.get("rent", []):
                    print(f"    Rent: {p['provider_name']}")
        else:
            print("No watch providers found")

    elif args.command == "discover":
        kwargs = {}
        if args.genre:
            kwargs["genre"] = args.genre
        if args.year:
            kwargs["year"] = args.year
        if args.rating:
            kwargs["vote_average.gte"] = args.rating
        items = t.discover_movies(**kwargs)
        for i, m in enumerate(items[:20], 1):
            print(f"  {i}. {m['title']} ({m.get('release_date', '')[:4]}) — {m.get('vote_average', 0)}/10")

    elif args.command == "list":
        lst = t.list_details(args.list_id)
        print(f"{lst['name']}")
        print(f"  Description: {lst.get('description', '')}")
        print(f"  Items: {lst.get('item_count', 0)}")
        owner = lst.get('created_by', '')
        if isinstance(owner, dict):
            owner = owner.get('name', '?')
        print(f"  Created by: {owner}")

    elif args.command == "list-items":
        items = t.list_items(args.list_id)
        print(f"List items ({len(items)}):")
        for i, m in enumerate(items[:30], 1):
            print(f"  {i}. {m.get('title', m.get('name', ''))} ({m.get('release_date', m.get('first_air_date', ''))[:4]})")

    elif args.command == "my-lists":
        print("--session-id required (use: python -m tmdb_api.cli my-lists --session-id XXX)")

    elif args.command == "create-list":
        result = t.list_create(args.session_id, args.name, args.description)
        print(f"Created list: {result.get('status_message', '')}")
        print(f"List ID: {result.get('list_id', '?')}")

    elif args.command == "delete-list":
        result = t.list_delete(args.list_id, args.session_id)
        print(f"Deleted: {result.get('status_message', '')}")

    elif args.command == "add-to-list":
        result = t.list_add_items(args.list_id, args.session_id, args.movie_ids)
        print(f"Added {len(args.movie_ids)} movies: {result.get('status_message', '')}")

    elif args.command == "remove-from-list":
        result = t.list_remove_items(args.list_id, args.session_id, args.movie_ids)
        print(f"Removed {len(args.movie_ids)} movies: {result.get('status_message', '')}")

    elif args.command == "clear-list":
        result = t.list_clear(args.list_id, args.session_id)
        print(f"Cleared: {result.get('status_message', '')}")

    elif args.command == "in-list":
        present = t.list_check_item(args.list_id, args.movie_id)
        print(f"{'Yes' if present else 'No'} — movie {'is' if present else 'is not'} in list")

    elif args.command == "collection-items":
        items = t.collection_items(args.collection_id)
        print(f"Collection ({len(items)} movies):")
        for i, m in enumerate(items[:30], 1):
            print(f"  {i}. {m.get('title', '')} ({m.get('release_date', '')[:4]})")


if __name__ == "__main__":
    main()
