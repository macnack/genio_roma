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

## Compile probes with DX-COM 2.4.1 (laptop, synthetic calibration images, **not** for accuracy)

- A opset 17 and 13: both fail in phase `SURGERY` after ~3 s with `UnknownError: Unknown error occurred during compilation`.
- Control (toy model: stem conv -> depthwise KxK -> GAP -> Gemm, K = 3, 5, 7): **all three fail identically**, including K=3 which the 2.4.1 table lists as supported.
- Therefore the failure is NOT evidence about ConvNeXt operators. It points to the toolchain/environment (dependencies resolved to the newest versions: numpy 2.5.4, onnx 1.23.2, onnxruntime 1.31.1, protobuf 7.x, torch 2.15) or the config. Under investigation: a venv resolved as of the release date.

## Open
- Whether unsupported ops (7x7 depthwise on 2.4.1) fail or fall back to the CPU is still unobserved.
- LayerNorm/GELU pattern matching of the exported chains is unverified until a compile succeeds.
