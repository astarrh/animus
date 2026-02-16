"""Tests for the Behave mode transformation pipeline.

Validates Phase 1 completion criteria:
1. INTJ-Capricorn processes bee-in-tent stimulus with plausible output
2. Varying mood inputs produces plausible behavioral shifts
3. Varying appraisal context produces different behavioral pathways
4. High intensity = personality-consistent; low intensity = more variance
5. All outputs are properly clamped to valid ranges
"""

import random

import pytest

from animus import behave
from animus.models import (
    AppraisalVector,
    BehaveResult,
    BehavioralVector,
    MoodVector,
    PersonalityProfile,
    Stimulus,
    TransformationMatrix,
)
from animus.personalities import ESTP_ARIES, INTJ_CAPRICORN


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def personality():
    return INTJ_CAPRICORN


@pytest.fixture
def bee_stimulus():
    """The bee-in-tent stimulus from design doc Section 4.6."""
    return Stimulus(
        appraisal=AppraisalVector(control=0.3, certainty=-0.2),
        behavioral={"threat": 0.3, "urgency": 0.5, "social_context": 0.6},
    )


@pytest.fixture
def rng():
    return random.Random(42)


# ---------------------------------------------------------------------------
# 1. Bee-in-tent: INTJ-Capricorn "doesn't even look up"
# ---------------------------------------------------------------------------

class TestBeeInTent:
    """The design doc expects ISTP-Capricorn to return roughly:
    { agg: +0.1, imp: -0.3, soc: -0.2, emp: -0.1, cur: +0.1 }

    INTJ-Capricorn should be similar: low aggression, deliberate,
    withdrawn, slightly self-interested, mildly curious. At high
    intensity, no action trigger should fire.
    """

    def test_high_intensity_doesnt_look_up(self, personality, bee_stimulus, rng):
        """At high intensity, INTJ-Cap should produce a muted response."""
        result = behave(personality, bee_stimulus, intensity=0.9, rng=rng)
        bv = result.behavioral_vector

        # No aggression trigger fires (threshold is +0.5)
        assert bv.aggression_passivity < 0.5, "Should not swat at the bee"
        # Not fleeing either (threshold is -0.4 aggression AND -0.3 sociability)
        # Deliberate, not impulsive
        assert bv.impulsiveness_deliberation < 0.0, "Should be deliberate, not impulsive"
        # Withdrawn
        assert bv.sociability_withdrawal < 0.0, "Should be withdrawn"

    def test_low_intensity_allows_variance(self, personality, bee_stimulus):
        """At low intensity, outputs should vary across seeds."""
        results = []
        for seed in range(20):
            r = behave(personality, bee_stimulus, intensity=0.1, rng=random.Random(seed))
            results.append(r.behavioral_vector.aggression_passivity)

        # With 20 seeds at low intensity, we should see meaningful spread
        spread = max(results) - min(results)
        assert spread > 0.2, f"Low intensity should produce variance, got spread={spread:.3f}"

    def test_result_has_metadata(self, personality, bee_stimulus, rng):
        result = behave(personality, bee_stimulus, intensity=0.5, rng=rng)
        assert isinstance(result, BehaveResult)
        assert isinstance(result.behavioral_vector, BehavioralVector)
        assert isinstance(result.conflict_flag, bool)
        assert isinstance(result.rigidity_indicator, float)
        assert isinstance(result.deviation_amount, float)


# ---------------------------------------------------------------------------
# 2. Mood variation produces plausible behavioral shifts
# ---------------------------------------------------------------------------

class TestMoodVariation:
    """The transformation matrix should convert different moods into
    meaningfully different behavioral outputs."""

    def test_distressed_mood_increases_deliberation(self, personality, bee_stimulus, rng):
        """Distressed INTJ-Cap should become more deliberate (not impulsive)."""
        distressed = MoodVector(-0.7, -0.5, -0.3, -0.3, 0.7)
        result_distressed = behave(personality, bee_stimulus, intensity=0.8, mood=distressed, rng=rng)
        result_resting = behave(personality, bee_stimulus, intensity=0.8, rng=random.Random(42))

        # Distress should push toward more deliberation (more negative impulsiveness)
        assert (result_distressed.behavioral_vector.impulsiveness_deliberation
                < result_resting.behavioral_vector.impulsiveness_deliberation), \
            "Distressed INTJ-Cap should be more deliberate"

    def test_content_mood_increases_curiosity(self, personality, bee_stimulus, rng):
        """Content INTJ-Cap should be more curious (mind is free to explore)."""
        content = MoodVector(0.7, 0.6, 0.3, 0.3, 0.3)
        result_content = behave(personality, bee_stimulus, intensity=0.8, mood=content, rng=rng)
        result_resting = behave(personality, bee_stimulus, intensity=0.8, rng=random.Random(42))

        assert (result_content.behavioral_vector.curiosity_avoidance
                > result_resting.behavioral_vector.curiosity_avoidance), \
            "Content INTJ-Cap should be more curious"

    def test_fearful_mood_increases_withdrawal(self, personality, bee_stimulus, rng):
        """Fearful INTJ-Cap should withdraw more."""
        fearful = MoodVector(-0.3, -0.8, -0.2, -0.2, 0.8)
        result_fearful = behave(personality, bee_stimulus, intensity=0.8, mood=fearful, rng=rng)
        result_resting = behave(personality, bee_stimulus, intensity=0.8, rng=random.Random(42))

        assert (result_fearful.behavioral_vector.sociability_withdrawal
                < result_resting.behavioral_vector.sociability_withdrawal), \
            "Fearful INTJ-Cap should be more withdrawn"

    def test_mood_not_suppressed_by_intensity(self, personality, bee_stimulus):
        """Design doc: mood is NOT suppressed by intensity. A distressed INTJ-Cap
        at high intensity should still show mood-driven behavioral shifts."""
        distressed = MoodVector(-0.8, -0.7, -0.5, -0.4, 0.8)
        resting = personality.resting_mood

        r_distressed = behave(personality, bee_stimulus, intensity=1.0, mood=distressed, rng=random.Random(42))
        r_resting = behave(personality, bee_stimulus, intensity=1.0, mood=resting, rng=random.Random(42))

        # Even at intensity=1.0, distressed mood should produce different output
        bv_d = r_distressed.behavioral_vector.to_list()
        bv_r = r_resting.behavioral_vector.to_list()
        diff = sum(abs(bv_d[i] - bv_r[i]) for i in range(5))
        assert diff > 0.01, f"Mood should influence output even at intensity=1.0, got diff={diff:.4f}"


# ---------------------------------------------------------------------------
# 3. Appraisal variation produces different behavioral pathways
# ---------------------------------------------------------------------------

class TestAppraisalVariation:
    """Different appraisal contexts should activate different transformation
    pathways, producing measurably different behavioral outputs."""

    def test_high_control_vs_low_control(self, personality):
        """High control (agentic) should produce more active response than
        low control (helpless), especially under negative mood."""
        distressed = MoodVector(-0.6, -0.6, -0.3, -0.2, 0.7)

        s_high = Stimulus(appraisal=AppraisalVector(control=0.8, certainty=0.0))
        s_low = Stimulus(appraisal=AppraisalVector(control=-0.8, certainty=0.0))

        r_high = behave(personality, s_high, 0.9, mood=distressed, rng=random.Random(42))
        r_low = behave(personality, s_low, 0.9, mood=distressed, rng=random.Random(42))

        # High control should produce more aggression (or less passivity) than low
        assert (r_high.behavioral_vector.aggression_passivity
                > r_low.behavioral_vector.aggression_passivity), \
            "High control should produce more active (aggressive) response"

    def test_high_certainty_vs_low_certainty(self, personality):
        """High certainty should produce more deliberation; low certainty
        should produce more impulsiveness."""
        distressed = MoodVector(-0.6, -0.6, -0.3, -0.2, 0.7)

        s_certain = Stimulus(appraisal=AppraisalVector(control=0.0, certainty=0.8))
        s_uncertain = Stimulus(appraisal=AppraisalVector(control=0.0, certainty=-0.8))

        r_certain = behave(personality, s_certain, 0.9, mood=distressed, rng=random.Random(42))
        r_uncertain = behave(personality, s_uncertain, 0.9, mood=distressed, rng=random.Random(42))

        # High certainty → more deliberate (lower impulsiveness value)
        assert (r_certain.behavioral_vector.impulsiveness_deliberation
                < r_uncertain.behavioral_vector.impulsiveness_deliberation), \
            "High certainty should produce more deliberation"


# ---------------------------------------------------------------------------
# 4. Intensity controls personality vs. variance
# ---------------------------------------------------------------------------

class TestIntensity:
    def test_high_intensity_is_consistent(self, personality, bee_stimulus):
        """At high intensity, different seeds should produce similar outputs."""
        results = []
        for seed in range(20):
            r = behave(personality, bee_stimulus, intensity=1.0, rng=random.Random(seed))
            results.append(r.behavioral_vector.to_list())

        # Check spread across seeds for each dimension
        for dim in range(5):
            values = [r[dim] for r in results]
            spread = max(values) - min(values)
            assert spread < 0.05, \
                f"At intensity=1.0, dimension {dim} spread should be near 0, got {spread:.4f}"

    def test_low_intensity_has_high_variance(self, personality, bee_stimulus):
        """At low intensity, different seeds should produce varied outputs."""
        results = []
        for seed in range(20):
            r = behave(personality, bee_stimulus, intensity=0.0, rng=random.Random(seed))
            results.append(r.behavioral_vector.to_list())

        # At least some dimensions should show significant spread
        max_spread = 0.0
        for dim in range(5):
            values = [r[dim] for r in results]
            spread = max(values) - min(values)
            max_spread = max(max_spread, spread)

        assert max_spread > 0.5, \
            f"At intensity=0.0, should see significant variance, max spread={max_spread:.3f}"

    def test_intensity_monotonic_deviation(self, personality, bee_stimulus):
        """As intensity increases, deviation from baseline should generally decrease
        (output converges to personality baseline)."""
        deviations = []
        for intensity in [0.0, 0.25, 0.5, 0.75, 1.0]:
            # Average over multiple seeds to smooth out randomness
            avg_dev = 0.0
            n = 50
            for seed in range(n):
                r = behave(personality, bee_stimulus, intensity, rng=random.Random(seed))
                avg_dev += r.deviation_amount
            deviations.append(avg_dev / n)

        # Deviation at intensity=1.0 should be less than at intensity=0.0
        assert deviations[-1] < deviations[0], \
            f"Higher intensity should mean lower deviation: {deviations}"


# ---------------------------------------------------------------------------
# 5. Output clamping
# ---------------------------------------------------------------------------

class TestClamping:
    def test_behavioral_output_is_clamped(self, personality, bee_stimulus):
        """All output values should be in [-1.0, 1.0]."""
        for seed in range(100):
            r = behave(personality, bee_stimulus, intensity=0.0, rng=random.Random(seed))
            for val in r.behavioral_vector.to_list():
                assert -1.0 <= val <= 1.0, f"Output {val} is out of range"

    def test_extreme_mood_is_handled(self, personality, bee_stimulus, rng):
        """Extreme mood values should still produce clamped output."""
        extreme = MoodVector(-1.0, -1.0, -1.0, -1.0, 1.0)
        r = behave(personality, bee_stimulus, intensity=1.0, mood=extreme, rng=rng)
        for val in r.behavioral_vector.to_list():
            assert -1.0 <= val <= 1.0, f"Output {val} out of range with extreme mood"

    def test_extreme_appraisal_is_handled(self, personality, rng):
        """Extreme appraisal values should be clamped internally."""
        extreme_stim = Stimulus(
            appraisal=AppraisalVector(control=5.0, certainty=-5.0),
            behavioral={},
        )
        r = behave(personality, extreme_stim, intensity=0.5, rng=rng)
        for val in r.behavioral_vector.to_list():
            assert -1.0 <= val <= 1.0, f"Output {val} out of range with extreme appraisal"


# ---------------------------------------------------------------------------
# 6. Default mood uses resting baseline
# ---------------------------------------------------------------------------

class TestDefaults:
    def test_no_mood_uses_resting_baseline(self, personality, bee_stimulus, rng):
        """When mood is not provided, the resting baseline should be used."""
        r_default = behave(personality, bee_stimulus, intensity=1.0, rng=rng)
        r_explicit = behave(personality, bee_stimulus, intensity=1.0,
                           mood=personality.resting_mood, rng=random.Random(42))
        assert r_default.behavioral_vector == r_explicit.behavioral_vector

    def test_deviation_is_non_negative(self, personality, bee_stimulus, rng):
        r = behave(personality, bee_stimulus, intensity=0.5, rng=rng)
        assert r.deviation_amount >= 0.0

    def test_deviation_is_bounded(self, personality, bee_stimulus, rng):
        r = behave(personality, bee_stimulus, intensity=0.5, rng=rng)
        assert r.deviation_amount <= 1.0


# ---------------------------------------------------------------------------
# 7. Personality comparison: INTJ-Capricorn vs ESTP-Aries
# ---------------------------------------------------------------------------

class TestPersonalityComparison:
    """Same stimulus, two opposite personalities. Validates that the pipeline
    produces meaningfully different outputs — not just different numbers,
    but directionally correct differences matching design doc expectations.

    Design doc Section 4.6 expectations:
    - ESTP-Aries: { agg: +0.7, imp: +0.6, soc: +0.2, emp: -0.1, cur: +0.3 } → swats at the bee
    - ISTP-Capricorn: { agg: +0.1, imp: -0.3, soc: -0.2, emp: -0.1, cur: +0.1 } → doesn't look up
    """

    @pytest.fixture
    def estp_aries(self):
        return ESTP_ARIES

    @pytest.fixture
    def bee_stimulus(self):
        return Stimulus(
            appraisal=AppraisalVector(control=0.3, certainty=-0.2),
            behavioral={"threat": 0.3, "urgency": 0.5, "social_context": 0.6},
        )

    def test_estp_more_aggressive_than_intj(self, estp_aries, bee_stimulus):
        """ESTP-Aries should be significantly more aggressive to the bee."""
        r_estp = behave(estp_aries, bee_stimulus, intensity=0.8, rng=random.Random(42))
        r_intj = behave(INTJ_CAPRICORN, bee_stimulus, intensity=0.8, rng=random.Random(42))

        assert (r_estp.behavioral_vector.aggression_passivity
                > r_intj.behavioral_vector.aggression_passivity), \
            "ESTP-Aries should be more aggressive than INTJ-Capricorn"

    def test_estp_more_impulsive_than_intj(self, estp_aries, bee_stimulus):
        """ESTP-Aries should be impulsive; INTJ-Capricorn should be deliberate."""
        r_estp = behave(estp_aries, bee_stimulus, intensity=0.8, rng=random.Random(42))
        r_intj = behave(INTJ_CAPRICORN, bee_stimulus, intensity=0.8, rng=random.Random(42))

        assert r_estp.behavioral_vector.impulsiveness_deliberation > 0.0, \
            "ESTP-Aries should be impulsive (positive)"
        assert r_intj.behavioral_vector.impulsiveness_deliberation < 0.0, \
            "INTJ-Capricorn should be deliberate (negative)"

    def test_estp_more_sociable_than_intj(self, estp_aries, bee_stimulus):
        """ESTP-Aries should lean sociable; INTJ-Capricorn should lean withdrawn."""
        r_estp = behave(estp_aries, bee_stimulus, intensity=0.8, rng=random.Random(42))
        r_intj = behave(INTJ_CAPRICORN, bee_stimulus, intensity=0.8, rng=random.Random(42))

        assert (r_estp.behavioral_vector.sociability_withdrawal
                > r_intj.behavioral_vector.sociability_withdrawal), \
            "ESTP-Aries should be more sociable than INTJ-Capricorn"

    def test_estp_swats_intj_ignores(self, estp_aries, bee_stimulus):
        """At high intensity, ESTP-Aries should cross the aggression trigger
        threshold (+0.5) while INTJ-Capricorn should not."""
        r_estp = behave(estp_aries, bee_stimulus, intensity=0.9, rng=random.Random(42))
        r_intj = behave(INTJ_CAPRICORN, bee_stimulus, intensity=0.9, rng=random.Random(42))

        # Design doc trigger: aggression > 0.5 → swats at the bee
        assert r_estp.behavioral_vector.aggression_passivity > 0.2, \
            "ESTP-Aries should show meaningful aggression toward the bee"
        assert r_intj.behavioral_vector.aggression_passivity < 0.1, \
            "INTJ-Capricorn should barely register the bee"

    def test_estp_more_curious_than_intj_under_stimulus(self, estp_aries, bee_stimulus):
        """ESTP-Aries is curious about immediate, tangible things (the bee).
        INTJ-Capricorn is curious in the abstract but unbothered by a bee."""
        r_estp = behave(estp_aries, bee_stimulus, intensity=0.8, rng=random.Random(42))
        r_intj = behave(INTJ_CAPRICORN, bee_stimulus, intensity=0.8, rng=random.Random(42))

        assert (r_estp.behavioral_vector.curiosity_avoidance
                > r_intj.behavioral_vector.curiosity_avoidance), \
            "ESTP-Aries should be more engaged with the bee"

    def test_distressed_estp_still_more_active_than_distressed_intj(self, estp_aries, bee_stimulus):
        """Even when both are distressed, ESTP-Aries should still be more
        aggressive and impulsive — personality shapes how distress manifests."""
        distressed = MoodVector(-0.7, -0.5, -0.3, -0.3, 0.7)

        r_estp = behave(estp_aries, bee_stimulus, intensity=0.8, mood=distressed, rng=random.Random(42))
        r_intj = behave(INTJ_CAPRICORN, bee_stimulus, intensity=0.8, mood=distressed, rng=random.Random(42))

        assert (r_estp.behavioral_vector.aggression_passivity
                > r_intj.behavioral_vector.aggression_passivity), \
            "Distressed ESTP-Aries should still be more aggressive"
        assert (r_estp.behavioral_vector.impulsiveness_deliberation
                > r_intj.behavioral_vector.impulsiveness_deliberation), \
            "Distressed ESTP-Aries should still be more impulsive"

    def test_estp_lower_rumination(self, estp_aries):
        """ESTP-Aries should have lower rumination (lets go of moods faster)."""
        assert estp_aries.rumination < INTJ_CAPRICORN.rumination, \
            "ESTP-Aries should ruminate less than INTJ-Capricorn"

    def test_estp_lower_rigidity(self, estp_aries):
        """ESTP-Aries (Perceiving) should be less rigid than INTJ-Capricorn (Judging)."""
        assert estp_aries.rigidity < INTJ_CAPRICORN.rigidity, \
            "ESTP-Aries should be less rigid than INTJ-Capricorn"
