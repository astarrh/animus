"""Export all 192 packaged-default character cards as JSON.

Usage::

    python -m animus.tools.export_character_cards --output cards.json
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from animus.composite import generate_all_composites
from animus.data_pipeline import assemble, load_building_blocks
from animus.designer import compute_scalar_bounds
from animus.envelope import character_card


def export_character_cards(output: Path) -> None:
    composites = generate_all_composites(assemble(load_building_blocks()))
    bounds = compute_scalar_bounds(composites)
    cards = {
        f"{mbti}_{sign}": character_card(profile, bounds)
        for (mbti, sign), profile in composites.items()
    }
    output.write_text(json.dumps(cards, indent=2), encoding="utf-8")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Export Animus character cards for the packaged default library.",
    )
    parser.add_argument(
        "--output",
        "-o",
        type=Path,
        default=Path("character_cards.json"),
        help="JSON file to write (default: character_cards.json)",
    )
    args = parser.parse_args(argv)
    export_character_cards(args.output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
