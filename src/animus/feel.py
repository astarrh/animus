"""Feel mode — situation → mood delta, modulated by personality.

Takes a raw mood-space vector (the situation's base effect), a personality,
and optional current mood. Returns the modulated mood delta and resulting mood.

Pipeline:
  1. Treat situation_vector as base mood-space delta (developer-provided)
  2. Modulate by personality susceptibility (scales delta magnitude)
  3. Apply modulated delta to current mood (or resting baseline if omitted)
  4. Clamp result to valid ranges
  5. Return mood_delta + new_mood
"""

from __future__ import annotations

from animus.models import FeelResult, MoodVector, PersonalityProfile


def feel(
    situation_vector: MoodVector | list[float],
    personality: PersonalityProfile,
    current_mood: MoodVector | list[float] | None = None,
) -> FeelResult:
    """Compute personality-modulated mood change from a situation.

    Args:
        situation_vector: Raw mood-space delta (dc, fc, ib, sp, arousal).
            Developer maps game events to this; engine does not resolve keywords.
        personality: The character's personality profile.
        current_mood: Current mood state. If None, uses personality.resting_mood.

    Returns:
        FeelResult with mood_delta (modulated change applied) and new_mood (result).
    """
    # Normalize inputs
    situation = _to_mood_vector(situation_vector)
    current = _to_mood_vector(current_mood) if current_mood is not None else personality.resting_mood

    # Modulate delta by susceptibility (per-axis scaling)
    modulated = MoodVector(
        distress_contentment=situation.distress_contentment * personality.susceptibility,
        fear_confidence=situation.fear_confidence * personality.susceptibility,
        isolation_belonging=situation.isolation_belonging * personality.susceptibility,
        shame_pride=situation.shame_pride * personality.susceptibility,
        arousal=situation.arousal * personality.susceptibility,
    )

    # Apply to current mood and clamp
    raw_new = MoodVector(
        distress_contentment=current.distress_contentment + modulated.distress_contentment,
        fear_confidence=current.fear_confidence + modulated.fear_confidence,
        isolation_belonging=current.isolation_belonging + modulated.isolation_belonging,
        shame_pride=current.shame_pride + modulated.shame_pride,
        arousal=current.arousal + modulated.arousal,
    )
    new_mood = raw_new.clamped()

    return FeelResult(mood_delta=modulated, new_mood=new_mood)


def _to_mood_vector(v: MoodVector | list[float]) -> MoodVector:
    if isinstance(v, MoodVector):
        return v
    if isinstance(v, (list, tuple)) and len(v) >= 5:
        return MoodVector.from_list(list(v)[:5])
    raise TypeError("situation_vector must be MoodVector or list[float] of length 5")
