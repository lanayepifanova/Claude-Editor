#!/usr/bin/env python3
"""reframe.py — cut a range out of a landscape source and reframe it to 9:16,
following whoever is on screen.

Built 2026-10-26 for the Keith Newman x Carmen Li shorts: "follow whoever is on
screen for the single shots of the speaker". The source is a multi-cam edit, so
the crop is held still within a shot and jumps at each camera cut, never pans.

    python3 edit/reframe.py "footage/<clip>.mp4" --start 563.28 --end 620.20 \
        --out graphics/<name>-vertical.mp4

1. Letterbox: the active picture rows are measured, so baked-in bars never
   reach the vertical frame (CLAUDE.md hard no).
2. Shots: mean absolute luma difference between consecutive low-res frames;
   a spike is a camera cut.
3. Subject: several frames per shot go through OpenCV's Haar frontal + profile
   cascades. The largest face wins; that is the single, not the soft
   over-the-shoulder head at the frame edge. A shot with no face inherits the
   previous shot's centre.
4. Encode: one ffmpeg pass. Crop x is a per-frame expression stepping at the
   shot boundaries, then lanczos to 1080x1920 at CRF 12, which is a
   visually-lossless intermediate that preprocess.py / burn.py treat as the
   source.
5. Loudness: audio is normalised to -18 LUFS. A broadcast interview mix sits
   ~10 dB under her own recordings (Keith x Carmen: -30.5 LUFS, speech cluster
   at -37 dB), which puts the locked -35 dB trigger in the MIDDLE of the speech
   and deleted 48% of a clip. Normalising moves the data to the recipe; the
   recipe itself stays exactly as locked.

Writes <out>.shots.json alongside, so the framing can be checked as text.
"""
import argparse, json, subprocess, sys
from pathlib import Path

import cv2
import numpy as np

CASCADES = Path("/opt/homebrew/share/opencv4/haarcascades")
OUT_W, OUT_H = 1080, 1920


def probe(src):
    j = json.loads(subprocess.run(
        ["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries",
         "stream=width,height,r_frame_rate", "-of", "json", src],
        capture_output=True, text=True, check=True).stdout)["streams"][0]
    n, d = j["r_frame_rate"].split("/")
    return j["width"], j["height"], float(n) / float(d)


def frame(src, t, w, h, gray=True, scale=None):
    vf = [f"scale={scale}:-2"] if scale else []
    cmd = ["ffmpeg", "-v", "error", "-ss", f"{t:.3f}", "-i", src, "-frames:v", "1"]
    if vf:
        cmd += ["-vf", ",".join(vf)]
    cmd += ["-f", "rawvideo", "-pix_fmt", "gray" if gray else "bgr24", "-"]
    raw = subprocess.run(cmd, capture_output=True, check=True).stdout
    if scale:
        h = len(raw) // (scale * (1 if gray else 3))
        w = scale
    return np.frombuffer(raw, np.uint8).reshape((h, w) if gray else (h, w, 3))


def letterbox(src, w, h, start, end):
    tops, bots = [], []
    for t in np.linspace(start, end, 6):
        rows = frame(src, t, w, h).max(1)
        act = np.where(rows > 25)[0]
        tops.append(act[0]); bots.append(act[-1])
    top, bot = max(tops), min(bots)
    top += top % 2                       # even rows for yuv420
    hh = (bot - top + 1) // 2 * 2
    return int(top), int(hh)


def shots(src, start, end, fps, thresh):
    """camera cuts, in seconds relative to start"""
    sw = 160
    p = subprocess.run(
        ["ffmpeg", "-v", "error", "-ss", f"{start:.3f}", "-t", f"{end - start:.3f}",
         "-i", src, "-vf", f"scale={sw}:90", "-f", "rawvideo", "-pix_fmt", "gray", "-"],
        capture_output=True, check=True).stdout
    fr = np.frombuffer(p, np.uint8).reshape(-1, 90, sw).astype(np.int16)
    diff = np.abs(np.diff(fr, axis=0)).mean((1, 2))
    cuts = [0.0]
    for i, d in enumerate(diff):
        t = (i + 1) / fps
        if d > thresh and t - cuts[-1] > 0.4:
            cuts.append(t)
    return cuts + [end - start], diff


def subject_x(src, t0, t1, w, h, top, hh, dets):
    xs = []
    for t in np.linspace(t0 + 0.15, max(t0 + 0.15, t1 - 0.15), 5):
        g = frame(src, t, w, h)[top:top + hh]
        faces = []
        for name, img, flip in dets:
            im = cv2.flip(g, 1) if flip else g
            for (x, y, fw, fh) in name.detectMultiScale(im, 1.1, 6, minSize=(90, 90)):
                cx = x + fw / 2
                faces.append((fw * fh, w - cx if flip else cx))
        if faces:
            xs.append(max(faces)[1])
    return float(np.median(xs)) if xs else None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("src")
    ap.add_argument("--start", type=float, required=True)
    ap.add_argument("--end", type=float, required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("--cut-thresh", type=float, default=28.0,
                    help="mean abs luma diff (0-255, 160x90) that counts as a camera cut")
    a = ap.parse_args()

    w, h, fps = probe(a.src)
    top, hh = letterbox(a.src, w, h, a.start, a.end)
    cw = int(round(hh * 9 / 16)) // 2 * 2
    print(f"source {w}x{h} @ {fps:.3f}  active rows {top}-{top + hh}  crop {cw}x{hh}")

    cuts, _ = shots(a.src, a.start, a.end, fps, a.cut_thresh)
    front = cv2.CascadeClassifier(str(CASCADES / "haarcascade_frontalface_default.xml"))
    prof = cv2.CascadeClassifier(str(CASCADES / "haarcascade_profileface.xml"))
    dets = [(front, None, False), (prof, None, False), (prof, None, True)]

    plan, prev = [], w / 2
    for t0, t1 in zip(cuts, cuts[1:]):
        x = subject_x(a.src, a.start + t0, a.start + t1, w, h, top, hh, dets)
        found = x is not None
        cx = x if found else prev
        left = int(min(max(cx - cw / 2, 0), w - cw)) // 2 * 2
        plan.append({"t0": round(t0, 3), "t1": round(t1, 3), "face_x": None if x is None else round(x),
                     "crop_x": left, "found": found})
        prev = cx
        print(f"  shot {t0:7.2f}-{t1:7.2f}s  face_x {'—' if x is None else round(x):>5}  crop_x {left}")

    # crop x as a step function of t (t is relative to the -ss seek)
    expr = str(plan[-1]["crop_x"])
    for s in reversed(plan[:-1]):
        expr = f"if(lt(t,{s['t1']}),{s['crop_x']},{expr})"
    vf = (f"crop={cw}:{hh}:'{expr}':{top},"
          f"scale={OUT_W}:{OUT_H}:flags=lanczos,setsar=1")
    out = Path(a.out); out.parent.mkdir(parents=True, exist_ok=True)
    subprocess.run(
        ["ffmpeg", "-v", "error", "-y", "-ss", f"{a.start:.3f}", "-t", f"{a.end - a.start:.3f}",
         "-i", a.src, "-vf", vf, "-c:v", "libx264", "-crf", "12", "-preset", "slow",
         "-pix_fmt", "yuv420p", "-af", "loudnorm=I=-18:TP=-2:LRA=11,aresample=48000",
         "-c:a", "aac", "-b:a", "320k", str(out)],
        check=True)
    json.dump({"source": a.src, "start": a.start, "end": a.end, "active": [top, hh],
               "crop": [cw, hh], "shots": plan}, open(str(out) + ".shots.json", "w"), indent=1)
    miss = sum(not s["found"] for s in plan)
    print(f"wrote {out}  ({len(plan)} shots, {miss} without a face)")


if __name__ == "__main__":
    sys.exit(main())
