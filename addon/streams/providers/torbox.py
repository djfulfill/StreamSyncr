import json
import time
from typing import List, Dict
from urllib.request import Request, urlopen
from urllib.error import HTTPError
from urllib.parse import urlencode


class TorBoxClient:
    BASE = "https://api.torbox.app/v1"

    def __init__(self, api_key: str):
        self.api_key = api_key

    def _request(self, method: str, path: str, data: dict = None, params: dict = None) -> dict:
        url = f"{self.BASE}{path}"
        if params:
            url += "?" + urlencode(params)

        body = json.dumps(data).encode() if data else None
        req = Request(url, data=body, method=method)
        req.add_header("Authorization", f"Bearer {self.api_key}")
        req.add_header("Content-Type", "application/json")
        req.add_header("User-Agent", "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36")
        req.add_header("Accept", "application/json")

        try:
            with urlopen(req) as resp:
                return json.loads(resp.read())
        except HTTPError as e:
            error_body = e.read().decode()
            print(f"TorBox API error {e.code}: {error_body}")
            raise

    def create_torrent(self, magnet: str) -> Dict:
        return self._request("POST", "/api/torrents/createurl", data={"url": magnet})

    def get_torrents(self) -> List[Dict]:
        result = self._request("GET", "/api/torrents/mylist")
        if isinstance(result, dict) and "data" in result:
            return result["data"]
        if isinstance(result, list):
            return result
        return []

    def get_torrent_info(self, torrent_id: int) -> Dict:
        result = self._request("GET", f"/api/torrents/torrentinfo", params={"id": torrent_id})
        if isinstance(result, dict) and "data" in result:
            return result["data"]
        return result

    def get_download_link(self, torrent_id: int, file_id: int = None) -> str:
        params = {"id": torrent_id}
        if file_id:
            params["file_id"] = file_id
        result = self._request("GET", "/api/torrents/requestdl", params=params)
        if isinstance(result, dict) and "data" in result:
            return result["data"]
        return result.get("data", "")

    def add_magnet(self, magnet: str) -> Dict:
        """Add a magnet and return the torrent info."""
        result = self.create_torrent(magnet)
        if isinstance(result, dict) and "data" in result:
            return result["data"]
        return result

    def wait_for_torrent(self, torrent_id: int, max_wait: int = 30) -> Dict:
        """Wait for a torrent to be ready."""
        for _ in range(max_wait):
            info = self.get_torrent_info(torrent_id)
            status = info.get("status", "")
            if status in ("downloaded", "ready"):
                return info
            if status in ("error", "dead", "magnet_error"):
                raise Exception(f"Torrent failed: {status}")
            time.sleep(1)
        raise Exception("Torrent download timed out")

    def resolve_imdb(self, imdb_id: str) -> List[Dict]:
        """Resolve an IMDB ID by checking existing torrents."""
        torrents = self.get_torrents()
        streams = []

        for torrent in torrents:
            name = torrent.get("name", "")
            if imdb_id in name or imdb_id in str(torrent.get("hash", "")):
                files = torrent.get("files", [])
                for f in files:
                    if f.get("short_name", "").lower().endswith((".mkv", ".mp4", ".avi")):
                        try:
                            link = self.get_download_link(torrent["id"], f["id"])
                            if link:
                                streams.append({
                                    "name": "TorBox",
                                    "title": f.get("short_name", "Unknown"),
                                    "url": link,
                                    "behaviorHints": {
                                        "bingeGroup": f"torbox-{torrent.get('id', '')}",
                                    },
                                })
                        except Exception:
                            pass

        return streams

    def add_and_resolve(self, magnet: str) -> List[Dict]:
        """Add a magnet and resolve to streaming links."""
        try:
            result = self.add_magnet(magnet)
            torrent_id = result.get("id") if isinstance(result, dict) else None
            if not torrent_id:
                return []

            info = self.wait_for_torrent(torrent_id, max_wait=30)
            streams = []

            for f in info.get("files", []):
                name = f.get("short_name", "") or f.get("name", "")
                if name.lower().endswith((".mkv", ".mp4", ".avi")):
                    try:
                        link = self.get_download_link(torrent_id, f["id"])
                        if link:
                            streams.append({
                                "name": "TorBox",
                                "title": name,
                                "url": link,
                                "behaviorHints": {
                                    "bingeGroup": f"torbox-{torrent_id}",
                                },
                            })
                    except Exception:
                        pass

            return streams
        except Exception as e:
            print(f"[TorBox] add_and_resolve error: {e}")
            return []
