#!/bin/bash
# usage: render.sh N
cd /Users/lanayepifanova/Claude-Editor/graphics/ignite-17-short$1-captions || exit 1
for i in 1 2 3; do
  nice -n 10 caffeinate -dimsu npx hyperframes render . --format mov -q high -f 24000/1001 --workers 1 -o ../ignite-17-short$1-cap.mov < /dev/null > ../../edit/shorts-ignite-17/render$1.log 2>&1 && { echo "render $1 ok"; exit 0; }
  echo "render $1 attempt $i failed"
done
echo "render $1 FAIL"
