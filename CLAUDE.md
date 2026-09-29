# Claude Video Editor — Project Context

This folder is a self-contained editing studio. When Claude opens it, this file
tells Claude **how you edit** and **which tools to drive**. Everything Claude
needs to cut a video the way you would lives here.

> The "How I edit" section below is the source of truth for style. Update it as
> your taste sharpens — every edit gets reviewed against it before export.

---

## The engine

**HyperFrames** — writes HTML/CSS, animates it, and records the animation into an
MP4 (or a transparent ProRes overlay). Use it for every title card, lower-third,
motion graphic, callout, caption track and animated element. Compositions and
their renders live in `graphics/`.

**There is no NLE, on purpose.** Premiere Pro and its MCP bridge were removed on
2026-09-21 — she asked for the studio to have no reliance on it. The cut is
computed by `edit/preprocess.py`, graphics are rendered by HyperFrames, and
`edit/burn.py` composites and encodes the finished video into `output/` with
ffmpeg. The whole pipeline is scripts and files; nothing needs an application to
be open, and nothing needs a human to touch a timeline. Do not propose Premiere,
Final Cut, Resolve or any other timeline app as a step — if something genuinely
cannot be done headlessly, say so plainly rather than reaching for one.

## Folder layout

- `footage/`  — drop raw footage + audio here
- `graphics/` — HyperFrames compositions and their renders
- `output/`   — final exports (hers alone — never delete from it)
- `project/`  — caption sidecars (`<name>.srt`), the editable source of the wording

---

## How I edit

**The through-line:** information over atmosphere. Every edit should feel like a
sharp news segment — focused, dense, always moving forward. If a moment isn't
delivering information or holding attention, it gets cut. Nothing is on screen
just to look nice.

**Pacing & feel:** Fast and punchy. Cut on motion. No dead air. Density is the
goal — the viewer should never wait for the next thing. Momentum over polish;
a slightly rough cut that keeps moving beats a smooth one that drags.

**Silence removal (do this first, always):** This is THE signature of my edit.
The settings below are locked in — I approved this pacing on "Intro to Claude
Editor" (2026-08-15) and it is exactly what I want. Do not soften them.

*The recipe — reproduce this every time:*

| Parameter | Value | What it does |
|---|---|---|
| Speech threshold | **-35 dB** RMS | Above this = speech, keep it |
| Hysteresis floor | **-37 dB** | Extend keep-region down to here so consonant tails survive |
| Lead-in padding | **0.02s** | Breath of air before the word |
| Tail padding | **0.04s** | Cut ~2 frames after the sound stops — right after the word |
| Min gap to cut | **0.05s** | Slices *between words*, not just between sentences |
| Min segment kept | **0.08s** | Anything shorter is a blip, drop it |
| Envelope resolution | **20ms** windows | 100ms is too coarse for word-level cuts |

Run `edit/preprocess.py` — it measures the envelope, applies the recipe, and
writes `silence.json` (the cut list `burn.py` exports from) plus a
`cut_proof.mp4`. It is the *only* implementation of this recipe. Do not eyeball
this, and do not reach for an NLE's built-in silence detection — those are far
too conservative for this pacing.

*Method notes that matter:*
- Always measure the RMS envelope first and check the histogram. Speech and
  room tone form two clusters; the threshold belongs in the valley between
  them. Never assume a threshold — a wrong one deletes quiet speech.
- Verify against the picture before deleting long stretches. If the footage is
  showing something during a silence, that silence stays.
- Drop stray sub-0.15s blips at the head and tail — they're bumps, not speech.
- Jump cuts are expected and wanted. Never soften them with dissolves,
  reframes, or punch-ins.
- Render a quick local ffmpeg proof to check for clipped consonants before
  calling it done.

*Only if a word sounds bitten off:* raise tail padding to 0.07s. Change nothing
else. Never widen the gap threshold — the density is the point.

*If she says something was "cut too soon" or "cut out", that is usually not the
padding.* Speech quieter than the -35 dB trigger — a trailing word, the end of a
sentence she drops her voice on — is deleted as room tone, and a brief dip inside
one continuous phrase gets sliced by the 0.05s min-gap. Run
`python3 edit/restore_speech.py edit/analysis-<name>`: it finds those runs inside
the removed regions and writes `overrides-<name>.json`, then re-run `preprocess.py`
with `--overrides`. The recipe itself stays exactly as locked.

**Repeated takes (locked, her rule 2026-09-21):** *"If a sentence repeats twice,
that means it's a retake, so cut out all repeats of that sentence or line besides
the last one, since the last one is the usable take."* Treat this as standing
policy on every video, not something to ask about each time — **the last take is
always the keeper**, because she re-reads a line until she gets it right. The
same holds for a run of three or more: only the final attempt survives.

Run `python3 edit/retakes.py edit/analysis-<name>` *after* `preprocess.py`. It
reads the word timings off the cut timeline, groups them into lines, and flags
two shapes:

- a **near-duplicate line** — the same sentence said again (difflib ratio
  `>= --sim`, default 0.72, so a reworded retake like "an editing process you
  like" / "an editing process **that** you like" still matches)
- a **false start** — an abandoned run the next attempt restates from the top

Only lines within `--window` (default 6) of each other are compared; a phrase
that comes back a minute later is rhetoric, not a retake. It prints a report by
default — **read it before `--apply`**, because this deletes content and a false
positive silently loses a real sentence. `--apply` writes the doomed spans into
`overrides-<name>.json` as a `remove` list in **source** time, then re-run
`preprocess.py --overrides` to excise them. The silence recipe is not touched.

`remove` is source-time rather than segment indices on purpose: detection re-runs
every pass and the indices move, a source span does not, and a span landing
mid-segment splits it (which `in`/`out` cannot do). Two seams to watch, both
already handled in the tool but worth knowing when reading its output: whisper
ends every word exactly where the next begins, so the doomed line's last word
looks like it runs past the join it sits on — padding from there clips the first
word of the take replacing it; and a leftover under 0.30s at either edge is not a
word, it is the stub of the take just removed, so the span snaps out to the
segment edge and takes it along.

**Cuts:** Hard cuts by default. J/L cuts on dialogue so audio leads or trails
the picture — this is what keeps aggressive silence removal from feeling
choppy. Cut away to b-roll or a graphic over the ugliest jump cuts rather than
hiding them with an effect.

**Transitions:** Hard cut is the default and the overwhelming majority. Cross-
dissolve only between distinct scenes or clear time jumps — never within a
scene, never between two shots of the same subject. No other transition types.

**Captions:** Single line, conventional and understated — legibility first,
never decorative. Present for all spoken audio. Break lines on natural phrase
boundaries, not mid-clause. Never let a caption cover a lower-third or an
on-screen graphic — move the caption or move the graphic.

**Orientation decides length and position.** Her rule: vertical footage gets
vertical captions, horizontal gets horizontal. Check the real frame from the
*proof* — `ffprobe` on the source reports rotated display dimensions.

| | Landscape 16:9 | Vertical 9:16 |
|---|---|---|
| Position | Lower third — `--y 0.82` | Upper quarter — `--y 0.25`, clears the TikTok UI |
| Line length | ~42 chars | ~24 chars |
| Flags | `--res 1920x1080 --y 0.82 --size 48 --maxw 0.61` | tool defaults (`--y 0.25`) |

`--y` is measured from the **top** of the frame. Line length is *derived*, not
set: `captions_overlay.py` computes it from frame width, font size and `--maxw`.
The 42-char broadcast line only physically fits in landscape — in 9:16 the same
spec is ~24 chars, which is why forcing 42 there breaks cues mid-clause.

**Caption pipeline (locked, approved 2026-08-15 on "Intro to Claude Editor"):**

This produced captions I was very happy with. Reproduce it exactly.

1. Transcribe the **cut** audio, never the original — timings must land on the
   edited timeline. Extract it from the ffmpeg proof render.
2. `whisper-cli -m ~/.cache/whisper/ggml-small.en.bin -f cut.wav -oj -ml 1`
   (`-ml 1` gives word-level timings; installed via `brew install whisper-cpp`,
   model in `~/.cache/whisper/`). Runs locally, nothing uploaded. **small.en,
   not base.en** — base mangles finance/hardware jargon ("trade GPU out",
   "Cash shuttle listed on Nimus"). `preprocess.py` defaults to small.en.
3. Merge subword tokens back into whole words before grouping — whisper splits
   `don`+`'t` and `V`+`OD`.
4. Group into single lines: max 3.5s, min 0.7s, and the character budget for
   the orientation (~42 landscape / ~24 vertical — see the caption table above;
   the tool derives it, never hardcode it). Break at sentence punctuation first,
   then clauses, then length. Flush *before* appending the token that would
   overflow, not after.
5. Fix known mis-hearings. **Whisper reliably hears "Claude" as "VOD".** Always
   check proper nouns and product names against the actual audio.
6. Export `.srt` into `project/` alongside the overlay. It is the editable
   source of truth for the *wording* — fix it there and re-run rather than
   retyping anywhere else — and it is the file to hand to TikTok or YouTube if a
   platform caption track is ever wanted on top of the burned-in one.

**Captions are burned in.** `edit/captions_overlay.py` renders them as a
HyperFrames overlay: scriptable end to end, positioned with `--y`, and sized by
the orientation table above.

`edit/burn.py` then finishes the video: it cuts the original footage with
`silence.json`, composites the rendered overlay, and writes H.264/AAC into
`output/`. It never overwrites an existing export without `--force`, and it
verifies the composite by measuring how much of each frame the ink actually
changed.

```bash
python3 edit/burn.py --analysis edit/analysis-<name> \
    --overlay graphics/<name>-cap.mov --out "output/<name>.mp4" \
    --master graphics/<name>-master.mp4
```

**Caption position is scriptable.** It is the `--y` flag on
`captions_overlay.py`, measured from the top of the frame — 0.82 landscape, 0.25
vertical. This used to be the one thing I had to eyeball and nudge by hand in a
GUI; since Premiere was dropped it is just a number, so move it on request
rather than telling me where to click.

**Motion graphics style:** Editorial / print-inspired — rules, grids, a
considered typographic hierarchy, magazine-layout logic. Serif for headlines,
sans for labels and data. Graphics should read like a well-designed page, not a
motion-graphics reel.

- Palette: navy `#0F1E3D` · cream `#FAF7F2` · gold `#E8B33A` (accent only —
  gold is for emphasis, never a background or body text)
- Type: serif headlines, sans labels/captions/data. *Starting point:*
  Instrument Serif + Inter. Swap in brand fonts when there are some.
- Animation: restrained and quick. Elements cut or wipe on along the grid;
  rules draw in. Fast, tight easing. Nothing bounces, nothing floats, nothing
  slides in linearly.
- **Decorative and textural graphics are welcome** (updated 2026-08-15 — this
  reverses an earlier "no decoration" rule). Film-strip rules, shutter wipes,
  record dots, halftone, ink stamps, proofreader's marks, little character
  icons: all good. Charm is allowed to be the point. The restraint above is
  about *easing*, not about *ornament* — decorative elements still move fast
  and tight, they just don't have to justify themselves with information.

**Photo / b-roll overlays (locked, approved 2026-08-19 on "Sony TSMC"):** Her
own images laid over the cut, one per beat, each pinned to the words it lands
on. Built with `edit/prep_photos.py` + `edit/build_photos.py` — never hand-written
HTML. Name each source file for the phrase it belongs to; the stem is the
manifest key, so **two files may not share a stem** (`chip stacking.jpeg` and
`chip stacking.jpg` silently overwrote each other until one was renamed).

| | Landscape 16:9 | Vertical 9:16 |
|---|---|---|
| Legal band | 120 – 845 (above the caption) | **580 – 1620** (below the caption, above TikTok UI) |
| Centre | per beat | x 540, **y 1260** |
| Width | per beat | ~900 (max 980) |
| Hold | 1.9 – 4.3s | **1.8 – 3.2s** |

- Captions sit at the *top* in vertical, so the graphics go *below* them — the
  reverse of landscape. `build_photos.py` reads `frame` and `band` per project.
- **y 1260, not 1090.** 1090 was the first pass and put the taller plates at
  mid-face; she asked for them lower. 1260 clears her chin and still lands the
  tallest plate's bottom at 1567, inside the 1620 floor.
- **Knock out logos and line art; leave labelled diagrams on their card.** A
  knocked-out brand mark reads as ink on the footage and is the look she wants.
  But knocking a diagram whose labels are anti-aliased grey text drops them to an
  unreadable smudge over her hair — legibility wins, so those keep the white
  card. Screenshots keep their card too; knocking them strips highlight spans to
  blobs.
- **Leave a gesture alone.** Where she mimes something on camera, hold the frame
  clear rather than covering it.

**Titles / lower-thirds:** Lower-left, on the grid. Appear on the speaker's
first sentence, dwell ~3s, then leave. Name in serif, role in sans caps below a
hairline rule. One per person per video unless the segment changes.

**Music & audio:** Dialogue at ~-6 dBFS peaks. Duck music under speech by
~-12 dB — the voice always wins. Music is a bed for energy, not a feature; it
can drop out entirely during dense information. Cut to the beat on montage
sections only.

**Color:** Clean and neutral — this is news, not cinema. Correct for accurate
skin tones and a true white point first. Keep contrast crisp and blacks honest
(not crushed, not lifted). No stylized grade or film emulation unless asked.

**Hard nos:**
- No canned title templates or graphics presets from any app — every graphic is
  built in HyperFrames
- No stock transition effects (zoom blur, page peel, spin, push)
- No letterboxing or baked-in black bars
- No music competing with dialogue
- No holding on a shot with nothing happening in it

---

## Read this too

`WORKING-NOTES.md` is a living document of how Lana works — how she phrases
requests, what she reacts to, which preferences have been reversed, and the
process lessons that cost time before. **Read it at the start of a session, and
update it at the end of any session where a preference is established, reversed,
or clarified.** This file is the settled spec; that one is the context behind it.

## Operating rules for Claude

- Inspect before mutating: `ffprobe` the clip, read `silence.json`, run
  `edit/verify.py` — check the real numbers before changing anything.
- Use **the real footage** in `footage/`, at full resolution. Never cut from
  `cut_proof.mp4`; it is half-res and the softness is permanent once exported.
- Build motion graphics in HyperFrames → render to `graphics/` → composite with
  `edit/burn.py`. Every graphic is authored as HTML, never drawn by hand.
- Each video gets its **own clearly named** analysis dir, composition dir and
  export — `edit/analysis-<name>`, `graphics/<name>-*`, `output/<name>.mp4` —
  rather than overwriting the last one's.
- **Ask before destructive/irreversible actions:** deleting media, overwriting an
  export.
- **Raw footage may be deleted only at the very end**, after the final export to
  `output/` is confirmed on disk AND she has said this is the final export. Never
  on an intermediate export. Footage is not in git.
- **Reclaim disk with `edit/cleanup.py`, never with a hand-written `rm`.** It is
  dry-run by default and physically cannot reach `footage/`, `output/`,
  `project/`, or any analysis `.json`. Note the trap it exists to prevent:
  deleting the footage turns every `cut_proof.mp4` into the last copy of that
  cut, so cleanup refuses to remove a proof whose source clip is gone.

  ```bash
  python3 edit/cleanup.py --list                 # what exists, what it costs
  python3 edit/cleanup.py --done <name>          # dry run for one project
  python3 edit/cleanup.py --caches --apply       # caches, snapshots, junk
  ```
- If a tool returns `success: false`, report the exact error and run diagnostics
  before retrying.

## Session hygiene — read before starting a new video

**One video per session.** Context is re-sent every turn, so a session that has
already made a video charges its whole history again on each message. Measured on
this project: **435,000 tokens per turn versus ~6,000 to bootstrap fresh — 73x.**

Before starting a new video, run:

```bash
python3 edit/session-cost.py     # exit 2 = start fresh now
```

**This now fires on its own.** `.claude/settings.json` wires
`session-cost.py --hook` to `UserPromptSubmit`, so once average context passes
250k/turn a one-line directive to reset is injected automatically. It is silent
below that. Nobody has to remember the command — but when the line appears,
act on it rather than reading past it.

**If Lana starts a new video in an already-long session** (she has said she may),
do not just carry on — that is the expensive path she asked to avoid. Instead
launch a subagent with a clean context to do the work:

> Use the Agent tool (`general-purpose`). Give it only: the footage path, the
> resolution/fps, what she asked for, and the instruction to read `NEW-VIDEO.md`
> first. It bootstraps in a few thousand tokens, does the whole pipeline in its
> own context, and returns a short report. The renders, analysis, and images stay
> out of the main conversation entirely.

`NEW-VIDEO.md` is that bootstrap document. Keep it current.

## The edit pipeline (use this, not ad-hoc HTML)

The video lives in `edit/manifest.json`. Analysis is computed once into
`edit/analysis/`; compositions are **generated** by `edit/build.py` and must never
be hand-edited. Checks come from `edit/verify.py` as text, not screenshots.

```bash
python3 edit/preprocess.py footage/clip.MOV --out edit/analysis   # once per video
python3 edit/retakes.py edit/analysis                             # drop repeated takes
python3 edit/verify.py                                            # after every change
python3 edit/build.py --out graphics/<project>/index.html         # then render
```

Pin beats to speech with `"cue": "<words>"` rather than a bare timestamp — verify
re-checks the cue against the transcript and reports drift. See `edit/README.md`.

## Typical workflow

1. `ffprobe` the clip — resolution, fps, duration. Orientation decides the
   caption spec, and fps is detected and recorded in `silence.json`.
2. Watch/scan the footage; propose an edit plan (structure, beats, music).
3. **Silence pass** — `python3 edit/preprocess.py <clip> --out edit/analysis-<name>`.
   It writes `silence.json` (the cut list) and `cut_proof.mp4` (the cut itself).
   See the locked recipe above. Do this before any graphics work; it changes all
   downstream timings.
4. **Retake pass** — `python3 edit/retakes.py edit/analysis-<name>`, read the
   report, then `--apply` and re-run `preprocess.py --overrides`. Always, not
   only when she mentions it. Content cuts go before captions, for the same
   reason the silence pass does: they move every timing after them.
5. **Caption pass** — `captions_overlay.py` → `review.py` the wording → render.
6. Design motion graphics in HyperFrames → render to `graphics/`.
7. Composite and export — `edit/burn.py` → `output/`.
8. Review pass against the "How I edit" rules above, then commit.
