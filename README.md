# Claude Editor

A self-contained video editing studio that Claude drives end to end — cutting the
timeline in Adobe Premiere Pro over an MCP bridge, and building motion graphics as
HTML compositions rendered to transparent ProRes overlays.

This repo is the studio itself: the editing spec, the tooling, and the graphics
source. The footage and the multi-hundred-megabyte renders stay local.

## What it does

The first video cut with it went from **62.1s to 21.1s — 66% of the runtime removed** —
then had captions and six motion-graphic cards added, without a human touching the
timeline.

| Stage | How |
|---|---|
| Silence removal | RMS envelope analysis → frame-accurate cut list → Premiere |
| Captions | Local Whisper transcription of the *cut* audio → SRT → caption track |
| Motion graphics | HyperFrames HTML compositions → ProRes 4444 with alpha → V2/V3 |

## Layout

```
CLAUDE.md              the editing spec — pacing, cuts, captions, palette
tools/silence-cut.py   RMS analysis → clip list for add_to_timeline_batch
tools/captions.py      Whisper word timings → broadcast-style SRT
graphics/              HyperFrames projects (compositions/, .media/, config)
footage/  output/      local only, git-ignored
```

## The silence recipe

The heart of it. Speech and room tone form two clusters in an RMS histogram; the
threshold belongs in the valley between them, never assumed:

| Parameter | Value |
|---|---|
| Speech threshold | -35 dB RMS |
| Hysteresis floor | -37 dB (keeps consonant tails) |
| Lead-in / tail | 0.02s / 0.04s — cuts ~2 frames after the word |
| Min gap cut | 0.05s — slices *between* words |
| Envelope resolution | 20ms |

```bash
python3 tools/silence-cut.py footage/clip.MOV --item-id <id> --proof
```

## Captions

Transcribe the **cut** audio, never the original, or the timings land on the wrong
timeline:

```bash
ffmpeg -i PROOF.mp4 -map 0:a:0 -ac 1 -ar 16000 -c:a pcm_s16le cut.wav
whisper-cli -m ~/.cache/whisper/ggml-base.en.bin -f cut.wav -oj -ml 1 -of words
python3 tools/captions.py words.json -o "project/My Sequence.srt"
```

## Graphics

```bash
cd graphics/intro-overlays
npx hyperframes check .                        # lint, layout, motion, contrast
npx hyperframes render . --format mov -q high  # ProRes 4444 with alpha
```

Overlays are black ink with a flat cream knockout edge — no glow — so type stays
legible over footage. Render with a raised `FFMPEG_ENCODE_TIMEOUT_MS`; 4K60 ProRes
4444 will otherwise starve the encoder and fail while still exiting 0.

## Requirements

macOS · Premiere Pro with the MCP bridge panel · Node 20+ · ffmpeg · whisper-cpp

See `SETUP.md`.

## Credits

Inspired by [Jason Cooperson](https://www.youtube.com/@jasoncooperson)'s tutorial on
driving Premiere Pro with Claude. Built on the Premiere Pro MCP bridge and HyperFrames.
