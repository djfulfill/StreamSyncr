"""
SQLite-backed persistent storage for StreamSyncr.

Replaces the in-memory _config_store dict with a database that
survives restarts. Also stores resume positions for cross-device
playback sync.

Database location: ~/.streamsyncr/config.db
"""

import sqlite3
import json
import os
import time
import threading
from pathlib import Path

DB_DIR = Path.home() / ".streamsyncr"
DB_PATH = DB_DIR / "config.db"


class ConfigStore:
    """SQLite-backed config store. Drop-in replacement for _config_store dict.

    Supports the same interface as a plain dict:
        store[token] = config_dict
        store.get(token, {})
        token in store
        store.keys()
        store.items()
        store.pop(token)
    """

    def __init__(self, db_path: str | Path = DB_PATH):
        DB_DIR.mkdir(parents=True, exist_ok=True)
        self._db_path = str(db_path)
        self._local = threading.local()
        self._init_db()

    def _get_conn(self) -> sqlite3.Connection:
        if not hasattr(self._local, "conn") or self._local.conn is None:
            conn = sqlite3.connect(self._db_path, check_same_thread=False)
            conn.execute("PRAGMA journal_mode=WAL")
            conn.execute("PRAGMA busy_timeout=5000")
            conn.row_factory = sqlite3.Row
            self._local.conn = conn
        return self._local.conn

    def _init_db(self):
        conn = self._get_conn()
        conn.executescript("""
            CREATE TABLE IF NOT EXISTS config_store (
                token       TEXT PRIMARY KEY,
                config_json TEXT NOT NULL,
                created_at  REAL NOT NULL,
                updated_at  REAL NOT NULL
            );
            CREATE TABLE IF NOT EXISTS resume_positions (
                id              INTEGER PRIMARY KEY AUTOINCREMENT,
                token           TEXT NOT NULL,
                item_id         TEXT NOT NULL,
                media_type      TEXT NOT NULL DEFAULT 'movie',
                season          INTEGER,
                episode         INTEGER,
                position_seconds REAL NOT NULL,
                total_seconds   REAL NOT NULL,
                progress_pct    REAL NOT NULL,
                title           TEXT,
                year            INTEGER,
                updated_at      REAL NOT NULL,
                UNIQUE(token, item_id, media_type, season, episode)
            );
            CREATE INDEX IF NOT EXISTS idx_resume_token ON resume_positions(token);
            CREATE INDEX IF NOT EXISTS idx_resume_item   ON resume_positions(item_id);
        """)
        conn.commit()

    # ── Dict-like interface ──────────────────────────────────

    def get(self, token: str, default=None) -> dict | None:
        conn = self._get_conn()
        row = conn.execute(
            "SELECT config_json FROM config_store WHERE token = ?", (token,)
        ).fetchone()
        if row is None:
            return default
        return json.loads(row["config_json"])

    def __contains__(self, token: str) -> bool:
        conn = self._get_conn()
        row = conn.execute(
            "SELECT 1 FROM config_store WHERE token = ?", (token,)
        ).fetchone()
        return row is not None

    def __setitem__(self, token: str, config: dict):
        now = time.time()
        conn = self._get_conn()
        conn.execute(
            """INSERT INTO config_store (token, config_json, created_at, updated_at)
               VALUES (?, ?, ?, ?)
               ON CONFLICT(token) DO UPDATE SET
                 config_json = excluded.config_json,
                 updated_at  = excluded.updated_at""",
            (token, json.dumps(config), now, now),
        )
        conn.commit()

    def __getitem__(self, token: str) -> dict:
        result = self.get(token)
        if result is None:
            raise KeyError(token)
        return result

    def pop(self, token: str, default=None):
        conn = self._get_conn()
        row = conn.execute(
            "SELECT config_json FROM config_store WHERE token = ?", (token,)
        ).fetchone()
        if row is None:
            return default
        conn.execute("DELETE FROM config_store WHERE token = ?", (token,))
        conn.commit()
        return json.loads(row["config_json"])

    def keys(self):
        conn = self._get_conn()
        return [r["token"] for r in conn.execute("SELECT token FROM config_store")]

    def items(self):
        conn = self._get_conn()
        return [(r["token"], json.loads(r["config_json"]))
                for r in conn.execute("SELECT token, config_json FROM config_store")]

    def update(self, token: str, updates: dict):
        """Merge updates into existing config for a token."""
        existing = self.get(token, {})
        existing.update(updates)
        self[token] = existing


class ResumeStore:
    """Resume position storage and sync.

    Stores playback positions so users can resume across devices.
    Positions >95% are treated as "watched" and cleared.
    """

    def __init__(self, db_path: str | Path = DB_PATH):
        DB_DIR.mkdir(parents=True, exist_ok=True)
        self._db_path = str(db_path)
        self._local = threading.local()
        self._init_db()

    def _get_conn(self) -> sqlite3.Connection:
        if not hasattr(self._local, "conn") or self._local.conn is None:
            conn = sqlite3.connect(self._db_path, check_same_thread=False)
            conn.execute("PRAGMA journal_mode=WAL")
            conn.execute("PRAGMA busy_timeout=5000")
            conn.row_factory = sqlite3.Row
            self._local.conn = conn
        return self._local.conn

    def _init_db(self):
        # Shares DB with ConfigStore — tables already created
        pass

    def save_position(
        self,
        token: str,
        item_id: str,
        position_seconds: float,
        total_seconds: float,
        media_type: str = "movie",
        season: int | None = None,
        episode: int | None = None,
        title: str = "",
        year: int | None = None,
    ):
        """Upsert resume position."""
        if total_seconds <= 0:
            return

        progress_pct = min(100.0, (position_seconds / total_seconds) * 100)

        # Don't save if very close to end — it's "watched"
        if progress_pct >= 95:
            self.clear_position(token, item_id, media_type, season, episode)
            return

        now = time.time()
        conn = self._get_conn()
        conn.execute(
            """INSERT INTO resume_positions
               (token, item_id, media_type, season, episode,
                position_seconds, total_seconds, progress_pct,
                title, year, updated_at)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
               ON CONFLICT(token, item_id, media_type, season, episode) DO UPDATE SET
                 position_seconds = excluded.position_seconds,
                 total_seconds    = excluded.total_seconds,
                 progress_pct     = excluded.progress_pct,
                 title            = COALESCE(excluded.title, resume_positions.title),
                 year             = COALESCE(excluded.year, resume_positions.year),
                 updated_at       = excluded.updated_at""",
            (token, item_id, media_type, season, episode,
             position_seconds, total_seconds, progress_pct,
             title or None, year, now),
        )
        conn.commit()

    def get_position(
        self,
        token: str,
        item_id: str,
        media_type: str = "movie",
        season: int | None = None,
        episode: int | None = None,
    ) -> dict | None:
        """Get resume position for an item."""
        conn = self._get_conn()
        row = conn.execute(
            """SELECT position_seconds, total_seconds, progress_pct,
                      title, year, updated_at
               FROM resume_positions
               WHERE token = ? AND item_id = ? AND media_type = ?
                 AND season IS ? AND episode IS ?""",
            (token, item_id, media_type, season, episode),
        ).fetchone()
        if row is None:
            return None
        if row["progress_pct"] >= 95:
            return None
        return {
            "position_seconds": row["position_seconds"],
            "total_seconds": row["total_seconds"],
            "progress_pct": row["progress_pct"],
            "title": row["title"],
            "year": row["year"],
            "updated_at": row["updated_at"],
        }

    def clear_position(
        self,
        token: str,
        item_id: str,
        media_type: str = "movie",
        season: int | None = None,
        episode: int | None = None,
    ):
        conn = self._get_conn()
        conn.execute(
            """DELETE FROM resume_positions
               WHERE token = ? AND item_id = ? AND media_type = ?
                 AND season IS ? AND episode IS ?""",
            (token, item_id, media_type, season, episode),
        )
        conn.commit()

    def get_all_positions(self, token: str) -> list[dict]:
        """Get all resume positions for a user."""
        conn = self._get_conn()
        rows = conn.execute(
            """SELECT item_id, media_type, season, episode,
                      position_seconds, total_seconds, progress_pct,
                      title, year, updated_at
               FROM resume_positions
               WHERE token = ? AND progress_pct < 95
               ORDER BY updated_at DESC""",
            (token,),
        ).fetchall()
        return [dict(r) for r in rows]


# ── Global instances ────────────────────────────────────────

config_store = ConfigStore()
resume_store = ResumeStore()
