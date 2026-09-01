"""Real-Debrid provider plugin."""

import json
import time
from urllib.request import Request, urlopen
from urllib.error import HTTPError
from urllib.parse import urlencode

from core.plugins.base import Stream


class RealDebridProvider:
    """Real-Debrid debrid service — cache check, add magnet, resolve to stream."""

    name = "realdebrid"
    BASE = "https://api.real-debrid.com/rest/1.0"

    def __init__(self):
        pass

    def _request(self, method: str, path: str, api_key: str,
                 data: dict = None, params: dict = None) -> dict:
        url = f"{self.BASE}{path}"
        if params:
            url += "?" + urlencode(params)
        body = json.dumps(data).encode() if data else None
        req = Request(url, data=body, method=method)
        req.add_header("Authorization", f"Bearer {api_key}")
        req.add_header("Content-Type", "application/json")
        try:
            with urlopen(req) as resp:
                return json.loads(resp.read())
        except HTTPError as e:
            raise Exception(f"RD API {e.code}: {e.read().decode()}")

    def check_cached(self, api_key: str, hashes: list[str]) -> list[dict]:
        params = {"hashes": ",".join(hashes)}
        result = self._request("GET", "/torrents/instantAvailability", api_key, params=params)
        cached = []
        for hash_val, variants in result.items():
            if variants:
                cached.append({"hash": hash_val, "variant": list(variants.keys())[0]})
        return cached

    def get_download_url(self, api_key: str, magnet: str, file_id: int | None = None) -> str:
        torrent = self._request("POST", "/torrents/addMagnet", api_key, data={"magnet": magnet})
        tid = torrent.get("id")
        if not tid:
            return ""
        self._request("POST", f"/torrents/{tid}/selectFiles", api_key, data={"files": "all"})
        for _ in range(30):
            info = self._request("GET", f"/torrents/{tid}", api_key)
            if info.get("status") == "downloaded":
                break
            if info.get("status") in ("error", "dead"):
                return ""
            time.sleep(1)
        files = info.get("files", [])
        for f in files:
            if f.get("selected") or f.get("path", "").lower().endswith((".mkv", ".mp4", ".avi")):
                link = f.get("download")
                if link:
                    unrestricted = self._request("GET", "/unrestrict/link", api_key, params={"link": link})
                    return unrestricted.get("download", "")
        return ""

    def add_and_resolve(self, api_key: str, magnet: str) -> list[Stream]:
        torrent = self._request("POST", "/torrents/addMagnet", api_key, data={"magnet": magnet})
        tid = torrent.get("id")
        if not tid:
            return []
        self._request("POST", f"/torrents/{tid}/selectFiles", api_key, data={"files": "all"})
        for _ in range(30):
            info = self._request("GET", f"/torrents/{tid}", api_key)
            if info.get("status") == "downloaded":
                break
            if info.get("status") in ("error", "dead"):
                return []
            time.sleep(1)
        streams = []
        for f in info.get("files", []):
            if f.get("selected") or f.get("path", "").lower().endswith((".mkv", ".mp4", ".avi")):
                link = f.get("download")
                if link:
                    try:
                        unrestricted = self._request("GET", "/unrestrict/link", api_key, params={"link": link})
                        url = unrestricted.get("download", "")
                        if url:
                            streams.append(Stream(
                                name="Real-Debrid",
                                title=f.get("path", "Unknown"),
                                url=url,
                                duration=f.get("length", 0),
                            ))
                    except Exception:
                        pass
        return streams
