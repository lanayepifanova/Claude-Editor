#!/usr/bin/env python3
"""Print 50ms RMS dB around given times in audio.wav: env.py t1 t2 ... (window +-1.5s)"""
import sys, wave, numpy as np
w = wave.open(sys.argv[1]); sr = w.getframerate()
x = np.frombuffer(w.readframes(w.getnframes()), np.int16).astype(float) / 32768
for t in map(float, sys.argv[2:]):
    out = []
    for k in np.arange(t - 1.5, t + 1.5, 0.05):
        a = x[int(k * sr):int((k + 0.05) * sr)]
        db = 20 * np.log10(np.sqrt((a ** 2).mean()) + 1e-9)
        out.append(f"{k:.2f}:{db:.0f}")
    print(t, " ".join(out)); print()
