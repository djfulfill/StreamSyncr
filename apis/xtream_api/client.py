"""
Xtream Codes API Client

Full-featured client for Xtream Codes compatible IPTV providers.
Requires only a server URL, username, and password.

Usage:
    from xtream_api import XtreamClient

    x = XtreamClient("http://provider.com:8080", "user", "pass")
    print(x.auth())
    print(x.live_categories())
    print(x.live_streams())
    print(x.vod_categories())
    print(x.vod_streams())
    print(x.series_categories())
    print(x.series())
"""

import json
import sys
from typing import List, Dict, Optional
from urllib.request import Request, urlopen
from urllib.error import HTTPError
from urllib.parse import urlencode


class XtreamClient:
    """Xtream Codes IPTV API client."""

    def __init__(self, url: str, username: str, password: str):
        self.url = url.rstrip("/")
        self.username = username
        self.password = password
        self._user_info = None
        self._server_info = None

    def _request(self, params: dict = None) -> dict:
        query = {"username": self.username, "password": self.password}
        if params:
            query.update(params)
        url = f"{self.url}/player_api.php?{urlencode(query)}"

        req = Request(url)
        req.add_header("Accept", "application/json")
        req.add_header("User-Agent", "StreamSyncr/1.0")

        try:
            with urlopen(req, timeout=15) as resp:
                return json.loads(resp.read())
        except HTTPError as e:
            error_body = e.read().decode()
            print(f"Xtream API error {e.code}: {error_body}", file=sys.stderr)
            raise
        except Exception as e:
            print(f"Xtream connection error: {e}", file=sys.stderr)
            raise

    def _get_streams(self, action: str, category_id: int = None) -> List[Dict]:
        params = {"action": action}
        if category_id:
            params["category_id"] = category_id
        data = self._request(params)
        return data if isinstance(data, list) else data.get("data", [])

    # ── Authentication & Account ──────────────────────────────

    def auth(self) -> Dict:
        """Authenticate and get user/server info. Caches result."""
        if self._user_info is None:
            data = self._request()
            self._user_info = data.get("user_info", {})
            self._server_info = data.get("server_info", {})
        return {
            "user_info": self._user_info,
            "server_info": self._server_info,
        }

    def user_info(self) -> Dict:
        """Get user account info (status, expiry, connections)."""
        if self._user_info is None:
            self.auth()
        return self._user_info

    def server_info(self) -> Dict:
        """Get server info (URL, ports, timezone)."""
        if self._server_info is None:
            self.auth()
        return self._server_info

    def is_active(self) -> bool:
        """Check if account is active and not expired."""
        info = self.user_info()
        return info.get("auth") == 1 and info.get("status") == "Active"

    # ── Live TV ───────────────────────────────────────────────

    def live_categories(self) -> List[Dict]:
        """Get all live TV categories."""
        data = self._request({"action": "get_live_categories"})
        return data if isinstance(data, list) else data.get("data", [])

    def live_streams(self, category_id: int = None) -> List[Dict]:
        """Get live streams, optionally filtered by category."""
        return self._get_streams("get_live_streams", category_id)

    def live_stream_url(self, stream_id: int) -> str:
        """Get the stream URL for a live channel."""
        return f"{self.url}/live/{self.username}/{self.password}/{stream_id}"

    # ── VOD (Movies) ──────────────────────────────────────────

    def vod_categories(self) -> List[Dict]:
        """Get all VOD/movie categories."""
        data = self._request({"action": "get_vod_categories"})
        return data if isinstance(data, list) else data.get("data", [])

    def vod_streams(self, category_id: int = None) -> List[Dict]:
        """Get VOD streams, optionally filtered by category."""
        return self._get_streams("get_vod_streams", category_id)

    def vod_info(self, vod_id: int) -> Dict:
        """Get detailed info for a VOD item (streams, metadata, backdrop)."""
        data = self._request({"action": "get_vod_info", "vod_id": vod_id})
        return data if isinstance(data, dict) else {}

    def vod_stream_url(self, stream_id: int) -> str:
        """Get the stream URL for a VOD movie."""
        return f"{self.url}/movie/{self.username}/{self.password}/{stream_id}"

    # ── Series ────────────────────────────────────────────────

    def series_categories(self) -> List[Dict]:
        """Get all series categories."""
        data = self._request({"action": "get_series_categories"})
        return data if isinstance(data, list) else data.get("data", [])

    def series(self, category_id: int = None) -> List[Dict]:
        """Get all series, optionally filtered by category."""
        return self._get_streams("get_series", category_id)

    def series_info(self, series_id: int) -> Dict:
        """Get detailed info for a series (seasons, episodes, info)."""
        data = self._request({"action": "get_series_info", "series_id": series_id})
        return data if isinstance(data, dict) else {}

    def series_stream_url(self, stream_id: int) -> str:
        """Get the stream URL for a series episode."""
        return f"{self.url}/movie/{self.username}/{self.password}/{stream_id}"

    # ── EPG (Electronic Program Guide) ────────────────────────

    def short_epg(self, stream_id: int, limit: int = 24) -> Dict:
        """Get short EPG for a specific live stream."""
        data = self._request({
            "action": "get_short_epg",
            "stream_id": stream_id,
            "limit": limit,
        })
        return data if isinstance(data, dict) else {}

    def full_epg(self, stream_id: int) -> Dict:
        """Get full EPG data table for a live stream."""
        data = self._request({
            "action": "get_simple_data_table",
            "stream_id": stream_id,
        })
        return data if isinstance(data, dict) else {}

    def xmltv_url(self) -> str:
        """Get the XMLTV EPG URL for use in external players."""
        return f"{self.url}/xmltv.php?username={self.username}&password={self.password}"

    # ── Search ────────────────────────────────────────────────

    def search(self, query: str, search_type: str = "live") -> List[Dict]:
        """Search across live, vod, or series. Type: live, vod, series."""
        data = self._request({
            "action": "search",
            "type": search_type,
            "query": query,
        })
        return data if isinstance(data, list) else data.get("data", [])

    # ── M3U Playlist ──────────────────────────────────────────

    def m3u_url(self, output: str = "ts") -> str:
        """Get M3U playlist URL. Output: ts, m3u8."""
        return f"{self.url}/get.php?username={self.username}&password={self.password}&type=m3u_plus&output={output}"

    # ── Stream URL Helpers ────────────────────────────────────

    def stream_url(self, stream_id: int, stream_type: str = "live") -> str:
        """Get stream URL by type. Type: live, movie."""
        return f"{self.url}/{stream_type}/{self.username}/{self.password}/{stream_id}"

    def timeshift_url(self, stream_id: int, duration: int, start: str) -> str:
        """Get timeshift/catchup URL."""
        return f"{self.url}/timeshift/{self.username}/{self.password}/{duration}/{start}/{stream_id}"

    # ── Connection Info ───────────────────────────────────────

    def connections(self) -> Dict:
        """Get connection info (active, max, allowed formats)."""
        info = self.user_info()
        return {
            "active": int(info.get("active_cons", 0)),
            "max": int(info.get("max_connections", 0)),
            "formats": info.get("allowed_output_formats", []),
        }

    def expiry(self) -> Optional[str]:
        """Get account expiry as human-readable date."""
        import datetime
        info = self.user_info()
        exp = info.get("exp_date")
        if exp:
            try:
                ts = int(exp)
                return datetime.datetime.fromtimestamp(ts).isoformat()
            except (ValueError, TypeError):
                pass
        return None
