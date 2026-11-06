# DX-COM compiler pipeline

> Compact of docs/deepx/compiler.md. Full text and extended citations are in the source file.

Scope: DX-COM (`dxcom` CLI / `dx_com` Python module) v2.5.0.

## Officially documented facts

Role and I/O
- ONNX (structure + weights) plus config JSON (pre/post-processing, compile params) -> hardware-optimized `.dxnn`. [dx-compiler@a087726ead v2.5.0: source/docs/01_DXNN_Compiler_Overview.md#L8]
- `dx_com.compile()` "performs quantization, optimization, partitioning, and generates compiled artifacts including the `.dxnn` file." [dx-compiler@a087726ead v2.5.0: source/docs/02_06_Execution_of_DX-COM.md#L240]
- Output is `.dxnn` format v9 only; loading requires DX-RT v3.5.0 or later (DX-RT v3.4.2 and earlier cannot load it). [dx-compiler@a087726ead v2.5.0: source/docs/02_01_System_Requirements_of_DX-COM.md#L13] [dx-compiler@a087726ead v2.5.0: source/docs/Appendix_Change_Log.md#L13]
- Output dir: `[model_name].dxnn`, plus `compiler.log` (`gen_log`) and `[model_name]_summary.html` (`export_html`). [dx-compiler@a087726ead v2.5.0: source/docs/02_06_Execution_of_DX-COM.md#L756-L762]
- Results may vary with CPU architecture, OS, host factors; `--float64_calibration` documented for cross-CPU determinism. [dx-compiler@a087726ead v2.5.0: source/docs/02_06_Execution_of_DX-COM.md#L23-L24] [dx-compiler@a087726ead v2.5.0: source/docs/02_06_Execution_of_DX-COM.md#L82]

Host requirements
- amd64 (x86_64) only, aarch64 NOT supported; RAM >= 16 GB; disk >= 8 GB; Ubuntu 20.04/22.04/24.04/26.04 (18.04 unsupported); glibc >= 2.31; Python 3.8-3.14. [dx-compiler@a087726ead v2.5.0: source/docs/02_01_System_Requirements_of_DX-COM.md#L5-L12]

CLI
- `dxcom -m model.onnx -c config.json -o output/`. [dx-compiler@a087726ead v2.5.0: source/docs/02_06_Execution_of_DX-COM.md#L39]
- `dxcom -m <MODEL_PATH> -c <CONFIG_PATH> -o <OUTPUT_DIR> [OPTIONS]`; required `--model_path/-m`, `--config_path/-c`, `--output_dir/-o`. [dx-compiler@a087726ead v2.5.0: source/docs/02_06_Execution_of_DX-COM.md#L53-L62]
- Options: `--opt_level {0,1}` (default 1; 0 = fast compile/higher NPU latency, 1 = full optimization/lowest latency); `--aggressive_partitioning` (experimental); `--use_gpu {True,False}` (default True, new in v2.5.0); `--float64_calibration`; `--use_q_pro`; `--quant_diagnosis`; `--checkpoint`; `--recalibration_method {minmax,ema,iqr}`; `--enhanced_scheme`, `--dataset_path` (last three resume-only); `--gen_log`; `--export_html`; `--verbose`; `--version/-v`; `--compile_input_nodes`; `--compile_output_nodes`. [dx-compiler@a087726ead v2.5.0: source/docs/02_06_Execution_of_DX-COM.md#L77-L155]
- `--compile_input_nodes` / `--compile_output_nodes`: comma-separated ONNX operator node names (not tensor names); compiles a subgraph. [dx-compiler@a087726ead v2.5.0: source/docs/02_06_Execution_of_DX-COM.md#L149-L158]
- CLI supports single-input models only; multi-input needs `dx_com` Python with a DataLoader. [dx-compiler@a087726ead v2.5.0: source/docs/02_06_Execution_of_DX-COM.md#L20-L21]

Python
- `compile(model, output_dir, config=None, dataloader=None, calibration_method="ema", calibration_num=100, use_gpu=True, opt_level=1, aggressive_partitioning=False, input_nodes=None, output_nodes=None, use_q_pro=False, enhanced_scheme=None, ppu_config=None, qmaster=None, gen_log=False, float64_calibration=False, export_html=False, verbose=False, **kwargs) -> None`. [dx-compiler@a087726ead v2.5.0: source/docs/02_06_Execution_of_DX-COM.md#L247-L268]
- Minimal call: [dx-compiler@a087726ead v2.5.0: source/docs/02_06_Execution_of_DX-COM.md#L720-L728]
  ```python
  import dx_com
  dx_com.compile(model="model.onnx", output_dir="./compiled", config="config.json")
  ```
- `config` and `dataloader` are mutually exclusive; one required; DataLoader `batch_size` must be 1; with `dataloader`, JSON `default_loader.preprocessings` is unused. [dx-compiler@a087726ead v2.5.0: source/docs/02_06_Execution_of_DX-COM.md#L320-L367]

Partitioning and report
- `--aggressive_partitioning`: experimental, may give unexpected results, may raise compile time/memory; helps weak-CPU hosts; default may be faster end-to-end on strong hosts. [dx-compiler@a087726ead v2.5.0: source/docs/02_06_Execution_of_DX-COM.md#L90-L94]
- Summary HTML (`--export_html`): graph viewer with "NPU vs CPU workload distribution and per-partition CPU-fallback reasons"; best-effort, never blocks compilation. [dx-compiler@a087726ead v2.5.0: source/docs/04_Compilation_Summary_Report.md#L13] [dx-compiler@a087726ead v2.5.0: source/docs/04_Compilation_Summary_Report.md#L75-L76]
- DX-TRON removed in v2.5.0; use `--export_html`. [dx-compiler@a087726ead v2.5.0: source/docs/Appendix_Change_Log.md#L9]
- Preprocessing ops (e.g. `normalize`, `div`, `subtract`) may be integrated into the NPU graph (shown by `[INFO] - Added nodes:` in log); remove them from host code. `convertColor` not integrated (listed under `Skipped nodes` in `compiler.log`). Not guaranteed. [dx-compiler@a087726ead v2.5.0: source/docs/02_05_JSON_File_Configuration.md#L451-L497]

Errors (documented names)
- NotSupportError (multi-input via CLI, dynamic input shape, cubic resize), ConfigFileError, ConfigInputError, DatasetPathError, NodeNotFoundError ("ONNX model contains a node that is unsupported by the compiler"), NotsupportedPaddingError (e.g. asymmetric padding in width and height), DataNotFoundError, OnnxFileNotFound, plus host-check errors. [dx-compiler@a087726ead v2.5.0: source/docs/02_06_Execution_of_DX-COM.md#L770-L785]

Other
- PTQ uses CUDA GPU when available, else CPU; JSON `quantization_device` deprecated/ignored since v2.5.0. [dx-compiler@a087726ead v2.5.0: source/docs/02_05_JSON_File_Configuration.md#L136-L143]
- Web nav lists DX-COM pages (Quick Start, Overview, ONNX/JSON config, Execution, Supported ONNX Operators at `Building_Models/`, Quantization Tuning, QAT, Pre-Optimize, Use Cases, Summary Report, Change Log). [developer.deepx.ai/tech-docs/DXNN-SDK/DX-COM/Quick_Start/, fetched 2026-11-05] Note: the fetched nav still lists DX-TRON, i.e. an older release than the repo; see Hypotheses.

## Experimentally verified facts

- DX-COM 2.4.1 compiled ConvNeXt-Tiny and -Small (A: facebookresearch IN-1K; B: HF DINOv3) as **1 NPU group, 0 CPU groups**, although the 2.4.1 tables list depthwise kernels 3x3/5x5 only and have no `LayerNormalization` row (the models have 18/36 depthwise 7x7 convs). The tables are conservative or incomplete; support is verified by compiling. (`reports/ops.md`; `models/A_fb_in1k/real_ptq13/compiler.log`)
- The `SURGERY` "UnknownError" we first hit was caused by our own config (missing official preprocessing block), not by the model, the ops, the dependency versions or the compiler version. Which single key triggers it was not isolated. (`reports/ops.md`, "Correction")
- Official-style preprocessing config works: resize 256 bicubic, centercrop 224, convertColor BGR2RGB, div 255, normalize, transpose [2,0,1], expandDim 0, `quantization_device: cpu`. The compiler fuses div/normalize/transpose; NPU input is uint8 NHWC [1,224,224,3]. (`scripts/compile_dxnn.sh`, `models/A_fb_in1k/real_ptq13/config.json`)
- Compile times (laptop): A-tiny PTQ 108 s, A-small 389 s, B-tiny 424 s, B-small 481 s, A-tiny Q-Pro 9424 s. (`models/*/real_*/compile_time.txt`)
- `calibration_method` `ema` vs `minmax` produced byte-identical `.dxnn` for A-tiny; unexplained. (`models/A_fb_in1k/real_minmax13/`, `reports/acc/A13_minmax_compare.json`)
- Q-Pro (`--use_q_pro`) did not improve Top-1 over plain PTQ (79.8% vs 80.8%, inside the +-1.2-point interval) though logit cosine/KL improved. (`reports/accuracy.md`)

## Hypotheses needing validation

- No doc says which ONNX nodes land on CPU vs NPU for our ConvNeXt-Tiny. Settle: compile with `--export_html`, read graph viewer and `compiler.log`.
- Exact `.dxnn` on-disk layout, and whether CPU subgraphs are embedded or need a separate runtime (ONNX Runtime), is not documented in compiler docs. dx-modelzoo YAML has `use_ort: true` with comment "Run unsupported ops on ONNX Runtime" [dx-modelzoo@ab3e3a4234 v1.0.0: docs/source/02_03_YAML_Configuration.md#L280]; whether DX-RT does this for CPU partitions needs DX-RT docs or an experiment.
- Web docs (developer.deepx.ai, still listing DX-TRON and v2.4.0 nav) may lag repo v2.5.0; repo treated as authoritative. Check page version when quoting web.
- DX-COM User Manual 2.5.0 appears on Document Download page (dated Nov 4, 2026) but file links were placeholders; format and URL unknown. [developer.deepx.ai/document-download/, fetched 2026-11-05] Check whether it has material beyond repo `source/docs`.
- Compile determinism across hosts is not guaranteed. If reproducible `.dxnn` matters, test with `--float64_calibration` on two machines.
- Why `minmax` and `ema` give identical output, and which preprocessing key triggers `SURGERY` on the first config, are open.
