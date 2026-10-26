#!/bin/zsh
# check_render, trim overlay to proof frame count, burn — sequential
cd /Users/lanayepifanova/Claude-Editor
typeset -A T
T=(1 "a cloud is a glass of ice" 2 "this is pushing people" 3 "bitcoin miner to GPU cloud" 4 "delivery is a promise" 5 "they used to be called containers" 6 "boots on the ground across Asia")
mkdir -p output/ignite-11-shorts
for n in "$@"; do
  A=edit/analysis-ignite-11-short$n; O=graphics/ignite-11-short$n-cap.mov
  python3 edit/check_render.py --render $O --srt project/ignite-11-short$n.srt --res 1080x1920 --y 0.65 < /dev/null | tail -3
  pf=$(ffprobe -v error -count_frames -select_streams v:0 -show_entries stream=nb_read_frames -of csv=p=0 $A/cut_proof.mp4)
  of=$(ffprobe -v error -count_frames -select_streams v:0 -show_entries stream=nb_read_frames -of csv=p=0 $O)
  echo "short$n proof $pf overlay $of"
  if [ "$of" -gt "$pf" ]; then
    nice -n 10 ffmpeg -nostdin -v error -y -i $O -frames:v $pf -c copy graphics/ignite-11-short$n-cap-trim.mov < /dev/null && mv graphics/ignite-11-short$n-cap-trim.mov $O
    echo "trimmed to $pf"
  fi
  caffeinate -dimsu nice -n 10 python3 edit/burn.py --analysis $A --overlay $O --out "output/ignite-11-shorts/$n ${T[$n]}.mp4" --master graphics/ignite-11-short$n-master.mp4 < /dev/null 2>&1 | tail -4
  echo "burn $n exit $?"
done
