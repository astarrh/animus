"""Tests for reference behavioral envelopes (Phase 2)."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from animus.composite import generate_all_composites
from animus.data_pipeline import assemble, load_building_blocks
from animus.designer import compute_scalar_bounds
from animus.envelope import (
    BEHAVIORAL_AXES,
    REFERENCE_SITUATIONS,
    compute_all_envelopes,
    compute_envelope,
    character_card,
    probe_situation,
)
from animus.tools.export_character_cards import export_character_cards


@pytest.fixture(scope="module")
def all_composites():
    return generate_all_composites(assemble(load_building_blocks()))


@pytest.fixture(scope="module")
def bounds(all_composites):
    return compute_scalar_bounds(all_composites)


# ---------------------------------------------------------------------------
# Reference ladder
# ---------------------------------------------------------------------------

class TestReferenceSituations:
    def test_ladder_names_and_order(self):
        names = [sit.name for sit in REFERENCE_SITUATIONS]
        assert names == [
            "resting",
            "mild_irritation",
            "moderate_conflict",
            "severe_crisis",
        ]

    def test_intensities_increase_with_severity(self):
        intensities = [sit.intensity for sit in REFERENCE_SITUATIONS]
        assert intensities == [0.0, 0.5, 0.5, 1.0]


# ---------------------------------------------------------------------------
# Envelope invariants
# ---------------------------------------------------------------------------

class TestComputeEnvelope:
    def test_empty_situations_raises(self, all_composites):
        profile = all_composites[("INTJ", "Capricorn")]
        with pytest.raises(ValueError, match="empty"):
            compute_envelope(profile, situations=())

    def test_min_at_resting_max_order(self, all_composites):
        for profile in all_composites.values():
            env = compute_envelope(profile)
            for axis in BEHAVIORAL_AXES + ("deviation_amount",):
                envelope = getattr(env, axis)
                assert envelope.min <= envelope.at_resting + 1e-12
                assert envelope.at_resting <= envelope.max + 1e-12

    def test_behavioral_axes_clamped(self, all_composites):
        for profile in all_composites.values():
            env = compute_envelope(profile)
            for axis in BEHAVIORAL_AXES:
                envelope = getattr(env, axis)
                for value in (envelope.min, envelope.max, envelope.at_resting):
                    assert -1.0 <= value <= 1.0

    def test_uses_feel_then_behave_not_resting_only(self, all_composites):
        profile = all_composites[("ESTP", "Aries")]
        env = compute_envelope(profile)
        # Severe crisis should move at least one axis off resting.
        moved = any(
            abs(getattr(env, axis).max - getattr(env, axis).at_resting) > 0.05
            or abs(getattr(env, axis).min - getattr(env, axis).at_resting) > 0.05
            for axis in BEHAVIORAL_AXES
        )
        assert moved


class TestIntjCapricornSnapshot:
    """Regression snapshot: INTJ-Capricorn under the shipped ladder."""

    def test_aggression_and_withdrawal_shape(self, all_composites):
        env = compute_envelope(all_composites[("INTJ", "Capricorn")])
        assert env.aggression_passivity.at_resting == pytest.approx(-0.077, abs=0.02)
        assert env.aggression_passivity.max == pytest.approx(-0.077, abs=0.02)
        assert env.aggression_passivity.min == pytest.approx(-0.178, abs=0.03)
        assert env.sociability_withdrawal.at_resting < 0.0
        assert env.impulsiveness_deliberation.max < 0.0
        assert env.deviation_amount.at_resting < env.deviation_amount.max


class TestSeveritySpread:
    def test_severe_crisis_wider_aggression_than_mild(self, all_composites):
        mild = next(s for s in REFERENCE_SITUATIONS if s.name == "mild_irritation")
        severe = next(s for s in REFERENCE_SITUATIONS if s.name == "severe_crisis")
        mild_vals = []
        severe_vals = []
        for profile in all_composites.values():
            mild_vals.append(probe_situation(profile, mild)[0].aggression_passivity)
            severe_vals.append(probe_situation(profile, severe)[0].aggression_passivity)
        mild_spread = max(mild_vals) - min(mild_vals)
        severe_spread = max(severe_vals) - min(severe_vals)
        assert severe_spread > mild_spread


class TestComputeAllEnvelopes:
    def test_covers_all_composites(self, all_composites):
        envelopes = compute_all_envelopes(all_composites)
        assert len(envelopes) == 192
        assert ("ENFP", "Pisces") in envelopes


# ---------------------------------------------------------------------------
# Character cards
# ---------------------------------------------------------------------------

class TestCharacterCard:
    def test_estp_aries_card_has_aggression_range(self, all_composites, bounds):
        card = character_card(all_composites[("ESTP", "Aries")], bounds)
        assert card["mbti_type"] == "ESTP"
        assert card["sign"] == "Aries"
        agg = card["envelope"]["aggression_passivity"]
        assert "min" in agg and "max" in agg and "at_resting" in agg
        assert agg["min"] <= agg["max"]
        ds = card["designer_scalars"]
        for key in ("reactivity", "inflexibility", "persistence", "flexibility"):
            assert 0.0 <= ds[key] <= 1.0
        assert card["reference_situations"] == [s.name for s in REFERENCE_SITUATIONS]

    def test_export_cli_writes_json(self, tmp_path: Path):
        out = tmp_path / "cards.json"
        export_character_cards(out)
        data = json.loads(out.read_text(encoding="utf-8"))
        assert "INTJ_Capricorn" in data
        assert len(data) == 192
