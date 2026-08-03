"""
ID resolver — matches items across services using IMDb/TMDB IDs or title+year.

All services normalize to a canonical item represented by:
  - imdb_id (preferred)
  - tmdb_id (fallback)
  - title + year (last resort)
"""

import re


def normalize_title(title):
    """Normalize a title for fuzzy matching."""
    if not title:
        return ""
    t = title.lower().strip()
    # Remove common suffixes/prefixes
    for suffix in [" (tv series)", " (tv movie)", " (video)", " (short)", " (mini series)"]:
        t = t.replace(suffix, "")
    # Remove non-alphanumeric except spaces
    t = re.sub(r"[^a-z0-9\s]", "", t)
    # Collapse whitespace
    t = re.sub(r"\s+", " ", t).strip()
    return t


def normalize_year(year_str):
    """Extract year from various formats."""
    if not year_str:
        return None
    if isinstance(year_str, int):
        return year_str
    s = str(year_str).strip()
    # Extract 4-digit year
    m = re.search(r"(\d{4})", s)
    return int(m.group(1)) if m else None


class CanonicalItem:
    """A normalized representation of a movie/show across all services."""

    def __init__(self, imdb_id=None, tmdb_id=None, title=None, year=None,
                 media_type=None, anilist_id=None, kodi_id=None):
        self.imdb_id = imdb_id
        self.tmdb_id = tmdb_id
        self.title = title
        self.year = normalize_year(year)
        self.media_type = media_type  # "movie" or "show"
        self.anilist_id = anilist_id
        self.kodi_id = kodi_id

        # Service-specific IDs (populated during resolution)
        self.trakt_id = None
        self.wetrakr_id = None
        self.imdb_internal_id = None
        self.letterboxd_lid = None
        self.plex_rating_key = None
        self.jellyfin_id = None
        self.simkl_id = None

        # Per-service state
        self.service_states = {}  # {service_name: {watched, rating, favorite, ...}}

    @property
    def display_name(self):
        year_str = f" ({self.year})" if self.year else ""
        return f"{self.title}{year_str}"

    def __repr__(self):
        return f"<CanonicalItem {self.display_name} imdb={self.imdb_id} tmdb={self.tmdb_id}>"


def build_key(item):
    """Build a dedup key for a canonical item."""
    if item.imdb_id:
        return f"imdb:{item.imdb_id}"
    if item.tmdb_id:
        return f"tmdb:{item.tmdb_id}"
    title = normalize_title(item.title)
    year = item.year or ""
    return f"titleyear:{title}:{year}"


def items_match(a, b):
    """Check if two items refer to the same content."""
    # IMDb match (strongest)
    if a.imdb_id and b.imdb_id:
        return a.imdb_id == b.imdb_id

    # TMDB match
    if a.tmdb_id and b.tmdb_id:
        return str(a.tmdb_id) == str(b.tmdb_id)

    # Title + year match
    if a.title and b.title:
        a_title = normalize_title(a.title)
        b_title = normalize_title(b.title)
        if a_title and b_title and a_title == b_title:
            if a.year and b.year:
                return abs(a.year - b.year) <= 1  # allow 1 year tolerance
            return True  # title match without year

    return False


def merge_items(a, b):
    """Merge two matched items, keeping the best available IDs."""
    merged = CanonicalItem(
        imdb_id=a.imdb_id or b.imdb_id,
        tmdb_id=a.tmdb_id or b.tmdb_id,
        title=a.title or b.title,
        year=a.year or b.year,
        media_type=a.media_type or b.media_type,
        anilist_id=a.anilist_id or b.anilist_id,
        kodi_id=a.kodi_id or b.kodi_id,
    )
    merged.trakt_id = a.trakt_id or b.trakt_id
    merged.wetrakr_id = a.wetrakr_id or b.wetrakr_id
    merged.imdb_internal_id = a.imdb_internal_id or b.imdb_internal_id
    merged.letterboxd_lid = a.letterboxd_lid or b.letterboxd_lid
    merged.plex_rating_key = a.plex_rating_key or b.plex_rating_key
    merged.jellyfin_id = a.jellyfin_id or b.jellyfin_id
    merged.simkl_id = a.simkl_id or b.simkl_id
    merged.service_states = {**b.service_states, **a.service_states}
    return merged
