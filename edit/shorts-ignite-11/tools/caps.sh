#!/bin/zsh
# caps.sh N : build caption project + srt for short N, print review
cd /Users/lanayepifanova/Claude-Editor
n=$1
python3 edit/captions_overlay.py --analysis edit/analysis-ignite-11-short$n --out graphics/ignite-11-short$n-captions \
  --res 1080x1920 --y 0.65 --maxw 0.72 --srt project/ignite-11-short$n.srt --fixes edit/fixes-ignite-11.json < /dev/null
