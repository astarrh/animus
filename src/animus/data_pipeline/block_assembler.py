"""Tier 2: Compute building blocks from raw Excel data.

Sums axis-pole contributions into MBTI types, element+modality+tweak
contributions into astrological signs, normalizes coefficients, and
produces a BuildingBlockLibrary.
"""

from __future__ import annotations

from animus.building_blocks import AstrologicalSign, BuildingBlockLibrary, MBTIType
from animus.data_pipeline.excel_parser import RawExcelData
from animus.models import (
    AppraisalVector,
    BehavioralVector,
    MoodVector,
    TransformationMatrix,
)

# ---------------------------------------------------------------------------
# MBTI type compositions: which 4 poles compose each type
# ---------------------------------------------------------------------------

MBTI_TYPE_POLES: dict[str, tuple[str, str, str, str]] = {
    "INTJ": ("I", "N", "T", "J"),
    "ENTJ": ("E", "N", "T", "J"),
    "INTP": ("I", "N", "T", "P"),
    "ENTP": ("E", "N", "T", "P"),
    "INFJ": ("I", "N", "F", "J"),
    "ENFJ": ("E", "N", "F", "J"),
    "INFP": ("I", "N", "F", "P"),
    "ENFP": ("E", "N", "F", "P"),
    "ISTJ": ("I", "S", "T", "J"),
    "ESTJ": ("E", "S", "T", "J"),
    "ISTP": ("I", "S", "T", "P"),
    "ESTP": ("E", "S", "T", "P"),
    "ISFJ": ("I", "S", "F", "J"),
    "ESFJ": ("E", "S", "F", "J"),
    "ISFP": ("I", "S", "F", "P"),
    "ESFP": ("E", "S", "F", "P"),
}

# ---------------------------------------------------------------------------
# Sign compositions: which element + modality compose each sign
# ---------------------------------------------------------------------------

SIGN_COMPONENTS: dict[str, tuple[str, str]] = {
    "Aries": ("Fire", "Cardinal"),
    "Taurus": ("Earth", "Fixed"),
    "Gemini": ("Air", "Mutable"),
    "Cancer": ("Water", "Cardinal"),
    "Leo": ("Fire", "Fixed"),
    "Virgo": ("Earth", "Mutable"),
    "Libra": ("Air", "Cardinal"),
    "Scorpio": ("Water", "Fixed"),
    "Sagittarius": ("Fire", "Mutable"),
    "Capricorn": ("Earth", "Cardinal"),
    "Aquarius": ("Air", "Fixed"),
    "Pisces": ("Water", "Mutable"),
}

# ---------------------------------------------------------------------------
# Normalization constants
# ---------------------------------------------------------------------------

_MBTI_COEFF_DIVISOR = 4.0
_SIGN_COEFF_DIVISOR = 2.0
_MBTI_APPRAISAL_DIVISOR = 4.0
_SIGN_APPRAISAL_DIVISOR = 2.0


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def assemble(raw: RawExcelData) -> BuildingBlockLibrary:
    """Build all 28 building blocks from raw Excel data."""
    mbti_types = _assemble_mbti_types(raw)
    signs = _assemble_signs(raw)
    return BuildingBlockLibrary(mbti_types=mbti_types, signs=signs)


def compute_mbti_raw_sums(raw: RawExcelData) -> dict[str, dict[str, float]]:
    """Compute pre-normalization scalar sums for all 16 MBTI types.

    Used for validation against Sheet 3 reference values.
    """
    result = {}
    for type_name, poles in MBTI_TYPE_POLES.items():
        sums: dict[str, float] = {}
        for coeff_name in ("assertiveness", "susceptibility", "rigidity", "rumination",
                           "control", "certainty"):
            sums[coeff_name] = sum(
                raw.mbti_axes.poles[coeff_name][p] for p in poles
            )
        result[type_name] = sums
    return result


def compute_sign_raw_sums(raw: RawExcelData) -> dict[str, dict[str, float]]:
    """Compute pre-normalization scalar sums for all 12 signs.

    Used for validation against Sheet 4 reference values.
    """
    result = {}
    for sign_name, (element, modality) in SIGN_COMPONENTS.items():
        sums: dict[str, float] = {}
        for coeff_name in ("assertiveness", "susceptibility", "rigidity", "rumination",
                           "control", "certainty"):
            sums[coeff_name] = (
                raw.astrology.elements[element][coeff_name]
                + raw.astrology.modalities[modality][coeff_name]
                + raw.astrology.tweaks[sign_name][coeff_name]
            )
        result[sign_name] = sums
    return result


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _normalize_coeff(raw: float, divisor: float) -> float:
    """Normalize a coefficient to [0.0, 1.0]."""
    return max(0.0, min(1.0, raw / divisor))


def _normalize_appraisal(raw: float, divisor: float) -> float:
    """Normalize an appraisal value to [-1.0, 1.0]."""
    return max(-1.0, min(1.0, raw / divisor))


def _sum_matrices(matrices: list[list[list[float]]]) -> list[list[float]]:
    """Sum a list of 5x5 matrices element-wise."""
    result = [[0.0] * 5 for _ in range(5)]
    for m in matrices:
        for i in range(5):
            for j in range(5):
                result[i][j] += m[i][j]
    return result


def _sum_vectors(vectors: list[list[float]]) -> list[float]:
    """Sum a list of vectors element-wise."""
    n = len(vectors[0])
    return [sum(v[i] for v in vectors) for i in range(n)]


def _matrix_to_transformation(matrix: list[list[float]]) -> TransformationMatrix:
    """Convert a list-of-lists matrix to a TransformationMatrix."""
    return TransformationMatrix(rows=tuple(tuple(row) for row in matrix))


def _assemble_mbti_types(raw: RawExcelData) -> dict[str, MBTIType]:
    """Assemble all 16 MBTI type building blocks."""
    result = {}
    for type_name, poles in MBTI_TYPE_POLES.items():
        # Sum scalar coefficients
        raw_sums: dict[str, float] = {}
        for coeff in ("assertiveness", "susceptibility", "rigidity", "rumination",
                      "control", "certainty"):
            raw_sums[coeff] = sum(raw.mbti_axes.poles[coeff][p] for p in poles)

        # Sum matrix contributions
        matrix = _sum_matrices([raw.mbti_matrices.matrices[p] for p in poles])

        # Sum baseline and mood contributions
        baseline = _sum_vectors([raw.mbti_baselines.behavioral_baselines[p] for p in poles])
        mood = _sum_vectors([raw.mbti_baselines.resting_moods[p] for p in poles])

        # Normalize scalar coefficients
        assertiveness = _normalize_coeff(raw_sums["assertiveness"], _MBTI_COEFF_DIVISOR)
        susceptibility = _normalize_coeff(raw_sums["susceptibility"], _MBTI_COEFF_DIVISOR)
        rigidity = _normalize_coeff(raw_sums["rigidity"], _MBTI_COEFF_DIVISOR)
        rumination = _normalize_coeff(raw_sums["rumination"], _MBTI_COEFF_DIVISOR)
        control = _normalize_appraisal(raw_sums["control"], _MBTI_APPRAISAL_DIVISOR)
        certainty = _normalize_appraisal(raw_sums["certainty"], _MBTI_APPRAISAL_DIVISOR)

        result[type_name] = MBTIType(
            name=type_name,
            transform_matrix=_matrix_to_transformation(matrix),
            appraisal_baseline=AppraisalVector(control=control, certainty=certainty),
            susceptibility=susceptibility,
            rigidity=rigidity,
            rumination=rumination,
            assertiveness=assertiveness,
            behavioral_baseline=BehavioralVector.from_list(baseline),
            resting_mood=MoodVector.from_list(mood),
        )

    return result


def _assemble_signs(raw: RawExcelData) -> dict[str, AstrologicalSign]:
    """Assemble all 12 astrological sign building blocks."""
    result = {}
    for sign_name, (element, modality) in SIGN_COMPONENTS.items():
        # Sum scalar coefficients
        raw_sums: dict[str, float] = {}
        for coeff in ("assertiveness", "susceptibility", "rigidity", "rumination",
                      "control", "certainty"):
            raw_sums[coeff] = (
                raw.astrology.elements[element][coeff]
                + raw.astrology.modalities[modality][coeff]
                + raw.astrology.tweaks[sign_name][coeff]
            )

        # Sum matrix contributions
        matrix = _sum_matrices([
            raw.astro_matrices.elements[element],
            raw.astro_matrices.modalities[modality],
            raw.astro_matrices.tweaks[sign_name],
        ])

        # Sum baseline contributions
        baseline = _sum_vectors([
            raw.astro_baselines.element_baselines[element],
            raw.astro_baselines.modality_baselines[modality],
            raw.astro_baselines.tweak_baselines[sign_name],
        ])

        # Sum mood contributions
        mood = _sum_vectors([
            raw.astro_baselines.element_moods[element],
            raw.astro_baselines.modality_moods[modality],
            raw.astro_baselines.tweak_moods[sign_name],
        ])

        # Normalize scalar coefficients
        assertiveness = _normalize_coeff(raw_sums["assertiveness"], _SIGN_COEFF_DIVISOR)
        susceptibility = _normalize_coeff(raw_sums["susceptibility"], _SIGN_COEFF_DIVISOR)
        rigidity = _normalize_coeff(raw_sums["rigidity"], _SIGN_COEFF_DIVISOR)
        rumination = _normalize_coeff(raw_sums["rumination"], _SIGN_COEFF_DIVISOR)
        control = _normalize_appraisal(raw_sums["control"], _SIGN_APPRAISAL_DIVISOR)
        certainty = _normalize_appraisal(raw_sums["certainty"], _SIGN_APPRAISAL_DIVISOR)

        result[sign_name] = AstrologicalSign(
            name=sign_name,
            transform_matrix=_matrix_to_transformation(matrix),
            appraisal_baseline=AppraisalVector(control=control, certainty=certainty),
            susceptibility=susceptibility,
            rigidity=rigidity,
            rumination=rumination,
            assertiveness=assertiveness,
            behavioral_baseline=BehavioralVector.from_list(baseline),
            resting_mood=MoodVector.from_list(mood),
        )

    return result
