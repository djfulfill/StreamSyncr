import json
from typing import List, Dict, Optional
from urllib.request import Request, urlopen
from urllib.error import HTTPError
from urllib.parse import urlencode


class RealDebridClient:
    BASE = "https://api.real-debrid.com/rest/1.0"

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
            print(f"RealDebrid API error {e.code}: {error_body}")
            raise

    def get_torrents(self, query: str = None) -> List[Dict]:
        params = {}
        if query:
            params["search"] = query
        return self._request("GET", "/torrents", params=params)

    def add_torrent(self, torrent_id: str) -> Dict:
        return self._request("POST", f"/torrents/{torrent_id}")

    def select_files(self, torrent_id: str, files: str = "all") -> None:
        self._request("POST", f"/torrents/{torrent_id}/selectFiles", data={"files": files})

    def get_torrent_info(self, torrent_id: str) -> Dict:
        return self._request("GET", f"/torrents/{torrent_id}")

    def get_unrestricted_link(self, link: str) -> Dict:
        return self._request("GET", f"/unrestrict/link", params={"link": link})

    def resolve_imdb(self, imdb_id: str) -> List[Dict]:
        results = self.get_torrents(query=imdb_id)
        streams = []

        for torrent in results[:5]:
            status = torrent.get("status")
            if status == "downloaded":
                files = torrent.get("files", [])
                for f in files:
                    if f.get("selected") or f.get("path", "").lower().endswith((".mkv", ".mp4", ".avi")):
                        link = f.get("download")
                        if link:
                            try:
                                unrestricted = self.get_unrestricted_link(link)
                                streams.append({
                                    "name": "Real-Debrid",
                                    "title": f.get("path", "Unknown"),
                                    "url": unrestricted.get("download", ""),
                                    "duration": f.get("length", 0),
                                    "behaviorHints": {
                                        "bingeGroup": f"rd-{torrent.get('id', '')}",
                                    },
                                })
                            except Exception:
                                pass

        return streams
