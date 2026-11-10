#!/bin/bash
# Evaluate existing B-tiny .dxnn builds on the 4000 eval images. usage: confirm_eval.sh "sel_s0_n500 sel_s3_n250"
set -uo pipefail; cd "$(cd "$(dirname "$0")/.." && pwd)"
for b in $1; do name=B13_$b
  adb push models/B_dinov3/$b/*.dxnn /home/ubuntu/cal.dxnn >/dev/null
  adb shell "cd /home/ubuntu && /home/ubuntu/dxenv/bin/python eval_dx_board.py --model cal.dxnn --x eval_u8.npy --out $name 2>&1 | tail -1 | cut -c1-120; rm -f cal.dxnn"
  adb pull /home/ubuntu/${name}_out.npy reports/acc/ >/dev/null
  python3 scripts/compare_acc.py reports/acc/B13_fp32_out.npy reports/acc/${name}_out.npy --feature > reports/acc/${name}_score.json
  echo "$name $(python3 -c "import json;d=json.load(open('reports/acc/${name}_score.json'));print('cos',round(d['cosine_mean'],4),'min',round(d['cosine_min'],3))")"
done; touch models/confirm_eval.done
