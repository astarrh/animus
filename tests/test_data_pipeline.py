"""Tests for the data pipeline: Excel parsing, block assembly, and validation."""

from pathlib import Path

import pytest

from animus.data_pipeline.excel_parser import (
    parse_excel,
    parse_reference_mbti,
    parse_reference_signs,
)
from animus.data_pipeline.block_assembler import (
    assemble,
    compute_mbti_raw_sums,
    compute_sign_raw_sums,
    MBTI_TYPE_POLES,
    SIGN_COMPONENTS,
)

EXCEL_PATH = Path(__file__).parent.parent / "docs" / "personality_building_blocks.xlsx"

pytestmark = pytest.mark.skipif(
    not EXCEL_PATH.exists(),
    reason="Excel file docs/personality_building_blocks.xlsx not found",
)


@pytest.fixture(scope="module")
def raw_data():
    return parse_excel(EXCEL_PATH)


@pytest.fixture(scope="module")
def library(raw_data):
    return assemble(raw_data)


# ============================================================================
# Tier 1: Excel Parser Tests
# ============================================================================

class TestExcelParser:
    """Verify the parser reads all expected data from the Excel file."""

    def test_reads_all_8_poles_per_coefficient(self, raw_data):
        expected_poles = {"E", "I", "S", "N", "T", "F", "J", "P"}
        for coeff in ("assertiveness", "susceptibility", "rigidity", "rumination",
                      "control", "certainty"):
            assert coeff in raw_data.mbti_axes.poles
            assert set(raw_data.mbti_axes.poles[coeff].keys()) == expected_poles

    def test_reads_4_elements(self, raw_data):
        assert set(raw_data.astrology.elements.keys()) == {"Fire", "Earth", "Air", "Water"}

    def test_reads_3_modalities(self, raw_data):
        assert set(raw_data.astrology.modalities.keys()) == {"Cardinal", "Fixed", "Mutable"}

    def test_reads_12_sign_tweaks(self, raw_data):
        expected_signs = set(SIGN_COMPONENTS.keys())
        assert set(raw_data.astrology.tweaks.keys()) == expected_signs

    def test_element_has_all_coefficients(self, raw_data):
        expected_keys = {"assertiveness", "susceptibility", "rigidity",
                         "rumination", "control", "certainty"}
        for element in raw_data.astrology.elements.values():
            assert set(element.keys()) == expected_keys

    def test_reads_mbti_matrix_components(self, raw_data):
        expected_poles = {"E", "I", "S", "N", "T", "F", "J", "P"}
        assert set(raw_data.mbti_matrices.matrices.keys()) == expected_poles
        for matrix in raw_data.mbti_matrices.matrices.values():
            assert len(matrix) == 5
            for row in matrix:
                assert len(row) == 5

    def test_reads_mbti_baseline_components(self, raw_data):
        expected_poles = {"E", "I", "S", "N", "T", "F", "J", "P"}
        assert set(raw_data.mbti_baselines.behavioral_baselines.keys()) == expected_poles
        assert set(raw_data.mbti_baselines.resting_moods.keys()) == expected_poles
        for baseline in raw_data.mbti_baselines.behavioral_baselines.values():
            assert len(baseline) == 5
        for mood in raw_data.mbti_baselines.resting_moods.values():
            assert len(mood) == 5

    def test_reads_astro_matrix_components(self, raw_data):
        assert set(raw_data.astro_matrices.elements.keys()) == {"Fire", "Earth", "Air", "Water"}
        assert set(raw_data.astro_matrices.modalities.keys()) == {"Cardinal", "Fixed", "Mutable"}
        assert set(raw_data.astro_matrices.tweaks.keys()) == set(SIGN_COMPONENTS.keys())
        for matrices in (raw_data.astro_matrices.elements,
                         raw_data.astro_matrices.modalities,
                         raw_data.astro_matrices.tweaks):
            for matrix in matrices.values():
                assert len(matrix) == 5
                for row in matrix:
                    assert len(row) == 5

    def test_reads_astro_baseline_components(self, raw_data):
        assert set(raw_data.astro_baselines.element_baselines.keys()) == {"Fire", "Earth", "Air", "Water"}
        assert set(raw_data.astro_baselines.element_moods.keys()) == {"Fire", "Earth", "Air", "Water"}
        assert set(raw_data.astro_baselines.modality_baselines.keys()) == {"Cardinal", "Fixed", "Mutable"}
        assert set(raw_data.astro_baselines.modality_moods.keys()) == {"Cardinal", "Fixed", "Mutable"}
        assert set(raw_data.astro_baselines.tweak_baselines.keys()) == set(SIGN_COMPONENTS.keys())
        assert set(raw_data.astro_baselines.tweak_moods.keys()) == set(SIGN_COMPONENTS.keys())


# ============================================================================
# Tier 2: Block Assembler Tests
# ============================================================================

class TestBlockAssembler:
    """Verify computed sums match reference values and blocks are well-formed."""

    def test_all_16_mbti_sums_match_sheet3(self, raw_data):
        """Validate all 16 type sums against Sheet 3 reference."""
        computed = compute_mbti_raw_sums(raw_data)
        reference = parse_reference_mbti(EXCEL_PATH)

        for type_name in MBTI_TYPE_POLES:
            assert type_name in computed, f"{type_name} missing from computed"
            assert type_name in reference, f"{type_name} missing from reference"
            for coeff in ("assertiveness", "susceptibility", "rigidity",
                          "rumination", "control", "certainty"):
                assert abs(computed[type_name][coeff] - reference[type_name][coeff]) < 0.001, (
                    f"{type_name}.{coeff}: computed={computed[type_name][coeff]:.3f}, "
                    f"reference={reference[type_name][coeff]:.3f}"
                )

    def test_all_12_sign_sums_match_sheet4(self, raw_data):
        """Validate all 12 sign sums against Sheet 4 reference."""
        computed = compute_sign_raw_sums(raw_data)
        reference = parse_reference_signs(EXCEL_PATH)

        for sign_name in SIGN_COMPONENTS:
            assert sign_name in computed, f"{sign_name} missing from computed"
            assert sign_name in reference, f"{sign_name} missing from reference"
            for coeff in ("assertiveness", "susceptibility", "rigidity",
                          "rumination", "control", "certainty"):
                assert abs(computed[sign_name][coeff] - reference[sign_name][coeff]) < 0.001, (
                    f"{sign_name}.{coeff}: computed={computed[sign_name][coeff]:.3f}, "
                    f"reference={reference[sign_name][coeff]:.3f}"
                )

    def test_intj_raw_sums_match_phase1(self, raw_data):
        """Verify INTJ sums match the Phase 1 hardcoded _INTJ_RAW values."""
        computed = compute_mbti_raw_sums(raw_data)
        intj = computed["INTJ"]
        assert abs(intj["assertiveness"] - 2.00) < 0.001
        assert abs(intj["susceptibility"] - 1.65) < 0.001
        assert abs(intj["rigidity"] - 2.20) < 0.001
        assert abs(intj["rumination"] - 1.95) < 0.001
        assert abs(intj["control"] - 0.25) < 0.001
        assert abs(intj["certainty"] - 0.15) < 0.001

    def test_capricorn_raw_sums_match_phase1(self, raw_data):
        """Verify Capricorn sums match the Phase 1 hardcoded _CAP_RAW values."""
        computed = compute_sign_raw_sums(raw_data)
        cap = computed["Capricorn"]
        assert abs(cap["assertiveness"] - 1.05) < 0.001
        assert abs(cap["susceptibility"] - 0.70) < 0.001
        assert abs(cap["rigidity"] - 1.10) < 0.001
        assert abs(cap["rumination"] - 0.90) < 0.001
        assert abs(cap["control"] - 0.30) < 0.001
        assert abs(cap["certainty"] - 0.30) < 0.001

    def test_assemble_produces_28_blocks(self, library):
        assert len(library.mbti_types) == 16
        assert len(library.signs) == 12

    def test_normalization_range_coefficients(self, library):
        """All normalized coefficients must be in [0, 1]."""
        for mb in library.mbti_types.values():
            for val in (mb.susceptibility, mb.rigidity, mb.rumination, mb.assertiveness):
                assert 0.0 <= val <= 1.0, f"{mb.name}: coefficient {val} out of range"
        for sign in library.signs.values():
            for val in (sign.susceptibility, sign.rigidity, sign.rumination, sign.assertiveness):
                assert 0.0 <= val <= 1.0, f"{sign.name}: coefficient {val} out of range"

    def test_normalization_range_appraisals(self, library):
        """All normalized appraisals must be in [-1, 1]."""
        for mb in library.mbti_types.values():
            assert -1.0 <= mb.appraisal_baseline.control <= 1.0
            assert -1.0 <= mb.appraisal_baseline.certainty <= 1.0
        for sign in library.signs.values():
            assert -1.0 <= sign.appraisal_baseline.control <= 1.0
            assert -1.0 <= sign.appraisal_baseline.certainty <= 1.0

    def test_mbti_types_have_valid_matrices(self, library):
        """All MBTI types have 5x5 transformation matrices."""
        for mb in library.mbti_types.values():
            assert len(mb.transform_matrix.rows) == 5
            for row in mb.transform_matrix.rows:
                assert len(row) == 5

    def test_signs_have_valid_matrices(self, library):
        """All signs have 5x5 transformation matrices."""
        for sign in library.signs.values():
            assert len(sign.transform_matrix.rows) == 5
            for row in sign.transform_matrix.rows:
                assert len(row) == 5
