# Designer calibration revision — implementation plan

**Status:** Draft for review  
**Target release:** 0.3.0  
**Authors:** Animus team  
**Last updated:** 2026-08-20

---

## 1. Problem statement

Animus exposes `PersonalityProfile.susceptibility` and `PersonalityProfile.rigidity` as `[0, 1]` floats. Game designers and downstream consumers reasonably treat them as full-range author dials. In practice, all 192 MBTI×sign composites produced by `generate_all_composites()` occupy only the middle third of that range:

| Scalar | Observed composite range | Nominal range | Usable span |
|--------|--------------------------|---------------|-------------|
| `susceptibility` | 0.362 – 0.614 | [0, 1] | ~25% |
| `rigidity` | 0.332 – 0.619 | [0, 1] | ~29% |
| `rumination` | 0.361 – 0.614 | [0, 1] | ~25% |

This creates two related failures:

1. **Scalar illegibility.** Profiles look interchangeable when read side-by-side (`0.48` vs `0.52`). Volatility formulas that assume `[0, 1]` inputs (e.g. `R = 0.6·s + 0.4·(1−r)`) compress further and lose discriminative power.

2. **Unpredictable outer limits.** Under reference stress, composites *do* diverge in `behave` output (aggression spread ~1.0+ on moderate situations; 89/192 hit ±1 clamp at max severity). Authors cannot know a pawn's behavioral ceiling without playtesting each composite because Animus publishes no envelope or calibration layer.

Additionally:

- `rigidity` is returned on `BehaveResult` but **does not affect** `feel`, `behave`, or `decay`.
- `susceptibility` scales both `feel` (mood delta) and `behave` (mood→behavior offset), so reactivity is nonlinear; outer limits depend on the full loop.
- `_normalize_coeff` clamping is not the cause — it never fires on current data.

**User-visible symptom:** Pawns feel more generic than designers expect; behaviors are harder to parse and threshold without guess-and-test.

---

## 2. Goals

| ID | Goal |
|----|------|
| G1 | Give designers **predictable `[0, 1]` semantics** for personality scalars without breaking regression tests or raw assembly values. |
| G2 | Publish **reference behavioral envelopes** so authors know outer limits per profile without playtesting every composite. |
| G3 | **Separate internal assembly coefficients from author-facing readings** in docs and API. |
| G4 | Increase **differentiation** where it matters (scalar spread, rigidity as a live lever) via data retune and pipeline wiring. |
| G5 | Ship changes in **versioned, opt-in phases** so existing games can migrate deliberately. |

## 3. Non-goals

- Changing the core feel → behave → decay pipeline structure.
- Owning pawn entities, dialogue, or action selection (remains game-side).
- Resolving two-pawn social dynamics or `conflict_flag` (separate work).
- Consuming `Stimulus.behavioral` tags (separate work).
- Replacing the 192-composite grid with a different personality model.

---

## 4. Design principles

1. **Raw stays raw.** Assembly output (`PersonalityProfile` fields as today) remains stable for regression and building-block math. Designer views are a layer on top.

2. **Calibration is library-relative unless overridden.** Designer `[0, 1]` means "most vs least within this building-block library," not an absolute psychological claim. Games that fork JSON get bounds recomputed from their file.

3. **Envelopes over guesswork.** Threshold authoring should reference documented min/max behavioral output under standard reference situations, not discovered limits.

4. **Full loop for envelopes.** Reference scenarios run `feel` → `behave` (not `behave` alone) because susceptibility affects both stages.

5. **Backward compatibility by default.** Phase 1–2 are additive APIs. Phase 3 (JSON retune) bumps `version` and is documented as a behavioral change for packaged defaults.

---

## 5. Architecture overview

```text
┌─────────────────────────────────────────────────────────────────┐
│  personality_building_blocks.json (authoring)                 │
└────────────────────────────┬────────────────────────────────────┘
                             │ assemble() + generate_all_composites()
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│  PersonalityProfile (raw assembly coefficients)                 │
│  susceptibility, rigidity, rumination ∈ narrow band (~0.35–0.62)│
└────────────┬───────────────────────────────┬────────────────────┘
             │                               │
             ▼                               ▼
┌────────────────────────────┐   ┌────────────────────────────────┐
│  designer.py (NEW)         │   │  feel / behave / decay (existing)│
│  · ScalarBounds            │   │  · rigidity wired in (Phase 4)   │
│  · DesignerScalars         │   └────────────────────────────────┘
│  · remap helpers           │
└────────────┬───────────────┘
             │
             ▼
┌────────────────────────────┐
│  envelope.py (NEW)         │
│  · ReferenceSituation      │
│  · compute_envelope()      │
│  · export_character_card() │
└────────────────────────────┘
             │
             ▼
┌────────────────────────────┐
│  Game designer / UI /      │
│  threshold authoring       │
└────────────────────────────┘
```

---

## 6. Phase 1 — Scalar bounds and designer calibration (0.3.0-alpha)

**Objective:** Expose honest `[0, 1]` readings without changing pipeline math or default JSON.

### 6.1 New module: `animus/designer.py`

#### `ScalarBounds`

Frozen dataclass holding empirical min/max for each calibratable scalar across a composite library:

```python
@dataclass(frozen=True)
class ScalarBounds:
    susceptibility: tuple[float, float]   # (min, max)
    rigidity: tuple[float, float]
    rumination: tuple[float, float]

    def remap(self, value: float, field: str) -> float:
        """Linear map from observed [min, max] → [0, 1]. Clamp at ends."""
```

#### `compute_scalar_bounds(composites) -> ScalarBounds`

- Input: `dict[tuple[str, str], PersonalityProfile]` or iterable of profiles.
- Output: min/max per scalar across all provided profiles.
- Default use: pass output of `generate_all_composites(library)`.

**Packaged defaults (current JSON, verified 2026-08-20):**

| Scalar | min | max |
|--------|-----|-----|
| susceptibility | 0.362 | 0.614 |
| rigidity | 0.332 | 0.619 |
| rumination | 0.361 | 0.614 |

These are **derived**, not hardcoded — hardcoded values may appear only in tests as regression anchors with tolerance.

#### `DesignerScalars`

Author-facing readings, all in `[0, 1]`:

```python
@dataclass(frozen=True)
class DesignerScalars:
    reactivity: float       # remapped susceptibility; 0 = thickest-skinned in library
    inflexibility: float    # remapped rigidity; 0 = most flexible in library
    persistence: float      # remapped rumination; 0 = snaps back fastest
```

Naming note: use `inflexibility` (not `flexibility = 1 - rigidity`) so higher values consistently mean "more of the trait" across all three fields. Document aliases for consumers who prefer `flexibility`.

#### `designer_scalars(profile, bounds) -> DesignerScalars`

Pure function; no mutation of `profile`.

#### Optional: `apply_designer_scalars(profile, bounds) -> PersonalityProfile`

Returns a **new** profile with raw coefficients replaced by remapped values. Intended for games that want calibrated values inside the pipeline (opt-in). Document that this changes feel/behave output and is not the default.

### 6.2 Public exports

Add to `animus/__init__.py`:

```python
from animus.designer import (
    ScalarBounds,
    DesignerScalars,
    compute_scalar_bounds,
    designer_scalars,
)
```

### 6.3 Documentation updates (`README.md`)

Add section **"Raw vs designer scalars"**:

| Layer | Source | Range (defaults) | Use for |
|-------|--------|------------------|---------|
| Raw | `profile.susceptibility` etc. | ~0.35–0.62 | Regression, building-block debugging |
| Designer | `designer_scalars(profile, bounds)` | [0, 1] library-relative | UI labels, sorting, volatility formulas |
| Envelope | Phase 2 | behavioral axis min/max | Action thresholds |

Update the susceptibility band table to clarify it applies to **designer remapped** values, not raw composites.

Add `models.py` field comments (or docstring on `PersonalityProfile`) noting raw assembly range.

### 6.4 Tests (`tests/test_designer.py`)

- `compute_scalar_bounds` on all 192 composites matches known ranges ±ε.
- Remap: min composite → 0.0, max composite → 1.0 (per field).
- Remap is monotonic across composites.
- `apply_designer_scalars` changes feel/behave output vs raw (smoke test).
- Empty/single-profile edge cases handled.

### 6.5 Acceptance criteria

- [x] Designer can call `designer_scalars()` and get `[0, 1]` with documented meaning.
- [x] README explicitly states raw composite range and tells authors not to threshold on raw values.
- [x] No change to default feel/behave/decay output for existing callers.
- [x] All existing tests pass unchanged.

---

## 7. Phase 2 — Reference envelopes (0.3.0-beta)

**Objective:** Answer "where is the outer limit for this pawn?" without playtesting.

### 7.1 New module: `animus/envelope.py`

#### `ReferenceSituation`

```python
@dataclass(frozen=True)
class ReferenceSituation:
    name: str
    situation: MoodVector           # input to feel()
    appraisal: AppraisalVector        # input to behave() stimulus
    intensity: float                  # behave() intensity
    description: str                  # author-facing label
```

#### Shipped reference ladder

| Name | Purpose | situation (dc, fc, ib, sp, arousal) | appraisal (control, certainty) | intensity |
|------|---------|--------------------------------------|----------------------------------|-----------|
| `resting` | Baseline at equilibrium | (0, 0, 0, 0, 0) | (0, 0) | 0.0 |
| `mild_irritation` | Everyday friction | (−0.25, 0.10, −0.20, 0.15, 0.35) | (0.25, −0.20) | 0.5 |
| `moderate_conflict` | Clear interpersonal stress | (−0.50, −0.30, −0.40, −0.20, 0.60) | (−0.30, −0.30) | 0.5 |
| `severe_crisis` | Breaking-point probe | (−0.80, −0.70, −0.60, −0.50, 0.90) | (−0.50, −0.60) | 1.0 |

These mirror the scenarios validated in analysis (2026-08-20). Store as `REFERENCE_SITUATIONS: tuple[ReferenceSituation, ...]` in `envelope.py`.

#### `BehavioralEnvelope`

Per-axis min/max across a set of situations for one profile:

```python
@dataclass(frozen=True)
class AxisEnvelope:
    min: float
    max: float
    at_resting: float                 # value under `resting` reference

@dataclass(frozen=True)
class BehavioralEnvelope:
    aggression_passivity: AxisEnvelope
    impulsiveness_deliberation: AxisEnvelope
    sociability_withdrawal: AxisEnvelope
    empathy_self_interest: AxisEnvelope
    curiosity_avoidance: AxisEnvelope
    deviation_amount: AxisEnvelope    # metadata; useful for "how far from baseline"
```

#### `compute_envelope(profile, situations=REFERENCE_SITUATIONS) -> BehavioralEnvelope`

For each situation:

1. `felt = feel(situation.situation, profile, current_mood=profile.resting_mood)`
2. `out = behave(profile, Stimulus(appraisal=situation.appraisal), situation.intensity, mood=felt.new_mood)`
3. Record each behavioral axis and `deviation_amount`.

Aggregate min/max per axis across all situations.

#### `character_card(profile, bounds, situations=REFERENCE_SITUATIONS) -> dict`

Human- and machine-readable summary for designer tools:

```python
{
    "mbti_type": "INTJ",
    "sign": "Capricorn",
    "designer_scalars": {"reactivity": 0.08, "inflexibility": 0.72, ...},
    "envelope": {
        "aggression_passivity": {"min": -0.17, "max": 0.55, "at_resting": 0.02},
        ...
    },
    "reference_situations": ["resting", "mild_irritation", ...],
}
```

#### Batch helper

```python
def compute_all_envelopes(
    composites: dict[tuple[str, str], PersonalityProfile],
    situations: tuple[ReferenceSituation, ...] = REFERENCE_SITUATIONS,
) -> dict[tuple[str, str], BehavioralEnvelope]:
    ...
```

Enables precomputing a 192-row lookup table at game load or in CI.

### 7.2 CLI / tooling (optional in 0.3.0, recommended)

```bash
python -m animus.tools.export_character_cards --output cards.json
```

Writes all 192 character cards for the packaged default library. Useful for browser editor integration and design docs.

### 7.3 Browser editor integration (follow-up)

Extend `tools/building-blocks-editor/` with a "Character card" panel:

- Select MBTI×sign → show designer scalars + envelope bars.
- Visualize where ±1 clamp is reachable under `severe_crisis`.

Not blocking 0.3.0 API ship.

### 7.4 Tests (`tests/test_envelope.py`)

- Envelope min ≤ at_resting ≤ max per axis (where applicable).
- `severe_crisis` produces wider spread than `mild_irritation` for majority of composites.
- INTJ-Capricorn envelope matches snapshot (tolerance-based) for regression.
- All envelope values within [−1, 1] for behavioral axes.

### 7.5 Acceptance criteria

- [x] Author can read `character_card(composites[("ESTP", "Aries")])` and know aggression range under standard stress.
- [x] Reference situations documented in README with plain-language labels.
- [x] Envelope computation uses feel → behave full loop.

---

## 8. Phase 3 — Building-block data retune (0.3.0)

**Objective:** Widen raw composite spread so assembly coefficients use more of `[0, 1]` natively, reducing reliance on remap for differentiation.

### 8.1 Authoring changes (`personality_building_blocks.json`)

Bump `"version": 2` (see §10 migration).

**Pole scalar targets (MBTI axes):**

| Pole | Current susceptibility | Proposed | Current rigidity | Proposed |
|------|------------------------|----------|------------------|----------|
| T | 0.25 | **0.10** | 0.55 | 0.60 |
| F | 0.75 | **0.90** | 0.40 | 0.35 |
| J | 0.40 | **0.55** | 0.65 | **0.80** |
| P | 0.55 | **0.35** | 0.30 | **0.15** |
| E, I, S, N | 0.40–0.55 | Widen ±0.10 toward poles | 0.40–0.55 | Widen ±0.10 |

Exact values to be tuned in a spreadsheet pass; goal is:

- Raw composite susceptibility range ≥ **0.20 – 0.80** (target; validate after retune).
- Raw composite rigidity range ≥ **0.15 – 0.85** (target).

**Sign components:**

- Elements/modalities: widen toward 0.15 / 0.85 where semantically appropriate (Earth → lower susceptibility, Water → higher, etc.).
- Sign tweaks: keep ±0.10 max (design unchanged — tweaks are deltas, not full scales).

**Do not change** `_MBTI_COEFF_DIVISOR = 4.0` or `_SIGN_COEFF_DIVISOR = 2.0` in this phase. Divisors are correct for the semantic model (see §12.1).

### 8.2 Validation gate

Before merging retune:

1. Run full test suite.
2. Regenerate scalar bounds; confirm target spread met.
3. Regenerate all 192 character cards; design review for archetype plausibility (INTJ-Cap still stoic, ENFP-Pisces still reactive).
4. Compare behave output rank-order: retune should **reorder** extremes, not invert archetypes (ISTJ-Cap among least reactive, etc.).
5. Update snapshot tolerances in `test_composites.py` and scenario tests.

### 8.3 Acceptance criteria

- [ ] Raw susceptibility spread ≥ 0.45 (max − min) on packaged defaults.
- [ ] Raw rigidity spread ≥ 0.50.
- [ ] Designer remap still works (now less aggressive correction).
- [ ] CHANGELOG documents behavioral change for games using packaged JSON.

---

## 9. Phase 4 — Wire rigidity into pipeline (0.3.0 or 0.3.1)

**Objective:** Make `rigidity` a live lever, not metadata.

### 9.1 Proposed behavior

**In `behave` only (initial wiring):**

Scale mood-driven behavioral offset by flexibility:

```python
flexibility = 1.0 - personality.rigidity
behavioral_offset = [v * personality.susceptibility * flexibility for v in raw_offset]
```

Effect:

- High rigidity → mood pushes behavior less (stuck in patterns).
- Low rigidity → mood pushes behavior more (adaptable outward expression).

**Not in `feel` initially.** Rigidity as "emotional stiffness" vs "behavioral inflexibility" should be validated with design review. Alternative: apply to both feel and behave with a smaller feel coefficient.

**`rigidity_indicator` on `BehaveResult`:** Keep as raw rigidity; add optional `flexibility_factor` to result if useful.

### 9.2 Susceptibility double-scaling review

Phase 4 should include a design decision document on whether susceptibility should remain in **both** feel and behave:

| Option | Pros | Cons |
|--------|------|------|
| Keep both (status quo) | Reactive types move more AND express more | Nonlinear; harder to explain |
| Feel only | Cleaner "reactivity" semantics | Behave less differentiated by susceptibility |
| Behave only | Mood moves same; expression varies | Less "thick-skinned" feel in mood |

**Recommendation:** Keep both for 0.3.0; document in README. Revisit if envelope tooling makes nonlinear effects confusing.

### 9.3 Tests

- High-rigidity profile produces smaller deviation from baseline than low-rigidity at same mood (same susceptibility).
- Rigidity = 0 → offset scaled only by susceptibility (backward-compatible corner).
- Envelope tests updated for rigidity effect.

### 9.4 Acceptance criteria

- [ ] `rigidity` documented as active in behave pipeline.
- [ ] README "not yet used" note removed.
- [ ] Regression tests for INTJ-Cap, ESTP-Aries updated with tolerances.

---

## 10. Versioning and migration

### 10.1 JSON format version

| Version | Change |
|---------|--------|
| `1` | Current packaged defaults |
| `2` | Widened pole/component scalars (Phase 3) |

`json_parser.py` accepts both; warn on v1 after 0.4.0.

### 10.2 Game migration guide (for CHANGELOG / README)

**If you use packaged defaults and upgrade to 0.3.0:**

1. Expect different mood/behave outputs for the same situation vectors.
2. Replace raw scalar thresholds with `designer_scalars()` or envelope-based thresholds.
3. Recompute any cached character cards or volatility formulas.

**If you fork `personality_building_blocks.json`:**

1. Call `compute_scalar_bounds(generate_all_composites(assemble(load_building_blocks("yours.json"))))` at load time.
2. Do not assume packaged default bounds.

**If you need zero behavior change:**

- Pin `animus==0.2.x` and/or pin your JSON copy at version 1.

### 10.3 API stability

| API | Stability |
|-----|-----------|
| `feel`, `behave`, `decay` signatures | Stable |
| Raw `PersonalityProfile` fields | Stable (values change with JSON v2) |
| `designer.py`, `envelope.py` | New in 0.3.0; minor additions allowed in 0.3.x |
| `REFERENCE_SITUATIONS` | Additive only (new situations appended) |

---

## 11. Implementation schedule

| Phase | Deliverable | Depends on | Breaking |
|-------|-------------|------------|----------|
| **1** | `designer.py`, README, tests | — | No |
| **2** | `envelope.py`, character cards, tests | Phase 1 | No |
| **3** | JSON v2 retune, CHANGELOG | Phases 1–2 for validation | Yes (default outputs) |
| **4** | Rigidity in behave, docs | Phase 2 envelopes for verification | Yes (behave outputs) |

**Recommended merge order:** 1 → 2 → 4 → 3 (wire rigidity before JSON retune so retune validates against final pipeline). Alternative: 1 → 2 → 3 → 4 if rigidity wiring needs more design time (document as 0.3.1).

---

## 12. Open questions

### 12.1 Sign divisor (`_SIGN_COEFF_DIVISOR = 2.0`)

**Resolved:** Intentional. Sign scalar = (element + modality + tweak) / 2, where element and modality are full `[0, 1]` contributions and tweak is a small delta. Dividing by 3 would compress further. No change planned.

### 12.2 Designer remap: linear vs percentile

**Default:** Linear min-max remap (simple, invertible).

**Future:** Optional percentile rank across 192 composites for UI ("90th percentile reactive"). Not in 0.3.0 scope.

### 12.3 Global vs per-game bounds

**Default:** Bounds computed from the library the game loads.

**Future:** Allow games to pass custom bounds (e.g. only the 12 signs used in this title).

### 12.4 `apply_designer_scalars` default

**Recommendation:** Off by default. Most games should use designer scalars for UI/thresholds only; pipeline uses raw unless explicitly opted in.

### 12.5 Rigidity in feel

Defer until Phase 4 design review completes. Envelope tooling will show whether behavioral-only wiring is sufficient.

---

## 13. Success metrics

After 0.3.0 ships, we should be able to demonstrate:

| Metric | Before (0.2.0) | Target (0.3.0) |
|--------|----------------|----------------|
| Raw susceptibility spread | 0.25 | ≥ 0.45 (after Phase 3) |
| Designer reactivity spread | N/A | 1.0 by construction |
| Author can answer "max aggression under standard crisis" | Playtest only | `character_card()` |
| README documents raw vs designer | No | Yes |
| Rigidity affects behave | No | Yes (Phase 4) |

Qualitative: external consumers (e.g. SleepersGame) report reduced guess-and-test for threshold authoring.

---

## 14. File checklist

| File | Action |
|------|--------|
| `src/animus/designer.py` | **Create** (Phase 1) |
| `src/animus/envelope.py` | **Create** (Phase 2) |
| `src/animus/__init__.py` | Export new APIs |
| `src/animus/models.py` | Docstrings on scalar fields |
| `src/animus/behave.py` | Rigidity wiring (Phase 4) |
| `src/animus/data/personality_building_blocks.json` | Version 2 retune (Phase 3) |
| `src/animus/data_pipeline/json_parser.py` | Accept version 2 |
| `tests/test_designer.py` | **Create** |
| `tests/test_envelope.py` | **Create** |
| `README.md` | Raw vs designer, envelopes, migration |
| `CHANGELOG.md` | 0.3.0 entries per phase |
| `docs/designer_calibration_revision.md` | This document |
| `tools/building-blocks-editor/` | Character card panel (follow-up) |

---

## 15. Appendix A — Empirical reference (packaged JSON v1, 2026-08-20)

### Composite scalar ranges

```
susceptibility: [0.362, 0.614]  mean=0.482  stdev=0.057
rigidity:       [0.332, 0.619]  mean=0.475  stdev=0.069
rumination:     [0.361, 0.614]  mean=0.468  stdev=0.058
```

### Behavioral spread under shared situations (all 192 composites)

| Situation | Aggression spread | Sociability spread | Deviation spread |
|-----------|-------------------|--------------------|------------------|
| Mild irritation | 0.94 | 1.31 | 0.09 |
| Moderate conflict | 1.00 | 1.38 | 0.09 |
| Severe crisis (intensity 1.0) | 1.26 | 2.00 | 0.19 |

89/192 composites hit ±1 behavioral clamp on at least one axis under severe crisis + max intensity.

### Example extremes

| Composite | susceptibility | rigidity |
|-----------|----------------|----------|
| ISTJ-Capricorn (lowest susc) | 0.362 | 0.556 |
| ENFP-Pisces (highest susc) | 0.614 | 0.361 |
| ENFP-Gemini (lowest rigid) | 0.507 | 0.332 |
| ISTJ-Taurus (highest rigid) | 0.388 | 0.619 |

### Consumer remap example (SleepersGame-style)

```python
bounds = compute_scalar_bounds(composites)
ds = designer_scalars(profile, bounds)

# Volatility index on calibrated [0, 1] inputs
R = 0.6 * ds.reactivity + 0.4 * (1.0 - ds.inflexibility)

# Or threshold from envelope
card = character_card(profile, bounds)
if card["envelope"]["aggression_passivity"]["max"] > 0.7:
    tag = "can snap under standard crisis"
```

---

## 16. Appendix B — Root cause summary (for issue tracker)

1. **Conservative pole authoring** — MBTI poles in ~[0.25, 0.75]; sign tweaks ±0.10.
2. **Pole averaging** — MBTI type = mean of 4 poles (/4); primary algorithmic narrowing.
3. **Composite blend** — MBTI×sign weighted average; minor additional narrowing (spread 0.253 vs MBTI-only 0.213 for susceptibility).
4. **Clamp** — Not active on current data.
5. **Documentation gap** — `[0, 1]` types imply full range; no designer calibration layer documented.

---

*End of plan.*
