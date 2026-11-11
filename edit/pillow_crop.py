#!/usr/bin/env python3
"""pillow_crop.py — re-crop Carmen's shots on Ignite 04 so the compute.exchange
pillow she holds is out of frame (R1 review: "Crop any scene where Carmen is
holding a pillow"). Always cuts from the original footage, frame by frame:

    # rebuild one short's vertical + master; timing, segments and audio unchanged
    python3 edit/pillow_crop.py short kc-short3
    # REVERSED 2026-11-05 — she overruled the reviewer: "do not crop any scene where
    # carmen is holding a pillow. it looks off" and "do not zoom up for any of the
    # clips". --restore puts back reframe.py's original framing:
    python3 edit/pillow_crop.py short kc-short3 --restore
    # re-export the long form (cards + logo composited on the cropped picture)
    python3 edit/pillow_crop.py long --cards graphics/keith-carmen-cards.mov \\
        --logo graphics/brand/silicon-data-white-1080p.png --out "<file>.mp4"

Per-shot rectangles live in edit/crops-keith-carmen.json (`keith` shots are never
touched). ffmpeg's crop cannot change size per frame, and split+trim branches
buffer the whole interview, so frames go through numpy on raw yuv420p planes.

Landscape: each rectangle fills the 1920x1012 picture and the baked letterbox stays.
Vertical: the crop is at most ~375px wide, about one head, so a fixed crop would
clip her when she leans. It re-centres only at a silence-cut jump, where the picture
already jumps, and only when the head has drifted > HOLD px. It never pans.
"""
import argparse, json, os, subprocess, sys
from pathlib import Path

import cv2
import numpy as np

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO/"edit"))
import burn

CFG = json.load(open(REPO/"edit"/"crops-keith-carmen.json"))
FPS = 24000 / 1001
COLOR = ["-colorspace", "bt709", "-color_primaries", "bt709", "-color_trc", "bt709", "-color_range", "tv"]
HOLD = 30           # source px of head drift before re-centring at a jump
BIAS = 10           # Haar centres on the nose; hair sits to the right of it
# 9:16 can't hold the two-shot, and these rows keep her head clear of the pillow
VERT_WIDE = {2: (300, 628), 5: (300, 630), 10: (300, 628), 14: (297, 627), 22: (305, 635),
             30: (335, 655), 44: (340, 660)}
CASC = "/opt/homebrew/share/opencv4/haarcascades/"


def reader(start=None, dur=None, W=1920, H=1080):
    cmd = ["ffmpeg", "-v", "error"]
    if start is not None:
        cmd += ["-ss", f"{start:.3f}", "-t", f"{dur:.3f}"]
    cmd += ["-i", str(REPO/CFG["source"]), "-fps_mode", "vfr",
            "-f", "rawvideo", "-pix_fmt", "yuv420p", "-"]
    p = subprocess.Popen(cmd, stdout=subprocess.PIPE, stdin=subprocess.DEVNULL, bufsize=1 << 24)
    size = W * H * 3 // 2
    while True:
        b = p.stdout.read(size)
        if len(b) < size:
            break
        yield np.frombuffer(b, np.uint8)
    p.wait()


def planes(fr, W=1920, H=1080):
    y = fr[:W*H].reshape(H, W)
    u = fr[W*H:W*H + W*H//4].reshape(H//2, W//2)
    v = fr[W*H + W*H//4:].reshape(H//2, W//2)
    return y, u, v


def crop_to(p, x, y, w, h, ow, oh):
    Y, U, V = p
    fx = cv2.INTER_LANCZOS4
    yy = cv2.resize(Y[y:y+h, x:x+w], (ow, oh), interpolation=fx)
    uu = cv2.resize(U[y//2:(y+h)//2, x//2:(x+w)//2], (ow//2, oh//2), interpolation=fx)
    vv = cv2.resize(V[y//2:(y+h)//2, x//2:(x+w)//2], (ow//2, oh//2), interpolation=fx)
    return yy, uu, vv


def shot_at(t):
    for s in CFG["shots"]:
        if s["t0"] <= t < s["t1"]:
            return s
    return CFG["shots"][-1]


def face(g, dets):
    fs = []
    for det, flip in dets:
        gg = cv2.flip(g, 1) if flip else g
        for (x, y, w, h) in det.detectMultiScale(gg, 1.1, 5, minSize=(60, 60)):
            fs.append((w, (g.shape[1] - x - w/2) if flip else x + w/2))
    return max(fs)[1] if fs else None


def lowres(path):
    raw = subprocess.run(["ffmpeg", "-v", "error", "-i", str(path), "-fps_mode", "vfr", "-vf", "scale=64:36",
                          "-f", "rawvideo", "-pix_fmt", "gray", "-"],
                         capture_output=True, stdin=subprocess.DEVNULL, check=True).stdout
    return np.frombuffer(raw, np.uint8).reshape(-1, 36, 64).astype(np.int16)


def frame_map(name, vert, master, segs, fps):
    """Which vertical frame each shipped master frame came from. Masters built
    before burn.py's whole-frame trim differ from today's formula by a frame here
    and there, so the cut is read off the master itself (Viterbi over offsets,
    each frame's match scored against the vertical) and saved: replaying this map
    reproduces the shipped cut exactly, and it stays valid after the master is
    replaced."""
    path = REPO/"edit"/f"analysis-{name}"/"frame_map.json"
    if path.exists():
        return json.load(open(path))["map"]
    v, m = lowres(vert), lowres(master)
    expect = [f for a, b in segs for f in range(round(a * fps), round(b * fps))]
    expect += [expect[-1] + 1 + i for i in range(max(0, len(m) - len(expect)))]
    R, PEN = 4, 3.0
    offs = list(range(-R, R + 1))
    cost = np.zeros(len(offs)); back = []
    for i in range(len(m)):
        sad = np.array([np.abs(m[i] - v[min(max(expect[i] + d, 0), len(v) - 1)]).mean() for d in offs])
        trans = cost[None, :] + PEN * (np.arange(len(offs))[None, :] != np.arange(len(offs))[:, None])
        back.append(trans.argmin(1))
        cost = trans.min(1) + sad
    k = int(cost.argmin()); path_o = []
    for i in range(len(m) - 1, -1, -1):
        path_o.append(k)
        k = int(back[i][k])
    path_o.reverse()
    fm = [min(max(expect[i] + offs[path_o[i]], 0), len(v) - 1) for i in range(len(m))]
    if any(b <= a for a, b in zip(fm, fm[1:])):
        sys.exit(f"{name}: frame map is not monotonic")
    score = float(np.mean([np.abs(m[i] - v[fm[i]]).mean() for i in range(len(m))]))
    json.dump({"map": fm, "mean_sad": round(score, 3)}, open(path, "w"))
    print(f"{name}: frame map {len(fm)} frames, mean SAD {score:.2f}, "
          f"{sum(e != f for e, f in zip(expect, fm))} differ from the segment formula")
    return fm


def short(name, restore=False):
    an = json.load(open(REPO/"edit"/f"analysis-{name}"/"silence.json"))
    vert = REPO/"graphics"/f"{name}-vertical.mp4"
    meta = json.load(open(str(vert) + ".shots.json"))
    start, end = meta["start"], meta["end"]
    segs = an["segments"]; fps = an["fps"]
    master = REPO/"graphics"/f"{name}-master.mp4"
    fm = frame_map(name, vert, master, segs, fps)
    runs, r0 = [], fm[0]
    for p, q in zip(fm, fm[1:]):
        if q != p + 1:
            runs.append((r0, p + 1)); r0 = q
    runs.append((r0, fm[-1] + 1))
    if restore:
        # her call 2026-11-05: no pillow crop, no zoom. Replay reframe.py's own
        # crop (orig_crop_x, full letterbox height) frame for frame.
        top, hh = meta["active"]; cw = meta["crop"][0]
        class Orig:
            def __getitem__(self, f):
                t = f / FPS
                o = next((o for o in meta["shots"] if t < o["t1"]), meta["shots"][-1])
                return (o.get("orig_crop_x", o["crop_x"]), top, cw, hh)
        fplan, report = Orig(), None
    else:
        # first pass: frames, camera cuts, head tracks
        dets = [(cv2.CascadeClassifier(CASC + "haarcascade_frontalface_default.xml"), False),
                (cv2.CascadeClassifier(CASC + "haarcascade_profileface.xml"), False),
                (cv2.CascadeClassifier(CASC + "haarcascade_profileface.xml"), True)]
        prev, cuts, n, track = None, [0], 0, {}
        for fr in reader(start, end - start):
            g = planes(fr)[0]
            small = g[34:1046:12, ::12].astype(np.int16)
            if prev is not None and np.abs(small - prev).mean() > 25:
                cuts.append(n)
            prev = small
            if n % 6 == 0:
                s = shot_at(start + n / FPS)
                if s["kind"] in ("cu", "wide", "two"):
                    x0 = 500 if s["kind"] == "cu" else 900
                    c = face(g[34:700, x0:1500], dets)
                    if c is not None:
                        track[n] = c + x0
            n += 1
        cuts.append(n)
        # second: a crop per frame
        fplan = [None] * n
        report = []
        for a, b in zip(cuts, cuts[1:]):
            s = shot_at(start + (a + b) / 2 / FPS)
            if s["kind"] == "keith":
                old = next(o for o in meta["shots"] if o["t0"] <= (a + b) / 2 / FPS < o["t1"])
                for f in range(a, b):
                    fplan[f] = (old.get("orig_crop_x", old["crop_x"]), 34, 568, 1012)
                report.append((s["i"], "keith", a, b, 0, None))
                continue
            if s["kind"] == "cu":
                y, h = s["y"], s["h"]
            else:
                y, y1 = VERT_WIDE[s["i"]]; y, h = y // 2 * 2, (y1 - y) // 2 * 2
            w = int(round(h * 9 / 16)) // 2 * 2
            spans = [(max(a, x), min(b, z)) for x, z in runs]
            spans = [(p, q) for p, q in spans if p < q] or [(a, b)]
            cur, moves, worst = None, 0, 0
            last_end = a
            for i, (p, q) in enumerate(spans):
                xs = [v for f, v in track.items() if p <= f < q]
                nxt = spans[i+1][0] if i + 1 < len(spans) else b
                m = float(np.median(xs)) if xs else cur
                if m is not None and (cur is None or abs(m - cur) > HOLD):
                    moves += cur is not None
                    cur = m
                if xs:
                    worst = max(worst, max(abs(v - cur) for v in xs))
                c = cur if cur is not None else s.get("cx", 900)
                left = int(min(max(c + BIAS - w / 2, 0), 1920 - w)) // 2 * 2
                for f in range(last_end, max(nxt, q) if i + 1 == len(spans) else nxt):
                    fplan[f] = (left, y, w, h)
                last_end = nxt
            for f in range(a, b):
                if fplan[f] is None:
                    fplan[f] = (left, y, w, h)
            report.append((s["i"], s["kind"], a, b, moves, round(worst), w, h, left))
    # third: encode, audio copied unchanged from the current vertical
    tmp = str(vert).replace(".mp4", ".new.mp4")
    enc = subprocess.Popen(
        ["nice", "-n", "10", "ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "yuv420p", "-s", "1080x1920",
         "-r", "24000/1001", *COLOR, "-i", "-", "-i", str(vert), "-map", "0:v", "-map", "1:a", "-c:a", "copy",
         "-c:v", "libx264", "-crf", "12", "-preset", "slow", "-pix_fmt", "yuv420p", *COLOR, tmp],
        stdin=subprocess.PIPE)
    for f, fr in enumerate(reader(start, end - start)):
        x, y, w, h = fplan[f]
        for pl in crop_to(planes(fr), x, y, w, h, 1080, 1920):
            enc.stdin.write(pl.tobytes())
    enc.stdin.close(); enc.wait()
    if enc.returncode:
        sys.exit("encode failed")
    old_v = int(burn.probe(str(vert))["nb_read_packets"]); new_v = int(burn.probe(tmp)["nb_read_packets"])
    if old_v != new_v:
        sys.exit(f"{name}: vertical frames {new_v} != {old_v}, kept {tmp}")
    # master: replay the shipped cut frame for frame, audio stream copied untouched
    tmpm = str(master).replace(".mp4", ".new.mp4")
    enc = subprocess.Popen(
        ["nice", "-n", "10", "ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "yuv420p", "-s", "1080x1920",
         "-r", "24000/1001", *COLOR, "-i", "-", "-i", str(master), "-map", "0:v", "-map", "1:a", "-c:a", "copy",
         "-c:v", "libx264", "-preset", "slow", "-crf", "16", "-pix_fmt", "yuv420p", *COLOR,
         "-movflags", "+faststart", tmpm], stdin=subprocess.PIPE)
    dec = subprocess.Popen(["ffmpeg", "-v", "error", "-i", tmp, "-fps_mode", "vfr", "-f", "rawvideo",
                            "-pix_fmt", "yuv420p", "-"], stdout=subprocess.PIPE, stdin=subprocess.DEVNULL,
                           bufsize=1 << 24)
    size = 1080 * 1920 * 3 // 2
    want, f = 0, 0
    while want < len(fm):
        b = dec.stdout.read(size)
        if len(b) < size:
            sys.exit(f"{name}: vertical ended at {f}, map wants {fm[want]}")
        if f == fm[want]:
            enc.stdin.write(b)
            want += 1
        f += 1
    dec.stdout.close(); dec.terminate(); enc.stdin.close(); enc.wait()
    om, nm = int(burn.probe(str(master))["nb_read_packets"]), int(burn.probe(tmpm)["nb_read_packets"])
    if enc.returncode or om != nm:
        sys.exit(f"{name}: master frames {nm} != {om}, kept {tmpm}")
    for o in meta["shots"]:
        o.setdefault("orig_crop_x", o["crop_x"])
    if restore:
        meta.pop("pillow_crop", None)
    else:
        meta["pillow_crop"] = [list(r) for r in report]
    json.dump(meta, open(str(vert) + ".shots.json", "w"), indent=1)
    os.replace(tmp, vert)
    os.replace(tmpm, master)
    twin = REPO/"graphics"/f"{name}-brand-master.mp4"
    if twin.exists():                  # byte-identical duplicate; keep it from going stale
        twin_tmp = str(twin).replace(".mp4", ".new.mp4")
        subprocess.run(["cp", str(master), twin_tmp], check=True)
        os.replace(twin_tmp, twin)
    print(name, nm, "frames; shots (id kind f0 f1 moves worst_drift w h x):", report)


def long_form(cards, logo, out):
    frames = 0
    enc = subprocess.Popen(
        ["nice", "-n", "10", "ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "yuv420p", "-s", "1920x1080",
         "-r", "24000/1001", *COLOR, "-i", "-", "-i", str(REPO/CFG["source"]), "-i", cards, "-i", logo,
         "-filter_complex", "[0:v][2:v]overlay=0:0:format=auto:eof_action=pass[a];[a][3:v]overlay=52:62:format=auto[v]",
         "-map", "[v]", "-map", "1:a", "-c:a", "copy", "-c:v", "libx264", "-preset", "slow", "-crf", "16",
         "-pix_fmt", "yuv420p", *COLOR, "-movflags", "+faststart", out], stdin=subprocess.PIPE)
    bounds = [(s["f0"], s["f1"], s) for s in CFG["shots"]]
    bi = 0
    for fr in reader():
        while frames >= bounds[bi][1]:
            bi += 1
        s = bounds[bi][2]
        if s["kind"] == "keith":
            enc.stdin.write(fr.tobytes())
        else:
            Y, U, V = planes(fr)
            Y, U, V = Y.copy(), U.copy(), V.copy()
            yy, uu, vv = crop_to((Y, U, V), s["x"], s["y"], s["w"], s["h"], 1920, 1012)
            Y[34:1046] = yy; U[17:523] = uu; V[17:523] = vv
            for pl in (Y, U, V):
                enc.stdin.write(pl.tobytes())
        frames += 1
    enc.stdin.close(); enc.wait()
    if enc.returncode:
        sys.exit("encode failed")
    print("frames", frames)


def main():
    ap = argparse.ArgumentParser()
    sub = ap.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("short"); p.add_argument("name")
    p.add_argument("--restore", action="store_true", help="undo the pillow crop: original reframe framing")
    p = sub.add_parser("long"); p.add_argument("--cards", required=True)
    p.add_argument("--logo", required=True); p.add_argument("--out", required=True)
    a = ap.parse_args()
    if a.cmd == "short":
        short(a.name, a.restore)
    else:
        long_form(a.cards, a.logo, a.out)


if __name__ == "__main__":
    main()
