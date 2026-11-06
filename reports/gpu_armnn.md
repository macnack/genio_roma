# Mali-G57 MC3 GPU: ConvNeXt-Tiny/Small via Arm NN 23.08 (GpuAcc)

Board: GenioBoard-700 (MT8390). Batch 1, 224x224, FP32, model-only. Evidence: `reports/acc/gpu_At.{json,log}`, `gpu_As.{json,log}`,
`armnn_profile_At_gpu.json`. Scripts: `scripts/make_gpu_tflite.sh`, `rewrite_matmul_reshape.py`, `rewrite_mean.py`, `bench_armnn.py`, `eval_armnn_board.py`.

## Result
| Model | Backend | Precision | ms/img (mean, p95) | Top-1 / Top-5 (4000 imgs) | vs ONNX FP32 |
|---|---|---|---|---|---|
| A-tiny | Arm NN GpuAcc | FP32 | 317.7 (318.8) | 81.98 / 95.95 (ref 81.93 / 95.93) | cos 0.999994, top-1 agreement 99.85% |
| A-small | Arm NN GpuAcc | FP32 | 602.9 (603.5) | 83.05 / 96.18 (ref 83.13 / 96.15) | cos 0.999991, top-1 agreement 99.85% |
| A-tiny | Arm NN CpuAcc (Neon) | FP32 | 668 | not run | - |
| A-small | Arm NN CpuAcc | FP32 | 1149 | not run | - |

Top-1 95% CI is about +/-1.2 points, so the GPU matches the FP32 reference within noise. Per-image max abs logit difference 0.05 (tiny) / 0.11 (small),
caused by the tanh GELU approximation (below).

## Proof of GPU execution
- Arm NN profiler (`armnn_profile_At_gpu.json`): 959 of 959 workload events are `Cl*Workload`; no Neon or Ref events.
- GPU clock 950 MHz under load vs 390 MHz idle (devfreq). CpuAcc run for comparison is 2.1x slower, so the work did move.

## Pipeline and logged graph changes (none applied silently)
ONNX (opset 13, FP32) -> ONNX rewrites -> TFLite (onnx2tf 2.6.9, TF 2.21, `.venv-tflite`) -> PyArmNN 33.0.0 (TFLite parser; there is no ONNX parser in this build).
1. **GELU**: `onnx2tf -rtpo gelu erf` replaces Erf-GELU with a tanh composition because the Arm NN parser rejects builtin GELU (op 150). Approximate, not exact.
2. **4-D x 2-D MatMul** -> Reshape / 2-D MatMul / Reshape (`rewrite_matmul_reshape.py`). `LoadNetwork` failed on BATCH_MATMUL ("Invalid dimension index"). Lossless (max abs 3e-7).
3. **LayerNorm ReduceMean** -> 1x1 Conv / MatMul with C x C weights of 1/C (`rewrite_mean.py --broadcast`, max abs 4e-7). A GpuAcc MEAN over >=96 channels faults the
   Mali job slot (`GPU fault 0x5b`, `cl::Error clEnqueueMapBuffer`). This set is sufficient; it is not shown to be minimal, and some bisect results were non-monotonic (unexplained).
4. GlobalAveragePool handled as a standard pool op.

## Not usable
- **FP16** (`m_ReduceFp32ToFp16`): 160.7 ms (tiny) but output invalid (cosine -0.019). Not reported as a result; cause unknown.
- Model B (DINOv3) not run on GPU.

## Board changes (undo)
Installed with `dpkg -i` from debs fetched on the laptop (board has no network): Arm NN 23.08 (`libarmnn33t64`, `libarm-compute32t64`, `libarmnn-cpuacc/gpuacc/cpuref-backend33`,
`libarmnntfliteparser24t64`, `libflatbuffers2`, `python3-pyarmnn`, `armnn-latest-cpu-gpu`), `clinfo`, `python3-numpy`, `libc++1(-18)`, `libc++abi1-18`, `libunwind-18`.
Undo: `sudo dpkg -r python3-pyarmnn armnn-latest-cpu-gpu libarmnntfliteparser24t64 libarmnn-gpuacc-backend33 libarmnn-cpuacc-backend33 libarmnn-cpuref-backend33 libarmnn33t64 libarm-compute32t64 clinfo` (leave shared libs if other things depend on them).
The APU packages are listed in `reports/apu_neuron.md`.
