"""Built-in torrent scrapers — Python ports of Sootio's JS scrapers.

Each scraper implements the ScraperPlugin protocol and searches a
single source for torrents matching an IMDb ID.
"""

from .torrentio import TorrentioScraper
from .jackett import JackettScraper
from .btdig import BTDiggScraper
from .magnetdl import MagnetDLScraper

__all__ = [
    "TorrentioScraper",
    "JackettScraper",
    "BTDiggScraper",
    "MagnetDLScraper",
]
