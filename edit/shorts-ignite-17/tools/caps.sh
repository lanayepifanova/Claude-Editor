#!/bin/bash
# usage: caps.sh N -> captions composition + srt + review for short N
cd /Users/lanayepifanova/Claude-Editor
N=$1
python3 edit/captions_overlay.py --analysis edit/analysis-ignite-17-short$N --out graphics/ignite-17-short$N-captions \
  --res 1080x1920 --y 0.75 --maxw 0.72 --srt project/ignite-17-short$N.srt --fixes edit/fixes-ignite-17.json < /dev/null > edit/shorts-ignite-17/cap$N.log 2>&1 || echo "cap $N FAIL"
