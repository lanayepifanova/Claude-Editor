cd /Users/lanayepifanova/Claude-Editor
for n in "$@"; do
  for try in 1 2 3; do
    (cd graphics/ignite-09-short$n-captions && npx hyperframes render . --format mov -q high -f 24000/1001 --workers 1 -o ../ignite-09-short$n-captions.mov < /dev/null > ../../edit/shorts-ignite-09/render$n.log 2>&1)
    [ -s graphics/ignite-09-short$n-captions.mov ] && break
  done
  echo rendered $n
done
