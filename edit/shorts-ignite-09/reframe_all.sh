cd /Users/lanayepifanova/Claude-Editor
F="footage/Ignite Oct 2026/09 Pheobe Lui The Information and Carmen Li Compute Exchange.mp4"
while read n a b; do
  python3 edit/reframe.py "$F" --start $a --end $b --out graphics/ignite-09-short$n-vertical.mp4 < /dev/null > edit/shorts-ignite-09/reframe$n.log 2>&1
  python3 edit/preprocess.py graphics/ignite-09-short$n-vertical.mp4 --out edit/analysis-ignite-09-short$n --skip-framing < /dev/null > edit/shorts-ignite-09/pre$n.log 2>&1
  echo done $n
done < edit/shorts-ignite-09/clips.txt
