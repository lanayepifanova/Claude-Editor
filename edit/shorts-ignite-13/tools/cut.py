#!/usr/bin/env python3
"""cut.py N : cut transcript text of short N, plus removed % and duration"""
import json, sys
a = f"edit/analysis-ignite-13-short{sys.argv[1]}"
d = json.load(open(f"{a}/transcript.json")); s = json.load(open(f"{a}/silence.json"))
w = d["words"]
print(f"short{sys.argv[1]}: {s['source_duration']} -> {s['cut_duration']}s ({s['removed_pct']}% removed), {len(w)} words")
print(" ".join(x["w"] if isinstance(x, dict) else str(x) for x in w))
print("first:", w[:3]); print("last:", w[-3:])
