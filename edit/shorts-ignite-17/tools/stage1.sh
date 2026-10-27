#!/bin/bash
cd /Users/lanayepifanova/Claude-Editor
F="footage/Ignite Oct 2026/17 Steven Hou Silicon Data and Jasper Zhang Hyperbolic.mp4"
while read n a b; do
  nice -n 10 python3 edit/reframe.py "$F" --start $a --end $b --out graphics/ignite-17-short$n-vertical.mp4 < /dev/null > edit/shorts-ignite-17/reframe$n.log 2>&1 || echo "reframe $n FAIL"
  nice -n 10 python3 edit/preprocess.py graphics/ignite-17-short$n-vertical.mp4 --out edit/analysis-ignite-17-short$n --skip-framing < /dev/null > edit/shorts-ignite-17/pre$n.log 2>&1 || echo "pre $n FAIL"
  echo "short $n done"
done < edit/shorts-ignite-17/ranges.txt
