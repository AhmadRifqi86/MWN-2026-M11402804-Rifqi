#!/usr/bin/env bash
# A4 — run the Kong et al. Fig. 7 sweep inside the A2 container (image ns3lab, ns-3.48 at /work/ns-3-dev).
#
#   3 variants (802.11b PHY / Table I PHY, retry limit 7 attempts; Table I PHY, 4 attempts)
#   x M = 5..30 x seeds 1..10 = 180 runs, 33 s each (statistics 3-33 s)
#
# Prerequisites (once):
#   cd /work/ns-3-dev && git apply /work/a4/dsss-ideal-plcp.patch   # only changes behaviour when
#                                                                    # NS3_DSSS_IDEAL_PLCP is set
#   cp /work/a4/kong-edca.cc scratch/ && ./ns3 build kong-edca
# Usage (inside the container):  bash /work/a4/run_sweep.sh [parallel jobs, default 16]
# Runs whose CSV already exists in $OUT are skipped, so an interrupted sweep can be resumed.
set -euo pipefail
JOBS=${1:-16}
NS3=${NS3:-/work/ns-3-dev}   # ns-3 tree (override to use another build)
A4=${A4:-/work/a4}           # where per-run files and the merged CSV go
BIN=$NS3/build/scratch/ns3.48-kong-edca-optimized
OUT=$A4/runs
mkdir -p "$OUT"

for v in "0 7" "1 7" "1 4"; do for m in 5 10 15 20 25 30; do for s in $(seq 1 10); do
  echo "$v $m $s"
done; done; done | xargs -P "$JOBS" -n 4 sh -c \
  "f=$OUT/run_\$0_r\$1_\$2_\$3.csv; [ -s \$f ] ||
   $BIN --idealPlcp=\$0 --retryLimit=\$1 --nSta=\$2 --seed=\$3 --simTime=33 | tail -1 > \$f"

# merge: one header + one line per run
{ echo "M,seed,ideal_plcp,retry,S_ac3,S_ac1,D_ac3_ms,D_ac1_ms,n_ac3,n_ac1,drop_ac3,drop_ac1,Dall_ac3_ms,Dall_ac1_ms,associated"
  cat "$OUT"/run_*.csv | sort -t, -k3,3n -k4,4nr -k1,1n -k2,2n; } > $A4/kong_fig7_sweep.csv
echo "wrote $A4/kong_fig7_sweep.csv ($(($(wc -l < $A4/kong_fig7_sweep.csv) - 1)) runs)"
