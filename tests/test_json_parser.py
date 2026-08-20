"""Tests for JSON building-block loading and Excel parity."""

from pathlib import Path

import pytest

from animus.data import building_blocks_json_path
from animus.data_pipeline.block_assembler import assemble
from animus.data_pipeline.excel_parser import parse_excel
from animus.data_pipeline.json_parser import DEFAULT_JSON_PATH, parse_json
from animus.data_pipeline.loader import default_building_blocks_path, load_building_blocks

EXCEL_PATH = Path(__file__).parent.parent / "docs" / "personality_building_blocks.xlsx"


@pytest.fixture(scope="module")
def json_raw():
    return parse_json()


class TestJsonParser:
    def test_format_and_poles(self, json_raw):
        assert set(json_raw.mbti_matrices.matrices) == set("EISTNFJP")
        assert set(json_raw.astrology.elements) == {"Fire", "Earth", "Air", "Water"}
        assert len(json_raw.astrology.tweaks) == 12

    def test_matrices_are_5x5(self, json_raw):
        for matrix in json_raw.mbti_matrices.matrices.values():
            assert len(matrix) == 5
            assert all(len(row) == 5 for row in matrix)

    def test_default_path_is_packaged(self):
        path = building_blocks_json_path()
        assert path.is_file()
        assert path.name == "personality_building_blocks.json"
        assert "animus" in path.parts
        assert path.parent.name == "data"
        assert DEFAULT_JSON_PATH == path
        assert default_building_blocks_path() == path

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

    def test_packaged_defaults_are_version_2(self):
        import json
        from animus.data import building_blocks_json_dict

        assert building_blocks_json_dict()["version"] == 2

    def test_version_1_still_parses(self, tmp_path):
        import json
        from animus.data import building_blocks_json_dict

        data = building_blocks_json_dict()
        data["version"] = 1
        path = tmp_path / "v1.json"
        path.write_text(json.dumps(data))
        raw = parse_json(path)
        assert "INTJ" not in raw.mbti_axes.poles["susceptibility"]  # poles keyed by letter
        assert "T" in raw.mbti_axes.poles["susceptibility"]

    def test_unsupported_version_rejected(self, tmp_path):
        path = tmp_path / "v3.json"
        path.write_text('{"version": 3, "format": "animus.building_blocks"}')
        with pytest.raises(ValueError, match="Unsupported building-blocks version"):
            parse_json(path)


@pytest.mark.skip(reason="Excel authoring pipeline deprecated; JSON is canonical")
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
