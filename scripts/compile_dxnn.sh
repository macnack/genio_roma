#!/bin/bash
# Compile an ONNX (static [1,3,224,224], input named "input") to .dxnn with DX-COM 2.4.1 using the real
# calibration images (ImageNet subset, calib split). Usage: compile_dxnn.sh model.onnx out_dir [extra dxcom flags]
# Env: CALIB_NUM (default 100), CALIB_METHOD (ema|minmax, default ema), DXCOM (default .venv-dxcom/bin/dxcom)
set -euo pipefail
ROOT=$(cd "$(dirname "$0")/.." && pwd)
ONNX=$1; OUT=$2; shift 2
DXCOM=${DXCOM:-$ROOT/.venv-dxcom/bin/dxcom}
mkdir -p "$OUT"
python3 - "$OUT/config.json" "$ROOT" "${CALIB_NUM:-100}" "${CALIB_METHOD:-ema}" <<'PY'
import json, sys
out, root, n, method = sys.argv[1], sys.argv[2], int(sys.argv[3]), sys.argv[4]
# preprocessing block follows the official DEEPX sample config (MobileNetV2-1.json); resize/crop as ConvNeXt eval
cfg = {"inputs": {"input": [1, 3, 224, 224]}, "calibration_method": method, "calibration_num": n,
       "quantization_device": "cpu",
       "default_loader": {"dataset_path": f"{root}/data/imagenet_subset/calib", "file_extensions": ["jpg"],
       "preprocessings": [
           {"resize": {"mode": "torchvision", "size": 256, "interpolation": "BICUBIC"}},
           {"centercrop": {"width": 224, "height": 224}},
           {"convertColor": {"form": "BGR2RGB"}}, {"div": {"x": 255}},
           {"normalize": {"mean": [0.485, 0.456, 0.406], "std": [0.229, 0.224, 0.225]}},
           {"transpose": {"axis": [2, 0, 1]}}, {"expandDim": {"axis": 0}}]}}
json.dump(cfg, open(out, "w"), indent=1)
PY
START=$(date +%s)
"$DXCOM" -m "$ONNX" -c "$OUT/config.json" -o "$OUT" --gen_log "$@" > "$OUT/stdout.txt" 2>&1 || { echo "dxcom FAILED, see $OUT/stdout.txt"; exit 1; }
echo "compile_seconds=$(( $(date +%s) - START ))" | tee "$OUT/compile_time.txt"
grep -E "Final result" "$OUT/compiler.log" | sed 's/.* - //'
