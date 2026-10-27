#!/bin/bash
# Local workaround: reframe.py picks the largest face, which in the 45s wide shot of short 5 is
# Steven (listening). Angela is speaking, so pin the crop on her (face x ~1330 in the wide).
cd /Users/lanayepifanova/Claude-Editor
F="footage/Ignite Oct 2026/15 Steven Hou Silicon Data and Angela Young Cerebras.mp4"
nice -n 10 ffmpeg -nostdin -v error -y -ss 202.380 -t 45.620 -i "$F" \
  -vf "crop=568:1012:'if(lt(t,45.3),1046,574)':34,scale=1080:1920:flags=lanczos,setsar=1" \
  -c:v libx264 -crf 12 -preset slow -pix_fmt yuv420p -af "loudnorm=I=-18:TP=-2:LRA=11,aresample=48000" \
  -c:a aac -b:a 320k graphics/ignite-15-short5-vertical.mp4
nice -n 10 python3 edit/preprocess.py graphics/ignite-15-short5-vertical.mp4 --out edit/analysis-ignite-15-short5 --skip-framing < /dev/null > edit/shorts-ignite-15/pre5.log 2>&1 || echo "pre 5 FAIL"
