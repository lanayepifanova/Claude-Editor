# Working notes — how Lana works, and what she wants

A living document. **Update it at the end of any session where a preference is
established, reversed, or clarified.** `CLAUDE.md` is the *spec* (the settled
rules); this is the *context* behind it — how she asks, what she reacts to, and
what I've learned the hard way.

Last updated: 2026-08-29 · after "oil markets" (70.7s → 48.4s, captions-only route)

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
| Full-frame graphic takeovers | **Panels floating over the video** (reversed 2026-08-17) |
| The decks' own colour | **B&W with one accent hue kept** |

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

**`app.project` is NOT the project you just opened — guard on the path before every
mutation.** On 2026-08-17 this destroyed `Reddit - Cut` and `GPU Hours - Cut`. Premiere had
three projects open at once and **two of them were named `Demo.prproj`** (the repo one and a
default at `~/Documents/Adobe/Premiere Pro/26.0/`). `open_project` reported success and
`list_sequences` showed the right sequences, but ExtendScript's `app.project` still pointed at
a *different* open document, so the sequences were built against the wrong project and
`save_project` wrote the wrong contents over `project/Demo.prproj` — 28,167 bytes down to
16,321. Git had it tracked, so `git checkout -- project/Demo.prproj` restored it fully; that
was the versioning saving it, not any care taken at the time. The procedure now:

1. `cp project/Demo.prproj` somewhere first — belt and braces on top of git.
2. Close every other open project (`closeDocument(0,0)`) so exactly **one** remains.
3. Assert `app.project.path === <repo path>` and `app.projects.numProjects === 1` at the top
   of every mutating script, and return `ABORT` otherwise.
4. List the sequences **before** saving and confirm the old ones are still there.
5. After saving, parse the `.prproj` on disk and confirm the names survived.

Never trust a save because the tool returned `success: true`. (Established 2026-08-17.)

**The 2026-08-17 clobber repeated on 2026-08-19 — because step 3 of the procedure
above is not actually executable.** `evaluate_expression` rejects every argument
spelling (`expression`, `code`, `returnValue`) and returns `{"type":"undefined"}`
for all of them, so the `app.projects.numProjects === 1` assertion cannot be run
through the bridge. Proceeding without it is what cost the four old sequences:
two documents were open on the same path, the first `save_project` wrote the good
one (41,176 bytes, five sequences, verified on disk), and the second wrote the
*other* document over the same path (18,464 bytes, one sequence). No MCP call of
mine touched the sequences — `app.project` simply resolved to a different document
between the two saves.

**The workable substitute is `get_project_info`'s `itemCount`** (or
`list_project_items`): the good document reported 18 items, the stray one 3. Record
it before the first mutation and re-check it before and after every save — a change
means `app.project` moved and the next save will clobber. Also parse the `.prproj`
on disk after *every* save, not just the last one; the 41 KB file was correct and
the damage was only visible after the second save. Recovery here was free (git HEAD
plus three 2026-08-18 autosaves each held all five sequences, and the autosave
folder is the thing to copy out first), and Lana then chose to discard them —
`Demo.prproj` is now Sony-only by her decision, not by the accident. (Re-established
2026-08-19.)

**A second Premiere save in the same session can land in a different document —
`itemCount` is the check that works.** After the 2026-08-19 clobber, every save
this session was bracketed with `get_project_info`: 3/3, 4/4, 5/5, 6/6 across
four saves, and none moved. That is the assertion the written procedure wanted
and could not express, because `evaluate_expression` cannot run one. Cheap, and
it turns an invisible failure into a visible number.

**`delete_project_item` reports success without deleting.** It returned
`success: true, method: "deleteBin"` on an unused footage item that was still in
the Project panel afterwards; `delete_multiple_project_items` then died with
`deleteResults.filter is not a function`. Removing a project item is a manual
step — say so rather than reporting it done.

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
  The preset that works is AME's factory `H264 Match Source - High bitrate.epr`
  (`/Applications/Adobe Media Encoder 2026/Adobe Media Encoder 2026.app/Contents/
  MediaIO/systempresets/3F3F3F3F_4D6F6F56/`); `get_encoder_presets` returns an empty
  list because factory preset enumeration isn't supported. Call it as
  `seq.exportAsMediaDirect(outPath, presetPath, 0)` — `0` = entire sequence.
- **That preset writes PCM audio into the .mp4, not AAC.** `pcm_s24le` in an MP4
  container plays in Premiere and QuickTime but is rejected or silently muted by
  several browsers and social uploaders, and it inflates the file ~25%. Always
  `ffprobe` the export and, if audio is PCM, remux with
  `ffmpeg -c:v copy -c:a aac -b:a 192k -movflags +faststart` — video is untouched,
  so it costs nothing in quality. (Established 2026-08-18 exporting Firecrawl -
  Photos: 46.6 MB PCM became 37.8 MB AAC.)
- **`get_sequence_structure` reports every clip's source `inPoint`/`outPoint` one
  frame low** — durations and timeline positions are exact, only the source in/out
  read 0.033s early. Seen on all 20 clips of `Sony TSMC - Cut` (2026-08-19), video
  and audio alike, against in-points that were already on the frame grid. Don't
  treat it as a placement error and don't "correct" the cut list for it. If it ever
  matters, the check is whether the final frame of each kept segment carries energy
  above the hysteresis floor — on that clip every one was room tone, so a one-frame
  shift could not have clipped a word either way.
- **`create_sequence_from_clips` rejects every argument spelling tried** and
  `create_sequence` ignores frame rate, so the way to get a correctly-specced blank
  timeline is `duplicate_sequence` with `clearContents=true` from a sequence that
  already has the frame rate you want, then `set_sequence_resolution`. `Firecrawl -
  Cut` is the clean exact-30fps donor (timebase 8467200000); `GPU Hours - Cut` is
  30.00003 and `Reddit - Cut` is 29.97.
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

**Not every video goes through Premiere — sometimes the deliverable is just the
captioned cut.** On 2026-08-29 the bridge was down and she said: "its ok i dont
rlly need the premiere bridge right now since i dont need the graphics." So the
pipeline has a shorter route that ends at `output/`: cut the **original** footage
with the `silence.json` segments, composite the rendered caption overlay, encode
H.264/AAC. No sequence, no assembly, no caption retiming onto Premiere's frame
grid (that step only exists because Premiere snaps clips — ffmpeg does not, so
the overlay and the cut share a frame count exactly: 1453 and 1453 here).

Two things to get right on that route. **Cut from `footage/`, never from
`cut_proof.mp4`** — the proof is half-resolution (960x1706 for 1080x1920
footage) and using it is exactly what baked permanent softness into the
Firecrawl export. And **check `output/` before writing**, since it is hers alone.
There was no script for this; it is ~15 lines of ffmpeg `trim`/`concat` built
from the segment pairs. Worth turning into `edit/burn.py` if she asks for it
again. Verify the burn with a luma-difference `signalstats` read against the
uncaptioned master rather than by eye — `check_render.py` only sees the overlay,
not the composite. (Established 2026-08-29.)

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

**The masters for Firecrawl and Browser Use were deleted before either was ever
exported, and the quality loss is permanent.** On 2026-08-17 she asked to export both
("they are good to go"). `output/` was empty — neither had ever been exported — and
`footage/` held only `.gitkeep`. `silence.json` still named the sources
(`footage/Firecrawl.mov`, 57.48s; `footage/Browser Use.mov`, 81.02s). Both were gone:
nothing in Trash, on `/Volumes/Claude`, in iCloud, in the Adobe media cache or preview
folders, and nothing in a filesystem-wide sweep for large video. Footage is gitignored,
so git could not help either. Neither video ever entered Premiere — `Demo.prproj` carries
only `Reddit - Cut` and `GPU Hours - Cut` — so there was no sequence or preview render to
fall back on. The **only** surviving picture was `cut_proof.mp4` at **960x540**, half the
1920x1080 the captions were built for. She chose the salvage export: lanczos upscale to
1080p with the natively-rendered 1080p overlay composited on top, so the text is sharp
and the footage is soft. That softness is now baked into the deliverable and cannot be
undone. The rule in this section was already right; what it was missing is that the
housekeeping exemption below ("footage for an already-exported video disappearing is
routine") **only applies once the export actually exists in `output/`**. Check `output/`
before concluding that missing footage is routine — that check is what separates
housekeeping from an unrecoverable loss. (Established 2026-08-17.)

**Commit the repo after every export, before cleanup — she asked for this
explicitly.** Her words, 2026-08-17: "including all the files that are deleted in the
edit, this should be updated in the repo each time please." So `git add -A` (deletions
included), commit, push — the repo is meant to track each project's arrival *and* its
cleanup, not drift out of date until someone notices. Ordering is the part that bites:
on 2026-08-17 her cleanup ran between the export and the commit, and
`graphics/firecrawl-captions/index.html` and `graphics/browser-use-captions/index.html`
were still untracked when it did, so they went from disk to nothing with no git copy.
`.gitignore` promises that heavy renders are safe to delete *because* "the compositions
that generate them are versioned instead" — that promise only holds if the composition
was committed first. Analysis dirs are the same story: once `transcript.json` is gone,
the composition cannot even be regenerated. **Commit at export time, then let cleanup
run.** (Established 2026-08-17.)

## 5b. Standing to-dos

- [x] Duplicate "Intro - Silence Pass" sequence — moot, the project is Sony-only now
- [x] Superseded renders accumulate — **done 2026-08-19**: `cleanup.py --renders`
      sweeps loose `graphics/*.mov|mp4` whose composition is committed. Four of
      them were 1.5 GB after one video, and nothing else reached them.
- [ ] Jason's avatar/thumbnail are git-ignored; a fresh clone can't render that card
- [ ] Keep the Firecrawl / Browser Use `cut_proof.mp4` files until both are posted — they are the only caption-free copy of either cut
