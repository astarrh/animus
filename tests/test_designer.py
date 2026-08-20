"""Tests for designer scalar calibration (Phase 1)."""

from __future__ import annotations

import pytest

from animus import behave, feel
from animus.composite import generate_all_composites
from animus.data_pipeline import assemble, load_building_blocks
from animus.designer import (
    DesignerScalars,
    apply_designer_scalars,
    compute_scalar_bounds,
    designer_scalars,
)
from animus.models import AppraisalVector, MoodVector, Stimulus


@pytest.fixture(scope="module")
def all_composites():
    library = assemble(load_building_blocks())
    return generate_all_composites(library)


@pytest.fixture(scope="module")
def bounds(all_composites):
    return compute_scalar_bounds(all_composites)


# ---------------------------------------------------------------------------
# Bounds computation
# ---------------------------------------------------------------------------

class TestComputeScalarBounds:
    def test_all_192_composites_meet_spread_targets(self, bounds):
        susc_spread = bounds.susceptibility[1] - bounds.susceptibility[0]
        rigid_spread = bounds.rigidity[1] - bounds.rigidity[0]
        assert susc_spread >= 0.45
        assert rigid_spread >= 0.50
        assert bounds.susceptibility[0] <= 0.30
        assert bounds.susceptibility[1] >= 0.70
        assert bounds.rigidity[0] <= 0.25
        assert bounds.rigidity[1] >= 0.70

    def test_accepts_iterable_of_profiles(self, all_composites):
        profiles = list(all_composites.values())
        bounds = compute_scalar_bounds(profiles)
        assert bounds.susceptibility == compute_scalar_bounds(all_composites).susceptibility

    def test_empty_collection_raises(self):
        with pytest.raises(ValueError, match="empty"):
            compute_scalar_bounds([])

    def test_single_profile_degenerate_remap(self):
        profile = next(iter(generate_all_composites(assemble(load_building_blocks())).values()))
        bounds = compute_scalar_bounds([profile])
        assert bounds.remap(profile.susceptibility, "susceptibility") == 0.5


# ---------------------------------------------------------------------------
# Remap semantics
# ---------------------------------------------------------------------------

class TestRemap:
    def test_extreme_composites_map_to_zero_and_one(self, all_composites, bounds):
        low_susc = min(all_composites.values(), key=lambda p: p.susceptibility)
        high_susc = max(all_composites.values(), key=lambda p: p.susceptibility)
        assert designer_scalars(low_susc, bounds).reactivity == pytest.approx(0.0, abs=1e-9)
        assert designer_scalars(high_susc, bounds).reactivity == pytest.approx(1.0, abs=1e-9)

        low_rigid = min(all_composites.values(), key=lambda p: p.rigidity)
        high_rigid = max(all_composites.values(), key=lambda p: p.rigidity)
        assert designer_scalars(low_rigid, bounds).inflexibility == pytest.approx(0.0, abs=1e-9)
        assert designer_scalars(high_rigid, bounds).inflexibility == pytest.approx(1.0, abs=1e-9)

    def test_remap_is_monotonic_for_susceptibility(self, all_composites, bounds):
        profiles = sorted(all_composites.values(), key=lambda p: p.susceptibility)
        reactivities = [designer_scalars(p, bounds).reactivity for p in profiles]
        assert reactivities == sorted(reactivities)

    def test_designer_scalars_in_unit_interval(self, all_composites, bounds):
        for profile in all_composites.values():
            ds = designer_scalars(profile, bounds)
            assert isinstance(ds, DesignerScalars)
            assert 0.0 <= ds.reactivity <= 1.0
            assert 0.0 <= ds.inflexibility <= 1.0
            assert 0.0 <= ds.persistence <= 1.0
            assert ds.flexibility == pytest.approx(1.0 - ds.inflexibility)

    def test_unknown_field_raises(self, bounds):
        with pytest.raises(ValueError, match="Unknown field"):
            bounds.remap(0.5, "assertiveness")


# ---------------------------------------------------------------------------
# apply_designer_scalars (opt-in pipeline)
# ---------------------------------------------------------------------------

class TestApplyDesignerScalars:
    def test_returns_new_profile_without_mutating_original(self, all_composites, bounds):
        raw = all_composites[("INTJ", "Capricorn")]
        calibrated = apply_designer_scalars(raw, bounds)
        assert calibrated is not raw
        assert raw.susceptibility != calibrated.susceptibility or raw.rigidity != calibrated.rigidity

    def test_changes_feel_and_behave_output(self, all_composites, bounds):
        low = min(all_composites.values(), key=lambda p: p.susceptibility)
        high = max(all_composites.values(), key=lambda p: p.susceptibility)
        low_cal = apply_designer_scalars(low, bounds)
        high_cal = apply_designer_scalars(high, bounds)

        situation = MoodVector(-0.5, -0.3, -0.4, -0.2, 0.6)
        stimulus = Stimulus(appraisal=AppraisalVector(-0.3, -0.3))

        low_felt = feel(situation, low)
        high_felt = feel(situation, high)
        low_cal_felt = feel(situation, low_cal)
        high_cal_felt = feel(situation, high_cal)

        raw_delta_gap = (
            high_felt.mood_delta.distress_contentment
            - low_felt.mood_delta.distress_contentment
        )
        cal_delta_gap = (
            high_cal_felt.mood_delta.distress_contentment
            - low_cal_felt.mood_delta.distress_contentment
        )
        assert abs(cal_delta_gap) > abs(raw_delta_gap)

        low_behave = behave(low, stimulus, intensity=0.5, mood=low_felt.new_mood)
        high_behave = behave(high, stimulus, intensity=0.5, mood=high_felt.new_mood)
        low_cal_behave = behave(low_cal, stimulus, intensity=0.5, mood=low_cal_felt.new_mood)
        high_cal_behave = behave(high_cal, stimulus, intensity=0.5, mood=high_cal_felt.new_mood)

        raw_ag_gap = (
            high_behave.behavioral_vector.aggression_passivity
            - low_behave.behavioral_vector.aggression_passivity
        )
        cal_ag_gap = (
            high_cal_behave.behavioral_vector.aggression_passivity
            - low_cal_behave.behavioral_vector.aggression_passivity
        )
        assert abs(cal_ag_gap) >= abs(raw_ag_gap) - 1e-9
