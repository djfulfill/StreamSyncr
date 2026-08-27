"""
Browser cookie loader — reads cookies directly from the local browser's
cookie database using browser_cookie3.

This is the server-side fallback for cookie-based services (IMDb, Letterboxd,
Sofa Sidekick, Netflix, etc.). It complements the Chrome extension, which
handles localStorage-based services (Trakt, AniList, Simkl, WeTrakr) that
store auth tokens in localStorage rather than cookies.

Usage:
    from browser_cookies import load_browser_cookies
    cookies = load_browser_cookies()
    # cookies = {"imdb": {"session-id": "...", "at-main": "..."}, ...}

    merged = merge_into_config(existing_config, cookies)
"""

import logging
from typing import Dict, Optional

logger = logging.getLogger("streamsyncr.browser_cookies")

# ── Service definitions ───────────────────────────────────────
# Maps service ID → (cookie domain, list of cookie names to extract,
# required cookie names for the service to be considered "valid")
SERVICE_COOKIE_MAP = {
    "imdb": {
        "domain": ".imdb.com",
        "cookies": ["session-id", "at-main", "session-token", "ubid-main",
                     "sess-at-main", "x-main", "aws-waf-token"],
        "required": ["session-id", "at-main", "session-token"],
    },
    "letterboxd": {
        "domain": ".letterboxd.com",
        "cookies": ["lfu-session", "remember", "com.xk72.webparts.csrf"],
        "required": ["lfu-session", "remember"],
    },
    "sofasidekick": {
        "domain": ".sofasidekick.com",
        "cookies": ["session_id", "cf_clearance", "__cf_bm"],
        "required": ["session_id"],
    },
    "netflix": {
        "domain": ".netflix.com",
        "cookies": ["NetflixId", "SecureNetflixId", "nfvdid", "memclid"],
        "required": ["NetflixId", "SecureNetflixId"],
    },
    "primevideo": {
        "domain": ".primevideo.com",
        "cookies": ["session-id", "at-main", "ubid-main", "x-main",
                     "sess-at-main", "lrc-main", "lc-main"],
        "required": ["session-id", "at-main"],
    },
    "disneyplus": {
        "domain": ".disneyplus.com",
        "cookies": ["ct_", "bt_obi", "dpong", "amplitude_id", "ajs_anonymous_id"],
        "required": ["ct_"],
    },
    "max": {
        "domain": ".max.com",
        "cookies": ["hb_obi", "tp_obi", "jwt", "apollo-auth", "BM-Visitor-Id"],
        "required": ["jwt"],
    },
    "simkl": {
        "domain": ".simkl.com",
        "cookies": ["simkl", "cf_clearance", "__cflb", "cc"],
        "required": ["simkl"],
    },
    "wetrakr": {
        "domain": ".wetrakr.com",
        "cookies": ["wta_at", "wta_rt"],
        "required": ["wta_at", "wta_rt"],
    },
    "trakt": {
        "domain": ".trakt.tv",
        "cookies": ["cf_clearance", "trakt-oidc-auth"],
        "required": [],  # Trakt auth is in localStorage, cookies alone aren't enough
    },
    "anilist": {
        "domain": ".anilist.co",
        "cookies": ["laravel_session"],
        "required": [],  # AniList auth is in localStorage
    },
}


def _try_load(browser_fn, browser_name: str) -> Optional[object]:
    """Try to load cookies from a browser, return None on failure."""
    try:
        return browser_fn(domain_name="")
    except Exception as e:
        logger.debug(f"Could not load {browser_name} cookies: {e}")
        return None


def load_browser_cookies() -> Dict[str, Dict[str, str]]:
    """Load cookies for all known services from the local browser.

    Tries Chrome, Brave, Firefox, Edge in order and merges results.
    Returns {service_id: {cookie_name: cookie_value}}.
    """
    import browser_cookie3

    cookie_jars = []
    for fn, name in [
        (browser_cookie3.chrome, "Chrome"),
        (browser_cookie3.brave, "Brave"),
        (browser_cookie3.firefox, "Firefox"),
        (browser_cookie3.edge, "Edge"),
    ]:
        jar = _try_load(fn, name)
        if jar:
            cookie_jars.append((name, jar))

    if not cookie_jars:
        logger.warning("No browser cookie databases found")
        return {}

    results = {}

    for service_id, spec in SERVICE_COOKIE_MAP.items():
        domain = spec["domain"]
        wanted = set(spec["cookies"])
        extracted = {}

        for browser_name, jar in cookie_jars:
            for cookie in jar:
                if domain in cookie.domain and cookie.name in wanted:
                    # First browser that has the cookie wins
                    if cookie.name not in extracted:
                        extracted[cookie.name] = cookie.value

        if extracted:
            required = spec["required"]
            valid = all(name in extracted for name in required) if required else True
            results[service_id] = {
                "cookies": extracted,
                "valid": valid,
                "missing": [r for r in required if r not in extracted],
                "source": "browser",
            }
            logger.debug(f"Loaded {service_id}: {len(extracted)} cookies (valid={valid})")

    return results


def cookies_to_config(service_id: str, cookies: Dict[str, str]) -> Dict[str, str]:
    """Convert raw cookies for a service into config-store format.

    This mirrors the mapping in server.py's extension_cookies endpoint.
    """
    c = cookies

    if service_id == "imdb":
        return {
            "imdb_full_cookies": "; ".join(f"{k}={v}" for k, v in c.items()),
            "imdb_session_id": c.get("session-id", ""),
            "imdb_at_main": c.get("at-main", ""),
            "imdb_session_token": c.get("session-token", ""),
            "imdb_ubid_main": c.get("ubid-main", ""),
            "imdb_sess_at_main": c.get("sess-at-main", ""),
        }

    if service_id == "letterboxd":
        return {
            "letterboxd_cookies": "; ".join(f"{k}={v}" for k, v in c.items()),
            "letterboxd_session": c.get("lfu-session", ""),
            "letterboxd_remember": c.get("remember", ""),
            "letterboxd_csrf": c.get("com.xk72.webparts.csrf", ""),
        }

    if service_id == "sofasidekick":
        return {
            "sofasidekick_session_id": c.get("session_id", ""),
            "sofasidekick_cf_clearance": c.get("cf_clearance", ""),
            "sofasidekick_cf_bm": c.get("__cf_bm", ""),
        }

    if service_id == "netflix":
        return {
            "netflix_id": c.get("NetflixId", ""),
            "netflix_secure_id": c.get("SecureNetflixId", ""),
        }

    if service_id == "primevideo":
        return {
            "primevideo_session_id": c.get("session-id", ""),
            "primevideo_at_main": c.get("at-main", ""),
        }

    if service_id == "disneyplus":
        return {"disneyplus_ct": c.get("ct_", "")}

    if service_id == "max":
        return {"max_jwt": c.get("jwt", "")}

    if service_id == "simkl":
        return {"simkl_session_cookie": c.get("simkl", "")}

    if service_id == "wetrakr":
        return {
            "wetrakr_access_token": c.get("wta_at", ""),
            "wetrakr_refresh_token": c.get("wta_rt", ""),
        }

    return {}


def merge_into_config(existing: dict, browser_cookies: Dict[str, Dict]) -> dict:
    """Merge browser-extracted cookies into an existing config dict.

    Only overwrites fields when the browser has a valid value; never
    clears an existing config value with an empty one.
    """
    merged = dict(existing)

    for service_id, data in browser_cookies.items():
        if not data.get("valid"):
            continue
        config_updates = cookies_to_config(service_id, data["cookies"])
        for key, value in config_updates.items():
            if value:  # Only set non-empty values
                merged[key] = value

    return merged


def merge_extension_config(existing: dict, extension_config: dict) -> dict:
    """Merge extension-sourced config into an existing config dict.

    Only overwrites with non-empty extension values; preserves existing
    values that the extension doesn't have.
    """
    merged = dict(existing)
    for key, value in extension_config.items():
        if value:  # Only set non-empty values
            merged[key] = value
    return merged
