#!/bin/zsh
cd /Users/lanayepifanova/Claude-Editor
F="footage/Ignite Oct 2026/13 Steven Hou Silicon Data and Liran Zvibel Weka.mp4"
D=edit/shorts-ignite-13
typeset -A IN OUT
IN=(1 738.90 2 308.55 3 244.25 4 169.55 5 490.22 6 444.65)
OUT=(1 793.12 2 357.60 3 292.10 4 223.00 5 542.95 6 489.55)
for n in "$@"; do
  caffeinate -dimsu nice -n 10 python3 edit/reframe.py "$F" --start ${IN[$n]} --end ${OUT[$n]} --out graphics/ignite-13-short$n-vertical.mp4 > $D/reframe$n.log 2>&1 < /dev/null
  echo "reframe $n exit $?"
  caffeinate -dimsu nice -n 10 python3 edit/preprocess.py graphics/ignite-13-short$n-vertical.mp4 --out edit/analysis-ignite-13-short$n --skip-framing > $D/pre$n.log 2>&1 < /dev/null
  echo "pre $n exit $?"
done
