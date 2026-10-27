# hist.py N : envelope histogram (dB, 3dB bins) for short N
import json, sys, numpy as np
e = json.load(open(f"edit/analysis-ignite-13-short{sys.argv[1]}/envelope.json"))
v = np.array(e["values"], float); h, b = np.histogram(v, bins=np.arange(-80, 0, 3))
for c, lo in zip(h, b[:-1]): print(f"{lo:4.0f} {'#' * int(60 * c / h.max())}")
