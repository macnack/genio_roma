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
3. **ReduceMean** (see "Minimal rewrite set" below; the first version rewrote all 47 ReduceMean nodes, only 9 are needed): the 8 channels-first LayerNorm means
   -> 1x1 Conv C->C with 1/C weights (`rewrite_mean.py --broadcast --only nchw_c,gap`, max abs 3e-7) and the global-average ReduceMean -> GlobalAveragePool.
4. GlobalAveragePool handled as a standard pool op.

## Minimal rewrite set (ablation, 2026-11-07; supersedes "sufficient, not minimal" above)
Each variant = A-tiny `mm2d` ONNX + a subset of ReduceMean rewrites -> onnx2tf -> one `EnqueueWorkload` in a fresh process, run twice, with the known-good model run
between variants as a control (control always passed, so a fault is not leftover GPU state). Logs: `reports/fp16/ablate_mean_*.log`. "fault" = `GPU fault 0x5x`, `clEnqueueMapBuffer`, abort.
| Variant (what was rewritten) | Result |
|---|---|
| all four kinds, broadcast (earlier "full" set) | pass, valid |
| all four kinds, no broadcast (Conv C->1) | fault |
| only the 36 stage-LN means (NHWC) / only 8 downsample-LN means / only flat+GAP / all but GAP | fault (each) |
| all but the 36 stage-LN means (left as native MEAN) | pass, valid |
| all but the 2 flat-LN means | pass, valid |
| all but the 8 downsample-LN means | fault |
| **only** the 8 downsample-LN means (broadcast) **+ GAP->GlobalAveragePool** (`M_bc`) | **pass, valid** (cos 0.99999 vs FP32 on 400 images, top-1 agreement 100%) |
| same, no broadcast (Conv C->1) | fault |
| leave one downsample layer out: ds1, ds2 or ds3 | fault each |
| leave ds0 out | "OK" but output WRONG and non-deterministic (mean|y| 0.68 then 0.73 vs 0.154): silent failure |
Reading (verified: the TFLite op list of each variant): the faulting MEANs are the ones left in channels-first layout (`[1,C,H,W]` axis 1, and `[1,768,7,7]` axes 2,3); the 36+2
channels-last MEANs (`[1,H,W,C]` axis 3, ~96-768 channels) run correctly on GpuAcc. Rewriting to a Conv with a single output channel also faults, so the C->C ("broadcast") weights are needed.
Why the Mali job faults is not established. The earlier note "MEAN over >=96 channels faults" was a micro-model result and is too broad: channels-last MEAN over 768 channels works inside the full model.
An "OK" return is not proof of correctness (ds0 case): always compare the output with the ONNX reference.
The 4D x 2D MatMul rewrite is still required (LoadNetwork fails without it, confirmed on micro-models). GELU->tanh is required by the parser. Not retested individually in the full model.
Effect: **the minimal set is 17% faster** (A-tiny FP32 263.9 ms vs 317.7 ms) because the 38 extra MatMul rewrites were slower than native MEAN.

## FP16: root cause and fix (2026-11-07)
`OptimizerOptions.m_ReduceFp32ToFp16` on the earlier model gave cosine 0.03-0.27 vs FP32 on real images, finite but wrong values. Findings:
1. Not a general FP16 precision problem: prefix cuts of the model run in FP16 vs FP32 on the board stay at cosine >= 0.9999 through all of stage 2 (cut after node 487, `reports/fp16/bisect_cuts.log`), then break at the downsample-3 LayerNorm.
2. Cause: **FP16 overflow in the LayerNorm variance**. ORT FP32 activation scan on 16 real images (`scripts/act_range.py`, `reports/fp16/act_range_At.json`): `(x-mean)^2` (the `Pow` node) reaches 6.7e6 at downsample-3 and 7.3e4 at downsample-2; FP16 max is 65504. With 2 test images, the cut at the downsample-3 variance already has 147456 non-finite values.
   All other nodes stay below ~5.2e3. Gelu x^3 reaches ~2.1e4, inside the range.
3. Ruled out: the tanh in the GELU composition (a Tanh micro-model with arguments up to 21 matches FP32 in FP16, `reports/fp16/tanh_micro.log`); a first bisect cut inside the GELU erf polynomial (node 298) gave NaNs but that cut is an artificial `Erf` decomposition not present in the full model, so it was discarded.
4. Fix (a logged graph change, FP32-exact because the scale is a power of two, ORT parity max_abs 0.0): `rewrite_ln_scale.py` computes `var = mean((d*c)^2) * (1/c^2)` with c = 2^-3 (downsample-2) and 2^-6 (downsample-3), chosen from the measured range with 1.5x margin.
   Only those two LayerNorms need it. Ranges come from 16 images, so an unusual image could still overflow elsewhere; not checked beyond the 4000 evaluated images.
5. Result (4000 images, GpuAcc, `m_ReduceFp32ToFp16`): see table below. Limits: the Arm NN option converts the whole network; I did not look for per-layer FP16 control (none documented in what I used).

| Config (A-tiny) | ms/img (p95) | Top-1 / Top-5 | cosine vs ONNX FP32 | top-1 agreement |
|---|---|---|---|---|
| FP32, full 47-mean rewrite (first version) | 317.7 (318.8) | 81.98 / 95.95 | 0.999994 | 99.85% |
| FP32, minimal rewrite set | 263.9 (264.5) | 400-image check only: agreement 100%, cos 0.99999 | 0.99999 (400 imgs) | 100% (400 imgs) |
| FP16, full rewrite + variance rescale | 161.2 (162.0) | 82.00 / 95.90 | 0.99966 | 99.38% |
| **FP16, minimal rewrite set + variance rescale** | **133.8 (134.9)** | **82.00 / 95.83** | 0.99969 | 99.45% |
| FP16, without the variance rescale | 160.7 | invalid | -0.019 | - |
FP16 costs ~0.1 points of Top-1 vs FP32 within the +/-1.2 CI and 0.5 points of agreement; logit KL 6e-4 vs 6e-6 for FP32. FP16 + minimal set is faster than ORT FP32 on all 8 CPU cores (156.7 ms) and about 3.3x slower than the DX-M1 (40.1 ms, INT8).
A-small and model B were not re-run with these changes.

## Not usable / not done
- Model B (DINOv3) not run on GPU.

## Board changes (undo)
Installed with `dpkg -i` from debs fetched on the laptop (board has no network): Arm NN 23.08 (`libarmnn33t64`, `libarm-compute32t64`, `libarmnn-cpuacc/gpuacc/cpuref-backend33`,
`libarmnntfliteparser24t64`, `libflatbuffers2`, `python3-pyarmnn`, `armnn-latest-cpu-gpu`), `clinfo`, `python3-numpy`, `libc++1(-18)`, `libc++abi1-18`, `libunwind-18`.
Undo: `sudo dpkg -r python3-pyarmnn armnn-latest-cpu-gpu libarmnntfliteparser24t64 libarmnn-gpuacc-backend33 libarmnn-cpuacc-backend33 libarmnn-cpuref-backend33 libarmnn33t64 libarm-compute32t64 clinfo` (leave shared libs if other things depend on them).
The APU packages are listed in `reports/apu_neuron.md`.
