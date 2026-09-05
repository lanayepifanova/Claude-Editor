#!/usr/bin/env python3
"""Captions-only route: cut the ORIGINAL footage, burn the caption overlay,
encode H.264/AAC into output/.

This is the short route that skips Premiere entirely (established 2026-08-29 on
"oil markets"). It exists because the two traps here are easy to walk into by
hand:

  * cut from `footage/`, never from `cut_proof.mp4` — the proof is half
    resolution, and using it baked permanent softness into the Firecrawl export
  * `output/` is hers alone — nothing here overwrites a file that already exists
    unless --force says so explicitly

Stage 1 builds an uncaptioned master from the segments in silence.json. Stage 2
composites the rendered overlay on top. Keeping the master lets --verify read a
luma difference between the two, which is what proves the ink actually landed —
check_render.py only ever sees the overlay on its own.

    python3 edit/burn.py --analysis edit/analysis-<name> \
        --overlay graphics/<name>-cap.mov --out "output/<name>.mp4"
"""
import argparse, json, os, shlex, subprocess, sys, tempfile

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def run(cmd, **kw):
    p = subprocess.run(cmd, capture_output=True, text=True, **kw)
    if p.returncode != 0:
        sys.exit("ffmpeg failed:\n  " + " ".join(shlex.quote(c) for c in cmd)
                 + "\n" + p.stderr[-2000:])
    return p


def probe(path, stream="v:0", entries="width,height,nb_read_packets"):
    cmd = ["ffprobe", "-v", "error", "-select_streams", stream,
           "-count_packets", "-show_entries", f"stream={entries}",
           "-of", "json", path]
    p = subprocess.run(cmd, capture_output=True, text=True)
    if p.returncode != 0:
        sys.exit(f"ffprobe failed on {path}\n{p.stderr[-800:]}")
    st = json.loads(p.stdout)["streams"]
    return st[0] if st else {}


def build_master(src, segments, dest):
    """Concat the kept segments straight out of the original footage."""
    parts, labels = [], []
    for i, (a, b) in enumerate(segments):
        parts.append(f"[0:v]trim=start={a:.6f}:end={b:.6f},setpts=PTS-STARTPTS[v{i}]")
        parts.append(f"[0:a]atrim=start={a:.6f}:end={b:.6f},asetpts=PTS-STARTPTS[a{i}]")
        labels.append(f"[v{i}][a{i}]")
    graph = ";".join(parts) + ";" + "".join(labels) + \
        f"concat=n={len(segments)}:v=1:a=1[v][a]"
    run(["ffmpeg", "-y", "-i", src, "-filter_complex", graph,
         "-map", "[v]", "-map", "[a]",
         "-c:v", "libx264", "-preset", "slow", "-crf", "16", "-pix_fmt", "yuv420p",
         "-c:a", "aac", "-b:a", "192k", "-movflags", "+faststart", dest])


def composite(master, overlay, dest):
    run(["ffmpeg", "-y", "-i", master, "-i", overlay,
         "-filter_complex", "[0:v][1:v]overlay=0:0:format=auto:eof_action=pass[v]",
         "-map", "[v]", "-map", "0:a",
         "-c:v", "libx264", "-preset", "slow", "-crf", "16", "-pix_fmt", "yuv420p",
         "-c:a", "aac", "-b:a", "192k", "-movflags", "+faststart", dest])


def ink_fraction(master, burn):
    """Per-frame fraction of pixels the captions actually changed.

    Mean luma difference does NOT work here: master and burn are encoded
    separately, so x264 noise alone reads ~1.0 YAVG — the same order as the
    text, and every frame looks "inked". Binarising the difference first
    (|delta| > 60) throws the noise away and leaves the caption strokes, so the
    number that comes back is the share of the frame the ink covers: ~2-10% on
    a captioned frame, ~0 in a gap.
    """
    with tempfile.NamedTemporaryFile(suffix=".txt", delete=False) as fh:
        stats = fh.name
    run(["ffmpeg", "-y", "-i", burn, "-i", master, "-filter_complex",
         "[0:v][1:v]blend=all_mode=difference,"
         "lut=y='if(gt(val,60),255,0)',signalstats,"
         f"metadata=print:key=lavfi.signalstats.YAVG:file={stats}",
         "-f", "null", "-"])
    vals = []
    for line in open(stats):
        if "YAVG=" in line:
            vals.append(float(line.strip().split("YAVG=")[1]) / 255.0)
    os.unlink(stats)
    return vals


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--analysis", required=True, help="edit/analysis-<name>")
    ap.add_argument("--overlay", help="rendered caption overlay (.mov with alpha)")
    ap.add_argument("--out", required=True, help="final file, normally output/<name>.mp4")
    ap.add_argument("--master", help="where to keep the uncaptioned cut "
                                     "(default: alongside --out, .master.mp4)")
    ap.add_argument("--force", action="store_true",
                    help="allow overwriting an existing --out. output/ is hers.")
    ap.add_argument("--verify-only", action="store_true",
                    help="re-read an existing burn against its master, encode nothing")
    args = ap.parse_args()

    sil = json.load(open(os.path.join(args.analysis, "silence.json")))
    src = sil["source"]
    if not os.path.isabs(src):
        src = os.path.join(REPO, src)
    if not os.path.exists(src):
        sys.exit(f"source footage is gone: {sil['source']}\n"
                 "Do NOT substitute cut_proof.mp4 — it is half resolution.")
    if "cut_proof" in os.path.basename(src):
        sys.exit("refusing to cut from a proof render; use the original footage")

    master = args.master or os.path.splitext(args.out)[0] + ".master.mp4"
    segments = sil["segments"]

    if not args.verify_only:
        if os.path.exists(args.out) and not args.force:
            sys.exit(f"{args.out} already exists — pass --force to overwrite it.")
        os.makedirs(os.path.dirname(os.path.abspath(args.out)), exist_ok=True)
        print(f"1/2  cutting {len(segments)} segments from {os.path.basename(src)} "
              f"({sil['source_duration']:.1f}s -> {sil['cut_duration']:.1f}s, "
              f"{sil['removed_pct']}% removed)")
        build_master(src, segments, master)

        if args.overlay:
            v = probe(master)
            o = probe(args.overlay)
            print(f"     master {v['width']}x{v['height']} {v['nb_read_packets']}f · "
                  f"overlay {o['width']}x{o['height']} {o['nb_read_packets']}f")
            if (v["width"], v["height"]) != (o["width"], o["height"]):
                sys.exit("overlay resolution does not match the cut")
            if abs(int(v["nb_read_packets"]) - int(o["nb_read_packets"])) > 1:
                sys.exit("frame counts differ — the overlay was built from a "
                         "different cut. Re-run captions_overlay.py.")
            print("2/2  compositing captions")
            composite(master, args.overlay, args.out)
        else:
            print("2/2  no --overlay given; master only")
            return

    print("     verifying burn against the uncaptioned master …")
    vals = ink_fraction(master, args.out)
    INK = 0.002                       # 0.2% of the frame; a one-word cue is ~2%
    lit = [i for i, v in enumerate(vals) if v > INK]
    if not lit:
        sys.exit("FAIL: no frame differs from the master — no captions burned in.")
    fps = sil.get("fps", 30.0)
    peak = max(vals)
    print(f"     {len(lit)}/{len(vals)} frames carry ink "
          f"({100*len(lit)/len(vals):.0f}% of the cut) · "
          f"peak coverage {100*peak:.1f}% of frame")
    gaps, run_start = [], None
    for i in range(len(vals)):
        hot = vals[i] > INK
        if hot and run_start is not None:
            if (i - run_start) / fps > 2.0:
                gaps.append((run_start / fps, i / fps))
            run_start = None
        elif not hot and run_start is None:
            run_start = i
    if run_start is not None and (len(vals) - run_start) / fps > 2.0:
        gaps.append((run_start / fps, len(vals) / fps))
    if gaps:
        print("     gaps with no caption over 2s: " +
              ", ".join(f"{a:.1f}-{b:.1f}s" for a, b in gaps))
    print(f"\n-> {args.out}  ({os.path.getsize(args.out)/1e6:.1f} MB)")
    print(f"   master kept at {master}")


if __name__ == "__main__":
    main()
