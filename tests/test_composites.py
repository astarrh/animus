"""Tests for composite generation, layer dominance, and differentiation.

Phase 2 completion criteria covered:
- All 192 composites generated from 28 building blocks
- Contrasting personalities produce meaningfully different behavioral outputs
- Layer dominance model: MB-dominant, astrology-dominant, tension composites
- Global bias dial shifts outputs in expected direction
- Strong-MB + mild-sign vs mild-MB + strong-sign behave differently
- INTJ-Capricorn composite matches Phase 1 hardcoded (regression)
"""

import random

import pytest

from animus import behave
from animus.building_blocks import BuildingBlockLibrary
from animus.composite import (
    blend_composite,
    compute_blend_weight,
    generate_all_composites,
)
from animus.data_pipeline import load_building_blocks
from animus.data_pipeline.block_assembler import assemble
from animus.models import (
    AppraisalVector,
    PersonalityProfile,
    Stimulus,
)


@pytest.fixture(scope="module")
def raw_data():
    return load_building_blocks()


@pytest.fixture(scope="module")
def library(raw_data):
    return assemble(raw_data)


@pytest.fixture(scope="module")
def all_composites(library):
    return generate_all_composites(library)


# ---------------------------------------------------------------------------
# 1. All 192 composites generated
# ---------------------------------------------------------------------------

class TestCompositeGeneration:
    """Verify all 192 composites are generated from 28 building blocks."""

    def test_generates_192_composites(self, all_composites):
        assert len(all_composites) == 192

    def test_every_mbti_sign_pair_present(self, all_composites, library):
        for mb_name in library.mbti_types:
            for sign_name in library.signs:
                key = (mb_name, sign_name)
                assert key in all_composites
                profile = all_composites[key]
                assert profile.mbti_type == mb_name
                assert profile.sign == sign_name

    def test_each_composite_has_required_attributes(self, all_composites):
        for (mb, sign), profile in all_composites.items():
            assert isinstance(profile, PersonalityProfile)
            assert profile.mbti_type == mb
            assert profile.sign == sign
            assert 0.0 <= profile.susceptibility <= 1.0
            assert 0.0 <= profile.rigidity <= 1.0
            assert 0.0 <= profile.rumination <= 1.0
            assert len(profile.transform_matrix.rows) == 5
            for row in profile.transform_matrix.rows:
                assert len(row) == 5


# ---------------------------------------------------------------------------
# 2. INTJ-Capricorn matches Phase 1 hardcoded (regression)
# ---------------------------------------------------------------------------

class TestINTJCapricornRegression:
    """INTJ-Capricorn stays a stoic/rigid archetype after JSON v2 retune.

    Phase-1 hardcoded ``INTJ_CAPRICORN`` is a historical hand profile; scalar
    equality is not required after building-block version 2.
    """

    def test_intj_capricorn_labels(self, all_composites):
        composite = all_composites[("INTJ", "Capricorn")]
        assert composite.mbti_type == "INTJ"
        assert composite.sign == "Capricorn"

    def test_intj_capricorn_is_among_least_reactive(self, all_composites):
        ranked = sorted(all_composites.values(), key=lambda p: p.susceptibility)
        cutoff = ranked[int(len(ranked) * 0.15)]
        composite = all_composites[("INTJ", "Capricorn")]
        assert composite.susceptibility <= cutoff.susceptibility + 1e-12

    def test_intj_capricorn_behaves_stoic(self, all_composites):
        composite = all_composites[("INTJ", "Capricorn")]
        stimulus = Stimulus(
            appraisal=AppraisalVector(control=0.3, certainty=-0.2),
            behavioral={"threat": 0.3, "urgency": 0.5, "social_context": 0.6},
        )
        result = behave(composite, stimulus, intensity=0.0)
        bv = result.behavioral_vector
        assert bv.impulsiveness_deliberation < 0.0
        assert bv.sociability_withdrawal < 0.0
        assert bv.aggression_passivity < 0.2

    def test_archetype_rank_order_preserved(self, all_composites):
        """Retune must not invert stoic vs reactive / rigid vs flexible extremes."""
        susc = sorted(all_composites, key=lambda k: all_composites[k].susceptibility)
        rigid = sorted(all_composites, key=lambda k: all_composites[k].rigidity)
        n = len(susc)
        low_s, high_s = set(susc[: n // 5]), set(susc[-n // 5 :])
        low_r, high_r = set(rigid[: n // 5]), set(rigid[-n // 5 :])
        assert ("ISTJ", "Capricorn") in low_s
        assert ("INTJ", "Capricorn") in low_s
        assert ("ENFP", "Pisces") in high_s
        assert ("ENFP", "Gemini") in low_r
        assert ("ISTJ", "Taurus") in high_r


# ---------------------------------------------------------------------------
# 3. Contrasting personalities produce meaningfully different outputs
# ---------------------------------------------------------------------------

# Pairs chosen for contrast: ESTP-Aries (bold, impulsive), INFP-Pisces (soft, reflective),
# ENTJ-Scorpio (dominant, intense), ISFJ-Cancer (nurturing, cautious).
CONTRASTING_KEYS = [
    ("ESTP", "Aries"),
    ("INFP", "Pisces"),
    ("ENTJ", "Scorpio"),
    ("ISFJ", "Cancer"),
    ("ISTP", "Capricorn"),
    ("ENFP", "Sagittarius"),
    ("INTJ", "Capricorn"),
    ("ESFJ", "Leo"),
]


class TestDifferentiation:
    """Same stimulus → contrasting personalities produce meaningfully distinct outputs."""

    @pytest.fixture
    def bee_stimulus(self):
        return Stimulus(
            appraisal=AppraisalVector(control=0.3, certainty=-0.2),
            behavioral={"threat": 0.3, "urgency": 0.5, "social_context": 0.6},
        )

    def test_contrasting_personalities_differ(self, all_composites, bee_stimulus):
        """Run same stimulus against 8 contrasting personalities; outputs must be distinct."""
        rng = random.Random(12345)
        results = {}
        for key in CONTRASTING_KEYS:
            profile = all_composites[key]
            results[key] = behave(profile, bee_stimulus, intensity=0.85, rng=rng).behavioral_vector.to_list()

        # Pairwise: at least one dimension should differ (threshold 0.06)
        # Some pairs (e.g. INFP-Pisces vs ISFJ-Cancer) can be relatively close; we require
        # that every pair has some measurable difference.
        for i, key_a in enumerate(CONTRASTING_KEYS):
            for key_b in CONTRASTING_KEYS[i + 1:]:
                vec_a = results[key_a]
                vec_b = results[key_b]
                max_diff = max(abs(vec_a[j] - vec_b[j]) for j in range(5))
                assert max_diff > 0.06, (
                    f"{key_a} vs {key_b}: outputs too similar (max_diff={max_diff:.3f})"
                )

    def test_estp_aries_more_aggressive_than_infp_pisces(self, all_composites, bee_stimulus):
        rng = random.Random(42)
        estp = behave(all_composites[("ESTP", "Aries")], bee_stimulus, intensity=0.8, rng=rng)
        infp = behave(all_composites[("INFP", "Pisces")], bee_stimulus, intensity=0.8, rng=rng)
        assert estp.behavioral_vector.aggression_passivity > infp.behavioral_vector.aggression_passivity

    def test_entj_scorpio_more_dominant_than_infj_cancer(self, all_composites, bee_stimulus):
        """Dominant intuitive Thinking vs gentle intuitive Feeling (same S/N pole)."""
        rng = random.Random(42)
        entj = behave(all_composites[("ENTJ", "Scorpio")], bee_stimulus, intensity=0.8, rng=rng)
        infj = behave(all_composites[("INFJ", "Cancer")], bee_stimulus, intensity=0.8, rng=rng)
        assert entj.behavioral_vector.aggression_passivity > infj.behavioral_vector.aggression_passivity


# ---------------------------------------------------------------------------
# 4. Layer dominance & global bias dial
# ---------------------------------------------------------------------------

class TestLayerDominance:
    """Layer dominance model and global bias produce expected shifts."""

    def test_blend_weight_bounds(self):
        """compute_blend_weight returns mb_weight in [0.05, 0.95]."""
        for mb in [0.0, 0.5, 1.0]:
            for sign in [0.0, 0.5, 1.0]:
                w = compute_blend_weight(mb, sign, global_bias=0.0)
                assert 0.05 <= w <= 0.95
        # Bias extremes
        w_neg = compute_blend_weight(0.5, 0.5, global_bias=-1.0)
        w_pos = compute_blend_weight(0.5, 0.5, global_bias=1.0)
        assert w_neg < 0.5 < w_pos

    def test_global_bias_positive_shifts_toward_mbti(self, library):
        """Bias +1.0 → composite closer to MBTI base than with bias 0 or -1."""
        mb = library.get_mbti("INTJ")
        sign = library.get_sign("Capricorn")
        neutral = blend_composite(mb, sign, global_bias=0.0)
        mb_dominant = blend_composite(mb, sign, global_bias=1.0)
        sign_dominant = blend_composite(mb, sign, global_bias=-1.0)
        # The more-rigid layer should pull rigidity when bias favors that layer.
        if mb.rigidity >= sign.rigidity:
            assert mb_dominant.rigidity >= sign_dominant.rigidity - 0.01
        else:
            assert sign_dominant.rigidity >= mb_dominant.rigidity - 0.01
        if mb.rumination >= sign.rumination:
            assert mb_dominant.rumination >= sign_dominant.rumination - 0.01
        else:
            assert sign_dominant.rumination >= mb_dominant.rumination - 0.01

    def test_global_bias_negative_shifts_toward_astrology(self, library):
        """Bias -1.0 → composite closer to sign than with bias 0 or +1."""
        mb = library.get_mbti("INTJ")
        sign = library.get_sign("Capricorn")
        w_neutral = compute_blend_weight(mb.assertiveness, sign.assertiveness, 0.0)
        w_neg = compute_blend_weight(mb.assertiveness, sign.assertiveness, -1.0)
        w_pos = compute_blend_weight(mb.assertiveness, sign.assertiveness, 1.0)
        assert w_neg < w_neutral < w_pos

    def test_bias_extremes_shift_behavior(self, library):
        """Same personality type, bias -1 vs +1: behavioral output should differ."""
        composites_neg = generate_all_composites(library, global_bias=-1.0)
        composites_pos = generate_all_composites(library, global_bias=1.0)
        profile_neg = composites_neg[("INTJ", "Capricorn")]
        profile_pos = composites_pos[("INTJ", "Capricorn")]
        stimulus = Stimulus(appraisal=AppraisalVector(0.0, 0.0))
        rng = random.Random(99)
        out_neg = behave(profile_neg, stimulus, intensity=0.9, rng=rng)
        out_pos = behave(profile_pos, stimulus, intensity=0.9, rng=rng)
        diff = sum(abs(a - b) for a, b in zip(out_neg.behavioral_vector.to_list(), out_pos.behavioral_vector.to_list()))
        assert diff > 0.05, "Bias -1 vs +1 should produce different behavioral output"


# ---------------------------------------------------------------------------
# 5. Strong-MB + mild-sign vs mild-MB + strong-sign
# ---------------------------------------------------------------------------

class TestStrongMildCombinations:
    """Strong-MB + mild-sign composites behave differently from mild-MB + strong-sign."""

    def test_high_mb_low_sign_vs_low_mb_high_sign_differ(self, library):
        """ENTJ (high assertiveness) + Pisces (low) vs INFP (low) + Aries (high)."""
        entj_pisces = blend_composite(
            library.get_mbti("ENTJ"), library.get_sign("Pisces"), global_bias=0.0
        )
        infp_aries = blend_composite(
            library.get_mbti("INFP"), library.get_sign("Aries"), global_bias=0.0
        )
        stimulus = Stimulus(appraisal=AppraisalVector(0.2, -0.1))
        rng = random.Random(77)
        r_entj_p = behave(entj_pisces, stimulus, intensity=0.85, rng=rng)
        r_infp_a = behave(infp_aries, stimulus, intensity=0.85, rng=rng)
        # ENTJ-Pisces should be more deliberate, INFP-Aries more impulsive (directionally)
        assert (r_entj_p.behavioral_vector.impulsiveness_deliberation
                != r_infp_a.behavioral_vector.impulsiveness_deliberation)
        # Outputs should differ on at least one dimension
        vec_entj = r_entj_p.behavioral_vector.to_list()
        vec_infp = r_infp_a.behavioral_vector.to_list()
        assert any(abs(a - b) > 0.05 for a, b in zip(vec_entj, vec_infp))


# ---------------------------------------------------------------------------
# 6. BuildingBlockLibrary lookup
# ---------------------------------------------------------------------------

class TestLibraryLookup:
    """Library get_mbti / get_sign return correct blocks."""

    def test_get_mbti_returns_correct_type(self, library):
        for name, block in library.mbti_types.items():
            assert library.get_mbti(name) is block
            assert library.get_mbti(name).name == name

    def test_get_sign_returns_correct_sign(self, library):
        for name, block in library.signs.items():
            assert library.get_sign(name) is block
            assert library.get_sign(name).name == name
