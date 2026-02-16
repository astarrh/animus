"""Tests for decay utility.

Phase 3: exponential decay toward resting baseline, rate by rumination.
"""

import math

import pytest

from animus import decay
from animus.models import MoodVector
from animus.personalities import ESTP_ARIES, INTJ_CAPRICORN


# ---------------------------------------------------------------------------
# 1. Formula correctness
# ---------------------------------------------------------------------------

class TestFormula:
    """decayed = resting + (current - resting) * exp(-elapsed / rumination)"""

    def test_elapsed_zero_returns_current(self):
        disturbed = MoodVector(-0.5, -0.3, 0.2, 0.0, 0.7)
        result = decay(INTJ_CAPRICORN, disturbed, elapsed=0.0)
        for i, attr in enumerate(["distress_contentment", "fear_confidence", "isolation_belonging", "shame_pride", "arousal"]):
            assert getattr(result, attr) == pytest.approx(getattr(disturbed, attr), abs=0.001)

    def test_large_elapsed_approaches_resting(self):
        disturbed = MoodVector(-0.6, -0.5, 0.3, -0.2, 0.8)
        result = decay(INTJ_CAPRICORN, disturbed, elapsed=100.0)
        resting = INTJ_CAPRICORN.resting_mood
        for attr in ["distress_contentment", "fear_confidence", "isolation_belonging", "shame_pride", "arousal"]:
            assert getattr(result, attr) == pytest.approx(getattr(resting, attr), abs=0.05)

    def test_half_life_midpoint(self):
        resting = INTJ_CAPRICORN.resting_mood
        disturbed = MoodVector(
            resting.distress_contentment + 0.5,
            resting.fear_confidence,
            resting.isolation_belonging,
            resting.shame_pride,
            resting.arousal,
        )
        tau = INTJ_CAPRICORN.rumination
        half_life = tau * math.log(2)
        result = decay(INTJ_CAPRICORN, disturbed, elapsed=half_life)
        expected_dc = resting.distress_contentment + 0.5 * 0.5
        assert result.distress_contentment == pytest.approx(expected_dc, abs=0.02)


# ---------------------------------------------------------------------------
# 2. Rumination affects rate
# ---------------------------------------------------------------------------

class TestRuminationRate:
    """High rumination = slower decay. Low rumination = faster decay."""

    def test_high_rumination_retains_more(self):
        disturbed = MoodVector(-0.5, -0.4, 0.2, -0.1, 0.6)
        elapsed = 2.0
        result_intj = decay(INTJ_CAPRICORN, disturbed, elapsed)
        result_estp = decay(ESTP_ARIES, disturbed, elapsed)
        resting_intj = INTJ_CAPRICORN.resting_mood
        resting_estp = ESTP_ARIES.resting_mood
        # INTJ-Capricorn has higher rumination than ESTP-Aries
        assert INTJ_CAPRICORN.rumination > ESTP_ARIES.rumination
        # INTJ should be closer to disturbed (less decay) than ESTP
        dist_intj = sum(abs(getattr(result_intj, a) - getattr(disturbed, a)) for a in ["distress_contentment", "fear_confidence"])
        dist_estp = sum(abs(getattr(result_estp, a) - getattr(disturbed, a)) for a in ["distress_contentment", "fear_confidence"])
        dist_to_rest_intj = sum(abs(getattr(result_intj, a) - getattr(resting_intj, a)) for a in ["distress_contentment", "fear_confidence"])
        dist_to_rest_estp = sum(abs(getattr(result_estp, a) - getattr(resting_estp, a)) for a in ["distress_contentment", "fear_confidence"])
        # INTJ retains more of the disturbance (closer to disturbed, farther from resting)
        assert dist_to_rest_intj > dist_to_rest_estp

    def test_low_rumination_returns_faster(self):
        disturbed = MoodVector(0.5, 0.4, -0.3, 0.2, 0.8)
        elapsed = 5.0
        result_estp = decay(ESTP_ARIES, disturbed, elapsed)
        resting_estp = ESTP_ARIES.resting_mood
        # ESTP (low rumination) should be close to resting after 5 units
        for attr in ["distress_contentment", "fear_confidence", "isolation_belonging"]:
            assert abs(getattr(result_estp, attr) - getattr(resting_estp, attr)) < 0.15


# ---------------------------------------------------------------------------
# 3. Accepts list input
# ---------------------------------------------------------------------------

class TestInputFormats:
    def test_accepts_list(self):
        disturbed = [-0.5, -0.3, 0.0, 0.0, 0.6]
        result = decay(INTJ_CAPRICORN, disturbed, elapsed=1.0)
        assert isinstance(result, MoodVector)
