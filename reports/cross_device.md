# Cross-device benchmark: ConvNeXt-Tiny/Small (model A, ImageNet-1K) on the Genio-700 board

Board: Grinn GenioBoard-700 (MT8390: 2x Cortex-A78 = cores 6-7, 6x Cortex-A55 = cores 0-5). Batch 1, 224x224, model-only
(input already resized/cropped), sync one request at a time unless noted. Raw: `reports/acc/cpu_bench_board.jsonl`, `reports/acc/sweep_dxrun.csv`.

| Target | Precision | A-tiny ms/img | A-tiny FPS | A-small ms/img | A-small FPS | Verified executed there |
|---|---|---|---|---|---|---|
| DX-M1 NPU, single request | INT8 (PTQ) | 40.1 (NPU 35.3) | 24.2 | 65.3 (NPU 60.6) | ~15 | yes: `dxparse` single `npu_0` task, 0 CPU tasks |
| DX-M1 NPU, 3 cores async (`dxrun -b`) | INT8 | - | 58.9 | - | 34.4 | same |
| CPU 2xA78 (taskset 6,7), ORT 1.31.1 | FP32 | 207.4 (p95 207.6) | 4.8 | 383.2 | 2.6 | CPU EP, pinned |
| CPU 1xA78 | FP32 | 397.9 | 2.5 | 736.4 | 1.4 | CPU EP, pinned |
| CPU 6xA55 | FP32 | 341.7 | 2.9 | 631.7 | 1.6 | CPU EP, pinned |
| CPU all 8 cores | FP32 | 156.7 | 6.4 | 312.1 (p95 439.6) | 3.2 | CPU EP |
| Mali-G57 GPU, Arm NN GpuAcc | FP32 (3 logged graph changes) | 317.7 (p95 318.8) | 3.1 | 602.9 | 1.7 | yes: profiler 959/959 `Cl*Workload`; see `reports/gpu_armnn.md` |
| Mali-G57 GPU, Arm NN GpuAcc, minimal rewrite set | FP32 | 263.9 (p95 264.5) | 3.8 | 494.8 (p95 495.4) | 2.0 | yes (same pipeline); Top-1 81.98 / 83.05 on 4000 imgs |
| Mali-G57 GPU, Arm NN GpuAcc, minimal rewrite set + LN variance rescale | FP16 | 133.8 (p95 134.9) | 7.5 | 239.1 (p95 239.5) | 4.2 | yes, `m_ReduceFp32ToFp16`; Top-1 82.00 / 83.23 on 4000 imgs; `reports/gpu_armnn.md` |
| CPU all 8 cores, ORT static QDQ INT8 (MinMax, 100 calib imgs) | INT8 | 129.2 (p95 149.9) | 7.7 | 211.4 (p95 212.1) | 4.7 | CPU EP; **accuracy poor: Top-1 20.9% / 78.4%** |
| CPU all 8 cores, ORT FP16 model | FP16 | 210.9 (p95 216.4) | 4.7 | 391.2 (p95 401.9) | 2.6 | CPU EP; Top-1 81.85 / 83.13 |
| Arm NN CpuAcc (Neon) | FP32 | 668 | 1.5 | 1149 | 0.9 | CPU backend |
| Genio APU (MDLA 3.0), NeuroPilot 6.2.3 (`ncc-tflite` + `neuronrt -m hw`), minimal rewrites + LN rescale + MatMul->Gemm | FP16 | 54.8 (3 x 200 runs, model-only) | 18.2 | 105.0 | 9.5 | compiled for `mdla3.0` only (an unsupported op fails the compile); APU power-on in `dmesg`; Top-1 81.95 / 83.13 on 4000 imgs (ref 81.93 / 83.13), agreement 99.88% / 99.90%, 0 non-finite; `reports/apu_neuron.md` |
| Genio APU, NeuroPilot 8 / ORT Neuron EP (third-party) | - | not supported | - | not supported | - | NOT USABLE: first `/dev/apusys` ioctl returns EFAULT, then segfault |

- FP32 CPU outputs match the laptop FP32 reference (max abs diff <= 1e-5 on first 10 images), so CPU accuracy equals the FP32 reference (A-tiny 81.9%, A-small 83.1% Top-1 on the 4000-image subset); DX-M1 INT8 is 80.8% / 82.0%.
- DX-M1 single-request vs best CPU (all 8 cores, FP32): 3.9x faster (tiny), 4.8x (small); vs 2xA78: 5.2x / 5.9x. Async 3-core: 9.2x / 10.8x vs all-core CPU FP32.
- Iso-precision CPU baselines (4000 imgs, `reports/acc/cpu8_*`): INT8 (ORT static QDQ, MinMax, per-channel, 100 calibration images) is 1.2x faster than CPU FP32 for tiny (129 vs 157 ms) but accuracy collapses: Top-1 20.9% (agreement 22%) tiny, 78.4% (agreement 87%) small, vs ref 81.9 / 83.1. So the DX-M1 INT8 result (80.8 / 82.0) is not matched by a naive CPU INT8 PTQ; this compares calibration pipelines as much as devices. Cause of the CPU INT8 collapse is Unknown (not investigated; activation outliers in LayerNorm/GELU paths are a hypothesis). FP16 ORT on CPU is slower than FP32 (211 vs 157 ms tiny; 391 vs 312 small), accuracy equals reference (agreement 99.7% / 99.8%).
- On the same-precision axis: DX-M1 INT8 40.1 ms vs best accurate CPU 156.7 ms (FP32) = 3.9x; vs GPU FP16 133.8 ms = 3.3x.
- Not measured: power, temperature under load, CPU utilisation during DX-M1 runs, end-to-end including decode. CPU runs: 20 timed runs after 3 warmups, one session per config.
- all-cores A-small shows a high p95 (439.6 vs 312 mean): scheduler interference from the A55 cores is a hypothesis.
- GPU accuracy (4000 images, vs FP32 ONNX): A-tiny 81.98% Top-1 (ref 81.93), A-small 83.05% (ref 83.13); within the +/-1.2 pt CI. Differences come from the tanh-approximated GELU.
- GPU is 2x slower than all-core ORT CPU (157/312 ms) and ~8x slower than the DX-M1 single request; Arm NN FP16 on GPU was invalid because of an FP16 overflow in two LayerNorm variances; with a power-of-two rescale it is valid and the fastest non-DX-M1 target (133.8 ms, tiny), see `reports/gpu_armnn.md`.
- APU: an ORT Neuron EP session that lists the provider is not evidence of APU use (an FP16 model ran 615/615 nodes on CPU). Hypothesis: wrong package generation (NeuroPilot 8 from a third-party PPA vs MediaTek's NeuroPilot 6 for Genio 700, jammy-only) and/or userspace/kernel ABI mismatch with Grinn kernel 6.8.0-9003-mtk; untested, see `reports/apu_neuron.md`.

## Model B: DINOv3 ConvNeXt-Tiny (768-d pooled feature, no classifier head)

Same board, 4000-image eval subset, batch 1. Quality = cosine of the 768-d output vs the FP32 ONNX output on the laptop (mean / min over 4000 images); there is no Top-1 for B. Raw: `reports/acc/B13_*`, `gpuB_*`, `mdlaB*`.

| Target | Precision | ms/img | Cosine mean / min | Verified executed there |
|---|---|---|---|---|
| DX-M1 NPU, default PTQ (ema, 100 calib) | INT8 | 40.1 (NPU 35.3) | 0.734 / 0.314 | `dxparse`: 1 NPU group, 0 CPU |
| DX-M1 NPU, `--quant_diagnosis` then `--checkpoint` resume (`--recalibration_method` has no effect) | INT8 | 40.1 | 0.914 / 0.681 | same |
| DX-M1 NPU, API ema, 500 calibration images (`src` half of a held-out split) | INT8 | 40.1 | **0.9235 / 0.700** | same |
| DX-M1 NPU, Q-Pro (`use_q_pro`, API, 100 calib, built in ~2.5 h) | INT8 | 40.0 | 0.569 / 0.002 | same |
| Mali-G57 GPU, Arm NN GpuAcc, minimal rewrites | FP32 | 258.2 (p95 259.8) | 0.99999 / 0.99996 | Arm NN GpuAcc,CpuAcc |
| Mali-G57 GPU, Arm NN | FP16 | 130.2 (p95 130.7) | 0.9998 / 0.9988 | same |
| Genio APU MDLA 3.0, NeuroPilot 6.2.3, LayerNorm scaling `--lo 1.0` (first build) | FP16 | 55.0 (3 x 200 runs) | 0.99993 / 0.9989 over 3999 finite outputs; **1 of 4000 non-finite** (image 3574) | `neuronrt -m hw` on DLA compiled with `--arch=mdla3.0` |
| Genio APU MDLA 3.0, LayerNorm scaling `--lo 1000` (final build) | FP16 | 55.0 / 55.0 / 55.7 (3 x 200 runs) | **0.99997 / 0.9990, 0 of 4000 non-finite** | same |
| CPU 8 cores, ORT 1.31.1 | FP32 | 170.1 (p95 177.4, 400-image re-run) | 1.0 / 1.0 (= reference, max abs diff 2.8e-5) | CPU EP |

Facts and caveats
- **DX-M1 fidelity is the weak point for B-tiny.** INT8 on the NPU is the fastest target (40 ms), but its best feature cosine is 0.9235 (API ema, 500 calibration images; 0.914 before) vs 0.9999 for the FP16 APU/GPU, so the APU at 55 ms is the better accuracy/latency choice for B-tiny. Cause (from `dxcom --quant_diagnosis`): activation quantisation (activation-only cosine 0.951, weight-only 0.999).
- Build changes needed beyond A, each value-identical (ORT parity checked, `scripts/`): `rewrite_static_reshape.py` (computed Reshape targets -> constants; otherwise onnx2tf emits SELECT and Arm NN rejects it), `rewrite_gather_slice.py` (final Gather of token 0 -> Slice+Reshape; ncc-tflite "Cannot find an execution plan" on the Gather, found by bisect), `rewrite_ln_scale.py --lo 1.0 --fold` (B's early LayerNorm variances are ~1e-4, which FP16/MDLA could not represent: output all Inf; power-of-two up-scaling of the centred values with eps*c^2, no un-scale constant, since 2^-2k is FP16-subnormal and was flushed to 0 by MDLA).
- The first B-tiny MDLA build left 1 of 4000 outputs non-finite (image 3574; its largest FP32 tensor, 1.6e3, is far below 65504). The B-small build with the same scaling failed on 13 of 16 smoke-test images (all Inf; bisect: inside `stages.3/layers.2/layer_norm`, variance ~2.7e-3, eps 1e-6). Hypothesis (consistent with the result, not proven): in FP16 eps is a subnormal that MDLA may flush to zero, so a token with near-zero variance divides by zero. Fix: scale EVERY LayerNorm (`rewrite_ln_scale.py --lo 1000 --fold`, i.e. eps becomes eps*c^2, which is FP16-normal). Result: B-small 16/16 then 4000/4000 finite, B-tiny 4000/4000 finite (image 3574 now cosine 0.99993). Scale factors still come from `act_range` on 16 images.
- CPU FP32 timing: the 4000-image run was noisy (mean 261, p50 205, p95 396 ms; cause unknown), a quiet 400-image re-run gave 170.1 ms; the table uses the re-run. Outputs of the 4000 run equal the FP32 reference.
- GPU numbers use the same Arm NN path as A; the GPU FP16 needed no extra rescale beyond the one downsample LayerNorm.
- DX-M1 builds: API iqr with the full 1000-image pool gave 0.683, but API ema with 500 images from a split half gave 0.9235 on the 4000 images (N=250: 0.9209; held-out N=100 best subset 0.915; see `calibration_sensitivity.md` follow-up), so the method/pool, not the count alone, matters, cause unknown; `calibration_method`/`calibration_num` in `config.json` are ignored by the 2.4.1 CLI, and `--recalibration_method` is a no-op (ema/minmax/iqr resumes are md5-identical). The 0.914 comes from the resume path, but calibration-subset luck is not excluded: 5 random 100-image subsets give B-tiny cosine 0.792-0.909 (default build 0.734, resume 0.914) and A-tiny Top-1 80.73-81.25% with logit cosine 0.811-0.939 (`reports/calibration_sensitivity.md`). See `docs/deepx/compiler.md`.


## Model B-small: DINOv3 ConvNeXt-Small (768-d pooled feature)

Same protocol (4000 images, batch 1, cosine of the 768-d output vs FP32 ONNX). Reference `reports/acc/BS13_fp32_out.npy`. Raw: `reports/acc/gpuBs_*`, `mdlaBs*`, `cpuBs_t.json`.

| Target | Precision | ms/img | Cosine mean / min | Verified executed there |
|---|---|---|---|---|
| DX-M1 NPU, default PTQ (earlier build) | INT8 | 65.3 | 0.984 (mean) | `dxparse`: 1 NPU group, 0 CPU |
| Mali-G57 GPU, Arm NN GpuAcc | FP32 | 490.0 (p95 490.7) | 0.99999 / 0.99993 | GpuAcc,CpuAcc |
| Mali-G57 GPU, Arm NN | FP16 | 235.6 (p95 236.0) | 0.99988 / 0.99862 | same |
| Genio APU MDLA 3.0, NeuroPilot 6.2.3 (`--lo 1000` scaling) | FP16 | 105.4 / 106.0 / 106.0 (3 x 200 runs) | 0.99997 / 0.9985, 0 of 4000 non-finite | `neuronrt -m hw` on DLA compiled `--arch=mdla3.0` |
| CPU 8 cores, ORT 1.31.1 | FP32 | 375.9 (p95 391.8, 400-image quiet run) | = reference on the 400 images run (cosine >= 0.9999999) | CPU EP |

- The DX-M1 row is the earlier default-PTQ build (not re-timed or re-built in this round; calibration choice affects B-tiny fidelity strongly, see `calibration_sensitivity.md`, B-small was not swept).
- Same rewrites as B-tiny (static Reshape targets, MatMul->Gemm, Gather->Slice+Reshape, LayerNorm scaling). B-small needed the all-LayerNorm scaling from the start; with only the layers selected by `--lo 1.0` 13 of 16 outputs were Inf.
- ms are model-only. CPU outputs were compared only on the 400 images of the timing run.
