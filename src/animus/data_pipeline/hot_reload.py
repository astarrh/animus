"""Tier 3: File watcher for hot-reloading Excel changes during development.

Uses watchdog to monitor the Excel file for changes and re-run the full
data pipeline (parse → assemble → regenerate composites) on each save.

This is a dev-only feature. Production should load baked static data.
"""

from __future__ import annotations

import threading
from pathlib import Path
from typing import Callable

from watchdog.events import FileSystemEventHandler
from watchdog.observers import Observer


class _DebouncedHandler(FileSystemEventHandler):
    """Watches for changes to a target file, debouncing rapid saves.

    Excel triggers multiple filesystem events per save, so we debounce
    to avoid redundant rebuilds.
    """

    def __init__(
        self,
        target_path: Path,
        callback: Callable[[], None],
        debounce_seconds: float = 1.0,
    ):
        self._target_path = target_path.resolve()
        self._callback = callback
        self._debounce_seconds = debounce_seconds
        self._timer: threading.Timer | None = None
        self._lock = threading.Lock()

    def on_modified(self, event):
        if event.is_directory:
            return
        if Path(event.src_path).resolve() == self._target_path:
            self._schedule_rebuild()

    def on_created(self, event):
        if event.is_directory:
            return
        if Path(event.src_path).resolve() == self._target_path:
            self._schedule_rebuild()

    def _schedule_rebuild(self):
        with self._lock:
            if self._timer is not None:
                self._timer.cancel()
            self._timer = threading.Timer(self._debounce_seconds, self._callback)
            self._timer.daemon = True
            self._timer.start()


def start_watcher(
    excel_path: Path,
    on_rebuild: Callable[[], None],
    debounce_seconds: float = 1.0,
) -> Observer:
    """Start watching the Excel file for changes.

    Args:
        excel_path: Path to the Excel file to watch.
        on_rebuild: Callback to invoke when the file changes (after debounce).
        debounce_seconds: Minimum time between rebuilds. Default 1.0s.

    Returns:
        The watchdog Observer instance. Call observer.stop() to clean up.
    """
    handler = _DebouncedHandler(excel_path, on_rebuild, debounce_seconds)
    observer = Observer()
    observer.schedule(handler, str(excel_path.parent), recursive=False)
    observer.daemon = True
    observer.start()
    return observer
