"""Behave mode — the transformation pipeline.

Takes a personality, stimulus, intensity, and optional mood, and returns
a behavioral vector describing how the character acts.

Pipeline:
  1. appraisal = personality.appraisal_baseline + stimulus.appraisal
  2. modulated_matrix = personality.transform_matrix × appraisal_weights(appraisal)
  3. flexibility = 1 - rigidity
     behavioral_offset = modulated_matrix × mood × susceptibility × flexibility
  4. personality_output = personality.behavioral_baseline + behavioral_offset
  5. gained = personality_output × gain(intensity)
     where gain = 1 + intensity × (MAX_INTENSITY_GAIN - 1)
     intensity 0 → current (unamplified) signal; intensity 1 → max gain
  6. final_output = clamp(gained, -1.0, 1.0)
"""

from __future__ import annotations

import random

from animus.models import (
    AppraisalVector,
    BehaveResult,
    BehavioralVector,
    MoodVector,
    PersonalityProfile,
    Stimulus,
)

# At intensity=1.0, personality_output is scaled by this factor.
# intensity=0.0 leaves the authored signal unchanged (gain 1.0).
MAX_INTENSITY_GAIN = 4.0


def behave(
    personality: PersonalityProfile,
    stimulus: Stimulus,
    intensity: float,
    mood: MoodVector | None = None,
    *,
    rng: random.Random | None = None,
) -> BehaveResult:
    """Run the Behave mode transformation pipeline.

    Args:
        personality: The character's personality profile.
        stimulus: Description of the situation.
        intensity: Output gain control (0.0–1.0).
            0.0 = unamplified personality signal (baseline + mood offset).
            1.0 = maximum gain (see MAX_INTENSITY_GAIN).
        mood: Current mood state. If None, uses resting baseline.
        rng: Accepted for API compatibility; intensity no longer mixes noise,
            so output is deterministic for the same inputs.

    Returns:
        BehaveResult with behavioral_vector, conflict_flag, rigidity_indicator,
        flexibility_factor, and deviation_amount.
    """
    del rng  # Noise override removed; keep parameter for call-site compatibility.

    mood = mood if mood is not None else personality.resting_mood
    intensity = max(0.0, min(1.0, intensity))

    # Step 1: Resolve appraisal
    appraisal = AppraisalVector(
        control=personality.appraisal_baseline.control + stimulus.appraisal.control,
        certainty=personality.appraisal_baseline.certainty + stimulus.appraisal.certainty,
    ).clamped()

    # Step 2: Modulate transformation matrix by appraisal
    appraisal_weights = _compute_appraisal_weights(appraisal)
    modulated_matrix = personality.transform_matrix.scale(appraisal_weights)

    # Step 3: offset = matrix × mood × susceptibility × flexibility
    # High rigidity keeps the pawn closer to behavioral_baseline.
    mood_list = mood.to_list()
    raw_offset = modulated_matrix.multiply(mood_list)
    rigidity = max(0.0, min(1.0, personality.rigidity))
    flexibility = 1.0 - rigidity
    scale = personality.susceptibility * flexibility
    behavioral_offset = [v * scale for v in raw_offset]

    # Step 4: personality_output = behavioral_baseline + behavioral_offset
    baseline = personality.behavioral_baseline.to_list()
    personality_output = [baseline[i] + behavioral_offset[i] for i in range(5)]

    # Step 5: Intensity as output gain (not noise mix)
    gain = 1.0 + intensity * (MAX_INTENSITY_GAIN - 1.0)
    gained = [personality_output[i] * gain for i in range(5)]

    # Step 6: Clamp to valid range
    final = BehavioralVector.from_list(gained).clamped()

    # Compute metadata
    deviation = _deviation(personality.behavioral_baseline, final)

    return BehaveResult(
        behavioral_vector=final,
        conflict_flag=False,  # No external pressure in Phase 1
        rigidity_indicator=personality.rigidity,
        flexibility_factor=flexibility,
        deviation_amount=deviation,
    )


def _compute_appraisal_weights(appraisal: AppraisalVector) -> list[list[float]]:
    """Convert appraisal values into per-cell scaling factors for the transformation matrix.

    The appraisal layer modulates *which version* of the mood-to-behavior mapping is active.

    - High control amplifies pathways converting negative mood → active responses
      (fear→aggression, distress→determination) and dampens passive pathways.
    - Low control amplifies passive pathways (fear→withdrawal, distress→passivity).
    - High certainty amplifies deliberation pathways, dampens impulsive ones.
    - Low certainty amplifies impulsive pathways.

    Returns a 5x5 weight matrix where each cell is a multiplier for the
    corresponding transformation matrix cell.
    """
    ctrl = appraisal.control      # -1 (helpless) to +1 (agentic)
    cert = appraisal.certainty    # -1 (uncertain) to +1 (predictable)

    # Base weight is 1.0; appraisal shifts it up or down.
    # Scale factor: 1.0 + (appraisal_value * direction * magnitude)
    # Direction indicates whether high appraisal amplifies (+) or dampens (-) this pathway.

    # Row 0: aggression — high control amplifies (agentic → fight), high certainty amplifies
    # Row 1: impulsiveness — low certainty amplifies (uncertainty → react fast)
    # Row 2: sociability — high control slightly amplifies (agentic → engage)
    # Row 3: empathy — low control slightly amplifies (helpless → seek help)
    # Row 4: curiosity — high certainty dampens (known → less to explore), high control amplifies

    def w(ctrl_dir: float, cert_dir: float, magnitude: float = 0.5) -> float:
        return 1.0 + (ctrl * ctrl_dir + cert * cert_dir) * magnitude

    weights = [
        # aggression row: control amplifies, certainty slightly amplifies
        [w(0.4, 0.1), w(0.5, 0.1), w(0.1, 0.0), w(0.1, 0.0), w(0.2, 0.1)],
        # impulsiveness row: certainty amplifies deliberation pathways (matrix values are positive=deliberate)
        [w(0.0, 0.3), w(0.0, 0.4), w(0.0, 0.1), w(0.0, 0.2), w(-0.1, 0.3)],
        # sociability row: control slightly amplifies
        [w(0.2, 0.0), w(0.2, 0.0), w(0.1, 0.0), w(0.1, 0.0), w(0.0, 0.0)],
        # empathy row: low control amplifies (helpless → seek connection)
        [w(-0.2, 0.0), w(-0.2, 0.0), w(-0.1, 0.0), w(-0.2, 0.0), w(0.0, 0.0)],
        # curiosity row: high control amplifies, high certainty dampens
        [w(0.2, -0.2), w(0.1, -0.1), w(0.1, -0.1), w(0.0, 0.0), w(0.2, -0.3)],
    ]
    return weights


def _deviation(baseline: BehavioralVector, result: BehavioralVector) -> float:
    """Euclidean distance between baseline and result, normalized to [0, 1]."""
    b = baseline.to_list()
    r = result.to_list()
    squared_sum = sum((b[i] - r[i]) ** 2 for i in range(5))
    # Max possible distance in 5D bipolar space: sqrt(5 * (2.0)^2) = sqrt(20) ≈ 4.47
    max_dist = 20.0 ** 0.5
    return min(1.0, squared_sum ** 0.5 / max_dist)
