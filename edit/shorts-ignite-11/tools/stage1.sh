#!/bin/zsh
cd /Users/lanayepifanova/Claude-Editor
F="footage/Ignite Oct 2026/11 Steven Hou Silicon Data and Alex Yeh SMI Cloud.mp4"
D=edit/shorts-ignite-11
typeset -A IN OUT
IN=(1 275.65 2 359.55 3 93.08 4 464.68 5 169.10 6 513.60)
OUT=(1 334.20 2 414.58 3 150.45 4 512.00 5 215.00 6 557.15)
for n in 1 2 3 4 5 6; do
  caffeinate -dimsu nice -n 10 python3 edit/reframe.py "$F" --start ${IN[$n]} --end ${OUT[$n]} --out graphics/ignite-11-short$n-vertical.mp4 > $D/reframe$n.log 2>&1 < /dev/null
  echo "reframe $n exit $?"
  caffeinate -dimsu nice -n 10 python3 edit/preprocess.py graphics/ignite-11-short$n-vertical.mp4 --out edit/analysis-ignite-11-short$n --skip-framing > $D/pre$n.log 2>&1 < /dev/null
  echo "pre $n exit $?"
done
