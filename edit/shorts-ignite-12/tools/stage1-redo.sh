#!/bin/bash
cd /Users/lanayepifanova/Claude-Editor
F="footage/Ignite Oct 2026/12 Steven Hou Silicon Data and Aravindh Srikumar Upscale AI.mp4"
while read n a b; do
  nice -n 10 python3 edit/reframe.py "$F" --start $a --end $b --out graphics/ignite-12-short$n-vertical.mp4 < /dev/null > edit/shorts-ignite-12/reframe$n.log 2>&1 || echo "reframe $n FAIL"
  nice -n 10 python3 edit/preprocess.py graphics/ignite-12-short$n-vertical.mp4 --out edit/analysis-ignite-12-short$n --skip-framing < /dev/null > edit/shorts-ignite-12/pre$n.log 2>&1 || echo "pre $n FAIL"
  echo "short $n done"
done < edit/shorts-ignite-12/ranges-redo.txt
