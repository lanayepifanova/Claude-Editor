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

# 5. verify the RENDER as text, never through Premiere
python3 edit/check_render.py --render graphics/<name>-cap.mov \
    --srt "project/<name>.srt" --res <WxH>

# 6. assemble in Premiere, then re-read Premiere's real clip boundaries and
#    retime captions onto them (Premiere frame-snaps; the ffmpeg cut does not)
python3 edit/captions_overlay.py ... --timeline edit/analysis-<name>/premiere-clips.json
```

## Invariants

- **Batch instructions, render once.** A render is 1-60 min. If a change arrives
  mid-render, kill it (`pkill -f <output>.mov`) — do not let a stale render finish.
- **Never verify through Premiere.** `export_frame` ignores both `sequenceId` and
  time. Use `check_render.py`, or ffmpeg against the rendered `.mov`.
- **Re-place clips in Premiere after ANY change to the cut.** Changing
  `silence.json` regenerates captions but does not touch Premiere. Forgetting this
  desynced a whole video by 6.7s.
- **Read the transcript before rendering.** `review.py`. Whisper's errors move
  between runs, so pin every wrong variant in `fixes-*.json`, not just the latest.
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
