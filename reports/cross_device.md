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
| Mali-G57 GPU, Arm NN GpuAcc, minimal rewrite set | FP32 | 263.9 (p95 264.5) | 3.8 | - | - | yes (same pipeline; 400-image accuracy check only) |
| Mali-G57 GPU, Arm NN GpuAcc, minimal rewrite set + LN variance rescale | FP16 | 133.8 (p95 134.9) | 7.5 | - | - | yes, `m_ReduceFp32ToFp16`; Top-1 82.00% on 4000 imgs; `reports/gpu_armnn.md` |
| Arm NN CpuAcc (Neon) | FP32 | 668 | 1.5 | 1149 | 0.9 | CPU backend |
| Genio APU (MDLA 3.0) | - | not supported | - | not supported | - | NOT USABLE: first `/dev/apusys` ioctl returns EFAULT, then segfault (`reports/apu_neuron.md`) |

- FP32 CPU outputs match the laptop FP32 reference (max abs diff <= 1e-5 on first 10 images), so CPU accuracy equals the FP32 reference (A-tiny 81.9%, A-small 83.1% Top-1 on the 4000-image subset); DX-M1 INT8 is 80.8% / 82.0%.
- DX-M1 single-request vs best CPU (all 8 cores, FP32): 3.9x faster (tiny), 4.8x (small); vs 2xA78: 5.2x / 5.9x. Async 3-core: 9.2x / 10.8x vs all-core CPU FP32.
- Precision differs (INT8 vs FP32): this is a device comparison, not iso-precision. An INT8/FP16 CPU run was not done.
- Not measured: power, temperature under load, CPU utilisation during DX-M1 runs, end-to-end including decode. CPU runs: 20 timed runs after 3 warmups, one session per config.
- all-cores A-small shows a high p95 (439.6 vs 312 mean): scheduler interference from the A55 cores is a hypothesis.
- GPU accuracy (4000 images, vs FP32 ONNX): A-tiny 81.98% Top-1 (ref 81.93), A-small 83.05% (ref 83.13); within the +/-1.2 pt CI. Differences come from the tanh-approximated GELU.
- GPU is 2x slower than all-core ORT CPU (157/312 ms) and ~8x slower than the DX-M1 single request; Arm NN FP16 on GPU was invalid because of an FP16 overflow in two LayerNorm variances; with a power-of-two rescale it is valid and the fastest non-DX-M1 target (133.8 ms, tiny), see `reports/gpu_armnn.md`.
- APU: an ORT Neuron EP session that lists the provider is not evidence of APU use (an FP16 model ran 615/615 nodes on CPU). Hypothesis: wrong package generation (NeuroPilot 8 from a third-party PPA vs MediaTek's NeuroPilot 6 for Genio 700, jammy-only) and/or userspace/kernel ABI mismatch with Grinn kernel 6.8.0-9003-mtk; untested, see `reports/apu_neuron.md`.
