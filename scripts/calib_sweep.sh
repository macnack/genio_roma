#!/bin/bash
# Calibration-subset sensitivity sweep: for model tag (A|B) and seeds, build with DX-COM 2.4.1 (Python API, ema, N images from a seeded
# subset), push the .dxnn to the board, evaluate 4000 images with eval_dx_board.py, pull the outputs, delete the model on the board.
# usage: calib_sweep.sh "A B" "0 1 2 3 4" [N=100]      writes reports/acc/<tag>13_cal_s<seed>_out.npy and models/<dir>/cal_s<seed>/
set -uo pipefail
cd "$(cd "$(dirname "$0")/.." && pwd)"
TAGS=$1; SEEDS=$2; N=${3:-100}
CFG=models/B_dinov3/iqr1000/config.json
for tag in $TAGS; do
  if [ "$tag" = A ]; then DIR=models/A_fb_in1k; ONNX=$DIR/A_convnext_tiny_trace_opset13.onnx; else DIR=models/B_dinov3; ONNX=$DIR/B_convnext_tiny_trace_opset13.onnx; fi
  for s in $SEEDS; do
    sub=$(python3 scripts/make_calib_subset.py --seed $s --n $N); out=$DIR/cal_s${s}$([ "$N" != 100 ] && echo _n$N)
    name=${tag}13_cal_s${s}$([ "$N" != 100 ] && echo _n$N)
    if [ ! -f $out/*.dxnn ]; then .venv-dxcom/bin/python scripts/compile_dxnn_api.py $ONNX $out $CFG ema $N --dataset $sub > $out.log 2>&1 || { echo "$name COMPILE FAIL"; continue; }; fi
    grep -aE "Final result" $out/compiler.log | sed 's/.* - //' | sed "s/^/$name /"
    adb push $out/*.dxnn /home/ubuntu/cal.dxnn > /dev/null
    adb shell "cd /home/ubuntu && /home/ubuntu/dxenv/bin/python eval_dx_board.py --model cal.dxnn --x eval_u8.npy --out $name 2>&1 | tail -1 | cut -c1-200; rm -f cal.dxnn"
    adb pull /home/ubuntu/${name}_out.npy reports/acc/ > /dev/null && echo "$name done md5=$(md5sum $out/*.dxnn | cut -c1-12)"
  done
done
touch models/calib_sweep.done
