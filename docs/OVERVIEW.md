# Project overview: ConvNeXt on DEEPX DX-M1 and the Genio-700 accelerators

Goal: run ConvNeXt-Tiny/Small (model A, facebookresearch ImageNet-1K; model B, DINOv3 backbone) on the DEEPX DX-M1 NPU attached to a Grinn GenioBoard-700,
and compare it, on the same images and the same measurement harness, with the board's other compute: CPU (A78/A55), Mali-G57 GPU and MediaTek APU.
Rule throughout: no claim of acceleration without proof that the work ran on that device; every graph change is logged; docs split into documented / verified / hypothesised.

## Data flow (laptop -> board)
```
 LAPTOP (x86, .venv-export / .venv-dxcom / .venv-tflite)                          BOARD (Genio-700, adb, no network)
 ---------------------------------------------------------                        ------------------------------------------
 PyTorch ConvNeXt  --export_onnx.py-->  ONNX FP32 (opset 13, 1x3x224x224)
                                          |  inspect_onnx.py / check_ops.py  (op table vs DX-COM)
                                          |
        +---------------------------------+------------------------------------------------+---------------------+
        |                                 |                                                |                     |
   DX-M1 path                          GPU path                                        CPU path               APU path
   DX-COM 2.4.1 (PTQ, calib 1000 imgs)  rewrite_matmul_reshape.py                     ORT FP32 / INT8 / FP16   NeuroPilot 6
   -> .dxnn (v8)                        rewrite_mean.py (minimal set)                 (quantize_ort_int8.py,   (mediatek-libneuron,
        |                               rewrite_ln_scale.py (FP16 only)                to_fp16.py)              private dir)
        | adb push                      onnx2tf -rtpo gelu erf -> .tflite                  | adb push              | adb push
        v                                    | adb push                                   v                       v
   DX-RT 3.4.2 + driver 2.6.0 + FW 2.7.4     v                                       ORT CPUExecutionProvider   ncc-tflite -> .dla -> neuronrt
   dxrun / dx_engine -> PCIe -> DX-M1   PyArmNN 33 (Arm NN 23.08) GpuAcc,CpuAcc                                (blocked: /etc/nhw, see issue #2)
        |                                    |                                            |
        +------------------------------------+--------------------------+-----------------+
                                                                        v
              eval_*_board.py  -> logits .npy (4000 images)  ---> compare_acc.py (Top-1/5, cosine, KL, CI vs ONNX FP32)
              bench_*.py       -> latency mean/p50/p95, FPS      ---> reports/*.md  (cross_device.md = the comparison table)
```

## How each path works (mechanism)
- **DX-M1:** DX-COM compiles the ONNX to a `.dxnn`: it quantizes to INT8 using calibration images (PTQ) and maps the graph to the NPU. The runtime (DX-RT) loads it through the PCIe driver;
  `dxparse`/`dxrun` show one `npu_0` task and no CPU task, which is the proof of NPU execution. Compiler 2.4.1 was chosen because its `.dxnn` v8 loads on the board's RT 3.4.2 (2.5.0 emits v9 that needs RT >= 3.5.0).
- **CPU:** ONNX Runtime CPUExecutionProvider, cores pinned with `taskset`; the FP32 numbers are also the accuracy reference.
- **GPU:** the Mali is reached through Arm NN's OpenCL backend (GpuAcc). Arm NN only parses TFLite here, so ONNX -> TFLite (onnx2tf). Arm NN 23.08 cannot take every ConvNeXt op as exported, so the graph is rewritten (all rewrites are numerically equivalent in FP32 and ORT-parity checked):
  1. 4-D x 2-D MatMul -> Reshape / 2-D MatMul / Reshape (otherwise `LoadNetwork` fails);
  2. the 8 channels-first LayerNorm means -> 1x1 Conv with C x C weights of 1/C, and the global average -> GlobalAveragePool (found by ablation; the other MEAN ops run fine). Other forms fault the Mali job slot or silently return wrong output;
  3. GELU(erf) -> tanh composition (parser lacks GELU; small approximation error).
  Proof of GPU execution: the Arm NN profiler lists only `Cl*Workload` events and GPU clock rises from 390 to 950 MHz.
  FP16 (`m_ReduceFp32ToFp16`) needed one more change: `(x-mean)^2` in some LayerNorms exceeds the FP16 maximum 65504, so the variance is computed on a power-of-two scaled input and rescaled.
- **APU:** MediaTek's NeuroPilot. The third-party NeuroPilot 8 build fails with EFAULT on `/dev/apusys`; MediaTek's NeuroPilot 6 (the official Genio 700 package set) runs the VPU self-test PASS from a private directory. The MDLA path (compile with `ncc-tflite`, run with `neuronrt`) still needs `/etc/nhw`, a system change waiting for approval.

## Methodology
1. Docs first (`docs/deepx*`, `docs/genio`): every claim is tagged documented (with citation), verified (our measurement, linked report) or hypothesis. `deepx-compact` is the token-cheap copy.
2. One data protocol: seeded ImageNet-1K *validation* subset (`make_imagenet_subset.py`): calibration and 4000 disjoint eval images; identical preprocessing (`preproc.py`) for every device; Top-1 CI about +/-1.2 points.
3. FP32 ONNX on the laptop is the reference; each device is scored by Top-1/Top-5, logit cosine, KL and top-1 agreement against it (`compare_acc.py`).
4. Every unsupported or failing case is isolated before it is worked around: micro-models, prefix-cut bisect, leave-one-out ablation with a control run between variants, activation-range scans. "Provider listed" or "run returned OK" never counts as proof (we saw an all-CPU "APU" run and a wrong-but-OK GPU run).
5. Safety: board changes are explained and reversible (undo commands in the reports); anything touching system config waits for approval.

## Results so far (A-tiny / A-small, batch 1, model-only)
| Target | Precision | Tiny ms | Small ms | Top-1 tiny / small |
|---|---|---|---|---|
| ONNX FP32 (laptop reference) | FP32 | - | - | 81.9 / 83.1 |
| DX-M1 NPU | INT8 | 40.1 | 65.3 | 80.8 / 82.0 |
| Genio CPU, 8 cores (ORT) | FP32 | 156.7 | 312.1 | = reference |
| Mali GPU (Arm NN), minimal rewrites | FP16 | 133.8 | 239.1 | 82.0 / 83.2 |
| Mali GPU (Arm NN), minimal rewrites | FP32 | 263.9 | 494.8 | 82.0 / 83.05 |
| Mali GPU, first version (full rewrites) | FP32 | 317.7 | 602.9 | 82.0 / 83.1 |
| CPU 8 cores, ORT INT8 (naive MinMax PTQ) | INT8 | 129.2 | 211.4 | 20.9 / 78.4 (collapsed) |
| CPU 8 cores, ORT FP16 | FP16 | 210.9 | 391.2 | 81.85 / 83.13 |
| APU MDLA (NeuroPilot 6.2.3), FP16 | FP16 | 54.8 | 105.0 | 81.95 / 83.13; INT8 blocked (SQRT/EXP op versions) |
Details and caveats: `reports/cross_device.md`, `gpu_armnn.md`, `apu_neuron.md`, `accuracy.md`, `ops.md`.

## Model B (DINOv3 ConvNeXt-Tiny, 768-d feature; cosine vs FP32 ONNX, 4000 images)
| Target | Precision | ms | Cosine mean / min |
|---|---|---|---|
| DX-M1, default PTQ | INT8 | 40.1 | 0.734 / 0.314 |
| DX-M1, `--quant_diagnosis` + `--checkpoint` resume (best) | INT8 | 40.1 | 0.914 / 0.681 |
| DX-M1, Q-Pro | INT8 | 40.0 | 0.569 / 0.002 |
| APU MDLA (LayerNorm scaling `--lo 1000`) | FP16 | 55.0 | 0.99997 / 0.9990, 0 of 4000 non-finite (first build: 1 of 4000 non-finite) |
| Mali GPU | FP16 / FP32 | 130.2 / 258.2 | 0.9998 / 0.99999 |
| CPU 8 cores | FP32 | 170.1 | = reference |
- B-tiny's DX-M1 fidelity is the open problem (activation-quantisation dominated). The APU is the better accuracy/latency choice for B-tiny.
- B needs extra value-identical rewrites: static Reshape targets, Gather->Slice+Reshape, and scaling of every LayerNorm (`rewrite_ln_scale.py --lo 1000 --fold`; hypothesis: FP16 eps flushed to zero on MDLA).

## Model B-small (768-d feature; cosine vs FP32 ONNX, 4000 images)
| Target | Precision | ms | Cosine mean / min |
|---|---|---|---|
| DX-M1, default PTQ | INT8 | 65.3 | 0.984 |
| APU MDLA | FP16 | 105.8 | 0.99997 / 0.9985 (0 of 4000 non-finite) |
| Mali GPU | FP16 / FP32 | 235.6 / 490.0 | 0.99988 / 0.99999 |
| CPU 8 cores | FP32 | 375.9 | = reference (400 images) |
- DX-COM 2.4.1: `calibration_method`/`calibration_num` in `config.json` are ignored by the CLI; `--recalibration_method` is a no-op (ema/minmax/iqr resumes are md5-identical). Earlier A minmax/calibration comparisons compared identical builds. The resume path changes the result (B up, A-tiny 80.8 -> 80.0% Top-1), but calibration-subset choice alone moves B-tiny cosine 0.792-0.909 across 5 random 100-image subsets (A-tiny Top-1 only 80.73-81.25%, logit cosine 0.811-0.939), so the resume gain is not distinguishable from subset luck (`reports/calibration_sensitivity.md`). See `docs/deepx/compiler.md`.

## Repo map
- `docs/deepx/`, `docs/deepx-compact/`, `docs/genio/`, `grinn-genio-700-sbc-docs/`: documentation (see `CLAUDE.md`).
- `scripts/`: export, graph inspection, rewrites, quantization, board eval/bench, bisect and ablation harnesses.
- `reports/`: result reports; `reports/acc` logs and JSON, `reports/fp16` FP16 and ablation evidence.
- `bin/`: board helpers (serial, flash). Git-ignored: `models/`, `data/`, `weights/`, `.venv-*`, `.onnx/.dxnn/.tflite/.npy`.
