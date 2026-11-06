#!/bin/bash
# On-board sweep: dxrun benchmark mode (max throughput) per model over NPU binding and buffer count.
# Usage (board): sweep_dxrun.sh out.csv model1.dxnn [model2.dxnn ...]   env: T=seconds per point (default 10)
out=$1; shift; T=${T:-10}
echo "model,npu_bind,buffer_count,fps" > $out
strip(){ sed 's/\x1b\[[0-9;]*m//g'; }
for m in "$@"; do
  for n in 0 1 2 3 4 5 6; do
    f=$(dxrun -m $m -b -t $T -w 5 -n $n 2>&1 | strip | grep -E "^\s*- FPS" | tail -1 | awk '{print $4}')
    echo "$(basename $m),$n,6,$f" | tee -a $out
  done
  for b in 1 2 3 12 24; do
    f=$(dxrun -m $m -b -t $T -w 5 -n 0 --buffer-count $b 2>&1 | strip | grep -E "^\s*- FPS" | tail -1 | awk '{print $4}')
    echo "$(basename $m),0,$b,$f" | tee -a $out
  done
done
echo SWEEPDONE >> $out
