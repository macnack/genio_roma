# DX-COM calibration

> Compact of docs/deepx/calibration.md. Full text and extended citations are in the source file.

## Officially documented facts

Data
- Default calibration data: image files (JPEG, PNG). Non-image data needs the `dx_com` Python module with a torch DataLoader. [dx-compiler@a087726ead v2.5.0: source/docs/02_06_Execution_of_DX-COM.md#L14-L18]
- `calibration_num`: default 100, positive integer; if dataset is smaller, all images are used without warning; manual suggests trying 1, 5, 10, 100, 1000. [dx-compiler@a087726ead v2.5.0: source/docs/02_05_JSON_File_Configuration.md#L83-L87]
- Harness: 100-image sample set fetched by `example/2-download_sample_calibration_dataset.sh` into `dx_com/calibration_dataset/`. [dx-compiler@a087726ead v2.5.0: .deepx/instructions/compilation-workflow.md#L36-L40]
- Harness pitfall (not manual): calibration images should be representative of inference data. [dx-compiler@a087726ead v2.5.0: .deepx/memory/common_pitfalls.md#L55-L74]

JSON keys
| Key | Required | Meaning |
|---|---|---|
| `inputs` | Yes | `{"name": [1,C,H,W]}`; batch 1; name must match ONNX |
| `calibration_method` | No | `"ema"` (default), `"minmax"`, `"iqr"`; lowercase only |
| `calibration_num` | No | default 100 |
| `default_loader` | Yes | dataset + preprocessing |
| `quantization_device` | No | deprecated, ignored in v2.5.0 |
[dx-compiler@a087726ead v2.5.0: source/docs/02_05_JSON_File_Configuration.md#L9-L19] [dx-compiler@a087726ead v2.5.0: source/docs/02_05_JSON_File_Configuration.md#L57-L70]
- Methods: `ema` (exponential moving average, recommended), `minmax`, `iqr` (25th/75th percentile, robust to outliers). [dx-compiler@a087726ead v2.5.0: source/docs/02_05_JSON_File_Configuration.md#L59-L68]
- `default_loader` example: `dataset_path` + `file_extensions` ["jpeg","png","jpg","JPEG"] + preprocessings: resize 224x224, convertColor BGR2RGB, div x 255, normalize mean [0.485,0.456,0.406] std [0.229,0.224,0.225], transpose [2,0,1], expandDim axis 0. [dx-compiler@a087726ead v2.5.0: source/docs/02_05_JSON_File_Configuration.md#L102-L117]
- `dataset_path` relative paths resolve from CWD, not the config file; `file_extensions` required, no dot, case-sensitive; subfolders searched. [dx-compiler@a087726ead v2.5.0: source/docs/02_05_JSON_File_Configuration.md#L123-L124]

Preprocessing and layout
- `default_loader` reads OpenCV BGR, HWC, uint8 (0-255); applies only listed `preprocessings` in order; never rescales, converts color or transposes by itself. [dx-compiler@a087726ead v2.5.0: source/docs/02_05_JSON_File_Configuration.md#L119]
- NCHW models: end with `transpose [2,0,1]` then `expandDim 0`; without transpose calibration fails with `DataLoaderError`. [dx-compiler@a087726ead v2.5.0: source/docs/02_05_JSON_File_Configuration.md#L121] NHWC `[1,H,W,C]` models: only `expandDim 0` (harness schema note). [dx-compiler@a087726ead v2.5.0: .deepx/toolsets/config-schema.md#L127-L135]
- RGB model trained on [0,1]: `convertColor BGR2RGB` and `div 255` before `normalize`. `normalize` alone does not rescale; compile still succeeds with wrongly scaled data. [dx-compiler@a087726ead v2.5.0: source/docs/02_05_JSON_File_Configuration.md#L122]
- Ops: `convertColor` (RGB2BGR, BGR2RGB, *2GRAY, *2YCrCb, *2YUV, *2HSV, *2LAB), `resize` (`mode` default/torchvision; `width`/`height` or `size`; `interpolation`), `centercrop`, `transpose`, `expandDim`, `normalize`, `mul`, `add`, `subtract`, `div`. [dx-compiler@a087726ead v2.5.0: source/docs/02_05_JSON_File_Configuration.md#L487-L563] Python table adds `resize2`/`resize3`/`resize_tv`, `centercrop2`, `squeeze`, `slice`, `dtype`, `pil_2_cv`. [dx-compiler@a087726ead v2.5.0: source/docs/02_06_Execution_of_DX-COM.md#L412-L428]
- Interpolation (mode-specific uppercase): `default`: LINEAR, NEAREST, CUBIC, AREA, LANCZOS4; `torchvision`: BILINEAR, NEAREST, BICUBIC, LANCZOS; cubic resize raises NotSupportError. [dx-compiler@a087726ead v2.5.0: source/docs/02_05_JSON_File_Configuration.md#L507-L512] [dx-compiler@a087726ead v2.5.0: source/docs/02_06_Execution_of_DX-COM.md#L772]
- normalize, div, subtract may be folded into the NPU graph; check `[INFO] - Added nodes:` in log and drop those steps from host code. `convertColor` is never folded, so runtime must apply it. [dx-compiler@a087726ead v2.5.0: source/docs/02_05_JSON_File_Configuration.md#L451-L497]
- Calibration preprocessing must match deployment preprocessing. [dx-compiler@a087726ead v2.5.0: source/docs/02_06_Execution_of_DX-COM.md#L366-L367]
- Python DataLoader: batch_size 1; items shaped as model input without batch dim (e.g. `[3,224,224]`), float32; batched sample must match ONNX input exactly; item may be tensor, dict keyed by input name (recommended for multi-input), or list/tuple. [dx-compiler@a087726ead v2.5.0: source/docs/02_06_Execution_of_DX-COM.md#L430-L434]
- Resume: calibration settings embedded in `.qxnn`; `--dataset_path` overrides dataset; `--recalibration_method` overrides observer. [dx-compiler@a087726ead v2.5.0: source/docs/02_07_Quantization_Tuning_Workflow.md#L91] [dx-compiler@a087726ead v2.5.0: source/docs/02_07_Quantization_Tuning_Workflow.md#L142-L145]
- dx-modelzoo YAML: `compile.calibration.method`, `.num`, `.seed`, `.use_q_pro` (modelzoo layer, not DX-COM JSON keys). [dx-modelzoo@ab3e3a4234 v1.0.0: docs/source/02_03_YAML_Configuration.md#L320-L325]
- Q-Master reuses `default_loader` as the single preprocessing source; use training-like images, not the evaluation set. [dx-compiler@a087726ead v2.5.0: source/docs/02_08_Quantization_Aware_Training.md#L39] [dx-compiler@a087726ead v2.5.0: source/docs/02_08_Quantization_Aware_Training.md#L77-L81]

## Experimentally verified facts

None yet (no DX-M1 available on host as of 2026-11-05).
- **Calibration-subset sensitivity (DX-COM 2.4.1, ema, N=100, 5 seeded random subsets of the 1000-image pool, 4000 eval images):** A-tiny Top-1 80.73-81.25% (spread 0.52 pt, inside the +-1.2 pt CI) but logit cosine 0.811-0.939; B-tiny feature cosine 0.792-0.909 (spread 0.117). Same seed twice gives md5-identical `.dxnn` (deterministic). The default build (B 0.734) is below all five subsets and the checkpoint-resume build (B 0.914) above all five, so the earlier resume/iqr gains are not distinguishable from subset luck. The API on the full pool with N=100 reproduces the CLI default byte for byte, but its 100 images are not the first 100 by name; which ones is unknown. (`reports/calibration_sensitivity.md`, `scripts/calib_sweep.sh`)
- **Held-out subset search and size sweep (B-tiny, 500-image held-out `sel` half, API ema):** N=100 over 10 seeds cosine 0.793-0.914; N=20 0.806; N=250 0.920; N=500 0.922 (one seed per size). The best N=100 subset chosen on `sel` scored 0.915 on the 4000 eval images (default build 0.734). B-small with the same recipe: 0.974 (N=100) and 0.970 (N=500), below its earlier default 0.984. (`reports/calibration_sensitivity.md`, `scripts/calib_sel_sweep.sh`)

## Hypotheses needing validation

- ConvNeXt-Tiny preprocessing: torchvision/timm ImageNet recipe (resize 256 shortest side -> centercrop 224, RGB, /255, ImageNet mean/std) is inferred from the general QAT example using `resize {"mode":"default","size":256}` + `centercrop`. [dx-compiler@a087726ead v2.5.0: source/docs/02_08_Quantization_Aware_Training.md#L59-L66] Our checkpoint using these exact values is an assumption; verify against the training config. Also check that `resize` with `size` matches training shortest-side semantics (settle by comparing tensors against torchvision on one image).
- Whether `default_loader` (OpenCV resize, BGR->RGB) numerically matches the PIL-based training pipeline; docs offer `mode: torchvision` (PIL) for resize. Compare FP32 ONNX accuracy under both.
- Minimum useful calibration size for ConvNeXt (docs say default 100, try 1..1000). Sweep and compare accuracy.
- Whether normalize/div fold into the NPU graph for our model (check `Added nodes` log), which sets host-side runtime preprocessing. Runtime input dtype (uint8 vs float32) is a DX-RT matter, not answered here.
- dx-modelzoo `preprocessing` config for calibration data: not read in detail.
