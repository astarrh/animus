# Changelog

## Unreleased

### Added

- **Designer calibration (Phase 1):** `animus.designer` module with
  `ScalarBounds`, `DesignerScalars`, `compute_scalar_bounds`,
  `designer_scalars`, and opt-in `apply_designer_scalars`. Remaps raw assembly
  coefficients to library-relative `[0, 1]` for UI and threshold authoring
  without changing default pipeline output.

### Changed

- `PersonalityProfile` docstring and README clarify raw scalar clustering on
  default composites (~0.35–0.62); author band guides apply to designer
  remapped values.

## 0.2.0

### Fixed

- Packaged `personality_building_blocks.json` inside `animus.data` so
  `load_building_blocks()` / `parse_json()` with no path work after
  `pip install` (not only from a source checkout). `DEFAULT_JSON_PATH` and
  `default_building_blocks_path()` now resolve to the installed package data.

### Changed

- Default building-block coefficients were retuned for expression (behavioral
  change for all 192 composites when using packaged defaults):
  - E/I sociability baselines and related matrix paths
  - S/N aggression / curiosity (including N arousal→curiosity polarity)
  - T/F empathy baselines (corrected inverted polarity) and matrix paths
  - Astrology element contrasts (Fire / Earth / Air / Water); Water empathy
    polarity corrected
- Canonical authoring path is now
  `src/animus/data/personality_building_blocks.json`. The file under `docs/`
  remains a convenience symlink for local tooling.

## 0.1.0

- Initial public calculator API (feel / behave / decay, composites, JSON authoring).
