#!/usr/bin/env python3
"""
silence-cut.py — Lana's locked silence-removal recipe.

Approved on "Intro to Claude Editor" (2026-08-15). These defaults ARE the
house style: cut right after the word, slice between words, jump cuts welcome.
Don't soften them without being asked.

Usage:
    python3 tools/silence-cut.py footage/clip.MOV [--item-id 000f4241] [--fps 60]
    python3 tools/silence-cut.py footage/clip.MOV --proof     # also render an ffmpeg proof

Emits:
  - a human-readable segment table
  - clips.json  -> paste straight into add_to_timeline_batch
"""
import argparse, json, os, subprocess, sys, tempfile

# ---- THE LOCKED RECIPE -------------------------------------------------
HARD      = -35.0   # speech threshold (dB RMS)
SOFT      = -37.0   # hysteresis floor: extend through consonant tails
LEAD      = 0.02    # padding before speech (s)
TAIL      = 0.04    # padding after speech (s) -- "right after the word"
MIN_GAP   = 0.05    # cut any gap >= this (s) -- slices between words
MIN_SEG   = 0.08    # discard kept segments shorter than this (s)
WINDOW    = 0.02    # envelope resolution (s)
EDGE_BLIP = 0.15    # drop head/tail segments shorter than this
# ------------------------------------------------------------------------


def envelope(path, sr=48000):
    """Per-window RMS in dB via ffmpeg astats."""
    n = int(sr * WINDOW)
    tmp = tempfile.NamedTemporaryFile(suffix=".txt", delete=False).name
    subprocess.run([
        "ffmpeg", "-hide_banner", "-v", "error", "-i", path, "-map", "0:a:0",
        "-af", f"asetnsamples=n={n},astats=metadata=1:reset=1,"
               f"ametadata=print:key=lavfi.astats.Overall.RMS_level:file={tmp}",
        "-f", "null", "-"], check=True)
    vals = []
    for line in open(tmp):
        line = line.strip()
        if line.startswith("lavfi.astats.Overall.RMS_level"):
            v = line.split("=")[1]
            vals.append(-90.0 if v in ("-inf", "nan") else float(v))
    os.unlink(tmp)
    return vals


def histogram(vals):
    """Sanity check: speech and room tone should form two clusters."""
    print("\nRMS histogram (confirm two clusters with a valley near the threshold):")
    for b in range(-90, 0, 5):
        n = sum(1 for v in vals if b <= v < b + 5)
        if n:
            mark = "  <- threshold" if b <= HARD < b + 5 else ""
            print(f"  {b:4d}..{b+5:4d} {'#' * min(n, 50):<50} {n}{mark}")


def segments(vals, fps):
    keep = set()
    for i, v in enumerate(vals):
        if v > HARD:
            keep.add(i)
            j = i - 1
            while j >= 0 and vals[j] > SOFT:
                keep.add(j); j -= 1
            j = i + 1
            while j < len(vals) and vals[j] > SOFT:
                keep.add(j); j += 1

    runs, run = [], None
    for i in range(len(vals)):
        if i in keep:
            run = [i, i] if run is None else [run[0], i]
        elif run is not None:
            runs.append(run); run = None
    if run:
        runs.append(run)
    if not runs:
        return []

    segs = [[max(0.0, a * WINDOW - LEAD),
             min(len(vals) * WINDOW, (b + 1) * WINDOW + TAIL)] for a, b in runs]

    merged = [segs[0]]
    for s, e in segs[1:]:
        if s - merged[-1][1] < MIN_GAP:
            merged[-1][1] = e
        else:
            merged.append([s, e])

    merged = [x for x in merged if x[1] - x[0] >= MIN_SEG]
    # strip stray blips at head/tail (bumps, not speech)
    while merged and merged[0][1] - merged[0][0] < EDGE_BLIP:
        merged.pop(0)
    while merged and merged[-1][1] - merged[-1][0] < EDGE_BLIP:
        merged.pop()

    return [(round(s * fps) / fps, round(e * fps) / fps) for s, e in merged]


def proof(src, segs, out):
    v = "".join(f"[0:v]trim={s}:{e},setpts=PTS-STARTPTS,scale=1280:-2[v{i}];"
                for i, (s, e) in enumerate(segs))
    a = "".join(f"[0:a:0]atrim={s}:{e},asetpts=PTS-STARTPTS[a{i}];"
                for i, (s, e) in enumerate(segs))
    cc = "".join(f"[v{i}][a{i}]" for i in range(len(segs)))
    cc += f"concat=n={len(segs)}:v=1:a=1[vo][ao]"
    subprocess.run(["ffmpeg", "-hide_banner", "-v", "error", "-y", "-i", src,
                    "-filter_complex", v + a + cc, "-map", "[vo]", "-map", "[ao]",
                    "-c:v", "h264_videotoolbox", "-b:v", "6M",
                    "-c:a", "aac", "-b:a", "192k", out], check=True)
    print(f"\nproof rendered -> {out}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("media")
    ap.add_argument("--item-id", default="PROJECT_ITEM_ID")
    ap.add_argument("--fps", type=float, default=60.0)
    ap.add_argument("--track", type=int, default=0)
    ap.add_argument("--proof", action="store_true")
    ap.add_argument("--out", default="clips.json")
    args = ap.parse_args()

    vals = envelope(args.media)
    dur = len(vals) * WINDOW
    histogram(vals)

    segs = segments(vals, args.fps)
    if not segs:
        sys.exit("No speech found — check the threshold against the histogram above.")

    print(f"\n{'#':>3} {'src in':>9} {'src out':>9} {'dur':>7} {'gap cut':>8} {'tl pos':>8}")
    clips, t, prev = [], 0.0, 0.0
    for i, (s, e) in enumerate(segs, 1):
        print(f"{i:>3} {s:9.3f} {e:9.3f} {e-s:7.3f} {s-prev:8.3f} {t:8.3f}")
        clips.append({"projectItemId": args.item_id, "trackIndex": args.track,
                      "time": round(t, 6), "sourceInPoint": round(s, 6),
                      "sourceOutPoint": round(e, 6)})
        prev = e
        t += e - s

    print(f"\nsegments: {len(segs)}")
    print(f"kept:     {t:.2f}s of {dur:.2f}s  ({t/dur*100:.0f}%)")
    print(f"removed:  {dur-t:.2f}s  ({(dur-t)/dur*100:.0f}%)")

    json.dump(clips, open(args.out, "w"), indent=1)
    print(f"\nwrote {args.out} -> paste into add_to_timeline_batch")

    if args.proof:
        proof(args.media, segs, "PROOF.mp4")


if __name__ == "__main__":
    main()
