"""Animus — A personality engine for autonomous NPC decision-making."""

from animus.models import (
    AppraisalVector,
    BehaveResult,
    BehavioralVector,
    MoodVector,
    PersonalityProfile,
    Stimulus,
    TransformationMatrix,
)
from animus.behave import behave
from animus.building_blocks import (
    AstrologicalSign,
    BuildingBlockLibrary,
    MBTIType,
)
from animus.composite import (
    blend_composite,
    compute_blend_weight,
    generate_all_composites,
)

__all__ = [
    # Core types
    "AppraisalVector",
    "BehaveResult",
    "BehavioralVector",
    "MoodVector",
    "PersonalityProfile",
    "Stimulus",
    "TransformationMatrix",
    # Behave pipeline
    "behave",
    # Building blocks (Phase 2)
    "AstrologicalSign",
    "BuildingBlockLibrary",
    "MBTIType",
    # Composite generation (Phase 2)
    "blend_composite",
    "compute_blend_weight",
    "generate_all_composites",
]
