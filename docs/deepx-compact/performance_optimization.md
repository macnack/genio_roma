# DX-RT performance, profiling and benchmarking

> Compact of docs/deepx/performance_optimization.md. Full text and extended citations are in the source file.

Citation prefixes: `RT` = `dx_rt@f997363c97 v3.5.0`, `BM` = `dx-all-suite@51d81fe2ef v2.5.0` (dx-benchmark), `dx_stream@c575ed2896 v3.2.0`, `dx_app@375de0344f v3.3.0`.

## Officially documented facts

### Measurement methodology and metrics
- `dxrun` metrics: NPU Processing Time (core compute), Queue Wait Time, E2E Response Time (incl. waits/transfer), Latency = E2E minus buffer-pool and queue wait, FPS = completed inputs per second. In benchmark mode, queue wait and E2E grow with `--buffer-count`. [RT: docs/source/docs/05_Command_Line_Interface.md#L199-L223]
- Per-job APIs: `GetLatency()` = E2E (v3.5.0 change), `GetCoreLatency()`, `GetNpuInferenceTime()`, plus mean/std/count/vector variants. [RT: RELEASE_NOTES.md#L9] [RT: lib/include/dxrt/inference_engine.h#L406-L419]
- `dxrun` modes: `-s/--single` (sequential, single core) vs `-b/--benchmark` (fixed buffer count; default); `-f` target-FPS; `-w` warmup; `-t` overrides `-l`. [RT: docs/source/docs/05_Command_Line_Interface.md#L70-L101]
- DX-Benchmark protocol: latency = `dxrun -s` 300 loops, 1 warmup, cold; throughput = `dxrun -t 30` after `--max-throughput` sweep (10 s probe x 3 repeats, 1% tolerance), 3 runs after cooldown and 2 s throw-away run; ORT ON and OFF both measured; NPU cooldown target `min(idle+10C, 55C)`. [BM: dx-benchmark/README.md#L328-L347]
- E2E pipeline FPS: DX-Stream (decode, `dxpreprocess`, `dxinfer`, `dxpostprocess`), 1080p30 H.264; channel capacity = max concurrent streams all >=30 fps. [BM: dx-benchmark/docs/ANALYSIS_EN.md#L32-L38]
- DX-APP examples print per-stage Performance Summary (read / pre / NPU / post / display) and FPS. [dx_app@375de0344f v3.3.0: docs/source/docs/01_DXNN_Application_Overview.md#L121-L139]
- DX-Stream: `dxinfer` reports moving-average inference time; GstShark `proctime` tracer measures per-element time (`GST_TRACERS`, `GST_SHARK_LOCATION`). [dx_stream@c575ed2896 v3.2.0: docs/source/docs/Elements/03_02_DxInfer.md#L67-L69] [dx_stream@c575ed2896 v3.2.0: docs/source/docs/Appendix_Performance_Evaluation_with_GstShark.md#L27-L42]

### Profiler
- `dxrun -m model.dxnn --profiler` writes `profiler.json`. App-level: `Configuration::ITEM::PROFILER` + `PROFILER_SHOW_DATA`/`PROFILER_SAVE_DATA` = `"ON"`. [RT: docs/source/docs/04_Model_Inference.md#L264-L295]
- `Profiler::GetJobMetrics(jobId)` after `Wait()`: input_format_us, h2d_us, inference_core_{all,0,1,2}_us, d2h_us, output_format_us, total_us, cpu_task_us. `GetPerformanceData*` deprecated. [RT: docs/source/docs/04_Model_Inference.md#L299-L364]
- Custom events: `profiler.Start("name")` / `End("name")` (Python `start/end`). [RT: docs/source/docs/04_Model_Inference.md#L368-L377]
- Plot: `python3 tool/profiler/plot.py -i profiler.json`; `tool/profiler/plot_html.py -i profiler.json [-o out.html]` (needs pandas, plotly). [RT: docs/source/docs/04_Model_Inference.md#L385-L442]
- Event remedies: Buffer Wait -> `export DXRT_DYNAMIC_CPU_THREAD=ON`; NPU Input/Output Format Handler -> NFH acceleration; CPU Task Queue Wait and `cpu_N` -> CPU op acceleration; PCIe Write / NPU Core / PCIe Read have none. [RT: docs/source/docs/04_Model_Inference.md#L450-L462]
- `dxtop` (live per-core util, temp, voltage, clock; see `runtime.md`); `dxcli -m <sec>` periodic status. [RT: docs/source/docs/05_Command_Line_Interface.md#L273-L274] [RT: docs/source/docs/05_Command_Line_Interface.md#L371-L380]

### Tuning knobs (documented)
- Async (`RunAsync`) with multiple buffers/threads; sync `Run` is sequential, one core; batch increases memory. [RT: docs/source/docs/06_Inference_API.md#L509-L515] [RT: docs/source/docs/09_01_C++_Tutorials.md#L18-L23]
- Keep callbacks short ("processing this callback as quickly as possible is beneficial"). [RT: docs/source/docs/09_01_C++_Tutorials.md#L85-L90]
- `bufferCount`: more buffers can improve pipelined throughput (1-100 in `dxrun`); `dxrun --max-throughput [--buffer-count 3-16]` picks it; NPU memory overflow at large counts terminates `dxrun`. [RT: docs/source/docs/04_Model_Inference.md#L79-L83] [RT: docs/source/docs/05_Command_Line_Interface.md#L146-L150] [RT: docs/source/docs/05_Command_Line_Interface.md#L194-L197]
- User-provided output buffers avoid per-call allocation. [RT: docs/source/docs/06_Inference_API.md#L502-L507]
- `NPU_ALL` (default) for max throughput; single-core binding partitions NPU between engines. [RT: docs/source/docs/04_Model_Inference.md#L62-L66]
- ORT ON runs CPU-side subgraphs inside the call; OFF returns raw NPU tensors. DX-Benchmark: ORT ON limits light models to 53-58% of NPU-only throughput on ARM hosts, 75-76% on x86 (size n); best mode for E2E FPS depends on host. [RT: docs/source/docs/04_Model_Inference.md#L695-L696] [BM: dx-benchmark/docs/ANALYSIS_EN.md#L135-L137] [BM: dx-benchmark/docs/ANALYSIS_EN.md#L559-L590]
- NFH acceleration (Intel IPP / ARM NEON) and CPU-op acceleration (OpenVINO / XNNPACK EP): off by default; need CMake `USE_NPU_FORMAT_CONVERSION_ACCELERATION=ON` / `USE_CPU_OP_ACCELERATION=ON` + `./build.sh --clean` (internet needed); runtime `Configuration::ITEM::NFH_ACCELERATION` / `CPU_OP_ACCELERATION` or `dxrun --accel-nfh --accel-cpu`. Orange Pi 5 Plus, v3.3.0, YoloV8S 84 -> 131 (both). CPU-op gain only for compute-heavy ops (Conv, MatMul). [RT: docs/source/docs/04_Model_Inference.md#L701-L822]
- Dynamic CPU threading: `export DXRT_DYNAMIC_CPU_THREAD=ON` (or config key `DXRT_DYNAMIC_CPU_THREAD=1`); runtime may print a hint. ORT threads: `CUSTOM_INTRA_OP_THREADS(_NUM)` / `CUSTOM_INTER_OP_THREADS(_NUM)`. [RT: docs/source/docs/04_Model_Inference.md#L824-L850] [RT: docs/source/docs/08_Global_Instance.md#L64-L79]
- `NFH_ASYNC` enabled by default. [RT: docs/source/docs/08_Global_Instance.md#L66]
- Host factors measured by DEEPX (YOLO26, 6 hosts): hardware video decoder, cooling (throttling drops NPU clock below nominal 1000 MHz, seen down to 300-800 MHz), host CPU, PCIe lane width (Gen3 x1: 39-47% lower NPU-only throughput on light 640x640 detection/segmentation, size n), host RAM (~32 MiB per channel median). [BM: dx-benchmark/docs/ANALYSIS_EN.md#L125-L143] [BM: dx-benchmark/docs/ANALYSIS_EN.md#L454-L485]
- Multi-model: separate engine per model; core binding partitions NPUs, but new `NPU_ALL` engine blocks until bound cores free. [RT: docs/source/docs/09_01_C++_Tutorials.md#L630-L632]
- DX-Stream `dxinfer`: `use-ort` (default true), `backend` auto/dxrt/dxvnpu; DxRate throttle QoS makes `dxinfer` drop frames in low-framerate pipelines. [dx_stream@c575ed2896 v3.2.0: docs/source/docs/Elements/03_02_DxInfer.md#L23-L31] [dx_stream@c575ed2896 v3.2.0: docs/source/docs/Elements/03_02_DxInfer.md#L73-L82]

## Experimentally verified facts

None yet (no DX-M1 available on host as of 2026-11-05).

## Hypotheses needing validation

- DEEPX FPS/latency numbers (M1 on Orange Pi/RPi5, YOLO26/YoloV8) will not transfer to our host/model. Need our own `dxrun -s -l 300` (latency) and `dxrun --max-throughput -t 30` (throughput) baselines.
- Whether our pipeline is host-bound (pre/post, decode) or NPU-bound. Settle with `dxtop` core Util during run plus `Profiler` events (Buffer Wait, Format Handler, `cpu_N`).
- Best ORT mode and `bufferCount` for our model on our host (DX-Benchmark shows host-dependent sign). Measure ON/OFF and sweep.
- Optimal number of Python submit threads / queue depth for `run_async` (docs give no number). Sweep 1..N threads with callback vs `wait`.
- Whether `dxtop` "Util" is meaningful for sub-second runs (DX-Benchmark notes ~1 Hz sampler, `README.md#L359-L363`). Use sustained runs.
- Acceleration build flag effects on our host (aarch64 vs x86): needs source rebuild; unverified.
- web: developer.deepx.ai/tech-docs and /document-download pages (fetched 2026-11-05) list only DX-RT User Manual 3.5.0 (Nov 4, 2026) and an overview; the downloadable manual was not read. This doc relies on the repo's `docs/source` copy, assumed equivalent.
