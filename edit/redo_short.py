#!/usr/bin/env python3
"""redo_short.py -- rebuild ONE shipped Ignite short from the original footage with the
2026-11-09 fixes, into fresh names, never touching output/Short Form/.

    nice -n 10 python3 edit/redo_short.py kc-short1
    nice -n 10 python3 edit/redo_short.py ignite-07-short1 --suffix r3 --out-dir output/Review
    python3 edit/redo_short.py ignite-07-short1 --plan          # text only, no encode

Chain (the recipe reverse-engineered from kc-short3's redo):
  0. plan     source / start / end from graphics/<stem>-vertical.mp4.shots.json, tail
              extension measured on the source audio (voice decay ~-50 dB, stopping at
              the next onset or the next camera cut), speaker pins carried over
  1. reframe  frame-exact camera cuts (vfr), crop stepped on the frame number, audit
  2. preprocess  --skip-framing --overrides (old overrides, with end handling replaced);
              word times mapped from the UNCUT source transcript
  3. captions captions_overlay.py (y/size/maxw read from the shipped captions dir,
              fixes-<video>.json) -> brand_overlay.py (highlights + logo)
  4. master   burn.py master-only (cut from footage at full res)
  5. title    shorts_title_cards.build_one(c=<stem>-<suffix>): card + captions at y 0.775,
              composited, checked, written to --out-dir as "<name>.mp4"
  6. audit    text only: reframe spikes, caption cue durations, word time vs envelope,
              end-tail level, shipped-vs-new segment agreement

Everything new is named <stem>-<suffix> (default r3): graphics/<stem>-r3-*,
edit/analysis-<stem>-r3, edit/overrides-<stem>-r3.json, project/<stem>-r3.srt.
The shipped analysis, graphics and exports are only ever READ.

Manual speaker pins: shots the shipped vertical pinned by hand (a `"pinned": true` entry
in .shots.json, or PINS below) are re-applied to whichever new shot contains the pinned
shot's midpoint. Anything else that differs from the shipped crop_x by >60px is listed
as a WARN in the audit so a wrong-speaker crop is seen as text before it is seen on screen.
"""
import argparse, json, os, re, subprocess, sys, time
from pathlib import Path

import numpy as np

REPO = Path(__file__).resolve().parent.parent
os.chdir(REPO)
sys.path.insert(0, str(REPO / "edit"))
os.environ.setdefault("TC_SCRATCH", "/private/tmp/claude-501/redo_scratch")
Path(os.environ["TC_SCRATCH"]).mkdir(parents=True, exist_ok=True)

import preprocess as pp          # envelope(), WINDOW
import reframe as rf             # shots(), subject_x(), letterbox(), audit(), probe()
import shorts_title_cards as stc

FPS_STR = "24000/1001"
# pins made by hand-written scripts that never wrote `pinned` into .shots.json.
# (start_rel, end_rel, crop_x) in the shipped vertical's own time. Source: the tools dir.
PINS = {
    # edit/shorts-ignite-15/tools/reframe5.sh: wide shot follows Steven (listener); pin Angela
    "ignite-15-short5": [(0.0, 45.3, 1046)],
    # Carmen sits left of centre in the wide two-shot: auto crop (x 58) put her at the crop's edge.
    # Face centre x~510 -> crop 568 wide starts at 226 so she is centred (her gesturing hands stay in).
    # Bianca in the wide two-shot: the face detector latched onto the shelf/pillow behind her (x 1486, crop 1200);
    # her face is at x~1330, so a 568-wide crop centred on her starts at 1046.
    # Phoebe (left, blue sweater) speaks the last shot; face detection found nobody there, so the crop held the
    # previous x and framed the gap between the two women. Her face is at x~580 -> 568-wide crop starts at 296.
    "ignite-09-short5": [(52.2, 54.5, 296)],
    # Steve in the wide two-shot: the detector took the pillow behind him (x 1502) for his face, so the crop
    # (1218) showed only his shoulder at its edge. His face is at x~1200 -> crop 568 wide starts at 916.
    "ignite-10-short5": [(10.9, 14.2, 916)],
    # Angela in the wide two-shot (24-56s): the detector took the pillow behind her (x 1525) for her face, so she sat
    # in the left third of the crop. Her face is at x~1350 -> a 568-wide crop starts at 1066.
    "ignite-15-short3": [(24.0, 55.8, 1066)],
    # "This is the largest chip in the world": keep the CHIP in frame while it is introduced, not Steve.
    # 0-3.8 wide: chip on the table + Angela handing it over (x 900); 3.8-7.5 close-up: the chip held at the left
    # of the source frame (x 0, the furthest left a crop can go); 7.5-11.2 Steve holding it (x 700, face + tablet inside);
    # 11.3-15.5 Angela talking again, wide: her face is at x~1350 (the detector took the pillow), crop 1066.
    "ignite-15-short1": [(0.0, 3.8, 900), (3.8, 7.5, 0), (7.5, 11.2, 700), (11.3, 15.5, 1066)],
    "ignite-16-short5": [(32.5, 34.9, 1046)],
    "ignite-07-short2": [(52.0, 55.6, 226), (62.0, 66.1, 226)],
}
# a short the shipped set has that is missing from BREAKS (pilot, built before the table)
EXTRA_BREAKS = {"No way to short compute": ("No way to", "short compute")}
stc.BREAKS.update(EXTRA_BREAKS)

T0 = time.time()


def log(s):
    print(f"[{time.time() - T0:6.0f}s] {s}", flush=True)


def run(cmd, **kw):
    log("$ " + " ".join(str(c) for c in cmd)[:230])
    p = subprocess.run([str(c) for c in cmd], stdin=subprocess.DEVNULL, capture_output=True, text=True, **kw)
    if p.returncode:
        sys.exit(f"FAILED: {' '.join(map(str, cmd))[:200]}\n{(p.stderr or p.stdout)[-1800:]}")
    return p.stdout + p.stderr


# ---------------------------------------------------------------- 0. plan
def shipped_name(stem):
    """'[CP] Ignite 04 - 3 neoclouds to 300' for a stem, via the title-card lines of the shipped build."""
    html = (REPO / "graphics" / f"{stem}-title-card" / "index.html").read_text()
    lines = [__import__("html").unescape(l) for l in re.findall(r'<div class="line">(.*?)</div>', html)]
    key = " ".join(lines)
    for pil in sorted(stc.SHORT.iterdir()):
        for f in pil.glob("*.mp4"):
            m = re.match(r"\[(\w+)\] Ignite (\d+) - (.*)$", f.stem)
            if m and " ".join(stc.BREAKS.get(m.group(3), ())) == key:
                return f.stem
    sys.exit(f"{stem}: no shipped short matches title lines {lines}")


def caption_params(stem):
    h = (REPO / "graphics" / f"{stem}-captions" / "index.html").read_text()
    y = float(re.search(r"\.cue \{\s*position:absolute; left:0; right:0; top:([\d.]+)%", h).group(1)) / 100
    size = int(re.search(r"font-size:(\d+)px", h).group(1))
    mw = int(re.search(r"max-width:(\d+)px", h).group(1))
    return y, size, round(mw / 1080, 2)


def fixes_file(stem):
    if stem.startswith("kc-"):
        return "edit/fixes-kc.json"
    return f"edit/fixes-{'-'.join(stem.split('-')[:2])}.json"


def scan_tail(env, e0, fps, cut_t=None, cap=1.0):
    """Scan an envelope (20 ms windows, clip-relative) forward from the shipped cut point e0.
    Returns (end, why, limit): end = where the voice has decayed (< -50 dB x3 windows), the valley
    before a new onset (> -35 after a dip below -42), or just before a camera cut at cut_t; limit =
    the latest point the clip may run to without taking in the next onset/cut. If speech is still
    running at the cap, end == e0 (no extension)."""
    W = pp.WINDOW
    i0 = int(round(e0 / W))
    hi = min(i0 + int(cap / W), len(env) - 3)
    dipped = env[min(i0, len(env) - 1)] < -42
    end, why = None, "speech still running at the cap, not extended"
    limit = None
    for i in range(i0 + 1, hi):
        t = i * W
        if cut_t is not None and t >= cut_t - 2 / fps:
            end, why = (end if end is not None else cut_t - 2 / fps), (why if end is not None else "camera cut")
            limit = cut_t - 2 / fps
            break
        if env[i] < -42:
            dipped = True
        if env[i] > -35 and dipped:
            j = i - 1
            while j > i0 and env[j - 1] <= env[j]:
                j -= 1               # walk back down the rise to the valley floor
            if end is None:
                end, why = (j + 1) * W, "next onset"
            limit = (j + 1) * W
            break
        if end is None and env[i] < -50 and env[i + 1] < -50 and env[i + 2] < -50:
            end, why = (i + 2) * W, "decayed to -50 dB"   # +2 windows: land inside the quiet, not on its edge
        if end is not None and t > end + 0.3:
            break
    if end is None:
        return e0, why, e0
    if limit is None:
        limit = end + 0.3
    return max(e0, end), why, max(limit, end)


def tail_extension(src, start, e0_rel, end_ship_rel, fps):
    """First estimate on the SOURCE audio (loudnorm'd like the vertical) so the vertical is cut long
    enough to hold the decay. The final out point is re-measured on the real vertical afterwards."""
    wav = Path(os.environ["TC_SCRATCH"]) / "tail.wav"
    t = end_ship_rel + 2.0
    run(["ffmpeg", "-y", "-v", "error", "-ss", f"{start:.3f}", "-t", f"{t:.3f}", "-i", src, "-vn",
         "-af", "loudnorm=I=-18:TP=-2:LRA=11,aresample=48000", "-ac", "1", str(wav)])
    env = pp.envelope(str(wav))
    cut_t = None
    cuts, _, _ = rf.shots(src, start, start + t, fps, 28.0)
    for f in cuts[1:-1]:
        if f / fps > e0_rel + 0.02:
            cut_t = f / fps
            break
    end, why, limit = scan_tail(env, e0_rel, fps, cut_t)
    return end, why, limit, cut_t


def plan(stem, suffix, end_source=None, start_source=None, exact_end=False):
    shots = json.load(open(REPO / "graphics" / f"{stem}-vertical.mp4.shots.json"))
    sil = json.load(open(REPO / "edit" / f"analysis-{stem}" / "silence.json"))
    ovp = REPO / "edit" / f"overrides-{stem}.json"
    ov = json.load(open(ovp)) if ovp.exists() else {}
    src, start, end = shots["source"], shots["start"], shots["end"]
    fps = sil["fps"]
    e0 = sil["segments"][-1][1]
    if start_source:
        # the clip's OPENING is being re-chosen (the shipped one began mid-sentence). All clip-relative numbers
        # (cut point, old `remove` spans) move by the difference; head trims (spans starting at 0) are dropped,
        # they only existed to hide the old, mid-sentence start.
        shift = start - start_source
        ov["remove"] = [[r[0] + shift, r[1] + shift] for r in ov.get("remove", []) if r[0] > 0.01]
        e0 += shift
        start = start_source
    if end_source:
        # the clip's ending is being re-chosen (review note: "cut off"): the last spoken word now
        # ends at source time `end_source`. Old `remove` spans at/after the old end are stale.
        ov["remove"] = [r for r in ov.get("remove", []) if r[1] <= (end - start) - 1.0]
        e0, end = end_source - start, end_source
    e_ext, why, limit, cut_t = tail_extension(str(REPO / src), start, e0, end - start, fps)
    if exact_end:
        # she runs straight into the next sentence (no silence): cut exactly at --end-source, no tail scan
        e_ext, limit, why = e0, e0, "exact end, no extension"
    pins = [(s["t0"], s["t1"], s["crop_x"]) for s in shots["shots"] if s.get("pinned")]
    pins += PINS.get(stem, [])
    return dict(shots=shots, sil=sil, ov=ov, src=src, start=start, end_ship=end, fps=fps, e0=e0,
                e_ext=e_ext, why=why, limit=limit, cut_t=cut_t, pins=pins, exact=exact_end)


def new_overrides(P, vert, path):
    """Old overrides minus whatever decided the END of the old cut (negative indices point at the
    old trailing segments, which the new vertical may not have). The new end is an explicit `out`
    on the raw segment holding the shipped cut point, with every later raw segment dropped. The
    out point is measured on the real vertical's envelope (the source-audio estimate can be ~40 ms
    early, which kc-short1 showed as an end still at -32 dB)."""
    fps = P["fps"]
    env = pp.envelope(str(vert))
    raw = pp.segments(env, fps)
    e0 = P["e0"]
    k = next((i for i, (a_, b_) in enumerate(raw) if b_ >= e0 - 0.12), len(raw) - 1)
    cut_t = P["cut_t"]
    end, why, _ = scan_tail(env, raw[k][1] if raw[k][1] > e0 else e0, fps, cut_t)
    if P.get("exact"):
        end, why = e0, "exact end"
    if end < e0:
        end = e0
    ov = json.loads(json.dumps(P["ov"]))
    segs = {kk: v for kk, v in ov.get("segments", {}).items() if int(kk) >= 0 and int(kk) != k}
    segs[str(k)] = {"out": round(end, 3)}
    ov["segments"] = segs
    drops = {d for d in ov.get("drop", []) if 0 <= d <= k}
    drops |= set(range(k + 1, len(raw)))
    ov["drop"] = sorted(drops)
    Path(path).write_text(json.dumps(ov, indent=1))
    P["e_final"], P["why_final"], P["raw_k"] = end, why, (k, len(raw))
    return ov


# ---------------------------------------------------------------- 1. reframe
def do_reframe(P, out):
    src = str(REPO / P["src"])
    start = P["start"]
    end = start + min(P["e_ext"] + 0.3, P["limit"] + 0.02)   # long enough to hold the decay, short of the next onset/cut
    w, h, fps = rf.probe(src)
    top, hh = rf.letterbox(src, w, h, start, end)
    cw = int(round(hh * 9 / 16)) // 2 * 2
    cuts, _, flashes = rf.shots(src, start, end, fps, 28.0)
    front = rf.cv2.CascadeClassifier(str(rf.CASCADES / "haarcascade_frontalface_default.xml"))
    prof = rf.cv2.CascadeClassifier(str(rf.CASCADES / "haarcascade_profileface.xml"))
    dets = [(front, None, False), (prof, None, False), (prof, None, True)]
    old = P["shots"]["shots"]
    plan_, prev, warns = [], w / 2, []
    for f0, f1 in zip(cuts, cuts[1:]):
        t0, t1 = f0 / fps, f1 / fps
        mid = (t0 + t1) / 2
        x = rf.subject_x(src, start + t0, start + t1, w, h, top, hh, dets)
        cx = x if x is not None else prev
        left = int(min(max(cx - cw / 2, 0), w - cw)) // 2 * 2
        pinned = False
        for a, b, px in P["pins"]:
            if a <= mid < b:
                left, pinned = px, True
        sh = {"t0": round(t0, 3), "t1": round(t1, 3), "f0": f0, "f1": f1,
              "face_x": None if x is None else round(x), "crop_x": left, "found": x is not None}
        if pinned:
            sh["pinned"] = True
        plan_.append(sh)
        prev = cx
        o = next((s for s in old if s["t0"] <= mid < s["t1"]), None)
        if o and abs(o["crop_x"] - left) > 60:
            warns.append(f"shot {t0:.2f}-{t1:.2f}s crop_x {left} vs shipped {o['crop_x']} "
                         f"({'pinned' if pinned else 'AUTO - check who is speaking'})")
        if t1 - t0 > 12 and not pinned:
            warns.append(f"shot {t0:.2f}-{t1:.2f}s is {t1 - t0:.0f}s long: largest-face crop may follow the listener")
    expr = str(plan_[-1]["crop_x"])
    for s in reversed(plan_[:-1]):
        expr = f"if(lt(n,{s['f1']}),{s['crop_x']},{expr})"
    vf = f"crop={cw}:{hh}:'{expr}':{top},scale=1080:1920:flags=lanczos,setsar=1"
    run(["ffmpeg", "-v", "error", "-y", "-ss", f"{start:.3f}", "-t", f"{end - start:.3f}", "-i", src,
         "-fps_mode", "passthrough", "-vf", vf, "-c:v", "libx264", "-crf", "12", "-preset", "slow",
         "-pix_fmt", "yuv420p", "-af", "loudnorm=I=-18:TP=-2:LRA=11,aresample=48000",
         "-c:a", "aac", "-b:a", "320k", str(out)])
    json.dump({"source": P["src"], "start": start, "end": round(end, 3), "active": [top, hh],
               "crop": [cw, hh], "shots": plan_}, open(str(out) + ".shots.json", "w"), indent=1)
    return dict(n_shots=len(plan_), flashes=flashes, warns=warns, end=end, **cut_audit(out, plan_))


def cut_audit(path, plan_, thresh=6.0):
    """Per planned camera cut: it must be ONE frame-to-frame spike. A second spike on the next frame
    is the wrong-crop flash. (reframe.audit's whole-clip count is noise on moving footage: the
    shipped kc-short1 reads 248 spikes with ZERO cuts, so only the planned cut frames are judged.)"""
    raw = subprocess.run(
        ["ffmpeg", "-v", "error", "-i", str(path), "-fps_mode", "vfr", "-vf", "scale=90:160",
         "-f", "rawvideo", "-pix_fmt", "gray", "-"],
        capture_output=True, stdin=subprocess.DEVNULL, check=True).stdout
    fr = np.frombuffer(raw, np.uint8).reshape(-1, 160, 90).astype(np.int16)
    d = np.abs(np.diff(fr, axis=0)).mean((1, 2))          # d[i] = change into frame i+1
    rows, bad = [], []
    for sh in plan_[1:]:
        f = sh["f0"]
        a, b = d[f - 1], (d[f] if f < len(d) else 0.0)
        rows.append((f, round(float(a), 1), round(float(b), 1)))
        if b > max(thresh, a * 0.5):
            bad.append(f)
    return dict(cuts=rows, double=bad, frames=len(fr))


# ---------------------------------------------------------------- audit helpers
def srt_cues(path):
    cues = []
    for blk in Path(path).read_text().strip().split("\n\n"):
        ln = blk.split("\n")
        m = re.match(r"(\d+):(\d+):([\d,]+) --> (\d+):(\d+):([\d,]+)", ln[1])
        f = lambda h, mi, s: int(h) * 3600 + int(mi) * 60 + float(s.replace(",", "."))
        cues.append((f(*m.groups()[:3]), f(*m.groups()[3:]), " ".join(ln[2:])))
    return cues


def audit(stem, c, name, rfr, P, final):
    out = []
    A = REPO / "edit" / f"analysis-{c}"
    sil = json.load(open(A / "silence.json"))
    words = json.load(open(A / "transcript.json"))["words"]
    master = REPO / "graphics" / f"{c}-master.mp4"
    out.append(f"== AUDIT {stem} -> {name}")
    out.append(f"reframe: {rfr['n_shots']} shots, {rfr['frames']} frames, cuts (frame, spike, next-frame) "
               f"{rfr['cuts']}; wrong-crop frames {rfr['double']}"
               f"{' OK' if not rfr['double'] else ' DEFECT'}; flash cutaways {rfr['flashes']}")
    for w_ in rfr["warns"]:
        out.append(f"  WARN {w_}")
    out.append(f"cut: {P['sil']['cut_duration']:.2f}s shipped -> {sil['cut_duration']:.2f}s new; "
               f"end {P['e0']:.2f} -> {sil['segments'][-1][1]:.2f} ({sil['segments'][-1][1] - P['e0']:+.2f}s; {P.get('why_final', 'see log')})")
    # shipped vs new segment agreement (stale override indices show up here)
    old, new = P["sil"]["segments"], sil["segments"]
    n = min(len(old), len(new)) - 1
    bad = [i for i in range(n) if abs(old[i][0] - new[i][0]) > 0.1 or abs(old[i][1] - new[i][1]) > 0.1]
    out.append(f"segments: shipped {len(old)} new {len(new)}; first {n} disagree at {bad if bad else 'none'}"
               f"{'  <- CHECK OVERRIDES' if bad or abs(len(old) - len(new)) > 0 else ''}")
    # captions
    cues = srt_cues(REPO / "project" / f"{c}.srt")
    durs = [b - a for a, b, _ in cues]
    out.append(f"captions: {len(cues)} cues, min {min(durs):.2f}s (<0.45s: {sum(d < 0.45 for d in durs)}), "
               f"last cue {durs[-1]:.2f}s, longest {max(len(t) for _, _, t in cues)} chars")
    out.append(f"  first: {cues[0][2]!r}   last: {cues[-1][2]!r}")
    # word times vs envelope of the master audio
    env = pp.envelope(str(master))
    W = pp.WINDOW
    quiet = []
    for wd in words:
        a, b = int((wd["t0"] + 0.03) / W), int((wd["t1"] - 0.03) / W)
        seg = env[a:max(b, a + 1)]
        if seg and max(seg) < -42 and wd["t1"] - wd["t0"] > 0.1:
            quiet.append((round(wd["t0"], 2), wd["w"], round(max(seg), 1)))
    out.append(f"word-time vs envelope: {len(words)} words, {len(quiet)} sit on near-silence (peak < -42 dB)"
               f"{': ' + str(quiet[:6]) if quiet else ''}")
    tail = env[-5:]
    last_loud = max((i for i, v in enumerate(env) if v > -35), default=0) * W
    last2 = max(env[-3:-1])        # final window is a partial one; judge the two before it
    out.append(f"end tail: last 100 ms {[round(v) for v in tail]} dB; last two full windows peak {last2:.1f} dB "
               f"({'OK <= -45, voice has decayed' if last2 <= -45 else 'NOT DECAYED, still voiced at the cut'}); "
               f"last > -35 dB at {last_loud:.2f}s of {len(env) * W:.2f}s")
    out.append(f"final: {final}")
    return "\n".join(out)


# ---------------------------------------------------------------- main
def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("stem", help="project stem, e.g. ignite-07-short1 or kc-short1")
    ap.add_argument("--suffix", default="r3")
    ap.add_argument("--cut-transcript", action="store_true",
                    help="transcribe the CUT audio instead of mapping uncut-source words (use when the source "
                         "word times drift and a ghost cue lands over the last word, e.g. kc-short6)")
    ap.add_argument("--keep-json", help="JSON list of [start,end] spans (clip time of the vertical) to hold as "
                    "pauses: short in-phrase gaps the 0.05s min-gap cut, so an opening is less choppy")
    ap.add_argument("--exact-end", action="store_true",
                    help="cut exactly at --end-source with no tail extension (speaker runs on with no silence)")
    ap.add_argument("--start-source", type=float,
                    help="source-time second where the clip should BEGIN; replaces the shipped start")
    ap.add_argument("--name", help="export name when no shipped copy exists in output/Short Form")
    ap.add_argument("--end-source", type=float,
                    help="source-time second where the last word of the clip ends; replaces the shipped end")
    ap.add_argument("--out-dir", default="output/Review")
    ap.add_argument("--plan", action="store_true", help="print the plan (incl. tail extension) and stop")
    ap.add_argument("--reframe-only", action="store_true",
                    help="plan + reframe + cut audit only (about 2 min); stops before preprocess")
    ap.add_argument("--audit-only", action="store_true", help="re-print the audit of an existing -<suffix> build")
    ap.add_argument("--force", action="store_true", help="rebuild even if the -<suffix> files exist")
    a = ap.parse_args()
    stem, c = a.stem, f"{a.stem}-{a.suffix}"
    if a.out_dir.rstrip("/").endswith("Short Form") or "Short Form" in a.out_dir:
        sys.exit("refusing to write into output/Short Form")
    name = a.name or shipped_name(stem)
    P = plan(stem, a.suffix, a.end_source, a.start_source, a.exact_end)
    y, size, maxw = caption_params(stem)
    log(f"{stem} = {name}")
    log(f"source {P['src']}  start {P['start']}  shipped end {P['end_ship']}  "
        f"cut point {P['e0']:.2f} -> ~{P['e_ext']:.2f} ({P['why']}, limit {P['limit']:.2f})  pins {P['pins']}")
    log(f"captions y {y} size {size} maxw {maxw}  fixes {fixes_file(stem)}")
    if a.plan:
        return
    vert = REPO / "graphics" / f"{c}-vertical.mp4"
    if a.audit_only:
        sj = json.load(open(str(vert) + ".shots.json"))
        rfr = dict(n_shots=len(sj["shots"]), flashes=[], warns=[], end=sj["end"], **cut_audit(vert, sj["shots"]))
        print(audit(stem, c, name, rfr, P, "audit-only"))
        return
    for p in (vert, REPO / "edit" / f"analysis-{c}", REPO / "graphics" / f"{c}-master.mp4"):
        if p.exists() and not a.force:
            sys.exit(f"{p} exists; pass --force to rebuild (shipped files use no suffix and are never touched)")
    ovp = REPO / "edit" / f"overrides-{c}.json"

    stale = REPO / "edit" / f"analysis-{c}" / "source_words.json"
    if stale.exists():
        stale.unlink()                 # cached whisper words of a previous -<suffix> pass: wrong clip length
    log("1/5 reframe")
    rfr = do_reframe(P, vert)
    if a.reframe_only:
        log(f"reframe only: {rfr['n_shots']} shots; cuts {rfr['cuts']}; wrong-crop frames {rfr['double']}")
        for w_ in rfr["warns"]:
            log("WARN " + w_)
        return
    new_overrides(P, vert, ovp)
    if a.keep_json:
        ov_ = json.load(open(ovp))
        ov_["keep"] = json.load(open(a.keep_json))
        Path(ovp).write_text(json.dumps(ov_, indent=1))
    log(f"end: shipped cut point {P['e0']:.3f}s -> {P['e_final']:.3f}s ({P['why_final']}); "
        f"last-segment index/raw count {P['raw_k']}")
    log(f"audit: cuts {rfr['cuts']} wrong-crop frames {rfr['double']}")

    log("2/5 preprocess")
    run(["python3", "edit/preprocess.py", vert, "--out", f"edit/analysis-{c}", "--skip-framing",
         "--overrides", ovp] + (["--cut-transcript"] if a.cut_transcript else []))

    log("3/5 captions")
    capdir = f"graphics/{c}-captions"
    srt = f"project/{c}.srt"
    cmd = ["python3", "edit/captions_overlay.py", "--analysis", f"edit/analysis-{c}", "--out", capdir,
           "--res", "1080x1920", "--y", y, "--size", size, "--maxw", maxw, "--srt", srt]
    if Path(fixes_file(stem)).exists():
        cmd += ["--fixes", fixes_file(stem)]
    run(cmd)
    hl = REPO / "edit" / f"highlights-{stem}.json"
    bcmd = ["python3", "edit/brand_overlay.py", "--src", capdir, "--out", f"graphics/{c}-brand-captions",
            "--logo", "graphics/brand/silicon-data-white.png"]
    if hl.exists():
        bcmd += ["--highlight", hl]
    bout = run(bcmd)
    for ln in bout.splitlines():
        if "WARNING" in ln:
            log(ln.strip())

    log("4/5 master (burn.py, master only)")
    run(["python3", "edit/burn.py", "--analysis", f"edit/analysis-{c}", "--out", f"{a.out_dir}/.unused-{c}.mp4",
         "--master", f"graphics/{c}-master.mp4"])

    log("5/5 title card + composite")
    res = stc.build_one(name, c=c, out_dir=str(REPO / a.out_dir))
    log(f"build_one: {res}")
    final = REPO / a.out_dir / f"{name}.mp4"
    print(audit(stem, c, name, rfr, P, f"{final} ok={res.get('ok')}"))
    log("done")


if __name__ == "__main__":
    main()
