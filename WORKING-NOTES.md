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
- `export_frame`'s `time` argument doesn't map exactly; a "missing" graphic may just
  be a frame landing in a gap between cards. Cross-check against the visible caption
  before concluding something is broken.
- `export_sequence` fails with `MEDIA_ENCODER_NOT_INSTALLED` because it only looks
  directly in `/Applications`. AME lives at
  `/Applications/Adobe Media Encoder 2026/Adobe Media Encoder 2026.app`. Use
  `exportAsMediaDirect` via `execute_extendscript` instead.
- Caption tracks can't be read back via scripting — the `.srt` in `project/` is the
  source of truth.
- Premiere's bridge occasionally returns `Unexpected end of JSON input` under load.
  Just retry.

**Disk discipline.** Each render is 0.5–1 GB. Delete superseded versions, and remove
the bin entry *before* deleting the file so nothing goes offline.

---

## 5. Standing instructions

**Raw footage cleanup — end of project only.** Once the final video is exported to
`output/` *and she has explicitly said it's the final export*, delete the source
footage from `footage/`. Do not do this earlier, do not do it on an intermediate
export, and do not infer it from a video merely looking finished. The trigger is
her saying to export at the very end. Footage is irreplaceable and is not in git —
confirm the export exists and plays before removing anything.

## 5b. Standing to-dos

- [ ] Duplicate 62.05s "Intro - Silence Pass" sequence still in the project
- [ ] Superseded renders accumulate — sweep at the end of a session
- [ ] Jason's avatar/thumbnail are git-ignored; a fresh clone can't render that card
