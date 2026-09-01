"""External HTTP plugin client — communicates with out-of-process plugins.

This enables third-party scrapers and debrid providers written in any language
(Rust, Go, Node.js, etc.) to participate in the StreamSyncr ecosystem.

Protocol:
  GET  /health              → {"status": "ok", "version": "1.0.0"}
  GET  /config              → {"schema": {...}}               (optional)
  POST /search              → {"results": [...]}              (scrapers)
  POST /resolve             → {"streams": [...]}              (debrid)
  POST /enrich              → {"metadata": {...}}             (metadata)
"""

import json
import logging
from urllib.request import Request, urlopen
from urllib.error import HTTPError, URLError

logger = logging.getLogger("streamsyncr.plugins.external")


class ExternalPluginClient:
    """HTTP client for communicating with external plugins."""

    def __init__(self, endpoint: str, timeout: int = 15):
        self.endpoint = endpoint.rstrip("/")
        self.timeout = timeout

    def _request(self, method: str, path: str, data: dict = None) -> dict | None:
        url = f"{self.endpoint}{path}"
        body = json.dumps(data).encode() if data else None
        req = Request(url, data=body, method=method)
        req.add_header("Content-Type", "application/json")
        req.add_header("User-Agent", "StreamSyncr/2.0")
        try:
            with urlopen(req, timeout=self.timeout) as resp:
                return json.loads(resp.read())
        except (HTTPError, URLError, TimeoutError) as e:
            logger.warning(f"External plugin {url} failed: {e}")
            return None

    def health(self) -> dict | None:
        return self._request("GET", "/health")

    def get_config(self) -> dict | None:
        return self._request("GET", "/config")

    def search(self, media_type: str, item_id: str, query: str = None,
               config: dict = None) -> list[dict]:
        payload = {"type": media_type, "id": item_id}
        if query:
            payload["query"] = query
        if config:
            payload["config"] = config
        result = self._request("POST", "/search", payload)
        if result and "results" in result:
            return result["results"]
        return []

    def resolve(self, media_type: str, item_id: str, config: dict = None) -> list[dict]:
        payload = {"type": media_type, "id": item_id}
        if config:
            payload["config"] = config
        result = self._request("POST", "/resolve", payload)
        if result and "streams" in result:
            return result["streams"]
        return []

    def enrich(self, item_id: str, media_type: str, config: dict = None) -> dict | None:
        payload = {"id": item_id, "type": media_type}
        if config:
            payload["config"] = config
        result = self._request("POST", "/enrich", payload)
        if result and "metadata" in result:
            return result["metadata"]
        return None


class ExternalScraperPlugin:
    """Wrapper that makes an external HTTP scraper look like a ScraperPlugin."""

    def __init__(self, name: str, endpoint: str, category: str = "external"):
        self.name = name
        self.category = category
        self.enabled = True
        self._client = ExternalPluginClient(endpoint)

    def health(self) -> dict:
        result = self._client.health()
        return result or {"status": "unreachable"}

    def search(self, media_type: str, item_id: str, config: dict,
               query: str = None, limit: int = 50) -> list:
        results = self._client.search(media_type, item_id, query, config)
        return results[:limit]


class ExternalDebridPlugin:
    """Wrapper that makes an external HTTP debrid provider look like a DebridPlugin."""

    def __init__(self, name: str, endpoint: str):
        self.name = name
        self._client = ExternalPluginClient(endpoint)

    def health(self) -> dict:
        result = self._client.health()
        return result or {"status": "unreachable"}

    def check_cached(self, api_key: str, hashes: list[str]) -> list[dict]:
        result = self._client._request("POST", "/check-cached",
                                       {"api_key": api_key, "hashes": hashes})
        return result.get("cached", []) if result else []

    def get_download_url(self, api_key: str, magnet: str, file_id: int | None = None) -> str:
        payload = {"api_key": api_key, "magnet": magnet}
        if file_id:
            payload["file_id"] = file_id
        result = self._client._request("POST", "/download-url", payload)
        return result.get("url", "") if result else ""

    def add_and_resolve(self, api_key: str, magnet: str) -> list:
        result = self._client._request("POST", "/add-and-resolve",
                                       {"api_key": api_key, "magnet": magnet})
        return result.get("streams", []) if result else []
