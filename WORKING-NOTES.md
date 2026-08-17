# Working notes — how Lana works, and what she wants

A living document. **Update it at the end of any session where a preference is
established, reversed, or clarified.** `CLAUDE.md` is the *spec* (the settled
rules); this is the *context* behind it — how she asks, what she reacts to, and
what I've learned the hard way.

Last updated: 2026-08-15 · after "Intro to Claude Editor" (62.1s → 21.1s)

---

## 1. How she prompts

**She reacts to what she sees, not to what I describe.** Descriptions of a change
land flat; a rendered frame gets an immediate, decisive answer. Show a composite
over the real footage before asking whether something works — never ask her to
imagine it.

**Rapid, additive iteration.** Changes arrive in quick succession, often several
while I'm still working on the last one. She does not batch. Expect to be
interrupted mid-render, and expect the request in flight to become stale.

**Strong affirmation = lock it in.** "PERFECT", "this is SO good", "keep this" are
not pleasantries — they mean *stop tuning this and write it down*. When she said
the aggressive silence pass was perfect, that became the locked recipe in
`CLAUDE.md`. Treat that language as a signal to persist the setting.

**Mostly subtractive.** The majority of her direction is "get rid of X" — the
sprocket rule, "An experiment", "What's next", the 66% stat, the glow, the boxes.
When in doubt, propose the version with less in it.

**She will reverse her own rules once she sees them applied.** `CLAUDE.md`
originally banned decorative graphics; once there were real graphics on screen she
explicitly removed that rule. Don't treat a written preference as permanent — when
a rule starts fighting what she's asking for, surface it rather than silently
obeying it.

**Timing is specified against her own speech**, not the clock: "have 02 pop up when
I say *also add*". Always map a request back to the transcript and use the actual
cue time (that one is 5.84s).

**Position is relative and iterative**: "move it up a bit", "towards the middle",
then "more up". Expect two or three passes to land. Make the first move
deliberately large enough to see.

**She wants the deliverable verified, not the source.** Repeatedly — and rightly —
she pushed back with "it isn't updated". See §4.

---

## 2. Taste

### Settled
- **Big, centred, full-frame.** Corner-pinned cards were rejected. Graphics span
  the video and may sit over her face.
- **Black ink, heavy.** True `#000`, bold weights. Navy read as not-black.
- **Flat and matte.** No glow, no shine, no haze. Legibility over footage comes
  from a **zero-blur cream knockout edge**, not a soft halo.
- **No boxes.** No panels, cards, or fills behind type. Ink sits directly on the
  footage.
- **Slow.** Every single pacing note has been "slower" or "hold longer". Nothing
  under ~2.5s. Her instinct for cuts is fast; her instinct for *graphics* is slow.
  These are not in conflict — the cut is dense, the graphics breathe.
- **Decoration is welcome** (reversed 2026-08-15). Film-strip rules, record dots,
  proof marks, little icons. Charm may be its own justification.
- **Real data over decorative fakes.** The waveform is her actual RMS envelope with
  the actual removed regions. She responded much better to that than to generic
  motion. Prefer graphics computed from the real edit.
- **Official brand marks only**, never traced. Claude mark in orange `#D97757`.

### Reversed / superseded — don't re-suggest
| Was | Now |
|---|---|
| Didot serif | **Georgia Bold** — Didot's hairlines vanish over video |
| Navy `#0F1E3D` ink | **Black `#000`** |
| Cream halo glow | **Hard cream edge, 0 blur** |
| Navy panels behind text | **No panels** |
| "No decorative graphics" | **Decoration welcome** |
| Corner-pinned cards | **Full-frame, centred** |

### Unresolved
- **"A random blue target thing that keeps popping up"** — never identified. A
  pixel scan found no blue in the overlays; the only blue is the Premiere Pro icon
  and Jason's avatar backdrop. She dropped it. If it reappears, ask her to point at
  a timecode.
- **Caption position** — she asked to shift captions up, then said the default was
  fine. Not scriptable (Premiere exposes no caption API); mention it after a
  caption pass rather than assuming.

---

## 3. Content instincts worth reusing

- She supplies real source material when the graphic needs specificity (Jason's
  channel page, her own Premiere screenshot). **Ask for the asset rather than
  inventing a placeholder** — she'd rather provide it.
- She liked the meta touches: the Premiere screenshot on the "Edited by Claude"
  card, the checklist recapping the work, the waveform showing the actual cut.
  Self-referential graphics land well for this kind of video.
- Sync coincidences are worth catching — the "two repos" card landed while she held
  up two fingers. Point these out; she enjoys them.

---

## 4. Process lessons (the expensive ones)

**A task is not done when the render finishes. It is done when Premiere has the
file and I have verified it by exporting a frame from the sequence.** The loop is:

```
edit HTML → render (~4 min) → import → swap clip → save → export_frame → LOOK
```

Skipping the last two steps caused the single biggest friction in this project.
She saw stale video repeatedly while I reported "done". If a render is still
running, say **"not in Premiere yet"** — never "done".

**Interrupting requests invalidate in-flight renders.** When a change arrives
mid-render, kill the render (`pkill -f <output>.mov`), apply the change, restart.
Don't let a stale render finish and get swapped in.

**Batch when possible.** Offer to collect several changes and render once. Each
round trip is ~4 minutes of dead time.

**Renders:**
- 4K60 ProRes 4444 with alpha needs `FFMPEG_ENCODE_TIMEOUT_MS=3600000` and
  `PRODUCER_ENABLE_CHUNKED_ENCODE=true`. Without them ffmpeg is killed at 600s —
  **and the process still exits 0 with no file written.** Never trust the exit code;
  check the file exists.
- Large-radius blurs are brutally expensive: the glow version took **36 minutes and
  1.7 GB**; the same composition with a hard edge took **4 minutes and 513 MB**.
- Detailed screenshots inflate ProRes a lot (786 MB vs 535 MB) — many hard edges.

**Premiere quirks:**
- **`export_frame` is unreliable — do not verify timing with it.** It ignores the
  `sequenceId` (renders whichever sequence is active) AND effectively ignores the
  time/playhead: asked for 30s on a 44s sequence it returned the opening frame.
  It cost hours across this project, twice producing false alarms about correct
  work (the "missing" 66% card, and caption sync). To verify what a graphic
  actually shows at time T, extract from the **rendered .mov with ffmpeg** and
  composite over the cut proof. Premiere is for assembly, not for inspection.
- `export_sequence` fails with `MEDIA_ENCODER_NOT_INSTALLED` because it only looks
  directly in `/Applications`. AME lives at
  `/Applications/Adobe Media Encoder 2026/Adobe Media Encoder 2026.app`. Use
  `exportAsMediaDirect` via `execute_extendscript` instead.
- Caption tracks can't be read back via scripting — the `.srt` in `project/` is the
  source of truth.
- Premiere's bridge occasionally returns `Unexpected end of JSON input` under load.
  Just retry.

**Re-place clips in Premiere after ANY change to the cut.** Changing
`silence.json` (an override, a merge) regenerates the transcript and captions but
does NOT touch Premiere. Forgetting this desynced a whole video by up to 6.7s and
read as "captions feel a bit off". The cut, the captions, and Premiere must be
updated as one unit.

**Captions must be retimed onto Premiere's actual clip boundaries.** Premiere
frame-snaps each segment, so its timeline runs slightly shorter than the ffmpeg
cut the transcript was made from — about 2 frames by the end of a 45s video. Read
the real clip starts out of Premiere and pass them to
`captions_overlay.py --timeline`.

**Transcription: use `small.en`, and expect errors to MOVE.** `base.en` mangles
finance and hardware jargon — across one 45s video it produced "trade GPU out",
"trade on Prudel", "Cash shuttle listed on Nimus", "Compu", "the AI8", and once
inverted a sentence to "you will **not** be able to trade". `small.en` (466 MB,
`~/.cache/whisper/ggml-small.en.bin`, now the default in `preprocess.py`) fixed
five of those unaided. It is not perfect — it invented "listed on 9S" — so a
per-video `fixes-*.json` is still required. Critically, **re-running the analysis
re-transcribes and the errors relocate**, so pin every wrong variant seen, not
just the latest one. Always read the full transcript back before rendering.

**Session cost is the dominant expense — reset between videos.** Measured on this
project: 1,285 turns, 1.2M output tokens, but **556M cache reads** because the
whole history is re-sent every turn. That is 435K per turn against ~6K to
bootstrap a fresh session from `NEW-VIDEO.md`. Run `edit/session-cost.py`; exit 2
means stop. If she starts a new video anyway, delegate it to a subagent with a
clean context rather than continuing inline — she explicitly asked for this.

**Read captions as text before rendering.** `edit/review.py` prints the full
wording plus flags odd tokens (it catches the `AI8` / `9S` pattern). A render is
1-60 minutes and 45-100 MB; reading is free. Several rounds this session were
spent rendering to discover a wrong word.

**Verify renders with `edit/check_render.py`, not screenshots.** It measures the
alpha channel of the rendered .mov and reports, as text, whether ink is present
for each cue, whether it sits inside the caption band, and whether the gaps are
clean. 77 images entered context this session, each re-sent on every later turn.

**Disk discipline.** Each render is 0.5–1 GB. Delete superseded versions, and remove
the bin entry *before* deleting the file so nothing goes offline.

**The locked silence recipe is the floor — tightening it damages audio. Don't retest.**
She asked for a more aggressive cut on 2026-08-16; I swept the parameters, built every
candidate and re-transcribed each one. After a normal pass the envelope is no longer
bimodal — the room-tone cluster is gone and only one continuous speech distribution is
left, so there is no valley to move the threshold into. Measured on two clips: gentler
pads (0.015/0.03) bought 1.4–2.1%, which is nothing; pads 0.01/0.02 with a 0.03 gap
bought 4–7% but produced "gets **hosted**", "data **extract and** script", "Fire**call**";
−33 dB bought 8–13% and produced "scrolling through **egg**", "from **Dithrada**", and
truncated a clip's last sentence entirely. Whisper mis-hearing a word it previously got
right is a reliable proxy for a clipped consonant — use it as the test. Verdict: she
kept both cuts unchanged. **Further density has to come from cutting content at sentence
boundaries, not from the silence pass.** Offer specific lines with timings and let her
choose; she declined all of them this time, so don't assume trims are wanted.

---

## 5. Standing instructions

**Raw footage cleanup — end of project only.** Once the final video is exported to
`output/` *and she has explicitly said it's the final export*, delete the source
footage from `footage/`. Do not do this earlier, do not do it on an intermediate
export, and do not infer it from a video merely looking finished. The trigger is
her saying to export at the very end. Footage is irreplaceable and is not in git —
confirm the export exists and plays before removing anything.

**Caption orientation follows the footage.** Her rule, verbatim: "if a video is
vertical, use vertical captions. if its horizontal, use horizontal captions." So check
the real frame before choosing `--res` — and check it from the *proof*, not from
`ffprobe` on the source, which reports rotated display dimensions and reported 1080x1920
for footage that was actually 1920x1080. This matters more than it sounds: the 42-char
broadcast caption line only physically fits in landscape. In 9:16 at 54px
`captions_overlay.py` derives ~24 chars, which is why forcing 42 there breaks cues
mid-clause. CLAUDE.md now carries this as a per-orientation table rather than a flat
42; the number is derived from frame width, never hardcoded. Landscape: `--res 1920x1080 --y 0.82 --size 48
--maxw 0.61 --mindur 0.7 --maxdur 3.5` gives exactly 42 chars in the lower third.
Vertical keeps the tool's defaults (`--y 0.25`, 24 chars, 0.55/2.2) — `y` is measured
from the top, and 0.25 keeps captions clear of the TikTok UI. (Established 2026-08-16.)

**`output/` is hers alone — never delete from it.** Claude does not remove, overwrite
or sweep anything in `output/` under any circumstances, including exports that look
"superseded" or "old". She deletes those manually once the video is posted to
Instagram and TikTok, and only she knows when that has happened. `edit/cleanup.py`
already refuses `output/` by path — keep it that way and never hand-roll around it.
(Established 2026-08-16.)

**She cleans up finished projects herself, and that is expected.** Once a video is
exported to `output/`, she deletes that project's footage, cut proofs, analysis dir,
graphics and captions to reclaim storage — the export is the deliverable and the
intermediates have no further use. So if an `edit/analysis-*/` directory or the
footage for an already-exported video disappears mid-session, that is routine
housekeeping, not data loss. Check whether the missing files belong to an *exported*
project before saying anything. (Established 2026-08-16, after I escalated her own
cleanup of the Reddit and GPU projects as a deletion mystery and burned a chunk of
the session on it.)

**The spec used to contradict itself, and it cost real time.** A 2026-08-17 audit found
seven conflicts between CLAUDE.md, NEW-VIDEO.md and the code — most of them because
`tools/silence-cut.py` and `tools/captions.py` were a second, stale implementation of
the "locked" recipes that nothing but one CLAUDE.md line still referenced. They
disagreed with `edit/preprocess.py` on sample rate (hardcoded 48k vs. detected) and
still named `base.en`. `tools/` is deleted; `edit/` is the only implementation. The
lesson: when a recipe is "locked", it must have exactly **one** implementation, and the
docs must name that one. Two copies of a locked recipe silently diverge, and the second
copy is the one someone reads. Same fix for fps — preprocess.py now detects it and
records it in `silence.json`, and `captions_overlay.py` reads it from there instead of
carrying its own default. The old split (60 in one file, 30 in another, every real video
30) frame-snapped cut lists to a grid nothing else used. (Established 2026-08-17.)

## 5b. Standing to-dos

- [ ] Duplicate 62.05s "Intro - Silence Pass" sequence still in the project
- [ ] Superseded renders accumulate — sweep at the end of a session
- [ ] Jason's avatar/thumbnail are git-ignored; a fresh clone can't render that card
