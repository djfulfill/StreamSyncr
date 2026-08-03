"""
Background sync service — runs sync on a configurable interval.

Usage:
    from sync_engine.background import BackgroundSync
    bg = BackgroundSync(engine, interval_minutes=30)
    bg.start()
    # ... later ...
    bg.stop()
"""

import time
import threading
import json
import os
from datetime import datetime, timezone
from pathlib import Path

from .engine import SyncEngine


class SyncLog:
    """Append-only audit log for sync operations."""

    def __init__(self, log_path=None):
        if log_path is None:
            log_path = os.path.expanduser("~/.streamsyncr/sync_log.jsonl")
        self.log_path = Path(log_path)
        self.log_path.parent.mkdir(parents=True, exist_ok=True)

    def append(self, entry):
        """Append a sync entry to the log."""
        entry["timestamp"] = datetime.now(timezone.utc).isoformat()
        with open(self.log_path, "a") as f:
            f.write(json.dumps(entry, default=str) + "\n")

    def read(self, limit=50, offset=0):
        """Read recent sync entries (newest first)."""
        if not self.log_path.exists():
            return []
        lines = self.log_path.read_text().strip().split("\n")
        lines = [l for l in lines if l.strip()]
        entries = []
        for line in reversed(lines):
            try:
                entries.append(json.loads(line))
            except json.JSONDecodeError:
                continue
            if len(entries) >= limit + offset:
                break
        return entries[offset:offset + limit]

    def stats(self):
        """Get summary stats from the log."""
        entries = self.read(limit=1000)
        if not entries:
            return {"total_syncs": 0, "total_items": 0, "total_errors": 0}

        total_items = sum(e.get("items_synced", 0) for e in entries)
        total_errors = sum(len(e.get("errors", [])) for e in entries)
        services_seen = set()
        for e in entries:
            services_seen.update(e.get("services_synced", []))

        return {
            "total_syncs": len(entries),
            "total_items": total_items,
            "total_errors": total_errors,
            "services": list(services_seen),
            "last_sync": entries[0].get("timestamp") if entries else None,
        }

    def clear(self):
        """Clear the log."""
        if self.log_path.exists():
            self.log_path.unlink()


class BackgroundSync:
    """
    Runs sync on a background thread at a configurable interval.

    Usage:
        engine = SyncEngine()
        # register services...
        bg = BackgroundSync(engine, interval_minutes=30)
        bg.start()
        bg.stop()
    """

    def __init__(self, engine, interval_minutes=30, log_path=None):
        """
        Args:
            engine: SyncEngine instance with services registered
            interval_minutes: How often to sync (default 30 min)
            log_path: Optional path for the sync log
        """
        self.engine = engine
        self.interval = interval_minutes * 60  # convert to seconds
        self.log = SyncLog(log_path)
        self._thread = None
        self._stop_event = threading.Event()
        self._running = False
        self._last_sync = None
        self._sync_count = 0

    @property
    def is_running(self):
        return self._running

    @property
    def last_sync(self):
        return self._last_sync

    @property
    def sync_count(self):
        return self._sync_count

    def start(self, dry_run=False, sync_watched=True, sync_ratings=True,
              sync_favorites=True):
        """Start background sync."""
        if self._running:
            return

        self._stop_event.clear()
        self._running = True

        self._thread = threading.Thread(
            target=self._run_loop,
            args=(dry_run, sync_watched, sync_ratings, sync_favorites),
            daemon=True,
        )
        self._thread.start()

    def stop(self):
        """Stop background sync."""
        self._stop_event.set()
        self._running = False
        if self._thread:
            self._thread.join(timeout=5)
            self._thread = None

    def sync_once(self, dry_run=False, sync_watched=True, sync_ratings=True,
                  sync_favorites=True, progress_callback=None):
        """Run a single sync and log the result."""
        start = time.time()
        try:
            result = self.engine.sync(
                dry_run=dry_run,
                sync_watched=sync_watched,
                sync_ratings=sync_ratings,
                sync_favorites=sync_favorites,
                progress_callback=progress_callback,
            )
            entry = {
                "type": "sync",
                "strategy": result.strategy,
                "dry_run": result.dry_run,
                "services_synced": result.services_synced,
                "items_synced": result.items_synced,
                "watched_synced": result.watched_synced,
                "ratings_synced": result.ratings_synced,
                "favorites_synced": result.favorites_synced,
                "errors": result.errors,
                "duration_ms": result.duration_ms,
                "changes_count": len(result.changes),
            }
            self.log.append(entry)
            self._last_sync = datetime.now(timezone.utc).isoformat()
            self._sync_count += 1
            return result

        except Exception as e:
            entry = {
                "type": "sync_error",
                "error": str(e),
                "duration_ms": int((time.time() - start) * 1000),
            }
            self.log.append(entry)
            raise

    def _run_loop(self, dry_run, sync_watched, sync_ratings, sync_favorites):
        """Background loop that syncs at the configured interval."""
        while not self._stop_event.is_set():
            try:
                self.sync_once(
                    dry_run=dry_run,
                    sync_watched=sync_watched,
                    sync_ratings=sync_ratings,
                    sync_favorites=sync_favorites,
                )
            except Exception:
                pass  # errors are logged in sync_once

            # Wait for interval or stop signal
            self._stop_event.wait(timeout=self.interval)

    def get_status(self):
        """Get current background sync status."""
        log_stats = self.log.stats()
        return {
            "running": self._running,
            "interval_minutes": self.interval // 60,
            "last_sync": self._last_sync,
            "total_syncs": self._sync_count,
            "log": log_stats,
        }
