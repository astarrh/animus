# Animus 0.3 — patch notes for game teams

**Date:** 2026-08-20  
**Audience:** Gameplay / AI / tools engineers consuming Animus  
**Status:** Unreleased on `main`; shipped on the designer-calibration branch / PR

Pawns were harder to tell apart than the `[0, 1]` scalars implied. 0.3 gives you honest author-facing ranges, published behavioral outer limits, a live rigidity lever, and wider default composite spread.

This is a **behavioral change** if you load packaged defaults. Pin `0.2.x` if you need identical numbers this sprint.

---

## Breaking

1. **`behave` math changed.** Mood→behavior offset is now  
   `matrix × mood × susceptibility × (1 − rigidity)`.  
   Rigid pawns stay closer to `behavioral_baseline`. `feel` and `decay` are unchanged.

2. **Packaged building blocks are JSON version 2.** Default composites are more spread out. Same situation vectors will produce different mood/behavior numbers. Version 1 override files still parse.

3. **Do not threshold on raw `profile.susceptibility` / `.rigidity` / `.rumination`.** They are still assembly coefficients, not “0 = none, 1 = max in the game.” Use designer scalars (below) or envelopes.

If you cache character cards, volatility formulas, or dialogue thresholds keyed to old composites, recompute them.

---

## What to use instead

### Designer scalars — library-relative `[0, 1]`

```python
from animus import compute_scalar_bounds, designer_scalars, generate_all_composites
from animus.data_pipeline import assemble, load_building_blocks

composites = generate_all_composites(assemble(load_building_blocks()))
bounds = compute_scalar_bounds(composites)          # from YOUR library
ds = designer_scalars(composites[("INFP", "Pisces")], bounds)

ds.reactivity       # 0 = most stoic in this library, 1 = most reactive
ds.inflexibility    # 0 = most flexible, 1 = most rigid
ds.persistence      # 0 = snaps back fastest, 1 = lingers longest
ds.flexibility      # alias: 1 - inflexibility
```

Recompute `bounds` whenever you load a custom JSON. Do not hardcode packaged min/max.

Volatility example that actually spans `[0, 1]` across the 192 grid:

```python
R = 0.6 * ds.reactivity + 0.4 * ds.flexibility
```

`apply_designer_scalars(profile, bounds)` can push remapped values into the pipeline. **Off by default.** Most games should keep raw coefficients in `feel`/`behave`/`decay` and use designer scalars only for UI and thresholds.

### Character cards — outer limits without playtesting

```python
from animus import character_card

card = character_card(profile, bounds)
agg = card["envelope"]["aggression_passivity"]  # min, max, at_resting
```

Each card runs **feel → behave** on a shipped ladder:

| Name | Meaning | Intensity |
|------|---------|-----------|
| `resting` | No event | 0.0 |
| `mild_irritation` | Everyday friction | 0.5 |
| `moderate_conflict` | Clear interpersonal stress | 0.5 |
| `severe_crisis` | Breaking-point probe | 1.0 |

Export all 192 packaged defaults:

```bash
python -m animus.tools.export_character_cards --output cards.json
```

Threshold on envelope max (“can this pawn snap under standard crisis?”), not on guessed raw scalars.

---

## Pipeline (0.3)

```text
feel:   mood_delta = situation × susceptibility
behave: offset     = matrix × mood × susceptibility × (1 − rigidity)
decay:  still rumination only
```

- **Susceptibility** still scales both feel and behave (reactive types move more *and* show more).
- **Rigidity** is behave-only. `BehaveResult.rigidity_indicator` is the raw value; **`flexibility_factor`** is `1 − clamp(rigidity, 0, 1)`.
- `conflict_flag` is still always `False`. `Stimulus.behavioral` is still unused.

---

## Packaged default ranges (JSON v2)

| Scalar | v1 (0.2) | v2 (0.3) |
|--------|----------|----------|
| susceptibility | 0.36–0.61 | **0.25–0.74** |
| rigidity | 0.33–0.62 | **0.22–0.76** |
| rumination | 0.36–0.61 | **0.27–0.73** |

Still not a full `[0, 1]` on raw fields — that is why `designer_scalars` exists.

Rank-order held: ISTJ/INTJ-Capricorn stoic; ENFP-Pisces reactive; ISTJ-Taurus rigid; ENFP-Gemini flexible.

---

## Migration checklist

- [ ] Upgrade Animus; expect different numbers on packaged defaults.
- [ ] Replace raw scalar thresholds (`susceptibility > 0.55`, etc.) with `designer_scalars` or envelope max.
- [ ] Call `compute_scalar_bounds` at load time from the composites you actually spawn.
- [ ] Re-export / recache character cards.
- [ ] Re-tune dialogue / animation thresholds against the new envelopes (especially `severe_crisis`).
- [ ] If you fork `personality_building_blocks.json`, you can stay on version 1 or adopt v2 values; parser accepts both.
- [ ] Need bit-identical 0.2 behavior: pin `animus==0.2.x`.

---

## API added

| Symbol | Module | Role |
|--------|--------|------|
| `compute_scalar_bounds` | `animus.designer` | Empirical min/max for a profile set |
| `designer_scalars` | `animus.designer` | Library-relative `[0, 1]` readings |
| `apply_designer_scalars` | `animus.designer` | Opt-in remapped profile for the pipeline |
| `compute_envelope` / `character_card` | `animus.envelope` | Behavioral min/max under reference stress |
| `REFERENCE_SITUATIONS` | `animus.envelope` | Shipped severity ladder |
| `BehaveResult.flexibility_factor` | `animus.models` | `1 − rigidity` used in behave |

Full design notes: `docs/designer_calibration_revision.md`.
