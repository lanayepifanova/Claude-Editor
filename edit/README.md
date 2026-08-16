# The edit pipeline

The video is **data**, not a conversation. Analysis happens once; every change
after that is a small patch to `manifest.json`.

```
footage.MOV
    │
    ├─ preprocess.py ──► analysis/   envelope · silence · transcript · framing
    │                                (computed ONCE, never enters a conversation)
    │
manifest.json  ◄── edits happen HERE (a few lines, not a file rewrite)
    │
    ├─ build.py ──────► graphics/*/index.html   (generated, never hand-edited)
    └─ verify.py ─────► text findings           (not screenshots)
                            │
                        hyperframes render ──► ProRes ──► Premiere
```

## Why

Editing by conversation cost ~293M tokens on the first video, 98% of it
re-reading context. The expensive parts were full HTML rewrites and verification
screenshots, both of which persist in context forever and get re-sent every turn.

| | Conversational | This |
|---|---|---|
| Move a card | rewrite 380 lines (~15K tokens) | 1 line of JSON (~500) |
| Check placement | read a screenshot (~2K) | read a text line (~50) |

## Use

```bash
# once per video
python3 edit/preprocess.py footage/clip.MOV --out edit/analysis

# per change: patch manifest.json, then
python3 edit/verify.py            # text findings, no render needed
python3 edit/build.py --out graphics/intro-overlays/index.html

# housekeeping
python3 edit/session-cost.py      # is this session worth continuing?
python3 edit/cleanup.py --list    # what is safe to reclaim
```

Render only once `verify.py` is clean. Most rounds never need one.

## What verify catches without rendering

- clips overlapping on a track, or running past the end of the video
- cards under 1.8s (too fast to read)
- beats firing outside their own card
- timings off the frame grid
- **cue drift** — a beat pinned to a spoken word that no longer lands on it
- cards sitting on the subject vs. on the wall (from `framing.json`)
- stretches of video with no graphic

## framing.json

An 8×6 grid sampled every 0.5s of the cut timeline. A cell is *safe* when it is
bright and flat — wall rather than subject. This is what removes the need to look
at frames to decide placement; roughly 47% of this frame is placeable, all of it
at the edges.

Only the safe/not-safe verdict is stored, as one hex bitmask per sample (bit
`gy*8+gx`) — about 3KB per video instead of 160KB of mean/variance pairs nothing
read. `verify.py` still understands the old per-cell layout, so an analysis dir
restored from git history keeps working.

## Rules

- **Never hand-edit generated HTML.** `build.py` overwrites it. Change the manifest.
- **Pin timing to speech, not the clock.** `"cue": "also add"` — verify re-checks it
  against the transcript every run, so re-cutting the video surfaces the drift.
- **The manifest is the memory.** With it plus `WORKING-NOTES.md`, a fresh session
  resumes for a few thousand tokens instead of carrying the whole history.
