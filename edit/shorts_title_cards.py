#!/usr/bin/env python3
"""shorts_title_cards.py -- give an already-shipped short the approved title-card
treatment (2026-11-06, pilot: Ignite 04 short 1 "No way to short compute").

Per short: the small speaker card (title_overlay.py --style card --size 60, centre
y 0.69, on screen from frame 0, no transition) and the shipped captions moved
under it to y 0.775 (brand_overlay.py --restyle on a COPY of
graphics/<c>-brand-captions, cue lines untouched). The approved master is
re-used; nothing is re-cut and nothing is zoomed. Encodes with libx264 only.

    python3 edit/shorts_title_cards.py --ignite 07            # every short of one video
    python3 edit/shorts_title_cards.py --only "[CP] Ignite 07 - Coalition of experts"

Heavy intermediates (caption .mov, card .mov) go to a scratch dir outside the
repo and are deleted after each short. The shipped file is replaced with an
atomic mv in its pillar folder only after every check passes.
"""
import argparse, json, os, re, shutil, subprocess, sys, glob
from pathlib import Path
import numpy as np

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO / "edit"))
import burn

SHORT = REPO / "output" / "Short Form"
SCRATCH = Path(os.environ.get("TC_SCRATCH", "/private/tmp/claude-501/-Users-lanayepifanova-Claude-Editor/4636c49b-6ffc-41da-a2b6-e918ef110a80/scratchpad"))
CARD_Y, CAP_Y, SIZE = 0.69, 0.775, 60
W, H = 1080, 1920
FPS = "24000/1001"

# Two rows, broken at a natural phrase boundary. Key = filename title.
BREAKS = {
    "3 neoclouds to 300": ("3 neoclouds", "to 300"),
    "Compute is a giant baby": ("Compute is", "a giant baby"),
    "Is the AI bubble just a car loan": ("Is the AI bubble", "just a car loan"),
    "The NASDAQ for GPUs": ("The NASDAQ", "for GPUs"),
    "Tokens are a different animal": ("Tokens are", "a different animal"),
    "Coalition of experts": ("Coalition", "of experts"),
    "Here's my model, go train it": ("Here's my model,", "go train it"),
    "Inference will outgrow training": ("Inference will", "outgrow training"),
    "Mixture of experts vs the enterprise": ("Mixture of experts", "vs the enterprise"),
    "Prefill vs decode": ("Prefill", "vs decode"),
    "What HFT and AI have in common": ("What HFT and AI", "have in common"),
    "A billion dollars of RFQ a month": ("A billion dollars", "of RFQ a month"),
    "How does Nvidia feel about GPU futures": ("How does Nvidia feel", "about GPU futures"),
    "Three hyperscalers to 300 neoclouds": ("Three hyperscalers", "to 300 neoclouds"),
    "Uncertainty kills business planning": ("Uncertainty kills", "business planning"),
    "Why would a neocloud share its prices": ("Why would a neocloud", "share its prices"),
    "You can't be the referee and the player": ("You can't be the referee", "and the player"),
    "Anthropic's trillion-dollar valuation": ("Anthropic's", "trillion-dollar valuation"),
    "Do you pay providers for their data": ("Do you pay providers", "for their data"),
    "Pricing a GPU like a NYC apartment": ("Pricing a GPU like", "a NYC apartment"),
    "The shortage is power not chips": ("The shortage is", "power not chips"),
    "Machine learning or glorified regression": ("Machine learning or", "glorified regression"),
    "The token index everyone misreads": ("The token index", "everyone misreads"),
    "A cloud is a glass of ice": ("A cloud is", "a glass of ice"),
    "Bitcoin miner to GPU cloud": ("Bitcoin miner", "to GPU cloud"),
    "They used to be called containers": ("They used to be", "called containers"),
    "This is pushing people": ("This is", "pushing people"),
    "Running a cloud is a 24-7 grind": ("Running a cloud is", "a 24/7 grind"),
    "Compute grew 25X, the network 8X": ("Compute grew 25X,", "the network 8X"),
    "Does Upscale compete with NVIDIA": ("Does Upscale compete", "with NVIDIA"),
    "Not one technology suits every need": ("Not one technology", "suits every need"),
    "The network is the bottleneck": ("The network is", "the bottleneck"),
    "A single off-taker gets the better deal": ("A single off-taker", "gets the better deal"),
    "Only two or three labs will win": ("Only two or three", "labs will win"),
    "The crazy GPU guys were a detour": ("The crazy GPU guys", "were a detour"),
    "The shortage means everyone is winning": ("The shortage means", "everyone is winning"),
    "90 to 98 percent cache hit is 5x the tokens": ("90 to 98 percent cache hit", "is 5x the tokens"),
    "Inference is about economics": ("Inference is", "about economics"),
    "Power is the new currency": ("Power is", "the new currency"),
    "Why a chip company runs its own cloud": ("Why a chip company", "runs its own cloud"),
    "Not every chip company will survive": ("Not every chip", "company will survive"),
    "The largest chip in the world": ("The largest chip", "in the world"),
    "Why not just use NVIDIA GPUs": ("Why not just use", "NVIDIA GPUs"),
    "Why there are so many inference chips": ("Why there are so many", "inference chips"),
    "Seven years to plug into the grid": ("Seven years to", "plug into the grid"),
    "The time value of compute": ("The time value", "of compute"),
    "Training built big, inference runs small": ("Training built big,", "inference runs small"),
    "What power traders actually trade": ("What power traders", "actually trade"),
    "When power prices go negative": ("When power prices", "go negative"),
    "Agents will be the main consumers of compute": ("Agents will be the main", "consumers of compute"),
    "Developers already let agents rent GPUs": ("Developers already", "let agents rent GPUs"),
    "Everyone is just market making on compute": ("Everyone is just market", "making on compute"),
    "Long compute physically, short it on futures": ("Long compute physically,", "short it on futures"),
    "From asset-light to reserving compute": ("From asset-light", "to reserving compute"),
}


def sh(cmd, **kw):
    p = subprocess.run(cmd, capture_output=True, text=True, cwd=REPO, **kw)
    if p.returncode:
        raise RuntimeError(f"{' '.join(map(str, cmd))[:200]}\n{(p.stderr or p.stdout)[-1500:]}")
    return p


def frames_of(path):
    p = sh(["ffprobe", "-v", "error", "-select_streams", "v:0", "-count_packets",
            "-show_entries", "stream=codec_name,width,height,nb_read_packets", "-of", "json", str(path)])
    return json.loads(p.stdout)["streams"][0]


def duration_of(path, stream):
    p = sh(["ffprobe", "-v", "error", "-select_streams", stream, "-show_entries",
            "stream=codec_name,duration", "-of", "json", str(path)])
    return json.loads(p.stdout)["streams"][0]


def raw_frames(cmd_in, vf, w, h, pix="gray"):
    """Yield every frame of a filtered ffmpeg stream as a numpy array."""
    cmd = ["ffmpeg", "-v", "error", *cmd_in, "-vf", vf, "-f", "rawvideo", "-pix_fmt", pix, "-"]
    p = subprocess.Popen(cmd, stdout=subprocess.PIPE, stdin=subprocess.DEVNULL, bufsize=1 << 22)
    size = w * h
    while True:
        b = p.stdout.read(size)
        if len(b) < size:
            break
        yield np.frombuffer(b, np.uint8).reshape(h, w)
    p.wait()


def build_one(name, only_check=False, c=None, out_dir=None):
    m = re.match(r"\[(\w+)\] Ignite (\d+) - (.*)$", name)
    tag, nn, title = m.groups()
    pillar = {"CP": "[CP] Cloud Providers", "RP": "[RP] Reference Price", "SM": "[SM] SiliconMark"}[tag]
    shipped = SHORT / pillar / f"{name}.mp4"
    if c:
        # REDO: a freshly cut master replaces the shipped cut. Nothing is looked up
        # from the shipped file and the shipped file is never touched; the result
        # goes to out_dir for her to review first.
        master = REPO / "graphics" / f"{c}-master.mp4"
        n_frames = int(frames_of(master)["nb_read_packets"])
        shipped = None
    else:
        assert shipped.exists(), shipped
        sf = frames_of(shipped)
        n_frames = int(sf["nb_read_packets"])
        pre = "kc" if nn == "04" else f"ignite-{nn}"
        cands = []
        for mp in glob.glob(str(REPO / "graphics" / f"{pre}-short*-master.mp4")):
            if "brand" in mp:
                continue
            if int(frames_of(mp)["nb_read_packets"]) == n_frames:
                cands.append(Path(mp).name[:-len("-master.mp4")])
        assert len(cands) == 1, (name, cands)
        c = cands[0]
    master = REPO / "graphics" / f"{c}-master.mp4"
    src_caps = REPO / "graphics" / f"{c}-brand-captions"
    assert (src_caps / "index.html").exists()
    assert "67DEF9" in (src_caps / "index.html").read_text().upper(), "captions are not the R1 Sky style"
    lines = BREAKS[title]
    log = lambda s: print(f"[{name}] {s}", flush=True)
    log(f"source {c}, {n_frames}f, rows {lines}")

    # 1. captions: COPY, restyle y -> 0.775 (cue lines untouched)
    dst = REPO / "graphics" / f"{c}-title-captions"
    if dst.exists():
        shutil.rmtree(dst)
    shutil.copytree(src_caps, dst, ignore=shutil.ignore_patterns(".hyperframes"))
    sh([sys.executable, "edit/brand_overlay.py", "--restyle", str(dst), "--y", str(CAP_Y)])
    cue = lambda p: re.findall(r'^.*class="clip cue".*$', (p / "index.html").read_text(), re.M)
    assert cue(dst) == cue(src_caps), "cue lines changed"

    # 2. card: committed composition at full length; a 1 s twin is rendered for the still
    card = REPO / "graphics" / f"{c}-title-card"
    sh([sys.executable, "edit/title_overlay.py", "--lines", *lines, "--frames", str(n_frames),
        "--y", str(CARD_Y), "--size", str(SIZE), "--style", "card", "--out", str(card)])
    work = SCRATCH / c
    shutil.rmtree(work, ignore_errors=True)
    work.mkdir(parents=True)
    twin = work / "card24"
    sh([sys.executable, "edit/title_overlay.py", "--lines", *lines, "--frames", "24",
        "--y", str(CARD_Y), "--size", str(SIZE), "--style", "card", "--out", str(twin)])
    env = dict(os.environ, FFMPEG_ENCODE_TIMEOUT_MS="3600000", PRODUCER_ENABLE_CHUNKED_ENCODE="true")
    cardmov, capmov = work / "card.mov", work / "cap.mov"
    log("rendering card still")
    sh(["nice", "-n", "10", "npx", "hyperframes", "render", str(twin), "--format", "mov", "-q", "high",
        "-f", FPS, "--workers", "1", "-o", str(cardmov)], env=env)
    sh(["ffmpeg", "-y", "-v", "error", "-i", str(cardmov), "-frames:v", "1", str(work / "card.png")])
    log("rendering captions")
    sh(["nice", "-n", "10", "npx", "hyperframes", "render", str(dst), "--format", "mov", "-q", "high",
        "-f", FPS, "--workers", "1", "-o", str(capmov)], env=env)
    cf = int(frames_of(capmov)["nb_read_packets"])
    assert 0 <= cf - n_frames <= 3, f"caption overlay {cf}f vs {n_frames}f"

    # 3. geometry from alpha, as text
    import cv2
    png = cv2.imread(str(work / "card.png"), cv2.IMREAD_UNCHANGED)
    assert png.shape[2] == 4, "card still lost its alpha"
    ys, xs = np.where(png[..., 3] > 8)
    card_box = (int(xs.min()), int(ys.min()), int(xs.max()) + 1, int(ys.max()) + 1)
    log(f"card bbox x{card_box[0]}-{card_box[2]} y{card_box[1]}-{card_box[3]} (w {card_box[2]-card_box[0]})")
    rows_hi, rows_lo, ink_frames, cols = H, 0, [], [W, 0]
    bandshare = []
    band = None
    cap_rows = []
    for fr in raw_frames(["-i", str(capmov)], "alphaextract", W, H):
        a = fr[300:, :] > 40                       # skip the logo up top
        if a.any():
            r = np.where(a.any(axis=1))[0] + 300
            cap_rows.append((int(r.min()), int(r.max())))
            cc = np.where(a.any(axis=0))[0]
            cols = [min(cols[0], int(cc.min())), max(cols[1], int(cc.max()))]
        else:
            cap_rows.append(None)
    lit = [i for i, r in enumerate(cap_rows) if r]
    ymin = min(r[0] for r in cap_rows if r)
    ymax = max(r[1] for r in cap_rows if r)
    gap = ymin - card_box[3]
    log(f"captions ink rows {ymin}-{ymax}, x {cols[0]}-{cols[1]}; {len(lit)}/{n_frames} frames; gap to card {gap}px")
    assert gap >= 12, f"caption ink within {gap}px of the card"

    # 4. legibility: share of near-white pixels of the UNCAPTIONED picture in the caption band
    b0, b1 = max(ymin - 10, 0), min(ymax + 10, H)
    shares = []
    for i, fr in enumerate(raw_frames(["-i", str(master)], "format=gray", W, H)):
        if i < len(cap_rows) and cap_rows[i]:
            reg = fr[b0:b1, max(cols[0] - 10, 0):cols[1] + 10]
            shares.append(float((reg > 200).mean()))
    white_mean = 100 * float(np.mean(shares)) if shares else 0
    white_p90 = 100 * float(np.percentile(shares, 90)) if shares else 0
    log(f"caption band white-share (luma>200, caption frames): mean {white_mean:.1f}% p90 {white_p90:.1f}%")

    # 5. composite (same encode as burn.composite): master + card still + captions
    dest_dir = Path(out_dir) if out_dir else SHORT / pillar
    dest_dir.mkdir(parents=True, exist_ok=True)
    out_tmp = dest_dir / f".tmp-{c}.mp4"
    dur = float(duration_of(master, "v:0")["duration"])
    graph = ("[0:v][1:v]overlay=0:0:format=auto:eof_action=pass[s1];"
             "[s1][2:v]overlay=0:0:format=auto:eof_action=pass[v]")
    log("compositing")
    sh(["nice", "-n", "10", "ffmpeg", "-y", "-v", "error", "-i", str(master),
        "-loop", "1", "-framerate", FPS, "-t", f"{dur + 1:.3f}", "-i", str(work / "card.png"),
        "-i", str(capmov), "-filter_complex", graph, "-map", "[v]", "-map", "0:a",
        "-frames:v", str(n_frames), "-c:v", "libx264", "-preset", "slow", "-crf", "16",
        "-pix_fmt", "yuv420p", "-c:a", "aac", "-b:a", "192k", "-movflags", "+faststart", str(out_tmp)])

    # 6. verify
    v = frames_of(out_tmp)
    vd, ad = duration_of(out_tmp, "v:0"), duration_of(out_tmp, "a:0")
    sd = float(duration_of(shipped if shipped else master, "v:0")["duration"])
    checks = {
        "h264": v["codec_name"] == "h264", "aac": ad["codec_name"] == "aac",
        "1080x1920": (v["width"], v["height"]) == (W, H),
        "frames": int(v["nb_read_packets"]) == n_frames,
        "duration": abs(float(vd["duration"]) - sd) <= 1 / 23.976 + 1e-3,
    }
    # card present on every frame: changed-pixel share inside the card box vs the master
    x0, y0, x1, y1 = card_box
    crop = f"crop={x1-x0}:{y1-y0}:{x0}:{y0}"
    stats = work / "card.txt"
    sh(["ffmpeg", "-y", "-v", "error", "-i", str(out_tmp), "-i", str(master), "-filter_complex",
        f"[0:v]{crop}[a];[1:v]{crop}[b];[a][b]blend=all_mode=difference,"
        f"lut=y='if(gt(val,60),255,0)',signalstats,metadata=print:key=lavfi.signalstats.YAVG:file={stats}",
        "-f", "null", "-"])
    cv = [float(l.split("YAVG=")[1]) / 255 for l in open(stats) if "YAVG=" in l]
    checks["card_all_frames"] = len(cv) >= n_frames - 1 and min(cv) > 0.01
    # captions landed: changed pixels in the caption band on caption frames, none elsewhere
    cropb = f"crop={W}:{b1-b0}:0:{b0}"
    sh(["ffmpeg", "-y", "-v", "error", "-i", str(out_tmp), "-i", str(master), "-filter_complex",
        f"[0:v]{cropb}[a];[1:v]{cropb}[b];[a][b]blend=all_mode=difference,"
        f"lut=y='if(gt(val,60),255,0)',signalstats,metadata=print:key=lavfi.signalstats.YAVG:file={stats}",
        "-f", "null", "-"])
    bv = [float(l.split("YAVG=")[1]) / 255 for l in open(stats) if "YAVG=" in l]
    blit = sum(1 for x in bv if x > 0.002)
    checks["captions_landed"] = abs(blit - len(lit)) <= max(6, len(lit) // 25)
    log(f"min card change {min(cv)*100:.1f}% over {len(cv)}f; caption band lit {blit} vs alpha {len(lit)}")
    ok = all(checks.values())
    log("checks " + " ".join(f"{k}={'ok' if x else 'FAIL'}" for k, x in checks.items()))
    res = dict(name=name, c=c, ok=ok, frames=n_frames, card_w=card_box[2] - card_box[0],
               gap=gap, white_mean=round(white_mean, 1), white_p90=round(white_p90, 1),
               old_mb=round(shipped.stat().st_size / 1e6, 1) if shipped else 0, new_mb=round(out_tmp.stat().st_size / 1e6, 1))
    if ok and not shipped:
        target = dest_dir / f"{name}.mp4"
        os.replace(out_tmp, target)
        log(f"WROTE {target}")
    elif ok:
        os.replace(out_tmp, shipped)           # atomic: same folder, same filename
        log(f"REPLACED {shipped.name}")
    else:
        out_tmp.unlink()
        log("FAILED - kept the old export")
    shutil.rmtree(work, ignore_errors=True)
    return res


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--ignite")
    ap.add_argument("--only")
    ap.add_argument("--redo", help="project stem of a freshly cut master (e.g. kc-short3); builds into --out-dir "
                                   "and leaves the shipped file alone. Needs --only.")
    ap.add_argument("--out-dir", help="where a --redo build is written")
    ap.add_argument("--skip", action="append", default=[])
    a = ap.parse_args()
    names = []
    for pil in sorted(SHORT.iterdir()):
        for f in sorted(pil.glob("*.mp4")):
            n = f.stem
            if a.only and n != a.only:
                continue
            if a.ignite and f" Ignite {a.ignite} - " not in n:
                continue
            if n in a.skip:
                continue
            if n == "[RP] Ignite 04 - No way to short compute":
                continue                        # pilot, replaced from the approved review file
            names.append(n)
    results = []
    for n in names:
        try:
            results.append(build_one(n, c=a.redo, out_dir=a.out_dir))
        except Exception as e:
            print(f"[{n}] ERROR {e}", flush=True)
            results.append(dict(name=n, ok=False, error=str(e)[:300]))
    print("RESULTS " + json.dumps(results))


if __name__ == "__main__":
    main()
