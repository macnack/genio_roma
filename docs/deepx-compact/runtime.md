# DX-RT runtime: architecture, CLI, tensors, scheduling (compact)

> Compact of docs/deepx/runtime.md. Full text and extended citations are in the source file.

Scope: DX-RT v3.5.0 (`dx_rt@f997363c97`). Citation prefix `RT` means `dx_rt@f997363c97 v3.5.0`. Companion docs: `python_api.md`, `cpp_api.md`, `performance_optimization.md`.

## Officially documented facts

### Architecture
- DX-RT executes `.dxnn` on the DEEPX NPU via firmware and device drivers over PCIe; C/C++ and Python APIs; covers model loading, I/O buffers, inference, hardware monitoring. [RT: docs/source/docs/01_DXNN_Runtime_Overview.md#L19]
- Flow: app capture (OpenCV) -> app pre-processing -> input tensors into `InferenceEngine` (+ optional `InferenceOption`) -> NPU/CPU execution -> app post-processing. [RT: docs/source/docs/01_DXNN_Runtime_Overview.md#L29-L58]
- `InferenceEngine` initializes/controls the NPU, manages tensor memory, "schedules inference tasks across NPU and CPU". [RT: docs/source/docs/01_DXNN_Runtime_Overview.md#L47-L52]
- Model artifact: single `graph.dxnn` (NPU command data, metadata, parameters). [RT: docs/source/docs/04_Model_Inference.md#L5-L17]
- NPU/CPU partition: with ONNX Runtime enabled (`useORT`), unsupported ops run on CPU via ORT; otherwise only NPU tasks run. Partition exposed as `GetTaskOrder()` / `get_task_order()`; profiler task names `npu_0`, `cpu_0`. [RT: docs/source/docs/04_Model_Inference.md#L71-L77] [RT: lib/include/dxrt/inference_engine.h#L394-L397] [RT: docs/source/docs/04_Model_Inference.md#L305-L329]
- `dxrt.service` (systemd) is referenced in firmware-update workaround; `dxtop` works without it ("No Service Mode", reads shared memory). [RT: docs/source/docs/05_Command_Line_Interface.md#L319-L332] [RT: docs/source/docs/05_Command_Line_Interface.md#L340]
- `import dx_engine` raises `RuntimeError` if libdxrt.so major.minor differs; bypass `DX_ENGINE_SKIP_VERSION_CHECK=1`. [RT: RELEASE_NOTES.md#L34] [RT: python_package/src/dx_engine/__init__.py#L24-L52]
- Minimums in v3.5.0: Linux driver 2.7.0, Linux PCIe driver 2.7.0, firmware 2.7.6. [RT: RELEASE_NOTES.md#L11-L15]

### CLI tools (v3.5.0 names; legacy aliases kept)
- Aliases: `dxparse`=`parse_model`, `dxrun`=`run_model`, `dxcli`=`dxrt-cli`. [RT: docs/source/docs/05_Command_Line_Interface.md#L7-L15]
- `dxparse -m <model.dxnn>`; options `-m/--model`, `-v/--verbose`, `-o/--output FILE`, `-j/--json`, `-h/--help`. Shows structure, I/O tensors, metadata. [RT: docs/source/docs/05_Command_Line_Interface.md#L19-L40]
- `dxrun` options (exact): `-m/--model`, `-b/--benchmark`, `-s/--single`, `-v/--verbose`, `-n/--npu` (0 NPU_ALL,1 NPU_0,2 NPU_1,3 NPU_2,4 NPU_0/1,5 NPU_1/2,6 NPU_0/2), `-l/--loops` (default 30), `-t/--time`, `-w/--warmup-runs` (default 0), `-d/--devices` (`all`, `0`, `0,1,2`, `count:N`), `-f/--fps`, `--use-ort`, `--profiler`, `--accel-nfh`, `--accel-cpu`, `--buffer-count`, `--max-throughput`, `--probe-time` (2.0), `--sweep-tolerance` (1.0), `--cool-down-temp` (45), `-h`. [RT: docs/source/docs/05_Command_Line_Interface.md#L62-L131]
- `dxrun` default benchmark holds buffer count fixed (default 6); `--max-throughput` sweeps buffer counts (default 3-100), 3 measurements per count with dedicated engine, recommends smallest count within tolerance of peak. Exit codes: 0 ok, 1 bad args, -1/255 failure. [RT: docs/source/docs/05_Command_Line_Interface.md#L53-L55] [RT: docs/source/docs/05_Command_Line_Interface.md#L163-L167] [RT: docs/source/docs/05_Command_Line_Interface.md#L243-L252]
- `dxrun -v` metrics: NPU Processing Time, Queue Wait Time, E2E Response Time, Latency (= core latency), FPS. [RT: docs/source/docs/05_Command_Line_Interface.md#L199-L223]
- `dxcli` options: `-s/--status`, `-i/--info`, `-m/--monitor N`, `-r/--reset[=0]`, `-d/--device`, `-u/--fwupdate`, `-g/--fwversion`, `-C/--fwconfig_json`, `-v/--version`, `-h`. Accelerator devices only. [RT: docs/source/docs/05_Command_Line_Interface.md#L257-L285]
- `dxtop`: real-time NPU monitor; per device: ID, variant (M1, M1M; trailing M = LPDDR4), PCIe bus, firmware, NPU memory; per core: Util %, Temp, Voltage (mV), Clock (MHz). Keys q/n/p/h. Only `--help` option in source. [RT: docs/source/docs/05_Command_Line_Interface.md#L336-L402] [RT: cli/dxtop/dxtop.cpp#L29-L31]
- `dxbenchmark`: `--dir`, `--result-path`, `--sort`, `--order`, `-l`, `-t`, `--warmup` (10), `-n`, `-d`, `--only-data`, `--recursive`, `--use-ort`, `-v`, `-h`. Writes `DXBENCHMARK_{YYYY_MM_DD_HHMMSS}.html` and `rt_<ver>_dd_<ver>_pd_<ver>.json/csv`; `-t` takes priority over `-l`. [RT: docs/source/docs/05_Command_Line_Interface.md#L419-L520]

### Tensor layouts, dtypes, preprocessing
- Compiled models use NHWC by default. Device-side input: `Formatter` `[N,H,W,C]` 8-bit; `IM2COL` `[N,H,align64(W*C)]` 8-bit. Output `[N,H,W,align64(C)]`. [RT: docs/source/docs/04_Model_Inference.md#L214-L240]
- ORT off (v3.0.0+): runtime auto-pads inputs to NPU-aligned format and slices output padding; user output buffers must be >= `GetOutputSize()`. [RT: docs/source/docs/04_Model_Inference.md#L247-L258]
- "NPU Format Handler (NFH)" = input/output conversion stage; profiler lists Input Format Handler (padding + NHWC conversion) and Output Format Handler (padding removal, NHWC->NCHW). [RT: docs/source/docs/04_Model_Inference.md#L453-L457] [RT: docs/source/docs/04_Model_Inference.md#L705]
- Host does capture, pre-processing (resize/normalization) and post-processing; DX-APP pipelines time read/pre/NPU/post/display as separate stages. [RT: docs/source/docs/01_DXNN_Runtime_Overview.md#L31-L58] [dx_app@375de0344f v3.3.0: docs/source/docs/01_DXNN_Application_Overview.md#L121-L129]
- `DataType` enum: NONE_TYPE, FLOAT, UINT8, INT8, UINT16, INT16, INT32, INT64, UINT32, UINT64, BBOX, FACE, POSE; PPU structs `DeviceBoundingBox_t`, `DeviceFace_t`, `DevicePose_t`. [RT: lib/include/dxrt/datatype.h#L19-L35] [RT: lib/include/dxrt/datatype.h#L39-L89]
- Python maps to numpy (`FLOAT`->float32, ints to same-width numpy; BBOX/FACE/POSE stay strings). [RT: python_package/src/dx_engine/dtype.py#L12-L36]
- v3.5.0 added float32->int8 input quantization with NEON/SSE4.1 kernels "reducing DMA write time". [RT: RELEASE_NOTES.md#L37]
- Dynamic-shape outputs: `GetOutputSize()` returns 0; `HasDynamicOutput()`. [RT: lib/include/dxrt/inference_engine.h#L360-L369]
- DX-APP reads input shape as `shape = get_input_tensors_info()[0]["shape"]`, guessing NCHW vs NHWC from shape. [dx_app@375de0344f v3.3.0: src/python_example/common/runner/async_runner.py#L326-L338]

### Sync vs async, threads, devices, batching
- `Run()` blocks, uses one NPU core; `RunAsync()` uses all cores, blocks if device load >= max-load value; callback runs on background thread, outputs valid only inside it. [RT: docs/source/docs/09_01_C++_Tutorials.md#L18-L23] [RT: docs/source/docs/09_01_C++_Tutorials.md#L85-L90] [RT: docs/source/docs/04_Model_Inference.md#L192-L196]
- Multiple user threads can submit to one engine (callback + user_arg routes results). [RT: docs/source/docs/09_01_C++_Tutorials.md#L175-L184]; sync->async via multiple I/O buffers and thread-safe queues. [RT: docs/source/docs/09_01_C++_Tutorials.md#L524-L537]
- Device selection: `InferenceOption.devices` (empty = all); core binding via `boundOption` (`NPU_ALL`, `NPU_0..2`, `NPU_01/12/02`); `dxrun -d`/`-n`. Multi-device scheduling automatic, N/A for single-NPU hosts. [RT: docs/source/docs/04_Model_Inference.md#L56-L66] [RT: docs/source/docs/04_Model_Inference.md#L207-L210]
- A new `NPU_ALL` engine blocks while other engines hold NPUs 0,1,2 via specific bindings (threads and processes). [RT: docs/source/docs/09_01_C++_Tutorials.md#L630-L632]
- Batch: `Run(vector<void*> in, vector<void*> out, userArgs)` (sync; `outputBuffers` size must equal input size); Python `run()` batch needs `output_buffers`; async is single-sample only in Python. [RT: docs/source/docs/06_Inference_API.md#L45-L82] [RT: docs/source/docs/06_Inference_API.md#L266-L267] [RT: docs/source/docs/06_Inference_API.md#L482]
- Max in-flight jobs `INFERENCE_JOB_MAX_COUNT = 1024`. [RT: lib/include/dxrt/inference_engine.h#L75]

### Monitoring and events
- `RuntimeEventDispatcher`: levels INFO/WARNING/ERROR/CRITICAL; types DEVICE_CORE/STATUS/IO/MEMORY/UNKNOWN; codes incl. MEMORY_OVERFLOW, RECOVERY_OCCURRED, TIMEOUT_OCCURRED, THROTTLING_NOTICE, THROTTLING_EMERGENCY; one handler at a time. [RT: docs/source/docs/04_Model_Inference.md#L474-L510] [RT: docs/source/docs/04_Model_Inference.md#L605-L610]
- Python `DeviceStatus`: `get_device_count()`, `get_current_status(id)`, `get_temperature(ch)`, `get_npu_voltage(ch)`, `get_npu_clock(ch)`, `get_core_utilization(core)`, `get_memory_used/free()`, `is_valid()`, `get_driver_version()`. [RT: python_package/src/dx_engine/device_status.py#L14-L75]
- `Configuration` singleton ITEMs: DEBUG, PROFILER, SERVICE, DYNAMIC_CPU_THREAD, TASK_FLOW, SHOW_THROTTLING, SHOW_PROFILE, SHOW_MODEL_INFO, CUSTOM_INTRA/INTER_OP_THREADS, NFH_ASYNC (default on), NFH_ACCELERATION, CPU_OP_ACCELERATION (last two build-dependent). [RT: docs/source/docs/08_Global_Instance.md#L54-L79]

## Experimentally verified facts

None yet (no DX-M1 available on host as of 2026-11-05).

## Hypotheses needing validation

- Whether mean/std normalization and color order are baked into the `.dxnn` (compiler JSON "pre/post-processing settings" mentioned at `01_DXNN_Runtime_Overview.md#L18`) or must be done by the host. Settle: `dxparse -v` on a real model; compare outputs for raw uint8 vs normalized input.
- Actual input dtype/layout the host must pass to `Run()` (uint8 NHWC vs float32). Docs say only buffer size is `GetInputSize()` bytes; Python validates dtype against the model's. Settle: `get_input_tensors_info()` on a real model.
- Source tension: `04_Model_Inference.md#L243` says a device->NCHW/NHWC conversion API is "next release", while the profiler table (`#L457`) and v3.0 auto-slicing (`#L247-L254`) imply runtime does padding removal/NHWC->NCHW. Settle: inspect output tensor shapes with ORT on/off.
- `bufferCount` default: docs say 6 (`04#L79`, Python const `DXRT_TASK_MAX_LOAD_DEFAULT = 6`); header says `DXRT_TASK_MAX_LOAD_VALUE` = `dxrt::GetTaskMaxLoad()` (`lib/include/dxrt/common.h#L83`); `dxrt_cxx_api.h` says 0 = library default. Settle: print effective `option.bufferCount` or `dxrun` banner on hardware.
- Whether `Run()` truly uses only one core across all model types (tutorial text) vs scheduler spreading. Settle: `dxtop` core utilization during sync loop.
