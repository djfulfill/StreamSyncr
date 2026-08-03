import os
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class Config:
    host: str = "0.0.0.0"
    port: int = 7800

    tmdb_api_key: str = os.environ.get("TMDB_API_KEY", "")
    trakt_api_key: str = os.environ.get("TRAKT_API_KEY", "")
    trakt_token: str = os.environ.get("TRAKT_TOKEN", "")
    anilist_token: str = os.environ.get("ANILIST_TOKEN", "")
    simkl_client_id: str = os.environ.get("SIMKL_CLIENT_ID", "")

    debrid_priority: list = field(default_factory=lambda: [
        "realdebrid", "torbox", "alldebrid"
    ])


config = Config()
