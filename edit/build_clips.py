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
#
# Holds are 3.0-4.2s here, not the 1.8-3.2s in the locked table: she watched the
# first pass and said the skip was too fast, "I need like 3-5 seconds for each
# video clip". Fewer, longer beats — 11 instead of 14.
CLIPS = [
    ("neuron label",   1,  1.50,  5.60, 3.90, 786, None),
    ("cortical pong",  3,  0.00,  4.82, 3.80, 752, None),
    ("cl1 device",     4,  2.00,  7.20, 3.90, 752, None),
    # the whole slide is a white rectangle of tiny labels at plate size — crop to
    # the neural-progenitor -> neuron path, which is the bit the line is about
    ("stem cells",     5,  0.30,  5.50, 3.90, 786, "560:310:300:140"),
    ("lab hands",      4,  8.80, 15.00, 4.15, 752, None),
    # THE only place the black neural-network explainer is allowed. Her note:
    # "the black neural network should be put only for the neural network
    # section" — so it lands on "access to a living neural network that can
    # adapt and learn from feedback" and nowhere else. The span runs into the
    # pi-creatures asking "How does training work?", which is the adapt-and-learn
    # half of that line.
    ("neural network", 2, 26.50, 33.00, 4.10, 786, None),
    ("brain rotate",   1,  8.00, 13.00, 3.10, 786, None),
    ("neurons firing", 1, 43.00, 49.00, 3.90, 786, None),
    # same white-rectangle problem — crop to the one labelled colonies panel
    ("dual smad",      5, 15.00, 27.00, 4.65, 786, "640:355:490:105"),
    ("mea chip",       4,  0.00,  3.50, 3.15, 752, None),
    ("culture dish",   4, 15.30, 19.20, 3.80, 752, None),
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
