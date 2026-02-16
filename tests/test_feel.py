"""Tests for Feel mode.

Phase 3: personality-modulated mood deltas from raw situation vectors.
"""

import pytest

from animus import feel
from animus.models import FeelResult, MoodVector, PersonalityProfile
from animus.personalities import ESTP_ARIES, INTJ_CAPRICORN


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def situation_vector():
    """Base mood-space delta from a situation (e.g. hunger_pang)."""
    return MoodVector(
        distress_contentment=-0.2,
        fear_confidence=-0.1,
        isolation_belonging=0.0,
        shame_pride=0.0,
        arousal=0.2,
    )


# ---------------------------------------------------------------------------
# 1. Basic Feel call
# ---------------------------------------------------------------------------

class TestBasicFeel:
    def test_returns_feel_result(self, situation_vector):
        result = feel(situation_vector, INTJ_CAPRICORN)
        assert isinstance(result, FeelResult)
        assert isinstance(result.mood_delta, MoodVector)
        assert isinstance(result.new_mood, MoodVector)

    def test_accepts_list_input(self):
        situation = [-0.2, -0.1, 0.0, 0.0, 0.2]
        result = feel(situation, INTJ_CAPRICORN)
        assert result.new_mood.distress_contentment < INTJ_CAPRICORN.resting_mood.distress_contentment

    def test_default_current_mood_is_resting(self, situation_vector):
        result = feel(situation_vector, INTJ_CAPRICORN)
        # new_mood = resting + modulated_delta
        resting = INTJ_CAPRICORN.resting_mood
        assert result.new_mood.distress_contentment == pytest.approx(
            resting.distress_contentment + result.mood_delta.distress_contentment
        )

    def test_explicit_current_mood_is_used(self, situation_vector):
        current = MoodVector(-0.5, -0.3, 0.0, 0.0, 0.5)
        result = feel(situation_vector, INTJ_CAPRICORN, current_mood=current)
        # new_mood should reflect current + delta
        expected_dc = current.distress_contentment + result.mood_delta.distress_contentment
        assert result.new_mood.distress_contentment == pytest.approx(expected_dc, abs=0.01)


# ---------------------------------------------------------------------------
# 2. Susceptibility modulation
# ---------------------------------------------------------------------------

class TestSusceptibilityModulation:
    """High-susceptibility personalities should feel situations more strongly."""

    def test_high_susceptibility_larger_delta(self, situation_vector):
        # INFP-Pisces typically has higher susceptibility than ISTJ
        # Use INTJ (lower) vs ESTP (moderate-high) from personalities we have
        result_intj = feel(situation_vector, INTJ_CAPRICORN)
        result_estp = feel(situation_vector, ESTP_ARIES)
        # Both get same base situation; susceptibility scales the delta
        # ESTP has higher susceptibility than INTJ-Capricorn
        assert ESTP_ARIES.susceptibility > INTJ_CAPRICORN.susceptibility
        # ESTP's mood_delta should be larger in magnitude
        estp_delta_mag = sum(abs(v) for v in result_estp.mood_delta.to_list())
        intj_delta_mag = sum(abs(v) for v in result_intj.mood_delta.to_list())
        assert estp_delta_mag > intj_delta_mag

    def test_delta_scaled_by_susceptibility(self, situation_vector):
        result = feel(situation_vector, INTJ_CAPRICORN)
        # mood_delta[i] = situation[i] * susceptibility
        expected_dc = situation_vector.distress_contentment * INTJ_CAPRICORN.susceptibility
        assert result.mood_delta.distress_contentment == pytest.approx(expected_dc)


# ---------------------------------------------------------------------------
# 3. Clamping
# ---------------------------------------------------------------------------

class TestClamping:
    def test_new_mood_clamped_bipolar(self, situation_vector):
        current = MoodVector(0.9, 0.9, 0.9, 0.9, 0.9)
        strong_situation = MoodVector(0.5, 0.5, 0.5, 0.5, 0.2)
        result = feel(strong_situation, ESTP_ARIES, current_mood=current)
        for attr in ("distress_contentment", "fear_confidence", "isolation_belonging", "shame_pride"):
            assert -1.0 <= getattr(result.new_mood, attr) <= 1.0

    def test_arousal_clamped_unipolar(self):
        current = MoodVector(0.0, 0.0, 0.0, 0.0, 0.95)
        situation = MoodVector(0.0, 0.0, 0.0, 0.0, 0.2)
        result = feel(situation, ESTP_ARIES, current_mood=current)
        assert 0.0 <= result.new_mood.arousal <= 1.0


# ---------------------------------------------------------------------------
# 4. Invalid input
# ---------------------------------------------------------------------------

class TestInvalidInput:
    def test_rejects_too_short_list(self):
        with pytest.raises(TypeError):
            feel([0.0, 0.0], INTJ_CAPRICORN)
