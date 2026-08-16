# Claude Editor

A video editing studio that Claude operates end to end — cutting the timeline in
Adobe Premiere Pro over an MCP bridge, and authoring captions and motion graphics
as code that renders to transparent ProRes overlays.

The edit is **data, not conversation**: footage is analysed once into JSON, and
every subsequent decision is a small patch to a manifest rather than a rewrite.

## What it has actually done

| | Source | Cut | Removed |
|---|---|---|---|
| Intro to Claude Editor | 62.1s | 21.1s | **66%** |
| Trading GPU Hours | 78.9s | 44.7s | **43%** |
| Reddit | 86.5s | 40.0s | **54%** |

Each one silence-cut, captioned, and — for the first — given six motion-graphic
cards, without a human touching the timeline.

## How it works

```
footage.mov
    │
    ├─ preprocess.py ──► analysis/  envelope · silence · transcript · framing
    │                    (computed ONCE; never enters a conversation)
    │
manifest.json  ◄── edits happen HERE (a few lines, not a file rewrite)
    │
    ├─ build.py ──────► compositions/index.html   (generated, never hand-edited)
    ├─ review.py ─────► captions as text, for approval BEFORE rendering
    ├─ verify.py ─────► structural findings, no render needed
    │
    └─ hyperframes render ──► ProRes 4444 + alpha ──► Premiere V2/V3
                                    │
                          check_render.py ──► verified via the alpha channel, as text
```

### `framing.json` — placing graphics without looking

An 8×6 grid sampled every 0.5s. Each cell is judged bright-and-flat (wall) or
not, so *"will this cover her face?"* becomes a lookup instead of a screenshot.
Roughly 47% of a typical frame is placeable, all of it at the edges. Only that
verdict is stored — one hex bitmask per sample, ~3KB per video — so the file
never becomes something expensive to read.

### Analysis-driven graphics

The waveform card in the first video is the speaker's **real RMS envelope**, with
the **actual removed regions** struck through in red — computed from the same
data that drove the cut, not drawn to look plausible.

## The locked silence recipe

Speech and room tone form two clusters in an RMS histogram; the threshold belongs
in the valley between them, and is never assumed.

| Parameter | Value |
|---|---|
| Speech threshold | −35 dB RMS |
| Hysteresis floor | −37 dB (keeps consonant tails) |
| Lead-in / tail | 0.02s / 0.04s — cuts ~2 frames after the word |
| Min gap cut | 0.05s — slices *between* words |
| Envelope resolution | 20 ms |

Manual trims live in `overrides-*.json` with their reasoning, so a re-run
reproduces them exactly.

## Captions

Transcribed locally with whisper.cpp (`small.en`) against the **cut** audio, never
the original. Social style: one line enforced by deriving the character budget
from frame width ÷ font size, no entrance tweens (captions hard-switch like a
broadcast caption track), and a zero-blur knockout edge rather than a glow.

Whisper's errors *move* between runs, so `fixes-*.json` pins every wrong variant
seen — not merely the most recent one.

## Why the architecture looks like this

The first video was made conversationally and cost ~293M tokens, 98% of it
re-reading context. Full HTML rewrites and verification screenshots both persist
in context and are re-sent on every later turn.

| | Conversational | This |
|---|---|---|
| Move a card | rewrite 380 lines (~15K tokens) | 1 line of JSON (~500) |
| Check placement | read a screenshot (~2K) | read a text line (~50) |
| Resume a session | carry ~300K | ~6K from `NEW-VIDEO.md` |

`session-cost.py` reads Claude Code's own transcript and says when to reset.

## Docs

- **`NEW-VIDEO.md`** — start here for a new video; the whole pipeline in 61 lines
- **`CLAUDE.md`** — the editing spec: pacing, cuts, caption rules, palette
- **`WORKING-NOTES.md`** — working style, and every mistake that cost real time
- **`edit/README.md`** — the pipeline in detail

## Requirements

macOS · Premiere Pro with the MCP bridge panel · Node 20+ · ffmpeg · whisper-cpp

See `SETUP.md`. Footage and renders are git-ignored — they exceed GitHub's file
limit and regenerate from the compositions.

## Credits

Inspired by [Jason Cooperson](https://www.youtube.com/@jasoncooperson)'s tutorial
on driving Premiere Pro with Claude. Built on the Premiere Pro MCP bridge and
HyperFrames.
