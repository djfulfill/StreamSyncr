"""
Conflict resolution — determines the winning state when services disagree.

Strategies:
  - newest_wins: Most recent timestamp wins
  - watched_overrides: Watched always wins over unwatched
  - source_priority: User-configured service priority
  - manual: User resolves each conflict
"""

from enum import Enum


class ResolutionStrategy(Enum):
    NEWEST_WINS = "newest_wins"
    WATCHED_OVERRIDES = "watched_overrides"
    SOURCE_PRIORITY = "source_priority"
    MOST_COMPLETE = "most_complete"


DEFAULT_SERVICE_PRIORITY = [
    "plex", "jellyfin", "kodi",      # local servers (authoritative)
    "trakt",                           # dedicated tracker
    "wetrakr",                         # unofficial tracker
    "simkl",                           # tracker
    "anilist",                         # anime-specific
    "imdb",                            # read-only-ish
    "letterboxd",                      # social/logging
]


def resolve_watched(item, strategy=ResolutionStrategy.WATCHED_OVERRIDES,
                    service_priority=None):
    """
    Resolve watched status across services.

    Returns:
        dict: {service: should_be_watched} for each service
    """
    if service_priority is None:
        service_priority = DEFAULT_SERVICE_PRIORITY

    states = item.service_states
    if not states:
        return {}

    # Collect watched statuses
    watched_services = []
    unwatched_services = []
    for svc, state in states.items():
        if state.get("watched"):
            watched_services.append((svc, state))
        else:
            unwatched_services.append((svc, state))

    if not watched_services:
        return {svc: False for svc in states}
    if not unwatched_services:
        return {svc: True for svc in states}

    # All agree → no conflict
    if not watched_services or not unwatched_services:
        return {svc: True for svc in states}

    if strategy == ResolutionStrategy.WATCHED_OVERRIDES:
        # Watched always wins — if ANY service says watched, mark all as watched
        return {svc: True for svc in states}

    elif strategy == ResolutionStrategy.NEWEST_WINS:
        # Find the most recent timestamp
        latest = None
        latest_watched = True
        for svc, state in watched_services:
            ts = state.get("watched_at")
            if ts and (latest is None or ts > latest):
                latest = ts
                latest_watched = True
        for svc, state in unwatched_services:
            ts = state.get("watched_at")
            if ts and (latest is None or ts > latest):
                latest = ts
                latest_watched = False
        return {svc: latest_watched for svc in states}

    elif strategy == ResolutionStrategy.SOURCE_PRIORITY:
        # Highest priority service wins
        for svc in service_priority:
            if svc in states:
                is_watched = states[svc].get("watched", False)
                return {s: is_watched for s in states}
        # Fallback: watched wins
        return {svc: bool(watched_services) for svc in states}

    elif strategy == ResolutionStrategy.MOST_COMPLETE:
        # Service with most data wins
        best_svc = None
        best_score = -1
        for svc, state in {**watched_services, **unwatched_services}.items():
            score = sum(1 for v in state.values() if v is not None)
            if score > best_score:
                best_score = score
                best_svc = svc
        is_watched = states[best_svc].get("watched", False) if best_svc else False
        return {svc: is_watched for svc in states}

    return {svc: False for svc in states}


def resolve_rating(item, strategy=ResolutionStrategy.NEWEST_WINS,
                   service_priority=None):
    """
    Resolve rating conflicts.

    Returns:
        dict: {service: rating} or None if no rating
    """
    if service_priority is None:
        service_priority = DEFAULT_SERVICE_PRIORITY

    states = item.service_states
    rated = {svc: s for svc, s in states.items() if s.get("rating") is not None}

    if not rated:
        return {svc: None for svc in states}
    if len(rated) == 1:
        svc = list(rated.keys())[0]
        return {s: rated[svc].get("rating") if s == svc else None for s in states}

    if strategy == ResolutionStrategy.NEWEST_WINS:
        latest = None
        best_rating = None
        for svc, state in rated.items():
            ts = state.get("rated_at")
            if ts and (latest is None or ts > latest):
                latest = ts
                best_rating = state["rating"]
        return {s: best_rating if s in rated and rated[s].get("rated_at") == latest else
                (rated[s]["rating"] if len(rated) == 1 else None) for s in states}

    elif strategy == ResolutionStrategy.SOURCE_PRIORITY:
        for svc in service_priority:
            if svc in rated:
                rating = rated[svc]["rating"]
                return {s: rating for s in states}

    elif strategy == ResolutionStrategy.MOST_COMPLETE:
        best_svc = max(rated.keys(),
                       key=lambda s: sum(1 for v in rated[s].values() if v is not None))
        return {s: rated[best_svc]["rating"] for s in states}

    # Fallback: average
    ratings = [s["rating"] for s in rated.values() if s.get("rating")]
    avg = sum(ratings) / len(ratings) if ratings else None
    return {svc: avg for svc in states}


def resolve_favorite(item, strategy=ResolutionStrategy.WATCHED_OVERRIDES,
                     service_priority=None):
    """
    Resolve favorite status.

    Returns:
        dict: {service: is_favorite}
    """
    states = item.service_states
    favorited = [svc for svc, s in states.items() if s.get("favorite")]

    if not favorited:
        return {svc: False for svc in states}

    if strategy in (ResolutionStrategy.WATCHED_OVERRIDES, ResolutionStrategy.MOST_COMPLETE):
        return {svc: True for svc in states}

    elif strategy == ResolutionStrategy.SOURCE_PRIORITY:
        for svc in service_priority:
            if svc in states:
                return {s: states[svc].get("favorite", False) for s in states}

    return {svc: svc in favorited for svc in states}


def resolve_all(item, strategy=ResolutionStrategy.WATCHED_OVERRIDES,
                service_priority=None):
    """Resolve all fields for an item. Returns a full resolution dict."""
    return {
        "watched": resolve_watched(item, strategy, service_priority),
        "rating": resolve_rating(item, strategy, service_priority),
        "favorite": resolve_favorite(item, strategy, service_priority),
    }
