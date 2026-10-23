#!/usr/bin/env bash
# A4 — run the Kong et al. Fig. 7 sweep inside the A2 container (image ns3lab, ns-3.48 at /work/ns-3-dev).
#
#   2 PHY variants x M = 5..30 x seeds 1..10 = 120 runs, 33 s each (statistics 3-33 s)
#
# Prerequisites (once):
#   cd /work/ns-3-dev && git apply /work/a4/dsss-ideal-plcp.patch   # only changes behaviour when
#                                                                    # NS3_DSSS_IDEAL_PLCP is set
#   cp /work/a4/kong-edca.cc scratch/ && ./ns3 build kong-edca
# Usage (inside the container):  bash /work/a4/run_sweep.sh [parallel jobs, default 16]
set -euo pipefail
JOBS=${1:-16}
BIN=/work/ns-3-dev/build/scratch/ns3.48-kong-edca-optimized
OUT=/work/a4/runs
mkdir -p "$OUT"

for phy in 0 1; do for m in 5 10 15 20 25 30; do for s in $(seq 1 10); do
  echo "$phy $m $s"
done; done; done | xargs -P "$JOBS" -n 3 sh -c \
  "$BIN --idealPlcp=\$0 --nSta=\$1 --seed=\$2 --simTime=33 | tail -1 > $OUT/run_\$0_\$1_\$2.csv"

# merge: one header + one line per run
{ echo "M,seed,ideal_plcp,retry,S_ac3,S_ac1,D_ac3_ms,D_ac1_ms,n_ac3,n_ac1,drop_ac3,drop_ac1,Dall_ac3_ms,Dall_ac1_ms,associated"
  cat "$OUT"/run_*.csv | sort -t, -k3,3n -k1,1n -k2,2n; } > /work/a4/kong_fig7_sweep.csv
echo "wrote /work/a4/kong_fig7_sweep.csv ($(($(wc -l < /work/a4/kong_fig7_sweep.csv) - 1)) runs)"
