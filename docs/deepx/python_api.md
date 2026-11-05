# DX-RT Python API (`dx_engine`)

Source: `dx_rt@f997363c97 v3.5.0`, package `python_package/src/dx_engine/` (prefix `PY` = `dx_rt@f997363c97 v3.5.0: python_package/src/dx_engine`). Signatures below are copied from the `.py` wrappers (not memory).

## Officially documented facts

### Package exports
- `from dx_engine import InferenceEngine, InferenceOption, Configuration, DeviceStatus, RuntimeEventDispatcher, Profiler, JobMetrics, TaskMetrics, NpuDeviceMetrics`, plus `DeviceRemovedError`. [PY: __init__.py#L11-L18]

### InferenceOption
- Properties (and matching `set_*/get_*` methods): `use_ort: bool`, `bound_option: InferenceOption.BOUND_OPTION`, `devices: List[int]`, `buffer_count: int`, `show_model_info: bool`. Type-checked (TypeError on wrong type). [PY: inference_option.py#L1-L157]
- `BOUND_OPTION` enum: NPU_ALL=0, NPU_0=1, NPU_1=2, NPU_2=3, NPU_01=4, NPU_12=5, NPU_02=6; constants `DXRT_TASK_MAX_LOAD_DEFAULT = 6`, `DXRT_TASK_MAX_LOAD_LIMIT = 100`. [PY: inference_option.py#L21-L38]

### InferenceEngine (constructor and loading)
```python
def __init__(self, model_path: str, inference_option: Optional[InferenceOption] = None) -> None
@classmethod
def from_buffer(cls, memory_buffer: np.ndarray, inference_option: Optional[InferenceOption] = None) -> 'InferenceEngine'
```
[PY: inference_engine.py#L42-L47] [PY: inference_engine.py#L96-L101]
- If the build lacks ORT, `use_ort` is forced False with a RuntimeWarning. Context manager supported (`__enter__/__exit__` call `dispose()`). [PY: inference_engine.py#L58-L70] [PY: inference_engine.py#L1201-L1214]

### Inference methods (exact signatures)
```python
def run(self,
        input_data: Union[np.ndarray, List[np.ndarray], List[List[np.ndarray]]],
        output_buffers: Optional[Union[List[np.ndarray], List[List[np.ndarray]]]] = None,
        user_args: Optional[Union[Any, List[Any]]] = None
) -> Union[List[np.ndarray], List[List[np.ndarray]]]

def run_multi_input(self, input_tensors: Dict[str, np.ndarray],
        output_buffers: Optional[List[np.ndarray]] = None, user_arg: Any = None) -> List[np.ndarray]

def run_async(self, input_data: Union[np.ndarray, List[np.ndarray]],
        user_arg: Any = None,
        output_buffer: Optional[Union[np.ndarray, List[np.ndarray]]] = None) -> int

def run_async_multi_input(self, input_tensors: Dict[str, np.ndarray],
        user_arg: Any = None, output_buffer: Optional[List[np.ndarray]] = None) -> int

def register_callback(self, callback: Optional[Callable[[List[np.ndarray], Any], int]]) -> None
def wait(self, job_id: int) -> List[np.ndarray]
def run_benchmark(self, num_loops: int, input_data: Optional[List[np.ndarray]] = None) -> float
def validate_device(self, input_data: Union[np.ndarray, List[np.ndarray]], device_id: int = 0) -> List[np.ndarray]
def validate_device_multi_input(...)   # see inference_engine.py#L807
def dispose(self) -> None
```
[PY: inference_engine.py#L509-L513] [PY: inference_engine.py#L567-L571] [PY: inference_engine.py#L609-L613] [PY: inference_engine.py#L685-L689] [PY: inference_engine.py#L728-L742] [PY: inference_engine.py#L766-L770] [PY: inference_engine.py#L1201]
- `run_async` raises `ValueError` for batch input; "Async inference only supports single inference". `run_benchmark` without input fills a zero uint8 buffer of `get_input_size()`. [PY: inference_engine.py#L609-L632] [PY: inference_engine.py#L740-L755]
- Batch via `run()` requires `output_buffers`; input parsing rules (ndarray / list / list-of-lists, auto-split of concatenated multi-input buffer) in `06_Inference_API.md#L211-L293` and `#L361-L413`. [RT: docs/source/docs/06_Inference_API.md#L211-L293]
- Input dtype validated against the model's: `ValueError("Input dtype mismatch for '<name>': expected X, got Y")`; skipped if model reports unknown dtype. [PY: inference_engine.py#L1341-L1376]
- Callback outputs are valid only inside the callback; callback must return int. [RT: docs/source/docs/09_02_Python_Tutorials.md#L48-L51]

### Introspection and timing getters (names from source)
`get_input_size() -> int`, `get_input_tensor_sizes()`, `get_output_size()`, `get_output_tensor_sizes()`, `has_dynamic_output()`, `get_all_task_outputs()`, `get_input_tensors_info()`, `get_output_tensors_info()` (list of dicts with keys name, shape, dtype, elem_size), `get_input_tensor_count()`, `get_output_tensor_count()`, `get_input_data_type()`, `get_output_data_type()`, `get_task_order()`, `get_num_tail_tasks()`, `get_compile_type()`, `get_model_version()`, `is_ppu()`, `is_multi_input_model()`, `get_input_tensor_names()`, `get_output_tensor_names()`, `get_input_tensor_to_task_mapping()`, `get_bitmatch_mask(index=0)`.
Timing (all microseconds ints/floats): `get_latency()`, `get_core_latency()`, `get_e2e_response_time()`, `get_npu_inference_time()` and `*_list()`, `*_mean()`, `*_std()`, `*_count()` variants (latency, core_latency, npu_inference_time; e2e has `_list/_mean/_std/_count`). [PY: inference_engine.py#L850-L895] [PY: inference_engine.py#L1022-L1200]
- Module function `parse_model(model_path: str) -> str`. [PY: inference_engine.py#L1474-L1480]
- Deprecated aliases (emit DeprecationWarning): `Run, run_batch, RunBatch, RunAsync, RunBenchMark, ValidateDevice, RegisterCallBack, Wait, input_size, output_size, ...`. [PY: inference_engine.py#L1217-L1339]

### Configuration / Profiler / DeviceStatus
- `Configuration()` wraps C++ singleton: `load_config_file(file_name)`, `set_enable(item, enabled)`, `set_attribute(item, attrib, value:str)`, `get_enable`, `get_attribute`, `get_version()`, `get_driver_version()`, `get_pcie_driver_version()`, `set_fw_config_with_json(json_file)`. `ITEM` and `ATTRIBUTE` (PROFILER_SHOW_DATA=1001, PROFILER_SAVE_DATA=1002, CUSTOM_INTRA_OP_THREADS_NUM=1003, CUSTOM_INTER_OP_THREADS_NUM=1004). `NFH_ACCELERATION`/`CPU_OP_ACCELERATION` exist only if compiled in. [PY: configuration.py#L1-L84]
- `Profiler.get_instance()`; methods `show()`, `save(filename)`, `clear()`, `get_job_metrics(job_id) -> JobMetrics`, `start(name)`, `end(name)`, `user_clear()`. `JobMetrics.tasks/valid/get_task(name)`; `TaskMetrics.task_name/devices/cpu_task_us/valid`; `NpuDeviceMetrics.input_format_us/h2d_us/inference_core_all_us/inference_core_0_us.._2_us/d2h_us/output_format_us/total_us/valid`. [PY: profiler.py#L1-L173]
- `DeviceStatus` methods: see `runtime.md`. [PY: device_status.py#L1-L75]

### Minimal examples (copied from sources)
Sync loop. [RT: docs/source/docs/09_02_Python_Tutorials.md#L22-L37]
```python
ie = InferenceEngine(modelPath)
input = [np.zeros(ie.get_input_size(), dtype=np.uint8)]
for i in range(loop_count):
    outputs = ie.run(input)
    postProcessing(outputs)
```
Async + wait thread (note the buffer comment). [RT: examples/python/run_async_model_wait.py#L75-L99]
```python
with InferenceEngine(args.model) as ie:
    t1 = threading.Thread(target=inference_thread_func, args=(ie, args.loops))
    t1.start()
    # NOTE: np.zeros() uses COW zero pages — all virtual pages share one
    # physical page. PCIe DMA driver's get_user_pages() then sees duplicate
    # physical pages in the SG list and fails with EFAULT.
    # np.empty() + explicit fill forces unique physical page allocation.
    _buf = np.empty(ie.get_input_size(), dtype=np.uint8)
    _buf.fill(0)
    input = [_buf]
    for i in range(args.loops):
        jobId = ie.run_async(input, user_arg=0)
        q.put(jobId)
    t1.join()
```
Profiler per job. [PY: profiler.py#L110-L124]
```python
profiler = Profiler.get_instance()
job_id = ie.run_async([input])
outputs = ie.wait(job_id)
jm = profiler.get_job_metrics(job_id)
if jm.valid:
    npu = jm.get_task("npu_0")
    print(npu.devices[0].h2d_us)
```
Enable acceleration (only if built in). [RT: docs/source/docs/04_Model_Inference.md#L801-L806]
```python
from dx_engine import Configuration
config = Configuration()
config.set_enable(Configuration.ITEM.NFH_ACCELERATION, True)
config.set_enable(Configuration.ITEM.CPU_OP_ACCELERATION, True)
```

### DX-ModelZoo wrapper (separate package `dx_modelzoo`)
- `DxRuntimeSession(path, runtime_config=None)` with `run`, `run_async`, `wait`; uses `dx_engine`; device via `DxnnRuntimeConfig(device=0|[0,1])` or env `DXNN_DEVICES`; fixed `batch_size=1`. [dx-modelzoo@ab3e3a4234 v1.0.0: docs/source/04_03_Session_API.md#L84-L136]

## Experimentally verified facts

None yet (no DX-M1 available on host as of 2026-11-05).

## Hypotheses needing validation

- Docstring of `get_input_tensors_info` says dtype is `str`, but `_fetch_input_tensors_info` replaces it with numpy type/"BBOX" string via `NumpyDataTypeMapper` (`inference_engine.py#L886-L895` vs `#L1022-L1027`). Settle: print on a real model.
- The tutorial sync example uses `np.zeros`, while the shipped async example warns that `np.zeros` can fail DMA with EFAULT (`09_02_Python_Tutorials.md#L25` vs `run_async_model_wait.py#L84-L86`). Treat `np.empty`+fill as the safe path; confirm on hardware whether sync `run()` with `np.zeros` fails.
- Thread-safety of one `InferenceEngine` shared across threads in Python (examples do it, no formal guarantee read). Settle: stress test with N threads calling `run_async`.
- `dx_engine` wheel/Python version compatibility on this host (Debian package bundles wheels for Python 3.8-3.14 per `RELEASE_NOTES.md#L88`); confirm by install.
