"""Reference behavioral envelopes for designer threshold authoring.

Runs the full ``feel`` → ``behave`` loop on a shipped severity ladder so
authors can read a pawn's outer limits without playtesting every composite.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass

from animus.behave import behave
from animus.designer import ScalarBounds, designer_scalars
from animus.feel import feel
from animus.models import (
    AppraisalVector,
    BehavioralVector,
    MoodVector,
    PersonalityProfile,
    Stimulus,
)

BEHAVIORAL_AXES = (
    "aggression_passivity",
    "impulsiveness_deliberation",
    "sociability_withdrawal",
    "empathy_self_interest",
    "curiosity_avoidance",
)


@dataclass(frozen=True)
class ReferenceSituation:
    """A named stress probe for envelope computation."""

    name: str
    situation: MoodVector
    appraisal: AppraisalVector
    intensity: float
    description: str


REFERENCE_SITUATIONS: tuple[ReferenceSituation, ...] = (
    ReferenceSituation(
        name="resting",
        situation=MoodVector(0.0, 0.0, 0.0, 0.0, 0.0),
        appraisal=AppraisalVector(0.0, 0.0),
        intensity=0.0,
        description="Baseline at equilibrium (no event, unamplified intensity).",
    ),
    ReferenceSituation(
        name="mild_irritation",
        situation=MoodVector(-0.25, 0.10, -0.20, 0.15, 0.35),
        appraisal=AppraisalVector(0.25, -0.20),
        intensity=0.5,
        description="Everyday friction (e.g. petty disagreement).",
    ),
    ReferenceSituation(
        name="moderate_conflict",
        situation=MoodVector(-0.50, -0.30, -0.40, -0.20, 0.60),
        appraisal=AppraisalVector(-0.30, -0.30),
        intensity=0.5,
        description="Clear interpersonal stress.",
    ),
    ReferenceSituation(
        name="severe_crisis",
        situation=MoodVector(-0.80, -0.70, -0.60, -0.50, 0.90),
        appraisal=AppraisalVector(-0.50, -0.60),
        intensity=1.0,
        description="Breaking-point probe (max intensity).",
    ),
)


@dataclass(frozen=True)
class AxisEnvelope:
    """Min/max of one output axis across reference situations."""

    min: float
    max: float
    at_resting: float

    def to_dict(self) -> dict[str, float]:
        return {"min": self.min, "max": self.max, "at_resting": self.at_resting}


@dataclass(frozen=True)
class BehavioralEnvelope:
    """Per-axis outer limits for one personality under the reference ladder."""

    aggression_passivity: AxisEnvelope
    impulsiveness_deliberation: AxisEnvelope
    sociability_withdrawal: AxisEnvelope
    empathy_self_interest: AxisEnvelope
    curiosity_avoidance: AxisEnvelope
    deviation_amount: AxisEnvelope

    def to_dict(self) -> dict[str, dict[str, float]]:
        return {
            "aggression_passivity": self.aggression_passivity.to_dict(),
            "impulsiveness_deliberation": self.impulsiveness_deliberation.to_dict(),
            "sociability_withdrawal": self.sociability_withdrawal.to_dict(),
            "empathy_self_interest": self.empathy_self_interest.to_dict(),
            "curiosity_avoidance": self.curiosity_avoidance.to_dict(),
            "deviation_amount": self.deviation_amount.to_dict(),
        }


def probe_situation(
    profile: PersonalityProfile,
    situation: ReferenceSituation,
) -> tuple[BehavioralVector, float]:
    """Run feel → behave for one reference situation; return vector and deviation."""
    felt = feel(
        situation.situation,
        profile,
        current_mood=profile.resting_mood,
    )
    out = behave(
        profile,
        Stimulus(appraisal=situation.appraisal),
        situation.intensity,
        mood=felt.new_mood,
    )
    return out.behavioral_vector, out.deviation_amount


def compute_envelope(
    profile: PersonalityProfile,
    situations: Sequence[ReferenceSituation] = REFERENCE_SITUATIONS,
) -> BehavioralEnvelope:
    """Aggregate min/max behavioral output across reference situations."""
    if not situations:
        raise ValueError("cannot compute envelope from an empty situation list")

    samples: dict[str, list[float]] = {axis: [] for axis in BEHAVIORAL_AXES}
    samples["deviation_amount"] = []
    resting_values: dict[str, float] | None = None

    for sit in situations:
        vector, deviation = probe_situation(profile, sit)
        values = dict(zip(BEHAVIORAL_AXES, vector.to_list()))
        values["deviation_amount"] = deviation
        for key, value in values.items():
            samples[key].append(value)
        if sit.name == "resting" or resting_values is None:
            resting_values = values

    assert resting_values is not None

    def _axis(name: str) -> AxisEnvelope:
        vals = samples[name]
        return AxisEnvelope(
            min=min(vals),
            max=max(vals),
            at_resting=resting_values[name],
        )

    return BehavioralEnvelope(
        aggression_passivity=_axis("aggression_passivity"),
        impulsiveness_deliberation=_axis("impulsiveness_deliberation"),
        sociability_withdrawal=_axis("sociability_withdrawal"),
        empathy_self_interest=_axis("empathy_self_interest"),
        curiosity_avoidance=_axis("curiosity_avoidance"),
        deviation_amount=_axis("deviation_amount"),
    )


def compute_all_envelopes(
    composites: Mapping[tuple[str, str], PersonalityProfile],
    situations: Sequence[ReferenceSituation] = REFERENCE_SITUATIONS,
) -> dict[tuple[str, str], BehavioralEnvelope]:
    """Compute envelopes for every composite in a library."""
    return {
        key: compute_envelope(profile, situations)
        for key, profile in composites.items()
    }


def character_card(
    profile: PersonalityProfile,
    bounds: ScalarBounds,
    situations: Sequence[ReferenceSituation] = REFERENCE_SITUATIONS,
) -> dict:
    """Human- and machine-readable summary for designer tools."""
    ds = designer_scalars(profile, bounds)
    envelope = compute_envelope(profile, situations)
    return {
        "mbti_type": profile.mbti_type,
        "sign": profile.sign,
        "designer_scalars": {
            "reactivity": ds.reactivity,
            "inflexibility": ds.inflexibility,
            "persistence": ds.persistence,
            "flexibility": ds.flexibility,
        },
        "envelope": envelope.to_dict(),
        "reference_situations": [sit.name for sit in situations],
    }


def character_cards(
    composites: Mapping[tuple[str, str], PersonalityProfile],
    bounds: ScalarBounds,
    situations: Sequence[ReferenceSituation] = REFERENCE_SITUATIONS,
) -> dict[tuple[str, str], dict]:
    """Build character cards for every composite in a library."""
    return {
        key: character_card(profile, bounds, situations)
        for key, profile in composites.items()
    }
