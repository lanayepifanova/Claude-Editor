#!/usr/bin/env python3
"""
preprocess.py — analyse footage ONCE into structured JSON.

Everything downstream (build, verify, the agent) reads these files instead of
re-deriving anything from the video. Nothing here ever enters a conversation.

    python3 edit/preprocess.py footage/clip.MOV --out edit/analysis

Produces:
    envelope.json    RMS @20ms  — the audio, as numbers
    silence.json     the cut list from the locked recipe
    transcript.json  word timings on the CUT timeline
    framing.json     per-sample grid of where the subject is, so graphics can be
                     placed without anyone looking at a frame
"""
import argparse, json, os, subprocess, sys, tempfile
from pathlib import Path

# ── the locked silence recipe (see CLAUDE.md) ─────────────────────────────
HARD, SOFT = -35.0, -37.0
LEAD, TAIL = 0.02, 0.04
MIN_GAP, MIN_SEG, EDGE_BLIP = 0.05, 0.08, 0.15
WINDOW = 0.02

# ── framing grid ──────────────────────────────────────────────────────────
GRID_W, GRID_H = 8, 6          # cells across / down
FRAME_STEP = 0.5               # seconds between samples
SAFE_LUMA = 150               # cell mean above this is probably wall
SAFE_VAR = 900                # cell variance below this is probably flat


def run(cmd, **kw):
    return subprocess.run(cmd, capture_output=True, text=True, **kw)


def sample_rate(src):
    """Read the real rate — assuming 48k silently skews every window."""
    r = run(["ffprobe", "-v", "error", "-select_streams", "a:0",
             "-show_entries", "stream=sample_rate", "-of", "csv=p=0", src])
    try:
        return int(r.stdout.strip().split("\n")[0])
    except Exception:
        return 48000


def envelope(src):
    """Per-20ms RMS in dB, at the file's actual sample rate."""
    sr = sample_rate(src)
    tmp = tempfile.NamedTemporaryFile(suffix=".txt", delete=False).name
    run(["ffmpeg", "-hide_banner", "-v", "error", "-i", src, "-map", "0:a:0",
         "-af", f"asetnsamples=n={int(sr*WINDOW)},astats=metadata=1:reset=1,"
                f"ametadata=print:key=lavfi.astats.Overall.RMS_level:file={tmp}",
         "-f", "null", "-"])
    vals = []
    for line in open(tmp):
        line = line.strip()
        if line.startswith("lavfi.astats.Overall.RMS_level"):
            v = line.split("=")[1]
            vals.append(-90.0 if v in ("-inf", "nan") else round(float(v), 2))
    os.unlink(tmp)
    return vals


def segments(vals, fps):
    """Envelope -> kept segments, using the locked recipe."""
    keep = set()
    for i, v in enumerate(vals):
        if v > HARD:
            keep.add(i)
            j = i - 1
            while j >= 0 and vals[j] > SOFT: keep.add(j); j -= 1
            j = i + 1
            while j < len(vals) and vals[j] > SOFT: keep.add(j); j += 1
    runs, run_ = [], None
    for i in range(len(vals)):
        if i in keep:
            run_ = [i, i] if run_ is None else [run_[0], i]
        elif run_ is not None:
            runs.append(run_); run_ = None
    if run_: runs.append(run_)
    if not runs: return []
    segs = [[max(0.0, a*WINDOW - LEAD), min(len(vals)*WINDOW, (b+1)*WINDOW + TAIL)]
            for a, b in runs]
    merged = [segs[0]]
    for s, e in segs[1:]:
        if s - merged[-1][1] < MIN_GAP: merged[-1][1] = e
        else: merged.append([s, e])
    merged = [x for x in merged if x[1] - x[0] >= MIN_SEG]
    while merged and merged[0][1] - merged[0][0] < EDGE_BLIP: merged.pop(0)
    while merged and merged[-1][1] - merged[-1][0] < EDGE_BLIP: merged.pop()
    return [[round(s*fps)/fps, round(e*fps)/fps] for s, e in merged]


def proof_render(src, segs, out):
    """Concat the kept segments — this IS the cut timeline."""
    v = "".join(f"[0:v]trim={s}:{e},setpts=PTS-STARTPTS,scale=960:-2[v{i}];"
                for i, (s, e) in enumerate(segs))
    a = "".join(f"[0:a:0]atrim={s}:{e},asetpts=PTS-STARTPTS[a{i}];"
                for i, (s, e) in enumerate(segs))
    cc = "".join(f"[v{i}][a{i}]" for i in range(len(segs)))
    cc += f"concat=n={len(segs)}:v=1:a=1[vo][ao]"
    run(["ffmpeg", "-hide_banner", "-v", "error", "-y", "-i", src,
         "-filter_complex", v + a + cc, "-map", "[vo]", "-map", "[ao]",
         "-c:v", "h264_videotoolbox", "-b:v", "4M", "-c:a", "aac", out])


def transcript(proof, model):
    """Word timings against the CUT timeline (never the original)."""
    wav = tempfile.NamedTemporaryFile(suffix=".wav", delete=False).name
    run(["ffmpeg", "-hide_banner", "-v", "error", "-y", "-i", proof,
         "-map", "0:a:0", "-ac", "1", "-ar", "16000", "-c:a", "pcm_s16le", wav])
    stem = tempfile.mktemp()
    r = run(["whisper-cli", "-m", model, "-f", wav, "-oj", "-ml", "1", "-of", stem,
             "--no-prints"])
    jf = stem + ".json"
    if not os.path.exists(jf):
        print(f"  ! whisper failed ({r.stderr.strip()[:80]}) — skipping transcript",
              file=sys.stderr)
        return []
    d = json.load(open(jf))
    raw = [{"w": s["text"], "t0": s["offsets"]["from"]/1000.0,
            "t1": s["offsets"]["to"]/1000.0}
           for s in d["transcription"] if s["text"].strip()]
    toks = []                       # merge subword pieces into whole words
    for x in raw:
        if toks and not x["w"].startswith(" "):
            toks[-1]["w"] += x["w"]; toks[-1]["t1"] = x["t1"]
        else:
            toks.append(dict(x))
    for t in toks:
        t["w"] = t["w"].strip(); t["t0"] = round(t["t0"], 3); t["t1"] = round(t["t1"], 3)
    os.unlink(wav)
    return toks


def framing(proof, duration):
    """
    Sample the cut timeline and record, per cell, whether it's safe to place a
    graphic. 'Safe' = bright and flat, i.e. wall rather than subject.

    This is what removes the need to eyeball frames for placement.
    """
    samples = []
    t = 0.0
    while t < duration:
        raw = tempfile.NamedTemporaryFile(suffix=".rgb", delete=False).name
        run(["ffmpeg", "-hide_banner", "-v", "error", "-y", "-ss", f"{t:.2f}",
             "-i", proof, "-frames:v", "1",
             "-vf", f"scale={GRID_W*8}:{GRID_H*8}", "-pix_fmt", "rgb24",
             "-f", "rawvideo", raw])
        try:
            d = open(raw, "rb").read()
        finally:
            os.unlink(raw)
        W, H = GRID_W*8, GRID_H*8
        if len(d) < W*H*3:
            t += FRAME_STEP; continue
        cells = []
        for gy in range(GRID_H):
            row = []
            for gx in range(GRID_W):
                lum = []
                for py in range(gy*8, gy*8+8):
                    for px in range(gx*8, gx*8+8):
                        o = (py*W + px)*3
                        lum.append(0.299*d[o] + 0.587*d[o+1] + 0.114*d[o+2])
                mean = sum(lum)/len(lum)
                var = sum((x-mean)**2 for x in lum)/len(lum)
                row.append({"m": round(mean), "v": round(var),
                            "safe": bool(mean > SAFE_LUMA and var < SAFE_VAR)})
            cells.append(row)
        samples.append({"t": round(t, 2), "cells": cells})
        t += FRAME_STEP
    return samples


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("media")
    ap.add_argument("--out", default="edit/analysis")
    ap.add_argument("--fps", type=float, default=60.0)
    ap.add_argument("--model", default=str(Path.home()/".cache/whisper/ggml-base.en.bin"))
    ap.add_argument("--skip-framing", action="store_true")
    ap.add_argument("--overrides", default="",
                    help='JSON {"segments":{"0":{"out":4.80}}} — manual trims applied '
                         'after detection, so the proof/transcript stay consistent')
    a = ap.parse_args()

    out = Path(a.out); out.mkdir(parents=True, exist_ok=True)

    print("1/4  envelope …")
    vals = envelope(a.media)
    dur = len(vals) * WINDOW
    json.dump({"window": WINDOW, "unit": "dBFS_RMS", "duration": round(dur, 3),
               "values": vals}, open(out/"envelope.json", "w"))
    print(f"     {len(vals)} windows · {dur:.2f}s")

    print("2/4  silence …")
    segs = segments(vals, a.fps)
    if a.overrides and Path(a.overrides).exists():
        ov = json.load(open(a.overrides)).get("segments", {})
        for k, adj in ov.items():
            i = int(k)
            if i < 0:
                i += len(segs)
            if not (0 <= i < len(segs)):
                print(f"     ! override {k} out of range"); continue
            before = list(segs[i])
            if "in" in adj:  segs[i][0] = round(adj["in"] * a.fps) / a.fps
            if "out" in adj: segs[i][1] = round(adj["out"] * a.fps) / a.fps
            print(f"     override seg {i}: {before[0]:.3f}-{before[1]:.3f} -> "
                  f"{segs[i][0]:.3f}-{segs[i][1]:.3f}")
        drop = sorted((i if i >= 0 else i + len(segs)
                       for i in json.load(open(a.overrides)).get("drop", [])),
                      reverse=True)
        for i in drop:
            if 0 <= i < len(segs):
                print(f"     drop seg {i}: {segs[i][0]:.3f}-{segs[i][1]:.3f} "
                      f"(absorbed by a neighbour)")
                segs.pop(i)
    kept = sum(e-s for s, e in segs)
    json.dump({"recipe": {"hard_db": HARD, "soft_db": SOFT, "lead": LEAD,
                          "tail": TAIL, "min_gap": MIN_GAP, "min_seg": MIN_SEG},
               "source_duration": round(dur, 3), "cut_duration": round(kept, 3),
               "removed_pct": round((dur-kept)/dur*100, 1),
               "segments": segs}, open(out/"silence.json", "w"), indent=1)
    print(f"     {len(segs)} segments · {dur:.1f}s -> {kept:.1f}s "
          f"({(dur-kept)/dur*100:.0f}% removed)")

    proof = str(out/"cut_proof.mp4")
    print("3/4  cut proof + transcript …")
    proof_render(a.media, segs, proof)
    toks = transcript(proof, a.model)
    json.dump({"timeline": "cut", "words": toks}, open(out/"transcript.json", "w"))
    print(f"     {len(toks)} words")

    if a.skip_framing:
        print("4/4  framing … skipped")
    else:
        print("4/4  framing …")
        fr = framing(proof, kept)
        json.dump({"grid": [GRID_W, GRID_H], "step": FRAME_STEP,
                   "safe_luma": SAFE_LUMA, "safe_var": SAFE_VAR,
                   "samples": fr}, open(out/"framing.json", "w"))
        print(f"     {len(fr)} samples on a {GRID_W}x{GRID_H} grid")

    print(f"\n-> {out}/  (nothing here needs to enter a conversation)")


if __name__ == "__main__":
    main()
