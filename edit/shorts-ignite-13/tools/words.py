#!/usr/bin/env python3
"""words.py words.json t0 t1 : word-level whisper tokens in [t0,t1]"""
import sys, json
d = json.load(open(sys.argv[1])); a, b = float(sys.argv[2]), float(sys.argv[3])
print(" ".join(f"{s['offsets']['from']/1000:.2f}|{s['text'].strip()}" for s in d['transcription']
               if a <= s['offsets']['from']/1000 <= b and s['text'].strip()))
