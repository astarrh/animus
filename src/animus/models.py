"""Core data structures for the Animus personality engine."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class MoodVector:
    """Internal emotional state in mood space.

    First four axes are bipolar (-1.0 to +1.0). Arousal is unipolar (0.0 to 1.0).
    """

    distress_contentment: float = 0.0
    fear_confidence: float = 0.0
    isolation_belonging: float = 0.0
    shame_pride: float = 0.0
    arousal: float = 0.0

    def to_list(self) -> list[float]:
        return [
            self.distress_contentment,
            self.fear_confidence,
            self.isolation_belonging,
            self.shame_pride,
            self.arousal,
        ]

    @classmethod
    def from_list(cls, values: list[float]) -> MoodVector:
        return cls(*values)

    def clamped(self) -> MoodVector:
        return MoodVector(
            distress_contentment=_clamp_bipolar(self.distress_contentment),
            fear_confidence=_clamp_bipolar(self.fear_confidence),
            isolation_belonging=_clamp_bipolar(self.isolation_belonging),
            shame_pride=_clamp_bipolar(self.shame_pride),
            arousal=_clamp_unipolar(self.arousal),
        )


@dataclass(frozen=True)
class BehavioralVector:
    """External action tendencies in behavioral space. All axes bipolar (-1.0 to +1.0)."""

    aggression_passivity: float = 0.0
    impulsiveness_deliberation: float = 0.0
    sociability_withdrawal: float = 0.0
    empathy_self_interest: float = 0.0
    curiosity_avoidance: float = 0.0

    def to_list(self) -> list[float]:
        return [
            self.aggression_passivity,
            self.impulsiveness_deliberation,
            self.sociability_withdrawal,
            self.empathy_self_interest,
            self.curiosity_avoidance,
        ]

    @classmethod
    def from_list(cls, values: list[float]) -> BehavioralVector:
        return cls(*values)

    def clamped(self) -> BehavioralVector:
        return BehavioralVector(*[_clamp_bipolar(v) for v in self.to_list()])


@dataclass(frozen=True)
class AppraisalVector:
    """Cognitive appraisal state. Both axes bipolar (-1.0 to +1.0)."""

    control: float = 0.0
    certainty: float = 0.0

    def to_list(self) -> list[float]:
        return [self.control, self.certainty]

    @classmethod
    def from_list(cls, values: list[float]) -> AppraisalVector:
        return cls(*values)

    def clamped(self) -> AppraisalVector:
        return AppraisalVector(
            control=_clamp_bipolar(self.control),
            certainty=_clamp_bipolar(self.certainty),
        )


@dataclass(frozen=True)
class TransformationMatrix:
    """5x5 matrix mapping mood space to behavioral space.

    rows[i][j] = how mood dimension j influences behavioral dimension i.
    Row order: aggression, impulsiveness, sociability, empathy, curiosity.
    Column order: distress_contentment, fear_confidence, isolation_belonging, shame_pride, arousal.
    """

    rows: tuple[tuple[float, ...], ...] = (
        (0.0, 0.0, 0.0, 0.0, 0.0),
        (0.0, 0.0, 0.0, 0.0, 0.0),
        (0.0, 0.0, 0.0, 0.0, 0.0),
        (0.0, 0.0, 0.0, 0.0, 0.0),
        (0.0, 0.0, 0.0, 0.0, 0.0),
    )

    def multiply(self, mood: list[float]) -> list[float]:
        """Matrix-vector multiplication: transform mood into behavioral offset."""
        result = []
        for row in self.rows:
            result.append(sum(row[j] * mood[j] for j in range(5)))
        return result

    def scale(self, scalars: list[list[float]]) -> TransformationMatrix:
        """Return a new matrix with each cell multiplied by the corresponding scalar."""
        new_rows = []
        for i, row in enumerate(self.rows):
            new_rows.append(tuple(row[j] * scalars[i][j] for j in range(5)))
        return TransformationMatrix(rows=tuple(new_rows))


@dataclass(frozen=True)
class Stimulus:
    """Input to Behave mode describing a situation.

    appraisal: contextual shift to the character's appraisal (control, certainty).
    behavioral: named properties of the situation (variable-length, not used in Phase 1 pipeline).
    """

    appraisal: AppraisalVector = field(default_factory=AppraisalVector)
    behavioral: dict[str, float] = field(default_factory=dict)


@dataclass(frozen=True)
class PersonalityProfile:
    """Complete personality composite for one character."""

    mbti_type: str
    sign: str
    resting_mood: MoodVector
    appraisal_baseline: AppraisalVector
    transform_matrix: TransformationMatrix
    susceptibility: float
    rigidity: float
    rumination: float
    behavioral_baseline: BehavioralVector


@dataclass(frozen=True)
class BehaveResult:
    """Output from Behave mode."""

    behavioral_vector: BehavioralVector
    conflict_flag: bool
    rigidity_indicator: float
    deviation_amount: float


@dataclass(frozen=True)
class FeelResult:
    """Output from Feel mode."""

    mood_delta: MoodVector
    new_mood: MoodVector


def _clamp_bipolar(value: float) -> float:
    return max(-1.0, min(1.0, value))


def _clamp_unipolar(value: float) -> float:
    return max(0.0, min(1.0, value))
