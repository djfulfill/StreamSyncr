"""TorBox provider plugin."""

import json
import time
from urllib.request import Request, urlopen
from urllib.error import HTTPError
from urllib.parse import urlencode

from core.plugins.base import Stream


class TorBoxProvider:
    """TorBox debrid service — cache check, add magnet, resolve to stream."""

    name = "torbox"
    BASE = "https://api.torbox.app/v1"

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
        req.add_header("User-Agent", "StreamSyncr/2.0")
        try:
            with urlopen(req) as resp:
                return json.loads(resp.read())
        except HTTPError as e:
            raise Exception(f"TorBox API {e.code}: {e.read().decode()}")

    def check_cached(self, api_key: str, hashes: list[str]) -> list[dict]:
        params = {"hashes": ",".join(hashes)}
        result = self._request("GET", "/api/torrents/checkcache", api_key, params=params)
        data = result.get("data", result) if isinstance(result, dict) else result
        cached = []
        if isinstance(data, dict):
            for h in hashes:
                if h in data and data[h]:
                    cached.append({"hash": h})
        return cached

    def get_download_url(self, api_key: str, magnet: str, file_id: int | None = None) -> str:
        result = self._request("POST", "/api/torrents/createurl", api_key, data={"url": magnet})
        data = result.get("data", result) if isinstance(result, dict) else result
        tid = data if isinstance(data, int) else data.get("id") if isinstance(data, dict) else None
        if not tid:
            return ""
        for _ in range(30):
            info = self._request("GET", "/api/torrents/torrentinfo", api_key, params={"id": tid})
            info_data = info.get("data", info) if isinstance(info, dict) else info
            status = info_data.get("status", "") if isinstance(info_data, dict) else ""
            if status in ("downloaded", "ready"):
                break
            if status in ("error", "dead"):
                return ""
            time.sleep(1)
        params = {"id": tid}
        if file_id:
            params["file_id"] = file_id
        dl = self._request("GET", "/api/torrents/requestdl", api_key, params=params)
        return dl.get("data", "") if isinstance(dl, dict) else str(dl)

    def add_and_resolve(self, api_key: str, magnet: str) -> list[Stream]:
        result = self._request("POST", "/api/torrents/createurl", api_key, data={"url": magnet})
        data = result.get("data", result) if isinstance(result, dict) else result
        tid = data if isinstance(data, int) else data.get("id") if isinstance(data, dict) else None
        if not tid:
            return []
        for _ in range(30):
            info = self._request("GET", "/api/torrents/torrentinfo", api_key, params={"id": tid})
            info_data = info.get("data", info) if isinstance(info, dict) else info
            status = info_data.get("status", "") if isinstance(info_data, dict) else ""
            if status in ("downloaded", "ready"):
                break
            if status in ("error", "dead"):
                return []
            time.sleep(1)
        streams = []
        files = info_data.get("files", []) if isinstance(info_data, dict) else []
        for f in files:
            name = f.get("name", "")
            if name.lower().endswith((".mkv", ".mp4", ".avi")):
                fid = f.get("id")
                dl = self._request("GET", "/api/torrents/requestdl", api_key,
                                   params={"id": tid, "file_id": fid})
                url = dl.get("data", "") if isinstance(dl, dict) else str(dl)
                if url:
                    streams.append(Stream(
                        name="TorBox",
                        title=name,
                        url=url,
                    ))
        return streams
