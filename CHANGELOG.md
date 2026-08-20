# Changelog

## Unreleased

### Added

- **Designer calibration (Phase 1):** `animus.designer` module with
  `ScalarBounds`, `DesignerScalars`, `compute_scalar_bounds`,
  `designer_scalars`, and opt-in `apply_designer_scalars`. Remaps raw assembly
  coefficients to library-relative `[0, 1]` for UI and threshold authoring
  without changing default pipeline output.
- **Reference envelopes (Phase 2):** `animus.envelope` module with
  `REFERENCE_SITUATIONS`, `compute_envelope`, `compute_all_envelopes`,
  `character_card`, and `python -m animus.tools.export_character_cards`.
  Authors can read per-profile behavioral min/max under a shipped severity
  ladder (resting → mild irritation → moderate conflict → severe crisis).
- **`BehaveResult.flexibility_factor`:** `1 − clamp(rigidity, 0, 1)`, reported
  alongside `rigidity_indicator`.

### Changed

- **Packaged building blocks JSON version 2 (Phase 3):** widened MBTI pole
  and astrology element/modality scalars so default composites use more of
  `[0, 1]`. Observed packaged ranges (approx.): susceptibility 0.25–0.74,
  rigidity 0.22–0.76. **This changes `feel` / `behave` / `decay` output** for
  games using packaged defaults. Sign tweaks are unchanged (±0.10). Parser
  still accepts version 1 override files.
- **`behave` pipeline (Phase 4):** mood→behavior offset is now
  `matrix × mood × susceptibility × (1 − rigidity)`. High-rigidity profiles
  stay closer to `behavioral_baseline`. `feel` / `decay` are unchanged. This
  changes `behave` output for existing callers using packaged composites.
- `PersonalityProfile` docstring and README distinguish raw assembly ranges
  from designer-remapped `[0, 1]` readings.

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
