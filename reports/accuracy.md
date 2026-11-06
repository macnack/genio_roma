# Accuracy and latency of ConvNeXt on DX-M1 (Genio-700 board, RT 3.4.2, DX-COM 2.4.1)

Data: 4000 ImageNet-1K validation images (4 per class, seed 0, `scripts/make_imagenet_subset.py`); calibration: 100 images from a
disjoint 1-per-class set (EMA unless noted). Preprocessing: resize 256 bicubic, center-crop 224, RGB (`scripts/preproc.py`).
Reference: ONNX FP32 (opset 13) on laptop CPU. Device: `dx_engine` sync, uint8 NHWC input, batch 1, single run at a time.
Top-1 95% interval is about +-1.2 points at n=4000; differences below that are not significant. Raw files: `reports/acc/`.

## Classifiers (A = facebookresearch ConvNeXt, ImageNet-1K EMA weights)
| Model / quantisation | Top-1 FP32 -> DX-M1 | Top-5 FP32 -> DX-M1 | logit cosine | top-1 agreement | KL | NPU ms | latency ms | compile |
|---|---|---|---|---|---|---|---|---|
| A-tiny, PTQ EMA | 81.9 -> 80.8 | 95.9 -> 95.5 | 0.883 | 92.2% | 0.105 | 35.28 | 40.06 (p95 40.35) | 108 s |
| A-tiny, PTQ minmax | 80.8 (byte-identical .dxnn to EMA) | same | same | same | same | 35.28 | same | 112 s |
| A-tiny, Q-Pro (`--use_q_pro`) | 81.9 -> 79.8 | 95.9 -> 95.4 | 0.911 | 91.6% | 0.091 | 35.28 | 39.97 | 9424 s |
| A-small, PTQ EMA | 83.1 -> 82.0 | 96.2 -> 95.9 | 0.901 | 92.8% | 0.085 | 60.65 | 65.31 | 389 s |

## Feature models (B = HF DINOv3 ConvNeXt, pooled 768-d, no labels)
| Model | cosine mean (min) vs FP32 | rel. L2 | NPU ms | latency ms | compile |
|---|---|---|---|---|---|
| B-tiny, PTQ EMA | 0.734 (0.314) | 0.723 | 35.32 | 40.01 | 424 s |
| B-small, PTQ EMA | 0.984 (0.847) | 0.171 | 60.69 | 66.11 | 481 s |

## Observations (not explained)
- All variants compile as `1 NPU groups, 0 CPU groups` despite 18 (tiny) / 36 (small) depthwise 7x7 convs; `dxparse` shows a single `npu_0` task.
- `calibration_method` ema vs minmax gave a byte-identical `.dxnn` for A-tiny.
- Q-Pro did not improve Top-1 over PTQ here (difference inside the interval), but improved logit cosine/KL; cost 87x compile time.
- B-tiny feature fidelity is poor under PTQ (cosine 0.73) while B-small is good (0.98); cause not investigated.
- Latency/NPU time is identical for tiny across quantisation modes; model-only, preprocessing excluded. Single-request mode only; no benchmark-mode throughput yet.
