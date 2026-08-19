#!/usr/bin/env python3
"""
prep_photos.py — turn Lana's labelled source images into overlay-ready plates.

Her assets are named for the words they land on ("ai agent.webp", "seo tool.png").
Most are line art on a white background, and her room is white — so knocking the
background out lets the artwork sit *in* the room instead of reading as a pasted
screenshot. That was the A/B: raw showed an obvious white rectangle, knocked out
did not. It also matches the standing rule that ink sits directly on the footage
with no boxes.

Not everything should be knocked out. Assets that carry their own dark or
coloured ground (a code screenshot, a screen recording) are left alone — removing
"white" from them does nothing useful and risks eating content.

    python3 edit/prep_photos.py --deck firecrawl

Writes graphics/<deck>-photos/ plus a manifest of what was done to each file.
"""
import argparse, json, os, subprocess, sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parent.parent

# per-asset treatment. "knock" removes a light background; hi/lo bracket the
# ramp so anti-aliased edges keep a soft edge instead of fringing.
#   passthrough — already has usable alpha
#   raw         — has its own ground; leave it be
DECKS = {
    "firecrawl": {
        "src": "graphics/Firecrawl-png",
        "assets": {
            "website.jpeg":            {"mode": "knock"},
            "firecrawl.png":           {"mode": "passthrough"},
            "ai agent.webp":           {"mode": "knock"},
            # flat #D9D9D9 ground (measured, not guessed) sits above the
            # default ramp, so the default bracket leaves it 77% opaque
            "seo tool.png":            {"mode": "knock", "hi": 219, "lo": 198},
            "data extraction.jpeg":    {"mode": "knock"},
            "structured dataset.webp": {"mode": "raw"},
            "product launches.mov":    {"mode": "raw"},
            "love firecrawl.webp":     {"mode": "knock"},
            "student program.png":     {"mode": "knock"},
        },
    },
    "sonytsmc": {
        "src": "graphics/Sonytsmc-png",
        "assets": {
            # logos and white-ground diagrams knock out, so the mark sits ON the
            # footage instead of reading as a pasted white rectangle
            "tsmc.png":                       {"mode": "knock"},
            "sony.jpeg":                      {"mode": "knock"},
            # these two keep their white card: knocking it out drops the
            # anti-aliased label text ("Contact Pads", "Sensor Chip") to a grey
            # that dies over her hair. The diagram body looked better knocked,
            # but unreadable labels make the diagram pointless — legibility wins.
            "image sensor 2.png":             {"mode": "raw"},
            "image sensor 3.png":             {"mode": "raw"},
            "chip stacking.jpeg":             {"mode": "knock"},
            # the three source screenshots keep their white card — they read as
            # receipts, and knocking them would strip the highlight spans to
            # semi-transparent blobs and leave the grey source chips floating
            "largest contract chipmaker.png": {"mode": "raw"},
            "news piece.png":                 {"mode": "raw"},
            "news piece 2.png":               {"mode": "raw"},
            # everything else carries its own ground
            "chip factory.jpeg":              {"mode": "raw"},
            "chip maker.jpeg":                {"mode": "raw"},
            "copper connections.jpg":         {"mode": "raw"},
            "chipmaking.jpeg":                {"mode": "raw"},
            "chipstaking 2.jpeg":             {"mode": "raw"},
            "high rise 3d chips.jpeg":        {"mode": "raw"},
            "image sensors.jpeg":             {"mode": "raw"},
            "japan.jpeg":                     {"mode": "raw"},
            "kumamoto.jpeg":                  {"mode": "raw"},
            "minority partners.png":          {"mode": "raw"},
            "mobile processors.jpg":          {"mode": "raw"},
            "semiconductor.jpeg":             {"mode": "raw"},
        },
    },
}

HI, LO = 246.0, 228.0


def read_rgba(path):
    """Decode to HxWx4. ffmpeg cannot decode every webp variant, so fall back
    to macOS sips, which handles the ones it chokes on."""
    def probe(p):
        r = subprocess.run(["ffprobe", "-v", "error", "-select_streams", "v:0",
                            "-show_entries", "stream=width,height", "-of", "csv=p=0", str(p)],
                           capture_output=True, text=True)
        return [int(x) for x in r.stdout.strip().split("\n")[0].split(",")[:2]]

    raw = subprocess.run(["ffmpeg", "-v", "error", "-i", str(path),
                          "-f", "rawvideo", "-pix_fmt", "rgba", "-"],
                         capture_output=True).stdout
    w, h = probe(path)
    if len(raw) != w * h * 4:
        tmp = Path(os.environ.get("TMPDIR", "/tmp")) / "prep_photos_tmp.png"
        subprocess.run(["sips", "-s", "format", "png", str(path), "--out", str(tmp)],
                       capture_output=True)
        raw = subprocess.run(["ffmpeg", "-v", "error", "-i", str(tmp),
                              "-f", "rawvideo", "-pix_fmt", "rgba", "-"],
                             capture_output=True).stdout
        w, h = probe(tmp)
    return np.frombuffer(raw, np.uint8).reshape(h, w, 4).astype(np.float32)


def write_rgba(a, path):
    h, w, _ = a.shape
    p = subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo",
                          "-pix_fmt", "rgba", "-s", f"{w}x{h}", "-i", "-", str(path)],
                         stdin=subprocess.PIPE)
    p.communicate(np.clip(a, 0, 255).astype(np.uint8).tobytes())


def knock(a, hi=HI, lo=LO):
    """Light background -> transparent, then trim to what is left."""
    mn = a[..., :3].min(axis=2)
    alpha = np.clip((hi - mn) / (hi - lo), 0, 1) * 255.0
    out = a.copy()
    out[..., 3] = np.minimum(a[..., 3], alpha)
    ys, xs = np.where(out[..., 3] > 8)
    if len(ys):
        out = out[ys.min():ys.max() + 1, xs.min():xs.max() + 1]
    return out


def trim_alpha(a):
    ys, xs = np.where(a[..., 3] > 8)
    return a[ys.min():ys.max() + 1, xs.min():xs.max() + 1] if len(ys) else a


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--deck", default="firecrawl", choices=sorted(DECKS))
    args = ap.parse_args()

    deck = DECKS[args.deck]
    src = ROOT / deck["src"]
    out_dir = ROOT / "graphics" / f"{args.deck}-photos"
    out_dir.mkdir(parents=True, exist_ok=True)

    manifest = {}
    on_disk = {f.name for f in src.iterdir() if not f.name.startswith(".")}
    known = set(deck["assets"])
    for missing in sorted(known - on_disk):
        print(f"  ! declared but not on disk: {missing}")
    for extra in sorted(on_disk - known):
        print(f"  ! on disk but not declared, skipping: {extra}")

    for name in sorted(known & on_disk):
        spec = deck["assets"][name]
        stem = Path(name).stem
        if spec["mode"] == "raw" and name.lower().endswith(".mov"):
            dst = out_dir / name
            subprocess.run(["cp", str(src / name), str(dst)], check=True)
            manifest[stem] = {"file": name, "mode": "raw-video"}
            print(f"  {stem:22s} raw video")
            continue

        a = read_rgba(src / name)
        if spec["mode"] == "knock":
            a = knock(a, spec.get("hi", HI), spec.get("lo", LO))
        elif spec["mode"] == "passthrough":
            a = trim_alpha(a)
        dst = out_dir / f"{stem}.png"
        write_rgba(a, dst)
        h, w, _ = a.shape
        manifest[stem] = {"file": dst.name, "mode": spec["mode"], "w": w, "h": h}
        print(f"  {stem:22s} {spec['mode']:12s} {w}x{h}")

    (out_dir / "photos.json").write_text(json.dumps(manifest, indent=1))
    print(f"-> {out_dir}")


if __name__ == "__main__":
    sys.exit(main())
