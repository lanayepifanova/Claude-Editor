#!/usr/bin/env python3
"""
build_clips.py — her screen recordings -> overlay-ready video plates.

The photo pipeline (prep_photos.py -> build_photos.py) plays a `raw-video` plate
for exactly the length of its beat and has no in/out or speed control of its own,
so every splice and speed change has to be baked into the plate file here. Each
entry below is one beat: which recording, which span of it, and how long that
span has to become.

The speed factor is *derived* — span / want — never typed in. That is the point:
a slow stretch (a diagram that barely moves, an explainer holding on one idea)
gets a long span squeezed into a ~2.8s beat and so runs fast, while material that
is already lively (hands working, neurons firing) takes a span close to its beat
and stays near 1x. She asked to "speed up certain sections that are a little
slower"; this is where that decision lives.

`crop` exists because a full-frame slide of 16px labels becomes an unreadable
white rectangle at plate size. Cropping to the part that carries the meaning is
what keeps legibility first.

    python3 edit/build_clips.py            # writes graphics/Neurons-png/*.mov
    python3 edit/prep_photos.py --deck neurons
    python3 edit/build_photos.py

Plate height is fixed (PLATE_H) and the width follows each source's aspect, so
the band maths in build_photos.py stays a single number per project.
"""
import glob
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PLATE_H = 436          # x264 needs even dimensions; so do the widths below

# Sorted glob order, which is how the five recordings land: 10.00.19, 10.14.02,
# 9.55.40, 9.56.47, 9.59.11. Keyed 1-5 so the table below reads like a shot list.
RECORDINGS = "footage/Screen*.mov"

#  name, rec, in, out, want, width, crop "w:h:x:y" or None
CLIPS = [
    ("neuron label",   1,  1.50,  4.30, 2.70, 786, None),
    ("cortical pong",  3,  0.00,  4.82, 3.05, 752, None),
    ("cl1 device",     4,  2.00,  5.20, 2.80, 752, None),
    ("lab hands",      4,  8.80, 12.60, 2.50, 752, None),
    # the whole slide is a white rectangle of tiny labels at plate size — crop to
    # the neural-progenitor -> neuron path, which is the bit the line is about
    ("stem cells",     5,  0.30,  5.00, 2.70, 786, "560:310:300:140"),
    ("mea chip",       4,  0.00,  2.60, 2.60, 752, None),
    # 22.0-26.5 still carries the yellow "Hidden layers" box and read as a near
    # duplicate of the hidden-layers plate 7s later; this span is the plain pass
    ("cloud compute",  2, 26.50, 31.00, 2.85, 786, None),
    ("living network", 1, 22.80, 26.40, 3.00, 786, None),
    ("hidden layers",  2, 14.00, 20.50, 2.80, 786, None),
    ("why layers",     2, 41.00, 47.00, 2.55, 786, None),
    ("neurons firing", 1, 43.00, 49.00, 2.90, 786, None),
    # same white-rectangle problem — crop to the one labelled colonies panel
    ("dual smad",      5, 15.00, 25.00, 2.80, 786, "640:355:490:105"),
    ("net layers",     2,  0.00,  5.00, 2.90, 786, None),
    ("culture dish",   4, 15.50, 19.00, 2.85, 752, None),
]


def main():
    srcs = sorted(glob.glob(str(ROOT / RECORDINGS)))
    if len(srcs) < 5:
        sys.exit(f"expected 5 screen recordings under {RECORDINGS}, found {len(srcs)}")
    out_dir = ROOT / "graphics" / "Neurons-png"
    out_dir.mkdir(parents=True, exist_ok=True)

    stems = [c[0] for c in CLIPS]
    dupes = {s for s in stems if stems.count(s) > 1}
    # prep_photos keys its manifest on the stem, so a collision silently
    # overwrites a plate — the trap that cost a rename on Sony TSMC
    assert not dupes, f"two clips share a stem: {sorted(dupes)}"

    for name, rec, tin, tout, want, width, crop in CLIPS:
        factor = (tout - tin) / want
        # fps first: setpts before a frame-rate change gets undone by it
        vf = f"fps=30,setpts=PTS/{factor:.6f},"
        if crop:
            vf += f"crop={crop},"
        vf += f"scale={width}:{PLATE_H}:flags=lanczos"
        dst = out_dir / f"{name}.mov"
        # -ss/-to on the INPUT. `-t` on the output does not truncate a sped-up
        # stream and silently hands back the un-sped span instead.
        subprocess.run(
            ["ffmpeg", "-y", "-v", "error", "-ss", f"{tin}", "-to", f"{tout}",
             "-i", srcs[rec - 1], "-an", "-vf", vf,
             "-c:v", "libx264", "-preset", "slow", "-crf", "18",
             "-pix_fmt", "yuv420p", "-movflags", "+faststart", str(dst)],
            check=True)
        got = float(subprocess.run(
            ["ffprobe", "-v", "error", "-show_entries", "format=duration",
             "-of", "default=nw=1:nk=1", str(dst)],
            capture_output=True, text=True).stdout.strip())
        drift = "" if abs(got - want) < 0.09 else "   <-- drift, re-pin the beat"
        print(f"  {name:16s} rec{rec} {tin:5.1f}-{tout:5.1f}  x{factor:.2f}  "
              f"-> {got:.2f}s (want {want:.2f}){drift}")

    print(f"-> {out_dir}")


if __name__ == "__main__":
    main()
