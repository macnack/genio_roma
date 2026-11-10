# DX-M1 accuracy vs calibration subset (DX-COM 2.4.1, ConvNeXt-Tiny)

Question: how much does DX-M1 INT8 accuracy change with *which* 100 calibration images are used? Method fixed (`ema`, N=100), model fixed, only the subset varies. 2026-11-09.

## Method
- Pool: `data/imagenet_subset/calib` (1000 jpgs, one per class, disjoint from the 4000 eval images). Subsets: `scripts/make_calib_subset.py --seed S` (seeded random sample of 100, manifest with sha256; seeds 0-4; pairwise overlap 6-12 images).
- Build: `scripts/compile_dxnn_api.py ... ema 100 --dataset <subset>` (Python API; the CLI/JSON route ignores calibration keys, see `docs/deepx/compiler.md`). Evaluate: `scripts/eval_dx_board.py` on 4000 eval images (board, RT 3.4.2), score with `scripts/compare_acc.py` against FP32 ONNX. Sweep driver: `scripts/calib_sweep.sh`. All builds: 1 NPU group, 0 CPU groups.

## Results
A-tiny (ConvNeXt-Tiny, classifier; FP32 Top-1 81.925%):

| Calibration | Top-1 % | Top-1 agreement with FP32 | Logit cosine | KL(ref,dev) |
|---|---|---|---|---|
| seed 0 | 80.73 | 92.55 | 0.811 | 0.115 |
| seed 1 | 81.00 | 92.95 | 0.921 | 0.060 |
| seed 2 | 81.25 | 94.25 | 0.939 | 0.049 |
| seed 3 | 80.93 | 92.53 | 0.871 | 0.086 |
| seed 4 | 80.83 | 92.15 | 0.860 | 0.097 |
| control: default build (loader's own 100) | 80.80 | 92.23 | 0.883 | 0.105 |
| control: checkpoint-resume path | 80.03 | 90.97 | 0.855 | 0.126 |

B-tiny (DINOv3, 768-d feature; cosine vs FP32):

| Calibration | Cosine mean | Cosine min | Rel L2 |
|---|---|---|---|
| seed 0 | 0.828 | 0.500 | 0.573 |
| seed 1 | 0.870 | 0.545 | 0.502 |
| seed 2 | 0.909 | 0.651 | 0.409 |
| seed 3 | 0.853 | 0.432 | 0.526 |
| seed 4 | 0.792 | 0.425 | 0.624 |
| first 100 files by name (classes 0-99 only) | 0.885 | 0.566 | - |
| control: default build | 0.734 | 0.314 | 0.716 |
| control: checkpoint-resume path | 0.914 | 0.681 | 0.399 |

## Spread (5 random subsets)
- A-tiny Top-1: 80.73-81.25 % (range 0.52 pt, std 0.20 pt), inside the +-1.2 pt CI: Top-1 is insensitive to the subset. Logit cosine 0.811-0.939 (range 0.128, std 0.051) and KL 0.049-0.115: output fidelity is not.
- B-tiny feature cosine: 0.792-0.909 (range 0.117, std 0.044). Calibration choice moves B-tiny fidelity by more than any option tried earlier.

## Conclusions and caveats
- Verified: compilation is deterministic (same seed twice gave md5-identical `.dxnn`, `862b0984...`), so the spread is a subset effect, not compile noise.
- Verified: the API with the full pool and N=100 reproduces the original CLI default byte for byte (`25f0f95d...`), so the default build used some deterministic 100 images chosen by the loader. Which ones is unknown; it is NOT the first 100 by name (that build differs, `063e8b27...`).
- The default B-tiny build (0.734) is lower than all five random subsets; the checkpoint-resume build (0.914) is higher than all five. Earlier explanations for the resume gain ("iqr", "resume path") are therefore not distinguishable from calibration-subset luck: the resume path calibrates on a different (99-image) sample. Hypothesis, not verified.
- Class coverage is not the cause: calibration on only classes 0-99 gave 0.885, better than three of five random subsets.
- Five seeds is a small sample; the true spread may be wider. Subset size was varied only in the follow-up below (one seed per size).
- No subset in the first 5-seed sweep was selected on the eval images (see the held-out follow-up for the tuned choice).
- Not explained: why the loader's default pick and the resume path differ from random subsets; why A's Top-1 is stable while its logit cosine swings.

## Follow-up 2026-11-10: held-out subset search and size sweep (B-tiny)
Method: the 1000-image calib pool is split (seed 123, `scripts/make_calib_split.py`) into `src` (500, calibration source) and `sel` (500, held-out scoring set, never calibrated on, disjoint from the 4000 eval images). Reference: FP32 ONNX on `sel` (`reports/acc/Bsel_fp32_out.npy`). Builds via `scripts/calib_sel_sweep.sh` (API, ema); all builds 1 NPU group, 0 CPU groups.

| Build (subset of `src`) | cosine on `sel` | min |
|---|---|---|
| N=100 seeds 0,1,2,6 | 0.793 / 0.826 / 0.803 / 0.793 | 0.38-0.45 |
| N=100 seeds 4,5 | 0.877 / 0.873 | 0.51 / 0.55 |
| N=100 seeds 7,8,9 | 0.900 / 0.901 / 0.902 | 0.64-0.72 |
| N=100 seed 3 (best) | 0.914 | 0.729 |
| N=20 seed 3 | 0.806 | 0.418 |
| N=250 seed 3 | 0.920 | 0.674 |
| N=500 seed 0 (all of `src`) | 0.922 | 0.690 |

- Selected seed 3 on `sel`, then ONE confirmation on the 4000 eval images: cosine 0.9152 (min 0.715) vs 0.734 for the default build. Selection did not overfit (0.914 held-out vs 0.915 eval).
- Size trend: 20 -> 0.806; 100 -> 0.79-0.91 (10 seeds); 250 -> 0.920; 500 -> 0.922. N>=250 matches the best N=100 seed without selection. One seed per size, so a trend, not a proof; N=250/500 not confirmed on the 4000 images.
- B-small (4000 eval images, API ema, `scripts/bs_rebuild.sh`): seed 3 N=100 cosine 0.9743 (min 0.861); seed 0 N=500 0.9702 (min 0.790). Both below the earlier default build (0.984): the lever that helps B-tiny does not help B-small. Unknown why.
- B-tiny stays below the 0.95 bar proposed for the issue (best 0.915 confirmed). Unknown whether larger N than 500 (needs a bigger pool) helps.
