"""
IMDb API Client

Full-featured client for IMDb's GraphQL API.
Supports reading and writing lists, ratings, and watchlist.

Usage:
    from imdb_api import IMDbClient

    client = IMDbClient(session_id="...", at_main="...", session_token="...")
    
    # Get lists
    lists = client.get_lists()
    
    # Create list
    new_list = client.create_list("My New List", "Description", "PUBLIC")
    
    # Add item to list
    client.add_to_list(new_list["id"], "tt0467200", "title")
    
    # Rate a title
    client.rate_title("tt0467200", 8)
    
    # Get ratings
    ratings = client.get_ratings(["tt0467200", "tt9244578"])
"""

import json
import os
from typing import List, Dict, Optional
from urllib.request import Request, urlopen
from urllib.error import HTTPError
from urllib.parse import urlencode

from .operations import OPERATIONS, QUERIES

BASE_URL = "https://api.graphql.imdb.com"

# Required headers for IMDb API
DEFAULT_HEADERS = {
    "accept": "application/graphql+json, application/json",
    "accept-language": "en-US,en;q=0.8",
    "content-type": "application/json",
    "dnt": "1",
    "origin": "https://www.imdb.com",
    "referer": "https://www.imdb.com/",
    "sec-ch-ua": '"Not=A?Brand";v="99", "Brave";v="151", "Chromium";v="151"',
    "sec-ch-ua-mobile": "?0",
    "sec-ch-ua-platform": '"Linux"',
    "sec-fetch-dest": "empty",
    "sec-fetch-mode": "cors",
    "sec-fetch-site": "same-site",
    "sec-gpc": "1",
    "user-agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/151.0.0.0 Safari/537.36",
    "x-amzn-sessionid": "",
    "x-imdb-client-name": "imdb-web-next-localized",
    "x-imdb-client-rid": "YRP5V4Z60F0FQ1H5TCJZ",
    "x-imdb-consent-info": "eyJhZ2VTaWduYWwiOiJBRFVMVCIsImRpc2FibGVDQ0JBIjpmYWxzZSwiaXNHZHByIjpmYWxzZX0",
    "x-imdb-user-country": "US",
    "x-imdb-user-language": "en-US",
    "x-imdb-weblab-treatment-overrides": "",
}


class IMDbClient:
    """Full IMDb GraphQL API client."""

    def __init__(
        self,
        session_id: str = None,
        at_main: str = None,
        session_token: str = None,
        ubid_main: str = None,
        sess_at_main: str = None,
        x_main: str = None,
        aws_waf_token: str = None,
        full_cookies: str = None,
    ):
        self.session_id = session_id or os.environ.get("IMDB_SESSION_ID")
        self.at_main = at_main or os.environ.get("IMDB_AT_MAIN")
        self.session_token = session_token or os.environ.get("IMDB_SESSION_TOKEN")
        self.ubid_main = ubid_main or os.environ.get("IMDB_UBID_MAIN")
        self.sess_at_main = sess_at_main or os.environ.get("IMDB_SESS_AT_MAIN")
        self.x_main = x_main or os.environ.get("IMDB_X_MAIN")
        self.aws_waf_token = aws_waf_token or os.environ.get("IMDB_AWS_WAF_TOKEN")
        self.full_cookies = full_cookies or os.environ.get("IMDB_COOKIES")

        if not self.full_cookies and (not self.session_id or not self.at_main or not self.session_token):
            raise ValueError(
                "IMDb session credentials required. Set IMDB_SESSION_ID, IMDB_AT_MAIN, "
                "and IMDB_SESSION_TOKEN environment variables, or provide full_cookies."
            )

    def _get_cookies(self) -> str:
        """Build cookie string from session credentials."""
        if self.full_cookies:
            return self.full_cookies
        
        cookies = [
            f"session-id={self.session_id}",
            f"at-main={self.at_main}",
            f"session-token={self.session_token}",
        ]
        if self.ubid_main:
            cookies.append(f"ubid-main={self.ubid_main}")
        if self.sess_at_main:
            cookies.append(f"sess-at-main={self.sess_at_main}")
        if self.x_main:
            cookies.append(f"x-main={self.x_main}")
        if self.aws_waf_token:
            cookies.append(f"aws-waf-token={self.aws_waf_token}")
        cookies.append("lc-main=en_US")
        cookies.append("session-id-time=2082787201l")
        return "; ".join(cookies)

    def _get_headers(self) -> Dict[str, str]:
        """Build request headers."""
        headers = DEFAULT_HEADERS.copy()
        
        # Extract session-id from cookies if using full_cookies
        if self.full_cookies and not self.session_id:
            for part in self.full_cookies.split(";"):
                part = part.strip()
                if part.startswith("session-id="):
                    self.session_id = part.split("=", 1)[1]
                    break
        
        headers["x-amzn-sessionid"] = self.session_id
        headers["Cookie"] = self._get_cookies()
        return headers

    def _execute_operation(
        self, operation_name: str, variables: Dict = None
    ) -> Dict:
        """Execute a persisted query operation."""
        if operation_name not in OPERATIONS:
            raise ValueError(f"Unknown operation: {operation_name}")

        op = OPERATIONS[operation_name]
        headers = self._get_headers()

        # Build query params for GET request
        import urllib.parse
        extensions = json.dumps({
            "persistedQuery": {
                "sha256Hash": op["hash"],
                "version": 1,
            }
        }, separators=(',', ':'))

        params = f"operationName={urllib.parse.quote(operation_name)}&extensions={urllib.parse.quote(extensions)}"
        if variables:
            variables_json = json.dumps(variables, separators=(',', ':'))
            params += f"&variables={urllib.parse.quote(variables_json)}"

        url = f"{BASE_URL}?{params}"

        req = Request(url, headers=headers, method="GET")
        try:
            with urlopen(req) as resp:
                data = json.loads(resp.read().decode())
                if "errors" in data:
                    raise Exception(f"GraphQL errors: {data['errors']}")
                return data.get("data", {})
        except HTTPError as e:
            body = e.read().decode()
            raise Exception(f"HTTP {e.code}: {body}")

    def _execute_mutation(
        self, mutation_name: str, variables: Dict = None
    ) -> Dict:
        """Execute a mutation."""
        if mutation_name not in QUERIES:
            raise ValueError(f"Unknown mutation: {mutation_name}")

        query = QUERIES[mutation_name]
        headers = self._get_headers()

        body = {"query": query}
        if variables:
            body["variables"] = variables

        req = Request(
            BASE_URL,
            data=json.dumps(body).encode(),
            headers=headers,
            method="POST",
        )
        try:
            with urlopen(req) as resp:
                data = json.loads(resp.read().decode())
                if "errors" in data:
                    raise Exception(f"GraphQL errors: {data['errors']}")
                return data.get("data", {})
        except HTTPError as e:
            body = e.read().decode()
            raise Exception(f"HTTP {e.code}: {body}")

    # ==========================================
    # READ OPERATIONS
    # ==========================================

    def get_lists(self, first: int = 50) -> List[Dict]:
        """Get user's custom lists."""
        data = self._execute_operation(
            "YourListsSidebar",
            {"first": first, "locale": "en-US"},
        )
        edges = data.get("lists", {}).get("edges", [])
        return [edge["node"] for edge in edges]

    def get_ratings(
        self, title_ids: List[str], locale: str = "en-US"
    ) -> List[Dict]:
        """Get user's ratings and watched status for titles."""
        data = self._execute_operation(
            "PersonalizedUserData",
            {
                "idArray": title_ids,
                "includeUserData": True,
                "includeWatchedData": True,
                "fetchOtherUserRating": False,
                "locale": locale,
                "location": {
                    "postalCodeLocation": {
                        "country": "US",
                        "postalCode": "55401",
                    }
                },
            },
        )
        return data.get("titles", [])

    def get_recently_viewed(self, count: int = 15) -> List[Dict]:
        """Get recently viewed titles."""
        data = self._execute_operation(
            "RVI_Items",
            {"count": count, "locale": "en-US"},
        )
        edges = data.get("recentlyViewedItems", {}).get("edges", [])
        return [edge["node"] for edge in edges]

    # ==========================================
    # WRITE OPERATIONS - LISTS
    # ==========================================

    def create_list(
        self,
        name: str,
        description: str = "",
        visibility: str = "PUBLIC",
        allow_duplicates: bool = False,
        list_type: str = "TITLES",
    ) -> Dict:
        """Create a new list."""
        data = self._execute_mutation(
            "createList",
            {
                "input": {
                    "name": name,
                    "listDescription": description,
                    "visibility": visibility,
                    "allowDuplicates": allow_duplicates,
                    "listType": list_type,
                }
            },
        )
        return data.get("createList", {})

    def add_to_list(
        self, list_id: str, item_id: str, item_type: str = "title"
    ) -> Dict:
        """Add an item to a list."""
        data = self._execute_mutation(
            "addItemToList",
            {
                "input": {
                    "listId": list_id,
                    "item": {
                        "itemElementId": item_id,
                    },
                }
            },
        )
        return data.get("addItemToList", {})

    def remove_from_list(self, list_id: str, item_id: str) -> Dict:
        """Remove an item from a list."""
        data = self._execute_mutation(
            "removeElementFromList",
            {"listId": list_id, "itemId": item_id},
        )
        return data.get("removeElementFromList", {})

    def edit_list_name(self, list_id: str, name: str) -> Dict:
        """Edit a list's name."""
        data = self._execute_mutation(
            "editListName",
            {"listId": list_id, "name": name},
        )
        return data.get("editListName", {}).get("list", {})

    def edit_list_visibility(self, list_id: str, visibility: str) -> Dict:
        """Edit a list's visibility."""
        data = self._execute_mutation(
            "editListVisibility",
            {"listId": list_id, "visibility": visibility},
        )
        return data.get("editListVisibility", {}).get("list", {})

    def delete_list(self, list_id: str) -> bool:
        """Delete a list."""
        data = self._execute_mutation(
            "deleteList",
            {"listId": list_id},
        )
        return data.get("deleteList", False)

    def copy_list_items(
        self, source_list_id: str, target_list_id: str
    ) -> Dict:
        """Copy items from one list to another."""
        data = self._execute_mutation(
            "copyListItemIds",
            {
                "sourceListId": source_list_id,
                "targetListId": target_list_id,
            },
        )
        return data.get("copyListItemIds", {})

    # ==========================================
    # WRITE OPERATIONS - RATINGS
    # ==========================================

    def rate_title(self, title_id: str, rating: int) -> Dict:
        """Rate a title (1-10)."""
        if not 1 <= rating <= 10:
            raise ValueError("Rating must be between 1 and 10")
        data = self._execute_mutation(
            "rateTitle",
            {"titleId": title_id, "rating": rating},
        )
        return data.get("rateTitle", {})

    def delete_rating(self, title_id: str) -> bool:
        """Delete a rating."""
        data = self._execute_mutation(
            "deleteTitleRating",
            {"titleId": title_id},
        )
        return data.get("deleteTitleRating", False)

    # ==========================================
    # WRITE OPERATIONS - WATCHLIST
    # ==========================================

    def add_to_watchlist(
        self, item_id: str, item_type: str = "title"
    ) -> Dict:
        """Add item to watchlist."""
        data = self._execute_mutation(
            "addItemToPredefinedList",
            {
                "listType": "WATCHLIST",
                "itemId": item_id,
                "itemType": item_type,
            },
        )
        return data.get("addItemToPredefinedList", {})

    def remove_from_watchlist(self, item_id: str) -> Dict:
        """Remove item from watchlist."""
        data = self._execute_mutation(
            "removeElementFromPredefinedList",
            {
                "listType": "WATCHLIST",
                "itemId": item_id,
            },
        )
        return data.get("removeElementFromPredefinedList", {})


# CLI helper
def main():
    """CLI entry point."""
    import argparse

    parser = argparse.ArgumentParser(description="IMDb API Client")
    subparsers = parser.add_subparsers(dest="command")

    # Lists
    subparsers.add_parser("lists", help="Get user's lists")

    # Ratings
    ratings_parser = subparsers.add_parser("ratings", help="Get ratings")
    ratings_parser.add_argument("ids", nargs="+", help="IMDb title IDs")

    # Recently viewed
    subparsers.add_parser("recent", help="Get recently viewed")

    # Rate
    rate_parser = subparsers.add_parser("rate", help="Rate a title")
    rate_parser.add_argument("title_id", help="IMDb title ID")
    rate_parser.add_argument("rating", type=int, help="Rating (1-10)")

    # Create list
    create_parser = subparsers.add_parser("create-list", help="Create a list")
    create_parser.add_argument("name", help="List name")
    create_parser.add_argument("--description", default="", help="Description")
    create_parser.add_argument(
        "--visibility", default="PUBLIC", choices=["PUBLIC", "PRIVATE"]
    )

    # Add to list
    add_parser = subparsers.add_parser("add-to-list", help="Add to list")
    add_parser.add_argument("list_id", help="List ID")
    add_parser.add_argument("item_id", help="IMDb title ID")

    # Watchlist
    watchlist_parser = subparsers.add_parser(
        "watchlist", help="Add to watchlist"
    )
    watchlist_parser.add_argument("item_id", help="IMDb title ID")

    args = parser.parse_args()
    client = IMDbClient()

    if args.command == "lists":
        lists = client.get_lists()
        for lst in lists:
            print(f"  {lst['id']}: {lst['name']['originalText']} ({lst['items']['total']} items)")

    elif args.command == "ratings":
        ratings = client.get_ratings(args.ids)
        for r in ratings:
            rating = r.get("userRating", "Not rated")
            watched = "✓" if r.get("userWatchedStatus", {}).get("isWatched") else "✗"
            print(f"  {r['id']}: {rating} [{watched}]")

    elif args.command == "recent":
        items = client.get_recently_viewed()
        for item in items:
            print(f"  {item['id']}: {item['titleText']['text']}")

    elif args.command == "rate":
        result = client.rate_title(args.title_id, args.rating)
        print(f"Rated {args.title_id}: {args.rating}")

    elif args.command == "create-list":
        result = client.create_list(args.name, args.description, args.visibility)
        print(f"Created list: {result.get('id', 'unknown')}")

    elif args.command == "add-to-list":
        result = client.add_to_list(args.list_id, args.item_id)
        print(f"Added {args.item_id} to list {args.list_id}")

    elif args.command == "watchlist":
        result = client.add_to_watchlist(args.item_id)
        print(f"Added {args.item_id} to watchlist")

    else:
        parser.print_help()


if __name__ == "__main__":
    main()
