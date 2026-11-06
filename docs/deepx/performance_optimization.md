# DX-RT performance, profiling and benchmarking

Sources: `dx_rt@f997363c97 v3.5.0` (prefix `RT`), `dx-all-suite@51d81fe2ef v2.5.0` (`dx-benchmark`, prefix `BM`), `dx_stream@c575ed2896 v3.2.0`, `dx_app@375de0344f v3.3.0`.

## Officially documented facts

### Measurement methodology and metrics
- `dxrun` metrics: NPU Processing Time (core compute per request), Queue Wait Time, E2E Response Time (request start to completion incl. waits/transfer), Latency = core latency (E2E minus buffer-pool wait and queue wait), FPS = completed inputs per wall-clock second. In benchmark mode queue wait and E2E grow with `--buffer-count`. [RT: docs/source/docs/05_Command_Line_Interface.md#L199-L223]
- Per-job APIs: `GetLatency()` = E2E (v3.5.0 change), `GetCoreLatency()`, `GetNpuInferenceTime()`, plus mean/std/count/vector variants. [RT: RELEASE_NOTES.md#L9] [RT: lib/include/dxrt/inference_engine.h#L406-L419]
- Single-run vs benchmark modes in `dxrun`: `-s/--single` (sequential single-input, single core) vs `-b/--benchmark` (fixed buffer count; default), `-f` target-FPS mode, `-w` warmup, `-t` overrides `-l`. [RT: docs/source/docs/05_Command_Line_Interface.md#L70-L101]
- Latency+throughput protocol used by DX-Benchmark: latency = `dxrun -s` 300 loops, 1 warmup, measured cold; throughput = `dxrun -t 30` after `--max-throughput` sweep (10 s probe x 3 repeats, 1% tolerance), 3 runs each after cooldown and a 2 s throw-away run; ORT ON and OFF both measured; NPU temp cooldown target `min(idle+10C, 55C)`. [BM: dx-benchmark/README.md#L328-L347]
- E2E (pipeline) FPS: DX-Stream pipeline (decode, `dxpreprocess`, `dxinfer`, `dxpostprocess`), 1080p30 H.264; channel capacity = max concurrent streams all >=30 fps. [BM: dx-benchmark/docs/ANALYSIS_EN.md#L32-L38]
- DX-APP examples print a per-stage Performance Summary (read / pre / NPU / post / display) and overall FPS. [dx_app@375de0344f v3.3.0: docs/source/docs/01_DXNN_Application_Overview.md#L121-L139]
- DX-Stream: `dxinfer` reports moving-average inference time as its latency contribution; GstShark tracer `proctime` measures per-element time (`GST_TRACERS`, `GST_SHARK_LOCATION`). [dx_stream@c575ed2896 v3.2.0: docs/source/docs/Elements/03_02_DxInfer.md#L67-L69] [dx_stream@c575ed2896 v3.2.0: docs/source/docs/Appendix_Performance_Evaluation_with_GstShark.md#L27-L42]

### Profiler
- `dxrun -m model.dxnn --profiler` writes `profiler.json`. App-level: `Configuration::ITEM::PROFILER` + attributes `PROFILER_SHOW_DATA`/`PROFILER_SAVE_DATA` = `"ON"`. [RT: docs/source/docs/04_Model_Inference.md#L264-L295]
- Per-job breakdown via `Profiler::GetJobMetrics(jobId)` after `Wait()`: input_format_us, h2d_us, inference_core_{all,0,1,2}_us, d2h_us, output_format_us, total_us, cpu_task_us. Older `GetPerformanceData*` deprecated. [RT: docs/source/docs/04_Model_Inference.md#L299-L364]
- Custom events: `profiler.Start("name")` / `End("name")` (Python `start/end`). [RT: docs/source/docs/04_Model_Inference.md#L368-L377]
- Visualisation: `python3 tool/profiler/plot.py -i profiler.json` (options `-h -i -o -s -e -j -t -a`) and `tool/profiler/plot_html.py -i profiler.json [-o out.html]` (needs pandas, plotly). [RT: docs/source/docs/04_Model_Inference.md#L385-L442]
- Profiler event / remedy table: Buffer Wait -> `export DXRT_DYNAMIC_CPU_THREAD=ON`; NPU Input/Output Format Handler -> NFH acceleration; CPU Task Queue Wait and `cpu_N` -> CPU op acceleration; PCIe Write / NPU Core / PCIe Read have no remedy. [RT: docs/source/docs/04_Model_Inference.md#L450-L462]
- `dxtop` for live per-core utilization, temperature, voltage, clock (see `runtime.md`); `dxcli -m <sec>` monitors device status periodically. [RT: docs/source/docs/05_Command_Line_Interface.md#L273-L274] [RT: docs/source/docs/05_Command_Line_Interface.md#L371-L380]

### Tuning knobs (documented)
- Use async with multiple buffers/threads (`RunAsync`); sync `Run` is sequential and uses one core; batch increases memory. [RT: docs/source/docs/06_Inference_API.md#L509-L515] [RT: docs/source/docs/09_01_C++_Tutorials.md#L18-L23]
- Keep callbacks short ("processing this callback as quickly as possible is beneficial"). [RT: docs/source/docs/09_01_C++_Tutorials.md#L85-L90]
- `bufferCount`: more buffers can improve pipelined throughput (range 1-100 in `dxrun`); use `dxrun --max-throughput [--buffer-count 3-16]` to pick it; NPU memory overflow at large counts terminates `dxrun`. [RT: docs/source/docs/04_Model_Inference.md#L79-L83] [RT: docs/source/docs/05_Command_Line_Interface.md#L146-L150] [RT: docs/source/docs/05_Command_Line_Interface.md#L194-L197]
- User-provided output buffers avoid per-call allocation. [RT: docs/source/docs/06_Inference_API.md#L502-L507]
- `NPU_ALL` (default) recommended for max throughput; single-core binding useful to partition NPU between engines. [RT: docs/source/docs/04_Model_Inference.md#L62-L66]
- ORT on/off: ORT executes CPU-side subgraphs inside the call; off returns raw NPU tensors. DX-Benchmark: with ORT ON the host CPU limits light models (53-58% of NPU-only throughput on ARM hosts, 75-76% on x86 at size n); which mode gives better E2E FPS depends on host. [RT: docs/source/docs/04_Model_Inference.md#L695-L696] [BM: dx-benchmark/docs/ANALYSIS_EN.md#L135-L137] [BM: dx-benchmark/docs/ANALYSIS_EN.md#L559-L590]
- Hardware-accelerated NFH (Intel IPP / ARM NEON) and CPU-op acceleration (OpenVINO / XNNPACK EP): off by default; need CMake `USE_NPU_FORMAT_CONVERSION_ACCELERATION=ON` / `USE_CPU_OP_ACCELERATION=ON` + `./build.sh --clean` (internet needed), then runtime `Configuration::ITEM::NFH_ACCELERATION` / `CPU_OP_ACCELERATION` or `dxrun --accel-nfh --accel-cpu`. Reference FPS on Orange Pi 5 Plus, v3.3.0, YoloV8S 84 -> 131 (both). CPU-op gain only for compute-heavy CPU ops (Conv, MatMul). [RT: docs/source/docs/04_Model_Inference.md#L701-L822]
- Dynamic CPU threading: `export DXRT_DYNAMIC_CPU_THREAD=ON` (also config key `DXRT_DYNAMIC_CPU_THREAD=1`); runtime may print a hint recommending it. Custom ORT threads via `CUSTOM_INTRA_OP_THREADS(_NUM)` / `CUSTOM_INTER_OP_THREADS(_NUM)`. [RT: docs/source/docs/04_Model_Inference.md#L824-L850] [RT: docs/source/docs/08_Global_Instance.md#L64-L79]
- `NFH_ASYNC` enabled by default. [RT: docs/source/docs/08_Global_Instance.md#L66]
- Host-side factors measured by DEEPX (YOLO26, 6 hosts): hardware video decoder, cooling (throttling lowers NPU clock below nominal 1000 MHz, observed down to 300-800 MHz), host CPU, PCIe lane width (Gen3 x1 gave 39-47% lower NPU-only throughput on light 640x640 detection/segmentation at size n), host RAM (~32 MiB per channel median). [BM: dx-benchmark/docs/ANALYSIS_EN.md#L125-L143] [BM: dx-benchmark/docs/ANALYSIS_EN.md#L454-L485]
- Multi-model: separate engines per model; core binding can partition NPUs, but new `NPU_ALL` engine blocks until bound cores free. [RT: docs/source/docs/09_01_C++_Tutorials.md#L630-L632]
- DX-Stream: `dxinfer` `use-ort` (default true), `backend` auto/dxrt/dxvnpu; DxRate throttle QoS makes `dxinfer` drop frames in low-framerate pipelines. [dx_stream@c575ed2896 v3.2.0: docs/source/docs/Elements/03_02_DxInfer.md#L23-L31] [dx_stream@c575ed2896 v3.2.0: docs/source/docs/Elements/03_02_DxInfer.md#L73-L82]

## Experimentally verified facts

- ConvNeXt-Tiny / Small on DX-M1 (RT 3.4.2, batch 1): NPU time 35.3 / 60.7 ms, latency 40.1 / 65.3 ms (`dx_engine`, 4000 images). (`reports/accuracy.md`, `reports/acc/A13_ptq_ema100_board.json`, `reports/acc/AS13_ptq_board.json`)
- `dxrun -b` throughput: tiny 58.9 FPS on 3 cores, 28.3 on 1 core; small 34.4 / 16.5. `--buffer-count` saturates at 6 (tiny 24.4/39.8/53.4/58.9 FPS for 1/2/3/6 buffers). Single 10 s runs. (`reports/acc/sweep_dxrun.csv`, `scripts/sweep_dxrun.sh`)
- Genio CPU FP32 baseline (ORT 1.31.1): tiny 156.7 ms all 8 cores, 207.4 ms on 2xA78; small 312 / 383 ms. DX-M1 single request is about 3.9x (tiny) / 4.8x (small) faster; not iso-precision. (`reports/cross_device.md`, `reports/acc/cpu_bench_board.jsonl`)
- The board CPU is 6x Cortex-A55 (cores 0-5) + 2x Cortex-A78 (cores 6-7), not 4+4. (`lscpu`, recorded in `reports/cross_device.md`)

## Hypotheses needing validation

- FPS/latency numbers from DEEPX (M1 on Orange Pi/RPi5/etc., YOLO26/YoloV8) will not transfer to our host/model; need our own `dxrun -s -l 300` (latency) and `dxrun --max-throughput -t 30` (throughput) baselines.
- Whether our pipeline is host-bound (pre/post, decode) or NPU-bound: settle with `dxtop` core Util during run plus `Profiler` events (Buffer Wait, Format Handler, `cpu_N`).
- Best ORT mode and `bufferCount` for our model on our host (DX-Benchmark shows host-dependent sign); measure ON/OFF and sweep.
- Optimal number of Python submit threads / queue depth for `run_async` (docs give no number). Sweep 1..N threads with callback vs `wait`.
- Whether `dxtop` shown "Util" is meaningful for sub-second runs (DX-Benchmark notes its ~1 Hz sampler, `README.md#L359-L363`); use sustained runs.
- Acceleration build flags effect on our host (aarch64 vs x86): requires source rebuild; unverified.
- web: developer.deepx.ai/tech-docs and /document-download pages (fetched 2026-11-05) only list DX-RT User Manual 3.5.0 (Nov 4, 2026) for download and an overview page; no additional runtime detail was retrievable. The downloadable manual was not read; this doc relies on the repo's `docs/source` copy, assumed equivalent.
