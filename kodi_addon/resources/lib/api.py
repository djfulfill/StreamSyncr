"""
StreamSyncr API client for Kodi addon.

Communicates with the StreamSyncr backend (FastAPI on port 7800)
to fetch catalogs, resolve streams, and sync watch history.
"""

import json
import xbmcgui
import xbmcaddon

try:
    import requests
except ImportError:
    # Kodi's built-in requests fallback
    import urllib.request
    import urllib.error

    class _RequestsFallback:
        """Minimal requests-like wrapper using urllib."""

        class Response:
            def __init__(self, data, status_code):
                self._data = data
                self.status_code = status_code

            def json(self):
                return json.loads(self._data)

            @property
            def text(self):
                return self._data

        @classmethod
        def get(cls, url, timeout=10, **kwargs):
            try:
                req = urllib.request.Request(url, headers=kwargs.get("headers", {}))
                with urllib.request.urlopen(req, timeout=timeout) as resp:
                    data = resp.read().decode()
                    return cls.Response(data, resp.status)
            except urllib.error.HTTPError as e:
                return cls.Response("", e.code)
            except Exception:
                return cls.Response("", 0)

        @classmethod
        def post(cls, url, json=None, timeout=10, **kwargs):
            try:
                headers = kwargs.get("headers", {})
                headers["Content-Type"] = "application/json"
                data = json.dumps(json).encode() if json else None
                req = urllib.request.Request(url, data=data, headers=headers, method="POST")
                with urllib.request.urlopen(req, timeout=timeout) as resp:
                    data = resp.read().decode()
                    return cls.Response(data, resp.status)
            except urllib.error.HTTPError as e:
                return cls.Response("", e.code)
            except Exception:
                return cls.Response("", 0)

    requests = _RequestsFallback()


class StreamSyncrAPI:
    """Client for the StreamSyncr backend API."""

    def __init__(self, backend_url="http://localhost:7800", config_token=""):
        self.base_url = backend_url.rstrip("/")
        self.config_token = config_token
        self.timeout = 10

    def _url(self, path):
        """Build a full URL, prepending config token if available."""
        if self.config_token:
            return f"{self.base_url}/{self.config_token}{path}"
        return f"{self.base_url}{path}"

    def ping(self):
        """Check if the backend is reachable."""
        try:
            resp = requests.get(f"{self.base_url}/manifest.json", timeout=self.timeout)
            return resp.status_code == 200
        except Exception:
            return False

    def get_manifest(self):
        """Get the addon manifest from the backend."""
        try:
            resp = requests.get(self._url("/manifest.json"), timeout=self.timeout)
            if resp.status_code == 200:
                return resp.json()
        except Exception:
            pass
        return {}

    def get_catalogs(self):
        """Get list of available catalogs from the manifest."""
        manifest = self.get_manifest()
        return manifest.get("catalogs", [])

    def get_catalog(self, catalog_type, catalog_id, skip=0, genre=None, sort=None, search=None):
        """Fetch items from a specific catalog."""
        path = f"/catalog/{catalog_type}/{catalog_id}.json"
        params = []
        if skip:
            params.append(f"skip={skip}")
        if genre:
            params.append(f"genre={genre}")
        if sort:
            params.append(f"sort={sort}")
        if search:
            params.append(f"search={urllib.parse.quote(search)}")
        if params:
            path += "?" + "&".join(params)

        try:
            resp = requests.get(self._url(path), timeout=self.timeout)
            if resp.status_code == 200:
                data = resp.json()
                return data.get("metas", [])
        except Exception:
            pass
        return []

    def get_meta(self, meta_type, meta_id):
        """Get detailed metadata for an item."""
        path = f"/meta/{meta_type}/{meta_id}.json"
        try:
            resp = requests.get(self._url(path), timeout=self.timeout)
            if resp.status_code == 200:
                data = resp.json()
                return data.get("meta", {})
        except Exception:
            pass
        return {}

    def resolve_streams(self, stream_type="movie", stream_id=""):
        """Resolve playable streams for an item."""
        path = f"/stream/{stream_type}/{stream_id}.json"
        try:
            resp = requests.get(self._url(path), timeout=self.timeout)
            if resp.status_code == 200:
                data = resp.json()
                return data.get("streams", [])
        except Exception:
            pass
        return []

    def search(self, query, catalog_type="movie"):
        """Search for content."""
        # Use TMDB search via catalog with search parameter
        results = []
        for cat_id in ["tmdb-trending", "tmdb-popular"]:
            items = self.get_catalog(catalog_type, cat_id, search=query)
            results.extend(items)
        return results[:20]

    def scrobble(self, imdb_id, progress=100):
        """Report watch progress to the backend."""
        try:
            resp = requests.post(
                f"{self.base_url}/api/scrobble",
                json={"imdb_id": imdb_id, "progress": progress},
                timeout=self.timeout,
            )
            return resp.status_code == 200
        except Exception:
            return False

    def get_debrid_status(self):
        """Check which debrid services are configured."""
        manifest = self.get_manifest()
        streams = manifest.get("resources", [])
        return {
            "realdebrid": any("realdebrid" in str(s).lower() for s in streams),
            "torbox": any("torbox" in str(s).lower() for s in streams),
            "alldebrid": any("alldebrid" in str(s).lower() for s in streams),
        }