#!/usr/bin/env python3
"""
Trakt CLI — command-line interface to Trakt API

Usage:
    trakt me                          # profile
    trakt lists                       # all lists
    trakt list items <list_id>        # items in a list
    trakt collection                  # collection (movies)
    trakt watchlist                   # watchlist
    trakt history                     # watch history
    trakt ratings                     # ratings
    trakt search <query>              # search
    trakt trending                    # trending movies
    trakt movie <trakt_id>            # movie details
    trakt add-to-list <list> <ids>    # add trakt IDs to list
    trakt remove-from-list <list> <ids> # remove from list
    trakt rate <rating> <ids>         # rate (1-10)
    trakt watch <ids>                 # mark watched
"""

import argparse
import json
import sys


def pp(data):
    print(json.dumps(data, indent=2, default=str))


def main():
    parser = argparse.ArgumentParser(description="Trakt CLI")
    sub = parser.add_subparsers(dest="command")

    # me
    sub.add_parser("me", help="Profile info")

    # lists
    sub.add_parser("lists", help="All lists")

    # list items
    p = sub.add_parser("list-items", help="Items in a list")
    p.add_argument("list_id", type=int)

    # collection
    p = sub.add_parser("collection", help="Collection")
    p.add_argument("--shows", action="store_true")

    # watchlist
    p = sub.add_parser("watchlist", help="Watchlist")
    p.add_argument("--shows", action="store_true")

    # history
    p = sub.add_parser("history", help="Watch history")
    p.add_argument("--shows", action="store_true")

    # ratings
    p = sub.add_parser("ratings", help="Ratings")
    p.add_argument("--shows", action="store_true")

    # search
    p = sub.add_parser("search", help="Search")
    p.add_argument("query")
    p.add_argument("--type", default="movie", choices=["movie", "show", "episode"])

    # trending
    sub.add_parser("trending", help="Trending movies")
    sub.add_parser("popular", help="Popular movies")

    # movie
    p = sub.add_parser("movie", help="Movie details")
    p.add_argument("trakt_id", type=int)

    # add-to-list
    p = sub.add_parser("add-to-list", help="Add movies to list")
    p.add_argument("list_name")
    p.add_argument("ids", nargs="+", type=int, help="Trakt IDs")

    # remove-from-list
    p = sub.add_parser("remove-from-list", help="Remove from list")
    p.add_argument("list_name")
    p.add_argument("ids", nargs="+", type=int)

    # rate
    p = sub.add_parser("rate", help="Rate movies (1-10)")
    p.add_argument("rating", type=int)
    p.add_argument("ids", nargs="+", type=int)

    # watch
    p = sub.add_parser("watch", help="Mark watched")
    p.add_argument("ids", nargs="+", type=int)

    # movie-in-lists
    p = sub.add_parser("movie-in-lists", help="Which lists contain a movie")
    p.add_argument("trakt_id", type=int)

    # social
    sub.add_parser("following", help="Who you're following")
    sub.add_parser("followers", help="Your followers")

    p = sub.add_parser("follow", help="Follow a user")
    p.add_argument("username")

    p = sub.add_parser("unfollow", help="Unfollow a user")
    p.add_argument("username")

    p = sub.add_parser("user", help="User profile")
    p.add_argument("username")

    p = sub.add_parser("is-following", help="Check if following a user")
    p.add_argument("username")

    # watched
    sub.add_parser("watched", help="Watch history")
    p = sub.add_parser("watched-movies", help="Watched movies")
    sub.add_parser("watched-shows", help="Watched shows")

    # unwatch
    p = sub.add_parser("unwatch", help="Remove from history")
    p.add_argument("ids", nargs="+", type=int)
    sub.add_parser("unwatch-all", help="Remove all from history")

    # favorites
    sub.add_parser("favorites", help="Get favorites")
    p = sub.add_parser("favorite", help="Add to favorites")
    p.add_argument("ids", nargs="+", type=int)
    p = sub.add_parser("unfavorite", help="Remove from favorites")
    p.add_argument("ids", nargs="+", type=int)

    # plan to watch
    sub.add_parser("plan-to-watch", help="Plan to watch list")

    # scrobble
    p = sub.add_parser("scrobble-start", help="Start watching")
    p.add_argument("trakt_id", type=int)
    p.add_argument("--show", action="store_true", help="TV show episode")

    p = sub.add_parser("scrobble-pause", help="Pause watching")
    p.add_argument("trakt_id", type=int)
    p.add_argument("--progress", type=float, default=0.0)

    p = sub.add_parser("scrobble-stop", help="Stop watching")
    p.add_argument("trakt_id", type=int)
    p.add_argument("--progress", type=float, default=100.0)
    p.add_argument("--show", action="store_true", help="TV show episode")

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return

    from trakt_api import TraktClient
    t = TraktClient()

    if args.command == "me":
        pp(t.me())

    elif args.command == "lists":
        for lst in t.lists():
            print(f"  {lst['name']} (id: {lst['ids']['trakt']})")

    elif args.command == "list-items":
        for item in t.list_items(args.list_id):
            obj = item.get("movie", item.get("show", {}))
            print(f"  {obj.get('title')} ({obj.get('year')})")

    elif args.command == "collection":
        media = "shows" if args.shows else "movies"
        items = t.collection(media)
        print(f"Collection ({len(items)} items):")
        for item in items:
            obj = item.get("movie", item.get("show", {}))
            print(f"  {obj.get('title')} ({obj.get('year')})")

    elif args.command == "watchlist":
        media = "shows" if args.shows else "movies"
        items = t.watchlist(media)
        print(f"Watchlist ({len(items)} items):")
        for item in items:
            obj = item.get("movie", item.get("show", {}))
            print(f"  {obj.get('title')} ({obj.get('year')})")

    elif args.command == "history":
        media = "shows" if args.shows else "movies"
        items = t.history(media)
        print(f"History ({len(items)} items):")
        for item in items:
            obj = item.get("movie", item.get("show", {}))
            print(f"  {obj.get('title')} ({obj.get('year')})")

    elif args.command == "ratings":
        media = "shows" if args.shows else "movies"
        items = t.ratings(media)
        print(f"Ratings ({len(items)} items):")
        for item in items:
            obj = item.get("movie", item.get("show", {}))
            print(f"  {item.get('rating', '')}/10 — {obj.get('title')} ({obj.get('year')})")

    elif args.command == "search":
        results = t.search(args.query, args.type)
        for r in results:
            obj = r.get(args.type, {})
            print(f"  {obj.get('title', obj.get('name', ''))} ({obj.get('year', '')}) — trakt:{obj.get('ids', {}).get('trakt')}")

    elif args.command == "trending":
        items = t.trending_movies()
        for item in items:
            m = item.get("movie", {})
            print(f"  {m.get('title')} ({m.get('year')}) — {item.get('watchers', '?')} watching")

    elif args.command == "popular":
        items = t.popular_movies()
        for m in items:
            print(f"  {m.get('title')} ({m.get('year')})")

    elif args.command == "movie":
        m = t.movie(args.trakt_id)
        pp(m)

    elif args.command == "add-to-list":
        t.add_to_list(args.list_name, movies=args.ids)
        print(f"Added {len(args.ids)} movies to '{args.list_name}'")

    elif args.command == "remove-from-list":
        t.remove_from_list(args.list_name, movies=args.ids)
        print(f"Removed {len(args.ids)} movies from '{args.list_name}'")

    elif args.command == "rate":
        t.rate(args.rating, movies=args.ids)
        print(f"Rated {len(args.ids)} movies {args.rating}/10")

    elif args.command == "watch":
        t.mark_watched(movies=[{"ids": {"trakt": tid}, "watched_at": "now"} for tid in args.ids])
        print(f"Marked {len(args.ids)} movies watched")

    elif args.command == "movie-in-lists":
        lists = t.movie_in_lists(args.trakt_id)
        if lists:
            print(f"Found in {len(lists)} lists:")
            for l in lists:
                print(f"  {l['name']}")
        else:
            print("Not found in any lists")

    elif args.command == "following":
        users = t.following()
        if users:
            print(f"Following {len(users)} users:")
            for u in users:
                print(f"  {u['username']} ({u.get('name', '')})")
        else:
            print("Not following anyone")

    elif args.command == "followers":
        users = t.followers()
        if users:
            print(f"{len(users)} followers:")
            for u in users:
                print(f"  {u['username']} ({u.get('name', '')})")
        else:
            print("No followers")

    elif args.command == "follow":
        result = t.follow_user(args.username)
        print(f"Followed {args.username}")

    elif args.command == "unfollow":
        t.unfollow_user(args.username)
        print(f"Unfollowed {args.username}")

    elif args.command == "user":
        pp(t.user_profile(args.username))

    elif args.command == "is-following":
        if t.is_following(args.username):
            print(f"Yes, you are following {args.username}")
        else:
            print(f"No, you are not following {args.username}")

    elif args.command == "watched":
        items = t.history()
        print(f"Watch history ({len(items)} items):")
        for item in items[:30]:
            obj = item.get("movie", item.get("show", {}))
            print(f"  {obj.get('title')} ({obj.get('year')}) — {item.get('watched_at', '')[:10]}")

    elif args.command == "watched-movies":
        items = t.get_watched_movies()
        print(f"Watched movies ({len(items)}):")
        for item in items[:30]:
            m = item.get("movie", {})
            print(f"  {m.get('title')} ({m.get('year')}) — {item.get('watched_at', '')[:10]}")

    elif args.command == "watched-shows":
        items = t.get_watched_shows()
        print(f"Watched shows ({len(items)}):")
        for item in items[:30]:
            s = item.get("show", {})
            print(f"  {s.get('title')} ({s.get('year')})")

    elif args.command == "unwatch":
        t.unwatch(movies=args.ids)
        print(f"Removed {len(args.ids)} movies from history")

    elif args.command == "unwatch-all":
        t.unwatch_all()
        print("Removed all from history")

    elif args.command == "favorites":
        items = t.get_favorites()
        print(f"Favorites ({len(items)} items):")
        for item in items[:30]:
            obj = item.get("movie", item.get("show", {}))
            print(f"  {obj.get('title')} ({obj.get('year')})")

    elif args.command == "favorite":
        t.favorite(movies=args.ids)
        print(f"Added {len(args.ids)} movies to favorites")

    elif args.command == "unfavorite":
        t.unfavorite(movies=args.ids)
        print(f"Removed {len(args.ids)} movies from favorites")

    elif args.command == "plan-to-watch":
        items = t.get_plantowatch()
        print(f"Plan to watch ({len(items)} items):")
        for item in items[:30]:
            obj = item.get("movie", item.get("show", {}))
            print(f"  {obj.get('title')} ({obj.get('year')})")

    elif args.command == "scrobble-start":
        media = "episode" if args.show else "movie"
        result = t.scrobble_start(args.trakt_id, media)
        print(f"Started watching: {result.get('movie', result.get('show', {})).get('title', '?')}")
        print(f"Progress: {result.get('progress', 0)}%")

    elif args.command == "scrobble-pause":
        result = t.scrobble_pause(args.trakt_id, progress=args.progress)
        print(f"Paused: {result.get('movie', result.get('show', {})).get('title', '?')}")
        print(f"Progress: {result.get('progress', 0)}%")

    elif args.command == "scrobble-stop":
        media = "episode" if args.show else "movie"
        result = t.scrobble_stop(args.trakt_id, media, args.progress)
        if "message" in result:
            print(f"Error: {result['message']}")
        elif "watched_at" in result:
            print(f"Watched! Recorded at: {result['watched_at']}")
        else:
            title = result.get('movie', result.get('show', {}))
            if isinstance(title, dict):
                title = title.get('title', '?')
            print(f"Stopped: {title}")
            print(f"Progress: {result.get('progress', 0)}%")
            print(f"Action: {result.get('action', '?')}")


if __name__ == "__main__":
    main()
