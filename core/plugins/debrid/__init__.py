"""Built-in debrid providers — Python implementations."""

from .realdebrid import RealDebridProvider
from .torbox import TorBoxProvider
from .alldebrid import AllDebridProvider

__all__ = [
    "RealDebridProvider",
    "TorBoxProvider",
    "AllDebridProvider",
]
