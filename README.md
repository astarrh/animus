# Animus

A lightweight, game-agnostic **personality calculator** for NPCs.

Animus does not own pawns, dialogue, or action selection. It turns numerical
situation inputs into personality-colored **mood** and **behavioral tendency**
outputs. Your game keeps state, maps events to vectors, and decides narrative
outcomes.

Two different games can feed Animus the same situation and interpret the same
output vector in completely different ways.

```text
Game event  →  (author maps to numbers)  →  feel / behave / decay  →  numbers  →  (game maps to actions)
```

## Install

```bash
pip install -e ".[dev]"   # from repo root; openpyxl required
```

Requires Python 3.11+.

```python
from animus import feel, behave, decay
from animus import MoodVector, AppraisalVector, Stimulus
from animus.data_pipeline import load_building_blocks, assemble
from animus.composite import generate_all_composites
```

## Core idea

Each character is a `PersonalityProfile` (typically one of 192 MBTI × zodiac
composites). You call three operations:

| Call | Role |
|------|------|
| `feel(situation, personality, current_mood?)` | Situation → mood change |
| `behave(personality, stimulus, intensity, mood?)` | Mood + situation appraisal → outward tendencies (`intensity` = output gain) |
| `decay(personality, current_mood, elapsed)` | Mood drifts back toward resting baseline |

**Mood** is internal. **Behave** is how that internal state shows up outwardly
for *this* personality. Irritation vs hurt vs shutdown is not a separate mood
label — it emerges from personality + appraisal + mood through `behave`.

## Spaces (what the numbers mean)

### Mood (internal) — bipolar −1…+1, except arousal 0…1

| Axis | Negative pole | Positive pole |
|------|---------------|---------------|
| `distress_contentment` | upset / strained | at ease |
| `fear_confidence` | afraid / unsure | confident |
| `isolation_belonging` | alienated | connected |
| `shame_pride` | ashamed / diminished | proud / affirmed |
| `arousal` | (low) calm | (high) activated |

Rough magnitudes for authors: **±0.2** mild, **±0.5** clear, **±0.8** intense.

There is no dedicated “anger” axis. Annoyance is usually mild negative distress
plus some arousal; whether that becomes arguing or withdrawing is decided in
`behave`, not in mood naming.

### Appraisal (situational cognition) — bipolar −1…+1

Passed on the `Stimulus` into `behave` (added to the personality’s appraisal baseline):

| Axis | Negative | Positive |
|------|----------|----------|
| `control` | helpless / can’t steer this | agentic / I can direct this |
| `certainty` | unsettled / unpredictable | known / procedure is clear |

### Behavioral (outward tendencies) — bipolar −1…+1

Output of `behave`. **Not actions** — leanings your game thresholds into lines,
animations, or choices.

| Axis | Negative pole | Positive pole |
|------|---------------|---------------|
| `aggression_passivity` | passive / yielding | assertive / pushy |
| `impulsiveness_deliberation` | deliberate | impulsive |
| `sociability_withdrawal` | withdrawn | socially engaging |
| `empathy_self_interest` | self-focused | other-oriented |
| `curiosity_avoidance` | avoidant | investigative |

Example thresholds (illustrative only — pick your own):

- `aggression_passivity > 0.5` → character escalates / snaps  
- `sociability_withdrawal < -0.3` and low aggression → goes quiet  
- `impulsiveness_deliberation < 0` → plans before speaking  

## PersonalityProfile

A `PersonalityProfile` is the full static description of one character’s
personality. Animus does not store pawns; your game holds a profile (and a
separate current `MoodVector`) on each pawn and passes them into `feel` /
`behave` / `decay`.

Profiles are usually one of **192 composites** (16 MBTI × 12 signs) built from
the packaged default building-blocks JSON
(`animus/data/personality_building_blocks.json`).
You can also construct a `PersonalityProfile` by hand for characters outside
that grid.

```python
library = assemble(load_building_blocks())  # packaged defaults
composites = generate_all_composites(library)

profile = composites[("INTJ", "Capricorn")]
profile.susceptibility   # read any field directly
profile.resting_mood
```

Games override defaults by pointing at their own file:

```python
library = assemble(load_building_blocks("content/my_building_blocks.json"))
```

Optional `global_bias` on `generate_all_composites` / `blend_composite` shifts
blend weight toward MBTI (`+`) or astrology (`-`).

### Fields exposed

Every composite exposes these attributes:

| Field | Type | Range | Role |
|-------|------|-------|------|
| `mbti_type` | `str` | e.g. `"INTJ"` | Label of the MBTI half of the blend |
| `sign` | `str` | e.g. `"Capricorn"` | Label of the astrological half |
| `resting_mood` | `MoodVector` | mood axes | Default / equilibrium mood; used when `feel`/`behave` omit current mood, and as the attractor for `decay` |
| `appraisal_baseline` | `AppraisalVector` | −1…+1 | Habitual sense of control & certainty; added to every stimulus appraisal in `behave` |
| `behavioral_baseline` | `BehavioralVector` | −1…+1 | Habitual outward lean before mood/situation offsets |
| `transform_matrix` | `TransformationMatrix` | 5×5 | How mood dimensions push behavioral dimensions for this personality |
| `susceptibility` | `float` | 0…1 nominal | Raw assembly coefficient; **default composites cluster ~0.36–0.61** — use `designer_scalars` for full-range author readings |
| `rumination` | `float` | 0…1 nominal | Raw assembly coefficient; same clustering — use `designer_scalars` for calibrated view |
| `rigidity` | `float` | 0…1 nominal | Raw assembly; echoed on `BehaveResult`; **not yet used inside the pipeline math** |

Note: **`assertiveness` is not on `PersonalityProfile`**. It exists on MBTI /
sign *building blocks* and is consumed only when blending them into a
composite. After blend, read the fields above.

### Raw vs designer scalars

Assembly coefficients on `PersonalityProfile` are in nominal `[0, 1]` but **all
192 default composites occupy only the middle third** (e.g. susceptibility
~0.36–0.61). Do not threshold on raw values for UI, volatility formulas, or
“high/low reactive” labels — use the designer calibration layer:

| Layer | Source | Range (packaged defaults) | Use for |
|-------|--------|----------------------------|---------|
| **Raw** | `profile.susceptibility`, `.rigidity`, `.rumination` | ~0.35–0.62 | Regression, building-block debugging, pipeline input |
| **Designer** | `designer_scalars(profile, bounds)` | `[0, 1]` library-relative | UI labels, sorting, volatility formulas |
| **Envelope** | Phase 2 (`character_card`) | behavioral axis min/max | Action thresholds under reference stress |

```python
from animus import compute_scalar_bounds, designer_scalars, generate_all_composites
from animus.data_pipeline import assemble, load_building_blocks

library = assemble(load_building_blocks())
composites = generate_all_composites(library)
bounds = compute_scalar_bounds(composites)

profile = composites[("INFP", "Pisces")]
ds = designer_scalars(profile, bounds)
# ds.reactivity      — 0 = most stoic in library, 1 = most reactive
# ds.inflexibility   — 0 = most flexible, 1 = most rigid
# ds.persistence     — 0 = snaps back fastest, 1 = lingers longest
# ds.flexibility     — alias for 1 - ds.inflexibility

# Example volatility index on calibrated inputs
R = 0.6 * ds.reactivity + 0.4 * ds.flexibility
```

Recompute `bounds` when you load a custom building-blocks JSON — bounds are
**library-relative**, not universal constants.

**Opt-in pipeline remap:** `apply_designer_scalars(profile, bounds)` returns a
new profile with remapped coefficients inside `feel` / `behave` / `decay`.
Default is off; most games keep raw coefficients in the pipeline and use
designer scalars only for display and thresholds.

### How to interpret the scalars

#### Raw `susceptibility` (assembly coefficient)

The main dial for “how much does this pawn move?” in the pipeline:

- In **`feel`**: `mood_delta = situation_vector × susceptibility` (per axis).
- In **`behave`**: scales the mood→behavior offset the same way.

Raw values on default composites are clustered; compare using
`designer_scalars(...).reactivity` instead of raw thresholds like `< 0.4`.

#### Designer `reactivity` (calibrated susceptibility)

After remap, band guide for author reads:

| Band | Reading |
|------|---------|
| ~0.0–0.25 | Most stoic composites in your library |
| ~0.25–0.75 | Mid spread |
| ~0.75–1.0 | Most reactive composites in your library |

This is **reactivity**, not a named trait like “cynical.” Distrusting a
compliment’s *meaning* is still a game-side choice of input vector; low
reactivity only means the vector you *do* send moves them less (relative to
other composites in the same library).

#### Raw `rumination` / designer `persistence` (0 = snaps back, 1 = stews)

Controls `decay` only:

```text
decayed = resting + (current - resting) × e^(-elapsed / rumination)
```

High rumination → mood lingers across turns/scenes. Low → quick return to
`resting_mood`. Use it when deciding how long a compliment, insult, or spat
should still color the pawn.

High persistence (or raw rumination) → mood lingers across turns/scenes. Low →
quick return to `resting_mood`. Use `designer_scalars(...).persistence` when
ranking composites for how long a compliment, insult, or spat should still
color the pawn.

#### Raw `rigidity` / designer `inflexibility` (0 = flexible, 1 = rigid)

Available on the profile and echoed as `BehaveResult.rigidity_indicator`.
**Animus does not currently change `feel`/`behave`/`decay` from this value.**
Use `designer_scalars(...).inflexibility` (or `.flexibility`) for author reads.
Authors may still use it in their own runtime (e.g. resist changing plans,
harder to talk down) until the engine wires it in (planned 0.3).

### How to interpret the baselines

#### `resting_mood`

Where the character settles when nothing is happening. A slightly negative
`isolation_belonging` resting mood is a loner baseline; higher resting
`arousal` is someone who runs “on” even at rest. Initialize pawn mood from
this, and expect `decay` to pull back toward it.

#### `appraisal_baseline`

Default cognitive stance before the situation’s stimulus is added:

- Higher `control` → tends to feel agentic; `behave` amplifies more active pathways  
- Higher `certainty` → world feels predictable; leans deliberation over impulse  

Even with `Stimulus()` (zeros), `behave` still uses this baseline — so
neutral situations remain personality-colored.

#### `behavioral_baseline`

The character’s default outward lean (assertive vs passive, social vs
withdrawn, etc.) before mood offsets. Two pawns in the same mood can still
differ because baselines differ. Read it as “who they are when the math
hasn’t pushed them yet.”

#### `transform_matrix`

Advanced. Rows = behavioral axes, columns = mood axes; each cell is how
strongly a mood dimension drives a behavioral dimension for *this*
personality. This is why the same distressed mood can become aggression in
one composite and withdrawal in another. Most authors never edit it directly;
they pick a composite (or accept the JSON-authored blend).

### Identity labels

`mbti_type` and `sign` are informational labels for the composite. They do not
change runtime math by themselves — the numeric fields do. Useful for debug
UI, save data, and designer tools (“this pawn is ESTP-Aries”).

### Loading and attaching to a pawn

```python
from animus import compute_scalar_bounds, designer_scalars, generate_all_composites
from animus.data_pipeline import assemble, load_building_blocks

composites = generate_all_composites(assemble(load_building_blocks()))
bounds = compute_scalar_bounds(composites)

pawn = {
    "personality": composites[("ESFP", "Leo")],
    "mood": None,  # set below
}
pawn["mood"] = pawn["personality"].resting_mood

# Designer-facing reads — calibrated to [0, 1] within your library
p = pawn["personality"]
ds = designer_scalars(p, bounds)
print(p.mbti_type, p.sign)
print("reactivity", ds.reactivity, "(raw susceptibility", p.susceptibility, ")")
print("persistence", ds.persistence)
print("flexibility", ds.flexibility)
print("resting belonging", p.resting_mood.isolation_belonging)
print("baseline sociability", p.behavioral_baseline.sociability_withdrawal)
print("habitual control", p.appraisal_baseline.control)
```

Typical pattern: **profile is immutable/static**; **mood is mutable runtime
state** your game updates from `feel` / `decay`.

## Feel

Maps a **situation mood delta** (authored by you) through personality
susceptibility onto current mood.

```python
# "Petty disagreement while staking a tent"
situation = MoodVector(
    distress_contentment=-0.25,  # mild annoyance
    fear_confidence=0.10,        # not scared — slightly sure of self
    isolation_belonging=-0.20,   # friction with partner
    shame_pride=0.15,            # competence / "I'm right" nudge
    arousal=0.35,                # a bit heated
)

result = feel(situation, estp)           # uses resting mood if none provided
# result.mood_delta  — susceptibility-scaled change applied
# result.new_mood    — store this on your pawn
```

The engine does **not** parse keywords like `"argument"`. You own the catalog of
situation → `MoodVector` mappings.

## Behave

Turns personality + mood + situational appraisal into a behavioral tendency
vector.

```python
stimulus = Stimulus(
    appraisal=AppraisalVector(
        control=0.25,     # "I should direct how this is done"
        certainty=-0.20,  # procedure is contested
    ),
    # behavioral={...} is accepted but not used by the pipeline yet
)

out = behave(estp, stimulus, intensity=0.5, mood=result.new_mood)
bv = out.behavioral_vector
# bv.aggression_passivity, .impulsiveness_deliberation, ...
```

Pipeline (simplified):

1. `appraisal = personality.baseline + stimulus.appraisal`
2. Scale the mood→behavior matrix by appraisal (control/certainty pathways)
3. `offset = matrix × mood × susceptibility`
4. `personality_output = behavioral_baseline + offset`
5. Apply **intensity as gain**: `gain = 1 + intensity × (MAX_INTENSITY_GAIN - 1)`  
   (`MAX_INTENSITY_GAIN` is 4.0 today → intensity `0` keeps the authored signal; `1` amplifies up to 4×)
6. Clamp to [−1, 1]

`intensity` is **not** a randomness / personality-override dial. Output is
deterministic for the same inputs (`rng` is accepted but unused).

| Intensity | Effect |
|-----------|--------|
| `0.0` | Unamplified personality signal (previous “centered” magnitudes) |
| `0.5` | Mid gain (2.5× with default max) |
| `1.0` | Maximum expressiveness (4×, then clamp) |

`BehaveResult` also includes `conflict_flag` (always `False` for now),
`rigidity_indicator`, and `deviation_amount` from baseline.

### Same situation, different personalities

With the tent-stake inputs above at `intensity=0.5`, composites diverge, e.g.:

| Personality | aggression | impulsiveness | sociability | Plausible game read |
|-------------|------------|---------------|-------------|---------------------|
| ESTP-Aries | higher | nearer zero / + | engages | pushes the point |
| ESFJ-Leo | moderate + | more deliberate | engages | firm but social |
| INFP-Pisces | near zero | mild | slight − | soft, pulls back |
| INTJ-Capricorn | near zero | deliberate | withdrawn | quiet, does it their way |

Your game chooses the concrete line or animation; Animus only supplies the lean.

## Decay

Mood returns toward resting baseline. `elapsed` is abstract (seconds, turns,
story beats — your choice).

```python
pawn.mood = decay(estp, pawn.mood, elapsed=1.0)
```

Higher `rumination` → mood lingers longer.

## Full single-pawn loop

```python
# --- once at load ---
composites = generate_all_composites(assemble(load_building_blocks()))
pawn_personality = composites[("ISTJ", "Virgo")]
pawn_mood = pawn_personality.resting_mood

# --- on game event: disagreement over stake order ---
situation = MoodVector(-0.25, 0.10, -0.20, 0.15, 0.35)
felt = feel(situation, pawn_personality, current_mood=pawn_mood)
pawn_mood = felt.new_mood

stimulus = Stimulus(appraisal=AppraisalVector(control=0.25, certainty=-0.20))
tendencies = behave(
    pawn_personality,
    stimulus,
    intensity=0.5,  # mid gain; use 0.0 for unamplified, 1.0 for max
    mood=pawn_mood,
)

# --- your runtime ---
if tendencies.behavioral_vector.aggression_passivity > 0.35:
    play("insist_on_stake_order")
elif tendencies.behavioral_vector.sociability_withdrawal < -0.10:
    play("go_quiet_and_reposition_stakes")
else:
    play("negotiate")

# --- later ---
pawn_mood = decay(pawn_personality, pawn_mood, elapsed=1.0)
```

## Two pawns: passing values back and forth

Animus calculates **one character at a time**. A disagreement between two pawns
is a game-orchestrated loop: each side’s behavioral output is mapped by *you*
into the other side’s next Feel / Stimulus inputs.

```text
A.mood ──feel──► A.mood'
A.mood' + stimulus_A ──behave──► A.behavior
        │
        ▼  game: A.behavior → mood delta + appraisal for B
B.mood ──feel──► B.mood'
B.mood' + stimulus_B ──behave──► B.behavior
        │
        ▼  game: B.behavior → mood delta + appraisal for A
… optional decay on either pawn between beats …
```

Example bridge (illustrative — tune freely):

```python
def partner_impact(behavior) -> tuple[MoodVector, AppraisalVector]:
    """Map one pawn's outward lean into the other's next inputs."""
    mood_delta = MoodVector(
        distress_contentment=-0.15 * max(0.0, behavior.aggression_passivity),
        fear_confidence=-0.10 * max(0.0, behavior.aggression_passivity),
        isolation_belonging=-0.20 * max(0.0, -behavior.empathy_self_interest),
        shame_pride=-0.10 * max(0.0, behavior.aggression_passivity),
        arousal=0.20 * abs(behavior.aggression_passivity),
    )
    appraisal = AppraisalVector(
        control=-0.15 * behavior.aggression_passivity,   # pushed → feel less in charge
        certainty=-0.10 * abs(behavior.impulsiveness_deliberation),
    )
    return mood_delta, appraisal


def exchange(actor, partner, stimulus, intensity=0.5):
    """One beat: actor acts upon partner."""
    felt = feel(
        MoodVector(0, 0, 0, 0, 0),  # no new world event this beat
        actor["personality"],
        current_mood=actor["mood"],
    )
    # (In a real beat you may feel a world event on the actor first.)
    out = behave(actor["personality"], stimulus, intensity, mood=actor["mood"])
    delta, appraisal_shift = partner_impact(out.behavioral_vector)
    partner["mood"] = feel(delta, partner["personality"], partner["mood"]).new_mood
    return out, Stimulus(appraisal=appraisal_shift)


# Setup
A = {"personality": composites[("ESTP", "Aries")], "mood": None}
B = {"personality": composites[("INFP", "Pisces")], "mood": None}
A["mood"] = A["personality"].resting_mood
B["mood"] = B["personality"].resting_mood

# Opening spat hits both (shared situation, different susceptibilities)
opening = MoodVector(-0.25, 0.10, -0.20, 0.15, 0.35)
A["mood"] = feel(opening, A["personality"], A["mood"]).new_mood
B["mood"] = feel(opening, B["personality"], B["mood"]).new_mood

base = Stimulus(appraisal=AppraisalVector(control=0.25, certainty=-0.20))
a_out, b_stimulus = exchange(A, B, base)
b_out, a_stimulus = exchange(B, A, b_stimulus)

# Store a_out / b_out tendencies for dialogue selection; decay between scenes
A["mood"] = decay(A["personality"], A["mood"], elapsed=1.0)
B["mood"] = decay(B["personality"], B["mood"], elapsed=1.0)
```

What Animus guarantees in this loop: personality-consistent mood updates and
behavioral leans. What it does **not** do: resolve who “wins,” escalate
automatically, or define the partner-impact mapping — that stays in your
runtime so genre and tone remain yours.

## What you own vs what Animus owns

| You (game) | Animus |
|------------|--------|
| Pawn entities and saved mood | Profile math and composites |
| Event → mood / appraisal catalogs | `feel` / `behave` / `decay` |
| Behavioral vector → actions / lines | Axis ranges and clamping |
| Two-pawn bridging and conflict resolution | Per-call, single-character calculation |
| Narrative tone | Numerical calculator only |

## Authoring building blocks (JSON)

Personality coefficients live in versioned JSON packaged with Animus:

```text
src/animus/data/personality_building_blocks.json   # shipped default (format: animus.building_blocks)
```

`load_building_blocks()` with no path loads that file from the installed
package (works after `pip install`, not only from a git checkout).

Structure is **per component** (MBTI pole, element, modality, or sign tweak),
each with `scalars`, `behavioral_baseline`, `resting_mood`, and a 5×5 `matrix`.
The engine still sums poles into types / signs the same way as before.

### Browser editor

A local editor for tweaking those values:

```bash
# from repo root
python -m http.server 5178
# open http://localhost:5178/tools/building-blocks-editor/
```

- **Load default** — fetches the shipped JSON over HTTP  
- **Open JSON…** — pick any override file  
- **Save** — writes back via the File System Access API when the browser allows it  
- **Download JSON** — always available; drop the file into your game content folder  

The Excel (`.xlsx`) pipeline is **deprecated**. `load_building_blocks()` still
accepts `.xlsx` for old files, but new authoring and defaults live only in JSON.

### Game override pattern

1. Copy the packaged defaults into your project (from the repo path above, or
   from `importlib.resources` / your site-packages `animus/data/` folder)  
2. Edit in the browser tool (or any JSON editor)  
3. Load with `load_building_blocks("path/to/your.json")`  

Animus does not merge overrides with defaults — your file replaces the whole
building-block set.

## Authoring tips

1. **Keep situation vectors small** for mundane events (±0.1–0.3). Save large
   deltas for crises.
2. **Put “what kind of moment is this?” into appraisal** (`control` /
   `certainty`), not into inventing new mood axes.
3. **Put “how do they show it?” into reading `behave` output**, not into mood
   labels like anger vs hurt.
4. **Reuse a reference catalog** in your game (hunger, insult, compliment,
   task conflict) so designers aren’t inventing floats ad hoc every time.
5. **Use `intensity` as gain**, not drama-randomness: `0` for subtle leans,
   higher when the beat should read bigger on the same personality signal.

## Project layout

```text
src/animus/
  models.py           # vectors, Stimulus, PersonalityProfile, results
  feel.py / behave.py / decay.py
  composite.py        # blend MBTI × sign → profiles
  building_blocks.py
  data/               # packaged default building-blocks JSON
  data_pipeline/      # JSON building blocks (+ deprecated Excel loader)
  personalities.py    # Phase-1 hand profiles (tests / reference)
tools/building-blocks-editor/           # browser JSON editor
tests/
```

## Status notes

- Feel → Behave → Decay pipelines are implemented and covered by tests.
- Building blocks are authored in JSON; the Excel pipeline is deprecated.
- **Designer calibration (0.3):** `compute_scalar_bounds`, `designer_scalars`, and
  optional `apply_designer_scalars` remap raw assembly coefficients to
  library-relative `[0, 1]` for author tools. See
  `docs/designer_calibration_revision.md` for the full roadmap.
- `Stimulus.behavioral` tags are stored but **not** consumed yet.
- `conflict_flag` / external social pressure is **not** implemented (`False`).
- `rigidity` is returned on behave results but does not yet alter the pipeline.

## License

See repository metadata / license file if present.
