#!/bin/zsh
# render caption overlay, check, trim to proof frame count, burn — strictly sequential
cd /Users/lanayepifanova/Claude-Editor
typeset -A T
T=(1 "90 to 98 percent cache hit is 5x the tokens" 2 "inference is about economics" 3 "only two or three labs will win" 4 "the crazy GPU guys were a detour" 5 "a single off-taker gets the better deal" 6 "the shortage means everyone is winning")
mkdir -p output/ignite-13-shorts
for n in "$@"; do
  A=edit/analysis-ignite-13-short$n; O=graphics/ignite-13-short$n-cap.mov
  for try in 1 2 3; do
    (cd graphics/ignite-13-short$n-captions && caffeinate -dimsu nice -n 10 npx hyperframes render . --format mov -q high -f 24000/1001 --workers 1 -o ../ignite-13-short$n-cap.mov) > graphics/ignite-13-short$n-cap.log 2>&1 < /dev/null && [ -s $O ] && break
  done
  echo "render $n try $try"
  python3 edit/check_render.py --render $O --srt project/ignite-13-short$n.srt --res 1080x1920 --y 0.80 < /dev/null 2>&1 | tail -3
  pf=$(ffprobe -v error -count_frames -select_streams v:0 -show_entries stream=nb_read_frames -of csv=p=0 $A/cut_proof.mp4 < /dev/null)
  of=$(ffprobe -v error -count_frames -select_streams v:0 -show_entries stream=nb_read_frames -of csv=p=0 $O < /dev/null)
  echo "short$n proof $pf overlay $of"
  if [ "$of" -gt "$pf" ]; then
    nice -n 10 ffmpeg -nostdin -v error -y -i $O -frames:v $pf -c copy graphics/ignite-13-short$n-cap-trim.mov < /dev/null && mv graphics/ignite-13-short$n-cap-trim.mov $O
    echo "trimmed to $pf"
  fi
  caffeinate -dimsu nice -n 10 python3 edit/burn.py --analysis $A --overlay $O --out "output/ignite-13-shorts/$n ${T[$n]}.mp4" --master graphics/ignite-13-short$n-master.mp4 < /dev/null 2>&1 | tail -4
  echo "burn $n done"
done
