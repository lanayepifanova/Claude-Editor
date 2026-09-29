# Start here for a new video

A fresh session bootstraps from this file in a few thousand tokens. A session
that has already made a video carries its whole history and costs ~70x more per
turn — so **new video, new session.**

## Read, in order
1. `CLAUDE.md` — the editing spec (locked silence recipe, caption rules, style)
2. `WORKING-NOTES.md` — how Lana works, and the mistakes that cost time
3. `edit/README.md` — the pipeline

Nothing else. Do not read old compositions or transcripts.

## The loop

```bash
# 1. analyse once (envelope, silence, transcript, framing)
#    fps is detected from the media and recorded in silence.json — pass --fps
#    only to override. Everything downstream reads it from there.
python3 edit/preprocess.py "footage/<clip>.mov" --out edit/analysis-<name>

# 1b. drop repeated takes — ALWAYS, she re-reads a line until she gets it right
#     and only the LAST attempt is the keeper. Read the report before --apply;
#     this deletes content, so a false positive loses a real sentence.
python3 edit/retakes.py edit/analysis-<name>                    # report
python3 edit/retakes.py edit/analysis-<name> --apply            # write overrides
python3 edit/preprocess.py "footage/<clip>.mov" --out edit/analysis-<name> \
    --overrides edit/overrides-<name>.json                      # re-cut

# 2. captions -> READ THEM before spending a render
#    Orientation decides --y and line length (CLAUDE.md caption table):
#      vertical  9:16  -> --res 1080x1920 --y 0.25 --maxw 0.72   (~24 chars)
#      landscape 16:9  -> --res 1920x1080 --y 0.82 --size 48 --maxw 0.61  (~42)
#    Check the real frame from the PROOF, not ffprobe on the source.
python3 edit/captions_overlay.py --analysis edit/analysis-<name> \
    --out graphics/<name>-captions --res <WxH> --y <0.25|0.82> --maxw <0.72|0.61> \
    --srt "project/<name>.srt" --fixes edit/fixes-<name>.json
python3 edit/review.py "project/<name>.srt"        # <- approve wording HERE

# 3. structural checks, no render needed
python3 edit/verify.py

# 4. only now render
(cd graphics/<name>-captions && FFMPEG_ENCODE_TIMEOUT_MS=3600000 \
   PRODUCER_ENABLE_CHUNKED_ENCODE=true \
   npx hyperframes render . --format mov -q high -f <fps> -o ../<name>-cap.mov)
#  ^ <fps> = the fps in edit/analysis-<name>/silence.json

# 5. verify the RENDER as text, never with a screenshot
python3 edit/check_render.py --render graphics/<name>-cap.mov \
    --srt "project/<name>.srt" --res <WxH> --y <0.25|0.82>
#  ^ pass the SAME --y the overlay was built with; the band follows it. Without
#    it the check looks in the 9:16 band and reports NO INK on every landscape cue.

# 6. cut, composite and export — no NLE, this IS the assembly step
python3 edit/burn.py --analysis edit/analysis-<name> \
    --overlay graphics/<name>-cap.mov --out "output/<name>.mp4" \
    --master graphics/<name>-master.mp4
#  ^ cuts from footage/ at full res (never from cut_proof.mp4), composites the
#    overlay, and --verify measures the master-vs-final luma difference to prove
#    the ink actually landed. It refuses to overwrite an existing export.

# 7. commit — deletions included — BEFORE any cleanup runs
git add -A && git commit -m "Cut and caption <name>"
```

## Invariants

- **Batch instructions, render once.** A render is 1-60 min. If a change arrives
  mid-render, kill it (`pkill -f <output>.mov`) — do not let a stale render finish.
- **Verify as text, never as screenshots.** `check_render.py` for the overlay,
  `burn.py --verify` for the composite, ffmpeg/ffprobe for anything else. Images
  persist in context and are re-sent on every later turn.
- **Re-run downstream after ANY change to the cut.** Changing `silence.json`
  moves every timing after it, so captions, graphics and the export all have to
  be rebuilt from it — never patch one and leave the others.
- **Read the transcript before rendering.** `review.py`. Whisper's errors move
  between runs, so pin every wrong variant in `fixes-*.json`, not just the latest.
- **Content cuts before captions.** The retake pass moves every timing after it,
  exactly as the silence pass does, so run it before transcribing for captions.
- **`restore_speech.py`'s default `--quiet-db -45` assumes a quiet room.** Measure
  the room-tone PEAK first (`astats` on a gap); if it is already near -40, that
  default restores noise. See WORKING-NOTES.
- **Check the session cost** with `python3 edit/session-cost.py`. Exit code 2 means
  stop and start fresh. A `UserPromptSubmit` hook also injects a `[session-cost]`
  line automatically past 250k/turn — when it appears, finish the step and reset.
- **Reclaim disk with `python3 edit/cleanup.py`**, never a hand-written `rm`. It
  refuses to delete a `cut_proof.mp4` once its source footage is gone, because
  that proof is then the only copy of the cut.

## Handing off mid-project

Everything needed to resume is on disk: `edit/manifest.json`, `edit/analysis-*/`,
`edit/overrides-*.json`, `edit/fixes-*.json`, `project/*.srt`. A new session needs
no conversation history — only this file.
