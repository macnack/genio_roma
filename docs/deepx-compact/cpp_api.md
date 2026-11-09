# DX-RT C++ API

> Compact of docs/deepx/cpp_api.md. Full text and extended citations are in the source file.

Source: `dx_rt@f997363c97 v3.5.0` (prefix `RT`).

## Officially documented facts

### Headers
- Recommended: `<dxrt/dxrt_cxx_api.h>` (self-contained C++14, wraps C ABI `dxrt_c_api.h`). Do not include `dxrt_api.h` and `dxrt_cxx_api.h` in one TU (ODR). [RT: docs/source/docs/06_Inference_API.md#L3-L6] [RT: lib/include/dxrt/dxrt_cxx_api.h#L1-L19]
- `dxrt_api.h` umbrella: `inference_engine.h`, `tensor.h`, `profiler.h`, `configuration.h`, `runtime_event_dispatcher.h`, etc. [RT: lib/include/dxrt/dxrt_api.h#L15-L27]
- Link: `find_library(... NAMES dxrt_${CMAKE_SYSTEM_PROCESSOR} ...)` + `protobuf`; C++14. [RT: docs/source/docs/04_Model_Inference.md#L651-L668]

### InferenceOption (`inference_option.h`)
```cpp
enum BOUND_OPTION { NPU_ALL = 0, NPU_0, NPU_1, NPU_2, NPU_01, NPU_12, NPU_02 };
std::vector<int> devices = {};
uint32_t    boundOption = BOUND_OPTION::NPU_ALL;
bool useORT = ORT_OPTION_DEFAULT;
int bufferCount{DXRT_TASK_MAX_LOAD_VALUE};
bool showModelInfo = true;
```
[RT: lib/include/dxrt/inference_option.h#L30-L66] `ORT_OPTION_DEFAULT` true only when built with `USE_ORT`. [RT: lib/include/dxrt/inference_option.h#L15-L19] Global `DefaultInferenceOption`. [RT: lib/include/dxrt/inference_option.h#L75]
- `dxrt_cxx_api.h` variant: same fields, `bufferCount = 0` ("0 = library default"). [RT: lib/include/dxrt/dxrt_cxx_api.h#L376-L400]

### InferenceEngine (`inference_engine.h`)
```cpp
explicit InferenceEngine(const std::string &modelPath, InferenceOption &option = DefaultInferenceOption);
explicit InferenceEngine(const uint8_t* modelBuffer, size_t modelSize, InferenceOption &option = DefaultInferenceOption);
TensorPtrs Run(void *inputPtr, void *userArg = nullptr, void *outputPtr = nullptr);
std::vector<TensorPtrs> Run(const std::vector<void*>& inputBuffers, const std::vector<void*>& outputBuffers, const std::vector<void*>& userArgs = {});
int RunAsync(void *inputPtr, void *userArg=nullptr, void *outputPtr = nullptr);
int RunAsync(const std::vector<void*>& inputPtrs, void *userArg=nullptr, void *outputPtr = nullptr);
int RunAsyncMultiInput(const std::map<std::string, void*>& inputTensors, void *userArg=nullptr, void *outputPtr = nullptr);
int RunAsyncMultiInput(const std::vector<void*>& inputPtrs, void *userArg=nullptr, void *outputPtr = nullptr);
TensorPtrs RunMultiInput(const std::map<std::string, void*>& inputTensors, void *userArg=nullptr, void *outputPtr=nullptr);
TensorPtrs RunMultiInput(const std::vector<void*>& inputPtrs, void *userArg=nullptr, void *outputPtr=nullptr);
float RunBenchmark(int num, void* inputPtr = nullptr);
TensorPtrs ValidateDevice(void *inputPtr, int deviceId = 0);
void RegisterCallback(std::function<int(TensorPtrs& outputs, void* userArg)> callbackFunc);
TensorPtrs Wait(int jobId) const;
void Dispose();
```
Citations: ctors [RT: lib/include/dxrt/inference_engine.h#L96] [RT: lib/include/dxrt/inference_engine.h#L115]; Run [#L131] [#L140-L144]; RunAsync [#L160] [#L168]; RunAsyncMultiInput [#L176] [#L184]; RunMultiInput [#L687] [#L695]; RunBenchmark [#L201]; ValidateDevice [#L213]; RegisterCallback [#L256]; Wait [#L271]; Dispose [#L673] (all `RT: lib/include/dxrt/inference_engine.h`).
- Getters: `GetInputSize()` [#L336], `GetOutputSize()` [#L369], `GetInputTensorSizes()`, `GetOutputTensorSizes()`, `GetInputs(ptr, phyAddr)` [#L289], `GetOutputs(...)` [#L322], `GetModelName()`, `GetTaskOrder()` [#L397], `GetLatency()` [#L411], `GetCoreLatency()`, `GetE2EResponseTime()`, `GetNpuInferenceTime()` [#L436] and `*Vector/Mean/StdDev/Cnt` variants, `GetAllTaskOutputs()`, `GetNumTailTasks()` [#L590], `GetCompileType()` [#L604], `GetModelVersion()`, `IsPPU()` [#L624], `HasDynamicOutput()`, `IsOrtConfigured()`, `IsMultiInputModel()` [#L642], `GetInputTensorCount()`, `GetInputTensorNames()` [#L654], `GetOutputTensorNames()`, `GetInputTensorToTaskMapping()`. [RT: lib/include/dxrt/inference_engine.h#L330-L670]
- `GetLatency()` = E2E response time; `GetCoreLatency()` excludes host buffer-pool wait and queue wait. [RT: lib/include/dxrt/inference_engine.h#L406-L419]
- Legacy names (`RunBenchMark`, `RegisterCallBack`, `inputs()`, `input_size()`, `latency()`, ...) are `[[deprecated]]`. [RT: lib/include/dxrt/inference_engine.h#L193-L194] [RT: lib/include/dxrt/inference_engine.h#L250-L251]
- `dxrt_cxx_api.h`: `Run` L500, `RunAsync` L522, `Wait(int)` L530, extra `Wait(int, void* output)` L557, `RegisterCallback(std::function<int(TensorPtrs&, void*)>)` L581 (zero-copy: TensorPtrs valid only during callback), batch `Run` L596. [RT: lib/include/dxrt/dxrt_cxx_api.h#L500-L596]

### Semantics
- Batch: input size N => batch; `outputBuffers` size must equal inputs, else `InvalidArgumentException`; flat N*M layout is Python-only. [RT: docs/source/docs/06_Inference_API.md#L55-L82]
- `RunAsyncMultiInput` on single-input model throws; `RunAsync(vector)` with wrong count uses only first element. [RT: docs/source/docs/06_Inference_API.md#L153] [RT: docs/source/docs/06_Inference_API.md#L171]
- Output ownership: auto-allocated per call; user buffers (>= `GetOutputSize()`) are the perf option. [RT: docs/source/docs/06_Inference_API.md#L502-L507]

### Tensor (`tensor.h`)
- `Tensor(std::string name_, std::vector<int64_t> shape_, DataType type_, void *data_=nullptr, int memory_type_=1)`; `name()`, `shape()`, `type()`, `data()`, `phy_addr()`, `elem_size()`, `memory_type()`, `size_in_bytes()`, `void* data(int height, int width, int channel)` (NHWC, N=1); aliases `Tensors`, `TensorPtr = shared_ptr<Tensor>`, `TensorPtrs`. [RT: lib/include/dxrt/tensor.h#L31] [RT: lib/include/dxrt/tensor.h#L42-L50] [RT: lib/include/dxrt/tensor.h#L71-L89] [RT: lib/include/dxrt/tensor.h#L115-L117]
- `dxrt::Profiler::GetInstance()`, `GetJobMetrics(jobId)`, `Start(name)`, `End(name)`; `Configuration::GetInstance().SetEnable/SetAttribute`. [RT: docs/source/docs/04_Model_Inference.md#L283-L376]
- `dxrt::Exception` (`e.code()`); `DeviceRemovedException` (v3.5.0). [RT: docs/source/docs/09_01_C++_Tutorials.md#L55-L58] [RT: RELEASE_NOTES.md#L45]

### Minimal examples (copied)
Sync. [RT: docs/source/docs/09_01_C++_Tutorials.md#L35-L53]
```cpp
dxrt::InferenceEngine ie(modelPath);
std::vector<uint8_t> inputPtr(ie.GetInputSize(), 0);
for(int i = 0; i < 100; ++i)
{
    auto outputs = ie.Run(inputPtr.data());
    postProcessing(outputs);
}
```
Async + Wait. [RT: docs/source/docs/04_Model_Inference.md#L169-L172]
```cpp
auto jobId = ie.RunAsync(inputBuf.data());
auto outputs = ie.Wait(jobId);
```
Async + callback. [RT: examples/cpp/run_async_model.cpp#L66-L94]
```cpp
dxrt::InferenceEngine ie(model_path);
ie.RegisterCallback([&callback_count, &loop_count, &cv_mutex, &cv]
    (const dxrt::TensorPtrs &outputs, const void *userArg) {
    std::ignore = outputs;
    std::ignore = userArg;
    std::unique_lock<std::mutex> lock(cv_mutex);
    callback_count++;
    if ( callback_count == loop_count ) cv.notify_one();
    return 0;
});
std::vector<uint8_t> inputPtr(ie.GetInputSize(), 0);
for (int i = 0; i < loop_count; ++i)
{
    auto* userData = new std::pair<int, int>(i, loop_count);
    ie.RunAsync(inputPtr.data(), userData);
}
```
Device/core binding. [RT: docs/source/docs/09_01_C++_Tutorials.md#L584-L597]
```cpp
dxrt::InferenceOption op;
op.devices.push_back(0);
op.boundOption = dxrt::InferenceOption::BOUND_OPTION::NPU_0;
op.useORT = false;
dxrt::InferenceEngine ie(modelPath, op);
```
Batch. [RT: docs/source/docs/09_01_C++_Tutorials.md#L461-L487]
```cpp
dxrt::InferenceEngine ie(modelPath);
std::vector<uint8_t> inputBuffer(ie.GetInputSize(), 0);
std::vector<void*> inputBuffers;
for(int i = 0; i < batch_count; ++i) inputBuffers.emplace_back(inputBuffer.data());
std::vector<void*> output_buffers(batch_count, 0);
for(auto& ptr : output_buffers) ptr = new uint8_t[ie.GetOutputSize()];
auto outputPtrs = ie.Run(inputBuffers, output_buffers);
```

## Experimentally verified facts

None yet (no DX-M1 available on host as of 2026-11-05).

## Hypotheses needing validation

- Two header flavours (`inference_engine.h` vs `dxrt_cxx_api.h`) differ (`bufferCount` default, extra `Wait(int, void*)`). Which one the installed package exposes as `<dxrt/dxrt_api.h>` vs `<dxrt/dxrt_cxx_api.h>` needs a compile test against installed DX-RT.
- `examples/cpp/run_async_model.cpp` callback uses `(const TensorPtrs&, const void*)` while the header takes `(TensorPtrs&, void*)`; tutorial text uses the non-const form. Settle by compiling both.
- Example batch code passes `output_buffers` initialised to `0`; `06_Inference_API.md#L81` requires equal sizes and nullptr for engine-managed output. Confirm nullptr entries work.
- Whether `Wait()` output of `dxrt_cxx_api.h` copies data (zero-copy comment applies to callbacks). Measure copy cost with a large-output model.
