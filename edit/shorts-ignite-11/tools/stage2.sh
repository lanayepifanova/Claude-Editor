#!/bin/zsh
# render caption overlays for the given shorts, sequentially, retry up to 3x
cd /Users/lanayepifanova/Claude-Editor
for n in "$@"; do
  for try in 1 2 3; do
    (cd graphics/ignite-11-short$n-captions && caffeinate -dimsu nice -n 10 npx hyperframes render . --format mov -q high -f 24000/1001 --workers 1 -o ../ignite-11-short$n-cap.mov) > graphics/ignite-11-short$n-cap.log 2>&1 < /dev/null && [ -s graphics/ignite-11-short$n-cap.mov ] && break
  done
  echo "render $n try $try exit $?"
done
