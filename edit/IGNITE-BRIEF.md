# Ignite Oct 2026: per-video brief (speaker cards + 6 shorts)

Lana's ask (2026-10-26), after approving how video 04 (Keith Newman × Carmen Li) came out:
*"please do the same shorts clipping (i trust your 6 clip judgements) and also add the speaker
cards [to] the other videos in the ignite summit… repeat the process essentially."*

Each agent handles ONE video, end to end, without asking her anything. Footage is in
`footage/Ignite Oct 2026/`. All of it is 1920×1080 23.976 fps multicam with a baked-in letterbox
(picture rows 34–1046). Confirm that with ffprobe/cropdetect on your file.

`<NN>` = the two-digit number on the file, `<slug>` = the slug you were given (e.g.
`steven-alex`). Use `ignite-<NN>` as the project name everywhere below.

## Read first (only these)
1. `CLAUDE.md`: the spec.
2. `.claude/skills/find-shorts/SKILL.md`: clip selection AND the "If she then says clip them"
   pipeline.
3. In `WORKING-NOTES.md`, the two newest sections only: **"Ignite Oct 2026 speaker cards"** and
   **"Keith × Carmen shorts"**. Search for the headings; don't read the whole file.
4. Reference implementation: `edit/cards-keith-carmen.json`, `edit/shorts-keith-carmen/shortlist.md`,
   `edit/fixes-kc.json`.

## Part A: full interview with speaker cards (landscape)

- Transcribe the whole original first (step 2 of the skill, into `edit/shorts-ignite-<NN>/`).
  You need it for both parts.
- **Names and roles come from the audio, not only the filename.** Filenames have typos
  ("Pheobe Lui" is likely Phoebe Liu of The Information; "Silcom Data" is Silicon Data). Use how
  the host introduces the guest and how the guest describes their role. When a role is a guess,
  keep it short and generic ("Founder, Weka" beats an invented title), and say so in your
  report.
- One card per person, opening only: host first, then guest, each held ~5s. **Time each card to
  the camera shots, not the speech.** Use scene-detect to get the cut list and put each card on
  a shot where that person is the one on screen. The wide shot has the host on the left and the
  guest on the right. Check this per video, because the host is not always the first name in
  the filename. Card `side` follows where the person sits.
- `edit/cards-ignite-<NN>.json` → `python3 edit/speaker_cards.py edit/cards-ignite-<NN>.json --out graphics/ignite-<NN>-cards`
  → render (`-f 24000/1001 --workers 1`, `caffeinate -dimsu`, `< /dev/null`) to `graphics/ignite-<NN>-cards.mov`.
- Composite: a straight re-encode of the untouched interview, with no silence pass, retakes or captions:
  ```bash
  ffmpeg -nostdin -i "footage/Ignite Oct 2026/<file>" -i graphics/ignite-<NN>-cards.mov \
    -filter_complex "[0:v][1:v]overlay=0:0:eof_action=pass:format=auto[v]" -map "[v]" -map 0:a \
    -c:v libx264 -crf 16 -preset medium -pix_fmt yuv420p -c:a copy "output/ignite-<NN>-<slug>.mp4"
  ```
  Then check that its duration equals the source's, and pull 2 frames, one inside each card's
  hold, to confirm each card is over the right person. Small crops are fine.

## Part B: six vertical captioned shorts

- Pick 6 clips of 30–60s using the skill's criteria. She trusts the picks, so no approval
  round. Write `edit/shorts-ignite-<NN>/shortlist.md` in the same format as the reference.
- Then run the skill's clipping pipeline for each: `edit/reframe.py` → `preprocess.py --skip-framing`
  (check head/tail words; drop a leading "So"/"Yeah" with a source-time `remove` in
  `edit/overrides-ignite-<NN>-short<N>.json`) → `captions_overlay.py` with
  `--fixes edit/fixes-ignite-<NN>.json` → `review.py`. **Read every caption text** and fix
  names and jargon. Then render, `check_render.py`, trim the overlay tail to the proof's frame
  count if longer, and `burn.py`.
- Name things `graphics/ignite-<NN>-short<N>-*`, `edit/analysis-ignite-<NN>-short<N>`,
  `project/ignite-<NN>-short<N>.srt`.
- Caption y: measure the white-share of the band as in WORKING-NOTES. 0.65 was right for 04;
  confirm it on your footage.
- The silence pass must remove roughly 8–20%. If it removes much more, the loudness step
  didn't happen. Check the envelope histogram.
- Exports go in `output/ignite-<NN>-shorts/`, named `<N> <short title>.mp4` (N = rank 1–6).
- Spot-check framing with ONE small contact sheet of the six finished shorts (fps=1/8, 144px
  wide, one row per short). Images are expensive, so don't take more than that.

## Lessons from batch 1 (07/09/10)
- **Pick in/out and head/tail `remove` points from the loudness envelope, never from whisper
  word times.** Those drift up to ~1s near joins. First guesses clipped "Imagine a", "It's",
  "hotter" and "on the street". Check that the first and last words survive in the cut
  transcript.
- Whisper re-transcribes on every `preprocess.py` run and the wording moves, so write caption
  fixes against the FINAL pass.
- The last cue can get only 0.1–0.4s, because whisper's last word times run past the clip's
  end. Check the last cue's duration in `review.py --cues`.
- **Keep helper scripts in `edit/shorts-ignite-<NN>/tools/`, not the scratchpad.** The
  scratchpad is shared and agents overwrote each other's scripts.
- `npx hyperframes` may try to self-update mid-run and hit an npm timeout. Just re-run.
- **Caption y: check the contact sheet for small white logos on shirts, not just the
  white-share number.** On 07 the white-share at 0.65 was 0–2%, yet the caption sat right on
  an "AIG" shirt logo, so 07 went to 0.75. Decide y from both.
- Fix keys match ignoring case and punctuation, so `"really,,"` hit every "really". Make keys
  real multi-word sequences.
- The caption tool's orphan-carry overflow (a 32-char cue) is fixed in the shared
  `captions_overlay.py` as of 2026-10-26, so no local patch is needed.

## Lessons from 11
- **Cut-transcript word times are on the CUT timeline.** A `remove` is in the vertical clip's
  own (pre-cut) time, so place it from that clip's audio envelope, not from the cut transcript.
  A tail trim placed from cut times clipped "people".
- Whisper puts quote marks around reported speech, and the grouper then won't break at that
  sentence end. Strip them in the fixes file. Check for 0.1–0.3s single-word cues
  (`review.py --cues`) and merge them with a fix where you can.
- A 25–31% silence removal can be legitimate (a guest who pauses a lot mid-answer), but only if
  loudness is ~-18 LUFS and the histogram shows a clean valley. Report the numbers.
- A guest's first single shot may come much later than the host's (11: 49.6s). Put the card
  there rather than on a 2–4s shot.
- Don't use Monitor for long encode chains: it kills its command at 30 min. Use
  `run_in_background`.

## Lessons from 12
- Steven Hou wears a white "Silicon Data" sweatshirt logo at about y 0.62. On his videos,
  0.65 sits right on it; 12 used **0.70**. Check the contact sheet.
- Whisper adds a leading "And" to almost any clip start, so a leftover "And" may not be a
  clipped word. Probe it with a short isolated whisper run, and drop it with a caption fix.
- If a short drops under 30s after the silence pass, widen the in/out to the next payoff line.
- zsh `for p in "a b"` doesn't split words. Use comma pairs or arrays.

## Lessons from 15
- **On long wide shots, `reframe.py` follows the largest face, which may be the listener.**
  Read `.shots.json` against who is talking. Where it's wrong, pin the crop locally (15 used
  `edit/shorts-ignite-15/tools/reframe5.sh` as the model) and say so in your report.
- The white-share check is fooled by pale clothing. Decide y from the contact sheet. 0.70
  clears Steven's logo.
- An in-point that drops "So" can bite the next word. Probe candidate in-points with a short
  isolated whisper run.

## Lessons from 16
- Decide caption y from the guest's clothing too, not only Steven's. On 16, Bianca's cream top
  pushed captions to **0.78**.
- Full-transcript word times can run about 1s late. Set in/out from envelope gaps plus short
  isolated whisper probes. `edit/shorts-ignite-16/tools/gaps.py` and `probe.sh` do this.
- Isolated probes invent a leading "So"/"And". Check suspect head words against the envelope.

## Shared-machine rules (other agents are running at the same time)
- **One heavy encode at a time, and never run them in parallel within your own job.** The first batch ran the
  full composite and the reframes side by side across three agents on a 10-core / 16 GB Mac.
  Load hit 190, the machine swapped, and a 2-minute reframe took 46+ minutes. Run your steps
  strictly in sequence: full composite → each reframe → each render → each burn. Prefix every
  ffmpeg/reframe/render/burn with `nice -n 10`. Add `-threads 4` to the full composite.
- **Don't edit** `WORKING-NOTES.md`, `CLAUDE.md`, `NEW-VIDEO.md`, the skill, or any shared tool in
  `edit/*.py`. If a tool is genuinely broken, work around it locally and report it.
- **Don't commit** and don't run `cleanup.py`. The main session commits.
- Touch only files with your `ignite-<NN>` prefix. Never delete footage or anything in `output/`
  other than your own files.
- HyperFrames renders can fail under CPU contention ("Attempted to use detached Frame").
  Retry the same command up to 3 times. Always `< /dev/null` on ffmpeg and python in loops.
- Disk had ~46 GB free at the start. If it drops under 10 GB, stop and report.

## Your final report (short, plain text)
1. Card names and roles used, with a confidence note on each role.
2. A table of the six shorts: title, source in→out, final length.
3. Caption fixes that were uncertain (lines worth her listening to, with timestamps).
4. Anything that went wrong or a lesson worth adding to WORKING-NOTES (one line each).

## Replacement round (2026-10-27): no ads
Lana deleted every short that was an advertisement for the guest's business, and asked for
replacements. Read the **"No company pitches"** bullet in `.claude/skills/find-shorts/SKILL.md`
and apply it strictly. Plugs for the hosts (Silicon Data / Compute Exchange) are fine.
- Your video already has its transcript (`edit/shorts-ignite-<NN>/script.txt`), a shortlist and
  a bench. Don't redo Part A or the shorts that survive.
- Pick replacements that are NOT pitches and don't overlap a surviving short. The bench is a
  start, but re-read the script. **Quality beats count**: if the video lacks enough
  non-promotional material, deliver fewer and say so. Never deliver a borderline pitch to fill
  a slot.
- Number new shorts from 7 up (`ignite-<NN>-short7`, …), and name the output files
  `<N> <title>.mp4` with that same N. Use the caption y and fixes file already chosen for your
  video unless the new clip's framing says otherwise.
- Update `shortlist.md`: mark the deleted ones "removed: ad" and add the new ones.
