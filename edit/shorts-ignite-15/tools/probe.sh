#!/bin/bash
# usage: probe.sh a b  -> whisper text of original audio a..b (checks head/tail words)
cd /Users/lanayepifanova/Claude-Editor; P=edit/shorts-ignite-15/probe
mkdir -p $P; ffmpeg -nostdin -v error -y -ss $1 -to $2 -i edit/shorts-ignite-15/audio.wav $P/p.wav
whisper-cli -m ~/.cache/whisper/ggml-small.en.bin -f $P/p.wav -nt -np 2>/dev/null < /dev/null | tr '\n' ' '; echo
