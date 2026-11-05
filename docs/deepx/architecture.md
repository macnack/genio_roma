# DEEPX DX-M1 toolchain architecture

Scope: how DX-COM, DX-RT, driver, firmware, DX-APP, DX-Stream and ModelZoo fit together and how a `.dxnn` file flows from ONNX to the NPU. See `CONVENTIONS.md` for claim classes and citation format.

## Officially documented facts

### Two environments (host vs target)

- DX-AllSuite (DXNN SDK) integrates model optimization through target deployment as a single workflow: model compilation, simulation, runtime execution and monitoring. [dx-all-suite@51d81fe2ef v2.5.0: docs/source/01_DX-AllSuite_Architecture_Overview.md#L5-L11]
- Environment [1], "AI Model Compile Environment (Host Platform)", converts trained models into DEEPX-proprietary `.dxnn` binaries and supports x86_64 PCs. [dx-all-suite@51d81fe2ef v2.5.0: docs/source/01_DX-AllSuite_Architecture_Overview.md#L21-L22]
- Environment [2], "AI Model Runtime Environment (Target Platform)", runs `.dxnn` models on real NPU hardware and supports both x86_64 and aarch64. [dx-all-suite@51d81fe2ef v2.5.0: docs/source/01_DX-AllSuite_Architecture_Overview.md#L28-L29]
- Platform table: DX-Compiler (host) = x86_64 only; DX-Runtime (target) = x86_64 and aarch64. [dx-all-suite@51d81fe2ef v2.5.0: docs/source/01_DX-AllSuite_Architecture_Overview.md#L58-L62]
- DX-COM itself states aarch64 (arm64) is NOT supported. [dx-compiler@a087726ead v2.5.0: source/docs/02_01_System_Requirements_of_DX-COM.md#L5-L6]

### Components and roles

| Component | Role (as documented) | Citation |
|---|---|---|
| DX-COM (compiler, `dxcom`, Python `dx_com`) | Generates `.dxnn` from an ONNX model plus a JSON config; proprietary quantization/optimization. | [dx-all-suite@51d81fe2ef v2.5.0: docs/source/01_DX-AllSuite_Architecture_Overview.md#L24] |
| Compilation Summary Report | Interactive HTML report from DX-COM (`--export_html`) showing CPU/NPU partitioning. | [dx-all-suite@51d81fe2ef v2.5.0: docs/source/01_DX-AllSuite_Architecture_Overview.md#L25] |
| DX-ModelZoo | Pre-trained models as ONNX + JSON config + pre-compiled `.dxnn`; driven by the `dxmz` CLI (list/info/eval/compile/benchmark). | [dx-all-suite@51d81fe2ef v2.5.0: docs/source/01_DX-AllSuite_Architecture_Overview.md#L26], [dx-all-suite@51d81fe2ef v2.5.0: docs/source/01_DX-AllSuite_Architecture_Overview.md#L110-L114] |
| DX-RT (runtime) | Interacts with firmware and driver to run `.dxnn`; model loading, I/O buffers, inference, monitoring; C/C++ and Python APIs. | [dx-all-suite@51d81fe2ef v2.5.0: docs/source/01_DX-AllSuite_Architecture_Overview.md#L31] |
| DX-APP | Sample applications on DX-RT (detection, face recognition, classification ...). | [dx-all-suite@51d81fe2ef v2.5.0: docs/source/01_DX-AllSuite_Architecture_Overview.md#L32] |
| DX-STREAM | GStreamer plugin connecting real-time video to NPU inference (pre-process, inference, post-process elements). | [dx-all-suite@51d81fe2ef v2.5.0: docs/source/01_DX-AllSuite_Architecture_Overview.md#L33] |
| Driver and FW | Driver: high-speed communication over PCIe; firmware: NPU resource scheduling and power. | [dx-all-suite@51d81fe2ef v2.5.0: docs/source/01_DX-AllSuite_Architecture_Overview.md#L34] |

### How the pieces connect

- DX-RT "uses a PCIe-based interface for high-speed data transfer between the host and the NPU" and talks to the NPU through firmware and device drivers. [dx_rt@f997363c97 v3.5.0: docs/source/docs/01_DXNN_Runtime_Overview.md#L20]
- Inference flow: input (OpenCV) -> pre-processing -> `InferenceEngine` (given the `.dxnn` and optional `InferenceOption`) -> NPU/CPU scheduling -> post-processing/display. The `InferenceEngine` initializes/controls the NPU, manages I/O tensor memory, and schedules tasks across NPU and CPU. [dx_rt@f997363c97 v3.5.0: docs/source/docs/01_DXNN_Runtime_Overview.md#L45-L58]
- The kernel side consists of two modules: `dxrt_driver.ko` (from `modules/rt`; system-level communication, memory control, device commands) and `dx_dma.ko` (from `modules/pci_deepx`; PCIe DMA between host and device). [dx_rt@f997363c97 v3.5.0: docs/source/docs/02_Installation_on_Linux.md#L727-L733]
- The driver README confirms the same layout (`rt/` -> `dxrt_driver.ko`, `pci_deepx/` -> `dx_dma.ko`) and notes `virt_dma` is a prerequisite loaded before `dx_dma` and `dxrt_driver`. [dx_rt_npu_linux_driver@8455be6254 v2.7.0: README.md#L81-L91], [dx_rt_npu_linux_driver@8455be6254 v2.7.0: README.md#L195-L197]
- User space uses a systemd daemon `dxrtd` (service `dxrt.service`, `ExecStart=/usr/local/bin/dxrtd`) to allow multi-process NPU access; it is enabled by default (`USE_SERVICE=ON`). [dx_rt@f997363c97 v3.5.0: docs/source/docs/02_Installation_on_Linux.md#L969-L973], [dx_rt@f997363c97 v3.5.0: service/dxrt.service#L1-L12]
- `dxrtd` is a singleton across host plus all containers; a second instance fails with "Other instance of dxrtd is running". [dx-all-suite@51d81fe2ef v2.5.0: docs/source/05_FAQ_Troubleshooting_Guide.md#L43-L45]
- Docker containers share the host kernel, so the driver must be installed on the host; DX-RT in a container does not upgrade the driver. [dx-all-suite@51d81fe2ef v2.5.0: docs/source/02_Setting_Up_Environment.md#L426-L428], [dx-all-suite@51d81fe2ef v2.5.0: docs/source/05_FAQ_Troubleshooting_Guide.md#L466]
- Firmware is flashed onto the NPU device (`fw.bin`, separate trees for `m1` and `m1m`; `m1` also holds the `h1` build). It is not installed by APT packages. [dx_fw@a72406f3ca v2.7.6: README.md#L4-L15], [dx-all-suite@51d81fe2ef v2.5.0: docs/source/02_Setting_Up_Environment.md#L132-L136]
- The dx-runtime repo bundles `dx_rt_npu_linux_driver`, `dx_fw`, `dx_rt`, `dx_app`, `dx_stream` as git submodules. [dx-runtime@73ff9904f5 v2.5.0: README.md#L42]
- Python bindings: module `dx_engine`; `import dx_engine` raises `RuntimeError` if the `libdxrt.so` major.minor differs (bypass `DX_ENGINE_SKIP_VERSION_CHECK=1`). [dx_rt@f997363c97 v3.5.0: RELEASE_NOTES.md#L34]

### `.dxnn` flow

1. Export trained PyTorch/TensorFlow model to ONNX (guide tip: opset 11-21, 17 recommended). [dx-all-suite@51d81fe2ef v2.5.0: docs/source/02_Setting_Up_Environment.md#L211-L213]
2. DX-COM (host, in `venv-dx-compiler`) turns ONNX + JSON config into `.dxnn`. [dx-all-suite@51d81fe2ef v2.5.0: docs/source/02_Setting_Up_Environment.md#L214]
3. Transfer `.dxnn` to the target. [dx-all-suite@51d81fe2ef v2.5.0: docs/source/01_DX-AllSuite_Architecture_Overview.md#L41]
4. DX-RT on the target (in `venv-dx-runtime`) loads it and runs on the NPU. [dx-all-suite@51d81fe2ef v2.5.0: docs/source/02_Setting_Up_Environment.md#L215-L216]
- Shortcut: use a pre-compiled `.dxnn` from ModelZoo/sample data directly with DX-RT. [dx-all-suite@51d81fe2ef v2.5.0: docs/source/02_Setting_Up_Environment.md#L226-L230]
- Example compile command: `dxcom -m sample_models/onnx/YOLOV5S-1.onnx -c sample_models/json/YOLOV5S-1.json -o output/YOLOV5S-1`; output `output/YOLOV5S-1.dxnn`. [dx-all-suite@51d81fe2ef v2.5.0: docs/source/02_Setting_Up_Environment.md#L549-L557]
- DX-COM v2.5.0 emits `.dxnn` format v9; v9 needs DX-RT >= 3.5.0 and DX-RT <= 3.4.2 cannot load it. [dx-compiler@a087726ead v2.5.0: source/docs/02_01_System_Requirements_of_DX-COM.md#L13]
- DX-RT v3.5.0 added a V9 `.dxnn` parser. [dx_rt@f997363c97 v3.5.0: RELEASE_NOTES.md#L33]
- `dxparse -m <model.dxnn>` inspects a compiled model. [dx_rt@f997363c97 v3.5.0: docs/source/docs/05_Command_Line_Interface.md#L19-L30]
- DX-APP runners check DX-RT >= 3.5.0 (C++) and model format >= v7; ModelZoo 2_5_0 files are container v9. [dx_app@375de0344f v3.3.0: README.md#L287]

### Python / env layout

- Venvs created by scripts: `dx-compiler/venv-dx-compiler`, `dx-runtime/venv-dx-runtime`; ModelZoo (`dxmz`) is installed into the runtime venv (`/venv-dxnn` in Docker); `dx_com` is not installed there by default. [dx-all-suite@51d81fe2ef v2.5.0: docs/source/02_Setting_Up_Environment.md#L188-L192], [dx-all-suite@51d81fe2ef v2.5.0: docs/source/05_FAQ_Troubleshooting_Guide.md#L302]

### CLI naming

- Since DX-RT v3.4.0: `dxcli` (was `dxrt-cli`), `dxparse` (`parse_model`), `dxrun` (`run_model`); old names remain as aliases. [dx_rt@f997363c97 v3.5.0: docs/source/docs/05_Command_Line_Interface.md#L7-L15]

## Experimentally verified facts

None yet (no DX-M1 available on host as of 2026-11-05).

## Hypotheses needing validation

- H1. The suite docs name DX-RT/driver/FW as target-side only; whether DX-COM and DX-RT can share one venv on our dev host without `numpy` conflicts (ModelZoo pins `numpy>=1.20,<2.0` per [dx-all-suite@51d81fe2ef v2.5.0: docs/source/05_FAQ_Troubleshooting_Guide.md#L317]) is untested. Settle by creating a venv and installing both wheels.
- H2. Because DX-COM is x86_64-only, compilation must happen on the x86_64 dev host and `.dxnn` be copied to the (possibly ARM64) device. The docs state each half separately but never a combined x86-compile / arm64-run walk-through; verify by compiling a sample model and running `dxrun` on the target.
- H3. The `dxrtd` daemon/driver interplay when DX-RT is used from a container on a separate board is documented only for same-host containers; settle by running `dxcli -s` inside a container on the board.
