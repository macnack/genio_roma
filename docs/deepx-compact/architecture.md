# DEEPX DX-M1 toolchain architecture

> Compact of docs/deepx/architecture.md. Full text and extended citations are in the source file.

## Officially documented facts

### Two environments (host vs target)

- DX-AllSuite integrates compile, simulation, runtime and monitoring. [dx-all-suite@51d81fe2ef v2.5.0: docs/source/01_DX-AllSuite_Architecture_Overview.md#L5-L11]
- Host env [1] "AI Model Compile Environment": `.dxnn` builder, x86_64 only. [dx-all-suite@51d81fe2ef v2.5.0: docs/source/01_DX-AllSuite_Architecture_Overview.md#L21-L22]
- Target env [2] "AI Model Runtime Environment": runs `.dxnn` on NPU, x86_64 and aarch64. [dx-all-suite@51d81fe2ef v2.5.0: docs/source/01_DX-AllSuite_Architecture_Overview.md#L28-L29]
- DX-COM (host) x86_64 only; DX-Runtime (target) x86_64 and aarch64. [dx-all-suite@51d81fe2ef v2.5.0: docs/source/01_DX-AllSuite_Architecture_Overview.md#L58-L62]
- DX-COM states aarch64 (arm64) is NOT supported. [dx-compiler@a087726ead v2.5.0: source/docs/02_01_System_Requirements_of_DX-COM.md#L5-L6]

### Components and roles

| Component | Role | Citation |
|---|---|---|
| DX-COM (`dxcom`, Python `dx_com`) | ONNX + JSON config -> `.dxnn`; proprietary quantization/optimization | [dx-all-suite@51d81fe2ef v2.5.0: docs/source/01_DX-AllSuite_Architecture_Overview.md#L24] |
| Compilation Summary Report | HTML from `--export_html`; CPU/NPU partitioning | [dx-all-suite@51d81fe2ef v2.5.0: docs/source/01_DX-AllSuite_Architecture_Overview.md#L25] |
| DX-ModelZoo | ONNX + JSON + pre-compiled `.dxnn`; `dxmz` CLI (list/info/eval/compile/benchmark) | [dx-all-suite@51d81fe2ef v2.5.0: docs/source/01_DX-AllSuite_Architecture_Overview.md#L26], [dx-all-suite@51d81fe2ef v2.5.0: docs/source/01_DX-AllSuite_Architecture_Overview.md#L110-L114] |
| DX-RT | Firmware/driver interface to run `.dxnn`; buffers, inference, monitoring; C/C++ and Python APIs | [dx-all-suite@51d81fe2ef v2.5.0: docs/source/01_DX-AllSuite_Architecture_Overview.md#L31] |
| DX-APP | Sample apps on DX-RT | [dx-all-suite@51d81fe2ef v2.5.0: docs/source/01_DX-AllSuite_Architecture_Overview.md#L32] |
| DX-STREAM | GStreamer plugin: pre-process, inference, post-process elements | [dx-all-suite@51d81fe2ef v2.5.0: docs/source/01_DX-AllSuite_Architecture_Overview.md#L33] |
| Driver and FW | Driver: PCIe communication; firmware: NPU scheduling and power | [dx-all-suite@51d81fe2ef v2.5.0: docs/source/01_DX-AllSuite_Architecture_Overview.md#L34] |

### How the pieces connect

- DX-RT uses PCIe for host-NPU data transfer, via firmware and device drivers. [dx_rt@f997363c97 v3.5.0: docs/source/docs/01_DXNN_Runtime_Overview.md#L20]
- Inference flow: input (OpenCV) -> pre-processing -> `InferenceEngine` (`.dxnn` + optional `InferenceOption`) -> NPU/CPU scheduling -> post-processing. `InferenceEngine` controls NPU, manages I/O tensor memory, schedules NPU and CPU. [dx_rt@f997363c97 v3.5.0: docs/source/docs/01_DXNN_Runtime_Overview.md#L45-L58]
- Kernel modules: `dxrt_driver.ko` (from `modules/rt`; system comms, memory, device commands) and `dx_dma.ko` (from `modules/pci_deepx`; PCIe DMA). [dx_rt@f997363c97 v3.5.0: docs/source/docs/02_Installation_on_Linux.md#L727-L733]
- Driver README: `rt/` -> `dxrt_driver.ko`, `pci_deepx/` -> `dx_dma.ko`; `virt_dma` is a prerequisite loaded before `dx_dma` and `dxrt_driver`. [dx_rt_npu_linux_driver@8455be6254 v2.7.0: README.md#L81-L91], [dx_rt_npu_linux_driver@8455be6254 v2.7.0: README.md#L195-L197]
- systemd daemon `dxrtd` (`dxrt.service`, `ExecStart=/usr/local/bin/dxrtd`) enables multi-process NPU access; enabled by default (`USE_SERVICE=ON`). [dx_rt@f997363c97 v3.5.0: docs/source/docs/02_Installation_on_Linux.md#L969-L973], [dx_rt@f997363c97 v3.5.0: service/dxrt.service#L1-L12]
- `dxrtd` is a singleton across host and containers; a second instance fails with "Other instance of dxrtd is running". [dx-all-suite@51d81fe2ef v2.5.0: docs/source/05_FAQ_Troubleshooting_Guide.md#L43-L45]
- Containers share the host kernel: driver must be installed on host; DX-RT in a container does not upgrade the driver. [dx-all-suite@51d81fe2ef v2.5.0: docs/source/02_Setting_Up_Environment.md#L426-L428], [dx-all-suite@51d81fe2ef v2.5.0: docs/source/05_FAQ_Troubleshooting_Guide.md#L466]
- Firmware (`fw.bin`; trees for `m1` and `m1m`; `m1` also holds `h1`) is flashed to the NPU, not installed by APT. [dx_fw@a72406f3ca v2.7.6: README.md#L4-L15], [dx-all-suite@51d81fe2ef v2.5.0: docs/source/02_Setting_Up_Environment.md#L132-L136]
- dx-runtime bundles `dx_rt_npu_linux_driver`, `dx_fw`, `dx_rt`, `dx_app`, `dx_stream` as git submodules. [dx-runtime@73ff9904f5 v2.5.0: README.md#L42]
- Python module `dx_engine`: `import dx_engine` raises `RuntimeError` if `libdxrt.so` major.minor differs; bypass with `DX_ENGINE_SKIP_VERSION_CHECK=1`. [dx_rt@f997363c97 v3.5.0: RELEASE_NOTES.md#L34]

### `.dxnn` flow

1. Export PyTorch/TensorFlow model to ONNX (opset 11-21, 17 recommended). [dx-all-suite@51d81fe2ef v2.5.0: docs/source/02_Setting_Up_Environment.md#L211-L213]
2. DX-COM (host, `venv-dx-compiler`): ONNX + JSON -> `.dxnn`. [dx-all-suite@51d81fe2ef v2.5.0: docs/source/02_Setting_Up_Environment.md#L214]
3. Transfer `.dxnn` to target. [dx-all-suite@51d81fe2ef v2.5.0: docs/source/01_DX-AllSuite_Architecture_Overview.md#L41]
4. DX-RT on target (`venv-dx-runtime`) loads and runs it on NPU. [dx-all-suite@51d81fe2ef v2.5.0: docs/source/02_Setting_Up_Environment.md#L215-L216]
- Shortcut: use a pre-compiled `.dxnn` from ModelZoo/sample data directly with DX-RT. [dx-all-suite@51d81fe2ef v2.5.0: docs/source/02_Setting_Up_Environment.md#L226-L230]
- `dxcom -m sample_models/onnx/YOLOV5S-1.onnx -c sample_models/json/YOLOV5S-1.json -o output/YOLOV5S-1` -> `output/YOLOV5S-1.dxnn`. [dx-all-suite@51d81fe2ef v2.5.0: docs/source/02_Setting_Up_Environment.md#L549-L557]
- DX-COM v2.5.0 emits `.dxnn` format v9; v9 needs DX-RT >= 3.5.0 (DX-RT <= 3.4.2 cannot load it). [dx-compiler@a087726ead v2.5.0: source/docs/02_01_System_Requirements_of_DX-COM.md#L13]
- DX-RT v3.5.0 added a V9 `.dxnn` parser. [dx_rt@f997363c97 v3.5.0: RELEASE_NOTES.md#L33]
- `dxparse -m <model.dxnn>` inspects a compiled model. [dx_rt@f997363c97 v3.5.0: docs/source/docs/05_Command_Line_Interface.md#L19-L30]
- DX-APP runners check DX-RT >= 3.5.0 (C++) and model format >= v7; ModelZoo 2_5_0 files are container v9. [dx_app@375de0344f v3.3.0: README.md#L287]

### Python / env layout

- Venvs: `dx-compiler/venv-dx-compiler`, `dx-runtime/venv-dx-runtime`. ModelZoo (`dxmz`) installs into runtime venv (`/venv-dxnn` in Docker); `dx_com` not installed there by default. [dx-all-suite@51d81fe2ef v2.5.0: docs/source/02_Setting_Up_Environment.md#L188-L192], [dx-all-suite@51d81fe2ef v2.5.0: docs/source/05_FAQ_Troubleshooting_Guide.md#L302]

### CLI naming

- Since DX-RT v3.4.0: `dxcli` (was `dxrt-cli`), `dxparse` (`parse_model`), `dxrun` (`run_model`); old names remain as aliases. [dx_rt@f997363c97 v3.5.0: docs/source/docs/05_Command_Line_Interface.md#L7-L15]

## Experimentally verified facts

None yet (no DX-M1 available on host as of 2026-11-05).

## Hypotheses needing validation

- H1. Suite docs name DX-RT/driver/FW as target-side only; whether DX-COM and DX-RT can share one venv on our dev host without `numpy` conflicts (ModelZoo pins `numpy>=1.20,<2.0` per [dx-all-suite@51d81fe2ef v2.5.0: docs/source/05_FAQ_Troubleshooting_Guide.md#L317]) is untested. Settle by creating a venv and installing both wheels.
- H2. DX-COM is x86_64-only, so compile on the x86_64 dev host and copy `.dxnn` to the (possibly ARM64) device. Docs state each half separately, never a combined walk-through. Settle by compiling a sample model and running `dxrun` on the target.
- H3. `dxrtd` daemon/driver interplay for DX-RT in a container on a separate board is documented only for same-host containers. Settle by running `dxcli -s` inside a container on the board.
