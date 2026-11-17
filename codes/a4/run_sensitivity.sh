#!/usr/bin/env bash
# A4 — Kong sensitivity runs for §5.2 and §5.3 (Table I PHY), inside the A2 container:
#
#   AIFS offset : AIFSN (AC3, AC1) = (1,2), (2,3), (3,4), retry 7   x M = 15, 30 x seeds 1-3 = 18 runs
#   retry limit : 2, 3, 4, 5, 7 attempts, AIFSN (2,3)               x M = 15, 30 x seeds 1-3 = 30 runs
#
# Usage (inside the container, after building kong-edca as in run_sweep.sh):
#   bash /work/a4/run_sensitivity.sh [parallel jobs, default 16]
# Writes $A4/kong_aifs_sensitivity.csv and $A4/kong_retry_sensitivity.csv.
set -euo pipefail
JOBS=${1:-16}
NS3=${NS3:-/work/ns-3-dev}
A4=${A4:-/work/a4}
BIN=$NS3/build/scratch/ns3.48-kong-edca-optimized
OUT=$A4/sens_runs
mkdir -p "$OUT"

{ for a in "1 2" "2 3" "3 4"; do for m in 15 30; do for s in 1 2 3; do echo "aifs $a 7 $m $s"; done; done; done
  for r in 2 3 4 5 7; do for m in 15 30; do for s in 1 2 3; do echo "retry 2 3 $r $m $s"; done; done; done
} | xargs -P "$JOBS" -n 6 sh -c \
  "f=$OUT/\$0_\$1_\$2_\$3_\$4_\$5.csv; [ -s \$f ] ||
   { line=\$($BIN --idealPlcp=1 --aifsnAc3=\$1 --aifsnAc1=\$2 --retryLimit=\$3 --nSta=\$4 --seed=\$5 --simTime=33 | tail -1);
     if [ \$0 = aifs ]; then echo \"\$1,\$2,\$line\"; else echo \"\$line\"; fi > \$f; }"

H="M,seed,ideal_plcp,retry,S_ac3,S_ac1,D_ac3_ms,D_ac1_ms,n_ac3,n_ac1,drop_ac3,drop_ac1,Dall_ac3_ms,Dall_ac1_ms,associated"
{ echo "aifsn_ac3,aifsn_ac1,$H"; cat "$OUT"/aifs_*.csv | sort -t, -k1,1n -k3,3n -k4,4n; } > "$A4/kong_aifs_sensitivity.csv"
{ echo "$H"; cat "$OUT"/retry_*.csv | sort -t, -k1,1n -k4,4n -k2,2n; } > "$A4/kong_retry_sensitivity.csv"
echo "wrote $A4/kong_aifs_sensitivity.csv ($(($(wc -l < "$A4/kong_aifs_sensitivity.csv") - 1)) runs)," \
     "$A4/kong_retry_sensitivity.csv ($(($(wc -l < "$A4/kong_retry_sensitivity.csv") - 1)) runs)"
