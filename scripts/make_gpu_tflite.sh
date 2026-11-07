#!/usr/bin/env bash
# ONNX (ConvNeXt, static [1,3,224,224]) -> TFLite that Arm NN 23.08 GpuAcc can load and run correctly on the Mali-G57.
# Logged graph changes (each checked for ORT parity):
#   1. rewrite_matmul_reshape.py : 4D x 2D const MatMul -> Reshape/MatMul/Reshape   (Arm NN cannot load BATCH_MATMUL 4Dx2D)
#   2. rewrite_mean.py --broadcast --only nchw_c,gap : the 8 channels-first LayerNorm means (downsample layers) -> 1x1 Conv C->C with 1/C weights,
#      and the global-average ReduceMean -> GlobalAveragePool. This is the MINIMAL set found by ablation (reports/gpu_armnn.md);
#      set FULL=1 for the earlier, larger set (all ReduceMean rewritten; same accuracy, 20% slower).
#   3. onnx2tf -rtpo gelu erf    : GELU(erf) -> tanh-based composition (Arm NN 23.08 TFLite parser lacks builtin GELU)
#   4. FP16 only (RANGES=act_range.json): rewrite_ln_scale.py rescales the LayerNorm variance in the layers whose (x-mean)^2 exceeds the FP16 max.
#      Run the result with OptimizerOptions.m_ReduceFp32ToFp16 (bench_armnn.py --fp16).
# usage: [FULL=1] [RANGES=reports/fp16/act_range_At.json] make_gpu_tflite.sh in.onnx outdir name
set -euo pipefail
IN=$1; OUT=$2; NAME=$3; mkdir -p "$OUT"
PY=.venv-export/bin/python; TF=.venv-tflite/bin/onnx2tf
$PY scripts/rewrite_matmul_reshape.py "$IN" "$OUT/${NAME}_mm2d.onnx" | tail -2
if [ "${FULL:-0}" = 1 ]; then $PY scripts/rewrite_mean.py "$OUT/${NAME}_mm2d.onnx" "$OUT/${NAME}_gpu.onnx" --broadcast | tail -2
else $PY scripts/rewrite_mean.py "$OUT/${NAME}_mm2d.onnx" "$OUT/${NAME}_gpu.onnx" --broadcast --only nchw_c,gap | tail -2; fi
SRC=${NAME}_gpu
if [ -n "${RANGES:-}" ]; then $PY scripts/rewrite_ln_scale.py "$OUT/${NAME}_gpu.onnx" "$OUT/${NAME}_gpu_lns.onnx" "$RANGES"; SRC=${NAME}_gpu_lns; fi
(cd "$OUT" && "../../../$TF" -i "$SRC.onnx" -o tfl -n -rtpo gelu erf > convert.log 2>&1)
cp "$OUT/tfl/${SRC}_float32.tflite" "$OUT/${SRC}_fp32.tflite"; ls -la "$OUT/${SRC}_fp32.tflite"
