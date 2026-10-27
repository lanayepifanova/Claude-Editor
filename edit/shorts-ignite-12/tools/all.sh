#!/bin/bash
cd /Users/lanayepifanova/Claude-Editor; T=edit/shorts-ignite-12/tools
for n in 1 2 3 4 5 6; do $T/render.sh $n; done
$T/finish.sh 1 "Compute grew 25X, the network 8X"
$T/finish.sh 2 "Does Upscale compete with NVIDIA"
$T/finish.sh 3 "Networking for AI and nothing else"
$T/finish.sh 4 "The network is the bottleneck"
$T/finish.sh 5 "Ten generations of ASICs"
$T/finish.sh 6 "Pure-play AI networking"
