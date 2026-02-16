"""Decay utility — mood exponentially decays toward resting baseline.

Rate controlled by personality's rumination coefficient.
High rumination = mood lingers longer.
Low rumination = quick return to baseline.

elapsed is abstract (time steps, interaction count, etc.).
"""

from __future__ import annotations

import math

from animus.models import MoodVector, PersonalityProfile


def decay(
    personality: PersonalityProfile,
    current_mood: MoodVector | list[float],
    elapsed: float,
) -> MoodVector:
    """Decay mood toward personality's resting baseline.

    Formula (per axis):
        decayed[axis] = resting[axis] + (current[axis] - resting[axis]) × e^(-elapsed / rumination)

    Args:
        personality: Character's profile (provides resting_mood and rumination).
        current_mood: Current mood state.
        elapsed: Abstract elapsed units (time or interaction count).

    Returns:
        Decayed mood vector.
    """
    current = _to_mood_vector(current_mood)
    resting = personality.resting_mood
    tau = max(personality.rumination, 0.01)  # Avoid division by zero
    factor = math.exp(-elapsed / tau)

    return MoodVector(
        distress_contentment=resting.distress_contentment
        + (current.distress_contentment - resting.distress_contentment) * factor,
        fear_confidence=resting.fear_confidence
        + (current.fear_confidence - resting.fear_confidence) * factor,
        isolation_belonging=resting.isolation_belonging
        + (current.isolation_belonging - resting.isolation_belonging) * factor,
        shame_pride=resting.shame_pride
        + (current.shame_pride - resting.shame_pride) * factor,
        arousal=resting.arousal + (current.arousal - resting.arousal) * factor,
    ).clamped()


def _to_mood_vector(v: MoodVector | list[float]) -> MoodVector:
    if isinstance(v, MoodVector):
        return v
    if isinstance(v, (list, tuple)) and len(v) >= 5:
        return MoodVector.from_list(list(v)[:5])
    raise TypeError("current_mood must be MoodVector or list[float] of length 5")
