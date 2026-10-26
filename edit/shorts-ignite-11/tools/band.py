#!/usr/bin/env python3
"""band.py video.mp4 : per caption y, share of sampled frames whose text band is >25% white."""
import sys, subprocess, numpy as np
W, H = 108, 192
raw = subprocess.run(["nice", "-n", "10", "ffmpeg", "-nostdin", "-v", "error", "-i", sys.argv[1], "-vf",
                      f"fps=2,scale={W}:{H},format=gray", "-f", "rawvideo", "-"],
                     capture_output=True, stdin=subprocess.DEVNULL).stdout
f = np.frombuffer(raw, np.uint8).reshape(-1, H, W)
for y in (0.6, 0.65, 0.7, 0.75):
    a, b = int((y - 0.03) * H), int((y + 0.03) * H)
    band = f[:, a:b, int(W * .14):int(W * .86)]
    share = (band > 200).mean(axis=(1, 2))
    print(f"y {y}: {100 * (share > 0.25).mean():.0f}% frames >25% white, mean white {100 * share.mean():.1f}%")
