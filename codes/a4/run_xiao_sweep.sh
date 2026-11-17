#!/usr/bin/env bash
# A4 — run the Xiao (IEEE TWC 2005) sweeps inside the A2 container (image ns3lab, ns-3.48 at
# /work/ns-3-dev), 10 seeds per point, 20 s of statistics each:
#
#   fig2-4 : combined scheme, n0 = n1 = 5..40 (Table I is n = 10 and 30)     8 points
#   fig5   : n = 10, W1,0 = 16..56, W0,0 = 16, sigma = 2, L = 7               6 points
#   fig7   : n = 10, sigma1 = 1.6..2.6, W = 16, sigma0 = 2, L = 7             6 points
#   fig9   : n = 10, L1 = 0..8, W = 16, sigma = 2, L0 = 8                     9 points
#   = 29 points x 10 seeds = 290 runs
#
# Prerequisites (once):
#   cd /work/ns-3-dev && git apply /work/a4/txop-cw-growth.patch
#   cp /work/a4/xiao-priority.cc scratch/ && ./ns3 build xiao-priority
# Usage (inside the container):  bash /work/a4/run_xiao_sweep.sh [parallel jobs, default 16]
# Runs whose CSV already exists in $OUT are skipped, so an interrupted sweep can be resumed.
set -euo pipefail
JOBS=${1:-16}
NS3=${NS3:-/work/ns-3-dev}   # ns-3 tree (override to use another build)
A4=${A4:-/work/a4}           # where per-run files and the merged CSV go
BIN=$NS3/build/scratch/ns3.48-xiao-priority-optimized
OUT=$A4/xiao_runs
mkdir -p "$OUT"

{
  for n in 5 10 15 20 25 30 35 40; do echo "fig2-4 --n0=$n --n1=$n"; done
  for w in 16 24 32 40 48 56; do echo "fig5 --w00=16 --w10=$w --sigma0=2 --sigma1=2 --L0=7 --L1=7"; done
  for s in 1.6 1.8 2.0 2.2 2.4 2.6; do echo "fig7 --w00=16 --w10=16 --sigma0=2 --sigma1=$s --L0=7 --L1=7"; done
  for l in 0 1 2 3 4 5 6 7 8; do echo "fig9 --w00=16 --w10=16 --sigma0=2 --sigma1=2 --L0=8 --L1=$l"; done
} | while read -r exp args; do
  for seed in $(seq 1 10); do echo "$exp $seed $args"; done
done | xargs -P "$JOBS" -L 1 sh -c \
  'exp=$0; seed=$1; shift; f='"$OUT"'/$exp-$(echo "$@" | tr -cs "A-Za-z0-9." "_")-$seed.csv;
   [ -s "$f" ] || echo "$exp,$('"$BIN"' --seed=$seed "$@" | tail -1)" > "$f"'

# merge: one header + one line per run
{ echo "exp,n0,n1,seed,W0_0,W0_1,sigma0,sigma1,L0,L1,S0,S1,D0_ms,D1_ms,P0,P1,acked0,acked1,drop0,drop1,associated"
  cat "$OUT"/*.csv | sort -t, -k1,1 -k2,2n -k6,6n -k8,8n -k10,10n -k4,4n; } > $A4/xiao_sweep.csv
echo "wrote $A4/xiao_sweep.csv ($(($(wc -l < $A4/xiao_sweep.csv) - 1)) runs)"
