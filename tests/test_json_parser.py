"""Tests for JSON building-block loading and Excel parity."""

from pathlib import Path

import pytest

from animus.data_pipeline.block_assembler import assemble
from animus.data_pipeline.excel_parser import parse_excel
from animus.data_pipeline.json_parser import parse_json
from animus.data_pipeline.loader import load_building_blocks

ROOT = Path(__file__).parent.parent
JSON_PATH = ROOT / "docs" / "personality_building_blocks.json"
EXCEL_PATH = ROOT / "docs" / "personality_building_blocks.xlsx"

pytestmark = pytest.mark.skipif(
    not JSON_PATH.exists(),
    reason="JSON file docs/personality_building_blocks.json not found",
)


@pytest.fixture(scope="module")
def json_raw():
    return parse_json(JSON_PATH)


class TestJsonParser:
    def test_format_and_poles(self, json_raw):
        assert set(json_raw.mbti_matrices.matrices) == set("EISTNFJP")
        assert set(json_raw.astrology.elements) == {"Fire", "Earth", "Air", "Water"}
        assert len(json_raw.astrology.tweaks) == 12

    def test_matrices_are_5x5(self, json_raw):
        for matrix in json_raw.mbti_matrices.matrices.values():
            assert len(matrix) == 5
            assert all(len(row) == 5 for row in matrix)

    def test_loader_defaults_to_json(self):
        raw = load_building_blocks()
        lib = assemble(raw)
        assert len(lib.mbti_types) == 16
        assert len(lib.signs) == 12

    def test_loader_rejects_unknown_suffix(self, tmp_path):
        path = tmp_path / "blocks.txt"
        path.write_text("nope")
        with pytest.raises(ValueError, match="Unsupported"):
            load_building_blocks(path)

    def test_invalid_format_rejected(self, tmp_path):
        path = tmp_path / "bad.json"
        path.write_text('{"version": 1, "format": "other"}')
        with pytest.raises(ValueError, match="Unsupported JSON format"):
            parse_json(path)


@pytest.mark.skipif(not EXCEL_PATH.exists(), reason="Excel file not found")
class TestJsonExcelParity:
    def test_assembled_libraries_match(self, json_raw):
        excel_raw = parse_excel(EXCEL_PATH)
        json_lib = assemble(json_raw)
        excel_lib = assemble(excel_raw)

        for name, mb in json_lib.mbti_types.items():
            other = excel_lib.mbti_types[name]
            assert mb.susceptibility == pytest.approx(other.susceptibility, abs=1e-9)
            assert mb.behavioral_baseline.to_list() == pytest.approx(
                other.behavioral_baseline.to_list(), abs=1e-9
            )
            for i in range(5):
                assert mb.transform_matrix.rows[i] == pytest.approx(
                    other.transform_matrix.rows[i], abs=1e-9
                )

        for name, sign in json_lib.signs.items():
            other = excel_lib.signs[name]
            assert sign.rumination == pytest.approx(other.rumination, abs=1e-9)
            assert sign.resting_mood.to_list() == pytest.approx(
                other.resting_mood.to_list(), abs=1e-9
            )
