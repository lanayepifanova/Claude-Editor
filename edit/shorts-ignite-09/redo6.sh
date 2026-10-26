cd /Users/lanayepifanova/Claude-Editor
F="footage/Ignite Oct 2026/09 Pheobe Lui The Information and Carmen Li Compute Exchange.mp4"
python3 edit/reframe.py "$F" --start 702.30 --end 739.60 --out graphics/ignite-09-short6-vertical.mp4 < /dev/null > edit/shorts-ignite-09/reframe6.log 2>&1
python3 edit/preprocess.py graphics/ignite-09-short6-vertical.mp4 --out edit/analysis-ignite-09-short6 --skip-framing < /dev/null > edit/shorts-ignite-09/pre6.log 2>&1
echo redo6 done
