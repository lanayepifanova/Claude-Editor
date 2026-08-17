#!/usr/bin/env python3
"""
extract_panels.py — pull individual panels ("bubbles") out of the 4K slide decks
and treat them black-and-white with a single accent hue preserved.

The decks are strict grids of rounded panels on a near-black ground, so panels
are found by recursive projection: split into horizontal bands of content, then
split each band into columns, and keep the rectangles that survive. Nothing is
eyeballed and nothing is hardcoded per slide.

    python3 edit/extract_panels.py --deck firecrawl --debug
    python3 edit/extract_panels.py --deck firecrawl --crop 03-firecrawl-run.png:2

Treatment: luminance is kept as-is; pixels that carried colour are re-hued to the
deck's one accent so a tag or a diff still reads against the grey, per Lana's
"B&W but keep one accent". Red-vs-green diffs stop being distinguishable from
each other — that is the cost of one accent.
"""
import argparse, json, subprocess, sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parent.parent

DECKS = {
    "firecrawl":   {"dir": "graphics/Firecrawl-png",   "accent": (232, 122, 58),   # deck orange
                    "bg": 16.0, "row": 0.10, "col": 0.35},
    # the Browser Use deck sits darker and cooler, so its panel fills clear the
    # ground by less; detecting it with Firecrawl's thresholds drops the stat
    # tiles and the terminal pane entirely.
    "browser-use": {"dir": "graphics/Browser-use-png", "accent": (70, 150, 240),   # deck blue
                    "bg": 11.0, "row": 0.07, "col": 0.22},
}

BG_LUMA = 16.0      # ground is ~#07080C -> luma ~8; panels fill lighter than this
MIN_W_FRAC = 0.045  # ignore slivers
MIN_H_FRAC = 0.045
PAD = 2             # px of ground kept around a panel so its border survives


def read_rgb(path, width=None):
    """Decode an image to a float32 HxWx3 array via ffmpeg (no PIL here)."""
    vf = f"scale={width}:-1" if width else "null"
    probe = subprocess.run(
        ["ffprobe", "-v", "error", "-select_streams", "v:0",
         "-show_entries", "stream=width,height", "-of", "csv=p=0", str(path)],
        capture_output=True, text=True)
    sw, sh = (int(x) for x in probe.stdout.strip().split(",")[:2])
    if width:
        sh = round(sh * width / sw)
        sw = width
    raw = subprocess.run(
        ["ffmpeg", "-v", "error", "-i", str(path), "-vf", vf,
         "-f", "rawvideo", "-pix_fmt", "rgb24", "-"],
        capture_output=True).stdout
    return np.frombuffer(raw, np.uint8).reshape(sh, sw, 3).astype(np.float32)


def luma(a):
    return a[..., 0] * 0.299 + a[..., 1] * 0.587 + a[..., 2] * 0.114


def runs(mask, min_len):
    """Contiguous True runs in a 1-D boolean array, as (start, end_exclusive)."""
    out, start = [], None
    for i, v in enumerate(mask):
        if v and start is None:
            start = i
        elif not v and start is not None:
            if i - start >= min_len:
                out.append((start, i))
            start = None
    if start is not None and len(mask) - start >= min_len:
        out.append((start, len(mask)))
    return out


def find_panels(img, bg=BG_LUMA, row_t=0.10, col_t=0.35):
    """Recursive projection: horizontal bands, then columns inside each band."""
    h, w, _ = img.shape
    lit = luma(img) > bg
    panels = []
    # a row belongs to a band if a real fraction of it is lit (a panel fill),
    # which ignores the sparse rows that are only headline text
    row_hits = lit.mean(axis=1)
    for y0, y1 in runs(row_hits > row_t, int(h * MIN_H_FRAC)):
        band = lit[y0:y1]
        col_hits = band.mean(axis=0)
        for x0, x1 in runs(col_hits > col_t, int(w * MIN_W_FRAC)):
            # The band's height is the tallest panel in it, so a short tile
            # inherits a skirt of dead ground. Shrink to this column's own
            # content before keeping it.
            sub = lit[y0:y1, x0:x1]
            rows = np.where(sub.mean(axis=1) > col_t)[0]
            cols = np.where(sub.mean(axis=0) > row_t)[0]
            if rows.size == 0 or cols.size == 0:
                continue
            ty0, ty1 = y0 + int(rows[0]), y0 + int(rows[-1]) + 1
            tx0, tx1 = x0 + int(cols[0]), x0 + int(cols[-1]) + 1
            if (tx1 - tx0) < w * MIN_W_FRAC or (ty1 - ty0) < h * MIN_H_FRAC:
                continue
            panels.append((tx0, ty0, tx1 - tx0, ty1 - ty0))
    return panels


def treat(img, accent):
    """Grey by luminance, then re-hue whatever carried colour to the one accent."""
    mx = img.max(axis=2)
    mn = img.min(axis=2)
    sat = np.where(mx > 0, (mx - mn) / np.maximum(mx, 1e-6), 0.0)
    g = luma(img)
    out = np.repeat(g[..., None], 3, axis=2)
    # accent, normalised so applying it preserves the pixel's own brightness
    acc = np.array(accent, np.float32)
    acc = acc / (acc[0] * 0.299 + acc[1] * 0.587 + acc[2] * 0.114)
    tint = g[..., None] * acc[None, None, :]
    # Gate on saturation AND brightness. The deck's panel bodies are dark but
    # warm, so saturation alone tints the whole bubble brown; requiring real
    # brightness keeps bodies neutral grey and lets only tags, accent text and
    # diff markers take the accent.
    k = (np.clip((sat - 0.30) / 0.20, 0, 1) *
         np.clip((g - 55.0) / 45.0, 0, 1))[..., None]
    out = out * (1 - k) + tint * k
    return np.clip(out, 0, 255).astype(np.uint8)


def write_png(arr, path):
    h, w, _ = arr.shape
    p = subprocess.Popen(
        ["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24",
         "-s", f"{w}x{h}", "-i", "-", str(path)], stdin=subprocess.PIPE)
    p.communicate(arr.tobytes())


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--deck", required=True, choices=sorted(DECKS))
    ap.add_argument("--debug", action="store_true",
                    help="write a boxed contact sheet instead of crops")
    ap.add_argument("--out", default="")
    args = ap.parse_args()

    deck = DECKS[args.deck]
    src_dir = ROOT / deck["dir"]
    out_dir = Path(args.out) if args.out else ROOT / "graphics" / f"{args.deck}-bubbles"
    out_dir.mkdir(parents=True, exist_ok=True)

    index = {}
    for slide in sorted(src_dir.glob("*.png")):
        small = read_rgb(slide, width=960)
        panels = find_panels(small, deck.get("bg", BG_LUMA),
                             deck.get("row", 0.10), deck.get("col", 0.35))
        sx = 3840 / 960
        index[slide.name] = []
        if args.debug:
            dbg = small.copy()
            for (x, y, w, h) in panels:
                dbg[y:y + 2, x:x + w] = (255, 220, 0)
                dbg[y + h - 2:y + h, x:x + w] = (255, 220, 0)
                dbg[y:y + h, x:x + 2] = (255, 220, 0)
                dbg[y:y + h, x + w - 2:x + w] = (255, 220, 0)
            write_png(dbg.astype(np.uint8), out_dir / f"debug-{slide.name}")
        else:
            full = read_rgb(slide)
            for i, (x, y, w, h) in enumerate(panels):
                X, Y = int(x * sx) - PAD, int(y * sx) - PAD
                W, H = int(w * sx) + PAD * 2, int(h * sx) + PAD * 2
                X, Y = max(0, X), max(0, Y)
                W, H = min(W, 3840 - X), min(H, 2160 - Y)
                name = f"{slide.stem}--{i:02d}.png"
                write_png(treat(full[Y:Y + H, X:X + W], deck["accent"]), out_dir / name)
                index[slide.name].append({"file": name, "x": X, "y": Y, "w": W, "h": H})
        print(f"{slide.name:26s} {len(panels)} panels")

    if not args.debug:
        (out_dir / "panels.json").write_text(json.dumps(index, indent=1))
    print(f"-> {out_dir}")


if __name__ == "__main__":
    sys.exit(main())
