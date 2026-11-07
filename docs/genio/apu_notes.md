# Genio-700 APU (MediaTek MDLA 3.0): status for this project (2026-11-06)

## Experimentally verified facts
- 2026-11-06: installed `libneuropilot8` 8.2.16 + `python3-onnxruntime-neuron` 1.20.2 (via laptop-downloaded `.deb`, board has no network). The provider loads, but the first `/dev/apusys` ioctl returns `EFAULT` and compile aborts with `memAlloc ... fail(Bad address)` + segfault, for ConvNeXt and for a trivial CNN. No model ran on the APU. Details and logs: `reports/apu_neuron.md`.
- Board kernel exposes `apusys`/`apu_top` modules, `/dev/apusys*`, devfreq `mdla_devfreq`/`vpu_devfreq` (see plan notes). Before 2026-11-06 no NeuroPilot userspace was installed.

## Officially documented facts (web search, not yet read in full; fetched 2026-11-06)
- Genio 700 = MDLA 3.0 / NeuroPilot 6 [genio.mediatek.com/doc/iot-aihub/ai_hub/related_resource.html]. MediaTek's TFLite route: Neuron compiler `ncc-tflite` (TFLite -> DLA) or the Neuron Stable Delegate [mediatek.gitlab.io/aiot/doc/aiot-dev-guide/sw/yocto/ml-guide/ml-neuron-sdk.html].
- The ONNX Runtime NeuronExecutionProvider docs target Genio 720/520 on Yocto [genio.mediatek.com/doc/iot-aihub/ai_hub/supported_os/yocto/onnxruntime/accelerating_ort.html]; community post says enabling it on Genio 700/510 needs a MediaTek representative [genio-community.mediatek.com/t/accelerating-ai-on-genio-with-the-onnx-runtime-neuronexecutionprovider/1347].
- NP6 SDK bundles (with `ncc-tflite`) are NDA-gated. CORRECTION 2026-11-07: the Ubuntu runtime/utility debs `mediatek-libneuron`, `mediatek-neuron-utils` (contains `ncc-tflite`, `neuronrt`, `vpu5_test`) and `mediatek-apusys-firmware-genio700` are public in `ppa:mediatek-genio/genio-public` (jammy only); MediaTek's Genio 700 Ubuntu instructions install exactly these [genio.mediatek.com/doc/ubuntu/bsp-installation/neuropilot.html]. The NP8 packages used on 2026-11-06 are from a third-party PPA (`baoshan-team`). See `reports/apu_neuron.md` follow-up.

## Hypotheses needing validation
- Settled negatively for the NP8 apt packages as installed (see verified facts). Open: the MediaTek NP6 packages (jammy builds, unpacked privately, not run on the board yet) may match this kernel; the EFAULT root cause is unproven.
- ConvNeXt ops (7x7 depthwise, LayerNorm, GELU) on MDLA 3.0: unknown; unsupported ops would fall back to CPU, so a run would need partition proof before claiming APU acceleration.
