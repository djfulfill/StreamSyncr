"""
Stream resolver for the StreamSyncr Kodi addon.

Resolves debrid service streams (Real-Debrid, TorBox, AllDebrid)
and returns playable URLs for Kodi.
"""

import xbmcgui
import xbmcaddon


def resolve_stream(api, imdb_id, title=""):
    """
    Resolve a stream for the given IMDb ID.

    Returns a list of stream dicts with:
        - url: playable URL
        - name: service name (e.g., "Real-Debrid")
        - title: filename or description
        - quality: stream quality info
        - binge_group: for resume tracking
    """
    if not imdb_id:
        return []

    streams = api.resolve_streams("movie", imdb_id)

    resolved = []
    for stream in streams:
        resolved.append({
            "url": stream.get("url", ""),
            "name": stream.get("name", "Unknown"),
            "title": stream.get("title", ""),
            "quality": _extract_quality(stream),
            "binge_group": stream.get("behaviorHints", {}).get("binge_group", ""),
        })

    # Sort by quality (4K > 1080p > 720p > SD)
    resolved.sort(key=lambda s: _quality_rank(s["quality"]), reverse=True)

    return resolved


def _extract_quality(stream):
    """Extract quality info from stream title or filename."""
    title = stream.get("title", "").lower()

    quality_keywords = [
        ("2160p", "4K"),
        ("4k", "4K"),
        ("1080p", "1080p"),
        ("720p", "720p"),
        ("480p", "480p"),
    ]

    for keyword, label in quality_keywords:
        if keyword in title:
            return label

    # Check for HDR
    if "hdr" in title or "hdr10" in title or "dolby vision" in title:
        return "4K HDR"

    return "Unknown"


def _quality_rank(quality):
    """Rank quality for sorting."""
    ranks = {
        "4K HDR": 5,
        "4K": 4,
        "1080p": 3,
        "720p": 2,
        "480p": 1,
        "Unknown": 0,
    }
    return ranks.get(quality, 0)


def show_stream_selection(streams, title=""):
    """Show a dialog for the user to select a stream."""
    if not streams:
        xbmcgui.Dialog().notification(
            "StreamSyncr",
            "No streams available",
            xbmcgui.NOTIFICATION_WARNING,
            3000,
        )
        return None

    if len(streams) == 1:
        return streams[0]

    # Build selection list
    labels = []
    for s in streams:
        quality = s.get("quality", "?")
        service = s.get("name", "?")
        filename = s.get("title", "")
        label = f"[{quality}] {service} — {filename}"
        labels.append(label)

    dialog = xbmcgui.Dialog()
    idx = dialog.select(f"Select Stream ({len(streams)} available)", labels)

    if idx < 0:
        return None

    return streams[idx]


def play_resolved_stream(stream, title=""):
    """Play a resolved stream in Kodi."""
    url = stream.get("url", "")
    if not url:
        xbmcgui.Dialog().notification(
            "StreamSyncr",
            "Invalid stream URL",
            xbmcgui.NOTIFICATION_ERROR,
            3000,
        )
        return False

    li = xbmcgui.ListItem(label=title or stream.get("title", ""))
    li.setPath(url)

    # Set inputstream for adaptive streams
    if url.startswith("http") and not url.endswith((".mp4", ".mkv", ".avi")):
        li.setProperty("inputstream", "inputstream.adaptive")
        li.setProperty("inputstream.adaptive.manifest_type", "hls")

    # Set content type
    li.setMimeType("video/x-mpegURL")
    li.setContentLookup(False)

    import xbmcplugin
    import sys
    handle = int(sys.argv[1])
    xbmcplugin.setResolvedUrl(handle, True, li)

    return True