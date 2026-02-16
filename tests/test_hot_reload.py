"""Tests for the hot reload file watcher (Tier 3 pipeline).

Phase 2: Hot reload — modifying the Excel file triggers automatic recomputation.
"""

import threading
import time
from pathlib import Path

import pytest

pytest.importorskip("watchdog", reason="watchdog is an optional dev dependency")

from animus.data_pipeline.hot_reload import (
    start_watcher,
    _DebouncedHandler,
)


EXCEL_PATH = Path(__file__).parent.parent / "docs" / "personality_building_blocks.xlsx"


def _make_event(src_path: str, is_directory: bool = False):
    """Minimal event-like object with src_path and is_directory (watchdog API)."""
    return type("Event", (), {"src_path": src_path, "is_directory": is_directory})()


class TestHotReload:
    """File watcher debounces events and invokes callback on target file change."""

    def test_start_watcher_returns_observer(self):
        """start_watcher returns a watchdog Observer that can be stopped."""
        pytest.importorskip("watchdog")
        callback_invoked = threading.Event()

        def on_rebuild():
            callback_invoked.set()

        observer = start_watcher(EXCEL_PATH, on_rebuild, debounce_seconds=0.05)
        try:
            assert observer.is_alive()
        finally:
            observer.stop()
            observer.join(timeout=2.0)

    def test_debounced_handler_schedules_rebuild_on_modified(self):
        """When the target file is modified, callback is scheduled and runs after debounce."""
        callback_invoked = threading.Event()
        call_count = [0]

        def on_rebuild():
            call_count[0] += 1
            callback_invoked.set()

        handler = _DebouncedHandler(EXCEL_PATH, on_rebuild, debounce_seconds=0.03)
        event = _make_event(str(EXCEL_PATH.resolve()))
        handler.on_modified(event)
        # Wait for debounce timer to fire
        callback_invoked.wait(timeout=1.0)
        assert call_count[0] >= 1

    def test_debounced_handler_ignores_other_files(self):
        """Events for other paths do not trigger the callback."""
        callback_invoked = threading.Event()

        def on_rebuild():
            callback_invoked.set()

        handler = _DebouncedHandler(EXCEL_PATH, on_rebuild, debounce_seconds=0.02)
        other_path = EXCEL_PATH.parent / "other_file.xlsx"
        event = _make_event(str(other_path.resolve()))
        handler.on_modified(event)
        # Callback should not run (we don't wait long enough for a stray timer)
        time.sleep(0.1)
        assert not callback_invoked.is_set()

    def test_debounced_handler_ignores_directory_events(self):
        """Directory events are ignored."""
        callback_invoked = threading.Event()

        def on_rebuild():
            callback_invoked.set()

        handler = _DebouncedHandler(EXCEL_PATH, on_rebuild, debounce_seconds=0.02)
        event = _make_event(str(EXCEL_PATH.resolve()), is_directory=True)
        handler.on_modified(event)
        time.sleep(0.1)
        assert not callback_invoked.is_set()
