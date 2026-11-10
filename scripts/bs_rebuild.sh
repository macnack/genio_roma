#!/bin/bash
# B-small DX-M1 rebuilds with the API (ema) from the 'src' half of the calib pool; evaluate on the 4000 eval images.
set -uo pipefail; cd "$(cd "$(dirname "$0")/.." && pwd)"
ONNX=models/BS_dinov3_small/BS_convnext_small_trace_opset13.onnx; CFG=models/B_dinov3/iqr1000/config.json
for spec in "3 100" "0 500"; do set -- $spec; s=$1; N=$2; name=BS13_sel_s${s}_n${N}; out=models/BS_dinov3_small/sel_s${s}_n${N}
  sub=$(python3 scripts/make_calib_subset.py --seed $s --n $N --pool data/imagenet_subset/calib_split/src)
  .venv-dxcom/bin/python scripts/compile_dxnn_api.py $ONNX $out $CFG ema $N --dataset $sub > $out.log 2>&1 || { echo "$name COMPILE FAIL"; continue; }
  grep -aE "Final result" $out/compiler.log | sed 's/.* - //' | sed "s/^/$name /"
  adb push $out/*.dxnn /home/ubuntu/cal.dxnn >/dev/null
  adb shell "cd /home/ubuntu && /home/ubuntu/dxenv/bin/python eval_dx_board.py --model cal.dxnn --x eval_u8.npy --out $name 2>&1 | tail -1 | cut -c1-200; rm -f cal.dxnn"
  adb pull /home/ubuntu/${name}_out.npy reports/acc/ >/dev/null
  python3 scripts/compare_acc.py reports/acc/BS13_fp32_out.npy reports/acc/${name}_out.npy --feature > reports/acc/${name}_score.json
  echo "$name $(python3 -c "import json;d=json.load(open('reports/acc/${name}_score.json'));print('cos',round(d['cosine_mean'],4),'min',round(d['cosine_min'],3))")"
  find $out -mindepth 1 ! -name '*.dxnn' ! -name 'compiler.log' ! -name config_run.json -exec rm -rf {} + 2>/dev/null
done; touch models/bs_rebuild.done
