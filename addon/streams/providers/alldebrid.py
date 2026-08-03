import json
from typing import List, Dict
from urllib.request import Request, urlopen
from urllib.error import HTTPError
from urllib.parse import urlencode


class AllDebridClient:
    BASE = "https://api.alldebrid.com/v4"

    def __init__(self, api_key: str):
        self.api_key = api_key

    def _request(self, method: str, path: str, data: dict = None, params: dict = None) -> dict:
        url = f"{self.BASE}{path}"
        all_params = {"agent": "streamsyncr"}
        if params:
            all_params.update(params)
        url += "?" + urlencode(all_params)

        body = json.dumps(data).encode() if data else None
        req = Request(url, data=body, method=method)
        req.add_header("Authorization", f"Bearer {self.api_key}")
        req.add_header("Content-Type", "application/json")

        try:
            with urlopen(req) as resp:
                return json.loads(resp.read())
        except HTTPError as e:
            error_body = e.read().decode()
            print(f"AllDebrid API error {e.code}: {error_body}")
            raise

    def get_magnets(self) -> List[Dict]:
        return self._request("GET", "/magnet/status")

    def add_magnet(self, magnet: str) -> Dict:
        return self._request("POST", "/magnet/upload", data={"magnet": magnet})

    def get_magnet_status(self, magnet_id: str) -> Dict:
        return self._request("GET", f"/magnet/status/{magnet_id}")

    def get_link(self, link: str) -> Dict:
        return self._request("GET", f"/link/unlock/{link}")

    def resolve_imdb(self, imdb_id: str) -> List[Dict]:
        magnets = self.get_magnets()
        streams = []

        for magnet in magnets.get("data", []):
            name = magnet.get("filename", "")
            if imdb_id in name:
                files = magnet.get("files", [])
                for f in files:
                    if f.get("name", "").lower().endswith((".mkv", ".mp4", ".avi")):
                        try:
                            link_data = self.get_link(f.get("link", ""))
                            download_url = link_data.get("data", {}).get("link", "")
                            if download_url:
                                streams.append({
                                    "name": "AllDebrid",
                                    "title": f.get("name", "Unknown"),
                                    "url": download_url,
                                    "behaviorHints": {
                                        "bingeGroup": f"alldebrid-{magnet.get('id', '')}",
                                    },
                                })
                        except Exception:
                            pass

        return streams
