#!/usr/bin/env python3
"""
check_render.py — verify a rendered overlay WITHOUT putting images in context.

Replaces "export a frame from Premiere and look at it", which was both unreliable
(export_frame ignores sequenceId and time) and expensive (every image persists in
context and is re-sent on every later turn).

Works by measuring the alpha channel of the rendered .mov: where there is ink,
how much, and whether it lines up with the cue that the SRT says should be there.

    python3 edit/check_render.py --render graphics/gpu-cap.mov \
                            --srt "project/Trading GPU Hours.srt" \
                            --res 720x1280 --band 0.18,0.34
"""
import argparse, json, re, subprocess, sys, tempfile, os
from pathlib import Path


def alpha_stats(mov, t, w, h, band):
    """Return (ink_fraction_in_band, ink_fraction_outside_band, bbox) from alpha."""
    raw = tempfile.NamedTemporaryFile(suffix=".gray", delete=False).name
    sw, sh = 160, round(160 * h / w)
    subprocess.run(["ffmpeg", "-hide_banner", "-v", "error", "-y", "-ss", f"{t:.3f}",
                    "-i", mov, "-frames:v", "1",
                    "-vf", f"alphaextract,scale={sw}:{sh}",
                    "-pix_fmt", "gray", "-f", "rawvideo", raw], capture_output=True)
    try:
        d = open(raw, "rb").read()
    finally:
        os.unlink(raw)
    if len(d) < sw * sh:
        return None
    y0, y1 = int(band[0] * sh), int(band[1] * sh)
    inb = outb = 0
    minx, maxx, miny, maxy = sw, -1, sh, -1
    for y in range(sh):
        row = d[y * sw:(y + 1) * sw]
        for x, v in enumerate(row):
            if v > 40:
                if y0 <= y < y1:
                    inb += 1
                    minx, maxx = min(minx, x), max(maxx, x)
                    miny, maxy = min(miny, y), max(maxy, y)
                else:
                    outb += 1
    band_px = max(1, (y1 - y0) * sw)
    out_px = max(1, sh * sw - band_px)
    bbox = None if maxx < 0 else (minx / sw, miny / sh, maxx / sw, maxy / sh)
    return inb / band_px, outb / out_px, bbox


def read_srt(p):
    cues = []
    for b in Path(p).read_text().strip().split("\n\n"):
        L = b.split("\n")
        if len(L) < 3:
            continue
        a, z = L[1].split(" --> ")
        def s(ts):
            h, m, rest = ts.split(":")
            sec, ms = rest.split(",")
            return int(h) * 3600 + int(m) * 60 + int(sec) + int(ms) / 1000
        cues.append({"start": s(a), "end": s(z), "text": " ".join(L[2:])})
    return cues


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--render", required=True)
    ap.add_argument("--srt", required=True)
    ap.add_argument("--res", required=True)
    ap.add_argument("--band", default="0.18,0.34",
                    help="expected vertical band for the text, as fractions")
    ap.add_argument("--samples", type=int, default=8)
    a = ap.parse_args()

    if not Path(a.render).exists():
        sys.exit(f"render not found: {a.render}")
    w, h = (int(x) for x in a.res.lower().split("x"))
    band = tuple(float(x) for x in a.band.split(","))
    cues = read_srt(a.srt)
    if not cues:
        sys.exit("no cues in srt")

    dur = float(subprocess.run(["ffprobe", "-v", "error", "-show_entries",
                                "format=duration", "-of", "csv=p=0", a.render],
                               capture_output=True, text=True).stdout.strip())

    problems, notes = [], []
    # sample the middle of evenly-spaced cues, plus every gap between cues
    step = max(1, len(cues) // a.samples)
    checked = 0
    for c in cues[::step]:
        t = (c["start"] + c["end"]) / 2
        if t >= dur:
            continue
        st = alpha_stats(a.render, t, w, h, band)
        checked += 1
        if st is None:
            problems.append(f"could not read frame at {t:.2f}s"); continue
        inb, outb, bbox = st
        if inb < 0.002:
            problems.append(f"{t:6.2f}s  NO INK where \"{c['text'][:28]}\" should be")
        elif outb > 0.004:
            problems.append(f"{t:6.2f}s  ink OUTSIDE the caption band "
                            f"({outb*100:.1f}% of the rest of the frame)")
        else:
            cx = (bbox[0] + bbox[2]) / 2 if bbox else 0
            wfrac = (bbox[2] - bbox[0]) if bbox else 0
            off = abs(cx - 0.5)
            flag = "  <- not centred" if off > 0.06 else ""
            notes.append(f"{t:6.2f}s  ink {inb*100:4.1f}%  width {wfrac*100:4.1f}%  "
                         f"centre {cx:.2f}{flag}  \"{c['text'][:26]}\"")

    # a gap between cues should be empty
    gaps = 0
    for x, y in zip(cues, cues[1:]):
        g = y["start"] - x["end"]
        if g > 0.25:
            t = x["end"] + g / 2
            st = alpha_stats(a.render, t, w, h, band)
            if st and st[0] > 0.002:
                problems.append(f"{t:6.2f}s  ink present during a {g:.2f}s gap "
                                f"between cues")
            gaps += 1

    print(f"{Path(a.render).name} · {dur:.2f}s · {len(cues)} cues · "
          f"{checked} sampled · {gaps} gaps checked\n")
    for n in notes:
        print("  ·", n)
    print()
    if problems:
        for p in problems:
            print("  ✗", p)
        print(f"\n{len(problems)} problem(s)")
        sys.exit(1)
    print("  ✓ ink present for every sampled cue, inside the band, nothing in the gaps")


if __name__ == "__main__":
    main()
