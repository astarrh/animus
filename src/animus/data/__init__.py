"""Packaged default building-block data.

The canonical coefficient file ships inside the installed ``animus`` package so
``load_building_blocks()`` works after ``pip install``, not only from a git
checkout.
"""

from __future__ import annotations

import json
from importlib import resources
from pathlib import Path


def building_blocks_json_text() -> str:
    """Return the shipped building-blocks JSON as text."""
    return (
        resources.files(__name__)
        .joinpath("personality_building_blocks.json")
        .read_text(encoding="utf-8")
    )


def building_blocks_json_dict() -> dict:
    """Return the shipped building-blocks JSON as a dict."""
    return json.loads(building_blocks_json_text())


def building_blocks_json_path() -> Path:
    """Return the expected filesystem path to the shipped JSON.

    Normal wheel and editable installs keep this file on disk next to this
    module. For zipimport / unusual installs prefer
    :func:`building_blocks_json_text` or ``load_building_blocks()`` with no
    path (those use ``importlib.resources`` and do not require a real path).
    """
    return Path(__file__).resolve().parent / "personality_building_blocks.json"
