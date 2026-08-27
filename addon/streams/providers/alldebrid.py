import json
import time
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
        result = self._request("GET", "/magnet/status")
        if isinstance(result, dict) and "data" in result:
            return result["data"]
        return result if isinstance(result, list) else []

    def add_magnet(self, magnet: str) -> Dict:
        return self._request("POST", "/magnet/upload", data={"magnet": magnet})

    def get_magnet_status(self, magnet_id: str) -> Dict:
        return self._request("GET", f"/magnet/status/{magnet_id}")

    def get_link(self, link: str) -> Dict:
        return self._request("GET", f"/link/unlock/{link}")

    def wait_for_magnet(self, magnet_id: str, max_wait: int = 30) -> Dict:
        """Wait for a magnet to be ready."""
        for _ in range(max_wait):
            info = self.get_magnet_status(magnet_id)
            status = info.get("status", "")
            if status == "downloaded":
                return info
            if status in ("error", "dead"):
                raise Exception(f"Magnet failed: {status}")
            time.sleep(1)
        raise Exception("Magnet download timed out")

    def resolve_imdb(self, imdb_id: str) -> List[Dict]:
        """Resolve an IMDB ID by checking existing magnets."""
        magnets = self.get_magnets()
        streams = []

        for magnet in magnets:
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

    def add_and_resolve(self, magnet: str) -> List[Dict]:
        """Add a magnet and resolve to streaming links."""
        try:
            result = self.add_magnet(magnet)
            magnet_id = result.get("id") if isinstance(result, dict) else None
            if not magnet_id:
                return []

            info = self.wait_for_magnet(magnet_id, max_wait=30)
            streams = []

            for f in info.get("files", []):
                name = f.get("name", "")
                if name.lower().endswith((".mkv", ".mp4", ".avi")):
                    try:
                        link_data = self.get_link(f.get("link", ""))
                        download_url = link_data.get("data", {}).get("link", "")
                        if download_url:
                            streams.append({
                                "name": "AllDebrid",
                                "title": name,
                                "url": download_url,
                                "behaviorHints": {
                                    "bingeGroup": f"alldebrid-{magnet_id}",
                                },
                            })
                    except Exception:
                        pass

            return streams
        except Exception as e:
            print(f"[AllDebrid] add_and_resolve error: {e}")
            return []
