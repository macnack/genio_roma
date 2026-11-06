#!/usr/bin/env bash
# ONNX (ConvNeXt, static [1,3,224,224]) -> TFLite FP32 that Arm NN 23.08 GpuAcc can load and run correctly on the Mali-G57.
# Logged graph changes (each checked for ORT parity):
#   1. rewrite_matmul_reshape.py : 4D x 2D const MatMul -> Reshape/MatMul/Reshape   (Arm NN cannot load BATCH_MATMUL 4Dx2D)
#   2. rewrite_mean.py --broadcast: ReduceMean -> Conv1x1/MatMul/GlobalAveragePool with 1/C weights (GpuAcc MEAN fault; sufficient set)
#   3. onnx2tf -rtpo gelu erf    : GELU(erf) -> tanh-based composition (Arm NN 23.08 TFLite parser lacks builtin GELU)
# usage: make_gpu_tflite.sh in.onnx outdir name
set -euo pipefail
IN=$1; OUT=$2; NAME=$3; mkdir -p "$OUT"
PY=.venv-export/bin/python; TF=.venv-tflite/bin/onnx2tf
$PY scripts/rewrite_matmul_reshape.py "$IN" "$OUT/${NAME}_mm2d.onnx" | tail -2
$PY scripts/rewrite_mean.py "$OUT/${NAME}_mm2d.onnx" "$OUT/${NAME}_gpu.onnx" --broadcast | tail -2
(cd "$OUT" && "../../../$TF" -i "${NAME}_gpu.onnx" -o tfl -n -rtpo gelu erf > convert.log 2>&1)
cp "$OUT/tfl/${NAME}_gpu_float32.tflite" "$OUT/${NAME}_gpu_fp32.tflite"; ls -la "$OUT/${NAME}_gpu_fp32.tflite"
