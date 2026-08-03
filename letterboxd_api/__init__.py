"""Letterboxd API client (undocumented internal API)."""

import json
from urllib.request import Request, urlopen
from urllib.parse import urlencode
from typing import Dict, List, Optional


class LetterboxdClient:
    BASE = "https://letterboxd.com"

    def __init__(self, cookies: str, csrf_token: str):
        self.cookies = cookies
        self.csrf_token = csrf_token
        self.headers = {
            "accept": "*/*",
            "accept-language": "en-US,en;q=0.6",
            "content-type": "application/json; charset=UTF-8",
            "origin": self.BASE,
            "referer": f"{self.BASE}/films/",
            "sec-ch-ua": '"Not=A?Brand";v="99", "Brave";v="151", "Chromium";v="151"',
            "sec-ch-ua-mobile": "?0",
            "sec-ch-ua-platform": '"Linux"',
            "sec-fetch-dest": "empty",
            "sec-fetch-mode": "cors",
            "sec-fetch-site": "same-origin",
            "sec-gpc": "1",
            "user-agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/151.0.0.0 Safari/537.36",
            "x-csrf-token": self.csrf_token,
            "x-requested-with": "XMLHttpRequest",
        }

    def _request(self, method: str, path: str, data: dict = None, params: dict = None) -> dict:
        url = f"{self.BASE}{path}"
        if params:
            url += "?" + urlencode(params)

        body = json.dumps(data).encode() if data else None
        req = Request(url, data=body, method=method)
        for k, v in self.headers.items():
            req.add_header(k, v)
        req.add_header("cookie", self.cookies)

        with urlopen(req) as resp:
            return json.loads(resp.read())

    def search_film(self, query: str) -> List[Dict]:
        """Search for a film by name. Returns list of matches with `lid` codes."""
        import time
        result = self._request("GET", "/s/autocompletefilm", params={
            "q": query,
            "limit": 10,
            "timestamp": int(time.time() * 1000),
            "adult": "false",
        })
        return result.get("data", [])

    def get_film_code(self, query: str) -> Optional[str]:
        """Get the Letterboxd ID (`lid`) for a film."""
        films = self.search_film(query)
        if films:
            return films[0].get("lid")
        return None

    def create_list(
        self,
        name: str,
        description: str = "",
        film_lids: List[str] = None,
        share_policy: str = "You",
        ranked: bool = False,
    ) -> Dict:
        """Create a new list. Returns list ID."""
        entries = [{"film": lid} for lid in (film_lids or [])]
        data = {
            "published": True,
            "name": name,
            "sharePolicy": share_policy,
            "ranked": ranked,
            "description": description,
            "tags": [],
            "entries": entries,
        }
        return self._request("POST", "/api/v0/lists", data=data)

    def add_to_list(self, list_id: str, film_lids: List[str]) -> Dict:
        """Add films to an existing list."""
        return self._request("PATCH", "/api/v0/lists", data={
            "lists": [list_id],
            "listables": film_lids,
        })

    def remove_from_list(self, list_id: str, film_lids: List[str]) -> Dict:
        """Remove films from a list."""
        return self._request("DELETE", "/api/v0/lists", data={
            "lists": [list_id],
            "listables": film_lids,
        })

    def mark_watched(self, film_lid: str) -> Dict:
        """Mark a film as watched (add to diary)."""
        return self._request("POST", f"/ajax/film:{film_lid}/filmlistentry", data={
            "rating": 0,
            "like": False,
        })

    def add_to_watchlist(self, film_lid: str) -> Dict:
        """Add a film to watchlist."""
        return self._request("POST", f"/ajax/film:{film_lid}/watchlist")
