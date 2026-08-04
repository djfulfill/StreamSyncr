"""
OAuth2 flows for one-click service connection on the configure page.

Architecture:
  1. User clicks "Connect {Service}" → redirect to service auth page
  2. User authorizes on service's site → redirected back to our callback
  3. Our callback exchanges code for token → returns page that sends token
     back to configure page via postMessage + window.close()
  4. Configure page JS receives token → auto-populates the field

Requirements (env vars):
  TRAKT_CLIENT_ID / TRAKT_CLIENT_SECRET — from app.trakt.tv/settings/apps/api
  SIMKL_CLIENT_ID / SIMKL_CLIENT_SECRET — from simkl.com/settings/developer
  ANILIST_CLIENT_ID / ANILIST_CLIENT_SECRET — from anilist.co/settings/developer
"""

import json
import os
import secrets
import threading
import time
from typing import Optional, Tuple
from urllib.parse import urlencode
from urllib.request import Request, urlopen
from urllib.error import HTTPError

# In-memory state store. In production, use DB/Redis.
_pending_states: dict = {}
_pending_lock = threading.Lock()
STATE_TTL = 600  # 10 minutes

# Server base URL for redirect URIs
BASE_URL = os.environ.get("STREAMSYNCR_URL", "http://localhost:7800")


# ── State tokens (CSRF protection) ──────────────────────────

def _cleanup():
    now = time.time()
    with _pending_lock:
        expired = [s for s, v in _pending_states.items() if v["expires"] < now]
        for s in expired:
            del _pending_states[s]


def _create_state(service: str) -> str:
    _cleanup()
    state = secrets.token_hex(32)
    with _pending_lock:
        _pending_states[state] = {
            "service": service,
            "expires": time.time() + STATE_TTL,
        }
    return state


def _consume_state(state: str) -> Optional[str]:
    """Verify state token. Returns service name or None."""
    _cleanup()
    with _pending_lock:
        entry = _pending_states.pop(state, None)
    if entry and entry["expires"] >= time.time():
        return entry["service"]
    return None


# ── OAuth Callback HTML (rendered when user returns) ────────

def _callback_html(service: str, token: str, field_id: str, error: str = None) -> str:
    """HTML page that sends token/error to the opener configure page via postMessage."""
    payload = json.dumps({
        "service": service,
        "field_id": field_id,
        "token": token,
        "error": error,
    })
    return f"""<!DOCTYPE html>
<html><head><meta charset="UTF-8"><title>Authorizing...</title></head>
<body style="background:#0f0f1a;color:#e0e0e0;font-family:sans-serif;text-align:center;padding-top:60px;">
<p>{"✓ Connected!" if token else "✗ Failed: " + (error or "unknown")}</p>
<p>This window will close automatically.</p>
<script>
const payload = {payload};
if (window.opener && !window.opener.closed) {{
    window.opener.postMessage(payload, '*');
}}
setTimeout(function() {{ window.close(); }}, 2000);
</script>
</body></html>"""


# ── Trakt OAuth ─────────────────────────────────────────────

TRAKT_CLIENT_ID = os.environ.get("TRAKT_CLIENT_ID", "")
TRAKT_CLIENT_SECRET = os.environ.get("TRAKT_CLIENT_SECRET", "")
TRAKT_REDIRECT_URI = f"{BASE_URL}/api/oauth/trakt/callback"


def trakt_authorize_url() -> Tuple[Optional[str], Optional[str]]:
    """Returns (url, error)."""
    if not TRAKT_CLIENT_ID:
        return None, "TRAKT_CLIENT_ID not set (env var)"
    state = _create_state("trakt")
    url = (
        "https://trakt.tv/oauth/authorize?"
        + urlencode({
            "response_type": "code",
            "client_id": TRAKT_CLIENT_ID,
            "redirect_uri": TRAKT_REDIRECT_URI,
            "state": state,
        })
    )
    return url, None


def trakt_exchange_code(code: str) -> Tuple[Optional[str], Optional[str]]:
    """Returns (access_token, error)."""
    if not TRAKT_CLIENT_ID or not TRAKT_CLIENT_SECRET:
        return None, "Trakt client credentials not set"

    try:
        req = Request(
            "https://api.trakt.tv/oauth/token",
            data=json.dumps({
                "code": code,
                "client_id": TRAKT_CLIENT_ID,
                "client_secret": TRAKT_CLIENT_SECRET,
                "redirect_uri": TRAKT_REDIRECT_URI,
                "grant_type": "authorization_code",
            }).encode(),
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with urlopen(req) as resp:
            data = json.loads(resp.read())
            return data.get("access_token"), None
    except HTTPError as e:
        body = e.read().decode()
        return None, f"{e.code} — {body[:200]}"
    except Exception as e:
        return None, str(e)


# ── Simkl OAuth ─────────────────────────────────────────────

SIMKL_CLIENT_ID = os.environ.get("SIMKL_CLIENT_ID", "")
SIMKL_CLIENT_SECRET = os.environ.get("SIMKL_CLIENT_SECRET", "")
SIMKL_REDIRECT_URI = f"{BASE_URL}/api/oauth/simkl/callback"


def simkl_authorize_url() -> Tuple[Optional[str], Optional[str]]:
    if not SIMKL_CLIENT_ID:
        return None, "SIMKL_CLIENT_ID not set"
    state = _create_state("simkl")
    url = (
        "https://simkl.com/oauth/authorize?"
        + urlencode({
            "response_type": "code",
            "client_id": SIMKL_CLIENT_ID,
            "redirect_uri": SIMKL_REDIRECT_URI,
            "state": state,
        })
    )
    return url, None


def simkl_exchange_code(code: str) -> Tuple[Optional[str], Optional[str]]:
    if not SIMKL_CLIENT_ID or not SIMKL_CLIENT_SECRET:
        return None, "Simkl credentials not set"

    try:
        req = Request(
            "https://api.simkl.com/oauth/token",
            data=json.dumps({
                "code": code,
                "client_id": SIMKL_CLIENT_ID,
                "client_secret": SIMKL_CLIENT_SECRET,
                "redirect_uri": SIMKL_REDIRECT_URI,
                "grant_type": "authorization_code",
            }).encode(),
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with urlopen(req) as resp:
            data = json.loads(resp.read())
            return data.get("access_token"), None
    except HTTPError as e:
        return None, f"{e.code} — {e.read().decode()[:200]}"
    except Exception as e:
        return None, str(e)


# ── AniList OAuth ───────────────────────────────────────────

ANILIST_CLIENT_ID = os.environ.get("ANILIST_CLIENT_ID", "")
ANILIST_CLIENT_SECRET = os.environ.get("ANILIST_CLIENT_SECRET", "")
ANILIST_REDIRECT_URI = f"{BASE_URL}/api/oauth/anilist/callback"


def anilist_authorize_url() -> Tuple[Optional[str], Optional[str]]:
    if not ANILIST_CLIENT_ID:
        return None, "ANILIST_CLIENT_ID not set"
    state = _create_state("anilist")
    url = (
        "https://anilist.co/api/v2/oauth/authorize?"
        + urlencode({
            "client_id": ANILIST_CLIENT_ID,
            "redirect_uri": ANILIST_REDIRECT_URI,
            "response_type": "code",
            "state": state,
        })
    )
    return url, None


def anilist_exchange_code(code: str) -> Tuple[Optional[str], Optional[str]]:
    if not ANILIST_CLIENT_ID or not ANILIST_CLIENT_SECRET:
        return None, "AniList credentials not set"

    try:
        req = Request(
            "https://anilist.co/api/v2/oauth/token",
            data=json.dumps({
                "grant_type": "authorization_code",
                "client_id": ANILIST_CLIENT_ID,
                "client_secret": ANILIST_CLIENT_SECRET,
                "redirect_uri": ANILIST_REDIRECT_URI,
                "code": code,
            }).encode(),
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with urlopen(req) as resp:
            data = json.loads(resp.read())
            return data.get("access_token"), None
    except HTTPError as e:
        return None, f"{e.code} — {e.read().decode()[:200]}"
    except Exception as e:
        return None, str(e)