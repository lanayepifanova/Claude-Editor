# Claude Video Editor — Project Context

This folder is a self-contained editing studio. When Claude opens it, this file
tells Claude **how you edit** and **which tools to drive**. Everything Claude
needs to cut a video the way you would lives here.

> The "How I edit" section below is the source of truth for style. Update it as
> your taste sharpens — every edit gets reviewed against it before export.

---

## The two engines

**Premiere Pro MCP** — the bridge that lets Claude actually drive Premiere:
importing footage, cutting the timeline, adding transitions, effects, exports.
Always begin a session with `verify_premiere_connection` (read-only) to confirm
the bridge is live before touching the project.

**HyperFrames** — writes HTML/CSS, animates it, and records the animation into an
MP4 (or transparent overlay). Use it for every title card, lower-third, motion
graphic, callout, and animated element. Rendered graphics land in `graphics/`,
then get imported into Premiere as clips.

## Folder layout

- `footage/`  — drop raw footage + audio here (Claude imports from here)
- `graphics/` — HyperFrames renders motion graphics here
- `output/`   — final exports
- `project/`  — the `.prproj` Premiere project file(s)

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

Run `tools/silence-cut.py` — it does the analysis and emits the exact clip list
for `add_to_timeline_batch`. Do not eyeball this or use Premiere's built-in
silence detection; both are far too conservative for this pacing.

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

**Cuts:** Hard cuts by default. J/L cuts on dialogue so audio leads or trails
the picture — this is what keeps aggressive silence removal from feeling
choppy. Cut away to b-roll or a graphic over the ugliest jump cuts rather than
hiding them with an effect.

**Transitions:** Hard cut is the default and the overwhelming majority. Cross-
dissolve only between distinct scenes or clear time jumps — never within a
scene, never between two shots of the same subject. No other transition types.

**Captions:** Single line, broadcast-style, at the lower third. Conventional
and understated — legibility first, never decorative. Present for all spoken
audio. Break lines on natural phrase boundaries, not mid-clause. Never let a
caption cover a lower-third or an on-screen graphic — move the caption or move
the graphic.

**Caption pipeline (locked, approved 2026-08-15 on "Intro to Claude Editor"):**

This produced captions I was very happy with. Reproduce it exactly.

1. Transcribe the **cut** audio, never the original — timings must land on the
   edited timeline. Extract it from the ffmpeg proof render.
2. `whisper-cli -m ~/.cache/whisper/ggml-base.en.bin -f cut.wav -oj -ml 1`
   (`-ml 1` gives word-level timings; installed via `brew install whisper-cpp`,
   model in `~/.cache/whisper/`). Runs locally, nothing uploaded.
3. Merge subword tokens back into whole words before grouping — whisper splits
   `don`+`'t` and `V`+`OD`.
4. Group into single lines: **max 42 chars**, max 3.5s, min 0.7s. Break at
   sentence punctuation first, then clauses, then length. Flush *before*
   appending the token that would overflow, not after.
5. Fix known mis-hearings. **Whisper reliably hears "Claude" as "VOD".** Always
   check proper nouns and product names against the actual audio.
6. Export `.srt` into `project/`, `import_media`, then `create_caption_track`.

Premiere has no caption-read API, so the `.srt` in `project/` is the source of
truth — edit it there and re-import rather than retyping in Premiere.

**Caption position:** Premiere exposes no caption API in its scripting DOM (the
sequence only surfaces `videoTracks`/`audioTracks`), so caption placement cannot
be scripted. Premiere's default landed fine on the 2026-08-15 pass. If it ever
needs moving: select all captions in the Text panel → Essential Graphics →
Align and Transform → Position Y (~150–200px is a visible nudge on 4K). Mention
after a caption pass that position is the one thing I have to eyeball.

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
- No default Premiere title templates or Essential Graphics presets — every
  graphic is built in HyperFrames
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

- Run `verify_premiere_connection` first. If it fails, stop and diagnose — don't
  guess-edit against a dead bridge.
- Inspect before mutating: `get_project_info`, `list_sequences`,
  `get_active_sequence` before making changes.
- Use **real imported media** — import files from `footage/` with `import_media`,
  then place the returned item IDs on the timeline.
- Keep the bridge temp dir consistent: `/tmp/premiere-mcp-bridge`.
- Build motion graphics in HyperFrames → render to `graphics/` → import into
  Premiere as a clip. Don't fake graphics with Premiere's built-in titles.
- Prefer creating a **new, clearly named sequence** for a fresh assembly rather
  than clobbering my active timeline.
- **Ask before destructive/irreversible actions:** deleting media, overwriting an
  export, closing/saving over a project.
- If a tool returns `success: false`, report the exact error and run diagnostics
  before retrying.

## The edit pipeline (use this, not ad-hoc HTML)

The video lives in `edit/manifest.json`. Analysis is computed once into
`edit/analysis/`; compositions are **generated** by `edit/build.py` and must never
be hand-edited. Checks come from `edit/verify.py` as text, not screenshots.

```bash
python3 edit/preprocess.py footage/clip.MOV --out edit/analysis   # once per video
python3 edit/verify.py                                            # after every change
python3 edit/build.py --out graphics/<project>/index.html         # then render
```

Pin beats to speech with `"cue": "<words>"` rather than a bare timestamp — verify
re-checks the cue against the transcript and reports drift. See `edit/README.md`.

## Typical workflow

1. `verify_premiere_connection` → confirm live.
2. Import everything from `footage/`.
3. Watch/scan the footage; propose an edit plan (structure, beats, music).
4. Build the rough cut on a new sequence.
5. **Silence pass** — `detect_silence`, ripple-delete every gap. Do this before
   any graphics work; it changes all downstream timings.
6. **Caption pass** — transcribe, then build the caption track.
7. Design motion graphics in HyperFrames → render → import → place.
8. Add transitions, color, audio ducking.
9. Review pass against the "How I edit" rules above.
10. Export to `output/`.

**If the bridge is dead:** CEP scans extensions and reads `PlayerDebugMode` only
at Premiere launch. If the MCP Bridge panel is missing from Window → Extensions
or won't respond, restart Premiere — that resolves it in nearly every case.
