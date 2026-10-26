cd /Users/lanayepifanova/Claude-Editor
F="footage/Ignite Oct 2026/10 Pheobe Lui The Information and Steven Hou Silcom Data.mp4"
while read n a b; do
  python3 edit/reframe.py "$F" --start $a --end $b --out graphics/ignite-10-short$n-vertical.mp4 < /dev/null > edit/shorts-ignite-10/reframe$n.log 2>&1 || echo "reframe $n FAIL"
  python3 edit/preprocess.py graphics/ignite-10-short$n-vertical.mp4 --out edit/analysis-ignite-10-short$n --skip-framing < /dev/null > edit/shorts-ignite-10/pre$n.log 2>&1 || echo "pre $n FAIL"
  echo "short $n done"
done < edit/shorts-ignite-10/ranges.txt
