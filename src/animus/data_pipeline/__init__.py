"""Data pipeline for personality building blocks (JSON preferred, Excel supported)."""

from animus.data_pipeline.loader import (
    DEFAULT_BUILDING_BLOCKS_PATH,
    default_building_blocks_path,
    load_building_blocks,
)
from animus.data_pipeline.json_parser import DEFAULT_JSON_PATH, parse_json
from animus.data_pipeline.excel_parser import DEFAULT_EXCEL_PATH, parse_excel
from animus.data_pipeline.block_assembler import assemble

__all__ = [
    "DEFAULT_BUILDING_BLOCKS_PATH",
    "DEFAULT_EXCEL_PATH",
    "DEFAULT_JSON_PATH",
    "assemble",
    "default_building_blocks_path",
    "load_building_blocks",
    "parse_excel",
    "parse_json",
]


def __getattr__(name: str):
    """Lazy-export start_watcher so watchdog stays an optional dev dependency."""
    if name == "start_watcher":
        from animus.data_pipeline.hot_reload import start_watcher

        return start_watcher
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
