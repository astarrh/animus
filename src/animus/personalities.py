"""Hardcoded personality profiles for Phase 1.

Coefficients extracted from personality_building_blocks.xlsx via
scripts/extract_coefficients.py. Transformation matrix authored manually.
"""

from animus.models import (
    AppraisalVector,
    BehavioralVector,
    MoodVector,
    PersonalityProfile,
    TransformationMatrix,
)

# ---------------------------------------------------------------------------
# Raw extracted values (pre-normalization sums)
# ---------------------------------------------------------------------------

# INTJ = I(0.35) + N(0.50) + T(0.60) + J(0.55) etc.
_INTJ_RAW = {
    "assertiveness": 2.00,
    "susceptibility": 1.65,
    "rigidity": 2.20,
    "rumination": 1.95,
    "control": 0.25,
    "certainty": 0.15,
}

# Capricorn = Earth + Cardinal + Capricorn tweak
_CAP_RAW = {
    "assertiveness": 1.05,
    "susceptibility": 0.70,
    "rigidity": 1.10,
    "rumination": 0.90,
    "control": 0.30,
    "certainty": 0.30,
}


# ---------------------------------------------------------------------------
# Normalization
# ---------------------------------------------------------------------------
# MBTI sums: 4 poles each contributing 0.0-1.0, so raw range is [0.0, 4.0].
#   Normalize by dividing by 4 → coefficient range [0.0, 1.0].
# Sign sums: element (0.0-1.0) + modality (0.0-1.0) + tweak (small delta).
#   Raw range is roughly [0.0, 2.0+]. Normalize by dividing by 2 → [0.0, 1.0].
# Appraisal sums: component values are already in [-1.0, 1.0] range but sum
#   of 4 poles can reach [-4.0, 4.0] for MBTI. Normalize by dividing by 4.
#   Sign appraisals: sum of 3 components, normalize by dividing by 2.
#   Then clamp to [-1.0, 1.0].

_MBTI_COEFF_DIVISOR = 4.0
_SIGN_COEFF_DIVISOR = 2.0
_MBTI_APPRAISAL_DIVISOR = 4.0
_SIGN_APPRAISAL_DIVISOR = 2.0


def _normalize_coeff(raw: float, divisor: float) -> float:
    return max(0.0, min(1.0, raw / divisor))


def _normalize_appraisal(raw: float, divisor: float) -> float:
    return max(-1.0, min(1.0, raw / divisor))


def _blend(mb_val: float, sign_val: float, mb_weight: float) -> float:
    return mb_val * mb_weight + sign_val * (1.0 - mb_weight)


# Normalized INTJ coefficients
_INTJ = {k: _normalize_coeff(v, _MBTI_COEFF_DIVISOR) for k, v in _INTJ_RAW.items()
         if k not in ("control", "certainty")}
_INTJ["control"] = _normalize_appraisal(_INTJ_RAW["control"], _MBTI_APPRAISAL_DIVISOR)
_INTJ["certainty"] = _normalize_appraisal(_INTJ_RAW["certainty"], _MBTI_APPRAISAL_DIVISOR)

# Normalized Capricorn coefficients
_CAP = {k: _normalize_coeff(v, _SIGN_COEFF_DIVISOR) for k, v in _CAP_RAW.items()
        if k not in ("control", "certainty")}
_CAP["control"] = _normalize_appraisal(_CAP_RAW["control"], _SIGN_APPRAISAL_DIVISOR)
_CAP["certainty"] = _normalize_appraisal(_CAP_RAW["certainty"], _SIGN_APPRAISAL_DIVISOR)


# ---------------------------------------------------------------------------
# Layer dominance — INTJ-Capricorn blend weights
# ---------------------------------------------------------------------------
# INTJ assertiveness (normalized): 0.50, Capricorn assertiveness: 0.525
# These are close, so both layers have roughly equal say.
# Using the simpler approach: mb_weight = mb_assert / (mb_assert + sign_assert)
_mb_assert = _INTJ["assertiveness"]
_sign_assert = _CAP["assertiveness"]
_MB_WEIGHT = _mb_assert / (_mb_assert + _sign_assert)  # ~0.488

# Blended scalar coefficients
_susceptibility = _blend(_INTJ["susceptibility"], _CAP["susceptibility"], _MB_WEIGHT)
_rigidity = _blend(_INTJ["rigidity"], _CAP["rigidity"], _MB_WEIGHT)
_rumination = _blend(_INTJ["rumination"], _CAP["rumination"], _MB_WEIGHT)
_control = _blend(_INTJ["control"], _CAP["control"], _MB_WEIGHT)
_certainty = _blend(_INTJ["certainty"], _CAP["certainty"], _MB_WEIGHT)


# ---------------------------------------------------------------------------
# Transformation matrix: INTJ-Capricorn
# ---------------------------------------------------------------------------
# Rows = behavioral dimensions: aggression, impulsiveness, sociability, empathy, curiosity
# Cols = mood dimensions: distress_content, fear_confid, isol_belong, shame_pride, arousal
#
# Design rationale for INTJ-Capricorn:
# - Strategic, independent, decisive, disciplined
# - Low emotional susceptibility (Thinking + Earth)
# - High rigidity (Judging + Cardinal)
# - Favors deliberation, self-reliance, and controlled responses
# - Fear → deliberate action (not panic), distress → withdrawal rather than aggression
# - High control appraisal means negative moods become focused rather than scattered
#
# Values are intentionally moderate because susceptibility further scales the offset.

_INTJ_CAP_MATRIX = TransformationMatrix(rows=(
    # aggression ← mood
    #   distress→slight aggression, fear→slight aggression (controlled pushback),
    #   isolation→neutral, shame→suppressed, arousal→mild activation
    (-0.15, -0.20, 0.00, -0.05, 0.15),

    # impulsiveness ← mood (INTJ-Cap is strongly deliberate)
    #   distress→more deliberate, fear→more deliberate, isolation→neutral,
    #   shame→more deliberate (reflects before acting), arousal→slight impulse
    (0.10, 0.15, 0.00, 0.10, -0.10),

    # sociability ← mood
    #   distress→withdraw, fear→withdraw, isolation doesn't increase sociability
    #   (INTJ doesn't seek comfort in others), shame→withdraw, arousal→neutral
    (0.10, 0.10, -0.10, 0.15, 0.00),

    # empathy ← mood
    #   Generally self-interested under stress. Distress→self-focus,
    #   fear→self-focus, isolation→slight self-focus, shame→self-focus, arousal→neutral
    (0.05, 0.05, 0.05, 0.10, 0.00),

    # curiosity ← mood
    #   INTJ is naturally curious but stress dampens it.
    #   Distress→avoidance, fear→avoidance, isolation→slight curiosity (fills time),
    #   shame→avoidance, arousal→curiosity (activation engages the mind)
    (0.10, 0.10, -0.05, 0.05, -0.20),
))

# ---------------------------------------------------------------------------
# Resting baselines
# ---------------------------------------------------------------------------
# INTJ-Capricorn at rest: slightly content (disciplined satisfaction),
# confident, slightly isolated (independent, not lonely), neutral pride,
# low-moderate arousal (steady, not excitable).

_RESTING_MOOD = MoodVector(
    distress_contentment=0.15,
    fear_confidence=0.25,
    isolation_belonging=-0.10,
    shame_pride=0.10,
    arousal=0.3,
)

# Behavioral baseline: slightly passive (waits for good reason to act),
# deliberate (J + earth), withdrawn (I + earth), slightly self-interested (T),
# mildly curious (N).
_BEHAVIORAL_BASELINE = BehavioralVector(
    aggression_passivity=-0.10,
    impulsiveness_deliberation=-0.30,
    sociability_withdrawal=-0.25,
    empathy_self_interest=0.15,
    curiosity_avoidance=0.10,
)


# ---------------------------------------------------------------------------
# The complete INTJ-Capricorn profile
# ---------------------------------------------------------------------------

INTJ_CAPRICORN = PersonalityProfile(
    mbti_type="INTJ",
    sign="Capricorn",
    resting_mood=_RESTING_MOOD,
    appraisal_baseline=AppraisalVector(control=_control, certainty=_certainty),
    transform_matrix=_INTJ_CAP_MATRIX,
    susceptibility=_susceptibility,
    rigidity=_rigidity,
    rumination=_rumination,
    behavioral_baseline=_BEHAVIORAL_BASELINE,
)


# ===========================================================================
# ESTP-Aries — The bold, impulsive, action-first foil
# ===========================================================================

# ---------------------------------------------------------------------------
# Raw extracted values (pre-normalization sums)
# ---------------------------------------------------------------------------

# ESTP = E(0.55) + S(0.40) + T(0.60) + P(0.35) etc.
_ESTP_RAW = {
    "assertiveness": 1.90,
    "susceptibility": 1.70,
    "rigidity": 1.75,
    "rumination": 1.50,
    "control": 0.25,
    "certainty": 0.20,
}

# Aries = Fire + Cardinal + Aries tweak
_ARIES_RAW = {
    "assertiveness": 1.15,
    "susceptibility": 1.00,
    "rigidity": 0.90,
    "rumination": 0.70,
    "control": 0.30,
    "certainty": 0.00,
}

# Normalized ESTP coefficients
_ESTP = {k: _normalize_coeff(v, _MBTI_COEFF_DIVISOR) for k, v in _ESTP_RAW.items()
         if k not in ("control", "certainty")}
_ESTP["control"] = _normalize_appraisal(_ESTP_RAW["control"], _MBTI_APPRAISAL_DIVISOR)
_ESTP["certainty"] = _normalize_appraisal(_ESTP_RAW["certainty"], _MBTI_APPRAISAL_DIVISOR)

# Normalized Aries coefficients
_ARIES = {k: _normalize_coeff(v, _SIGN_COEFF_DIVISOR) for k, v in _ARIES_RAW.items()
          if k not in ("control", "certainty")}
_ARIES["control"] = _normalize_appraisal(_ARIES_RAW["control"], _SIGN_APPRAISAL_DIVISOR)
_ARIES["certainty"] = _normalize_appraisal(_ARIES_RAW["certainty"], _SIGN_APPRAISAL_DIVISOR)

# ---------------------------------------------------------------------------
# Layer dominance — ESTP-Aries blend weights
# ---------------------------------------------------------------------------
# ESTP assertiveness (normalized): 0.475, Aries assertiveness: 0.575
# Aries is slightly more assertive → astrology has a slight edge.
_estp_mb_assert = _ESTP["assertiveness"]
_aries_sign_assert = _ARIES["assertiveness"]
_ESTP_MB_WEIGHT = _estp_mb_assert / (_estp_mb_assert + _aries_sign_assert)  # ~0.452

# Blended scalar coefficients
_estp_susceptibility = _blend(_ESTP["susceptibility"], _ARIES["susceptibility"], _ESTP_MB_WEIGHT)
_estp_rigidity = _blend(_ESTP["rigidity"], _ARIES["rigidity"], _ESTP_MB_WEIGHT)
_estp_rumination = _blend(_ESTP["rumination"], _ARIES["rumination"], _ESTP_MB_WEIGHT)
_estp_control = _blend(_ESTP["control"], _ARIES["control"], _ESTP_MB_WEIGHT)
_estp_certainty = _blend(_ESTP["certainty"], _ARIES["certainty"], _ESTP_MB_WEIGHT)


# ---------------------------------------------------------------------------
# Transformation matrix: ESTP-Aries
# ---------------------------------------------------------------------------
# Rows = behavioral dimensions: aggression, impulsiveness, sociability, empathy, curiosity
# Cols = mood dimensions: distress_content, fear_confid, isol_belong, shame_pride, arousal
#
# Design rationale for ESTP-Aries:
# - Bold, action-oriented, lives in the moment, competitive
# - Moderate-high susceptibility (Perceiving + Fire sign)
# - Low-moderate rigidity (Perceiving + Cardinal, but fire's adaptability)
# - Fear → aggression (fight response), distress → action (do something about it)
# - Arousal strongly amplifies impulsiveness and aggression
# - Shame barely registers, doesn't linger
# - Isolation → seek others (extraverted), not withdraw

_ESTP_ARIES_MATRIX = TransformationMatrix(rows=(
    # aggression ← mood
    #   distress→aggression (fight the problem), fear→aggression (fight response),
    #   isolation→mild aggression (frustrated), shame→ignored, arousal→strong aggression
    (-0.25, -0.30, -0.10, -0.05, 0.35),

    # impulsiveness ← mood (ESTP-Aries is naturally impulsive)
    #   distress→more impulsive (act now!), fear→impulsive (react!),
    #   isolation→neutral, shame→neutral, arousal→strongly impulsive
    (-0.15, -0.20, 0.00, 0.00, -0.30),

    # sociability ← mood
    #   distress→seek others (extraverted coping), fear→seek allies,
    #   isolation→strongly seek others, shame→slight withdrawal (rare vulnerability),
    #   arousal→more social (energized)
    (-0.10, -0.05, -0.30, 0.10, -0.15),

    # empathy ← mood
    #   Generally self-interested under stress but less extreme than INTJ.
    #   distress→self-focus, fear→self-focus, isolation→neutral, shame→neutral,
    #   arousal→slight self-interest (competitive energy)
    (0.05, 0.10, 0.00, 0.00, 0.10),

    # curiosity ← mood
    #   ESTP is curious about immediate, tangible things.
    #   distress→approach (investigate the problem), fear→approach (confront it),
    #   isolation→curious (find something to do), shame→neutral,
    #   arousal→strongly curious (activated = engaged)
    (-0.10, -0.10, -0.10, 0.00, -0.25),
))

# ---------------------------------------------------------------------------
# Resting baselines — ESTP-Aries
# ---------------------------------------------------------------------------
# At rest: content (uncomplicated satisfaction), confident (bold),
# slightly belonging (social, part of the group), neutral pride,
# moderate-high arousal (always a bit activated, ready to go).

_ESTP_RESTING_MOOD = MoodVector(
    distress_contentment=0.20,
    fear_confidence=0.35,
    isolation_belonging=0.15,
    shame_pride=0.05,
    arousal=0.5,
)

# Behavioral baseline: aggressive (confrontational, assertive),
# impulsive (P + fire), sociable (E + fire), slightly self-interested (T),
# curious (S + fire — engaged with the immediate world).
_ESTP_BEHAVIORAL_BASELINE = BehavioralVector(
    aggression_passivity=0.25,
    impulsiveness_deliberation=0.30,
    sociability_withdrawal=0.30,
    empathy_self_interest=0.10,
    curiosity_avoidance=0.20,
)


# ---------------------------------------------------------------------------
# The complete ESTP-Aries profile
# ---------------------------------------------------------------------------

ESTP_ARIES = PersonalityProfile(
    mbti_type="ESTP",
    sign="Aries",
    resting_mood=_ESTP_RESTING_MOOD,
    appraisal_baseline=AppraisalVector(control=_estp_control, certainty=_estp_certainty),
    transform_matrix=_ESTP_ARIES_MATRIX,
    susceptibility=_estp_susceptibility,
    rigidity=_estp_rigidity,
    rumination=_estp_rumination,
    behavioral_baseline=_ESTP_BEHAVIORAL_BASELINE,
)
