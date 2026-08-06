# Animus Building Blocks Editor

Browser UI for editing `animus.building_blocks` JSON (scalars, baselines, resting moods, matrices).

## Run

From the **repo root** (so the default JSON is fetchable):

```bash
python -m http.server 8000
```

Open [http://localhost:8000/tools/building-blocks-editor/](http://localhost:8000/tools/building-blocks-editor/).

## Workflow

1. **Load default** — pulls `docs/personality_building_blocks.json`
2. Tweak MBTI poles / astrology components
3. **Save** (Chromium + File System Access) or **Download JSON**
4. In your game: `load_building_blocks("path/to/override.json")`

Opening a local file via **Open JSON…** also works without the HTTP server; Load default requires it (or any static file host).
