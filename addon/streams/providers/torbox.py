import json
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
        return self._request("GET", "/api/torrents/mylist")

    def get_torrent_info(self, torrent_id: int) -> Dict:
        return self._request("GET", f"/api/torrents/details/{torrent_id}")

    def get_download_link(self, torrent_id: int, file_id: int = None) -> str:
        params = {}
        if file_id:
            params["file_id"] = file_id
        result = self._request("GET", f"/api/torrents/{torrent_id}/download", params=params)
        return result.get("data", "")

    def resolve_imdb(self, imdb_id: str) -> List[Dict]:
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
