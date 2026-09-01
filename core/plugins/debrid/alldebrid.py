"""AllDebrid provider plugin."""

import json
import time
from urllib.request import Request, urlopen
from urllib.error import HTTPError
from urllib.parse import urlencode

from core.plugins.base import Stream


class AllDebridProvider:
    """AllDebrid debrid service — cache check, add magnet, resolve to stream."""

    name = "alldebrid"
    BASE = "https://api.alldebrid.com/v4"

    def __init__(self):
        pass

    def _request(self, method: str, path: str, api_key: str,
                 data: dict = None, params: dict = None) -> dict:
        url = f"{self.BASE}{path}"
        all_params = {"agent": "streamsyncr"}
        if params:
            all_params.update(params)
        url += "?" + urlencode(all_params)
        body = json.dumps(data).encode() if data else None
        req = Request(url, data=body, method=method)
        req.add_header("Authorization", f"Bearer {api_key}")
        req.add_header("Content-Type", "application/json")
        try:
            with urlopen(req) as resp:
                return json.loads(resp.read())
        except HTTPError as e:
            raise Exception(f"AD API {e.code}: {e.read().decode()}")

    def check_cached(self, api_key: str, hashes: list[str]) -> list[dict]:
        params = {"hashes": ",".join(hashes)}
        result = self._request("GET", "/magnet/instantAvailability", api_key, params=params)
        data = result.get("data", result) if isinstance(result, dict) else result
        cached = []
        if isinstance(data, dict):
            for h in hashes:
                if h in data and data[h]:
                    cached.append({"hash": h})
        return cached

    def get_download_url(self, api_key: str, magnet: str, file_id: int | None = None) -> str:
        result = self._request("POST", "/magnet/upload", api_key, data={"magnet": magnet})
        data = result.get("data", result) if isinstance(result, dict) else result
        mid = data.get("id") if isinstance(data, dict) else None
        if not mid:
            return ""
        for _ in range(30):
            info = self._request("GET", f"/magnet/status/{mid}", api_key)
            info_data = info.get("data", info) if isinstance(info, dict) else info
            status = info_data.get("status", "") if isinstance(info_data, dict) else ""
            if status == "downloaded":
                break
            if status in ("error", "dead"):
                return ""
            time.sleep(1)
        files = info_data.get("files", []) if isinstance(info_data, dict) else []
        for f in files:
            if f.get("name", "").lower().endswith((".mkv", ".mp4", ".avi")):
                link = f.get("link", "")
                if link:
                    unlock = self._request("GET", f"/link/unlock/{link}", api_key)
                    unlock_data = unlock.get("data", unlock) if isinstance(unlock, dict) else unlock
                    return unlock_data.get("link", "") if isinstance(unlock_data, dict) else ""
        return ""

    def add_and_resolve(self, api_key: str, magnet: str) -> list[Stream]:
        result = self._request("POST", "/magnet/upload", api_key, data={"magnet": magnet})
        data = result.get("data", result) if isinstance(result, dict) else result
        mid = data.get("id") if isinstance(data, dict) else None
        if not mid:
            return []
        for _ in range(30):
            info = self._request("GET", f"/magnet/status/{mid}", api_key)
            info_data = info.get("data", info) if isinstance(info, dict) else info
            status = info_data.get("status", "") if isinstance(info_data, dict) else ""
            if status == "downloaded":
                break
            if status in ("error", "dead"):
                return []
            time.sleep(1)
        streams = []
        files = info_data.get("files", []) if isinstance(info_data, dict) else []
        for f in files:
            name = f.get("name", "")
            if name.lower().endswith((".mkv", ".mp4", ".avi")):
                link = f.get("link", "")
                if link:
                    try:
                        unlock = self._request("GET", f"/link/unlock/{link}", api_key)
                        unlock_data = unlock.get("data", unlock) if isinstance(unlock, dict) else unlock
                        url = unlock_data.get("link", "") if isinstance(unlock_data, dict) else ""
                        if url:
                            streams.append(Stream(
                                name="AllDebrid",
                                title=name,
                                url=url,
                            ))
                    except Exception:
                        pass
        return streams
