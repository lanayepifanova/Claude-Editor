#!/bin/bash
cd /Users/lanayepifanova/Claude-Editor; T=edit/shorts-ignite-16/tools
for n in 1 2 3 4 5 6; do $T/render.sh $n; done
$T/finish.sh 1 "When power prices go negative"
$T/finish.sh 2 "Seven years to plug into the grid"
$T/finish.sh 3 "An energy-first neocloud"
$T/finish.sh 4 "Training built big, inference runs small"
$T/finish.sh 5 "The time value of compute"
$T/finish.sh 6 "Demand for AI is infinite"
