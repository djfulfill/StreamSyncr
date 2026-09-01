"""Letterboxd addon — movie tracking, write-only API."""

from core.addons.base import (
    Addon, CatalogDef, VerifyResult,
)


class LetterboxdAddon:
    name = "Letterboxd"
    slug = "letterboxd"
    description = "Log and rate films on Letterboxd (write-only API)"

    config_schema = {
        "letterboxd_session": {"type": "string", "label": "Session ID", "secret": True, "required": True},
        "letterboxd_csrf": {"type": "string", "label": "CSRF Token", "secret": True},
    }

    config_keys = ["letterboxd_session", "letterboxd_csrf"]

    catalogs = None  # Read-only not supported via API

    def is_configured(self, config: dict) -> bool:
        return bool(config.get("letterboxd_session"))

    def verify(self, config: dict) -> VerifyResult:
        if not config.get("letterboxd_session"):
            return VerifyResult(status="missing_credentials")
        return VerifyResult(status="ok", details={"note": "write-only API"})

    def get_catalog(self, catalog_id: str, media_type: str, skip: int,
                    config: dict, genre: str | None = None) -> list[dict]:
        return []
