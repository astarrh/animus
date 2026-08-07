"""Parse personality building-block JSON into RawExcelData.

JSON is the preferred authoring format. The schema is versioned
(`format: animus.building_blocks`) and organized per component so browser
editors and game overrides stay readable.
"""

from __future__ import annotations

import json
from pathlib import Path

from animus.data import building_blocks_json_dict, building_blocks_json_path
from animus.data_pipeline.excel_parser import (
    RawAstroBaselineComponents,
    RawAstrologyComponents,
    RawAstroMatrixComponents,
    RawExcelData,
    RawMBTIAxes,
    RawMBTIBaselineComponents,
    RawMBTIMatrixComponents,
)

# Packaged default — present after ``pip install``, not only in a git checkout.
DEFAULT_JSON_PATH = building_blocks_json_path()

SCALAR_KEYS = (
    "assertiveness",
    "susceptibility",
    "rigidity",
    "rumination",
    "control",
    "certainty",
)


def parse_json(path: Path | None = None) -> RawExcelData:
    """Load building-block JSON and return the same structure as parse_excel().

    With no ``path``, loads the packaged defaults via ``importlib.resources``
    so installs that are not on a normal filesystem still work.
    """
    if path is None:
        return raw_from_dict(building_blocks_json_dict())
    with Path(path).open(encoding="utf-8") as f:
        data = json.load(f)
    return raw_from_dict(data)


def raw_from_dict(data: dict) -> RawExcelData:
    """Convert a building-blocks dict into RawExcelData."""
    fmt = data.get("format")
    if fmt != "animus.building_blocks":
        raise ValueError(
            f"Unsupported JSON format {fmt!r}; expected 'animus.building_blocks'"
        )
    version = data.get("version")
    if version != 1:
        raise ValueError(f"Unsupported building-blocks version {version!r}; expected 1")

    mbti_poles = data["mbti_poles"]
    astrology = data["astrology"]

    return RawExcelData(
        mbti_axes=_mbti_axes(mbti_poles),
        mbti_matrices=RawMBTIMatrixComponents(
            matrices={pole: _matrix(block["matrix"]) for pole, block in mbti_poles.items()},
        ),
        mbti_baselines=RawMBTIBaselineComponents(
            behavioral_baselines={
                pole: list(block["behavioral_baseline"]) for pole, block in mbti_poles.items()
            },
            resting_moods={
                pole: list(block["resting_mood"]) for pole, block in mbti_poles.items()
            },
        ),
        astrology=RawAstrologyComponents(
            elements=_scalars_map(astrology["elements"]),
            modalities=_scalars_map(astrology["modalities"]),
            tweaks=_scalars_map(astrology["sign_tweaks"]),
        ),
        astro_matrices=RawAstroMatrixComponents(
            elements={
                name: _matrix(block["matrix"]) for name, block in astrology["elements"].items()
            },
            modalities={
                name: _matrix(block["matrix"])
                for name, block in astrology["modalities"].items()
            },
            tweaks={
                name: _matrix(block["matrix"])
                for name, block in astrology["sign_tweaks"].items()
            },
        ),
        astro_baselines=RawAstroBaselineComponents(
            element_baselines=_vector_map(astrology["elements"], "behavioral_baseline"),
            element_moods=_vector_map(astrology["elements"], "resting_mood"),
            modality_baselines=_vector_map(astrology["modalities"], "behavioral_baseline"),
            modality_moods=_vector_map(astrology["modalities"], "resting_mood"),
            tweak_baselines=_vector_map(astrology["sign_tweaks"], "behavioral_baseline"),
            tweak_moods=_vector_map(astrology["sign_tweaks"], "resting_mood"),
        ),
    )


def _mbti_axes(mbti_poles: dict) -> RawMBTIAxes:
    """Transpose per-pole scalars into coeff → pole → value (engine layout)."""
    poles: dict[str, dict[str, float]] = {key: {} for key in SCALAR_KEYS}
    for pole, block in mbti_poles.items():
        scalars = block["scalars"]
        for key in SCALAR_KEYS:
            poles[key][pole] = float(scalars[key])
    return RawMBTIAxes(poles=poles)


def _scalars_map(components: dict) -> dict[str, dict[str, float]]:
    return {
        name: {key: float(block["scalars"][key]) for key in SCALAR_KEYS}
        for name, block in components.items()
    }


def _vector_map(components: dict, field: str) -> dict[str, list[float]]:
    return {name: [float(v) for v in block[field]] for name, block in components.items()}


def _matrix(rows: list) -> list[list[float]]:
    matrix = [[float(v) for v in row] for row in rows]
    if len(matrix) != 5 or any(len(row) != 5 for row in matrix):
        raise ValueError("Each transformation matrix must be 5x5")
    return matrix
