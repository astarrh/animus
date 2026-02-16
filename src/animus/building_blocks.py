"""Building block data structures for personality composition.

Each MBTI type and astrological sign is represented as a building block
containing all the data needed to contribute to a composite personality profile.
"""

from __future__ import annotations

from dataclasses import dataclass

from animus.models import (
    AppraisalVector,
    BehavioralVector,
    MoodVector,
    TransformationMatrix,
)


@dataclass(frozen=True)
class MBTIType:
    """Building block for one of 16 MBTI types.

    Contains base values that get blended with an astrological sign
    via the layer dominance model to produce a composite personality.
    """

    name: str
    transform_matrix: TransformationMatrix
    appraisal_baseline: AppraisalVector
    susceptibility: float
    rigidity: float
    rumination: float
    assertiveness: float
    behavioral_baseline: BehavioralVector
    resting_mood: MoodVector


@dataclass(frozen=True)
class AstrologicalSign:
    """Building block for one of 12 astrological signs.

    Contains modifier values that get blended with an MBTI type
    via the layer dominance model to produce a composite personality.
    """

    name: str
    transform_matrix: TransformationMatrix
    appraisal_baseline: AppraisalVector
    susceptibility: float
    rigidity: float
    rumination: float
    assertiveness: float
    behavioral_baseline: BehavioralVector
    resting_mood: MoodVector


@dataclass(frozen=True)
class BuildingBlockLibrary:
    """Container for all 28 building blocks (16 MBTI types + 12 signs)."""

    mbti_types: dict[str, MBTIType]
    signs: dict[str, AstrologicalSign]

    def get_mbti(self, name: str) -> MBTIType:
        return self.mbti_types[name]

    def get_sign(self, name: str) -> AstrologicalSign:
        return self.signs[name]
