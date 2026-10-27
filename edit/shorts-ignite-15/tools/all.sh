#!/bin/bash
cd /Users/lanayepifanova/Claude-Editor; T=edit/shorts-ignite-15/tools
for n in 1 2 3 4 5 6; do $T/render.sh $n; done
$T/finish.sh 1 "The largest chip in the world"
$T/finish.sh 2 "Power is the new currency"
$T/finish.sh 3 "Why not just use NVIDIA GPUs"
$T/finish.sh 4 "Why a chip company runs its own cloud"
$T/finish.sh 5 "Waiting 30 seconds is a long time"
$T/finish.sh 6 "Not every chip company will survive"
