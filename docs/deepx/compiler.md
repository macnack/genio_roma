# DX-COM compiler pipeline

Scope: what DX-COM (`dxcom` CLI / `dx_com` Python module) takes in, does, and emits. Version pinned: DX-COM v2.5.0. Follows [CONVENTIONS.md](CONVENTIONS.md).

## Officially documented facts

Role and I/O
- DX-COM converts a pre-trained ONNX model plus a configuration JSON file into a hardware-optimized `.dxnn` binary for DEEPX NPUs; the ONNX holds structure and weights, the JSON holds pre/post-processing settings and compilation parameters. [dx-compiler@a087726ead v2.5.0: source/docs/01_DXNN_Compiler_Overview.md#L8]
- `dx_com.compile()` "performs quantization, optimization, partitioning, and generates compiled artifacts including the `.dxnn` file." [dx-compiler@a087726ead v2.5.0: source/docs/02_06_Execution_of_DX-COM.md#L240]
- Output format is `.dxnn` file format v9 (v2.5.0 outputs v9 only); loading requires DX-RT v3.5.0 or later, DX-RT v3.4.2 and earlier cannot load it. [dx-compiler@a087726ead v2.5.0: source/docs/02_01_System_Requirements_of_DX-COM.md#L13] [dx-compiler@a087726ead v2.5.0: source/docs/Appendix_Change_Log.md#L13]
- Output directory contains `[model_name].dxnn`, plus `compiler.log` (with `gen_log`) and `[model_name]_summary.html` (with `export_html`). [dx-compiler@a087726ead v2.5.0: source/docs/02_06_Execution_of_DX-COM.md#L756-L762]
- Compiled results may vary with CPU architecture, OS and other host factors; `--float64_calibration` is documented for cross-CPU determinism. [dx-compiler@a087726ead v2.5.0: source/docs/02_06_Execution_of_DX-COM.md#L23-L24] [dx-compiler@a087726ead v2.5.0: source/docs/02_06_Execution_of_DX-COM.md#L82]

Host requirements
- amd64 (x86_64) only, aarch64 NOT supported; RAM >= 16 GB; disk >= 8 GB; Ubuntu 20.04/22.04/24.04/26.04 (Ubuntu 18.04 unsupported); glibc >= 2.31; Python 3.8-3.14. [dx-compiler@a087726ead v2.5.0: source/docs/02_01_System_Requirements_of_DX-COM.md#L5-L12]

CLI (exactly as documented)
- Basic command: `dxcom -m model.onnx -c config.json -o output/` [dx-compiler@a087726ead v2.5.0: source/docs/02_06_Execution_of_DX-COM.md#L39]
- Format: `dxcom -m <MODEL_PATH> -c <CONFIG_PATH> -o <OUTPUT_DIR> [OPTIONS]`; required args `--model_path/-m`, `--config_path/-c`, `--output_dir/-o`. [dx-compiler@a087726ead v2.5.0: source/docs/02_06_Execution_of_DX-COM.md#L53-L62]
- Documented options: `--opt_level {0,1}` (default 1; 0 = fast compile/higher NPU latency, 1 = full optimization/lowest NPU latency), `--aggressive_partitioning` (experimental, maximize ops on NPU), `--use_gpu {True,False}` (default True, new in v2.5.0), `--float64_calibration`, `--use_q_pro`, `--quant_diagnosis`, `--checkpoint`, `--recalibration_method {minmax,ema,iqr}`, `--enhanced_scheme`, `--dataset_path` (last three resume-only), `--gen_log`, `--export_html`, `--verbose`, `--version/-v`, `--compile_input_nodes`, `--compile_output_nodes`. [dx-compiler@a087726ead v2.5.0: source/docs/02_06_Execution_of_DX-COM.md#L77-L155]
- `--compile_input_nodes` / `--compile_output_nodes` take comma-separated ONNX operator node names (not tensor names) and compile a subgraph. [dx-compiler@a087726ead v2.5.0: source/docs/02_06_Execution_of_DX-COM.md#L149-L158]
- Only single-input models are supported from the `dxcom` CLI; multi-input needs the `dx_com` Python module with a DataLoader. [dx-compiler@a087726ead v2.5.0: source/docs/02_06_Execution_of_DX-COM.md#L20-L21]

Python
- Signature (verbatim parameter list): `compile(model, output_dir, config=None, dataloader=None, calibration_method="ema", calibration_num=100, use_gpu=True, opt_level=1, aggressive_partitioning=False, input_nodes=None, output_nodes=None, use_q_pro=False, enhanced_scheme=None, ppu_config=None, qmaster=None, gen_log=False, float64_calibration=False, export_html=False, verbose=False, **kwargs) -> None`. [dx-compiler@a087726ead v2.5.0: source/docs/02_06_Execution_of_DX-COM.md#L247-L268]
- Minimal call:
  ```python
  import dx_com

  dx_com.compile(
      model="model.onnx",
      output_dir="./compiled",
      config="config.json",
  )
  ```
  [dx-compiler@a087726ead v2.5.0: source/docs/02_06_Execution_of_DX-COM.md#L720-L728]
- `config` and `dataloader` are mutually exclusive; one must be given; DataLoader `batch_size` must be 1; with a `dataloader` the JSON `default_loader.preprocessings` is not used. [dx-compiler@a087726ead v2.5.0: source/docs/02_06_Execution_of_DX-COM.md#L320-L367]

Partitioning, report
- `--aggressive_partitioning` is experimental, may give unexpected results, may raise compile time/memory; benefits hosts with weak CPU, default partitioning may be faster end-to-end on strong hosts. [dx-compiler@a087726ead v2.5.0: source/docs/02_06_Execution_of_DX-COM.md#L90-L94]
- The compilation summary HTML (`--export_html`) has a graph viewer showing "NPU vs CPU workload distribution and per-partition CPU-fallback reasons"; generation is best-effort and never blocks compilation. [dx-compiler@a087726ead v2.5.0: source/docs/04_Compilation_Summary_Report.md#L13] [dx-compiler@a087726ead v2.5.0: source/docs/04_Compilation_Summary_Report.md#L75-L76]
- DX-TRON is removed as of v2.5.0; use `--export_html` instead. [dx-compiler@a087726ead v2.5.0: source/docs/Appendix_Change_Log.md#L9]
- Preprocessing ops (e.g. `normalize`, `div`, `subtract`) may be integrated into the NPU graph; the compile log line `[INFO] - Added nodes:` shows which, and those must then be removed from host code; `convertColor` is not integrated (listed under `Skipped nodes` in `compiler.log`). Integration is not guaranteed. [dx-compiler@a087726ead v2.5.0: source/docs/02_05_JSON_File_Configuration.md#L451-L497]

Errors (names as documented)
- NotSupportError (multi-input via CLI, dynamic input shape, cubic resize), ConfigFileError, ConfigInputError, DatasetPathError, NodeNotFoundError ("ONNX model contains a node that is unsupported by the compiler"), NotsupportedPaddingError (e.g. asymmetric padding in width and height), DataNotFoundError, OnnxFileNotFound, plus host-check errors. [dx-compiler@a087726ead v2.5.0: source/docs/02_06_Execution_of_DX-COM.md#L770-L785]

Other
- GPU is optional for PTQ: quantization uses CUDA GPU when available, else CPU; JSON `quantization_device` is deprecated/ignored since v2.5.0. [dx-compiler@a087726ead v2.5.0: source/docs/02_05_JSON_File_Configuration.md#L136-L143]
- Web docs navigation lists DX-COM pages (Quick Start, Overview, ONNX/JSON config, Execution, Supported ONNX Operators at `Building_Models/`, Quantization Tuning, QAT, Pre-Optimize, Use Cases, Summary Report, Change Log). [developer.deepx.ai/tech-docs/DXNN-SDK/DX-COM/Quick_Start/, fetched 2026-11-05] (Note: the fetched site nav still lists DX-TRON, i.e. it reflects an older release than the repo; see Hypotheses.)

## Experimentally verified facts

- DX-COM 2.4.1 compiled ConvNeXt-Tiny and -Small (A: facebookresearch IN-1K; B: HF DINOv3) as **1 NPU group, 0 CPU groups**, although the 2.4.1 tables list depthwise kernels 3x3/5x5 only and have no `LayerNormalization` row (the models have 18/36 depthwise 7x7 convs). The tables are conservative or incomplete; support is verified by compiling. (`reports/ops.md`; `models/A_fb_in1k/real_ptq13/compiler.log`)
- The `SURGERY` "UnknownError" we first hit was caused by our own config (missing official preprocessing block), not by the model, the ops, the dependency versions or the compiler version. Which single key triggers it was not isolated. (`reports/ops.md`, "Correction")
- Official-style preprocessing config works: resize 256 bicubic, centercrop 224, convertColor BGR2RGB, div 255, normalize, transpose [2,0,1], expandDim 0, `quantization_device: cpu`. The compiler fuses div/normalize/transpose; NPU input is uint8 NHWC [1,224,224,3]. (`scripts/compile_dxnn.sh`, `models/A_fb_in1k/real_ptq13/config.json`)
- Compile times (laptop): A-tiny PTQ 108 s, A-small 389 s, B-tiny 424 s, B-small 481 s, A-tiny Q-Pro 9424 s. (`models/*/real_*/compile_time.txt`)
- **`calibration_method` / `calibration_num` in `config.json` are ignored by the 2.4.1 CLI** (`dxcom -m ... -c config.json`): a fresh compile of B-tiny with `"calibration_method":"iqr","calibration_num":1000` produced a `.dxnn` md5-identical to the default ema/100 build, and the log showed `Calibration .../100`. This explains the earlier byte-identical A-tiny `ema` vs `minmax` result (`models/B_dinov3/iqr1000/`, `real_ptq13/`). Methods that DO take effect: (a) the Python API `dx_com.compile(model=, output_dir=, config=, calibration_method=, calibration_num=, ...)` (log showed `Calibration .../1000`), whose 2.4.1 signature was read with `inspect.signature`; (b) `--checkpoint x.qxnn` resume (changes the build, but see the next item: its `--recalibration_method` has no effect). `scripts/compile_dxnn_api.py` wraps (a). All earlier A-model calibration-method/count comparisons made through the CLI/JSON route therefore compared identical builds.
- **`--recalibration_method {minmax,ema,iqr}` is a no-op in DX-COM 2.4.1.** Resuming the same `.qxnn` with `ema`, `minmax` and `iqr` gives md5-identical `.dxnn` for both A-tiny (`35d5ede3...`) and B-tiny (`e40985d9...`; `models/*/rq_{ema,minmax,iqr}/`). Earlier text attributing B's gain to `iqr` was wrong. What does change the build is the resume path itself (`--quant_diagnosis` then `--checkpoint`), which re-quantizes differently from the original compile: B-tiny feature cosine vs FP32 0.734 -> 0.914 (4000 images), A-tiny Top-1 80.8% -> 80.0% (cosine 0.855, same 4000 images). Why the resume differs from the original compile is unknown (hypothesis: different calibration sample handling, the resume log shows 99 captured samples; PTQ outcome may be sensitive to the calibration subset). `--enhanced_scheme` P0 (alpha 0.5) resume gave B-tiny cosine 0.886 (a different build, md5 `51fdd148...`); iqr+P0 equals P0 alone because the method flag does nothing. Q-Pro (API, 100 calib, ~2.5 h) gave 0.569 (worse than default PTQ); API fresh iqr/1000 gave 0.683 (calibration_num is honoured by the API; the method effect there is untested). `--quant_diagnosis` for B-tiny: weight-only cosine 0.9990, activation-only 0.9513 => activation-quantisation dominated; B-small baseline 0.984. (`reports/acc/B13_*`, `A13_rq_*`)
- Q-Pro (`--use_q_pro`) did not improve Top-1 over plain PTQ (79.8% vs 80.8%, inside the +-1.2-point interval) though logit cosine/KL improved. (`reports/accuracy.md`)

## Hypotheses needing validation

- Which ONNX nodes land on CPU vs NPU for our ConvNeXt-Tiny is not stated by any doc; settle by compiling with `--export_html` and reading the graph viewer / `compiler.log`.
- Exact on-disk layout of `.dxnn` and whether a CPU subgraph is embedded in it or needs a separate runtime (ONNX Runtime) is not documented in the compiler docs. The dx-modelzoo YAML has a `use_ort: true` runtime comment "Run unsupported ops on ONNX Runtime" [dx-modelzoo@ab3e3a4234 v1.0.0: docs/source/02_03_YAML_Configuration.md#L280]; whether this is what DX-RT does for CPU partitions needs DX-RT docs/experiment.
- The web docs (developer.deepx.ai, still listing DX-TRON and v2.4.0 nav) may lag the repo (v2.5.0); the repo was treated as authoritative. Check page version when quoting web.
- The DX-COM User Manual 2.5.0 appears on the Document Download page (dated Nov 4, 2026) but all file links were placeholders in the fetched content, so format (likely PDF) and URL are unknown. [developer.deepx.ai/document-download/, fetched 2026-11-05] Check whether it contains material beyond the repo `source/docs`.
- Compile determinism across hosts is explicitly not guaranteed; if reproducible `.dxnn` matters, test with `--float64_calibration` on two machines.
- Why `minmax` and `ema` give identical output, and which preprocessing key triggers `SURGERY` on the first config, are open.
