"""
StreamSyncr Kodi Addon — Main Entry Point

Browse catalogs, resolve streams, and scrobble watch history
from your StreamSyncr backend instance.
"""

import sys
import urllib.parse
import xbmcgui
import xbmcplugin
import xbmcaddon

from resources.lib.api import StreamSyncrAPI
from resources.lib.catalogs import list_catalogs, list_catalog_items
from resources.lib.resolver import resolve_stream
from resources.lib.scrobbler import scrobble_start, scrobble_stop

ADDON = xbmcaddon.Addon()
HANDLE = int(sys.argv[1])
BASE_URL = sys.argv[0]
ARGS = urllib.parse.parse_qs(sys.argv[2][1:])


def build_url(action, **params):
    """Build a plugin URL with action and parameters."""
    params["action"] = action
    return f"{BASE_URL}?{urllib.parse.urlencode(params)}"


def get_api():
    """Get configured StreamSyncr API client."""
    backend_url = ADDON.getSetting("backend_url") or "http://localhost:7800"
    config_token = ADDON.getSetting("config_token") or ""
    return StreamSyncrAPI(backend_url, config_token)


def main_menu():
    """Display the main addon menu."""
    api = get_api()

    # Check backend connection
    if not api.ping():
        xbmcgui.Dialog().notification(
            "StreamSyncr",
            "Cannot connect to backend",
            xbmcgui.NOTIFICATION_ERROR,
            5000,
        )
        return

    # Get available catalogs from backend
    catalogs = api.get_catalogs()

    # Add main menu items
    items = []

    # Trending & Popular (always available)
    items.append({
        "label": "Trending",
        "icon": "DefaultVideo.png",
        "url": build_url("catalogs", section="trending"),
    })
    items.append({
        "label": "Popular",
        "icon": "DefaultVideo.png",
        "url": build_url("catalogs", section="popular"),
    })

    # User-specific catalogs (if configured)
    if catalogs:
        for section in ["watchlist", "favorites", "ratings", "lists"]:
            section_catalogs = [c for c in catalogs if section in c.get("id", "")]
            if section_catalogs:
                items.append({
                    "label": section.replace("_", " ").title(),
                    "icon": "DefaultVideo.png",
                    "url": build_url("catalogs", section=section),
                })

    # Search
    items.append({
        "label": "Search",
        "icon": "DefaultVideo.png",
        "url": build_url("search"),
    })

    # Settings
    items.append({
        "label": "Settings",
        "icon": "DefaultAddonProgram.png",
        "url": build_url("settings"),
    })

    # Build menu
    xbmcplugin.setPluginCategory(HANDLE, "StreamSyncr")
    xbmcplugin.setContent(HANDLE, "videos")

    for item in items:
        li = xbmcgui.ListItem(label=item["label"])
        li.setArt({"icon": item["icon"]})
        url = item["url"]
        xbmcplugin.addDirectoryItem(HANDLE, url, li, isFolder=True)

    xbmcplugin.endOfDirectory(HANDLE)


def search():
    """Handle search input and display results."""
    kb = xbmc.Keyboard("", "Search StreamSyncr")
    kb.doModal()
    if not kb.isConfirmed():
        return

    query = kb.getText()
    if not query:
        return

    api = get_api()
    results = api.search(query)

    xbmcplugin.setPluginCategory(HANDLE, f"Search: {query}")
    xbmcplugin.setContent(HANDLE, "videos")

    for item in results:
        li = xbmcgui.ListItem(label=item.get("name", "Unknown"))
        li.setInfo("video", {
            "title": item.get("name", ""),
            "year": item.get("year"),
            "rating": item.get("imdb_rating"),
            "plot": item.get("description"),
            "mediatype": "movie" if item.get("type") == "movie" else "episode",
        })
        if item.get("poster"):
            li.setArt({"poster": item["poster"], "thumb": item["poster"]})

        # Stream resolution
        url = build_url("play", imdb_id=item.get("id", ""), title=item.get("name", ""))
        xbmcplugin.addDirectoryItem(HANDLE, url, li, isFolder=False)

    xbmcplugin.endOfDirectory(HANDLE)


def play_item(imdb_id, title=""):
    """Resolve and play a stream."""
    api = get_api()

    # Resolve stream from debrid services
    streams = api.resolve_streams(imdb_id)

    if not streams:
        xbmcgui.Dialog().notification(
            "StreamSyncr",
            "No streams found",
            xbmcgui.NOTIFICATION_WARNING,
            3000,
        )
        return

    # Let user select if multiple streams
    if len(streams) == 1:
        selected = streams[0]
    else:
        labels = [f"{s.get('name', '?')} — {s.get('title', '')}" for s in streams]
        dialog = xbmcgui.Dialog()
        idx = dialog.select("Select Stream", labels)
        if idx < 0:
            return
        selected = streams[idx]

    # Play the stream
    url = selected.get("url", "")
    if not url:
        xbmcgui.Dialog().notification(
            "StreamSyncr",
            "Invalid stream URL",
            xbmcgui.NOTIFICATION_ERROR,
            3000,
        )
        return

    li = xbmcgui.ListItem(label=title or selected.get("title", ""))
    li.setPath(url)

    # Set inputstream for adaptive streams
    if url.startswith("http") and not url.endswith((".mp4", ".mkv", ".avi")):
        li.setProperty("inputstream", "inputstream.adaptive")
        li.setProperty("inputstream.adaptive.manifest_type", "hls")

    # Scrobble start
    scrobble_start(imdb_id)

    xbmcplugin.setResolvedUrl(HANDLE, True, li)


def main():
    """Main router."""
    action = ARGS.get("action", [None])[0]

    if action is None:
        main_menu()
    elif action == "catalogs":
        section = ARGS.get("section", ["trending"])[0]
        list_catalog_items(get_api(), section, HANDLE, build_url)
    elif action == "search":
        search()
    elif action == "play":
        imdb_id = ARGS.get("imdb_id", [""])[0]
        title = ARGS.get("title", [""])[0]
        play_item(imdb_id, title)
    elif action == "settings":
        ADDON.openSettings()
    else:
        main_menu()


if __name__ == "__main__":
    main()