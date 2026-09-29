# Working notes — how Lana works, and what she wants

A living document. **Update it at the end of any session where a preference is
established, reversed, or clarified.** `CLAUDE.md` is the *spec* (the settled
rules); this is the *context* behind it — how she asks, what she reacts to, and
what I've learned the hard way.

Last updated: 2026-09-21 · after she asked for repeated takes to be cut down to the
last one, and then for Premiere Pro to be removed from the studio entirely

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
- **Caption position** — *resolved 2026-09-21.* She asked to shift captions up,
  then said the default was fine. It used to be unscriptable and something she
  had to nudge by hand in a GUI; with captions burned as an overlay it is just
  `captions_overlay.py --y`. Move it on request.

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

**A task is not done when the render finishes. It is done when the file she will
actually watch exists in `output/` and has been verified.** The loop is:

```
edit HTML → render (~4 min) → burn.py → --verify → THEN say done
```

Skipping the last two steps caused the single biggest friction in this project.
She saw stale video repeatedly while I reported "done". If a render is still
running, say **"still rendering"** — never "done".

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

**Verify a render with ffmpeg, never by looking at a frame an app gave you.**
The old route verified timing by asking Premiere to export a frame; it ignored
both the sequence and the requested time, and cost hours across this project by
twice raising false alarms about work that was already correct. Extract from the
rendered `.mov` with ffmpeg and composite over the cut proof, or use
`check_render.py` / `burn.py --verify`, which read the file itself and report as
text. (Established 2026-08-17; the tool that caused it is gone as of 2026-09-21,
the habit stays.)

**`ffprobe` every export before calling it delivered.** The old encoder quietly
wrote PCM audio into an `.mp4` — it played fine locally but was rejected or
silently muted by several browsers and social uploaders, and inflated the file
~25%. `burn.py` writes AAC now, so this cannot recur on the current route, but
the habit of probing the actual deliverable is what caught it.

**Re-run everything downstream after ANY change to the cut.** Changing
`silence.json` (an override, a merge) moves every timing after it. Back when the
assembly lived in a separate app, forgetting this desynced a whole video by up to
6.7s and read to her as "captions feel a bit off". The cut, the captions, the
graphics and the export are one unit — rebuild them together, never patch one and
leave the rest.

**Transcription: use `small.en`, and expect errors to MOVE.** `base.en` mangles
finance and hardware jargon — across one 45s video it produced "trade GPU out",
"trade on Prudel", "Cash shuttle listed on Nimus", "Compu", "the AI8", and once
inverted a sentence to "you will **not** be able to trade". `small.en` (466 MB,
`~/.cache/whisper/ggml-small.en.bin`, now the default in `preprocess.py`) fixed
five of those unaided. It is not perfect — it invented "listed on 9S" — so a
per-video `fixes-*.json` is still required. Critically, **re-running the analysis
re-transcribes and the errors relocate**, so pin every wrong variant seen, not
just the latest one. Always read the full transcript back before rendering.

**The ffmpeg route to `output/` started as a fallback and became the whole
pipeline.** On 2026-08-29 the Premiere bridge was down and she said: "its ok i
dont rlly need the premiere bridge right now since i dont need the graphics." So
a shorter route was built: cut the **original** footage with the `silence.json`
segments, composite the rendered caption overlay, encode H.264/AAC. It turned out
to be *better* than the route it replaced — nothing frame-snaps the segments, so
the overlay and the cut share a frame count exactly (1453 and 1453 here) — and on
2026-09-21 she removed Premiere altogether. This is now the only route.

Two things to get right on that route. **Cut from `footage/`, never from
`cut_proof.mp4`** — the proof is half-resolution (960x1706 for 1080x1920
footage) and using it is exactly what baked permanent softness into the
Firecrawl export. And **check `output/` before writing**, since it is hers alone.
There was no script for this; it is ~15 lines of ffmpeg `trim`/`concat` built
from the segment pairs. Worth turning into `edit/burn.py` if she asks for it
again. Verify the burn with a luma-difference `signalstats` read against the
uncaptioned master rather than by eye — `check_render.py` only sees the overlay,
not the composite. (Established 2026-08-29.)

**That route is now `edit/burn.py`** — she asked for it a second time on
2026-09-05 (four videos in one go), which was the trigger the note above named.
It cuts from `footage/` per `silence.json`, composites the overlay, encodes
H.264/AAC, refuses to overwrite anything already in `output/` without `--force`,
and keeps the uncaptioned master so the burn can be re-verified later with
`--verify-only`.

**Verify the burn by counting changed PIXELS, not mean luma.** The first version
of that check compared average luma between burn and master and reported "100% of
frames carry ink" on all four videos — meaningless, because the two files are
encoded separately and x264 noise alone reads ~1.0 YAVG, the same order as the
text. Binarising the difference first (`lut=y='if(gt(val,60),255,0)'`) drops the
noise and leaves the strokes; coverage then tracks the SRT closely (1246 inked
frames against 1244 cue-covered on hugging face, 97% on the two videos with real
gaps). A verification that passes on everything is not a verification.
(Established 2026-09-05.)

**Whisper can time a real word past the end of the cut, and dropping it loses
speech.** `captions_overlay.py` discarded any word starting after
`cut_duration`, which is right for a hallucinated trailing token but wrong for
drift: on "instinct" the closing "beta." was timed at 34.14s on a 33.97s cut and
vanished, so the last caption read "still in private". It now keeps a word that
lands within 0.75s of the end and pulls it onto the final frames. Check the last
cue of every video against the transcript tail — that is where this hides.
(Established 2026-09-05.)

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

**She asked for LESS cut for the first time on 2026-09-05 — and the recipe was not
the problem.** Her words: "make the instinct video less cut, there was some parts
that were cut too soon", then two examples ("last few weeks", "not even public
yet") and one on another clip ("the last bit for the '22b valuation' in the
polymarket video was cut off"). The instinct to reach for the sanctioned tail-pad
bump (0.04 -> 0.07) would have fixed none of them. What was actually happening:

- **Quiet trailing speech never trips the -35 dB trigger and is deleted as room
  tone.** "weeks" peaked at -39 dB and was removed with the 2.9s pause after it;
  polymarket's closing "valuation" peaked at -35 and fell off the end the same way.
- **A brief dip inside continuous speech gets sliced by the 0.05s min-gap.**
  "public yet" is one unbroken 0.40s utterance; the pass punched a 0.16s hole in
  the middle of it, so the phrase read as cut out.

She approved the result outright ("perfect!!"), so this is settled: when she says
something was cut too soon, restore the quiet speech — do not touch the recipe,
and do not reach for the tail-pad bump first.

The fix is `edit/restore_speech.py`, which does NOT touch the locked recipe: it
scans the REMOVED regions for runs above -45 dB lasting >=0.06s that are adjacent
to a cut, and writes `overrides-<name>.json` extending the neighbouring segment
over them. instinct +2.24s (12 spots), polymarket +1.49s (7). Run it after
preprocess, then re-run preprocess with the overrides.

**Only restore speech ADJACENT to the cut.** The first version extended to the
last qualifying run anywhere in the gap, which reached a lone breath 3s into a
pause and dragged the whole pause back with it — polymarket went 35s -> 46s. A
blip alone in the middle of a long silence is a breath; only a run continuing
from the cut (or leading into the next segment) is a clipped word.

**A by-product worth knowing: re-cutting re-transcribes, and the fixes moved
again.** "The valuation" became "The evaluation", "Polymarket" became "Poly
Market", "Kalshi" became "CalShe" (a variant not in the fixes file from the first
pass). Re-read every transcript after any change to the cut. The restored audio
also finally resolved a line I could not make sense of: "sort of like mine" was
"sort of like a fine line" — the words that made it parse had been cut out.

**Cues shorter than a frame render as nothing.** `check_render.py` reported NO INK
for "for" on instinct: the grouper left it as a 0.06s cue between two neighbours
that started 0.02s later, so at 30fps the word never appeared on screen. Borrowing
words backward and stretching the end both failed there because both neighbours
were immediate. `captions_overlay.py` now merges any cue still under 0.20s into
whichever neighbour can legally take it. This had been happening before anyone
noticed — the first pass flagged the same pattern on two cues. (2026-09-05.)

**The recipe's -35 dB is an ABSOLUTE threshold, so it only means what it meant if the
clip is recorded at the usual level. Check the loudness before trusting the cut.**
`openai.mov` (2026-09-09) came in at **-29.9 LUFS integrated, -11.0 dBFS true peak** —
roughly 12 dB under every clip the recipe was tuned on. The envelope was still cleanly
bimodal (room tone clustered at -74 dB, speech at -36/-34), but -35 landed *on top of the
speech cluster* rather than in the valley at -55..-64, so the pass cut 60.8s down to 35.5s
and about **13 of those 25 removed seconds were words**. The damage was invisible in the
duration and obvious in the transcript: the closing line "Navier-Stokes can blow up" came
out as "they glow up", "in finite time" disappeared, "can be checked by" became "compact
by". Two checks catch this and both are cheap:

- `ffmpeg -af ebur128` on the source. Well under ~-20 LUFS means the threshold is sitting
  too high inside the speech and the cut will eat quiet words.
- **Transcribe the ORIGINAL with full context (`whisper-cli` without `-ml 1`) and diff it
  against the cut's transcript.** Full-sentence context is markedly more accurate than the
  word-level pass, so it doubles as the ground truth for the fixes file — it got
  "formalized in Lean", "Clay Mathematics Institute" and "millions of messages" that the
  `-ml 1` run rendered as "gleaned", "Klee" and "a million inches". Missing *content words*
  in the cut (not just mangled ones) are the tell.

The fix is still `restore_speech.py` and still no change to the recipe — but the default
`--quiet-db -45` is not low enough on a quiet clip, because the trailing speech itself sits
at -47..-53. **Put `--quiet-db` in the valley for that clip** (-50 here). Two independent
routes agreed on where the cut belonged: `--quiet-db -50` gave 48.6s, and a control that
gain-corrected the audio +12 dB and ran the locked recipe completely untouched gave 49.3s.
Density did not suffer — the longest quiet run inside the finished 48.6s cut is **0.16s**,
so the extra 13s is speech, not air. Worth running that +12 dB control any time the
restoration looks alarmingly large; it says whether the growth is real speech or slop, and
it costs one preprocess run.

Her verdict on this pacing is still pending as of the export. (Established 2026-09-09.)

**A clip can have no room-tone cluster at all, and then the histogram — not the
duration — is the tell.** `anthropic.mov` (2026-09-09) measured **-25.1 LUFS, -5.9 dBFS
true peak**: only ~5 dB quiet, far less alarming than openai's -29.9, and the pass removed
just **19%** where openai removed 42%. Both of those reassuring numbers were wrong. The
envelope had **no valley to put a threshold in** — a continuous distribution rising from
-57 straight through to a peak at -30, with a true noise floor at -71 populated by almost
nothing. The median of the whole envelope was **-34.2 dB**, so the locked -35 sat
essentially *at the midpoint of the speech itself*. A low removed-percentage is not
evidence the cut is safe; on a clip with no pauses it just means there was little to
remove. **Plot the histogram every time and find the valley before trusting -35.**

The confirmation route that works, and costs one preprocess run: **gain the audio to about
-18 LUFS and run the locked recipe completely untouched.** Here +7 dB gave 41.2s against
the raw pass's 37.6s, and its transcript recovered every word the raw cut had lost. That
number is the target the restoration has to hit.

**`restore_speech.py` could not reach the quietest words on this clip, and lowering
`--quiet-db` far enough would have undone the cut.** Trailing speech here ran much lower
than on openai: "us all" sat at **-55..-59 dB** and "control" at -47..-55, against a -71
floor. `--quiet-db -48` matched the control's duration (41.9s vs 41.2s) and recovered most
losses, but -56 was needed to reach "us all" — and -56 restored 7.2s, leaving barely any
cut at all. The answer was **-48 plus five hand-checked `overrides` spans**, not a deeper
sweep. `preprocess.py --overrides` accepts `"in"` as well as `"out"`, which is what makes
targeted repair possible.

**Whisper will hallucinate a cut phrase back from context, so the transcript diff can
give a FALSE PASS.** The -48 cut transcribed as "could kill us all" while the region
holding "us all" (4.37-4.97) was still entirely removed — the language model simply
completed the idiom. Reading the transcript is necessary and not sufficient. The check
that does not lie is **peak level against the room-tone floor**: `astats` on the region
gave peak -25.6 dB where true room tone peaks at -62.6, i.e. 37 dB above the floor —
unambiguously speech, merely soft. Use RMS to find candidates and peak-vs-floor to decide.
Conversely, a 0.4s run at -50..-56 flanked by speech is usually a **breath**, and breaths
sit in the same RMS band as quiet speech; two such runs were left cut here and the words
around them survived intact.

**The last check is to transcribe the finished export.** `output/anthropic.mp4` came back
word-for-word identical to the ground truth read off the original. That is the only check
that covers the cut, the overrides, the caption timings and the burn at once.

**`edit/burn.py` cut every segment one frame long on this camera — now fixed.** The master
came out 1310 frames against the overlay's 1308 and burn.py refused to composite. The
segments were all exactly on the 30fps grid; the fault was that this camera writes frame
timestamps **truncated rather than rounded** (frame 108 lands at 3.599999, not 3.600000),
so `trim`'s half-open `[start, end)` still admitted the frame sitting on the boundary.
`build_master` now ends the **video** trim half a frame early — which excludes that frame
whether the timestamp was truncated or exact, and cannot reach the previous one — and
takes fps from `silence.json`. Audio is sample-accurate and is left alone.

**A `fixes-*.json` entry must never carry punctuation.** `apply_fixes` strips punctuation
when *matching* but emits the replacement **verbatim**, so an entry like
`"Anthropic,": "Anthropic,"` matches every bare "anthropic" and injects a comma —
producing "science at Anthropic,," and "Anthropic, is trying". Write bare words on both
sides; the tool re-attaches the original trailing punctuation itself.

**"Don't cut the dead space between 'kill us all'" — a pause *inside one phrase* is
hers to keep, even when it is genuinely silent.** (2026-09-09, anthropic.) Every earlier
note about this pass is about *speech* the recipe deleted; this one is not. The two
0.133s removals at source 3.600-3.733 and 3.867-4.000 were real silence, correctly
detected, and the 0.05s min-gap is doing exactly what the locked recipe says. She still
wanted them back, because they fall between "could kill" and "us all" and cutting there
chops the delivery of a single clause. The tell in the data was that whisper timed "kill"
at **0.02s** on the cut timeline — a word that short means the pass sliced through it.

So `restore_speech.py` is the wrong tool for this, and running it harder is the wrong
instinct: there is no quiet speech to find. The fix is a hand `overrides` span that
*merges across* the gaps — here seg 0 was extended to swallow segs 5 and 6, giving one
continuous kept region 0.0-9.033 — which restores the pauses and changes nothing else.
Cut went 43.60s -> 43.87s. **The recipe stayed exactly as locked; only the override moved.**

Watch for this phrasing generally: **"don't cut X"** where X is a *phrase she delivers as
one breath* means hold the whole span, silence included. That is different from **"X was
cut out"** / **"cut too soon"**, which still means quiet speech was deleted and still
routes to `restore_speech.py`.

One thing that survived the re-cut and is worth flagging next time: the captions still
break this phrase as "helped build could kill" / "us all." The 24-char vertical budget
allows "could kill us all." as its own cue, but the grouper ends a cue on "kill" because
only *leading* orphans are protected — it has no rule against stranding the object of a
verb. Left alone here because she asked about the cut, not the caption.

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

**Repeated takes are hers to cut, and the LAST one is always the keeper.**
(2026-09-21, chatcut.) Her words: *"if a sentence repeates twice, that means its a
retake, so you should cut out out all repeats of that sentence or line besides the
last one, since the last one is the usable take."* She asked for it to be written
down as standing behaviour, so it is now in `CLAUDE.md` and in the `NEW-VIDEO.md`
loop — run the pass on every video without being told. She says the quiet part out
loud on this clip: *"apparently I need three attempts to finish a sentence."*

The tool is `edit/retakes.py`, and it is deliberately a *separate* pass from the
silence recipe — this removes **content**, which the locked recipe must never do.
It groups the cut transcript into lines, compares only nearby ones, and flags a
near-duplicate (difflib ratio, default 0.72) or a false start (a run the next
attempt restates from the top). Here it found exactly one: "an editing process you
like" against "an editing process **that** you like" at ratio 0.98 — a reworded
retake, which is why the threshold is a ratio and not equality. Default is
report-only; read it before `--apply`, because a false positive deletes a real
sentence and nothing downstream will notice.

Removals are written as a **source-time `remove` list** in `overrides-<name>.json`
and excised by `preprocess.py --overrides` (new: `excise()`), not as segment
indices. Indices move every time detection re-runs; a source span does not, and a
span landing mid-segment splits it, which `in`/`out` cannot express.

Two seams cost a round each and are now handled in the tool:
- **Whisper ends every word exactly where the next one starts**, so the dying
  take's last word ("footage.", t1 36.16) looked like it ran into the segment
  holding the *replacement* take (starting 36.033). Padding from there ate 0.127s
  off the good take's "And". Anchor the pad on the **neighbour's** segment, never
  on the doomed line's own.
- A leftover under 0.30s at either edge is not a word, it is the **stub of the
  take just removed** — 0.12s of the dropped "And" survived as its own segment
  because it cleared `MIN_SEG`. Spans now snap out to the segment edge.

**`restore_speech.py`'s default `--quiet-db -45` assumes a quiet room, and this
clip does not have one.** chatcut measured **-16.4 LUFS, 0.1 dBFS true peak** —
the best-recorded clip in the project — but its **room tone peaks at -40 dB**
(RMS -52), where anthropic's peaked at -62.6. Run at the default, restore_speech
proposed 11 spots and +2.28s whose candidates peaked **-36 to -43 dB**, i.e. at or
*below* the room-tone peak. Every one was noise. Restoring them would have put the
dead air back — the opposite of what she asked for. **Loudness is not the tell;
the room-tone PEAK is.** Measure it with `astats` on an actual gap before trusting
any `--quiet-db`, and compare candidates against that number, not against -45.

What *was* real on this clip was the 0.05s min-gap slicing **through** words rather
than between them. Measuring the peak inside each sub-0.15s gap separated the two
cleanly: seven gaps came back at -24.7 to -33.2 dB (7-15 dB above the -40 floor —
speech), three at -36.2 to -37.4 (floor — genuinely between words). The tell in the
transcript was whisper mangling "repeated takes" into "repeat a take" on the cut
while the full-context read of the original got it right — the mis-hearing proxy
from the 2026-08-16 sweep, firing exactly where the measurement pointed. Six hand
`overrides` merges (0.55s total on a 40s cut) fixed it; the recipe was not touched.
One of the seven was deliberately left out: its join sat inside the retake being
removed, and merging it would have left a 0.117s stub after the excision — it
cleared `MIN_SEG`, so nothing else would have caught it.

**Delivery resolution is not always the footage's resolution, and three tools
quietly assumed it was.** chatcut.MOV is the first 4K clip in the project (3840x2160
at 60fps); every earlier one was 1080p, which is why nothing had ever disagreed.
She chose a 1080p export, matching the landscape caption spec. Three things broke
on that, all silent rather than loud:

- **`burn.py` composited with `overlay=0:0`, which does not scale** — a 1920x1080
  overlay would have landed in the top-left quarter of a 4K master. It now probes
  both and scales the master to the overlay's size on the way out of the concat,
  so the master itself is the deliverable resolution and the frame counts still
  line up. (It caught the mismatch either way — `sys.exit("overlay resolution does
  not match the cut")` — but catching it after the expensive master build is late.)
- **`check_render.py`'s `--band` defaulted to `0.18,0.34`**, the 9:16 band for
  `--y 0.25`. Run against a landscape render it reported **NO INK for all 11
  sampled cues** while the render was perfect — the ink was at 0.82, outside the
  band it was looking in. It now derives the band from a `--y` that matches the
  one `captions_overlay.py` was given. A verification that fails on everything is
  as useless as one that passes on everything.
- **`review.py` hardcoded a 26-char line budget** while `captions_overlay.py`
  derives the real one from frame width and font size (42 in landscape). It
  flagged 22 of 31 perfectly legal cues. Now `--maxchars`. Same lesson as the
  `tools/` split in 2026-08-17: a number with two copies is a number that will
  disagree with itself.

**`captions_overlay.py`'s ORPHAN list had no subordinating conjunctions**, so a
cue ended on "...and repeated takes, **because**" — a mid-clause break, which the
phrase-boundary rule in CLAUDE.md forbids. Added because/though/although/while/
since/unless/until/whether/after/before. Safe, because the orphan pull only runs
on an *overflow* flush, never on a flush at sentence punctuation, so a legitimate
"...like I said before." is untouched. The break moved to "the pauses and repeated
takes," / "because apparently I need three attempts". The known gap is still open:
nothing protects the object of a verb, so cues can still end on "or bring" and
"and move things".

**`preprocess.py` could not read this camera's frame rate.** ffprobe reports
`60/1,` with a trailing separator for chatcut.MOV, and `frame_rate()` died on
`int("1,")`, exiting with the message but **code 0** — a silent no-op that looks
like a completed run in a background task. The parse now strips the separator.
Worth remembering that the exit code lied here, as it did for the ProRes renders.

**Some footage is variable-frame-rate, and `burn.py` now conforms it.** (2026-09-28,
higgsfield.) The clip reports `r_frame_rate=30/1` but writes stamps off the 1/30 grid
(3953 frames at an average 30.011fps, e.g. 48.235), so grid-aligned trims admitted a
varying number of frames: master 1249f against the overlay's 1260f, and burn refused.
Each branch is now `fps=N` before the trim, and the trim is in whole frames
(`start_pts`/`end_pts`), because a seconds trim printed to 6 places rounded 65.0666…
*up* past frame 1952 and dropped it. `avg_frame_rate` differing from `r_frame_rate`
in ffprobe is the tell.

Same clip, same pattern as openai/anthropic: -22.1 LUFS, room tone RMS -72 / peak -55,
and the locked pass clipped "Higgsfield" to "Higgs", "marketing team" to "market" and
"cashback pool" to "rule". The +4 dB control did not recover them; `restore_speech.py
--quiet-db -50` did (38.1s -> 42.0s, candidates -32..-45 dB, all well above the -55
floor). Whisper hears her CTA "Comment strategy" as "Common strategy", and the
full-context read of the original drops the line entirely.

**`restore_speech.py` can restore a head-turn, not a word — she caught it.** (2026-09-29,
higgsfield.) "There is a big pause between 'including' and 'Seedance' ... its like me
looking to the side." The restore at `-50` had brought back 69.97-70.87: RMS -32, peak
-23.6, far above the -55 floor, so it passed every level check. Transcribed **on its own**
it came back as "(wind whooshing)" — clothing/hair rustle as she turned to look at her
notes. On the cut timeline whisper had smeared "Seedance" across it, which hid it. Fix was
a `remove` span; the recipe did not move. **Level alone cannot tell speech from a rustle.
Transcribe each restored run in isolation before trusting it** — a blank or bracketed
non-speech result means cut it.

**She wants b-roll with no gaps — "fill in the dead space".** After seeing the first pass
(message beats only, her face held clear between them), she asked for "random higgsfield
videos from the media kit, just to fill in the dead space". So on a kit-driven video,
plate the whole runtime, CTA included; filler is picked for motion and is named `fill *`
in `build_clips.py`. One trap: **no stranger's face directly before a person reveal** — an
openbinge close-up of a man played right before "is this guy" and read as Alex.

**Sound effects go in at the burn**: `burn.py --sfx path@seconds[@gainDb]`. The pop on
the Alex photo is the bundled media-use `pop.mp3` at -12 dB, peaking ~-15 against her
-6.8 dialogue. Her ask was "a little sound effect", so keep them small.

---

## 5. Standing instructions

**No NLE, and don't offer one.** On 2026-09-21 she asked: *"can you delete all the
stuff in this claude editor that has to do with the premiere pro mcp? because i
don't want to rely on the premiere pro stuff, i dont want any reliance on it."*
So Premiere, its MCP bridge, the CEP panel, the npm package and the
`premiere-pro` entry in `~/.claude.json` were all removed, and the docs were
rewritten around the ffmpeg route. The pipeline is now entirely scripts and
files: `preprocess.py` cuts, HyperFrames renders, `burn.py` composites and
encodes to `output/`. Do not propose Premiere, Final Cut, Resolve or any other
timeline app — not as a step, not as a fallback, not as "we could also". If
something genuinely cannot be done headlessly, say so plainly and stop there.
The restore commands are at the bottom of `SETUP.md` if she ever reverses this,
but she has to ask. (Established 2026-09-21.)

**This also made caption position scriptable**, which had been the one thing she
had to eyeball in a GUI — it is `captions_overlay.py --y` now. When a constraint
disappears because a dependency did, say so; she had stopped asking for that
nudge because the answer used to be "you have to do it by hand".

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

- [x] Duplicate "Intro - Silence Pass" sequence — moot; the NLE is gone entirely
      as of 2026-09-21
- [x] Superseded renders accumulate — **done 2026-08-19**: `cleanup.py --renders`
      sweeps loose `graphics/*.mov|mp4` whose composition is committed. Four of
      them were 1.5 GB after one video, and nothing else reached them.
- [ ] Jason's avatar/thumbnail are git-ignored; a fresh clone can't render that card
- [ ] Keep the Firecrawl / Browser Use `cut_proof.mp4` files until both are posted — they are the only caption-free copy of either cut
