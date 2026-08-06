#!/usr/bin/env python3
"""Export Excel building blocks to the versioned JSON authoring format.

Usage:
  PYTHONPATH=src python scripts/export_building_blocks_json.py
  PYTHONPATH=src python scripts/export_building_blocks_json.py --excel docs/foo.xlsx --out docs/foo.json
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from animus.data_pipeline.excel_parser import DEFAULT_EXCEL_PATH, parse_excel
from animus.data_pipeline.json_parser import DEFAULT_JSON_PATH, SCALAR_KEYS

POLES = ("E", "I", "S", "N", "T", "F", "J", "P")
ELEMENTS = ("Fire", "Earth", "Air", "Water")
MODALITIES = ("Cardinal", "Fixed", "Mutable")


def export_dict(raw) -> dict:
    mbti_poles = {}
    for pole in POLES:
        mbti_poles[pole] = {
            "scalars": {key: raw.mbti_axes.poles[key][pole] for key in SCALAR_KEYS},
            "behavioral_baseline": list(raw.mbti_baselines.behavioral_baselines[pole]),
            "resting_mood": list(raw.mbti_baselines.resting_moods[pole]),
            "matrix": [list(row) for row in raw.mbti_matrices.matrices[pole]],
        }

    def pack(names, scalars, matrices, baselines, moods):
        return {
            name: {
                "scalars": dict(scalars[name]),
                "behavioral_baseline": list(baselines[name]),
                "resting_mood": list(moods[name]),
                "matrix": [list(row) for row in matrices[name]],
            }
            for name in names
        }

    return {
        "version": 1,
        "format": "animus.building_blocks",
        "dimensions": {
            "behavioral": [
                "aggression_passivity",
                "impulsiveness_deliberation",
                "sociability_withdrawal",
                "empathy_self_interest",
                "curiosity_avoidance",
            ],
            "mood": [
                "distress_contentment",
                "fear_confidence",
                "isolation_belonging",
                "shame_pride",
                "arousal",
            ],
            "scalars": list(SCALAR_KEYS),
            "matrix_rows": [
                "aggression",
                "impulsiveness",
                "sociability",
                "empathy",
                "curiosity",
            ],
            "matrix_cols": [
                "distress_contentment",
                "fear_confidence",
                "isolation_belonging",
                "shame_pride",
                "arousal",
            ],
        },
        "mbti_poles": mbti_poles,
        "astrology": {
            "elements": pack(
                ELEMENTS,
                raw.astrology.elements,
                raw.astro_matrices.elements,
                raw.astro_baselines.element_baselines,
                raw.astro_baselines.element_moods,
            ),
            "modalities": pack(
                MODALITIES,
                raw.astrology.modalities,
                raw.astro_matrices.modalities,
                raw.astro_baselines.modality_baselines,
                raw.astro_baselines.modality_moods,
            ),
            "sign_tweaks": pack(
                list(raw.astrology.tweaks.keys()),
                raw.astrology.tweaks,
                raw.astro_matrices.tweaks,
                raw.astro_baselines.tweak_baselines,
                raw.astro_baselines.tweak_moods,
            ),
        },
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--excel", type=Path, default=DEFAULT_EXCEL_PATH)
    parser.add_argument("--out", type=Path, default=DEFAULT_JSON_PATH)
    args = parser.parse_args()

    raw = parse_excel(args.excel)
    args.out.parent.mkdir(parents=True, exist_ok=True)
    args.out.write_text(json.dumps(export_dict(raw), indent=2) + "\n", encoding="utf-8")
    print(f"Wrote {args.out}")


if __name__ == "__main__":
    main()
