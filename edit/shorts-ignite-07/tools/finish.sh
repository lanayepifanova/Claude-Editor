#!/bin/bash
# usage: finish.sh N "title"
cd /Users/lanayepifanova/Claude-Editor
N=$1; T="$2"; A=edit/analysis-ignite-07-short$N; C=graphics/ignite-07-short$N-cap.mov
python3 edit/check_render.py --render $C --srt project/ignite-07-short$N.srt --res 1080x1920 --y 0.75 < /dev/null > edit/shorts-ignite-07/check$N.log 2>&1; echo "check $N exit $?"; tail -4 edit/shorts-ignite-07/check$N.log
P=$(ffprobe -v error -count_frames -select_streams v:0 -show_entries stream=nb_read_frames -of csv=p=0 $A/cut_proof.mp4)
O=$(ffprobe -v error -count_frames -select_streams v:0 -show_entries stream=nb_read_frames -of csv=p=0 $C)
echo "proof $P overlay $O"
if [ "$O" -gt "$P" ]; then ffmpeg -nostdin -v error -y -i $C -frames:v $P -c copy graphics/ignite-07-short$N-cap-trim.mov && mv graphics/ignite-07-short$N-cap-trim.mov $C; echo trimmed; fi
mkdir -p output/ignite-07-shorts
nice -n 10 python3 edit/burn.py --analysis $A --overlay $C --out "output/ignite-07-shorts/$N $T.mp4" --master graphics/ignite-07-short$N-master.mp4 < /dev/null > edit/shorts-ignite-07/burn$N.log 2>&1; echo "burn $N exit $?"; tail -4 edit/shorts-ignite-07/burn$N.log
