"""Composite generator: blend building blocks into PersonalityProfiles.

Implements the layer dominance model and generates all 192 composites
from 28 building blocks (16 MBTI types × 12 astrological signs).
"""

from __future__ import annotations

from animus.building_blocks import AstrologicalSign, BuildingBlockLibrary, MBTIType
from animus.models import (
    AppraisalVector,
    BehavioralVector,
    MoodVector,
    PersonalityProfile,
    TransformationMatrix,
)


def compute_blend_weight(
    mb_assertiveness: float,
    sign_assertiveness: float,
    global_bias: float = 0.0,
) -> float:
    """Compute the MBTI blend weight from assertiveness ratings.

    The weight determines how much MBTI vs astrology dominates in the composite.

    Args:
        mb_assertiveness: Normalized assertiveness of the MBTI type (0.0-1.0).
        sign_assertiveness: Normalized assertiveness of the sign (0.0-1.0).
        global_bias: Developer dial (-1.0 to +1.0). Positive shifts toward MBTI,
            negative shifts toward astrology. Default 0.0 (neutral).

    Returns:
        mb_weight in [0.05, 0.95]. The sign weight is 1.0 - mb_weight.
    """
    total = mb_assertiveness + sign_assertiveness
    if total == 0:
        base_weight = 0.5
    else:
        base_weight = mb_assertiveness / total

    # Global bias shifts the weight. Max shift magnitude is 0.3.
    shifted = base_weight + global_bias * 0.3
    return max(0.05, min(0.95, shifted))


def blend_composite(
    mb: MBTIType,
    sign: AstrologicalSign,
    global_bias: float = 0.0,
) -> PersonalityProfile:
    """Blend one MBTI type + one astrological sign into a PersonalityProfile."""
    w = compute_blend_weight(mb.assertiveness, sign.assertiveness, global_bias)

    return PersonalityProfile(
        mbti_type=mb.name,
        sign=sign.name,
        resting_mood=_blend_mood(mb.resting_mood, sign.resting_mood, w),
        appraisal_baseline=_blend_appraisal(
            mb.appraisal_baseline, sign.appraisal_baseline, w,
        ),
        transform_matrix=_blend_matrix(mb.transform_matrix, sign.transform_matrix, w),
        susceptibility=_blend_scalar(mb.susceptibility, sign.susceptibility, w),
        rigidity=_blend_scalar(mb.rigidity, sign.rigidity, w),
        rumination=_blend_scalar(mb.rumination, sign.rumination, w),
        behavioral_baseline=_blend_behavioral(
            mb.behavioral_baseline, sign.behavioral_baseline, w,
        ),
    )


def generate_all_composites(
    library: BuildingBlockLibrary,
    global_bias: float = 0.0,
) -> dict[tuple[str, str], PersonalityProfile]:
    """Generate all 192 composites from 28 building blocks.

    Returns:
        Dict keyed by (mbti_type_name, sign_name) tuples.
    """
    composites: dict[tuple[str, str], PersonalityProfile] = {}
    for mb_name, mb in library.mbti_types.items():
        for sign_name, sign in library.signs.items():
            composites[(mb_name, sign_name)] = blend_composite(mb, sign, global_bias)
    return composites


# ---------------------------------------------------------------------------
# Blending helpers
# ---------------------------------------------------------------------------

def _blend_scalar(mb_val: float, sign_val: float, mb_weight: float) -> float:
    return mb_val * mb_weight + sign_val * (1.0 - mb_weight)


def _blend_mood(mb: MoodVector, sign: MoodVector, mb_weight: float) -> MoodVector:
    sw = 1.0 - mb_weight
    return MoodVector(
        distress_contentment=mb.distress_contentment * mb_weight + sign.distress_contentment * sw,
        fear_confidence=mb.fear_confidence * mb_weight + sign.fear_confidence * sw,
        isolation_belonging=mb.isolation_belonging * mb_weight + sign.isolation_belonging * sw,
        shame_pride=mb.shame_pride * mb_weight + sign.shame_pride * sw,
        arousal=mb.arousal * mb_weight + sign.arousal * sw,
    )


def _blend_behavioral(
    mb: BehavioralVector, sign: BehavioralVector, mb_weight: float,
) -> BehavioralVector:
    sw = 1.0 - mb_weight
    return BehavioralVector(
        aggression_passivity=mb.aggression_passivity * mb_weight + sign.aggression_passivity * sw,
        impulsiveness_deliberation=mb.impulsiveness_deliberation * mb_weight + sign.impulsiveness_deliberation * sw,
        sociability_withdrawal=mb.sociability_withdrawal * mb_weight + sign.sociability_withdrawal * sw,
        empathy_self_interest=mb.empathy_self_interest * mb_weight + sign.empathy_self_interest * sw,
        curiosity_avoidance=mb.curiosity_avoidance * mb_weight + sign.curiosity_avoidance * sw,
    )


def _blend_appraisal(
    mb: AppraisalVector, sign: AppraisalVector, mb_weight: float,
) -> AppraisalVector:
    sw = 1.0 - mb_weight
    return AppraisalVector(
        control=mb.control * mb_weight + sign.control * sw,
        certainty=mb.certainty * mb_weight + sign.certainty * sw,
    )


def _blend_matrix(
    mb: TransformationMatrix, sign: TransformationMatrix, mb_weight: float,
) -> TransformationMatrix:
    sw = 1.0 - mb_weight
    rows = []
    for i in range(5):
        row = tuple(
            mb.rows[i][j] * mb_weight + sign.rows[i][j] * sw
            for j in range(5)
        )
        rows.append(row)
    return TransformationMatrix(rows=tuple(rows))
