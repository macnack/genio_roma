# Genio-700 APU (MediaTek MDLA 3.0): status for this project (2026-11-06)

## Experimentally verified facts
- Board kernel exposes `apusys`/`apu_top` modules, `/dev/apusys*`, devfreq `mdla_devfreq`/`vpu_devfreq` (see plan notes). No NeuroPilot userspace is installed; apt offers `libneuropilot8` 8.2.16, `libonnxruntime-neuron`/`python3-onnxruntime-neuron` 1.20.2. Not installed or run.

## Officially documented facts (web search, not yet read in full; fetched 2026-11-06)
- Genio 700 = MDLA 3.0 / NeuroPilot 6 [genio.mediatek.com/doc/iot-aihub/ai_hub/related_resource.html]. MediaTek's TFLite route: Neuron compiler `ncc-tflite` (TFLite -> DLA) or the Neuron Stable Delegate [mediatek.gitlab.io/aiot/doc/aiot-dev-guide/sw/yocto/ml-guide/ml-neuron-sdk.html].
- The ONNX Runtime NeuronExecutionProvider docs target Genio 720/520 on Yocto [genio.mediatek.com/doc/iot-aihub/ai_hub/supported_os/yocto/onnxruntime/accelerating_ort.html]; community post says enabling it on Genio 700/510 needs a MediaTek representative [genio-community.mediatek.com/t/accelerating-ai-on-genio-with-the-onnx-runtime-neuronexecutionprovider/1347].
- NP6 SDK bundles (with `ncc-tflite`) are NDA-gated.

## Hypotheses needing validation
- The apt `python3-onnxruntime-neuron` may or may not work on Genio 700 Ubuntu (description says Genio 1200 "and related"). Settle by installing on the board (needs sudo, user approval) and creating a session with the Neuron EP.
- ConvNeXt ops (7x7 depthwise, LayerNorm, GELU) on MDLA 3.0: unknown; unsupported ops would fall back to CPU, so a run would need partition proof before claiming APU acceleration.
