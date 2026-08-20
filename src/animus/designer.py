"""Designer-facing calibration for personality scalars.

Raw assembly coefficients on ``PersonalityProfile`` occupy a narrow band across
the 192 default composites (roughly 0.35–0.62). This module remaps those values
to library-relative ``[0, 1]`` readings for UI labels, sorting, and threshold
authoring without changing default pipeline output unless callers opt in via
``apply_designer_scalars``.
"""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from dataclasses import dataclass

from animus.models import PersonalityProfile

CALIBRATABLE_FIELDS = ("susceptibility", "rigidity", "rumination")


@dataclass(frozen=True)
class ScalarBounds:
    """Empirical min/max for calibratable scalars across a profile library."""

    susceptibility: tuple[float, float]
    rigidity: tuple[float, float]
    rumination: tuple[float, float]

    def remap(self, value: float, field: str) -> float:
        """Linear map from observed ``[min, max]`` to ``[0, 1]``. Clamps at ends."""
        if field not in CALIBRATABLE_FIELDS:
            raise ValueError(
                f"Unknown field {field!r}; expected one of {CALIBRATABLE_FIELDS}"
            )
        lo, hi = getattr(self, field)
        if hi <= lo:
            return 0.5
        return max(0.0, min(1.0, (value - lo) / (hi - lo)))


@dataclass(frozen=True)
class DesignerScalars:
    """Author-facing scalar readings, each in ``[0, 1]`` (library-relative)."""

    reactivity: float
    inflexibility: float
    persistence: float

    @property
    def flexibility(self) -> float:
        """``1 - inflexibility`` for consumers who prefer a flexibility label."""
        return 1.0 - self.inflexibility


def compute_scalar_bounds(
    composites: Mapping[tuple[str, str], PersonalityProfile] | Iterable[PersonalityProfile],
) -> ScalarBounds:
    """Compute min/max for susceptibility, rigidity, and rumination.

    Pass the output of ``generate_all_composites(library)`` or any iterable of
    profiles (e.g. only the composites used in your game).
    """
    profiles = _profiles_from_input(composites)
    return ScalarBounds(
        susceptibility=_min_max(p.susceptibility for p in profiles),
        rigidity=_min_max(p.rigidity for p in profiles),
        rumination=_min_max(p.rumination for p in profiles),
    )


def designer_scalars(profile: PersonalityProfile, bounds: ScalarBounds) -> DesignerScalars:
    """Map raw assembly coefficients to library-relative designer readings."""
    return DesignerScalars(
        reactivity=bounds.remap(profile.susceptibility, "susceptibility"),
        inflexibility=bounds.remap(profile.rigidity, "rigidity"),
        persistence=bounds.remap(profile.rumination, "rumination"),
    )


def apply_designer_scalars(
    profile: PersonalityProfile,
    bounds: ScalarBounds,
) -> PersonalityProfile:
    """Return a copy of ``profile`` with remapped scalar coefficients.

    Opt-in only: remapped values feed ``feel`` / ``behave`` / ``decay`` and
    change pipeline output. Most games should use ``designer_scalars`` for
    display and thresholds while keeping raw coefficients in the pipeline.
    """
    ds = designer_scalars(profile, bounds)
    return PersonalityProfile(
        mbti_type=profile.mbti_type,
        sign=profile.sign,
        resting_mood=profile.resting_mood,
        appraisal_baseline=profile.appraisal_baseline,
        transform_matrix=profile.transform_matrix,
        behavioral_baseline=profile.behavioral_baseline,
        susceptibility=ds.reactivity,
        rigidity=ds.inflexibility,
        rumination=ds.persistence,
    )


def _profiles_from_input(
    composites: Mapping[tuple[str, str], PersonalityProfile] | Iterable[PersonalityProfile],
) -> list[PersonalityProfile]:
    if isinstance(composites, Mapping):
        profiles = list(composites.values())
    else:
        profiles = list(composites)
    if not profiles:
        raise ValueError("cannot compute bounds from an empty profile collection")
    return profiles


def _min_max(values: Iterable[float]) -> tuple[float, float]:
    vals = list(values)
    return min(vals), max(vals)
