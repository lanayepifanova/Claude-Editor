#!/bin/zsh
# caps.sh N... : build caption project + srt for short N
cd /Users/lanayepifanova/Claude-Editor
for n in "$@"; do
python3 edit/captions_overlay.py --analysis edit/analysis-ignite-13-short$n --out graphics/ignite-13-short$n-captions \
  --res 1080x1920 --y 0.80 --maxw 0.72 --srt project/ignite-13-short$n.srt --fixes edit/fixes-ignite-13.json < /dev/null | tail -2
done
