cd /Users/lanayepifanova/Claude-Editor
b(){ python3 edit/burn.py --analysis edit/analysis-ignite-09-short$1 --overlay graphics/ignite-09-short$1-captions.mov --out "output/ignite-09-shorts/$2.mp4" --master graphics/ignite-09-short$1-master.mp4 < /dev/null 2>&1 | tail -4; }
b 3 "3 Uncertainty kills business planning"
b 5 "5 Three hyperscalers to 300 neoclouds"
b 6 "6 A billion dollars of RFQ a month"
echo burns done
