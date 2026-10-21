#!/usr/bin/env python3
"""logo_card.py OUT W H COLS ROWS BOXW BOXH logo1 [logo2 ...] — official logo files laid
on a flat white card in a grid, each fitted (aspect kept) inside BOXWxBOXH and centred
in its cell. Alpha-composited over white; the card is opaque so it takes the plate frame."""
import subprocess, sys
import numpy as np
out, W, H, C, R, BW, BH = sys.argv[1], *map(int, sys.argv[2:8]); logos = sys.argv[8:]
def load(p, bw, bh):
    wh = subprocess.run(["ffprobe","-v","error","-select_streams","v:0","-show_entries","stream=width,height","-of","csv=p=0",p],capture_output=True,text=True).stdout.split(",")
    w, h = int(wh[0]), int(wh[1]); s = min(bw / w, bh / h); nw, nh = round(w * s), round(h * s)
    raw = subprocess.run(["ffmpeg","-v","error","-i",p,"-vf",f"scale={nw}:{nh}:flags=lanczos","-f","rawvideo","-pix_fmt","rgba","-"],capture_output=True).stdout
    return np.frombuffer(raw, np.uint8).reshape(nh, nw, 4).astype(np.float32)
card = np.full((H, W, 3), 255.0)
cw, ch = W / C, H / R
for i, p in enumerate(logos):
    a = load(p, BW, BH); h, w = a.shape[:2]
    cx, cy = (i % C + 0.5) * cw, (i // C + 0.5) * ch
    x, y = round(cx - w / 2), round(cy - h / 2)
    al = a[..., 3:4] / 255.0
    card[y:y+h, x:x+w] = a[..., :3] * al + card[y:y+h, x:x+w] * (1 - al)
p = subprocess.Popen(["ffmpeg","-v","error","-y","-f","rawvideo","-pix_fmt","rgb24","-s",f"{W}x{H}","-i","-",out],stdin=subprocess.PIPE)
p.communicate(np.clip(card,0,255).astype(np.uint8).tobytes())
