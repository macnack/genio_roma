# Genio-700 APU (MediaTek MDLA 3.0): status for this project (2026-11-06)

## Experimentally verified facts
- 2026-11-06: installed `libneuropilot8` 8.2.16 + `python3-onnxruntime-neuron` 1.20.2 (via laptop-downloaded `.deb`, board has no network). The provider loads, but the first `/dev/apusys` ioctl returns `EFAULT` and compile aborts with `memAlloc ... fail(Bad address)` + segfault, for ConvNeXt and for a trivial CNN. No model ran on the APU. Details and logs: `reports/apu_neuron.md`.
- Board kernel exposes `apusys`/`apu_top` modules, `/dev/apusys*`, devfreq `mdla_devfreq`/`vpu_devfreq` (see plan notes). Before 2026-11-06 no NeuroPilot userspace was installed.

## Officially documented facts (web search, not yet read in full; fetched 2026-11-06)
- Genio 700 = MDLA 3.0 / NeuroPilot 6 [genio.mediatek.com/doc/iot-aihub/ai_hub/related_resource.html]. MediaTek's TFLite route: Neuron compiler `ncc-tflite` (TFLite -> DLA) or the Neuron Stable Delegate [mediatek.gitlab.io/aiot/doc/aiot-dev-guide/sw/yocto/ml-guide/ml-neuron-sdk.html].
- The ONNX Runtime NeuronExecutionProvider docs target Genio 720/520 on Yocto [genio.mediatek.com/doc/iot-aihub/ai_hub/supported_os/yocto/onnxruntime/accelerating_ort.html]; community post says enabling it on Genio 700/510 needs a MediaTek representative [genio-community.mediatek.com/t/accelerating-ai-on-genio-with-the-onnx-runtime-neuronexecutionprovider/1347].
- NP6 SDK bundles (with `ncc-tflite`) are NDA-gated.

## Hypotheses needing validation
- Settled negatively for the apt packages as installed (see verified facts). Remaining hypothesis: a matching kernel/userspace pair from MediaTek or Grinn would work; not tested.
- ConvNeXt ops (7x7 depthwise, LayerNorm, GELU) on MDLA 3.0: unknown; unsupported ops would fall back to CPU, so a run would need partition proof before claiming APU acceleration.
