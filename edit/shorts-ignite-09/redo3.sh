cd /Users/lanayepifanova/Claude-Editor
until grep -q "done 6" edit/shorts-ignite-09/all.log; do sleep 15; done
F="footage/Ignite Oct 2026/09 Pheobe Lui The Information and Carmen Li Compute Exchange.mp4"
python3 edit/reframe.py "$F" --start 561.80 --end 618.95 --out graphics/ignite-09-short3-vertical.mp4 < /dev/null > edit/shorts-ignite-09/reframe3.log 2>&1
python3 edit/preprocess.py graphics/ignite-09-short3-vertical.mp4 --out edit/analysis-ignite-09-short3 --skip-framing < /dev/null > edit/shorts-ignite-09/pre3.log 2>&1
echo redo3 done
