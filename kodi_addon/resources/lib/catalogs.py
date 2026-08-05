"""
Catalog browsing for the StreamSyncr Kodi addon.

Lists catalogs and items from the StreamSyncr backend.
"""

import xbmcgui
import xbmcplugin


def list_catalogs(api, section, handle, build_url):
    """List available catalogs in a section."""
    all_catalogs = api.get_catalogs()

    # Filter catalogs by section
    section_filters = {
        "trending": ["trending"],
        "popular": ["popular"],
        "watchlist": ["watchlist"],
        "favorites": ["favorites", "favs"],
        "ratings": ["ratings", "rated"],
        "lists": ["list"],
    }

    keywords = section_filters.get(section, [section])
    filtered = [
        c for c in all_catalogs
        if any(kw in c.get("id", "").lower() for kw in keywords)
    ]

    if not filtered:
        # Show all catalogs if section filter returns nothing
        filtered = all_catalogs

    xbmcplugin.setPluginCategory(handle, f"StreamSyncr — {section.title()}")
    xbmcplugin.setContent(handle, "videos")

    for catalog in filtered:
        cat_type = catalog.get("type", "movie")
        cat_id = catalog.get("id", "")
        cat_name = catalog.get("name", cat_id)

        li = xbmcgui.ListItem(label=cat_name)
        li.setArt({"icon": "DefaultVideo.png"})

        # Add type badge
        type_badge = cat_type.upper()[:3]
        li.setLabel2(f"[{type_badge}] {cat_name}")

        url = build_url(
            "catalog_items",
            catalog_type=cat_type,
            catalog_id=cat_id,
        )
        xbmcplugin.addDirectoryItem(handle, url, li, isFolder=True)

    xbmcplugin.endOfDirectory(handle)


def list_catalog_items(api, section, handle, build_url):
    """List items within a catalog."""
    # This is called from the main router with section as catalog_type:catalog_id
    # For simplicity, we'll list trending movies by default
    xbmcplugin.setPluginCategory(handle, f"StreamSyncr — {section.title()}")
    xbmcplugin.setContent(handle, "videos")

    # Determine what to show based on section
    if section == "trending":
        items = api.get_catalog("movie", "tmdb-trending")
    elif section == "popular":
        items = api.get_catalog("movie", "tmdb-popular")
    elif section == "watchlist":
        items = api.get_catalog("movie", "trakt-watchlist")
    elif section == "favorites":
        items = api.get_catalog("movie", "trakt-favorites")
    elif section == "ratings":
        items = api.get_catalog("movie", "imdb-ratings")
    else:
        items = api.get_catalog("movie", "tmdb-trending")

    for item in items:
        meta = _item_to_listitem(item, build_url)
        if meta:
            xbmcplugin.addDirectoryItem(
                handle,
                meta["url"],
                meta["listitem"],
                isFolder=False,
            )

    xbmcplugin.endOfDirectory(handle)


def list_catalog_items_direct(api, catalog_type, catalog_id, handle, build_url):
    """List items from a specific catalog ID."""
    xbmcplugin.setPluginCategory(handle, f"StreamSyncr — {catalog_id}")
    xbmcplugin.setContent(handle, "videos")

    items = api.get_catalog(catalog_type, catalog_id)

    for item in items:
        meta = _item_to_listitem(item, build_url)
        if meta:
            xbmcplugin.addDirectoryItem(
                handle,
                meta["url"],
                meta["listitem"],
                isFolder=False,
            )

    xbmcplugin.endOfDirectory(handle)


def _item_to_listitem(item, build_url):
    """Convert a StreamSyncr meta item to a Kodi ListItem."""
    item_id = item.get("id", "")
    name = item.get("name", "Unknown")
    year = item.get("year")
    item_type = item.get("type", "movie")
    poster = item.get("poster")
    rating = item.get("imdb_rating")

    if not item_id:
        return None

    # Build display label
    label = name
    if year:
        label = f"{name} ({year})"

    li = xbmcgui.ListItem(label=label)

    # Set info
    info = {
        "title": name,
        "mediatype": "movie" if item_type == "movie" else "episode",
    }
    if year:
        info["year"] = year
    if rating:
        info["rating"] = rating
    if item.get("description"):
        info["plot"] = item["description"]

    li.setInfo("video", info)

    # Set art
    art = {}
    if poster:
        art["poster"] = poster
        art["thumb"] = poster
        art["fanart"] = poster
    li.setArt(art)

    # Build play URL
    imdb_id = item_id if item_id.startswith("tt") else ""
    url = build_url(
        "play",
        imdb_id=imdb_id,
        title=name,
        media_type=item_type,
    )

    return {"url": url, "listitem": li}