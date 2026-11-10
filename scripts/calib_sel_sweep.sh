#!/bin/bash
# Held-out calibration-subset search for B-tiny: subsets of N images drawn (seeded) from the 500-image 'src' half of the calib pool,
# scored on the disjoint 500-image 'sel' half (feature cosine vs FP32, reference reports/acc/Bsel_fp32_out.npy). Never touches the 4000 eval images.
# usage: calib_sel_sweep.sh "0 1 2" [N=100]   -> reports/acc/Bsel_s<seed>_n<N>_{out.npy,score.json}, models/B_dinov3/sel_s<seed>_n<N>/*.dxnn
set -uo pipefail
cd "$(cd "$(dirname "$0")/.." && pwd)"
SEEDS=$1; N=${2:-100}; CFG=models/B_dinov3/iqr1000/config.json; ONNX=models/B_dinov3/B_convnext_tiny_trace_opset13.onnx
for s in $SEEDS; do
  name=Bsel_s${s}_n${N}; out=models/B_dinov3/sel_s${s}_n${N}
  sub=$(python3 scripts/make_calib_subset.py --seed $s --n $N --pool data/imagenet_subset/calib_split/src)
  if ! ls $out/*.dxnn >/dev/null 2>&1; then .venv-dxcom/bin/python scripts/compile_dxnn_api.py $ONNX $out $CFG ema $N --dataset $sub > $out.log 2>&1 || { echo "$name COMPILE FAIL"; continue; }; fi
  grep -aE "Final result" $out/compiler.log | sed 's/.* - //' | sed "s/^/$name /"
  adb push $out/*.dxnn /home/ubuntu/cal.dxnn > /dev/null
  adb shell "cd /home/ubuntu && /home/ubuntu/dxenv/bin/python eval_dx_board.py --model cal.dxnn --x sel_u8.npy --out $name 2>&1 | tail -1 | cut -c1-160; rm -f cal.dxnn"
  adb pull /home/ubuntu/${name}_out.npy reports/acc/ > /dev/null
  python3 scripts/compare_acc.py reports/acc/Bsel_fp32_out.npy reports/acc/${name}_out.npy --feature > reports/acc/${name}_score.json
  echo "$name $(python3 -c "import json;d=json.load(open('reports/acc/${name}_score.json'));print('cos',round(d['cosine_mean'],4),'min',round(d['cosine_min'],3))") md5=$(md5sum $out/*.dxnn | cut -c1-12)"
  find $out -mindepth 1 ! -name '*.dxnn' ! -name 'compiler.log' ! -name config_run.json -exec rm -rf {} + 2>/dev/null
done
touch models/calib_sel_sweep.$(echo $SEEDS | tr ' ' _)_n$N.done
