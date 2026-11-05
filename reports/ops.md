# ONNX operator check: ConvNeXt-Tiny (A: facebookresearch IN-1K, B: HF DINOv3) vs DX-COM tables

Generated 2026-11-05 by `scripts/inspect_onnx.py` (raw JSON in `reports/ops/`). Models were NOT modified.
Exports: `scripts/export_onnx.py`, torch 2.15.0+cpu legacy tracer, static `[1,3,224,224]`, batch 1.
Parity vs PyTorch (ONNX Runtime CPU, seed 0): max abs diff <= 3.6e-6, cosine >= 0.9999999 for all four files.

Tables compared: DX-COM **2.4.1** (`dx-compiler` tag v2.4.1, `source/docs/03_Building_Models.md`, matches the board's RT 3.4.2 release set) and **2.5.0** (`dx-compiler@a087726ead`, same file).

## Verified (measured on our files)

| File | Opset | Nodes | LayerNorm form | GELU form | Ops |
|---|---|---|---|---|---|
| A | 17 | 375 | 19x `LayerNormalization` (+4 channels-first as Pow/Sqrt chain) | `Erf` chain x18 | Add, Constant, Conv x22, Div, Erf, Gemm, LayerNormalization, MatMul x36, Mul, Pow, ReduceMean, Sqrt, Sub, Transpose x36 |
| A | 13 | 565 | primitive chain (ReduceMean/Sub/Pow/Sqrt/Div) | `Erf` chain x18 | same minus LayerNormalization |
| B | 17 | 363 | 23x `LayerNormalization` | `Erf` chain x18 | Add, Concat, Constant, Conv x22, Div, Erf, Gather, GlobalAveragePool, LayerNormalization, MatMul x36, Mul, Reshape, Shape x2, Slice x2, Transpose x46 |
| B | 13 | 593 | primitive chain | `Erf` chain x18 | same minus LayerNormalization, plus Pow/Sqrt/Sub/ReduceMean |

- All Conv: 1x stem 4x4 s4, 3x downsample 2x2 s2, **18x depthwise 7x7** (g = 96/192/384/768), `pads=3`, dilation 1. Same in A and B.
- No dynamic dimensions; A output `[1,1000]`, B output `[1,768]` (pooled feature).
- Pointwise "Linear" layers appear as MatMul (36) and Transpose around LayerNorm.

## Comparison with the documented tables

| Item | DX-COM 2.4.1 table | DX-COM 2.5.0 table | Impact |
|---|---|---|---|
| Depthwise Conv kernel | `kernel_shape` in {[3,3],[5,5]} only | `kernel_shape` < 16 | **18 depthwise 7x7 are outside the 2.4.1 documented set**; inside 2.5.0 |
| `LayerNormalization` op | not listed | listed: last-dim only, D < 4080 | opset 17 exports need 2.5.0, per the tables |
| LayerNorm as primitive chain | `Div` row mentions "Part of LayerNorm"; ReduceMean only over channel or (W,H) | explicitly supported incl. ConvNeXt LayerNorm2d | opset 13 chain: documented partly in 2.4.1, explicitly in 2.5.0 |
| `Pow`, `Sqrt` | not named | not named | name absent in both tables; 2.5.0 text says chain LayerNorm is supported |
| `Erf` | "only as part of GELU" | same | GELU as Erf chain: needs to match the GELU pattern (unverified) |
| `Gelu` op | listed | listed | not emitted by the legacy tracer |
| Transpose, Reshape, MatMul, Gemm, GlobalAveragePool, Mul, Add, Sub, Div, Concat, Gather, Slice, Shape | listed | listed | no documented problem (Gather/Slice/Shape/Concat in B come from HF pooling code) |

## Format / version constraint (documented)

DX-COM 2.5.0 emits `.dxnn` format v9 only and requires DX-RT >= 3.5.0; RT 3.4.2 and earlier cannot load it
([dx-compiler@a087726ead v2.5.0: source/docs/Appendix_Change_Log.md#L13]). The board runs RT 3.4.2.
So: the 2.5.0-only features ConvNeXt needs (7x7 depthwise, LayerNormalization) and the board's runtime are in tension.

## Compile results with DX-COM 2.4.1 (laptop, synthetic calibration images, **not** for accuracy)

**Correction of earlier findings (2026-11-05).** The `SURGERY` "Unknown error" was caused by *our config*, not by the models, the ops or the dependency versions:
- Control: the official DEEPX sample `MobileNetV2-1.onnx` + config (from `sdk.deepx.ai/modelzoo/`, as in `dx-compiler/example/1-download_sample_models.sh`) compiles on 2.4.1 (newest deps venv) and on 2.5.0.
- Our toy models fail with our first config, but the same toy (3x3 stem + depthwise 3x3) compiles (exit 0) with the official preprocessing block (`convertColor BGR2RGB`, `div 255`, `normalize`, `transpose [2,0,1]`, `expandDim 0`) plus `quantization_device: cpu`. Cause is inside our preprocessing list (no `div`/`convertColor`, `transpose [0,3,1,2]`); exact key not isolated. Our first config was also semantically wrong (no /255, no BGR->RGB for cv2-loaded images).
- A dependency-pinned venv was therefore unnecessary (hypothesis rejected).

| Model | Opset | 2.4.1 | 2.5.0 | Compiler partition (compiler.log) |
|---|---|---|---|---|
| dw7 toy (7x7 depthwise) | 13 | compiles | compiles | - |
| A | 13 | compiles | compiles | 1 NPU group, 0 CPU groups (2.4.1) |
| A | 17 | compiles | not run | 1 NPU group, 0 CPU groups |
| B | 13 | compiles | not run | 1 NPU group, 0 CPU groups |
| B | 17 | compiles | not run | 1 NPU group, 0 CPU groups |

So the documented 2.4.1 limit (depthwise 3x3/5x5 only) did **not** stop compilation of 18 depthwise 7x7 convs, and `LayerNormalization` (opset 17) was accepted. The tables are conservative or incomplete for 2.4.1; support is verified only by compiling, and numerical quality is not yet checked.
Compiler guidance: NPU input is uint8 NHWC [1,224,224,3]; div/normalize/transpose are fused into the NPU graph, resize/centercrop/convertColor/expandDim stay host-side.

## Board check (RT 3.4.2, `dxparse`, `dxrun -s -v`), model A opset 13 `.dxnn` compiled by 2.4.1
- `.dxnn` format **v8**, DX-COM v2.4.1-rc.1, 1 task `npu_0 [NPU]`, no CPU task, 211.8 MB model memory.
- Loads and runs on RT 3.4.2: single-request NPU time 35.29 ms, latency 39.7-39.9 ms, 24.1-24.3 FPS (`-s` single mode; not comparable with the 65.91 FPS YOLOv5S benchmark-mode number).
- **No board upgrade is needed** to run ConvNeXt compiled with 2.4.1 (hypothesis H1 resolved for 2.4.1: output is v8, loadable).
- Accuracy not yet measured: this `.dxnn` was calibrated on synthetic images.

## Open
- Real calibration data and accuracy vs FP32 (needs a labelled ImageNet subset).
- Which preprocessing key triggered the SURGERY failure (low priority).
- Opset 13 vs 17 numerical/latency comparison; B on the board; Q-Pro.
