"""Load personality building blocks from JSON (canonical) or deprecated Excel."""

from __future__ import annotations

from pathlib import Path

from animus.data_pipeline.excel_parser import DEFAULT_EXCEL_PATH, RawExcelData, parse_excel
from animus.data_pipeline.json_parser import DEFAULT_JSON_PATH, parse_json

DEFAULT_BUILDING_BLOCKS_PATH = DEFAULT_JSON_PATH


def load_building_blocks(path: Path | str | None = None) -> RawExcelData:
    """Load raw building-block data from a JSON or Excel file.

    If ``path`` is omitted, loads the packaged default JSON
    (``docs/personality_building_blocks.json``). Games can pass their own
    override file to replace the defaults entirely.

    Excel (``.xlsx``) remains readable for legacy files but is deprecated as an
    authoring format — prefer JSON.
    """
    if path is None:
        path = DEFAULT_BUILDING_BLOCKS_PATH
    path = Path(path)

    suffix = path.suffix.lower()
    if suffix == ".json":
        return parse_json(path)
    if suffix in {".xlsx", ".xlsm", ".xltx", ".xltm"}:
        return parse_excel(path)
    raise ValueError(
        f"Unsupported building-blocks file type {path.suffix!r}; use .json"
    )


def default_building_blocks_path() -> Path:
    """Return the default JSON path if present, else the legacy Excel path."""
    if DEFAULT_JSON_PATH.exists():
        return DEFAULT_JSON_PATH
    return DEFAULT_EXCEL_PATH
